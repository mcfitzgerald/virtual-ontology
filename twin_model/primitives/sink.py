"""Sink primitive V2 for collecting from equipment output queues.

This module provides sink primitives that collect directly from
equipment output queues. NO BUFFERS - direct connection only.
"""

from typing import Optional, Generator, Union, Dict, Any, List
from dataclasses import dataclass, field
import simpy
import logging

from .base import BasePrimitive, PrimitiveConfig, SamplingConfig

logger = logging.getLogger(__name__)


@dataclass
class CollectedProduct:
    """Represents a collected finished product."""
    
    product_id: str
    order_id: Optional[str]
    quality: float
    collected_time: float
    source_equipment: Optional[str] = None


@dataclass
class OrderTracking:
    """Tracks order completion."""
    
    order_id: str
    target_quantity: int
    collected_quantity: int = 0
    start_time: float = 0.0
    completion_time: Optional[float] = None
    
    @property
    def is_complete(self) -> bool:
        """Check if order is complete."""
        return self.collected_quantity >= self.target_quantity
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage."""
        return (self.collected_quantity / self.target_quantity * 100) if self.target_quantity > 0 else 0


class SinkPrimitiveV2(BasePrimitive):
    """Sink that collects from equipment output queues.
    
    Key features:
    - Direct connection to last equipment's output queue
    - Order tracking and completion
    - Throughput monitoring
    - Quality tracking
    - Collection rate limiting
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        config: PrimitiveConfig,
        upstream: Optional[Union[simpy.Store, Any]] = None,
        sampling_config: Optional[SamplingConfig] = None
    ) -> None:
        """Initialize sink primitive.
        
        Args:
            env: SimPy environment
            config: Sink configuration
            upstream: Equipment output queue or equipment with output_queue
            sampling_config: Optional sampling configuration
        """
        super().__init__(env, config, sampling_config)
        
        # Direct connection to equipment (NO BUFFERS!)
        self.upstream = upstream
        
        # Sink parameters
        self.line_id = config.get_property("line_id", "LINE1")
        self.collection_rate = config.get_property("collection_rate", 50.0)
        self.quality_threshold = config.get_property("quality_threshold", 0.0)
        self.target_throughput = config.get_property("target_throughput", 45.0)
        self.order_tracking_enabled = config.get_property("order_tracking", True)
        
        # Collection storage
        self.collected_products: List[CollectedProduct] = []
        self.total_collected = 0
        self.total_units_collected = 0  # Alias for compatibility
        self.total_rejected = 0
        
        # Order tracking
        self.active_orders: Dict[str, OrderTracking] = {}
        self.completed_orders: List[OrderTracking] = []
        
        # Throughput tracking
        self.throughput_window = 60.0  # 1 hour window
        self.recent_collections: List[float] = []  # Timestamps
        
        # State
        self.is_running = True
        self.is_collecting = False
        
        # Process reference
        self.process = None
        
        logger.info(f"Sink {self.config.id} initialized for {self.line_id}")
    
    def set_upstream(self, upstream: Union[simpy.Store, Any]) -> None:
        """Set upstream connection.
        
        Args:
            upstream: Equipment output queue or equipment with output_queue
        """
        # Handle both direct queue and equipment with queue
        if hasattr(upstream, 'output_queue'):
            self.upstream = upstream.output_queue
        else:
            self.upstream = upstream
            
        logger.debug(f"{self.config.id}: Connected to upstream")
    
    def register_order(self, order_id: str, target_quantity: int) -> None:
        """Register a production order for tracking.
        
        Args:
            order_id: Order identifier
            target_quantity: Expected quantity
        """
        if self.order_tracking_enabled:
            self.active_orders[order_id] = OrderTracking(
                order_id=order_id,
                target_quantity=target_quantity,
                start_time=self.env.now
            )
            
            logger.info(f"{self.config.id}: Registered order {order_id} for {target_quantity} units")
    
    def run(self) -> Generator:
        """Main sink collection process."""
        while self.is_running:
            try:
                # Check for products to collect
                if not self.upstream:
                    logger.warning(f"{self.config.id}: No upstream connection")
                    yield self.env.timeout(1)
                    continue
                
                if hasattr(self.upstream, 'items') and len(self.upstream.items) == 0:
                    # No products available
                    self.is_collecting = False
                    yield self.env.timeout(0.1)  # Check every 0.1 minutes
                    continue
                
                # Collect product
                yield from self._collect_product()
                
                # Rate limiting
                collection_interval = 1.0 / self.collection_rate
                yield self.env.timeout(collection_interval)
                
            except Exception as e:
                logger.error(f"{self.config.id}: Error in collection: {e}")
                yield self.env.timeout(1)
    
    def _collect_product(self) -> Generator:
        """Collect a single product from upstream."""
        self.is_collecting = True
        
        # Get product from upstream queue
        if hasattr(self.upstream, 'get'):
            product = yield self.upstream.get()
            
            # Check if it's a ProductionUnit
            from .equipment import ProductionUnit
            if isinstance(product, ProductionUnit):
                # Quality check
                if product.quality < self.quality_threshold:
                    self.total_rejected += 1
                    self.emit_observable("product_rejected", {
                        "sink_id": self.config.id,
                        "product_id": product.product_id,
                        "quality": product.quality
                    })
                    return
                
                # Create collected product record
                collected = CollectedProduct(
                    product_id=product.product_id,
                    order_id=product.order_id,
                    quality=product.quality,
                    collected_time=self.env.now
                )
            else:
                # Generic product
                collected = CollectedProduct(
                    product_id="UNKNOWN",
                    order_id=None,
                    quality=1.0,
                    collected_time=self.env.now
                )
            
            # Store collected product
            self.collected_products.append(collected)
            self.total_collected += 1
            self.total_units_collected += 1  # Update alias
            
            # Update order tracking
            if self.order_tracking_enabled and collected.order_id:
                self._update_order_tracking(collected.order_id)
            
            # Update throughput tracking
            self.recent_collections.append(self.env.now)
            self._clean_throughput_window()
            
            # Emit collection event
            self.emit_observable("product_collected", {
                "sink_id": self.config.id,
                "product_id": collected.product_id,
                "order_id": collected.order_id,
                "total_collected": self.total_collected
            })
    
    def _update_order_tracking(self, order_id: str) -> None:
        """Update order tracking for collected product.
        
        Args:
            order_id: Order identifier
        """
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            order.collected_quantity += 1
            
            # Check if order is complete
            if order.is_complete:
                order.completion_time = self.env.now
                self.completed_orders.append(order)
                del self.active_orders[order_id]
                
                self.emit_observable("order_completed", {
                    "sink_id": self.config.id,
                    "order_id": order_id,
                    "quantity": order.collected_quantity,
                    "duration": order.completion_time - order.start_time
                })
                
                logger.info(f"{self.config.id}: Order {order_id} completed")
    
    def _clean_throughput_window(self) -> None:
        """Remove old timestamps from throughput tracking."""
        cutoff_time = self.env.now - self.throughput_window
        self.recent_collections = [
            t for t in self.recent_collections if t > cutoff_time
        ]
    
    def get_current_throughput(self) -> float:
        """Calculate current throughput rate.
        
        Returns:
            Units per minute
        """
        self._clean_throughput_window()
        
        if len(self.recent_collections) < 2:
            return 0.0
        
        time_span = self.env.now - self.recent_collections[0]
        if time_span > 0:
            return len(self.recent_collections) / time_span * 60  # Convert to per minute
        
        return 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get sink statistics.
        
        Returns:
            Statistics dictionary
        """
        throughput = self.get_current_throughput()
        
        stats = {
            "total_collected": self.total_collected,
            "total_rejected": self.total_rejected,
            "current_throughput": throughput,
            "target_throughput": self.target_throughput,
            "throughput_achievement": (throughput / self.target_throughput * 100) if self.target_throughput > 0 else 0,
            "active_orders": len(self.active_orders),
            "completed_orders": len(self.completed_orders)
        }
        
        # Add quality statistics
        if self.collected_products:
            qualities = [p.quality for p in self.collected_products[-100:]]  # Last 100
            stats["average_quality"] = sum(qualities) / len(qualities)
            stats["min_quality"] = min(qualities)
            stats["max_quality"] = max(qualities)
        
        return stats
    
    def get_order_status(self, order_id: Optional[str] = None) -> Union[OrderTracking, Dict[str, OrderTracking], None]:
        """Get status of specific order or all orders.
        
        Args:
            order_id: Optional specific order ID
            
        Returns:
            Order tracking information
        """
        if order_id:
            # Check active orders
            if order_id in self.active_orders:
                return self.active_orders[order_id]
            
            # Check completed orders
            for order in self.completed_orders:
                if order.order_id == order_id:
                    return order
            
            return None
        else:
            # Return all orders
            return {
                "active": self.active_orders,
                "completed": self.completed_orders
            }
    
    def get_products_by_order(self, order_id: str) -> List[CollectedProduct]:
        """Get all products collected for a specific order.
        
        Args:
            order_id: Order identifier
            
        Returns:
            List of collected products
        """
        return [p for p in self.collected_products if p.order_id == order_id]
    
    def stop(self) -> None:
        """Stop sink collection."""
        self.is_running = False
        logger.info(f"{self.config.id}: Sink stopped")
    
    def reset_statistics(self) -> None:
        """Reset collection statistics."""
        self.collected_products.clear()
        self.total_collected = 0
        self.total_rejected = 0
        self.recent_collections.clear()
        
        logger.info(f"{self.config.id}: Statistics reset")
    
    def start(self) -> None:
        """Start the sink collection process.
        
        Implements the abstract start method from BasePrimitive.
        """
        self.process = self.env.process(self.run())