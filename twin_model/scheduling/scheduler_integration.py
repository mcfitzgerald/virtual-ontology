"""Integration module for schedulers with SimPy simulation.

Connects scheduling algorithms to the simulation environment,
managing order dispatch and tracking.
"""

import logging
import random
from typing import Any, Dict, List, Optional

import simpy

from ..primitives.source_flow import SourceFlow
from .base_scheduler import BaseScheduler, OrderStatus, SchedulerConfig, SchedulingConstraints
from .campaign_optimizer import CampaignOptimizer
from .cost_calculator import ProductionCostCalculator
from .product_manifest import ProductManifest
from .production_scheduler import ProductionOrder, ProductionScheduler
from .sequential_scheduler import SequentialScheduler

logger = logging.getLogger(__name__)


class SchedulerSimulationBridge:
    """Bridge between schedulers and SimPy simulation.

    Manages the interaction between scheduling algorithms and
    the simulation environment, handling order dispatch and tracking.
    """

    def __init__(
        self,
        env: simpy.Environment,
        scheduler_type: str = "sequential",
        config: Optional[SchedulerConfig] = None,
        constraints: Optional[SchedulingConstraints] = None,
        product_manifest: Optional[ProductManifest] = None,
    ):
        """Initialize scheduler-simulation bridge.

        Args:
            env: SimPy environment
            scheduler_type: Type of scheduler ("sequential", "campaign", "production")
            config: Scheduler configuration
            constraints: Scheduling constraints
            product_manifest: Product specifications
        """
        self.env = env
        self.config = config or SchedulerConfig()
        self.constraints = constraints or SchedulingConstraints()
        self.product_manifest = product_manifest

        # Create scheduler based on type
        self.scheduler = self._create_scheduler(scheduler_type)

        # Cost calculator for optimization
        self.cost_calculator = None
        if product_manifest:
            self.cost_calculator = ProductionCostCalculator(product_manifest)

        # Order tracking
        self.pending_orders: List[ProductionOrder] = []
        self.active_orders: Dict[str, ProductionOrder] = {}
        self.completed_orders: List[ProductionOrder] = []

        # Line sources for order dispatch
        self.line_sources: Dict[str, SourceFlow] = {}

        # Metrics
        self.metrics = {
            "orders_scheduled": 0,
            "orders_dispatched": 0,
            "orders_completed": 0,
            "total_changeover_time": 0.0,
            "total_production_time": 0.0,
            "schedule_updates": 0,
        }

    def _create_scheduler(self, scheduler_type: str) -> BaseScheduler:
        """Create scheduler instance based on type.

        Args:
            scheduler_type: Type of scheduler

        Returns:
            Scheduler instance
        """
        schedulers = {
            "sequential": SequentialScheduler,
            "campaign": CampaignOptimizer,
            "production": ProductionScheduler,
        }

        scheduler_class = schedulers.get(scheduler_type.lower())
        if not scheduler_class:
            logger.warning(f"Unknown scheduler type {scheduler_type}, using sequential")
            scheduler_class = SequentialScheduler

        # Handle ProductionScheduler which needs env
        if scheduler_class == ProductionScheduler:
            return scheduler_class(
                env=self.env, config=self.config, constraints=self.constraints, product_manifest=self.product_manifest
            )
        else:
            return scheduler_class(
                config=self.config, constraints=self.constraints, product_manifest=self.product_manifest
            )

    def register_line_source(self, line_id: str, source: SourceFlow) -> None:
        """Register a source flow for a production line.

        Args:
            line_id: Line identifier
            source: SourceFlow instance for the line
        """
        self.line_sources[line_id] = source
        logger.info(f"Registered source for line {line_id}")

    def generate_orders(
        self, num_orders: int, products: Optional[List[str]] = None, horizon_hours: float = 168
    ) -> List[ProductionOrder]:
        """Generate random production orders.

        Args:
            num_orders: Number of orders to generate
            products: List of product IDs (uses manifest if not provided)
            horizon_hours: Planning horizon in hours

        Returns:
            List of generated orders
        """
        if products is None and self.product_manifest:
            products = list(self.product_manifest.products.keys())
        elif products is None:
            products = ["SKU-1001", "SKU-1002", "SKU-2001", "SKU-2002", "SKU-3001", "SKU-3002"]

        orders = []
        for i in range(num_orders):
            product_id = random.choice(products)

            # Get product details if available
            product_name = product_id
            target_volume = random.randint(5000, 50000)

            if self.product_manifest:
                product = self.product_manifest.get_product(product_id)
                if product:
                    product_name = product.name
                    # Use typical batch size if available
                    if product.constraints.optimal_batch_size > 0:
                        # Vary around optimal batch size
                        target_volume = int(product.constraints.optimal_batch_size * random.uniform(0.5, 1.5))

            order = ProductionOrder(
                order_id=f"ORD-{i+1:04d}",
                product_id=product_id,
                product_name=product_name,
                target_volume=target_volume,
                line_id="TBD",  # Will be assigned by scheduler
                scheduled_start=0,  # Will be assigned by scheduler
                scheduled_duration=1,  # Will be calculated by scheduler (set to 1 to pass validation)
                priority=random.randint(self.config.min_priority, self.config.max_priority),
                status=OrderStatus.PENDING,
            )
            orders.append(order)

        self.pending_orders.extend(orders)
        return orders

    def schedule_orders(
        self,
        orders: Optional[List[ProductionOrder]] = None,
        horizon_hours: Optional[float] = None,
        optimize: bool = True,
    ) -> Dict[str, List[ProductionOrder]]:
        """Schedule production orders.

        Args:
            orders: Orders to schedule (uses pending orders if not provided)
            horizon_hours: Planning horizon
            optimize: Whether to optimize the schedule

        Returns:
            Schedule by line
        """
        if orders is None:
            orders = self.pending_orders

        if not orders:
            logger.warning("No orders to schedule")
            return {}

        # Get available lines
        lines = list(self.line_sources.keys())
        if not lines:
            logger.error("No production lines registered")
            return {}

        # Generate initial schedule
        schedule = self.scheduler.generate_schedule(
            orders=orders, lines=lines, horizon_hours=horizon_hours, start_time=self.env.now
        )

        # Optimize if requested and cost calculator available
        if optimize and self.cost_calculator:
            logger.info("Optimizing schedule...")
            schedule = self.scheduler.optimize_schedule(current_schedule=schedule, cost_calculator=self.cost_calculator)

        # Update metrics
        self.metrics["orders_scheduled"] += sum(len(o) for o in schedule.values())
        self.metrics["schedule_updates"] += 1

        # Log schedule summary
        for line_id, line_orders in schedule.items():
            if line_orders:
                logger.info(f"Line {line_id}: {len(line_orders)} orders scheduled")
                first_start = line_orders[0].scheduled_start
                last_end = line_orders[-1].scheduled_start + line_orders[-1].scheduled_duration
                logger.info(f"  Time span: {first_start:.1f} - {last_end:.1f} minutes")

        return schedule

    def dispatch_schedule(self, schedule: Dict[str, List[ProductionOrder]]) -> None:
        """Dispatch scheduled orders to production lines.

        Args:
            schedule: Schedule to dispatch
        """
        for line_id, orders in schedule.items():
            if line_id not in self.line_sources:
                logger.error(f"No source registered for line {line_id}")
                continue

            source = self.line_sources[line_id]

            # Convert to source-compatible orders
            for order in orders:
                # Create order for source
                source_order = {
                    "order_id": order.order_id,
                    "product_id": order.product_id,
                    "target_volume": order.target_volume,
                    "due_time": order.scheduled_start + order.scheduled_duration,
                    "priority": order.priority,
                }

                # Add to source's order queue
                source.add_order(source_order)

                # Track order
                self.active_orders[order.order_id] = order
                order.status = OrderStatus.IN_PROGRESS
                self.metrics["orders_dispatched"] += 1

                logger.info(
                    f"Dispatched {order.order_id} ({order.product_id}) "
                    f"to {line_id} at time {order.scheduled_start:.1f}"
                )

    def run_scheduled_production(self, duration_hours: float = 168) -> None:
        """Run production according to schedule.

        This is a SimPy process that manages scheduled production.

        Args:
            duration_hours: Duration to run production
        """
        end_time = self.env.now + duration_hours * 60

        while self.env.now < end_time:
            # Check for orders to start
            for order_id, order in self.active_orders.items():
                if order.status == OrderStatus.IN_PROGRESS and order.scheduled_start <= self.env.now:
                    # Order should be running - check if complete
                    expected_end = order.scheduled_start + order.scheduled_duration
                    if self.env.now >= expected_end:
                        order.status = OrderStatus.COMPLETED
                        order.actual_end = self.env.now
                        self.completed_orders.append(order)
                        self.metrics["orders_completed"] += 1
                        logger.info(f"Order {order_id} completed at time {self.env.now:.1f}")

            # Remove completed orders from active
            self.active_orders = {oid: o for oid, o in self.active_orders.items() if o.status != OrderStatus.COMPLETED}

            # Wait before next check
            yield self.env.timeout(5)  # Check every 5 minutes

    def handle_disruption(
        self, disruption_type: str, affected_lines: List[str], duration_minutes: float = 60
    ) -> Dict[str, List[ProductionOrder]]:
        """Handle production disruption by rescheduling.

        Args:
            disruption_type: Type of disruption
            affected_lines: Affected production lines
            duration_minutes: Expected disruption duration

        Returns:
            Updated schedule
        """
        logger.warning(f"Disruption {disruption_type} affecting {affected_lines} " f"at time {self.env.now:.1f}")

        # Get current schedule state
        current_schedule = {}
        for line_id in self.line_sources.keys():
            line_orders = [
                o for o in self.active_orders.values() if o.line_id == line_id and o.status != OrderStatus.COMPLETED
            ]
            current_schedule[line_id] = sorted(line_orders, key=lambda o: o.scheduled_start)

        # Reschedule
        new_schedule = self.scheduler.reschedule(
            disruption_time=self.env.now,
            disruption_type=disruption_type,
            affected_resources=affected_lines,
            current_schedule=current_schedule,
        )

        # Update active orders with new schedule
        for line_id, orders in new_schedule.items():
            for order in orders:
                if order.order_id in self.active_orders:
                    self.active_orders[order.order_id] = order

        self.metrics["schedule_updates"] += 1
        return new_schedule

    def get_schedule_metrics(self) -> Dict[str, Any]:
        """Get comprehensive scheduling metrics.

        Returns:
            Metrics dictionary
        """
        metrics = self.metrics.copy()

        # Add scheduler-specific metrics
        scheduler_metrics = self.scheduler.get_metrics()
        metrics.update(scheduler_metrics)

        # Calculate KPIs
        if metrics["orders_scheduled"] > 0:
            metrics["completion_rate"] = metrics["orders_completed"] / metrics["orders_scheduled"] * 100

        # Calculate costs if available
        if self.cost_calculator and hasattr(self.scheduler, "line_schedules"):
            schedule_cost = self.cost_calculator.calculate_schedule_cost(self.scheduler.line_schedules)
            metrics["total_cost"] = schedule_cost["total_cost"]
            metrics["cost_per_order"] = (
                schedule_cost["total_cost"] / metrics["orders_scheduled"] if metrics["orders_scheduled"] > 0 else 0
            )

        return metrics

    def export_schedule(self, filename: str = "schedule.csv") -> None:
        """Export current schedule to CSV file.

        Args:
            filename: Output filename
        """
        import csv

        with open(filename, "w", newline="") as csvfile:
            fieldnames = [
                "order_id",
                "product_id",
                "product_name",
                "line_id",
                "scheduled_start",
                "scheduled_duration",
                "target_volume",
                "priority",
                "status",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for order in self.active_orders.values():
                writer.writerow(
                    {
                        "order_id": order.order_id,
                        "product_id": order.product_id,
                        "product_name": order.product_name,
                        "line_id": order.line_id,
                        "scheduled_start": order.scheduled_start,
                        "scheduled_duration": order.scheduled_duration,
                        "target_volume": order.target_volume,
                        "priority": order.priority,
                        "status": order.status.value,
                    }
                )

        logger.info(f"Schedule exported to {filename}")
