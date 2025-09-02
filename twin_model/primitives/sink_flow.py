"""Sink flow primitive for collecting finished products and calculating OEE.

This module implements sinks that collect finished products and provide
comprehensive OEE (Overall Equipment Effectiveness) calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator

import simpy

from .base_flow import BaseFlowPrimitive, FlowCapacity, FlowState


@dataclass
class ProductionWindow:
    """Represents a production time window for metrics calculation."""

    timestamp: float
    duration: float
    volume: float
    good_volume: float
    scrap_volume: float
    downtime: float
    product_id: str = "default"

    @property
    def quality_rate(self) -> float:
        """Calculate quality rate for this window."""
        total = self.good_volume + self.scrap_volume
        if total == 0:
            return 1.0
        return self.good_volume / total


@dataclass
class OEEMetrics:
    """OEE metrics for a time period."""

    oee: float
    availability: float
    performance: float
    quality: float
    timestamp: float
    window_duration: float

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "oee": self.oee,
            "availability": self.availability,
            "performance": self.performance,
            "quality": self.quality,
            "timestamp": self.timestamp,
            "window_duration": self.window_duration,
        }


class SinkFlow(BaseFlowPrimitive):
    """Sink collecting finished products and calculating OEE."""

    def __init__(
        self,
        env: simpy.Environment,
        config: dict[str, Any],
        flow_capacity: FlowCapacity,
        collection_rate: float,
        collection_interval: float = 0.1,
    ) -> None:
        """Initialize sink flow.

        Args:
            env: SimPy environment
            config: Configuration dictionary
            flow_capacity: Flow capacity constraints
            collection_rate: Maximum collection rate (units/minute)
            collection_interval: Time between collection attempts (minutes)
        """
        super().__init__(env, config, flow_capacity)
        self.collection_rate = collection_rate
        self.collection_interval = collection_interval
        self.total_collected = 0.0
        self.total_good = 0.0
        self.total_scrap = 0.0

        # Production windows for OEE calculation
        self.production_windows: list[ProductionWindow] = []
        self.current_window_start = 0.0
        self.window_duration = config.get("window_duration", 5.0)  # 5-minute windows

        # OEE history
        self.oee_history: list[OEEMetrics] = []

        # Product tracking
        self.products_collected: dict[str, float] = {}
        self.current_product = config.get("default_product", "default")

        # Nominal rate for performance calculation
        self.nominal_rate = config.get("nominal_rate", collection_rate)

        # Track upstream equipment for quality metrics
        self.upstream_equipment: list[Any] = []

        # Validate rates
        if collection_rate <= 0:
            raise ValueError(f"collection_rate must be positive, got {collection_rate}")
        if collection_interval <= 0:
            raise ValueError(f"collection_interval must be positive, got {collection_interval}")
        if self.nominal_rate <= 0:
            raise ValueError(f"nominal_rate must be positive, got {self.nominal_rate}")

        # Start window tracking
        self.env.process(self.window_tracker())

    def process_flow(self) -> Generator[Any, None, None]:
        """Collect products and track metrics."""
        while True:
            if self.input_buffer:
                available = self.input_buffer.level

                if available > 0:
                    # Calculate collection volume
                    max_collection = self.collection_rate * self.collection_interval
                    volume = min(max_collection, available)

                    # Collect from input
                    yield self.input_buffer.get(volume)
                    self.change_state(FlowState.FLOWING)

                    # Update metrics
                    self.total_collected += volume
                    self.total_good += volume  # Assuming all collected is good
                    self.flow_metrics.total_input += volume

                    # Track by product
                    if self.current_product not in self.products_collected:
                        self.products_collected[self.current_product] = 0.0
                    self.products_collected[self.current_product] += volume

                    # Emit observable
                    self.emit_observable(
                        "products_collected",
                        {
                            "volume": volume,
                            "total": self.total_collected,
                            "rate": volume / self.collection_interval,
                            "product": self.current_product,
                        },
                    )
                else:
                    # No material available
                    self.change_state(FlowState.STARVED_UPSTREAM)
            else:
                # No input buffer configured
                self.change_state(FlowState.IDLE)

            yield self.env.timeout(self.collection_interval)

    def window_tracker(self) -> Generator[Any, None, None]:
        """Track production windows for OEE calculation."""
        while True:
            # Wait for window duration
            yield self.env.timeout(self.window_duration)

            # Create production window
            window = ProductionWindow(
                timestamp=self.current_window_start,
                duration=self.window_duration,
                volume=self._get_window_volume(),
                good_volume=self._get_window_good_volume(),
                scrap_volume=self._get_window_scrap_volume(),
                downtime=self._get_window_downtime(),
                product_id=self.current_product,
            )

            self.production_windows.append(window)

            # Calculate and store OEE
            oee_metrics = self._calculate_window_oee(window)
            self.oee_history.append(oee_metrics)

            # Emit OEE metrics
            self.emit_observable("oee_calculated", oee_metrics.to_dict())

            # Trim history if too long
            max_windows = self.config.get("max_windows", 1000)
            if len(self.production_windows) > max_windows:
                self.production_windows = self.production_windows[-max_windows:]
            if len(self.oee_history) > max_windows:
                self.oee_history = self.oee_history[-max_windows:]

            # Reset window tracking
            self.current_window_start = self.env.now

    def _get_window_volume(self) -> float:
        """Get volume collected in current window."""
        # This is simplified - in production would track per window
        return self.total_collected / max(1, len(self.production_windows) + 1)

    def _get_window_good_volume(self) -> float:
        """Get good volume in current window."""
        return self.total_good / max(1, len(self.production_windows) + 1)

    def _get_window_scrap_volume(self) -> float:
        """Get scrap volume in current window from upstream equipment."""
        # Aggregate scrap from all upstream equipment
        total_scrap = 0.0
        for equipment in self.upstream_equipment:
            if hasattr(equipment, "flow_metrics") and hasattr(equipment.flow_metrics, "total_scrap"):
                total_scrap += equipment.flow_metrics.total_scrap

        # Calculate scrap for this window (approximate)
        if len(self.production_windows) > 0:
            # Use recent scrap rate
            return total_scrap / max(1, len(self.production_windows) + 1)
        else:
            # First window - use all scrap so far
            return total_scrap

    def _get_window_downtime(self) -> float:
        """Get downtime in current window."""
        # Calculate from state durations
        idle_time = self.flow_metrics.state_durations.get(FlowState.IDLE, 0.0)
        starved_time = self.flow_metrics.state_durations.get(FlowState.STARVED_UPSTREAM, 0.0)
        blocked_time = self.flow_metrics.state_durations.get(FlowState.BLOCKED_DOWNSTREAM, 0.0)

        return (idle_time + starved_time + blocked_time) / max(1, len(self.production_windows) + 1)

    def _calculate_window_oee(self, window: ProductionWindow) -> OEEMetrics:
        """Calculate OEE for a production window."""
        # Availability = (Total Time - Downtime) / Total Time
        availability = ((window.duration - window.downtime) / window.duration * 100) if window.duration > 0 else 0
        availability = max(0, min(100, availability))

        # Performance = Actual Rate / Nominal Rate
        actual_rate = window.volume / window.duration if window.duration > 0 else 0
        performance = (actual_rate / self.nominal_rate * 100) if self.nominal_rate > 0 else 0
        performance = max(0, min(100, performance))

        # Quality = Good Output / Total Output (including upstream scrap)
        # Get total scrap from upstream
        total_upstream_scrap = 0.0
        for equipment in self.upstream_equipment:
            if hasattr(equipment, "flow_metrics") and hasattr(equipment.flow_metrics, "total_scrap"):
                total_upstream_scrap += equipment.flow_metrics.total_scrap

        total_output = window.good_volume + total_upstream_scrap
        quality = (window.good_volume / total_output * 100) if total_output > 0 else 100
        quality = max(0, min(100, quality))

        # OEE = Availability × Performance × Quality
        oee = (availability * performance * quality) / 10000

        return OEEMetrics(
            oee=oee,
            availability=availability,
            performance=performance,
            quality=quality,
            timestamp=window.timestamp,
            window_duration=window.duration,
        )

    def calculate_oee(self, window_minutes: float = 60) -> tuple[float, float, float, float]:
        """Calculate OEE components for time window.

        Args:
            window_minutes: Time window in minutes

        Returns:
            Tuple of (OEE, Availability, Performance, Quality) as percentages
        """
        # Use simple calculation if no windows tracked yet
        if not self.production_windows and self.env.now > 0:
            # Simple calculation based on current metrics
            total_time = min(window_minutes, self.env.now)

            # Availability based on upstream equipment (system availability)
            if self.upstream_equipment:
                # Calculate system availability from worst equipment
                min_availability = 100.0
                for equipment in self.upstream_equipment:
                    if hasattr(equipment, "get_availability"):
                        equip_avail = equipment.get_availability()
                        min_availability = min(min_availability, equip_avail)
                availability = min_availability
            else:
                # Fall back to sink's own state if no upstream equipment
                self.flow_metrics.state_durations.get(FlowState.FLOWING, 0.0)
                idle_time = self.flow_metrics.state_durations.get(FlowState.IDLE, 0.0)
                starved_time = self.flow_metrics.state_durations.get(FlowState.STARVED_UPSTREAM, 0.0)
                blocked_time = self.flow_metrics.state_durations.get(FlowState.BLOCKED_DOWNSTREAM, 0.0)

                downtime = idle_time + starved_time + blocked_time
                availability = ((total_time - downtime) / total_time * 100) if total_time > 0 else 100
                availability = max(0, min(100, availability))

            # Performance based on actual vs nominal throughput
            actual_rate = self.total_collected / total_time if total_time > 0 else 0
            performance = (actual_rate / self.nominal_rate * 100) if self.nominal_rate > 0 else 0
            performance = max(0, min(100, performance))

            # Quality - calculate from upstream equipment
            total_good = self.total_collected
            total_scrap = 0.0

            # Aggregate scrap from all upstream equipment
            for equipment in self.upstream_equipment:
                if hasattr(equipment, "flow_metrics") and hasattr(equipment.flow_metrics, "total_scrap"):
                    total_scrap += equipment.flow_metrics.total_scrap

            # Calculate quality
            total_output = total_good + total_scrap
            quality = (total_good / total_output * 100) if total_output > 0 else 100.0
            quality = max(0, min(100, quality))

            # OEE = Availability × Performance × Quality
            oee = (availability * performance * quality) / 10000

            return oee, availability, performance, quality

        # Get data for window
        window_start = max(0, self.env.now - window_minutes)
        window_data = [w for w in self.production_windows if w.timestamp >= window_start]

        if not window_data:
            return 0.0, 0.0, 0.0, 100.0

        # Aggregate window data
        total_time = sum(w.duration for w in window_data)
        total_downtime = sum(w.downtime for w in window_data)
        total_volume = sum(w.volume for w in window_data)
        total_good = sum(w.good_volume for w in window_data)
        total_scrap = sum(w.scrap_volume for w in window_data)

        # Availability = (Total Time - Downtime) / Total Time
        availability = ((total_time - total_downtime) / total_time * 100) if total_time > 0 else 0
        availability = max(0, min(100, availability))

        # Performance = Actual Rate / Nominal Rate
        effective_time = total_time - total_downtime
        nominal_volume = self.nominal_rate * effective_time
        performance = (total_volume / nominal_volume * 100) if nominal_volume > 0 else 0
        performance = max(0, min(100, performance))

        # Quality = Good Output / Total Output
        # Need to get scrap from upstream equipment
        if not total_scrap and self.upstream_equipment:
            for equipment in self.upstream_equipment:
                if hasattr(equipment, "flow_metrics") and hasattr(equipment.flow_metrics, "total_scrap"):
                    total_scrap += equipment.flow_metrics.total_scrap

        total_output = total_good + total_scrap
        quality = (total_good / total_output * 100) if total_output > 0 else 100
        quality = max(0, min(100, quality))

        # OEE = Availability × Performance × Quality
        oee = (availability * performance * quality) / 10000

        return oee, availability, performance, quality

    def get_production_summary(self) -> dict[str, Any]:
        """Get production summary statistics.

        Returns:
            Dictionary with production summary
        """
        oee, availability, performance, quality = self.calculate_oee()

        return {
            "total_collected": self.total_collected,
            "total_good": self.total_good,
            "total_scrap": self.total_scrap,
            "collection_rate": self.total_collected / self.env.now if self.env.now > 0 else 0,
            "products": dict(self.products_collected),
            "oee": {"overall": oee, "availability": availability, "performance": performance, "quality": quality},
            "windows_tracked": len(self.production_windows),
            "current_state": self.current_state.value,
        }

    def set_product(self, product_id: str) -> None:
        """Set current product being collected.

        Args:
            product_id: Product identifier
        """
        if product_id != self.current_product:
            self.emit_observable("product_change", {"old_product": self.current_product, "new_product": product_id})
            self.current_product = product_id
