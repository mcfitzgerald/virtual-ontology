"""Equipment flow primitive for continuous processing simulation.

This module implements equipment with continuous flow processing using
SimPy Containers, modeling realistic production constraints and failures.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any, Generator

import simpy

from .base_flow import BaseFlowPrimitive, FlowCapacity, FlowState

logger = logging.getLogger(__name__)


@dataclass
class ProcessingParameters:
    """Equipment processing parameters for continuous flow."""

    nominal_rate: float  # units/minute continuous flow rate
    quality_rate: float  # fraction of good output (0-1)
    performance_factor: float  # actual vs nominal (0-1)
    processing_interval: float  # simulation update interval (minutes)
    batch_size: float = 0.0  # deprecated - kept for backward compatibility
    min_flow_threshold: float = 0.01  # minimum flow to avoid numerical issues

    def __post_init__(self) -> None:
        """Validate processing parameters."""
        if self.nominal_rate <= 0:
            raise ValueError(f"nominal_rate must be positive, got {self.nominal_rate}")
        if not 0 <= self.quality_rate <= 1:
            raise ValueError(f"quality_rate must be between 0 and 1, got {self.quality_rate}")
        if not 0 <= self.performance_factor <= 1:
            raise ValueError(f"performance_factor must be between 0 and 1, got {self.performance_factor}")
        if self.processing_interval <= 0:
            raise ValueError(f"processing_interval must be positive, got {self.processing_interval}")
        if self.batch_size > 0:
            logger.warning(f"batch_size parameter is deprecated for continuous flow. Value {self.batch_size} will be ignored.")


@dataclass
class FailureParameters:
    """Equipment failure parameters."""

    mtbf: float  # mean time between failures (minutes)
    mttr: float  # mean time to repair (minutes)
    micro_stop_rate: float  # micro-stops per hour
    micro_stop_duration: float  # average micro-stop duration (seconds)

    def __post_init__(self) -> None:
        """Validate failure parameters."""
        if self.mtbf <= 0:
            raise ValueError(f"mtbf must be positive, got {self.mtbf}")
        if self.mttr <= 0:
            raise ValueError(f"mttr must be positive, got {self.mttr}")
        if self.micro_stop_rate < 0:
            raise ValueError(f"micro_stop_rate cannot be negative, got {self.micro_stop_rate}")
        if self.micro_stop_duration < 0:
            raise ValueError(f"micro_stop_duration cannot be negative, got {self.micro_stop_duration}")


@dataclass
class ChangeoverMatrix:
    """Product changeover matrix with setup times.

    Defines the time required to switch between different products
    on the equipment, supporting both symmetric and asymmetric matrices.
    """

    # Matrix of changeover times: product_from -> product_to -> time (minutes)
    matrix: dict[str, dict[str, float]]
    # Default changeover time if product pair not in matrix
    default_time: float = 30.0
    # Whether to track changeover patterns for optimization
    track_patterns: bool = True
    # Minimum changeover time (safety constraint)
    min_changeover_time: float = 5.0

    def __post_init__(self) -> None:
        """Validate changeover matrix."""
        if self.default_time < 0:
            raise ValueError(f"default_time cannot be negative, got {self.default_time}")
        if self.min_changeover_time < 0:
            raise ValueError(f"min_changeover_time cannot be negative, got {self.min_changeover_time}")

        # Validate matrix entries
        for from_product, to_products in self.matrix.items():
            for to_product, time in to_products.items():
                if time < 0:
                    raise ValueError(f"Changeover time cannot be negative: {from_product} -> {to_product} = {time}")

    def get_changeover_time(self, from_product: str, to_product: str) -> float:
        """Get changeover time between two products.

        Args:
            from_product: Current product
            to_product: Target product

        Returns:
            Changeover time in minutes
        """
        # No changeover needed if same product
        if from_product == to_product:
            return 0.0

        # Check if specific time is defined
        if from_product in self.matrix and to_product in self.matrix[from_product]:
            time = self.matrix[from_product][to_product]
        else:
            time = self.default_time

        # Apply minimum constraint
        return max(time, self.min_changeover_time)


class EquipmentFlow(BaseFlowPrimitive):
    """Equipment with continuous flow processing."""

    def __init__(
        self,
        env: simpy.Environment,
        config: dict[str, Any],
        flow_capacity: FlowCapacity,
        processing: ProcessingParameters,
        failures: FailureParameters,
        changeover_matrix: ChangeoverMatrix | None = None,
    ) -> None:
        """Initialize equipment flow.

        Args:
            env: SimPy environment
            config: Configuration dictionary
            flow_capacity: Flow capacity constraints
            processing: Processing parameters
            failures: Failure parameters
            changeover_matrix: Optional changeover matrix for product changes
        """
        super().__init__(env, config, flow_capacity)
        self.processing = processing
        self.failures = failures
        self.changeover_matrix = changeover_matrix

        # Internal buffer for material accumulation
        self.internal_buffer = simpy.Container(
            env, capacity=flow_capacity.internal_capacity, init=flow_capacity.initial_level
        )

        # State tracking
        self.is_failed = False
        self.is_processing = False
        self.is_changing_over = False
        self.current_product = config.get("default_product", "default")
        self.next_product: str | None = None

        # Changeover tracking
        self.changeover_count = 0
        self.total_changeover_time = 0.0
        self.changeover_history: list[tuple[float, str, str, float]] = []  # (time, from, to, duration)

        # Start failure process if failures are configured
        if failures.mtbf > 0:
            self.env.process(self.failure_process())
        if failures.micro_stop_rate > 0:
            self.env.process(self.micro_stop_process())

    def process_flow(self) -> Generator[Any, None, None]:
        """Process material in continuous flow."""
        while True:
            try:
                # Check if equipment is failed
                if self.is_failed:
                    self.change_state(FlowState.FAILED)
                    yield self.env.timeout(self.processing.processing_interval)
                    continue

                # Check if product change is needed
                if self.next_product and self.next_product != self.current_product:
                    yield self.env.process(self.handle_product_change(self.next_product))
                    self.next_product = None

                # Check if currently changing over
                if self.is_changing_over:
                    yield self.env.timeout(self.processing.processing_interval)
                    continue

                # Calculate continuous flow volume for this interval
                target_volume = (
                    self.processing.nominal_rate
                    * self.processing.processing_interval
                    * self.processing.performance_factor
                )

                # Process any available material continuously
                if self.input_buffer and self.input_buffer.level > 0:
                    # Calculate actual volume to process (continuous flow)
                    actual_volume = min(
                        target_volume,  # Flow rate for this interval
                        self.input_buffer.level,  # Available material
                        self.internal_buffer.capacity - self.internal_buffer.level,  # Buffer space
                    )

                    # Process any positive amount (continuous flow)
                    if actual_volume > 0:
                        # Pull from input
                        yield self.input_buffer.get(actual_volume)
                        logger.debug(f"{self.config.get('name', 'Equipment')}: Processing {actual_volume:.1f} units")

                        # Add to internal buffer
                        yield self.internal_buffer.put(actual_volume)

                        # Process (with time delay)
                        if self.current_state != FlowState.FLOWING:
                            self.change_state(FlowState.FLOWING)
                        self.is_processing = True
                        yield self.env.timeout(self.processing.processing_interval)

                        # Get from internal buffer
                        processed = min(actual_volume, self.internal_buffer.level)
                        yield self.internal_buffer.get(processed)

                        # Apply quality split
                        good_output = processed * self.processing.quality_rate
                        scrap = processed * (1 - self.processing.quality_rate)

                        # Push to output
                        if self.output_buffer:
                            available_space = self.output_buffer.capacity - self.output_buffer.level
                            if available_space >= good_output:
                                yield self.output_buffer.put(good_output)

                                # Track metrics
                                self.flow_metrics.total_input += actual_volume
                                self.flow_metrics.total_output += good_output
                                self.flow_metrics.total_scrap += scrap

                                # Emit observable
                                self.emit_observable(
                                    "flow_processed",
                                    {
                                        "volume_in": actual_volume,
                                        "volume_out": good_output,
                                        "scrap": scrap,
                                        "rate": self.processing.nominal_rate * self.processing.performance_factor,
                                        "state": self.current_state.value,
                                        "product": self.current_product,
                                    },
                                )
                            else:
                                # Blocked downstream
                                if self.current_state != FlowState.BLOCKED_DOWNSTREAM:
                                    self.change_state(FlowState.BLOCKED_DOWNSTREAM)
                                # Return material to internal buffer
                                yield self.internal_buffer.put(processed)
                                yield self.env.timeout(self.processing.processing_interval)
                        else:
                            # No output buffer configured
                            self.flow_metrics.total_input += actual_volume
                            self.flow_metrics.total_output += good_output
                            self.flow_metrics.total_scrap += scrap
                    else:
                        # No material to process this interval
                        if self.current_state != FlowState.IDLE:
                            self.change_state(FlowState.IDLE)
                        yield self.env.timeout(self.processing.processing_interval)
                else:
                    # Starved - no material available
                    if self.current_state != FlowState.STARVED_UPSTREAM:
                        self.change_state(FlowState.STARVED_UPSTREAM)
                    yield self.env.timeout(self.processing.processing_interval)

                self.is_processing = False

            except simpy.Interrupt:
                # Handle interruptions (failures, maintenance, etc.)
                self.is_processing = False

    def failure_process(self) -> Generator[Any, None, None]:
        """Simulate random failures."""
        while True:
            # Wait for next failure
            time_to_failure = random.expovariate(1 / self.failures.mtbf)
            yield self.env.timeout(time_to_failure)

            # Fail the equipment
            self.is_failed = True
            self.change_state(FlowState.FAILED)  # Ensure state is changed
            failure_start = self.env.now

            self.emit_observable("failure_start", {"failure_type": "major", "expected_duration": self.failures.mttr})

            # Repair time
            repair_time = random.expovariate(1 / self.failures.mttr)
            yield self.env.timeout(repair_time)

            # Repair complete
            self.is_failed = False
            self.flow_metrics.total_downtime += repair_time

            self.emit_observable(
                "failure_end", {"failure_type": "major", "actual_duration": self.env.now - failure_start}
            )

    def micro_stop_process(self) -> Generator[Any, None, None]:
        """Simulate micro-stops."""
        while True:
            # Wait for next micro-stop
            time_to_stop = random.expovariate(self.failures.micro_stop_rate / 60)
            yield self.env.timeout(time_to_stop)

            # Only stop if currently processing
            if self.is_processing and not self.is_failed:
                stop_duration = self.failures.micro_stop_duration / 60  # Convert to minutes

                self.emit_observable("micro_stop", {"duration": stop_duration})

                # Brief pause
                yield self.env.timeout(stop_duration)
                self.flow_metrics.total_downtime += stop_duration

    def handle_product_change(self, new_product: str) -> Generator[Any, None, None]:
        """Handle automatic product change using changeover matrix.

        Args:
            new_product: New product to change to
        """
        # Determine changeover time
        if self.changeover_matrix:
            changeover_time = self.changeover_matrix.get_changeover_time(
                self.current_product, new_product
            )
        else:
            # Use default time if no matrix configured
            changeover_time = 30.0

        # Perform changeover if time > 0
        if changeover_time > 0:
            yield self.env.process(self.changeover(new_product, changeover_time))
        else:
            # Immediate switch for same product
            self.current_product = new_product

    def changeover(self, new_product: str, changeover_time: float) -> Generator[Any, None, None]:
        """Perform product changeover.

        Args:
            new_product: New product identifier
            changeover_time: Time required for changeover (minutes)
        """
        old_product = self.current_product
        self.is_changing_over = True
        self.change_state(FlowState.CHANGEOVER)
        changeover_start = self.env.now

        self.emit_observable(
            "changeover_start",
            {"old_product": old_product, "new_product": new_product, "expected_duration": changeover_time},
        )

        yield self.env.timeout(changeover_time)

        self.current_product = new_product
        self.is_changing_over = False
        self.change_state(FlowState.IDLE)

        # Track changeover metrics
        self.changeover_count += 1
        self.total_changeover_time += changeover_time
        self.changeover_history.append((changeover_start, old_product, new_product, changeover_time))

        self.emit_observable(
            "changeover_end",
            {"old_product": old_product, "new_product": new_product, "actual_duration": changeover_time},
        )

    def request_product_change(self, new_product: str) -> None:
        """Request a product change for the next processing cycle.

        Args:
            new_product: Product to change to
        """
        self.next_product = new_product
        logger.info(f"{self.config.get('name', 'Equipment')}: Product change requested from {self.current_product} to {new_product}")

    def get_changeover_metrics(self) -> dict[str, Any]:
        """Get changeover-specific metrics.

        Returns:
            Dictionary of changeover metrics
        """
        metrics = {
            "changeover_count": self.changeover_count,
            "total_changeover_time": self.total_changeover_time,
            "current_product": self.current_product,
            "next_product": self.next_product,
        }

        # Add average changeover time
        if self.changeover_count > 0:
            metrics["avg_changeover_time"] = self.total_changeover_time / self.changeover_count
        else:
            metrics["avg_changeover_time"] = 0.0

        # Add recent changeover history (last 10)
        metrics["recent_changeovers"] = [
            {
                "time": time,
                "from_product": from_prod,
                "to_product": to_prod,
                "duration": duration
            }
            for time, from_prod, to_prod, duration in self.changeover_history[-10:]
        ]

        # Add changeover matrix info if available
        if self.changeover_matrix:
            metrics["has_changeover_matrix"] = True
            metrics["changeover_matrix_default_time"] = self.changeover_matrix.default_time
        else:
            metrics["has_changeover_matrix"] = False

        return metrics
