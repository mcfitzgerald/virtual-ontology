"""
Equipment implementation for SimPy twin model.

Models production equipment with states, failures, and material flow.
All behavior is configuration-driven.
"""

import simpy
import random
from enum import Enum
from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass, field

from .buffer import Buffer
from .config import EquipmentConfig, ActionableParameters


class EquipmentState(Enum):
    """Equipment operational states."""

    RUNNING = "RUNNING"
    STOPPED_FAILURE = "STOPPED_FAILURE"
    STOPPED_MAINTENANCE = "STOPPED_MAINTENANCE"
    STARVED = "STARVED"  # No input material
    BLOCKED = "BLOCKED"  # Output buffer full
    IDLE = "IDLE"


@dataclass
class EquipmentStats:
    """Statistics tracking for equipment.

    Attributes:
        state_durations: Time spent in each state
        units_produced: Total units produced
        units_scrapped: Total units scrapped
        failure_count: Number of failures
        starvation_count: Number of starvation events
        blockage_count: Number of blockage events
        state_history: History of state changes
    """

    state_durations: Dict[EquipmentState, float] = field(
        default_factory=lambda: {state: 0.0 for state in EquipmentState}
    )
    units_produced: int = 0
    units_scrapped: int = 0
    failure_count: int = 0
    starvation_count: int = 0
    blockage_count: int = 0
    state_history: List[tuple[float, EquipmentState]] = field(default_factory=list)


class Equipment:
    """Production equipment with configurable behavior.

    Models a single piece of equipment that processes material from
    upstream buffer to downstream buffer, with failures and quality losses.
    """

    def __init__(
        self,
        env: simpy.Environment,
        config: EquipmentConfig,
        parameters: ActionableParameters,
        upstream_buffer: Optional[Buffer] = None,
        downstream_buffer: Optional[Buffer] = None,
    ):
        """Initialize equipment.

        Args:
            env: SimPy environment
            config: Equipment configuration
            parameters: Actionable parameters for adjustment
            upstream_buffer: Buffer to get materials from
            downstream_buffer: Buffer to put products into
        """
        self.env = env
        self.config = config
        self.parameters = parameters
        self.upstream_buffer = upstream_buffer
        self.downstream_buffer = downstream_buffer

        # State tracking
        self.state = EquipmentState.IDLE
        self.stats = EquipmentStats()
        self._last_state_change = 0.0

        # Calculate adjusted parameters
        self._update_adjusted_parameters()

        # Start processes
        self.production_process = env.process(self._production_loop())
        self.failure_process = env.process(self._failure_loop())

    def _update_adjusted_parameters(self) -> None:
        """Update parameters based on actionable parameters."""
        # Adjust MTBF based on micro_stop_probability
        # Higher micro_stop_probability = more frequent failures
        self.adjusted_mtbf = self.config.mtbf / self.parameters.micro_stop_probability

        # Adjust production rate based on performance_factor
        self.adjusted_rate = self.config.base_rate * self.parameters.performance_factor

        # Adjust scrap rate based on scrap_multiplier
        self.adjusted_scrap_rate = (
            self.config.base_scrap_rate * self.parameters.scrap_multiplier
        )

        # Calculate processing time per unit
        if self.adjusted_rate > 0:
            self.processing_time = 1.0 / self.adjusted_rate  # minutes per unit
        else:
            self.processing_time = float("inf")

    def _change_state(self, new_state: EquipmentState) -> None:
        """Change equipment state and update statistics."""
        current_time = self.env.now

        # Update duration for previous state
        if self.state in self.stats.state_durations:
            duration = current_time - self._last_state_change
            self.stats.state_durations[self.state] += duration

        # Record state change
        self.stats.state_history.append((current_time, new_state))

        # Update state
        self.state = new_state
        self._last_state_change = current_time

        # Update event counters
        if new_state == EquipmentState.STARVED:
            self.stats.starvation_count += 1
        elif new_state == EquipmentState.BLOCKED:
            self.stats.blockage_count += 1
        elif new_state == EquipmentState.STOPPED_FAILURE:
            self.stats.failure_count += 1

    def _production_loop(self) -> Generator[simpy.Event, None, None]:
        """Main production process."""
        while True:
            try:
                # Check if we have upstream material (or are a source)
                if self.upstream_buffer is not None:
                    # Try to get material from upstream
                    if self.upstream_buffer.is_empty():
                        self._change_state(EquipmentState.STARVED)
                        # Wait for material to become available
                        yield self.upstream_buffer.get(1)
                    else:
                        # Get material
                        yield self.upstream_buffer.get(1)

                # Now produce the unit
                yield from self._produce_unit()

            except simpy.Interrupt as interrupt:
                # Handle interruptions (failures, maintenance)
                if interrupt.cause == "failure":
                    self._change_state(EquipmentState.STOPPED_FAILURE)
                    # Repair will be handled by failure process
                elif interrupt.cause == "maintenance":
                    self._change_state(EquipmentState.STOPPED_MAINTENANCE)
                    # Maintenance will be handled externally

    def _produce_unit(self) -> Generator[simpy.Event, None, None]:
        """Produce a single unit."""
        self._change_state(EquipmentState.RUNNING)

        # Process the unit (takes time)
        yield self.env.timeout(self.processing_time)

        # Check for scrap
        if random.random() < self.adjusted_scrap_rate:
            self.stats.units_scrapped += 1
            # Scrapped units don't go to downstream
        else:
            # Good unit produced
            self.stats.units_produced += 1

            # Try to put in downstream buffer
            if self.downstream_buffer:
                if self.downstream_buffer.is_full():
                    self._change_state(EquipmentState.BLOCKED)
                    # Wait for space
                    yield self.downstream_buffer.put(1)
                    self._change_state(EquipmentState.RUNNING)
                else:
                    # Put without blocking
                    yield self.downstream_buffer.put(1)

    def _failure_loop(self) -> Generator[simpy.Event, None, None]:
        """Failure generation process."""
        while True:
            # Wait until next failure (exponential distribution)
            time_to_failure = random.expovariate(1.0 / self.adjusted_mtbf)
            yield self.env.timeout(time_to_failure)

            # Interrupt production
            if self.production_process and self.production_process.is_alive:
                self.production_process.interrupt("failure")

                # Repair time (exponential distribution)
                repair_time = random.expovariate(1.0 / self.config.mttr)
                yield self.env.timeout(repair_time)

                # Resume production
                self._change_state(EquipmentState.IDLE)

    def get_oee_metrics(self) -> Dict[str, float]:
        """Calculate OEE metrics.

        Returns:
            Dictionary with availability, performance, quality, and OEE
        """
        total_time = self.env.now if self.env.now > 0 else 1.0

        # Availability = Running time / Planned time
        running_time = self.stats.state_durations.get(EquipmentState.RUNNING, 0.0)
        planned_time = total_time  # Assuming 24/7 operation
        availability = (running_time / planned_time) * 100 if planned_time > 0 else 0.0

        # Performance = Actual production / (Running time * Ideal rate)
        ideal_production = running_time * self.adjusted_rate
        actual_production = self.stats.units_produced + self.stats.units_scrapped
        performance = (
            (actual_production / ideal_production) * 100
            if ideal_production > 0
            else 0.0
        )

        # Quality = Good units / Total units
        total_units = self.stats.units_produced + self.stats.units_scrapped
        quality = (
            (self.stats.units_produced / total_units) * 100 if total_units > 0 else 0.0
        )

        # OEE = Availability × Performance × Quality
        oee = (
            availability * performance * quality
        ) / 10000  # Convert from percentage³ to percentage

        return {
            "availability": availability,
            "performance": performance,
            "quality": quality,
            "oee": oee,
        }

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get comprehensive statistics summary.

        Returns:
            Dictionary with all equipment statistics
        """
        oee_metrics = self.get_oee_metrics()

        return {
            "equipment_id": self.config.equipment_id,
            "current_state": self.state.value,
            "units_produced": self.stats.units_produced,
            "units_scrapped": self.stats.units_scrapped,
            "failure_count": self.stats.failure_count,
            "starvation_count": self.stats.starvation_count,
            "blockage_count": self.stats.blockage_count,
            "state_durations": {
                state.value: duration
                for state, duration in self.stats.state_durations.items()
            },
            **oee_metrics,
        }
