"""Base flow primitive for container-based continuous flow simulation.

This module provides the foundation for all flow-based simulation primitives
using SimPy Containers exclusively for continuous flow modeling.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generator, Optional

import simpy


@dataclass
class FlowCapacity:
    """Defines flow capacity constraints for equipment."""

    max_input_rate: float      # units/minute
    max_output_rate: float     # units/minute
    internal_capacity: float   # units
    initial_level: float = 0.0

    def __post_init__(self) -> None:
        """Validate capacity parameters."""
        if self.max_input_rate <= 0:
            raise ValueError(f"max_input_rate must be positive, got {self.max_input_rate}")
        if self.max_output_rate <= 0:
            raise ValueError(f"max_output_rate must be positive, got {self.max_output_rate}")
        if self.internal_capacity <= 0:
            raise ValueError(f"internal_capacity must be positive, got {self.internal_capacity}")
        if self.initial_level < 0:
            raise ValueError(f"initial_level cannot be negative, got {self.initial_level}")
        if self.initial_level > self.internal_capacity:
            raise ValueError(
                f"initial_level ({self.initial_level}) cannot exceed "
                f"internal_capacity ({self.internal_capacity})"
            )


class FlowState(Enum):
    """Equipment flow states."""

    IDLE = "idle"
    FLOWING = "flowing"
    STARVED_UPSTREAM = "starved_upstream"
    BLOCKED_DOWNSTREAM = "blocked_downstream"
    FAILED = "failed"
    MAINTENANCE = "maintenance"
    CHANGEOVER = "changeover"


@dataclass
class FlowMetrics:
    """Tracks flow metrics for analysis."""

    total_input: float = 0.0
    total_output: float = 0.0
    total_scrap: float = 0.0
    total_downtime: float = 0.0
    state_durations: dict[FlowState, float] = field(default_factory=dict)
    last_state_change: float = 0.0

    def update_state_duration(self, old_state: FlowState, new_time: float) -> None:
        """Update duration tracking for state changes."""
        if old_state not in self.state_durations:
            self.state_durations[old_state] = 0.0
        duration = new_time - self.last_state_change
        self.state_durations[old_state] += duration
        self.last_state_change = new_time


class BaseFlowPrimitive(ABC):
    """Base class for all flow-based primitives."""

    def __init__(
        self,
        env: simpy.Environment,
        config: dict[str, Any],
        flow_capacity: FlowCapacity
    ) -> None:
        """Initialize base flow primitive.

        Args:
            env: SimPy environment
            config: Configuration dictionary
            flow_capacity: Flow capacity constraints
        """
        self.env = env
        self.config = config
        self.flow_capacity = flow_capacity

        # Container buffers for continuous flow
        self.input_buffer: Optional[simpy.Container] = None
        self.output_buffer: Optional[simpy.Container] = None

        # Flow tracking
        self.current_state = FlowState.IDLE
        self.flow_metrics = FlowMetrics()
        self.observables: list[dict[str, Any]] = []

        # Process reference
        self.process: Optional[simpy.Process] = None

    @abstractmethod
    def process_flow(self) -> Generator[Any, None, None]:
        """Main flow processing logic.

        Must be implemented by subclasses to define specific
        flow processing behavior.
        """
        pass

    def start(self) -> None:
        """Start the flow process."""
        if self.process is None:
            self.process = self.env.process(self.process_flow())

    def change_state(self, new_state: FlowState) -> None:
        """Change current state and update metrics.

        Args:
            new_state: New flow state
        """
        if new_state != self.current_state:
            self.flow_metrics.update_state_duration(self.current_state, self.env.now)
            old_state = self.current_state
            self.current_state = new_state

            self.emit_observable("state_change", {
                "old_state": old_state.value,
                "new_state": new_state.value,
                "timestamp": self.env.now
            })

    def emit_observable(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an observable event.

        Args:
            event_type: Type of event
            data: Event data
        """
        observable = {
            "timestamp": self.env.now,
            "equipment_id": self.config.get("id", "unknown"),
            "event_type": event_type,
            **data
        }
        self.observables.append(observable)

        # Trim observables list if it gets too large
        max_observables = self.config.get("max_observables", 10000)
        if len(self.observables) > max_observables:
            self.observables = self.observables[-max_observables:]

    def get_utilization(self) -> float:
        """Calculate equipment utilization.

        Returns:
            Utilization as percentage (0-100)
        """
        if self.env.now == 0:
            return 0.0

        flowing_time = self.flow_metrics.state_durations.get(FlowState.FLOWING, 0.0)
        if self.current_state == FlowState.FLOWING:
            flowing_time += self.env.now - self.flow_metrics.last_state_change

        return (flowing_time / self.env.now) * 100

    def get_availability(self) -> float:
        """Calculate equipment availability.

        Returns:
            Availability as percentage (0-100)
        """
        if self.env.now == 0:
            return 100.0

        failed_time = self.flow_metrics.state_durations.get(FlowState.FAILED, 0.0)
        maintenance_time = self.flow_metrics.state_durations.get(FlowState.MAINTENANCE, 0.0)

        if self.current_state in [FlowState.FAILED, FlowState.MAINTENANCE]:
            downtime_start = self.flow_metrics.last_state_change
            if self.current_state == FlowState.FAILED:
                failed_time += self.env.now - downtime_start
            else:
                maintenance_time += self.env.now - downtime_start

        total_downtime = failed_time + maintenance_time
        return ((self.env.now - total_downtime) / self.env.now) * 100

    def get_performance(self) -> float:
        """Calculate equipment performance.

        Returns:
            Performance as percentage (0-100)
        """
        if self.flow_metrics.total_input == 0:
            return 0.0

        # Performance based on actual vs theoretical throughput
        theoretical_output = self.flow_capacity.max_output_rate * (self.env.now / 60)
        if theoretical_output == 0:
            return 0.0

        return (self.flow_metrics.total_output / theoretical_output) * 100

    def get_quality(self) -> float:
        """Calculate equipment quality.

        Returns:
            Quality as percentage (0-100)
        """
        total_produced = self.flow_metrics.total_output + self.flow_metrics.total_scrap
        if total_produced == 0:
            return 100.0

        return (self.flow_metrics.total_output / total_produced) * 100

    def get_oee(self) -> float:
        """Calculate Overall Equipment Effectiveness.

        Returns:
            OEE as percentage (0-100)
        """
        availability = self.get_availability()
        performance = self.get_performance()
        quality = self.get_quality()

        return (availability * performance * quality) / 10000
