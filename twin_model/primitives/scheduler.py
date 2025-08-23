"""Scheduler primitive for production order management.

This module provides a scheduler primitive that manages production orders,
product changeovers, shift schedules, and maintenance windows. It coordinates
the timing and sequencing of production activities.
"""

from typing import Optional, Generator, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import simpy

from .base import BasePrimitive, PrimitiveConfig


class ScheduleEventType(str, Enum):
    """Types of schedule events."""

    PRODUCTION_ORDER = "PRODUCTION_ORDER"
    CHANGEOVER = "CHANGEOVER"
    MAINTENANCE = "MAINTENANCE"
    SHIFT_CHANGE = "SHIFT_CHANGE"
    BREAK = "BREAK"
    SHUTDOWN = "SHUTDOWN"


@dataclass
class ScheduleEvent:
    """A scheduled event in the production schedule.

    Attributes:
        event_type: Type of scheduled event
        start_time: Scheduled start time (minutes from sim start)
        duration: Expected duration in minutes
        product_id: Product ID for production orders
        order_id: Production order ID
        line_id: Production line affected
        priority: Priority level (lower = higher priority)
        metadata: Additional event-specific data
    """

    event_type: ScheduleEventType
    start_time: float
    duration: float
    product_id: Optional[str] = None
    order_id: Optional[str] = None
    line_id: Optional[str] = None
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: "ScheduleEvent") -> bool:
        """Compare events for priority queue."""
        if self.start_time == other.start_time:
            return self.priority < other.priority
        return self.start_time < other.start_time


@dataclass
class ProductionOrder:
    """Production order details.

    Attributes:
        order_id: Unique order identifier
        product_id: Product to produce
        target_quantity: Target production quantity
        due_time: Due date/time for order completion
        line_id: Assigned production line
        priority: Order priority
        status: Current order status
    """

    order_id: str
    product_id: str
    target_quantity: int
    due_time: float
    line_id: str
    priority: int = 5
    status: str = "pending"
    actual_quantity: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class SchedulerPrimitive(BasePrimitive):
    """Scheduler for coordinating production activities.

    Emits observables for:
    - Order scheduling and completion
    - Changeover events
    - Shift transitions
    - Schedule adherence metrics
    - Order tardiness
    - Resource conflicts
    """

    def __init__(self, env: simpy.Environment, config: PrimitiveConfig) -> None:
        """Initialize scheduler with configuration.

        Args:
            env: SimPy environment
            config: Scheduler configuration containing:
                - schedule_horizon: Planning horizon in minutes
                - changeover_matrix: Product-to-product changeover times
                - shift_schedule: Shift timing configuration
                - maintenance_schedule: Planned maintenance windows
                - optimization_mode: Scheduling algorithm to use
        """
        super().__init__(env, config)

        # Scheduler parameters
        self.schedule_horizon = config.get_property("schedule_horizon", 10080)  # 1 week
        self.changeover_matrix = config.get_property("changeover_matrix", {})
        self.shift_schedule = config.get_property("shift_schedule", {})
        self.maintenance_schedule = config.get_property("maintenance_schedule", [])
        self.optimization_mode = config.get_property("optimization_mode", "FIFO")

        # Schedule storage
        self.schedule_events: List[ScheduleEvent] = []
        self.production_orders: Dict[str, ProductionOrder] = {}
        self.active_order: Optional[ProductionOrder] = None

        # Tracking metrics
        self.orders_scheduled = 0
        self.orders_completed = 0
        self.total_changeover_time: float = 0.0
        self.schedule_adherence = 1.0
        self.tardiness_total: float = 0.0

        # Current state
        self.current_product: Optional[str] = None
        self.current_shift: Optional[str] = None
        self.current_line: Optional[str] = None

        # Registered equipment to control
        self.controlled_equipment: Dict[str, Any] = {}

    def start(self) -> None:
        """Start the scheduler process."""
        self.is_running = True
        self.process = self.env.process(self.schedule_process())
        self.env.process(self.monitor_process())

        # Load initial schedule if provided
        initial_schedule = self.config.get_property("initial_schedule", [])
        if initial_schedule:
            self.load_schedule(initial_schedule)

        self.emit_observable(
            event_type="scheduler_started",
            details={
                "horizon": self.schedule_horizon,
                "optimization_mode": self.optimization_mode,
                "initial_orders": len(self.production_orders),
            },
        )

    def schedule_process(self) -> Generator:
        """Main scheduling process."""
        while self.is_running:
            # Get next scheduled event
            next_event = self._get_next_event()

            if next_event:
                # Wait until event start time
                wait_time = next_event.start_time - self.env.now
                if wait_time > 0:
                    yield self.env.timeout(wait_time)

                # Process the event
                yield from self._process_event(next_event)
            else:
                # No events scheduled, wait
                yield self.env.timeout(1.0)

    def _get_next_event(self) -> Optional[ScheduleEvent]:
        """Get the next scheduled event.

        Returns:
            Next event to process or None
        """
        # Filter future events
        future_events = [e for e in self.schedule_events if e.start_time >= self.env.now]

        if not future_events:
            return None

        # Sort by start time and priority
        future_events.sort()
        return future_events[0]

    def _process_event(self, event: ScheduleEvent) -> Generator:
        """Process a scheduled event.

        Args:
            event: Event to process
        """
        self.emit_observable(
            event_type="schedule_event_started",
            details={
                "event_type": event.event_type.value,
                "order_id": event.order_id,
                "product_id": event.product_id,
                "duration": event.duration,
            },
        )

        if event.event_type == ScheduleEventType.PRODUCTION_ORDER:
            yield from self._process_production_order(event)
        elif event.event_type == ScheduleEventType.CHANGEOVER:
            yield from self._process_changeover(event)
        elif event.event_type == ScheduleEventType.MAINTENANCE:
            yield from self._process_maintenance(event)
        elif event.event_type == ScheduleEventType.SHIFT_CHANGE:
            yield from self._process_shift_change(event)

        # Remove processed event
        if event in self.schedule_events:
            self.schedule_events.remove(event)

    def _process_production_order(self, event: ScheduleEvent) -> Generator:
        """Process a production order event.

        Args:
            event: Production order event
        """
        order_id = event.order_id

        if order_id not in self.production_orders:
            # Create order if not exists
            order = ProductionOrder(
                order_id=order_id or "DEFAULT",
                product_id=event.product_id or "UNKNOWN",
                target_quantity=event.metadata.get("quantity", 1000),
                due_time=event.start_time + event.duration,
                line_id=event.line_id or "LINE1",
            )
            self.production_orders[order_id or "DEFAULT"] = order
        else:
            order = self.production_orders[order_id]

        # Check if changeover needed
        if self.current_product and self.current_product != order.product_id:
            changeover_time = self._get_changeover_time(self.current_product, order.product_id)

            if changeover_time > 0:
                # Schedule changeover first
                yield from self._process_changeover(
                    ScheduleEvent(
                        event_type=ScheduleEventType.CHANGEOVER,
                        start_time=self.env.now,
                        duration=changeover_time,
                        product_id=order.product_id,
                        metadata={
                            "from_product": self.current_product,
                            "to_product": order.product_id,
                        },
                    )
                )

        # Start production
        order.start_time = self.env.now
        order.status = "in_progress"
        self.active_order = order
        self.current_product = order.product_id

        # Configure equipment for this product
        self._configure_equipment_for_product(order.product_id, order.order_id)

        self.emit_observable(
            event_type="order_started",
            details={
                "order_id": order.order_id,
                "product": order.product_id,
                "target_quantity": order.target_quantity,
                "due_time": order.due_time,
                "line": order.line_id,
            },
        )

        # Wait for order duration
        yield self.env.timeout(event.duration)

        # Complete order
        order.end_time = self.env.now
        order.status = "completed"
        self.orders_completed += 1

        # Calculate tardiness
        if order.end_time > order.due_time:
            tardiness = order.end_time - order.due_time
            self.tardiness_total += float(tardiness)

            self.emit_observable(
                event_type="order_tardy",
                details={
                    "order_id": order.order_id,
                    "tardiness": tardiness,
                    "due_time": order.due_time,
                    "completion_time": order.end_time,
                },
                severity="WARNING",
            )

        self.emit_observable(
            event_type="order_completed",
            details={
                "order_id": order.order_id,
                "actual_quantity": order.actual_quantity,
                "target_quantity": order.target_quantity,
                "completion_rate": order.actual_quantity / order.target_quantity if order.target_quantity > 0 else 0,
                "lead_time": order.end_time - order.start_time,
            },
        )

        self.active_order = None

    def _process_changeover(self, event: ScheduleEvent) -> Generator:
        """Process a changeover event.

        Args:
            event: Changeover event
        """
        from_product = event.metadata.get("from_product", self.current_product)
        to_product = event.metadata.get("to_product", event.product_id)

        self.emit_observable(
            event_type="changeover_started",
            details={
                "from_product": from_product,
                "to_product": to_product,
                "duration": event.duration,
                "line": event.line_id,
            },
        )

        # Stop equipment for changeover
        self._stop_equipment_for_changeover()

        # Changeover duration
        yield self.env.timeout(event.duration)

        self.total_changeover_time += float(event.duration)
        self.current_product = to_product

        # Restart equipment with new product
        if to_product:
            self._configure_equipment_for_product(to_product, None)

        self.emit_observable(
            event_type="changeover_completed",
            details={
                "new_product": to_product,
                "changeover_time": event.duration,
                "total_changeover_time": self.total_changeover_time,
            },
        )

    def _process_maintenance(self, event: ScheduleEvent) -> Generator:
        """Process a maintenance event.

        Args:
            event: Maintenance event
        """
        self.emit_observable(
            event_type="maintenance_started",
            details={
                "maintenance_type": event.metadata.get("type", "planned"),
                "duration": event.duration,
                "equipment": event.metadata.get("equipment", []),
            },
        )

        # Stop affected equipment
        for eq_id in event.metadata.get("equipment", []):
            if eq_id in self.controlled_equipment:
                # Trigger maintenance on equipment
                equipment = self.controlled_equipment[eq_id]
                if hasattr(equipment, "process"):
                    equipment.process.interrupt({"type": "maintenance", "duration": event.duration})

        # Maintenance duration
        yield self.env.timeout(event.duration)

        self.emit_observable(event_type="maintenance_completed", details={"duration": event.duration})

    def _process_shift_change(self, event: ScheduleEvent) -> Generator:
        """Process a shift change event.

        Args:
            event: Shift change event
        """
        old_shift = self.current_shift
        new_shift = event.metadata.get("shift_id", "shift1")

        self.current_shift = new_shift

        self.emit_observable(
            event_type="shift_change",
            details={
                "old_shift": old_shift,
                "new_shift": new_shift,
                "handover_duration": event.duration,
            },
        )

        # Update equipment with new shift
        for equipment in self.controlled_equipment.values():
            if hasattr(equipment, "set_shift"):
                equipment.set_shift(new_shift)

        # Handover time
        yield self.env.timeout(event.duration)

    def _get_changeover_time(self, from_product: str, to_product: str) -> float:
        """Get changeover time between products.

        Args:
            from_product: Current product
            to_product: Next product

        Returns:
            Changeover time in minutes
        """
        if not self.changeover_matrix:
            return 30.0  # Default changeover time

        # Check matrix
        if from_product in self.changeover_matrix:
            if to_product in self.changeover_matrix[from_product]:
                return self.changeover_matrix[from_product][to_product]  # type: ignore[no-any-return]

        # Default based on product similarity
        if from_product == to_product:
            return 0.0
        elif from_product[:3] == to_product[:3]:  # Same family
            return 15.0
        else:
            return 45.0  # Different families

    def _configure_equipment_for_product(self, product_id: str, order_id: Optional[str]) -> None:
        """Configure equipment for a specific product.

        Args:
            product_id: Product to configure for
            order_id: Associated order ID
        """
        for equipment in self.controlled_equipment.values():
            if hasattr(equipment, "set_product"):
                equipment.set_product(product_id, order_id)

    def _stop_equipment_for_changeover(self) -> None:
        """Stop equipment for changeover."""
        for equipment in self.controlled_equipment.values():
            if hasattr(equipment, "process"):
                equipment.process.interrupt({"type": "changeover", "duration": 0})

    def register_equipment(self, equipment_id: str, equipment: Any) -> None:
        """Register equipment to be controlled by scheduler.

        Args:
            equipment_id: Equipment identifier
            equipment: Equipment primitive instance
        """
        self.controlled_equipment[equipment_id] = equipment

        self.emit_observable(
            event_type="equipment_registered",
            details={
                "equipment_id": equipment_id,
                "total_registered": len(self.controlled_equipment),
            },
        )

    def add_order(self, order: ProductionOrder) -> None:
        """Add a production order to the schedule.

        Args:
            order: Production order to add
        """
        self.production_orders[order.order_id] = order
        self.orders_scheduled += 1

        # Create schedule event
        event = ScheduleEvent(
            event_type=ScheduleEventType.PRODUCTION_ORDER,
            start_time=self.env.now,  # Or calculate based on optimization
            duration=(order.target_quantity / 60.0),  # Estimate based on rate
            product_id=order.product_id,
            order_id=order.order_id,
            line_id=order.line_id,
            priority=order.priority,
            metadata={"quantity": order.target_quantity},
        )

        self.schedule_events.append(event)

        self.emit_observable(
            event_type="order_added",
            details={
                "order_id": order.order_id,
                "product": order.product_id,
                "quantity": order.target_quantity,
                "due_time": order.due_time,
            },
        )

    def load_schedule(self, schedule_data: List[Dict[str, Any]]) -> None:
        """Load a complete schedule.

        Args:
            schedule_data: List of schedule events
        """
        for event_data in schedule_data:
            event_type = ScheduleEventType(event_data.get("type", "PRODUCTION_ORDER"))

            event = ScheduleEvent(
                event_type=event_type,
                start_time=event_data.get("start_time", 0),
                duration=event_data.get("duration", 60),
                product_id=event_data.get("product_id"),
                order_id=event_data.get("order_id"),
                line_id=event_data.get("line_id"),
                priority=event_data.get("priority", 5),
                metadata=event_data.get("metadata", {}),
            )

            self.schedule_events.append(event)

            # Create order if production order
            if event_type == ScheduleEventType.PRODUCTION_ORDER:
                order = ProductionOrder(
                    order_id=event.order_id or "DEFAULT",
                    product_id=event.product_id or "UNKNOWN",
                    target_quantity=event_data.get("quantity", 1000),
                    due_time=event.start_time + event.duration,
                    line_id=event.line_id or "LINE1",
                    priority=event.priority,
                )
                self.production_orders[order.order_id] = order
                self.orders_scheduled += 1

        self.emit_observable(
            event_type="schedule_loaded",
            details={
                "total_events": len(self.schedule_events),
                "total_orders": self.orders_scheduled,
            },
        )

    def optimize_schedule(self) -> None:
        """Optimize the current schedule based on mode."""
        if self.optimization_mode == "FIFO":
            # First in, first out
            self.schedule_events.sort(key=lambda e: e.start_time)
        elif self.optimization_mode == "SPT":
            # Shortest processing time
            self.schedule_events.sort(key=lambda e: e.duration)
        elif self.optimization_mode == "EDD":
            # Earliest due date
            production_events = [e for e in self.schedule_events if e.event_type == ScheduleEventType.PRODUCTION_ORDER]
            production_events.sort(
                key=lambda e: self.production_orders[e.order_id].due_time
                if e.order_id in self.production_orders
                else float("inf")
            )

        self.emit_observable(
            event_type="schedule_optimized",
            details={
                "mode": self.optimization_mode,
                "total_events": len(self.schedule_events),
            },
        )

    def monitor_process(self) -> Generator:
        """Background monitoring process."""
        while self.is_running:
            # Monitor every 5 minutes
            yield self.env.timeout(5.0)

            # Calculate schedule adherence
            if self.active_order:
                start_time = self.active_order.start_time or 0
                due_time = self.active_order.due_time or self.env.now + 1
                planned_progress = min(
                    1.0,
                    (self.env.now - start_time) / max(1, (due_time - start_time)),
                )
                actual_progress = (
                    self.active_order.actual_quantity / self.active_order.target_quantity
                    if self.active_order.target_quantity > 0
                    else 0
                )

                self.schedule_adherence = actual_progress / planned_progress if planned_progress > 0 else 1.0

            # Calculate metrics
            avg_tardiness = self.tardiness_total / self.orders_completed if self.orders_completed > 0 else 0
            changeover_ratio = self.total_changeover_time / self.env.now if self.env.now > 0 else 0

            self.emit_observable(
                event_type="scheduler_monitor",
                details={
                    "active_order": self.active_order.order_id if self.active_order else None,
                    "current_product": self.current_product,
                    "current_shift": self.current_shift,
                    "orders_scheduled": self.orders_scheduled,
                    "orders_completed": self.orders_completed,
                    "schedule_adherence": self.schedule_adherence,
                    "avg_tardiness": avg_tardiness,
                    "changeover_ratio": changeover_ratio,
                    "pending_events": len(self.schedule_events),
                },
                severity="DEBUG",
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics.

        Returns:
            Dictionary of scheduler metrics
        """
        completion_rate = self.orders_completed / self.orders_scheduled if self.orders_scheduled > 0 else 0
        avg_tardiness = self.tardiness_total / self.orders_completed if self.orders_completed > 0 else 0

        return {
            "orders_scheduled": self.orders_scheduled,
            "orders_completed": self.orders_completed,
            "completion_rate": completion_rate,
            "average_tardiness": avg_tardiness,
            "total_changeover_time": self.total_changeover_time,
            "schedule_adherence": self.schedule_adherence,
            "current_product": self.current_product,
            "active_order": self.active_order.order_id if self.active_order else None,
            "pending_events": len(self.schedule_events),
        }
