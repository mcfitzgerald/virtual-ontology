"""Flow monitor for real-time monitoring and bottleneck detection.

This module provides the FlowMonitor class that monitors production flow
in real-time and identifies bottlenecks and performance issues.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import simpy

from ..primitives import BaseFlowPrimitive, FlowState

logger = logging.getLogger(__name__)


@dataclass
class FlowSnapshot:
    """Snapshot of flow metrics at a point in time."""

    timestamp: float
    equipment_id: str
    state: FlowState
    input_level: float
    output_level: float
    throughput_rate: float
    utilization: float
    oee: float


@dataclass
class BottleneckInfo:
    """Information about a detected bottleneck."""

    equipment_id: str
    severity: float  # 0-1 scale
    upstream_blocked: list[str] = field(default_factory=list)
    downstream_starved: list[str] = field(default_factory=list)
    duration: float = 0.0
    impact: str = "Low"  # Low, Medium, High


class FlowMonitor:
    """Monitors flow and detects bottlenecks in real-time."""

    def __init__(
        self,
        env: simpy.Environment,
        monitoring_interval: float = 1.0,
        history_size: int = 100
    ) -> None:
        """Initialize flow monitor.

        Args:
            env: SimPy environment
            monitoring_interval: Time between monitoring checks (minutes)
            history_size: Number of snapshots to keep in history
        """
        self.env = env
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size

        # Monitoring data
        self.snapshots: dict[str, deque] = {}
        self.bottlenecks: list[BottleneckInfo] = []
        self.current_bottleneck: Optional[BottleneckInfo] = None

        # Performance metrics
        self.line_throughput: dict[str, float] = {}
        self.line_oee: dict[str, float] = {}

        # Primitives to monitor
        self.primitives: dict[str, BaseFlowPrimitive] = {}
        self.topology: dict[str, list[str]] = {}

        # Monitoring process
        self.monitoring_process: Optional[simpy.Process] = None

    def register_primitives(
        self,
        primitives: dict[str, BaseFlowPrimitive],
        topology: Optional[dict[str, list[str]]] = None
    ) -> None:
        """Register primitives to monitor.

        Args:
            primitives: Dictionary of primitive instances
            topology: Connection topology (optional)
        """
        self.primitives = primitives
        self.topology = topology or {}

        # Initialize snapshot history for each primitive
        for primitive_id in primitives:
            self.snapshots[primitive_id] = deque(maxlen=self.history_size)

        logger.info(f"Registered {len(primitives)} primitives for monitoring")

    def start(self) -> None:
        """Start monitoring process."""
        if self.monitoring_process is None:
            self.monitoring_process = self.env.process(self._monitor_flow())
            logger.info("Flow monitoring started")

    def _monitor_flow(self) -> simpy.core.Generator:
        """Main monitoring process."""
        while True:
            # Take snapshots of all primitives
            self._take_snapshots()

            # Analyze flow patterns
            self._analyze_flow()

            # Detect bottlenecks
            self._detect_bottlenecks()

            # Calculate line metrics
            self._calculate_line_metrics()

            # Wait for next interval
            yield self.env.timeout(self.monitoring_interval)

    def _take_snapshots(self) -> None:
        """Take snapshots of all primitive states."""
        for primitive_id, primitive in self.primitives.items():
            snapshot = self._create_snapshot(primitive_id, primitive)
            if snapshot:
                self.snapshots[primitive_id].append(snapshot)

    def _create_snapshot(
        self,
        primitive_id: str,
        primitive: BaseFlowPrimitive
    ) -> Optional[FlowSnapshot]:
        """Create a snapshot of primitive state.

        Args:
            primitive_id: Primitive identifier
            primitive: Primitive instance

        Returns:
            FlowSnapshot or None if primitive has no buffers
        """
        # Get buffer levels
        input_level = 0.0
        output_level = 0.0

        if hasattr(primitive, "input_buffer") and primitive.input_buffer:
            input_level = primitive.input_buffer.level

        if hasattr(primitive, "output_buffer") and primitive.output_buffer:
            output_level = primitive.output_buffer.level

        # Calculate throughput rate
        throughput_rate = self._calculate_throughput(primitive_id)

        # Get utilization and OEE
        utilization = 0.0
        oee = 0.0

        if hasattr(primitive, "get_utilization"):
            utilization = primitive.get_utilization()

        if hasattr(primitive, "get_oee"):
            oee = primitive.get_oee()

        return FlowSnapshot(
            timestamp=self.env.now,
            equipment_id=primitive_id,
            state=primitive.current_state,
            input_level=input_level,
            output_level=output_level,
            throughput_rate=throughput_rate,
            utilization=utilization,
            oee=oee
        )

    def _calculate_throughput(self, primitive_id: str) -> float:
        """Calculate current throughput rate.

        Args:
            primitive_id: Primitive identifier

        Returns:
            Throughput rate in units/minute
        """
        history = self.snapshots.get(primitive_id, deque())

        if len(history) < 2:
            return 0.0

        # Calculate based on output level changes
        recent = list(history)[-10:]  # Last 10 snapshots

        if len(recent) < 2:
            return 0.0

        output_change = recent[-1].output_level - recent[0].output_level
        time_span = recent[-1].timestamp - recent[0].timestamp

        if time_span > 0:
            return abs(output_change) / time_span

        return 0.0

    def _analyze_flow(self) -> None:
        """Analyze flow patterns across the system."""
        # Identify flow imbalances
        for primitive_id, primitive in self.primitives.items():
            history = self.snapshots.get(primitive_id, deque())

            if len(history) < 5:
                continue

            recent_states = [s.state for s in list(history)[-5:]]

            # Check for persistent blocking or starvation
            if all(s == FlowState.BLOCKED_DOWNSTREAM for s in recent_states):
                logger.warning(f"{primitive_id} persistently blocked downstream")

            elif all(s == FlowState.STARVED_UPSTREAM for s in recent_states):
                logger.warning(f"{primitive_id} persistently starved upstream")

    def _detect_bottlenecks(self) -> None:
        """Detect bottlenecks in the production flow."""
        bottleneck_candidates = []

        for primitive_id in self.primitives:
            score = self._calculate_bottleneck_score(primitive_id)

            if score > 0.5:  # Threshold for bottleneck detection
                bottleneck_candidates.append((primitive_id, score))

        if bottleneck_candidates:
            # Sort by severity
            bottleneck_candidates.sort(key=lambda x: x[1], reverse=True)

            # Take the most severe bottleneck
            bottleneck_id, severity = bottleneck_candidates[0]

            # Create or update bottleneck info
            if self.current_bottleneck and self.current_bottleneck.equipment_id == bottleneck_id:
                # Update existing bottleneck
                self.current_bottleneck.duration = (
                    self.env.now - (self.current_bottleneck.duration or self.env.now)
                )
                self.current_bottleneck.severity = severity
            else:
                # New bottleneck detected
                if self.current_bottleneck:
                    self.bottlenecks.append(self.current_bottleneck)

                self.current_bottleneck = self._create_bottleneck_info(bottleneck_id, severity)
                logger.warning(f"Bottleneck detected at {bottleneck_id} (severity: {severity:.2f})")
        else:
            # No bottleneck
            if self.current_bottleneck:
                self.bottlenecks.append(self.current_bottleneck)
                self.current_bottleneck = None

    def _calculate_bottleneck_score(self, primitive_id: str) -> float:
        """Calculate bottleneck score for a primitive.

        Args:
            primitive_id: Primitive identifier

        Returns:
            Bottleneck score (0-1)
        """
        history = self.snapshots.get(primitive_id, deque())

        if len(history) < 5:
            return 0.0

        recent = list(history)[-10:]

        # Factors that indicate a bottleneck
        factors = []

        # 1. Low utilization (equipment is constraining flow)
        avg_utilization = np.mean([s.utilization for s in recent])
        if avg_utilization > 90:
            factors.append(0.3)

        # 2. High input buffer level (material backing up)
        avg_input = np.mean([s.input_level for s in recent])
        if hasattr(self.primitives[primitive_id], "input_buffer"):
            buffer = self.primitives[primitive_id].input_buffer
            if buffer and buffer.capacity > 0:
                input_ratio = avg_input / buffer.capacity
                if input_ratio > 0.8:
                    factors.append(0.3)

        # 3. Low output buffer level (starving downstream)
        avg_output = np.mean([s.output_level for s in recent])
        if hasattr(self.primitives[primitive_id], "output_buffer"):
            buffer = self.primitives[primitive_id].output_buffer
            if buffer and buffer.capacity > 0:
                output_ratio = avg_output / buffer.capacity
                if output_ratio < 0.2:
                    factors.append(0.2)

        # 4. Lower throughput than neighbors
        throughput = recent[-1].throughput_rate
        neighbor_throughputs = self._get_neighbor_throughputs(primitive_id)
        if neighbor_throughputs:
            avg_neighbor = np.mean(neighbor_throughputs)
            if throughput < avg_neighbor * 0.8:
                factors.append(0.2)

        return min(sum(factors), 1.0)

    def _get_neighbor_throughputs(self, primitive_id: str) -> list[float]:
        """Get throughput rates of neighboring primitives.

        Args:
            primitive_id: Primitive identifier

        Returns:
            List of neighbor throughput rates
        """
        throughputs = []

        # Get upstream neighbors
        for upstream_id, downstream_list in self.topology.items():
            if primitive_id in downstream_list:
                history = self.snapshots.get(upstream_id, deque())
                if history:
                    throughputs.append(history[-1].throughput_rate)

        # Get downstream neighbors
        if primitive_id in self.topology:
            for downstream_id in self.topology[primitive_id]:
                history = self.snapshots.get(downstream_id, deque())
                if history:
                    throughputs.append(history[-1].throughput_rate)

        return throughputs

    def _create_bottleneck_info(
        self,
        bottleneck_id: str,
        severity: float
    ) -> BottleneckInfo:
        """Create bottleneck information.

        Args:
            bottleneck_id: Bottleneck equipment ID
            severity: Bottleneck severity (0-1)

        Returns:
            BottleneckInfo instance
        """
        info = BottleneckInfo(
            equipment_id=bottleneck_id,
            severity=severity,
            duration=self.env.now
        )

        # Find affected upstream equipment
        for upstream_id, downstream_list in self.topology.items():
            if bottleneck_id in downstream_list:
                history = self.snapshots.get(upstream_id, deque())
                if history and history[-1].state == FlowState.BLOCKED_DOWNSTREAM:
                    info.upstream_blocked.append(upstream_id)

        # Find affected downstream equipment
        if bottleneck_id in self.topology:
            for downstream_id in self.topology[bottleneck_id]:
                history = self.snapshots.get(downstream_id, deque())
                if history and history[-1].state == FlowState.STARVED_UPSTREAM:
                    info.downstream_starved.append(downstream_id)

        # Determine impact level
        total_affected = len(info.upstream_blocked) + len(info.downstream_starved)
        if total_affected >= 4:
            info.impact = "High"
        elif total_affected >= 2:
            info.impact = "Medium"
        else:
            info.impact = "Low"

        return info

    def _calculate_line_metrics(self) -> None:
        """Calculate metrics for production lines."""
        line_primitives: dict[str, list[str]] = {}

        # Group primitives by line
        for primitive_id, primitive in self.primitives.items():
            if hasattr(primitive, "config"):
                line_id = primitive.config.get("line_id", "default")
                if line_id not in line_primitives:
                    line_primitives[line_id] = []
                line_primitives[line_id].append(primitive_id)

        # Calculate metrics for each line
        for line_id, primitive_ids in line_primitives.items():
            # Find sink for line (endpoint)
            sink_id = f"{line_id}-SINK"
            if sink_id in primitive_ids:
                history = self.snapshots.get(sink_id, deque())
                if history:
                    self.line_throughput[line_id] = history[-1].throughput_rate
                    self.line_oee[line_id] = history[-1].oee

    def get_current_status(self) -> dict[str, Any]:
        """Get current monitoring status.

        Returns:
            Dictionary with current status information
        """
        status = {
            "timestamp": self.env.now,
            "monitored_equipment": len(self.primitives),
            "current_bottleneck": None,
            "line_metrics": {},
            "warnings": []
        }

        # Add bottleneck info
        if self.current_bottleneck:
            status["current_bottleneck"] = {
                "equipment": self.current_bottleneck.equipment_id,
                "severity": self.current_bottleneck.severity,
                "impact": self.current_bottleneck.impact,
                "affected_equipment": (
                    len(self.current_bottleneck.upstream_blocked) +
                    len(self.current_bottleneck.downstream_starved)
                )
            }

        # Add line metrics
        for line_id in self.line_throughput:
            status["line_metrics"][line_id] = {
                "throughput": self.line_throughput.get(line_id, 0),
                "oee": self.line_oee.get(line_id, 0)
            }

        # Check for warnings
        for primitive_id, history in self.snapshots.items():
            if history:
                latest = history[-1]
                if latest.utilization < 20:
                    status["warnings"].append(f"{primitive_id}: Very low utilization ({latest.utilization:.1f}%)")
                elif latest.oee < 30:
                    status["warnings"].append(f"{primitive_id}: Poor OEE ({latest.oee:.1f}%)")

        return status

    def get_bottleneck_history(self) -> list[dict[str, Any]]:
        """Get history of detected bottlenecks.

        Returns:
            List of bottleneck records
        """
        history = []

        for bottleneck in self.bottlenecks:
            history.append({
                "equipment": bottleneck.equipment_id,
                "severity": bottleneck.severity,
                "duration": bottleneck.duration,
                "impact": bottleneck.impact,
                "upstream_blocked": bottleneck.upstream_blocked,
                "downstream_starved": bottleneck.downstream_starved
            })

        # Add current bottleneck
        if self.current_bottleneck:
            history.append({
                "equipment": self.current_bottleneck.equipment_id,
                "severity": self.current_bottleneck.severity,
                "duration": self.env.now - self.current_bottleneck.duration,
                "impact": self.current_bottleneck.impact,
                "upstream_blocked": self.current_bottleneck.upstream_blocked,
                "downstream_starved": self.current_bottleneck.downstream_starved,
                "current": True
            })

        return history
