"""Source primitive V2 for direct equipment feeding.

This module provides source primitives that feed directly into
equipment input queues. NO BUFFERS - direct connection only.
"""

from typing import Optional, Generator, Any, Union
from enum import Enum
import random
import numpy as np
import simpy
import logging

from .base import BasePrimitive, PrimitiveConfig, SamplingConfig

logger = logging.getLogger(__name__)


class ArrivalPattern(str, Enum):
    """Material arrival patterns."""
    
    CONSTANT = "CONSTANT"
    EXPONENTIAL = "EXPONENTIAL"
    NORMAL = "NORMAL"
    BATCH = "BATCH"


class SourcePrimitiveV2(BasePrimitive):
    """Source that feeds directly into equipment input queues.
    
    Key features:
    - Direct connection to first equipment's input queue
    - Order-driven generation
    - Multiple arrival patterns
    - Quality inspection at source
    - Supply disruption modeling
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        config: PrimitiveConfig,
        downstream: Optional[Union[simpy.Store, Any]] = None,
        sampling_config: Optional[SamplingConfig] = None
    ) -> None:
        """Initialize source primitive.
        
        Args:
            env: SimPy environment
            config: Source configuration
            downstream: Equipment input queue or equipment with input_queue
            sampling_config: Optional sampling configuration
        """
        super().__init__(env, config, sampling_config)
        
        # Direct connection to equipment (NO BUFFERS!)
        self.downstream = downstream
        
        # Source parameters
        self.line_id = config.get_property("line_id", "LINE1")
        self.arrival_pattern = ArrivalPattern(
            config.get_property("arrival_pattern", "CONSTANT")
        )
        self.arrival_rate = config.get_property("arrival_rate", 85.0)
        self.batch_size = config.get_property("batch_size", 100)
        self.order_mode = config.get_property("order_mode", True)
        
        # Quality parameters
        self.quality_rate = config.get_property("quality_rate", 0.95)
        self.supply_variability = config.get_property("supply_variability", 0.1)
        self.disruption_probability = config.get_property("disruption_probability", 0.02)
        
        # Order management
        self.current_order = None
        self.order_queue = []
        self.units_remaining = 0
        self.total_generated = 0
        self.units_generated = 0  # Alias for compatibility
        self.total_rejected = 0
        
        # State tracking
        self.is_running = True
        self.is_disrupted = False
        
        # Process reference
        self.process = None
        
        logger.info(f"Source {self.config.id} initialized for {self.line_id}")
    
    def set_downstream(self, downstream: Union[simpy.Store, Any]) -> None:
        """Set downstream connection.
        
        Args:
            downstream: Equipment input queue or equipment with input_queue
        """
        # Handle both direct queue and equipment with queue
        if hasattr(downstream, 'input_queue'):
            self.downstream = downstream.input_queue
        else:
            self.downstream = downstream
            
        logger.debug(f"{self.config.id}: Connected to downstream")
    
    def set_production_order(self, order: 'ProductionOrder') -> None:
        """Set current production order.
        
        Args:
            order: Production order to process
        """
        self.current_order = order
        self.units_remaining = order.quantity if order else 0
        
        # Update order tracking
        if order:
            order.actual_start = self.env.now
        
        self.emit_observable("order_started", {
            "source_id": self.config.id,
            "order_id": order.order_id if order else None,
            "product_id": order.product.product_id if order and hasattr(order, 'product') else "DEFAULT",
            "target_quantity": order.quantity if order else 0
        })
        
        logger.info(f"{self.config.id}: Started order {order.order_id if order else 'None'}")
    
    def add_order_to_queue(self, order: 'ProductionOrder') -> None:
        """Add order to queue for processing.
        
        Args:
            order: Production order to queue
        """
        self.order_queue.append(order)
        logger.debug(f"{self.config.id}: Queued order {order.order_id}")
    
    def run(self) -> Generator:
        """Main source generation process."""
        while self.is_running:
            try:
                if self.order_mode:
                    # Order-driven generation
                    yield from self._order_driven_generation()
                else:
                    # Continuous generation
                    yield from self._continuous_generation()
                    
            except Exception as e:
                logger.error(f"{self.config.id}: Error in generation: {e}")
                yield self.env.timeout(1)
    
    def _order_driven_generation(self) -> Generator:
        """Generate material based on production orders."""
        # Check for current order
        if not self.current_order:
            # Try to get next order from queue
            if self.order_queue:
                self.set_production_order(self.order_queue.pop(0))
            else:
                # No orders - wait
                yield self.env.timeout(1)
                return
        
        # Check if order is complete
        if self.units_remaining <= 0:
            self._complete_current_order()
            yield self.env.timeout(0.01)  # Small delay to prevent tight loop
            return
        
        # Generate single unit at arrival rate
        unit_generated = yield from self._generate_unit()
        
        # Only decrement if unit was actually generated (not rejected)
        if unit_generated:
            self.units_remaining -= 1
            if self.current_order:
                self.current_order.completed_quantity += 1
        
        # Wait for next unit based on arrival rate
        # Adjust rate for quality rejects to maintain effective throughput
        if self.arrival_rate > 0 and self.quality_rate > 0:
            effective_rate = self.arrival_rate * self.quality_rate
            interval = 1.0 / self.arrival_rate  # Use raw rate, quality handled in generation
            yield self.env.timeout(interval)
    
    def _continuous_generation(self) -> Generator:
        """Generate material continuously."""
        # Check for supply disruption (probability per hour, not per unit)
        # Convert to per-generation probability based on arrival rate
        disruption_check_interval = 60  # Check once per hour
        if self.env.now % disruption_check_interval < 1.0/self.arrival_rate:
            if random.random() < self.disruption_probability:
                yield from self._handle_disruption()
                return
        
        # Generate based on arrival pattern
        if self.arrival_pattern == ArrivalPattern.BATCH:
            # Generate batch then wait
            yield from self._generate_batch(self.batch_size)
            interval = self.batch_size / self.arrival_rate
            yield self.env.timeout(interval)
        else:
            # For all non-batch patterns, generate single unit then wait
            # Generate the unit first
            yield from self._generate_unit()
            
            # Calculate interval based on pattern (in minutes)
            if self.arrival_pattern == ArrivalPattern.CONSTANT:
                interval = 1.0 / self.arrival_rate  # Minutes between units
            elif self.arrival_pattern == ArrivalPattern.EXPONENTIAL:
                # Use arrival_rate directly as the rate parameter (units per minute)
                interval = random.expovariate(self.arrival_rate)  # Returns time in minutes
            elif self.arrival_pattern == ArrivalPattern.NORMAL:
                mean = 1.0 / self.arrival_rate  # Mean interval in minutes
                std = mean * self.supply_variability
                interval = max(0.001, np.random.normal(mean, std))
            else:
                interval = 1.0 / self.arrival_rate
            
            # Debug excessive intervals
            if interval > 1.0:
                logger.debug(f"{self.config.id}: Long interval {interval:.2f} min for pattern {self.arrival_pattern}")
            
            # Wait for next generation
            yield self.env.timeout(interval)
    
    def _complete_current_order(self) -> None:
        """Complete the current production order."""
        if self.current_order:
            self.current_order.actual_end = self.env.now
            
            self.emit_observable("order_completed", {
                "source_id": self.config.id,
                "order_id": self.current_order.order_id,
                "product_id": self.current_order.product.product_id if hasattr(self.current_order, 'product') else "DEFAULT",
                "completed_quantity": self.current_order.completed_quantity,
                "target_quantity": self.current_order.quantity
            })
            
            logger.info(f"{self.config.id}: Completed order {self.current_order.order_id} "
                       f"({self.current_order.completed_quantity}/{self.current_order.quantity} units)")
            
            # Clear current order
            self.current_order = None
            self.units_remaining = 0
            
            # Check queue for next order
            if self.order_queue:
                next_order = self.order_queue.pop(0)
                self.set_production_order(next_order)
    
    def _generate_batch(self, size: int) -> Generator:
        """Generate a batch of units.
        
        Args:
            size: Batch size
        """
        for _ in range(size):
            yield from self._generate_unit()
            # Delay based on arrival rate (units per minute)
            if self.arrival_rate > 0:
                interval = 1.0 / self.arrival_rate
                yield self.env.timeout(interval)
    
    def _generate_unit(self) -> Generator:
        """Generate a single unit.
        
        Returns:
            bool: True if unit was generated, False if rejected
        """
        # Quality check
        if random.random() > self.quality_rate:
            # Unit rejected at source
            self.total_rejected += 1
            self.emit_observable("unit_rejected", {
                "source_id": self.config.id,
                "reason": "quality_check"
            })
            return False
        
        # Create production unit
        from .equipment_v2_fixed import ProductionUnit
        unit = ProductionUnit(
            product_id=self.current_order.product.product_id if self.current_order and hasattr(self.current_order, 'product') else "DEFAULT",
            order_id=self.current_order.order_id if self.current_order else None,
            quality=self.quality_rate,
            timestamp=self.env.now
        )
        
        # Send to downstream
        if self.downstream:
            if hasattr(self.downstream, 'put'):
                # Direct queue connection
                yield self.downstream.put(unit)
                self.total_generated += 1
                self.units_generated += 1  # Update alias
                
                self.emit_observable("unit_generated", {
                    "source_id": self.config.id,
                    "product_id": unit.product_id,
                    "order_id": unit.order_id
                })
            else:
                logger.warning(f"{self.config.id}: Downstream has no 'put' method")
        else:
            logger.warning(f"{self.config.id}: No downstream connection!")
        
        return True
    
    def _handle_disruption(self) -> Generator:
        """Handle supply disruption."""
        if not self.is_disrupted:
            self.is_disrupted = True
            disruption_duration = random.uniform(10, 60)  # 10-60 minutes
            
            self.emit_observable("supply_disruption", {
                "source_id": self.config.id,
                "duration": disruption_duration
            })
            
            logger.warning(f"{self.config.id}: Supply disruption for {disruption_duration:.1f} minutes")
            yield self.env.timeout(disruption_duration)
            
            self.is_disrupted = False
            self.emit_observable("supply_restored", {"source_id": self.config.id})
    
    
    def stop(self) -> None:
        """Stop source generation."""
        self.is_running = False
        logger.info(f"{self.config.id}: Source stopped")
    
    def get_statistics(self) -> dict:
        """Get source statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_generated": self.total_generated,
            "total_rejected": self.total_rejected,
            "quality_rate_actual": (
                self.total_generated / (self.total_generated + self.total_rejected)
                if (self.total_generated + self.total_rejected) > 0 else 0
            ),
            "current_order": self.current_order.order_id if self.current_order else None,
            "orders_pending": len(self.order_queue),
            "units_remaining": self.units_remaining,
            "is_disrupted": self.is_disrupted
        }
    
    def initialize_wip(self, level: float = 0.5) -> Generator:
        """Initialize work-in-progress in downstream equipment.
        
        Args:
            level: Fill level as fraction of capacity (0-1)
        """
        if self.downstream and hasattr(self.downstream, 'capacity'):
            initial_units = int(self.downstream.capacity * level)
            
            logger.info(f"{self.config.id}: Initializing {initial_units} units of WIP")
            
            for _ in range(initial_units):
                from .equipment import ProductionUnit
                unit = ProductionUnit(
                    product_id="INITIAL_WIP",
                    quality=1.0,
                    timestamp=0
                )
                
                if hasattr(self.downstream, 'put'):
                    yield self.downstream.put(unit)
                    
            self.emit_observable("wip_initialized", {
                "source_id": self.config.id,
                "units": initial_units
            })
    
    def start(self) -> None:
        """Start the source generation process.
        
        Implements the abstract start method from BasePrimitive.
        """
        self.process = self.env.process(self.run())