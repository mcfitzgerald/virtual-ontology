"""Sequential scheduler implementation.

Simple FIFO scheduling algorithm that processes orders in sequence,
respecting line compatibility and basic constraints.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_scheduler import BaseScheduler, OrderStatus, SchedulerConfig, SchedulingConstraints
from .product_manifest import ProductManifest
from .production_scheduler import ProductionOrder

logger = logging.getLogger(__name__)


class SequentialScheduler(BaseScheduler):
    """Sequential FIFO scheduler implementation.

    Schedules orders in priority/FIFO order, respecting line compatibility
    and maintenance windows.
    """

    def __init__(
        self,
        config: Optional[SchedulerConfig] = None,
        constraints: Optional[SchedulingConstraints] = None,
        product_manifest: Optional[ProductManifest] = None,
    ):
        """Initialize sequential scheduler.

        Args:
            config: Scheduler configuration
            constraints: Scheduling constraints
            product_manifest: Product specifications
        """
        # Note: We don't have env here anymore - it will be passed to methods that need it
        self.config = config or SchedulerConfig()
        self.constraints = constraints or SchedulingConstraints()
        self.product_manifest = product_manifest
        self.current_orders: Dict[str, ProductionOrder] = {}
        self.completed_orders: List[ProductionOrder] = []
        self.line_schedules: Dict[str, List[ProductionOrder]] = {}

    def generate_schedule(
        self,
        lines: List[str],
        products: List[str],
        duration: float,
        **kwargs
    ) -> Dict[str, List[ProductionOrder]]:
        """Generate schedule using sequential FIFO algorithm.

        Args:
            lines: List of production line IDs
            products: List of product IDs to schedule
            duration: Planning horizon in minutes
            **kwargs: Additional parameters (orders, horizon_hours, start_time)

        Returns:
            Schedule by line
        """
        # Extract orders from kwargs for backward compatibility
        orders = kwargs.get('orders', [])
        horizon_hours = kwargs.get('horizon_hours')
        start_time = kwargs.get('start_time', 0.0)

        # Sort orders by priority (higher first) then by order ID
        sorted_orders = sorted(orders, key=lambda o: (-o.priority, o.order_id))

        # Initialize schedule for each line
        schedule: Dict[str, List[ProductionOrder]] = {line: [] for line in lines}

        # Track next available time for each line (in minutes)
        line_availability: Dict[str, float] = {line: start_time for line in lines}

        # Track last product on each line for changeover calculation
        last_product_on_line: Dict[str, Optional[str]] = {line: None for line in lines}

        # Schedule each order
        for order in sorted_orders:
            # Find compatible lines
            compatible_lines = self._get_compatible_lines(order.product_id, lines)

            if not compatible_lines:
                logger.warning(f"No compatible lines for product {order.product_id}")
                continue

            # Choose line with earliest availability
            best_line = min(compatible_lines, key=lambda line: line_availability[line])

            # Calculate changeover time if needed
            changeover_time = 0.0
            last_product = last_product_on_line[best_line]
            if last_product and last_product != order.product_id:
                changeover_time = self._calculate_changeover_time(last_product, order.product_id)

            # Update order scheduling information
            order.line_id = best_line
            order.scheduled_start = line_availability[best_line] + changeover_time

            # Calculate duration based on product rate and volume
            if self.product_manifest:
                product = self.product_manifest.get_product(order.product_id)
                if product:
                    # Use nominal rate to calculate duration
                    rate_per_min = product.production.nominal_rate_per_min
                    if rate_per_min > 0:
                        order.scheduled_duration = order.target_volume / rate_per_min
                    else:
                        order.scheduled_duration = self.config.typical_order_duration_hours * 60
                else:
                    order.scheduled_duration = self.config.typical_order_duration_hours * 60
            else:
                # Use config defaults if no manifest
                order.scheduled_duration = self.config.typical_order_duration_hours * 60

            # Apply efficiency factor
            order.scheduled_duration *= 1.0 / self.config.efficiency_factor

            # Add to schedule
            schedule[best_line].append(order)

            # Update line availability and last product
            line_availability[best_line] = order.scheduled_start + order.scheduled_duration
            last_product_on_line[best_line] = order.product_id

            # Check horizon constraint
            if horizon_hours and line_availability[best_line] > (start_time + horizon_hours * 60):
                logger.info(f"Reached planning horizon at {line_availability[best_line]} minutes")
                break

        self.line_schedules = schedule
        return schedule

    def optimize_schedule(
        self, current_schedule: Dict[str, List[ProductionOrder]], objective: str = "minimize_changeover", **kwargs
    ) -> Dict[str, List[ProductionOrder]]:
        """Optimize existing schedule (no-op for sequential scheduler).

        Sequential scheduler doesn't optimize, just returns current schedule.

        Args:
            current_schedule: Current schedule to optimize
            cost_calculator: Cost calculator for evaluation

        Returns:
            Same schedule (no optimization)
        """
        logger.info("Sequential scheduler does not optimize - returning original schedule")
        return current_schedule

    def reschedule(
        self,
        disruption_time: float,
        disruption_type: str,
        affected_resources: List[str],
        **kwargs
    ) -> Dict[str, List[ProductionOrder]]:
        """Reschedule after disruption.

        Args:
            disruption_time: When disruption occurred (simulation time)
            disruption_type: Type of disruption
            affected_resources: Affected lines/resources
            current_schedule: Current schedule

        Returns:
            Updated schedule
        """
        current_schedule = kwargs.get('current_schedule', self.line_schedules)
        logger.info(f"Rescheduling due to {disruption_type} at time {disruption_time}")

        # Collect unfinished orders
        unfinished_orders = []
        for _line_id, orders in current_schedule.items():
            for order in orders:
                if order.scheduled_start > disruption_time:
                    # Order hasn't started yet
                    unfinished_orders.append(order)
                elif order.scheduled_start <= disruption_time < order.scheduled_start + order.scheduled_duration:
                    # Order was in progress - create new order for remaining volume
                    progress = (disruption_time - order.scheduled_start) / order.scheduled_duration
                    remaining_volume = order.target_volume * (1 - progress)

                    if remaining_volume > 0:
                        new_order = ProductionOrder(
                            order_id=f"{order.order_id}_R",
                            product_id=order.product_id,
                            product_name=order.product_name,
                            target_volume=remaining_volume,
                            line_id=order.line_id,
                            scheduled_start=0,  # Will be rescheduled
                            scheduled_duration=1,  # Will be recalculated (set to 1 for validation)
                            priority=order.priority + 1,  # Boost priority
                            status=OrderStatus.PENDING,
                        )
                        unfinished_orders.append(new_order)

        # Get available lines (excluding affected ones temporarily)
        available_lines = [line for line in current_schedule.keys() if line not in affected_resources]

        # Reschedule unfinished orders
        if available_lines:
            return self.generate_schedule(
                orders=unfinished_orders,
                lines=available_lines,
                start_time=disruption_time + 60,  # Add 1 hour buffer for disruption
            )
        else:
            logger.warning("No available lines for rescheduling")
            return current_schedule

    def get_metrics(self) -> Dict[str, Any]:
        """Get scheduler performance metrics.

        Returns:
            Metrics dictionary
        """
        total_orders = sum(len(orders) for orders in self.line_schedules.values())
        total_changeover_time = 0.0

        for _line_id, orders in self.line_schedules.items():
            last_product = None
            for order in orders:
                if last_product and last_product != order.product_id:
                    total_changeover_time += self._calculate_changeover_time(last_product, order.product_id)
                last_product = order.product_id

        metrics = {
            "total_orders_scheduled": total_orders,
            "lines_utilized": len([line for line, orders in self.line_schedules.items() if orders]),
            "total_changeover_time_minutes": total_changeover_time,
            "average_changeover_minutes": (total_changeover_time / total_orders if total_orders > 0 else 0),
        }

        return metrics

    def _get_compatible_lines(self, product_id: str, available_lines: List[str]) -> List[str]:
        """Get lines compatible with product.

        Args:
            product_id: Product ID
            available_lines: List of available lines

        Returns:
            List of compatible lines
        """
        compatible = []

        # Check constraints first
        if self.constraints.product_line_compatibility:
            if product_id in self.constraints.product_line_compatibility:
                allowed = self.constraints.product_line_compatibility[product_id]
                compatible = [line for line in available_lines if line in allowed]

        # If no constraints or no manifest, assume all lines are compatible
        if not compatible and not self.constraints.product_line_compatibility:
            # Check product manifest for line efficiency
            if self.product_manifest:
                product = self.product_manifest.get_product(product_id)
                if product and product.production.efficiency_by_line:
                    # Lines with non-zero efficiency are compatible
                    compatible = [
                        line
                        for line in available_lines
                        if line in product.production.efficiency_by_line
                        and product.production.efficiency_by_line[line] is not None
                        and product.production.efficiency_by_line[line] > 0
                    ]

            # Fall back to all lines if still no compatibility info
            if not compatible:
                compatible = available_lines

        return compatible

    def _calculate_changeover_time(self, from_product: str, to_product: str) -> float:
        """Calculate changeover time between products.

        Args:
            from_product: Current product ID
            to_product: Next product ID

        Returns:
            Changeover time in minutes
        """
        if self.product_manifest:
            return self.product_manifest.get_changeover_time(from_product, to_product)

        # Use config defaults if no manifest
        if from_product == to_product:
            return 0.0

        # Simple heuristic based on product family (first part of SKU)
        from_family = from_product.split("-")[0] if "-" in from_product else from_product
        to_family = to_product.split("-")[0] if "-" in to_product else to_product

        if from_family == to_family:
            return self.config.same_family_changeover_minutes
        else:
            return self.config.different_family_changeover_minutes
