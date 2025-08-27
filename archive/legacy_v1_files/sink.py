"""Sink primitive for product collection in manufacturing.

This module provides a sink primitive that collects finished products
exiting the production system. It tracks throughput, quality metrics,
and delivery performance.
"""

from typing import Optional, Generator, Dict, Any, List
from dataclasses import dataclass, field
import simpy

from .base import BasePrimitive, PrimitiveConfig


@dataclass
class CollectedProduct:
    """Product collected by sink with metadata.

    Attributes:
        product_id: Product identifier
        order_id: Associated production order
        collection_time: Simulation time when collected
        quality: Quality status
        lead_time: Time from order to collection
        metadata: Additional product data
    """

    product_id: str
    order_id: Optional[str]
    collection_time: float
    quality: str = "good"
    lead_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SinkPrimitive(BasePrimitive):
    """Generic sink that collects finished products.

    Emits observables for:
    - Product collection events
    - Throughput metrics
    - Quality statistics
    - Order fulfillment
    - Delivery performance
    """

    def __init__(
        self,
        env: simpy.Environment,
        config: PrimitiveConfig,
        upstream: Optional[Any] = None,
    ) -> None:
        """Initialize sink with configuration.

        Args:
            env: SimPy environment
            config: Sink configuration containing:
                - collection_rate: Maximum collection rate (units/minute)
                - quality_threshold: Minimum quality score for acceptance
                - target_throughput: Expected throughput for KPI
                - order_tracking: Whether to track order fulfillment
            upstream: Input buffer or equipment
        """
        super().__init__(env, config)

        # Connection
        self.upstream = upstream

        # Sink parameters
        self.collection_rate = config.get_property("collection_rate", float("inf"))
        self.quality_threshold = config.get_property("quality_threshold", 0.0)
        self.target_throughput = config.get_property("target_throughput", 50.0)
        self.order_tracking = config.get_property("order_tracking", True)

        # Collection storage
        self.collected_products: List[CollectedProduct] = []

        # Tracking metrics
        self.total_collected = 0
        self.total_rejected = 0
        self.products_by_type: Dict[str, int] = {}
        self.products_by_order: Dict[str, int] = {}

        # Performance metrics
        self.throughput_history: List[float] = []
        self.quality_history: List[float] = []

        # Order fulfillment tracking
        self.pending_orders: Dict[str, Dict[str, Any]] = {}
        self.completed_orders: List[Dict[str, Any]] = []

    def start(self) -> None:
        """Start the sink collection process."""
        self.is_running = True
        self.process = self.env.process(self.collect())
        self.env.process(self.monitor_process())

        self.emit_observable(
            event_type="sink_started",
            details={
                "collection_rate": self.collection_rate,
                "quality_threshold": self.quality_threshold,
                "target_throughput": self.target_throughput,
            },
        )

    def collect(self) -> Generator:
        """Main collection process for products."""
        while self.is_running:
            try:
                # Calculate collection interval based on rate
                if self.collection_rate != float("inf"):
                    collection_time = 1.0 / self.collection_rate
                    yield self.env.timeout(collection_time)

                # Get product from upstream if available
                if self.upstream:
                    if hasattr(self.upstream, "get"):
                        # Get from buffer
                        items = yield from self.upstream.get(1)
                        if items:
                            product_info = items[0] if isinstance(items, list) else items
                            yield from self._process_product(product_info)
                    elif hasattr(self.upstream, "is_empty"):
                        # Check if upstream has products
                        if not self.upstream.is_empty():
                            # Simulate collection
                            yield from self._process_product({"product_id": "UNKNOWN"})
                        else:
                            # Wait if no products available
                            yield self.env.timeout(0.1)
                    else:
                        # Direct collection without buffer
                        yield from self._process_product({"product_id": "DIRECT"})
                else:
                    # No upstream, just track time
                    yield self.env.timeout(1.0)

            except simpy.Interrupt as interrupt:
                # Handle collection interruptions
                yield from self._handle_interrupt(interrupt)

    def _process_product(self, product_info: Any) -> Generator:
        """Process a collected product.

        Args:
            product_info: Product information (dict or BufferItem)
        """
        # Extract product details
        if hasattr(product_info, "product_id"):
            product_id = product_info.product_id
            quality = getattr(product_info, "quality", "good")
            metadata = getattr(product_info, "metadata", {})
        elif isinstance(product_info, dict):
            product_id = product_info.get("product_id", "UNKNOWN")
            quality = product_info.get("quality", "good")
            metadata = product_info
        else:
            product_id = "UNKNOWN"
            quality = "good"
            metadata = {}

        # Quality check
        quality_score = metadata.get("quality_score", 1.0 if quality == "good" else 0.0)

        if quality_score >= self.quality_threshold:
            # Accept product
            order_id = metadata.get("order_id")

            collected = CollectedProduct(
                product_id=product_id,
                order_id=order_id,
                collection_time=self.env.now,
                quality=quality,
                metadata=metadata,
            )

            self.collected_products.append(collected)
            self.total_collected += 1

            # Update product type tracking
            self.products_by_type[product_id] = self.products_by_type.get(product_id, 0) + 1

            # Update order tracking
            if order_id:
                self.products_by_order[order_id] = self.products_by_order.get(order_id, 0) + 1
                yield from self._update_order_fulfillment(order_id, product_id)

            self.emit_observable(
                event_type="product_collected",
                details={
                    "product": product_id,
                    "order": order_id,
                    "quality": quality,
                    "quality_score": quality_score,
                    "total_collected": self.total_collected,
                    "collection_rate": self._calculate_current_rate(),
                },
            )

        else:
            # Reject product
            self.total_rejected += 1

            self.emit_observable(
                event_type="product_rejected",
                details={
                    "product": product_id,
                    "quality_score": quality_score,
                    "threshold": self.quality_threshold,
                    "total_rejected": self.total_rejected,
                },
                severity="WARNING",
            )

        # Small processing time
        yield self.env.timeout(0.01)

    def _update_order_fulfillment(self, order_id: str, product_id: str) -> Generator:
        """Update order fulfillment tracking.

        Args:
            order_id: Production order ID
            product_id: Product ID
        """
        if order_id not in self.pending_orders:
            # New order
            self.pending_orders[order_id] = {
                "start_time": self.env.now,
                "products": {},
                "target_quantity": 1000,  # Would come from manifest
            }

        order = self.pending_orders[order_id]
        order["products"][product_id] = order["products"].get(product_id, 0) + 1

        # Check if order is complete
        total_produced = sum(order["products"].values())
        if total_produced >= order["target_quantity"]:
            # Order complete
            order["end_time"] = self.env.now
            order["lead_time"] = order["end_time"] - order["start_time"]

            self.completed_orders.append(order)
            del self.pending_orders[order_id]

            self.emit_observable(
                event_type="order_completed",
                details={
                    "order_id": order_id,
                    "lead_time": order["lead_time"],
                    "total_quantity": total_produced,
                    "product_mix": order["products"],
                },
            )

        yield self.env.timeout(0)  # No actual delay

    def _handle_interrupt(self, interrupt: simpy.Interrupt) -> Generator:
        """Handle collection interruption.

        Args:
            interrupt: Interruption information
        """
        cause = interrupt.cause if isinstance(interrupt.cause, dict) else {}

        self.emit_observable(
            event_type="collection_interrupted",
            details={
                "reason": cause.get("reason", "unknown"),
                "duration": cause.get("duration", 0),
            },
            severity="WARNING",
        )

        # Wait for interruption to clear
        duration = cause.get("duration", 1.0)
        yield self.env.timeout(duration)

    def monitor_process(self) -> Generator:
        """Background monitoring process."""
        window_size = 5  # 5-minute windows for rate calculation

        while self.is_running:
            # Monitor every 5 minutes
            yield self.env.timeout(window_size)

            # Calculate throughput
            current_rate = self._calculate_current_rate(window_size)
            self.throughput_history.append(current_rate)

            # Calculate quality rate
            recent_products = [p for p in self.collected_products if p.collection_time >= self.env.now - window_size]

            if recent_products:
                quality_rate = sum(1 for p in recent_products if p.quality == "good") / len(recent_products)
            else:
                quality_rate = 0.0

            self.quality_history.append(quality_rate)

            # Check performance against target
            performance = current_rate / self.target_throughput if self.target_throughput > 0 else 0

            self.emit_observable(
                event_type="sink_monitor",
                details={
                    "throughput": current_rate,
                    "target_throughput": self.target_throughput,
                    "performance": performance,
                    "quality_rate": quality_rate,
                    "total_collected": self.total_collected,
                    "total_rejected": self.total_rejected,
                    "pending_orders": len(self.pending_orders),
                    "completed_orders": len(self.completed_orders),
                },
                severity="DEBUG",
            )

            # Alert if below target
            if performance < 0.9:  # Below 90% of target
                self.emit_observable(
                    event_type="throughput_below_target",
                    details={
                        "actual": current_rate,
                        "target": self.target_throughput,
                        "gap": self.target_throughput - current_rate,
                    },
                    severity="WARNING",
                )

    def _calculate_current_rate(self, window: float = 1.0) -> float:
        """Calculate current collection rate.

        Args:
            window: Time window in minutes

        Returns:
            Collection rate (units/minute)
        """
        recent_count = sum(1 for p in self.collected_products if p.collection_time >= self.env.now - window)
        return recent_count / window if window > 0 else 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get sink statistics.

        Returns:
            Dictionary of sink metrics
        """
        total_processed = self.total_collected + self.total_rejected
        acceptance_rate = self.total_collected / total_processed if total_processed > 0 else 0

        avg_throughput = sum(self.throughput_history) / len(self.throughput_history) if self.throughput_history else 0

        avg_quality = sum(self.quality_history) / len(self.quality_history) if self.quality_history else 0

        return {
            "total_collected": self.total_collected,
            "total_rejected": self.total_rejected,
            "acceptance_rate": acceptance_rate,
            "average_throughput": avg_throughput,
            "current_throughput": self._calculate_current_rate(),
            "average_quality": avg_quality,
            "products_by_type": dict(self.products_by_type),
            "completed_orders": len(self.completed_orders),
            "pending_orders": len(self.pending_orders),
            "performance_vs_target": avg_throughput / self.target_throughput if self.target_throughput > 0 else 0,
        }

    def get_order_metrics(self) -> Dict[str, Any]:
        """Get order fulfillment metrics.

        Returns:
            Dictionary of order-related metrics
        """
        if not self.completed_orders:
            return {"orders_completed": 0, "avg_lead_time": 0, "on_time_delivery": 0}

        lead_times = [o["lead_time"] for o in self.completed_orders]
        avg_lead_time = sum(lead_times) / len(lead_times)

        # Consider on-time if lead time < target (would come from manifest)
        target_lead_time = 480  # 8 hours default
        on_time = sum(1 for lt in lead_times if lt <= target_lead_time)
        on_time_rate = on_time / len(lead_times)

        return {
            "orders_completed": len(self.completed_orders),
            "orders_pending": len(self.pending_orders),
            "avg_lead_time": avg_lead_time,
            "min_lead_time": min(lead_times),
            "max_lead_time": max(lead_times),
            "on_time_delivery": on_time_rate,
            "products_by_order": dict(self.products_by_order),
        }
