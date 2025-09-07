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
    """Equipment processing parameters."""

    nominal_rate: float  # units/minute at 100% performance
    quality_rate: float  # fraction of good output (0-1)
    performance_factor: float  # actual vs nominal (0-1)
    batch_size: float  # minimum processing batch
    processing_interval: float  # time between batch processing (minutes)

    def __post_init__(self) -> None:
        """Validate processing parameters."""
        if self.nominal_rate <= 0:
            raise ValueError(f"nominal_rate must be positive, got {self.nominal_rate}")
        if not 0 <= self.quality_rate <= 1:
            raise ValueError(f"quality_rate must be between 0 and 1, got {self.quality_rate}")
        if not 0 <= self.performance_factor <= 1:
            raise ValueError(f"performance_factor must be between 0 and 1, got {self.performance_factor}")
        if self.batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {self.batch_size}")
        if self.processing_interval <= 0:
            raise ValueError(f"processing_interval must be positive, got {self.processing_interval}")


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


class EquipmentFlow(BaseFlowPrimitive):
    """Equipment with continuous flow processing."""

    def __init__(
        self,
        env: simpy.Environment,
        config: dict[str, Any],
        flow_capacity: FlowCapacity,
        processing: ProcessingParameters,
        failures: FailureParameters,
    ) -> None:
        """Initialize equipment flow.

        Args:
            env: SimPy environment
            config: Configuration dictionary
            flow_capacity: Flow capacity constraints
            processing: Processing parameters
            failures: Failure parameters
        """
        super().__init__(env, config, flow_capacity)
        self.processing = processing
        self.failures = failures

        # Internal buffer for material accumulation
        self.internal_buffer = simpy.Container(
            env, capacity=flow_capacity.internal_capacity, init=flow_capacity.initial_level
        )

        # State tracking
        self.is_failed = False
        self.is_processing = False
        self.current_product = config.get("default_product", "default")

        # Start failure process if failures are configured
        if failures.mtbf > 0:
            self.env.process(self.failure_process())
        if failures.micro_stop_rate > 0:
            self.env.process(self.micro_stop_process())

    def process_flow(self) -> Generator[Any, None, None]:
        """Process material in continuous batches."""
        while True:
            try:
                # Check if equipment is failed
                if self.is_failed:
                    self.change_state(FlowState.FAILED)
                    yield self.env.timeout(self.processing.processing_interval)
                    continue

                # Calculate batch volume based on rate and interval
                target_volume = (
                    self.processing.nominal_rate
                    * self.processing.processing_interval
                    * self.processing.performance_factor
                )

                # Check material availability
                if self.input_buffer and self.input_buffer.level >= self.processing.batch_size:
                    # Calculate actual volume to process
                    # Use at least batch_size if available, up to target_volume
                    actual_volume = min(
                        max(target_volume, self.processing.batch_size),  # At least batch_size
                        self.input_buffer.level,
                        self.internal_buffer.capacity - self.internal_buffer.level,
                    )

                    if actual_volume >= self.processing.batch_size:
                        # Pull from input
                        yield self.input_buffer.get(actual_volume)
                        logger.debug(f"{self.config.get('name', 'Equipment')}: Processing {actual_volume:.1f} units")

                        # Add to internal buffer
                        yield self.internal_buffer.put(actual_volume)

                        # Process (with time delay)
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
                                    "batch_processed",
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
                        # Not enough material for minimum batch
                        self.change_state(FlowState.STARVED_UPSTREAM)
                        yield self.env.timeout(self.processing.processing_interval)
                else:
                    # Starved - no material to process
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

    def changeover(self, new_product: str, changeover_time: float) -> Generator[Any, None, None]:
        """Perform product changeover.

        Args:
            new_product: New product identifier
            changeover_time: Time required for changeover (minutes)
        """
        old_product = self.current_product
        self.change_state(FlowState.CHANGEOVER)

        self.emit_observable(
            "changeover_start",
            {"old_product": old_product, "new_product": new_product, "expected_duration": changeover_time},
        )

        yield self.env.timeout(changeover_time)

        self.current_product = new_product
        self.change_state(FlowState.IDLE)

        self.emit_observable(
            "changeover_end",
            {"old_product": old_product, "new_product": new_product, "actual_duration": changeover_time},
        )
