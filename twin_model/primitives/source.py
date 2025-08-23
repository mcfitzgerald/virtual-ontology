"""Source primitive for material generation in manufacturing.

This module provides a source primitive that generates materials/units
entering the production system. It can model raw material arrival,
customer orders, or other input streams with various arrival patterns.
"""

from typing import Optional, Generator, Dict, Any
from enum import Enum
import random
import simpy

from .base import BasePrimitive, PrimitiveConfig


class ArrivalPattern(str, Enum):
    """Types of arrival patterns for source generation."""

    CONSTANT = "CONSTANT"
    EXPONENTIAL = "EXPONENTIAL"
    NORMAL = "NORMAL"
    BATCH = "BATCH"
    SCHEDULE = "SCHEDULE"
    STOCHASTIC = "STOCHASTIC"


class SourcePrimitive(BasePrimitive):
    """Generic source that generates materials.

    Emits observables for:
    - Material generation events
    - Arrival pattern variations
    - Batch characteristics
    - Supply disruptions
    - Schedule adherence
    """

    def __init__(
        self,
        env: simpy.Environment,
        config: PrimitiveConfig,
        downstream: Optional[Any] = None,
    ) -> None:
        """Initialize source with configuration.

        Args:
            env: SimPy environment
            config: Source configuration containing:
                - arrival_pattern: Type of arrival pattern
                - arrival_rate: Base rate for arrivals (units/minute)
                - batch_size: Size of batches if batch pattern
                - schedule: Arrival schedule if scheduled pattern
                - disruption_probability: Chance of supply disruption
            downstream: Output buffer or equipment
        """
        super().__init__(env, config)

        # Connection
        self.downstream = downstream

        # Source parameters
        self.arrival_pattern = ArrivalPattern(config.get_property("arrival_pattern", "CONSTANT"))
        self.arrival_rate = config.get_property("arrival_rate", 60.0)
        self.batch_size = config.get_property("batch_size", 1)
        self.schedule = config.get_property("schedule", [])
        self.disruption_probability = config.get_property("disruption_probability", 0.01)

        # Product configuration
        self.product_mix = config.get_property("product_mix", {"DEFAULT": 1.0})
        self.current_product = None

        # Tracking metrics
        self.total_generated = 0
        self.total_batches = 0
        self.disruption_count = 0
        self.blocked_count = 0

        # Supply characteristics
        self.quality_rate = config.get_property("quality_rate", 0.98)
        self.supply_variability = config.get_property("supply_variability", 0.1)

    def start(self) -> None:
        """Start the source generation process."""
        self.is_running = True
        self.process = self.env.process(self.generate())

        # Start disruption process if configured
        if self.disruption_probability > 0:
            self.env.process(self.disruption_process())

        self.emit_observable(
            event_type="source_started",
            details={
                "arrival_pattern": self.arrival_pattern.value,
                "arrival_rate": self.arrival_rate,
                "batch_size": self.batch_size,
                "product_mix": self.product_mix,
            },
        )

    def generate(self) -> Generator:
        """Main generation process for materials."""
        while self.is_running:
            try:
                # Get next arrival time based on pattern
                interarrival_time = self._get_interarrival_time()

                # Wait for next arrival
                yield self.env.timeout(interarrival_time)

                # Select product based on mix
                product = self._select_product()

                # Generate batch
                batch_size = self._get_batch_size()

                # Check quality for each item in batch
                good_units = 0
                rejected_units = 0

                for _ in range(batch_size):
                    if random.random() < self.quality_rate:
                        good_units += 1
                    else:
                        rejected_units += 1

                # Send good units downstream if available
                if self.downstream and good_units > 0:
                    # Check if downstream can accept
                    if hasattr(self.downstream, "is_full") and self.downstream.is_full():
                        self.blocked_count += good_units
                        self.emit_observable(
                            event_type="source_blocked",
                            details={
                                "product": product,
                                "units_blocked": good_units,
                                "downstream_id": self.downstream.config.id
                                if hasattr(self.downstream, "config")
                                else None,
                            },
                            severity="WARNING",
                        )
                    else:
                        # Send units downstream
                        if hasattr(self.downstream, "put"):
                            yield from self.downstream.put(good_units, product_id=product)

                        self.total_generated += good_units

                        self.emit_observable(
                            event_type="material_generated",
                            details={
                                "product": product,
                                "batch_size": batch_size,
                                "good_units": good_units,
                                "rejected_units": rejected_units,
                                "quality_rate": self.quality_rate,
                                "total_generated": self.total_generated,
                            },
                        )

                # Track rejected materials
                if rejected_units > 0:
                    self.emit_observable(
                        event_type="material_rejected",
                        details={
                            "product": product,
                            "rejected_units": rejected_units,
                            "reason": "quality_check_failed",
                        },
                        severity="INFO",
                    )

                self.total_batches += 1

            except simpy.Interrupt as interrupt:
                # Handle disruptions
                yield from self._handle_disruption(interrupt)

    def _get_interarrival_time(self) -> float:
        """Calculate time until next arrival based on pattern.

        Returns:
            Interarrival time in minutes
        """
        base_time = 1.0 / self.arrival_rate if self.arrival_rate > 0 else 60.0

        if self.arrival_pattern == ArrivalPattern.CONSTANT:
            return base_time

        elif self.arrival_pattern == ArrivalPattern.EXPONENTIAL:
            # Exponential distribution with mean = base_time
            return random.expovariate(1.0 / base_time)

        elif self.arrival_pattern == ArrivalPattern.NORMAL:
            # Normal distribution with variability
            std_dev = base_time * self.supply_variability
            time = random.gauss(base_time, std_dev)
            return max(0.1, time)  # Ensure positive

        elif self.arrival_pattern == ArrivalPattern.BATCH:
            # Longer time between batches
            return base_time * self.batch_size  # type: ignore[no-any-return]

        elif self.arrival_pattern == ArrivalPattern.SCHEDULE:
            # Use schedule if available
            if self.schedule:
                return self._get_scheduled_time()
            return base_time

        elif self.arrival_pattern == ArrivalPattern.STOCHASTIC:
            # Complex stochastic pattern
            return self._get_stochastic_time(base_time)

        return base_time

    def _get_batch_size(self) -> int:
        """Determine batch size for current generation.

        Returns:
            Number of units in batch
        """
        if self.arrival_pattern == ArrivalPattern.BATCH:
            # Add some variability to batch size
            variation = int(self.batch_size * self.supply_variability)
            return max(1, self.batch_size + random.randint(-variation, variation))  # type: ignore[no-any-return]
        return 1

    def _select_product(self) -> str:
        """Select product based on configured mix.

        Returns:
            Product identifier
        """
        if not self.product_mix:
            return "DEFAULT"

        # Weighted random selection
        products = list(self.product_mix.keys())
        weights = list(self.product_mix.values())

        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1.0 / len(products)] * len(products)

        return random.choices(products, weights=weights)[0]  # type: ignore[no-any-return]

    def _get_scheduled_time(self) -> float:
        """Get next scheduled arrival time.

        Returns:
            Time until next scheduled arrival
        """
        # Find next scheduled time after current time
        current_time = self.env.now

        for scheduled_time in self.schedule:
            if scheduled_time > current_time:
                return scheduled_time - current_time  # type: ignore[no-any-return]

        # If no future schedule, use base rate
        return 1.0 / self.arrival_rate  # type: ignore[no-any-return]

    def _get_stochastic_time(self, base_time: float) -> float:
        """Generate complex stochastic interarrival time.

        Args:
            base_time: Base interarrival time

        Returns:
            Stochastic interarrival time
        """
        # Model time-of-day effects
        hour_of_day = (self.env.now / 60) % 24

        # Peak hours (8am-5pm) have higher rate
        if 8 <= hour_of_day <= 17:
            time_factor = 0.8  # Faster arrivals
        else:
            time_factor = 1.2  # Slower arrivals

        # Add random variation
        variation = random.uniform(0.5, 1.5)

        return base_time * time_factor * variation

    def _handle_disruption(self, interrupt: simpy.Interrupt) -> Generator:
        """Handle supply disruption.

        Args:
            interrupt: Disruption information
        """
        disruption_info = interrupt.cause if isinstance(interrupt.cause, dict) else {}
        duration = disruption_info.get("duration", 30.0)

        self.disruption_count += 1

        self.emit_observable(
            event_type="supply_disruption",
            details={
                "duration": duration,
                "reason": disruption_info.get("reason", "unknown"),
                "impact": "generation_stopped",
            },
            severity="ERROR",
        )

        # Wait for disruption to end (protect against nested interrupts)
        try:
            yield self.env.timeout(duration)
        except simpy.Interrupt:
            # If interrupted during disruption, just continue
            pass

        self.emit_observable(
            event_type="supply_resumed",
            details={"downtime": duration, "total_disruptions": self.disruption_count},
        )

    def disruption_process(self) -> Generator:
        """Background process for random supply disruptions."""
        while self.is_running:
            # Check every 10 minutes
            yield self.env.timeout(10.0)

            if random.random() < self.disruption_probability:
                # Trigger disruption
                duration = random.uniform(10, 60)  # 10-60 minutes

                if self.process and not self.process.triggered:
                    self.process.interrupt({"duration": duration, "reason": "supply_shortage"})

    def set_arrival_rate(self, rate: float) -> None:
        """Dynamically adjust arrival rate.

        Args:
            rate: New arrival rate (units/minute)
        """
        old_rate = self.arrival_rate
        self.arrival_rate = rate

        self.emit_observable(
            event_type="arrival_rate_changed",
            details={
                "old_rate": old_rate,
                "new_rate": rate,
                "change_factor": rate / old_rate if old_rate > 0 else 0,
            },
        )

    def set_product_mix(self, mix: Dict[str, float]) -> None:
        """Update product mix.

        Args:
            mix: Dictionary of product IDs to weights
        """
        self.product_mix = mix

        self.emit_observable(event_type="product_mix_changed", details={"new_mix": mix})

    def get_statistics(self) -> Dict[str, Any]:
        """Get source statistics.

        Returns:
            Dictionary of source metrics
        """
        actual_rate = self.total_generated / self.env.now if self.env.now > 0 else 0

        return {
            "total_generated": self.total_generated,
            "total_batches": self.total_batches,
            "actual_rate": actual_rate,
            "configured_rate": self.arrival_rate,
            "efficiency": actual_rate / self.arrival_rate if self.arrival_rate > 0 else 0,
            "disruption_count": self.disruption_count,
            "blocked_count": self.blocked_count,
            "product_mix": self.product_mix,
        }
