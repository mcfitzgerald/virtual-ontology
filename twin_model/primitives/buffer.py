"""Buffer primitive for material storage between equipment.

This module provides a buffer primitive that represents material storage
locations (queues, conveyors, accumulation tables) between processing equipment.
It emits observables about material flow, levels, and dwell times.
"""

from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass, field
import simpy

from .base import BasePrimitive, PrimitiveConfig


@dataclass
class BufferItem:
    """Item stored in buffer with metadata for tracking.

    Attributes:
        product_id: Product identifier
        entry_time: Simulation time when item entered buffer
        quality: Quality status (good/scrap)
        metadata: Additional item-specific data
    """

    product_id: str
    entry_time: float
    quality: str = "good"
    metadata: Dict[str, Any] = field(default_factory=dict)


class BufferPrimitive(BasePrimitive):
    """Generic buffer for material storage.

    Emits observables for:
    - Level changes (material in/out)
    - Dwell time distribution
    - Overflow/underflow events
    - Capacity utilization patterns
    - Product mix in buffer
    """

    def __init__(self, env: simpy.Environment, config: PrimitiveConfig) -> None:
        """Initialize buffer with configuration.

        Args:
            env: SimPy environment
            config: Buffer configuration containing:
                - capacity: Maximum buffer capacity (units)
                - initial_level: Starting inventory level
                - buffer_type: Type of buffer (FIFO, LIFO, priority)
                - min_level: Minimum level for warnings
                - max_dwell_time: Maximum allowed dwell time
        """
        super().__init__(env, config)

        # Buffer parameters
        self.capacity = config.get_property("capacity", 100)
        self.initial_level = config.get_property("initial_level", 0)
        self.buffer_type = config.get_property("buffer_type", "FIFO")
        self.min_level = config.get_property("min_level", 10)
        self.max_dwell_time = config.get_property("max_dwell_time", 60.0)  # minutes

        # Create appropriate SimPy store based on type
        if self.buffer_type == "FIFO":
            self.store = simpy.Store(env, capacity=self.capacity)
        elif self.buffer_type == "LIFO":
            self.store = simpy.Store(env, capacity=self.capacity)  # SimPy doesn't have LifoStore, use FIFO
        elif self.buffer_type == "priority":
            self.store = simpy.PriorityStore(env, capacity=self.capacity)
        else:
            self.store = simpy.Store(env, capacity=self.capacity)

        # Tracking metrics
        self.total_items_in = 0
        self.total_items_out = 0
        self.max_level_reached = 0
        self.min_level_reached = self.initial_level
        self.overflow_count = 0
        self.underflow_count = 0

        # Dwell time tracking
        self.dwell_times: List[float] = []

        # Current state
        self.level = self.initial_level
        self.last_level_change = 0.0

        # Product mix tracking
        self.product_counts: Dict[str, int] = {}

    def start(self) -> None:
        """Start buffer monitoring processes."""
        self.is_running = True

        # Initialize with initial inventory
        if self.initial_level > 0:
            for _ in range(self.initial_level):
                item = BufferItem(product_id="INITIAL", entry_time=0.0)
                self.store.put(item)

        # Start monitoring process
        self.env.process(self.monitor_process())

        self.emit_observable(
            event_type="buffer_started",
            details={
                "capacity": self.capacity,
                "initial_level": self.initial_level,
                "buffer_type": self.buffer_type,
            },
        )

    def put(self, quantity: int = 1, product_id: Optional[str] = None, **kwargs) -> Generator:
        """Put items into buffer.

        Args:
            quantity: Number of items to add
            product_id: Product identifier
            **kwargs: Additional item metadata

        Yields:
            Store put event
        """
        for _ in range(quantity):
            # Check for overflow
            if len(self.store.items) >= self.capacity:
                self.overflow_count += 1
                self.emit_observable(
                    event_type="buffer_overflow",
                    details={
                        "current_level": len(self.store.items),
                        "capacity": self.capacity,
                        "product": product_id,
                    },
                    severity="WARNING",
                )
                # Wait for space
                while len(self.store.items) >= self.capacity:
                    yield self.env.timeout(0.1)

            # Create item with metadata
            item = BufferItem(
                product_id=product_id or "UNKNOWN",
                entry_time=self.env.now,
                metadata=kwargs,
            )

            # Put item in store
            yield self.store.put(item)

            # Update tracking
            self.total_items_in += 1
            self.level = len(self.store.items)
            self.max_level_reached = max(self.max_level_reached, self.level)

            # Track product mix
            if product_id:
                self.product_counts[product_id] = self.product_counts.get(product_id, 0) + 1

            # Emit observable
            self.emit_observable(
                event_type="buffer_put",
                details={
                    "level": self.level,
                    "product": product_id,
                    "utilization": self.level / self.capacity,
                },
            )

    def get(self, quantity: int = 1) -> Any:  # Returns Generator but yields items list
        """Get items from buffer.

        Args:
            quantity: Number of items to retrieve

        Yields:
            Store get event

        Returns:
            List of retrieved items
        """
        items: List[BufferItem] = []

        for _ in range(quantity):
            # Check for underflow
            if len(self.store.items) == 0:
                self.underflow_count += 1
                self.emit_observable(
                    event_type="buffer_underflow",
                    details={"current_level": 0, "min_level": self.min_level},
                    severity="WARNING",
                )

            # Get item from store
            item = yield self.store.get()
            items.append(item)

            # Calculate dwell time if item is valid
            if item and hasattr(item, "entry_time"):
                dwell_time = self.env.now - item.entry_time
                self.dwell_times.append(dwell_time)
            else:
                dwell_time = 0

            # Check for excessive dwell time
            if dwell_time > self.max_dwell_time:
                self.emit_observable(
                    event_type="excessive_dwell_time",
                    details={
                        "product": item.product_id if item and hasattr(item, "product_id") else "UNKNOWN",
                        "dwell_time": dwell_time,
                        "max_allowed": self.max_dwell_time,
                    },
                    severity="WARNING",
                )

            # Update tracking
            self.total_items_out += 1
            self.level = len(self.store.items)
            self.min_level_reached = min(self.min_level_reached, self.level)

            # Update product mix
            if item and hasattr(item, "product_id") and item.product_id in self.product_counts:
                self.product_counts[item.product_id] -= 1
                if self.product_counts[item.product_id] == 0:
                    del self.product_counts[item.product_id]

            # Emit observable
            self.emit_observable(
                event_type="buffer_get",
                details={
                    "level": self.level,
                    "product": item.product_id if item and hasattr(item, "product_id") else "UNKNOWN",
                    "dwell_time": dwell_time,
                    "utilization": self.level / self.capacity,
                },
            )

        return items

    def monitor_process(self) -> Generator:
        """Background process for buffer monitoring."""
        while self.is_running:
            # Monitor every minute
            yield self.env.timeout(1.0)

            # Check for low level warning
            if self.level < self.min_level and self.level > 0:
                self.emit_observable(
                    event_type="buffer_low_level",
                    details={
                        "level": self.level,
                        "min_level": self.min_level,
                        "utilization": self.level / self.capacity,
                    },
                    severity="WARNING",
                )

            # Calculate average dwell time
            avg_dwell = sum(self.dwell_times) / len(self.dwell_times) if self.dwell_times else 0

            # Emit monitoring observable
            self.emit_observable(
                event_type="buffer_monitor",
                details={
                    "level": self.level,
                    "utilization": self.level / self.capacity,
                    "total_in": self.total_items_in,
                    "total_out": self.total_items_out,
                    "avg_dwell_time": avg_dwell,
                    "product_mix": dict(self.product_counts),
                    "overflow_count": self.overflow_count,
                    "underflow_count": self.underflow_count,
                },
                severity="DEBUG",
            )

    def is_full(self) -> bool:
        """Check if buffer is at capacity.

        Returns:
            True if buffer is full
        """
        return len(self.store.items) >= self.capacity  # type: ignore[no-any-return]

    def is_empty(self) -> bool:
        """Check if buffer is empty.

        Returns:
            True if buffer is empty
        """
        return len(self.store.items) == 0

    def get_utilization(self) -> float:
        """Get current buffer utilization.

        Returns:
            Utilization percentage (0-100)
        """
        return (self.level / self.capacity) * 100 if self.capacity > 0 else 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get buffer statistics.

        Returns:
            Dictionary of buffer metrics
        """
        avg_dwell = sum(self.dwell_times) / len(self.dwell_times) if self.dwell_times else 0

        return {
            "current_level": self.level,
            "capacity": self.capacity,
            "utilization": self.get_utilization(),
            "total_throughput": self.total_items_out,
            "avg_dwell_time": avg_dwell,
            "max_level_reached": self.max_level_reached,
            "min_level_reached": self.min_level_reached,
            "overflow_events": self.overflow_count,
            "underflow_events": self.underflow_count,
            "product_mix": dict(self.product_counts),
        }

    def flush(self) -> List[BufferItem]:
        """Remove all items from buffer (e.g., for changeover).

        Returns:
            List of flushed items
        """
        flushed = list(self.store.items)
        self.store.items = []
        self.level = 0
        self.product_counts.clear()

        self.emit_observable(
            event_type="buffer_flushed",
            details={
                "items_flushed": len(flushed),
                "products": [item.product_id for item in flushed],
            },
        )

        return flushed
