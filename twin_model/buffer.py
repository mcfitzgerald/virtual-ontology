"""
Buffer implementation using SimPy Container.

Buffers represent Work-In-Process (WIP) storage between equipment.
"""

import simpy
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class BufferStats:
    """Statistics for buffer monitoring.

    Attributes:
        level_history: History of buffer levels over time
        total_puts: Total items put into buffer
        total_gets: Total items retrieved from buffer
        max_level: Maximum level reached
        starved_time: Total time buffer was empty
        blocked_time: Total time buffer was full
    """

    level_history: List[tuple[float, int]] = field(default_factory=list)
    total_puts: int = 0
    total_gets: int = 0
    max_level: int = 0
    starved_time: float = 0.0
    blocked_time: float = 0.0


class Buffer:
    """Buffer for storing work-in-process between equipment.

    Uses SimPy Container to manage discrete units with capacity limits.
    Tracks statistics for analysis.
    """

    def __init__(self, env: simpy.Environment, buffer_id: str, capacity: int):
        """Initialize buffer.

        Args:
            env: SimPy environment
            buffer_id: Unique identifier for the buffer
            capacity: Maximum number of units the buffer can hold
        """
        self.env = env
        self.buffer_id = buffer_id
        self.capacity = capacity
        self.container = simpy.Container(env, init=0, capacity=capacity)
        self.stats = BufferStats()

        # Track state changes
        self._last_level = 0
        self._last_time = 0.0
        self._update_stats()

    def put(self, amount: int = 1) -> simpy.Event:
        """Put items into the buffer.

        Args:
            amount: Number of items to put

        Returns:
            SimPy event that triggers when items are added
        """
        event = self.container.put(amount)
        # Schedule stats update when put completes
        event.callbacks.append(lambda _: self._on_put(amount))
        return event

    def get(self, amount: int = 1) -> simpy.Event:
        """Get items from the buffer.

        Args:
            amount: Number of items to get

        Returns:
            SimPy event that triggers when items are available
        """
        event = self.container.get(amount)
        # Schedule stats update when get completes
        event.callbacks.append(lambda _: self._on_get(amount))
        return event

    @property
    def level(self) -> int:
        """Current number of items in buffer."""
        return int(self.container.level)

    @property
    def available_space(self) -> int:
        """Available space in buffer."""
        return self.capacity - self.level

    @property
    def utilization(self) -> float:
        """Buffer utilization as percentage (0-100)."""
        if self.capacity == 0:
            return 0.0
        return (self.level / self.capacity) * 100.0

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return self.level == 0

    def is_full(self) -> bool:
        """Check if buffer is full."""
        return self.level >= self.capacity

    def _update_stats(self) -> None:
        """Update buffer statistics."""
        current_time = self.env.now
        time_delta = current_time - self._last_time

        # Update time-based stats
        if self._last_level == 0:
            self.stats.starved_time += time_delta
        elif self._last_level >= self.capacity:
            self.stats.blocked_time += time_delta

        # Record level change
        self.stats.level_history.append((current_time, self.level))
        self.stats.max_level = max(self.stats.max_level, self.level)

        # Update tracking variables
        self._last_level = self.level
        self._last_time = current_time

    def _on_put(self, amount: int) -> None:
        """Handle successful put operation."""
        self.stats.total_puts += amount
        self._update_stats()

    def _on_get(self, amount: int) -> None:
        """Handle successful get operation."""
        self.stats.total_gets += amount
        self._update_stats()

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get summary of buffer statistics.

        Returns:
            Dictionary with buffer statistics
        """
        total_time = self.env.now if self.env.now > 0 else 1.0

        return {
            "buffer_id": self.buffer_id,
            "capacity": self.capacity,
            "current_level": self.level,
            "utilization": self.utilization,
            "total_puts": self.stats.total_puts,
            "total_gets": self.stats.total_gets,
            "max_level": self.stats.max_level,
            "starved_percentage": (self.stats.starved_time / total_time) * 100,
            "blocked_percentage": (self.stats.blocked_time / total_time) * 100,
        }
