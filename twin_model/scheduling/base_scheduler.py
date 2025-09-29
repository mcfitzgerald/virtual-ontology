"""Base scheduler abstract class for production scheduling.

This module provides the abstract interface for production schedulers,
enabling different scheduling algorithms to be plugged in.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import simpy

if TYPE_CHECKING:
    from .production_scheduler import ProductionOrder

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Production order status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class SchedulerConfig:
    """Configuration for scheduler behavior."""

    # Scheduling parameters
    min_order_duration_hours: float = 2.0
    max_order_duration_hours: float = 8.0
    typical_order_duration_hours: float = 4.0
    efficiency_factor: float = 0.7  # Account for downtime/inefficiency

    # Priority settings
    min_priority: int = 1
    max_priority: int = 10
    default_priority: int = 5

    # Changeover settings
    same_family_changeover_minutes: float = 15.0
    different_family_changeover_minutes: float = 30.0
    cleaning_changeover_minutes: float = 45.0

    # Optimization settings
    allow_preemption: bool = False
    allow_splitting: bool = False
    maximize_campaign_length: bool = True


@dataclass
class SchedulingConstraints:
    """Constraints for scheduling decisions."""

    # Time constraints
    horizon_hours: Optional[float] = None
    maintenance_windows: Optional[List[tuple[float, float]]] = None  # List of (start, end) times

    # Product constraints
    product_line_compatibility: Optional[Dict[str, List[str]]] = None  # product -> allowed lines
    line_product_restrictions: Optional[Dict[str, List[str]]] = None  # line -> allowed products

    # Sequence constraints
    forbidden_sequences: Optional[List[tuple[str, str]]] = None  # List of (from_product, to_product)
    preferred_sequences: Optional[List[tuple[str, str]]] = None  # List of (from_product, to_product)

    # Resource constraints
    max_concurrent_orders: Optional[int] = None
    min_campaign_length: Optional[float] = None  # Minimum hours for a product campaign
    max_campaign_length: Optional[float] = None  # Maximum hours for a product campaign


class BaseScheduler(ABC):
    """Abstract base class for production schedulers.

    This class defines the interface that all scheduling algorithms must implement,
    allowing for different scheduling strategies to be used interchangeably.
    """

    def __init__(
        self,
        env: simpy.Environment,
        config: Optional[SchedulerConfig] = None,
        constraints: Optional[SchedulingConstraints] = None,
    ):
        """Initialize base scheduler.

        Args:
            env: SimPy environment
            config: Scheduler configuration
            constraints: Scheduling constraints
        """
        self.env = env
        self.config = config or SchedulerConfig()
        self.constraints = constraints or SchedulingConstraints()

        # Order tracking
        self.orders: Dict[str, ProductionOrder] = {}
        self.line_schedules: Dict[str, List[ProductionOrder]] = {}

        # Statistics
        self.total_orders_created = 0
        self.total_orders_completed = 0
        self.total_changeover_time = 0.0

    @abstractmethod
    def generate_schedule(
        self, lines: List[str], products: List[str], duration: float, **kwargs
    ) -> Dict[str, List["ProductionOrder"]]:
        """Generate production schedule for given lines and products.

        Args:
            lines: List of production line IDs
            products: List of product IDs to schedule
            duration: Planning horizon in minutes
            **kwargs: Additional algorithm-specific parameters

        Returns:
            Dictionary mapping line IDs to ordered lists of production orders
        """
        pass

    @abstractmethod
    def optimize_schedule(
        self, current_schedule: Dict[str, List["ProductionOrder"]], objective: str = "minimize_changeover", **kwargs
    ) -> Dict[str, List["ProductionOrder"]]:
        """Optimize an existing schedule based on given objective.

        Args:
            current_schedule: Current schedule to optimize
            objective: Optimization objective (e.g., 'minimize_changeover', 'maximize_throughput')
            **kwargs: Additional optimization parameters

        Returns:
            Optimized schedule
        """
        pass

    @abstractmethod
    def reschedule(
        self, disruption_time: float, disruption_type: str, affected_resources: List[str], **kwargs
    ) -> Dict[str, List["ProductionOrder"]]:
        """Reschedule production after a disruption.

        Args:
            disruption_time: Time when disruption occurred
            disruption_type: Type of disruption (e.g., 'equipment_failure', 'material_shortage')
            affected_resources: List of affected line/equipment IDs
            **kwargs: Additional disruption details

        Returns:
            Updated schedule
        """
        pass

    def validate_schedule(self, schedule: Dict[str, List["ProductionOrder"]]) -> tuple[bool, List[str]]:
        """Validate that a schedule meets all constraints.

        Args:
            schedule: Schedule to validate

        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []

        # Check product-line compatibility
        if self.constraints.product_line_compatibility:
            for line_id, orders in schedule.items():
                for order in orders:
                    allowed_lines = self.constraints.product_line_compatibility.get(order.product_id, [])
                    if allowed_lines and line_id not in allowed_lines:
                        violations.append(f"Product {order.product_id} not allowed on line {line_id}")

        # Check forbidden sequences
        if self.constraints.forbidden_sequences:
            for line_id, orders in schedule.items():
                for i in range(len(orders) - 1):
                    sequence = (orders[i].product_id, orders[i + 1].product_id)
                    if sequence in self.constraints.forbidden_sequences:
                        violations.append(f"Forbidden sequence {sequence[0]} -> {sequence[1]} on line {line_id}")

        # Check maintenance windows
        if self.constraints.maintenance_windows:
            for line_id, orders in schedule.items():
                for order in orders:
                    order_start = order.scheduled_start
                    order_end = order.scheduled_start + order.scheduled_duration

                    for maint_start, maint_end in self.constraints.maintenance_windows:
                        if not (order_end <= maint_start or order_start >= maint_end):
                            violations.append(
                                f"Order {order.order_id} conflicts with maintenance window "
                                f"[{maint_start}, {maint_end}]"
                            )

        # Check campaign length constraints
        if self.constraints.min_campaign_length or self.constraints.max_campaign_length:
            for line_id, orders in schedule.items():
                current_product = None
                campaign_start = 0.0

                for i, order in enumerate(orders):
                    if order.product_id != current_product:
                        # New campaign starting
                        if current_product and i > 0:
                            # Check previous campaign length
                            campaign_duration = order.scheduled_start - campaign_start
                            campaign_hours = campaign_duration / 60.0

                            if (
                                self.constraints.min_campaign_length
                                and campaign_hours < self.constraints.min_campaign_length
                            ):
                                violations.append(
                                    f"Campaign for {current_product} on line {line_id} "
                                    f"too short ({campaign_hours:.1f} hours)"
                                )

                            if (
                                self.constraints.max_campaign_length
                                and campaign_hours > self.constraints.max_campaign_length
                            ):
                                violations.append(
                                    f"Campaign for {current_product} on line {line_id} "
                                    f"too long ({campaign_hours:.1f} hours)"
                                )

                        current_product = order.product_id
                        campaign_start = order.scheduled_start

        is_valid = len(violations) == 0
        return is_valid, violations

    def calculate_metrics(self, schedule: Dict[str, List["ProductionOrder"]]) -> Dict[str, Any]:
        """Calculate metrics for a schedule.

        Args:
            schedule: Schedule to analyze

        Returns:
            Dictionary of metrics
        """
        metrics: Dict[str, Any] = {
            "total_orders": 0,
            "total_production_time": 0.0,
            "total_changeover_time": 0.0,
            "total_idle_time": 0.0,
            "line_utilization": {},
            "product_volumes": {},
            "changeover_count": 0,
            "average_campaign_length": 0.0,
        }

        campaign_lengths = []

        for line_id, orders in schedule.items():
            line_production_time = 0.0
            line_changeover_time = 0.0
            line_idle_time = 0.0
            last_end_time = 0.0
            current_product = None
            campaign_start = 0.0

            for order in orders:
                # Count orders
                metrics["total_orders"] += 1

                # Track idle time
                if order.scheduled_start > last_end_time:
                    idle = order.scheduled_start - last_end_time
                    line_idle_time += idle

                # Track production time
                line_production_time += order.scheduled_duration

                # Track changeovers and campaigns
                if current_product and current_product != order.product_id:
                    # Changeover detected
                    metrics["changeover_count"] += 1
                    changeover_time = self._estimate_changeover_time(current_product, order.product_id)
                    line_changeover_time += changeover_time

                    # Record campaign length
                    campaign_duration = order.scheduled_start - campaign_start
                    campaign_lengths.append(campaign_duration / 60.0)  # Convert to hours

                    campaign_start = order.scheduled_start

                if not current_product:
                    campaign_start = order.scheduled_start

                current_product = order.product_id
                last_end_time = order.scheduled_start + order.scheduled_duration

                # Track product volumes
                if order.product_id not in metrics["product_volumes"]:
                    metrics["product_volumes"][order.product_id] = 0.0
                metrics["product_volumes"][order.product_id] += order.target_volume

            # Calculate line utilization
            total_time = last_end_time if last_end_time > 0 else 1.0
            utilization = (line_production_time / total_time) * 100 if total_time > 0 else 0
            metrics["line_utilization"][line_id] = utilization

            # Accumulate totals
            metrics["total_production_time"] += line_production_time
            metrics["total_changeover_time"] += line_changeover_time
            metrics["total_idle_time"] += line_idle_time

        # Calculate average campaign length
        if campaign_lengths:
            metrics["average_campaign_length"] = sum(campaign_lengths) / len(campaign_lengths)

        return metrics

    def _estimate_changeover_time(self, from_product: str, to_product: str) -> float:
        """Estimate changeover time between products.

        Args:
            from_product: Current product ID
            to_product: Next product ID

        Returns:
            Estimated changeover time in minutes
        """
        if from_product == to_product:
            return 0.0

        # Check if products are in same family (simple heuristic: same prefix)
        if from_product[:7] == to_product[:7]:
            return self.config.same_family_changeover_minutes
        else:
            return self.config.different_family_changeover_minutes

    def export_schedule(self, schedule: Dict[str, List["ProductionOrder"]], format: str = "dict") -> Any:
        """Export schedule in specified format.

        Args:
            schedule: Schedule to export
            format: Export format ('dict', 'json', 'gantt')

        Returns:
            Schedule in requested format
        """
        if format == "dict":
            return schedule
        elif format == "json":
            # Convert to JSON-serializable format
            json_schedule = {}
            for line_id, orders in schedule.items():
                json_schedule[line_id] = [
                    {
                        "order_id": o.order_id,
                        "product_id": o.product_id,
                        "start": o.scheduled_start,
                        "duration": o.scheduled_duration,
                        "volume": o.target_volume,
                        "priority": o.priority,
                    }
                    for o in orders
                ]
            return json_schedule
        elif format == "gantt":
            # Format for Gantt chart visualization
            gantt_data = []
            for line_id, orders in schedule.items():
                for order in orders:
                    gantt_data.append(
                        {
                            "task": f"{line_id}-{order.product_id}",
                            "start": order.scheduled_start,
                            "finish": order.scheduled_start + order.scheduled_duration,
                            "resource": line_id,
                            "product": order.product_id,
                            "volume": order.target_volume,
                        }
                    )
            return gantt_data
        else:
            raise ValueError(f"Unknown export format: {format}")
