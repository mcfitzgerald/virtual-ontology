"""Source flow primitive for continuous material generation.

This module implements sources that generate continuous material flow
based on production orders or continuous generation patterns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator, Optional

import simpy

from .base_flow import BaseFlowPrimitive, FlowCapacity, FlowState


@dataclass
class ProductionOrder:
    """Production order for material generation."""

    order_id: str
    product_id: str
    target_volume: float
    due_time: float
    priority: int = 0
    completed_volume: float = 0.0

    def __post_init__(self) -> None:
        """Validate production order."""
        if self.target_volume <= 0:
            raise ValueError(f"target_volume must be positive, got {self.target_volume}")
        if self.due_time < 0:
            raise ValueError(f"due_time cannot be negative, got {self.due_time}")
        if self.completed_volume < 0:
            raise ValueError(f"completed_volume cannot be negative, got {self.completed_volume}")
        if self.completed_volume > self.target_volume:
            raise ValueError(
                f"completed_volume ({self.completed_volume}) cannot exceed "
                f"target_volume ({self.target_volume})"
            )

    @property
    def remaining_volume(self) -> float:
        """Calculate remaining volume to complete."""
        return self.target_volume - self.completed_volume

    @property
    def completion_percentage(self) -> float:
        """Calculate order completion percentage."""
        if self.target_volume == 0:
            return 100.0
        return (self.completed_volume / self.target_volume) * 100


class SourceFlow(BaseFlowPrimitive):
    """Source generating continuous material flow."""

    def __init__(
        self,
        env: simpy.Environment,
        config: dict[str, Any],
        flow_capacity: FlowCapacity,
        generation_rate: float,
        generation_interval: float = 0.1
    ) -> None:
        """Initialize source flow.

        Args:
            env: SimPy environment
            config: Configuration dictionary
            flow_capacity: Flow capacity constraints
            generation_rate: Material generation rate (units/minute)
            generation_interval: Time between generation attempts (minutes)
        """
        super().__init__(env, config, flow_capacity)
        self.generation_rate = generation_rate
        self.generation_interval = generation_interval
        self.order_queue: list[ProductionOrder] = []
        self.current_order: Optional[ProductionOrder] = None
        self.completed_orders: list[ProductionOrder] = []

        # Mode of operation
        self.continuous_mode = config.get("continuous_mode", True)
        self.default_product = config.get("default_product", "default")

        # Validate generation rate
        if generation_rate <= 0:
            raise ValueError(f"generation_rate must be positive, got {generation_rate}")
        if generation_interval <= 0:
            raise ValueError(f"generation_interval must be positive, got {generation_interval}")

    def process_flow(self) -> Generator[Any, None, None]:
        """Generate material based on orders or continuously."""
        while True:
            if not self.continuous_mode and self.current_order:
                # Order-based generation
                yield from self._process_order()
            elif self.continuous_mode:
                # Continuous generation
                yield from self._process_continuous()
            else:
                # No current order and not in continuous mode
                self.change_state(FlowState.IDLE)

                # Check for new orders
                if self.order_queue:
                    self.current_order = self._get_next_order()
                    if self.current_order:  # Add check for None
                        self.emit_observable("order_started", {
                            "order_id": self.current_order.order_id,
                            "product_id": self.current_order.product_id,
                            "target_volume": self.current_order.target_volume
                        })
                else:
                    # Wait for new orders
                    yield self.env.timeout(self.generation_interval)

    def _process_order(self) -> Generator[Any, None, None]:
        """Process current production order."""
        if not self.current_order or not self.output_buffer:
            yield self.env.timeout(self.generation_interval)
            return

        # Calculate volume to generate
        remaining = self.current_order.remaining_volume
        max_generation = self.generation_rate * self.generation_interval
        available_space = self.output_buffer.capacity - self.output_buffer.level

        volume = min(remaining, max_generation, available_space)

        if volume > 0:
            # Generate material
            self.change_state(FlowState.FLOWING)
            yield self.output_buffer.put(volume)
            self.current_order.completed_volume += volume
            self.flow_metrics.total_output += volume

            self.emit_observable("material_generated", {
                "order_id": self.current_order.order_id,
                "product_id": self.current_order.product_id,
                "volume": volume,
                "completion_percentage": self.current_order.completion_percentage
            })

            # Check if order is complete
            if self.current_order.completed_volume >= self.current_order.target_volume:
                self.emit_observable("order_completed", {
                    "order_id": self.current_order.order_id,
                    "product_id": self.current_order.product_id,
                    "total_volume": self.current_order.target_volume,
                    "completion_time": self.env.now
                })

                # Move to completed orders
                self.completed_orders.append(self.current_order)
                self.current_order = self._get_next_order()

                if self.current_order:
                    self.emit_observable("order_started", {
                        "order_id": self.current_order.order_id,
                        "product_id": self.current_order.product_id,
                        "target_volume": self.current_order.target_volume
                    })
        else:
            # Cannot generate - output buffer full
            self.change_state(FlowState.BLOCKED_DOWNSTREAM)

        yield self.env.timeout(self.generation_interval)

    def _process_continuous(self) -> Generator[Any, None, None]:
        """Process continuous generation."""
        if not self.output_buffer:
            yield self.env.timeout(self.generation_interval)
            return

        # Calculate volume to generate
        max_generation = self.generation_rate * self.generation_interval
        available_space = self.output_buffer.capacity - self.output_buffer.level

        volume = min(max_generation, available_space)

        if volume > 0:
            # Generate material
            self.change_state(FlowState.FLOWING)
            yield self.output_buffer.put(volume)
            self.flow_metrics.total_output += volume

            self.emit_observable("material_generated", {
                "product_id": self.default_product,
                "volume": volume,
                "rate": self.generation_rate
            })
        else:
            # Cannot generate - output buffer full
            self.change_state(FlowState.BLOCKED_DOWNSTREAM)

        yield self.env.timeout(self.generation_interval)

    def _get_next_order(self) -> Optional[ProductionOrder]:
        """Get next order from queue based on priority.

        Returns:
            Next production order or None if queue is empty
        """
        if not self.order_queue:
            return None

        # Sort by priority (higher priority first) then by due time
        self.order_queue.sort(key=lambda o: (-o.priority, o.due_time))
        return self.order_queue.pop(0)

    def add_order(self, order: ProductionOrder) -> None:
        """Add a production order to the queue.

        Args:
            order: Production order to add
        """
        self.order_queue.append(order)

        self.emit_observable("order_queued", {
            "order_id": order.order_id,
            "product_id": order.product_id,
            "target_volume": order.target_volume,
            "priority": order.priority,
            "queue_length": len(self.order_queue)
        })

        # If no current order and not in continuous mode, start processing
        if not self.current_order and not self.continuous_mode:
            self.current_order = self._get_next_order()
            if self.current_order:
                self.emit_observable("order_started", {
                    "order_id": self.current_order.order_id,
                    "product_id": self.current_order.product_id,
                    "target_volume": self.current_order.target_volume
                })

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a production order.

        Args:
            order_id: ID of order to cancel

        Returns:
            True if order was cancelled, False if not found
        """
        # Check if it's the current order
        if self.current_order and self.current_order.order_id == order_id:
            self.emit_observable("order_cancelled", {
                "order_id": order_id,
                "completed_volume": self.current_order.completed_volume,
                "target_volume": self.current_order.target_volume
            })
            self.current_order = self._get_next_order()
            return True

        # Check the queue
        for i, order in enumerate(self.order_queue):
            if order.order_id == order_id:
                cancelled_order = self.order_queue.pop(i)
                self.emit_observable("order_cancelled", {
                    "order_id": order_id,
                    "completed_volume": cancelled_order.completed_volume,
                    "target_volume": cancelled_order.target_volume
                })
                return True

        return False

    def get_queue_status(self) -> dict[str, Any]:
        """Get current queue status.

        Returns:
            Dictionary with queue status information
        """
        total_volume = sum(order.target_volume for order in self.order_queue)

        return {
            "queue_length": len(self.order_queue),
            "total_volume": total_volume,
            "current_order": {
                "order_id": self.current_order.order_id,
                "product_id": self.current_order.product_id,
                "completion_percentage": self.current_order.completion_percentage
            } if self.current_order else None,
            "completed_orders": len(self.completed_orders)
        }
