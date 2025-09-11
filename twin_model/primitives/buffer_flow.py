"""Accumulation buffer primitive for inter-equipment flow smoothing.

This module implements accumulation buffers that smooth flow variations
between equipment and prevent starvation/blocking in continuous flow systems.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Generator

import simpy

from .base_flow import BaseFlowPrimitive, FlowCapacity, FlowState

logger = logging.getLogger(__name__)


class BufferMode(Enum):
    """Buffer operation modes."""

    FIFO = "fifo"  # First-In-First-Out
    FILO = "filo"  # First-In-Last-Out (stack)


@dataclass
class BufferParameters:
    """Parameters for accumulation buffer operation."""

    mode: BufferMode  # FIFO or FILO operation
    warning_level_low: float  # Percentage (0-1) for low level warning
    warning_level_high: float  # Percentage (0-1) for high level warning
    max_dwell_time: float  # Maximum time material can stay in buffer (minutes)
    update_interval: float = 0.01  # How often to check buffer state (minutes)

    def __post_init__(self) -> None:
        """Validate buffer parameters."""
        if not 0 <= self.warning_level_low <= 1:
            raise ValueError(f"warning_level_low must be between 0 and 1, got {self.warning_level_low}")
        if not 0 <= self.warning_level_high <= 1:
            raise ValueError(f"warning_level_high must be between 0 and 1, got {self.warning_level_high}")
        if self.warning_level_low >= self.warning_level_high:
            raise ValueError("warning_level_low must be less than warning_level_high")
        if self.max_dwell_time <= 0:
            raise ValueError(f"max_dwell_time must be positive, got {self.max_dwell_time}")
        if self.update_interval <= 0:
            raise ValueError(f"update_interval must be positive, got {self.update_interval}")


class AccumulationBuffer(BaseFlowPrimitive):
    """Dynamic accumulation buffer between equipment."""

    def __init__(
        self,
        env: simpy.Environment,
        config: dict[str, Any],
        flow_capacity: FlowCapacity,
        buffer_params: BufferParameters,
    ) -> None:
        """Initialize accumulation buffer.

        Args:
            env: SimPy environment
            config: Configuration dictionary
            flow_capacity: Flow capacity constraints
            buffer_params: Buffer-specific parameters
        """
        # Initialize base class
        super().__init__(env, config, flow_capacity)
        
        self.buffer_params = buffer_params

        # Create the buffer container
        self.buffer = simpy.Container(
            env, capacity=flow_capacity.internal_capacity, init=flow_capacity.initial_level
        )

        # Track material dwell time (simplified - tracks average)
        self.material_entry_time = env.now
        self.total_dwell_time = 0.0
        self.dwell_samples = 0

        # Event tracking
        self.overflow_events = 0
        self.underflow_events = 0
        self.warning_events = {"low": 0, "high": 0}

        # State tracking
        self.is_warning_low = False
        self.is_warning_high = False
        self.is_overflow = False
        self.is_underflow = False

        # Flow tracking (for buffer-specific metrics, base class handles total_input/output)
        self.total_flow_in = 0.0
        self.total_flow_out = 0.0

        # Connection tracking
        self.upstream: BaseFlowPrimitive | None = None
        self.downstream: BaseFlowPrimitive | None = None
        self.input_container: simpy.Container | None = None
        self.output_container: simpy.Container | None = None

        logger.info(
            f"Created AccumulationBuffer {config.get('id', 'unknown')} "
            f"with capacity {flow_capacity.internal_capacity} units, "
            f"mode: {buffer_params.mode.value}"
        )

        # Start the buffer process
        self.process: simpy.Process | None = None

    def connect(self, upstream: BaseFlowPrimitive | None, downstream: BaseFlowPrimitive | None) -> None:
        """Connect buffer to upstream and downstream equipment.

        Args:
            upstream: Upstream equipment (source)
            downstream: Downstream equipment (consumer)
        """
        buffer_id = self.config.get("id", "unknown")
        self.upstream = upstream
        self.downstream = downstream

        logger.info(f"Connecting buffer {buffer_id}: upstream={upstream}, downstream={downstream}")

        if upstream and hasattr(upstream, "output_container"):
            self.input_container = upstream.output_container
            logger.info(f"Buffer {buffer_id}: Using upstream.output_container as input")
        elif upstream and hasattr(upstream, "output_buffer"):
            self.input_container = upstream.output_buffer
            logger.info(f"Buffer {buffer_id}: Using upstream.output_buffer as input")
        else:
            # Create internal input if no upstream
            self.input_container = simpy.Container(self.env, capacity=float("inf"))
            logger.warning(f"Buffer {buffer_id}: Created internal input container (no upstream connection)")

        # Buffer output is always its own buffer
        self.output_container = self.buffer

        # Log downstream attributes for debugging
        if downstream:
            logger.info(
                f"Buffer {buffer_id}: Downstream {downstream} has: "
                f"input_buffer={hasattr(downstream, 'input_buffer')}, "
                f"input_container={hasattr(downstream, 'input_container')}"
            )

        logger.info(f"Buffer {buffer_id} connection complete")

    def start(self) -> None:
        """Start the buffer flow process."""
        if self.process is None:
            self.process = self.env.process(self.process_flow())
            logger.debug(f"Started buffer process: {self.config.get('id')}")


    def get_utilization(self) -> float:
        """Calculate buffer utilization.

        Returns:
            Utilization as percentage (0-100)
        """
        if self.env.now == 0:
            return 0.0

        # For buffers, utilization is based on average fill level
        return (self.buffer.level / self.buffer.capacity * 100) if self.buffer.capacity > 0 else 0.0


    def process_flow(self) -> Generator[simpy.Event, None, None]:
        """Process continuous flow through the buffer."""
        buffer_id = self.config.get("id", "unknown")
        logger.info(f"Starting buffer process for {buffer_id}")

        while True:
            try:
                current_level = self.buffer.level
                capacity = self.buffer.capacity
                fill_percentage = current_level / capacity if capacity > 0 else 0

                # Log buffer state periodically
                if int(self.env.now) % 10 == 0:  # Log every 10 time units
                    logger.debug(
                        f"Buffer {buffer_id} @ {self.env.now:.1f}: "
                        f"level={current_level:.1f}/{capacity:.1f} ({fill_percentage*100:.1f}%), "
                        f"input_container={self.input_container is not None}, "
                        f"downstream={self.downstream is not None}"
                    )

                # Check warning levels
                self._check_warning_levels(fill_percentage)

                # Check overflow/underflow
                self._check_overflow_underflow(current_level, capacity)

                # Transfer from input to buffer
                if self.input_container and current_level < capacity:
                    # Calculate transfer amount
                    space_available = capacity - current_level
                    max_transfer = min(
                        self.flow_capacity.max_input_rate * self.buffer_params.update_interval,
                        space_available,
                        self.input_container.level,
                    )

                    if max_transfer > 0:
                        logger.debug(
                            f"Buffer {buffer_id}: Transferring {max_transfer:.2f} units from input to buffer"
                        )
                        # Pull from input
                        yield self.input_container.get(max_transfer)
                        # Push to buffer
                        yield self.buffer.put(max_transfer)
                        self.total_flow_in += max_transfer
                        # Track in base class metrics
                        self.flow_metrics.total_input += max_transfer
                        logger.debug(
                            f"Buffer {buffer_id}: Transfer complete. New level: {self.buffer.level:.2f}"
                        )

                        # Update dwell time tracking
                        if current_level > 0:
                            elapsed = self.env.now - self.material_entry_time
                            self.total_dwell_time += elapsed
                            self.dwell_samples += 1
                        self.material_entry_time = self.env.now

                        # Emit flow event
                        self.emit_observable(
                            "buffer_flow",
                            {
                                "timestamp": self.env.now,
                                "buffer_id": self.config.get("id"),
                                "level": self.buffer.level,
                                "fill_percentage": fill_percentage,
                                "flow_in": max_transfer,
                            },
                        )

                # Transfer from buffer to downstream
                # Check for both input_container and input_buffer (equipment uses input_buffer)
                if self.downstream and current_level > 0:
                    downstream_container = None
                    if hasattr(self.downstream, "input_container"):
                        downstream_container = self.downstream.input_container
                        logger.debug(f"Buffer {buffer_id}: Using downstream.input_container")
                    elif hasattr(self.downstream, "input_buffer"):
                        downstream_container = self.downstream.input_buffer
                        logger.debug(f"Buffer {buffer_id}: Using downstream.input_buffer")
                    else:
                        logger.warning(
                            f"Buffer {buffer_id}: Downstream {self.downstream} has no input_container or input_buffer"
                        )

                    if downstream_container is not None:
                        downstream_space = downstream_container.capacity - downstream_container.level
                        logger.debug(
                            f"Buffer {buffer_id}: Downstream space available: {downstream_space:.2f}"
                        )
                    else:
                        downstream_space = 0
                        logger.warning(f"Buffer {buffer_id}: No downstream container found")

                    max_output = min(
                        self.flow_capacity.max_output_rate * self.buffer_params.update_interval,
                        current_level,
                        downstream_space,
                    )

                    if max_output > 0 and downstream_container is not None:
                        logger.debug(
                            f"Buffer {buffer_id}: Transferring {max_output:.2f} units to downstream "
                            f"(container level: {downstream_container.level:.2f}/{downstream_container.capacity:.2f})"
                        )
                        try:
                            # Pull from buffer
                            yield self.buffer.get(max_output)
                            logger.debug(f"Buffer {buffer_id}: Got {max_output:.2f} from buffer")
                            # Push to downstream
                            yield downstream_container.put(max_output)
                            self.total_flow_out += max_output
                            # Track in base class metrics
                            self.flow_metrics.total_output += max_output
                            logger.debug(
                                f"Buffer {buffer_id}: Output transfer complete. Remaining: {self.buffer.level:.2f}"
                            )
                        except Exception as e:
                            logger.error(f"Buffer {buffer_id}: Transfer error: {e}")

                        # Check dwell time violation
                        if self.dwell_samples > 0:
                            avg_dwell = self.total_dwell_time / self.dwell_samples
                            if avg_dwell > self.buffer_params.max_dwell_time:
                                self.emit_observable(
                                    "dwell_time_exceeded",
                                    {
                                        "timestamp": self.env.now,
                                        "buffer_id": self.config.get("id"),
                                        "average_dwell_time": avg_dwell,
                                        "max_allowed": self.buffer_params.max_dwell_time,
                                    },
                                )

                # Update state based on flow conditions
                if current_level == 0 and self.input_container and self.input_container.level == 0:
                    self.change_state(FlowState.STARVED_UPSTREAM, "Buffer empty and no input available")
                elif current_level == capacity and downstream_space == 0 if self.downstream else False:
                    self.change_state(FlowState.BLOCKED_DOWNSTREAM, "Buffer full and downstream blocked")
                elif current_level > 0:
                    self.change_state(FlowState.FLOWING, "Buffer transferring material")
                else:
                    self.change_state(FlowState.IDLE, "Buffer waiting for material")

            except simpy.Interrupt:
                logger.debug(f"Buffer {self.config.get('id')} interrupted")
                break

            # Wait for next update
            yield self.env.timeout(self.buffer_params.update_interval)

    def _check_warning_levels(self, fill_percentage: float) -> None:
        """Check and emit warnings for buffer levels.

        Args:
            fill_percentage: Current fill level as percentage (0-1)
        """
        # Low level warning
        if fill_percentage <= self.buffer_params.warning_level_low:
            if not self.is_warning_low:
                self.is_warning_low = True
                self.warning_events["low"] += 1
                self.emit_observable(
                    "buffer_warning_low",
                    {
                        "timestamp": self.env.now,
                        "buffer_id": self.config.get("id"),
                        "level": self.buffer.level,
                        "fill_percentage": fill_percentage,
                    },
                )
        else:
            self.is_warning_low = False

        # High level warning
        if fill_percentage >= self.buffer_params.warning_level_high:
            if not self.is_warning_high:
                self.is_warning_high = True
                self.warning_events["high"] += 1
                self.emit_observable(
                    "buffer_warning_high",
                    {
                        "timestamp": self.env.now,
                        "buffer_id": self.config.get("id"),
                        "level": self.buffer.level,
                        "fill_percentage": fill_percentage,
                    },
                )
        else:
            self.is_warning_high = False

    def _check_overflow_underflow(self, current_level: float, capacity: float) -> None:
        """Check for overflow and underflow conditions.

        Args:
            current_level: Current buffer level
            capacity: Buffer capacity
        """
        # Underflow (empty)
        if current_level == 0:
            if not self.is_underflow:
                self.is_underflow = True
                self.underflow_events += 1
                self.emit_observable(
                    "buffer_underflow",
                    {"timestamp": self.env.now, "buffer_id": self.config.get("id")},
                )
        else:
            self.is_underflow = False

        # Overflow (full)
        if current_level >= capacity:
            if not self.is_overflow:
                self.is_overflow = True
                self.overflow_events += 1
                self.emit_observable(
                    "buffer_overflow",
                    {
                        "timestamp": self.env.now,
                        "buffer_id": self.config.get("id"),
                        "level": current_level,
                    },
                )
        else:
            self.is_overflow = False

    def get_metrics(self) -> dict[str, Any]:
        """Get buffer performance metrics.

        Returns:
            Dictionary of buffer metrics
        """
        # Base metrics using properties from BaseFlowPrimitive
        metrics = {
            "equipment_id": self.config.get("id"),
            "timestamp": self.env.now,
            "state": self.current_state.value,
            "total_input": self.total_input,  # From base class property
            "total_output": self.total_output,  # From base class property
            "total_scrap": self.total_scrap,  # From base class property
            "total_flow_in": self.total_flow_in,
            "total_flow_out": self.total_flow_out,
            "utilization": self.get_utilization(),
            "availability": self.get_availability(),
        }

        # Add buffer-specific metrics
        fill_percentage = self.buffer.level / self.buffer.capacity if self.buffer.capacity > 0 else 0
        avg_dwell = self.total_dwell_time / self.dwell_samples if self.dwell_samples > 0 else 0

        metrics.update(
            {
                "buffer_level": self.buffer.level,
                "fill_percentage": fill_percentage,
                "overflow_events": self.overflow_events,
                "underflow_events": self.underflow_events,
                "warning_events_low": self.warning_events["low"],
                "warning_events_high": self.warning_events["high"],
                "average_dwell_time": avg_dwell,
                "mode": self.buffer_params.mode.value,
            }
        )

        return metrics
