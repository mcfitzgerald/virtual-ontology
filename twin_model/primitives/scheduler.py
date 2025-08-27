"""Enhanced scheduler primitive V2 with smart production sequencing.

This module provides advanced scheduling capabilities including:
- Product sequencing strategies (random, changeover-optimized, campaign)
- Changeover matrices for product-to-product transition times
- Shift-specific scheduling
- ABC analysis for prioritization
- Control system integration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Generator, List, Optional, Tuple

import numpy as np
import simpy

from .base import BasePrimitive, PrimitiveConfig, SamplingConfig


class SequencingStrategy(Enum):
    """Product sequencing strategies."""
    
    RANDOM = "random"
    CHANGEOVER_OPTIMIZED = "changeover_optimized"
    CAMPAIGN_MODE = "campaign_mode"
    PRIORITY_BASED = "priority_based"
    DUE_DATE = "due_date"


class ProductCategory(Enum):
    """ABC analysis categories."""
    
    A = "A"  # High volume, high priority
    B = "B"  # Medium volume, medium priority
    C = "C"  # Low volume, low priority


@dataclass
class Product:
    """Product definition with changeover characteristics."""
    
    product_id: str
    category: ProductCategory
    family: str  # Product family for grouping
    volume_rank: int  # 1 = highest volume
    margin: float  # Profit margin
    complexity: float  # Production complexity (0-1)
    typical_batch_size: int
    min_batch_size: int
    max_batch_size: int


@dataclass
class ProductionOrder:
    """Enhanced production order with scheduling metadata."""
    
    order_id: str
    product: Product
    quantity: int
    due_date: float
    priority: int
    release_date: float = 0.0
    scheduled_start: Optional[float] = None
    actual_start: Optional[float] = None
    actual_end: Optional[float] = None
    completed_quantity: int = 0
    scrap_quantity: int = 0
    
    @property
    def is_complete(self) -> bool:
        """Check if order is complete."""
        return self.completed_quantity >= self.quantity
    
    @property
    def tardiness(self) -> float:
        """Calculate order tardiness."""
        if self.actual_end is None:
            return 0.0
        return max(0.0, self.actual_end - self.due_date)
    
    @property
    def urgency(self) -> float:
        """Calculate urgency score for scheduling."""
        return self.priority / max(1.0, self.due_date - self.release_date)


@dataclass
class ChangeoverMatrix:
    """Product-to-product changeover times."""
    
    products: List[str]
    base_times: np.ndarray  # NxN matrix of changeover times
    
    def get_changeover_time(self, from_product: str, to_product: str) -> float:
        """Get changeover time between products.
        
        Args:
            from_product: Current product
            to_product: Next product
        
        Returns:
            Changeover time in minutes
        """
        if from_product == to_product:
            return 0.0
        
        try:
            from_idx = self.products.index(from_product)
            to_idx = self.products.index(to_product)
            return float(self.base_times[from_idx, to_idx])
        except (ValueError, IndexError):
            # Default changeover time if products not in matrix
            return 30.0


class SchedulerPrimitiveV2(BasePrimitive):
    """Enhanced scheduler with intelligent production sequencing.
    
    Key features:
    - Multiple sequencing strategies
    - Changeover optimization
    - Campaign production support
    - Shift-aware scheduling
    - ABC prioritization
    - Control system integration
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        config: PrimitiveConfig,
        sampling_config: Optional[SamplingConfig] = None
    ) -> None:
        """Initialize enhanced scheduler.
        
        Args:
            env: SimPy environment
            config: Scheduler configuration
            sampling_config: Optional sampling configuration
        """
        super().__init__(env, config, sampling_config)
        
        # Scheduling parameters from config
        self.strategy = SequencingStrategy(
            config.get_property("sequencing_strategy", "changeover_optimized")
        )
        self.campaign_size = config.get_property("campaign_size", 100)
        self.lookahead_horizon = config.get_property("lookahead_horizon", 480.0)
        
        # Initialize product catalog
        self.products: Dict[str, Product] = {}
        self._initialize_products()
        
        # Initialize changeover matrix
        self.changeover_matrix = self._initialize_changeover_matrix()
        
        # Order management
        self.pending_orders: List[ProductionOrder] = []
        self.active_order: Optional[ProductionOrder] = None
        self.completed_orders: List[ProductionOrder] = []
        self.order_queue = simpy.Store(env)
        
        # Current production state
        self.current_product: Optional[str] = None
        self.last_changeover_time: float = 0.0
        self.total_changeover_time: float = 0.0
        self.changeover_count: int = 0
        
        # Shift management
        self.current_shift: int = 1
        self.shift_start_time: float = 0.0
        self.shifts_config = config.get_property("shifts", {
            1: {"start": 0, "duration": 480, "efficiency": 1.0},
            2: {"start": 480, "duration": 480, "efficiency": 0.95},
            3: {"start": 960, "duration": 480, "efficiency": 0.9}
        })
        
        # Performance tracking
        self.orders_scheduled: int = 0
        self.orders_completed: int = 0
        self.total_tardiness: float = 0.0
        self.schedule_adherence: float = 0.0
        
        # Process reference
        self.process = None
    
    def _initialize_products(self) -> None:
        """Initialize product catalog from configuration."""
        products_config = self.config.get_property("products", {})
        
        # Default products if none configured
        if not products_config:
            products_config = {
                "SKU-1001": {"family": "A", "volume_rank": 1, "margin": 0.35, "complexity": 0.3},
                "SKU-1002": {"family": "A", "volume_rank": 2, "margin": 0.30, "complexity": 0.4},
                "SKU-2001": {"family": "B", "volume_rank": 3, "margin": 0.40, "complexity": 0.5},
                "SKU-2002": {"family": "B", "volume_rank": 4, "margin": 0.38, "complexity": 0.6},
                "SKU-3001": {"family": "C", "volume_rank": 5, "margin": 0.45, "complexity": 0.7}
            }
        
        for product_id, props in products_config.items():
            # Determine category based on volume rank
            volume_rank = props.get("volume_rank", 5)
            if volume_rank <= 2:
                category = ProductCategory.A
            elif volume_rank <= 4:
                category = ProductCategory.B
            else:
                category = ProductCategory.C
            
            self.products[product_id] = Product(
                product_id=product_id,
                category=category,
                family=props.get("family", "Default"),
                volume_rank=volume_rank,
                margin=props.get("margin", 0.3),
                complexity=props.get("complexity", 0.5),
                typical_batch_size=props.get("typical_batch", 50),
                min_batch_size=props.get("min_batch", 10),
                max_batch_size=props.get("max_batch", 200)
            )
    
    def _initialize_changeover_matrix(self) -> ChangeoverMatrix:
        """Initialize product changeover matrix.
        
        Returns:
            ChangeoverMatrix with product-to-product times
        """
        product_list = list(self.products.keys())
        n_products = len(product_list)
        
        # Base changeover times (minutes)
        base_times = np.full((n_products, n_products), 30.0)
        
        # Set changeover times based on product families
        for i, prod1 in enumerate(product_list):
            for j, prod2 in enumerate(product_list):
                if i == j:
                    base_times[i, j] = 0.0  # Same product, no changeover
                elif self.products[prod1].family == self.products[prod2].family:
                    base_times[i, j] = 10.0  # Same family, quick changeover
                else:
                    # Different families, complexity-based changeover
                    complexity_diff = abs(
                        self.products[prod1].complexity - 
                        self.products[prod2].complexity
                    )
                    base_times[i, j] = 20.0 + complexity_diff * 40.0
        
        return ChangeoverMatrix(products=product_list, base_times=base_times)
    
    def run(self) -> Generator:
        """Main scheduler process."""
        while True:
            # Update shift if needed
            self._update_shift()
            
            # Check for new orders
            if self.pending_orders:
                # Sequence orders based on strategy
                sequenced_orders = self._sequence_orders()
                
                # Release orders to production
                for order in sequenced_orders:
                    yield self.order_queue.put(order)
                    self.orders_scheduled += 1
                    
                    self.emit_observable("order_scheduled", {
                        "order_id": order.order_id,
                        "product_id": order.product.product_id,
                        "quantity": order.quantity,
                        "scheduled_start": order.scheduled_start
                    })
            
            # Wait before next scheduling cycle
            yield self.env.timeout(5.0)  # Check every 5 minutes
    
    def add_order(self, order: ProductionOrder) -> None:
        """Add a production order to the schedule.
        
        Args:
            order: Production order to add
        """
        self.pending_orders.append(order)
        
        self.emit_observable("order_received", {
            "order_id": order.order_id,
            "product_id": order.product.product_id,
            "quantity": order.quantity,
            "due_date": order.due_date
        })
    
    def _sequence_orders(self) -> List[ProductionOrder]:
        """Sequence orders based on current strategy.
        
        Returns:
            List of orders in execution sequence
        """
        if not self.pending_orders:
            return []
        
        if self.strategy == SequencingStrategy.RANDOM:
            # Random sequencing (baseline)
            np.random.shuffle(self.pending_orders)
            sequenced = self.pending_orders[:5]  # Take next 5 orders
            
        elif self.strategy == SequencingStrategy.CHANGEOVER_OPTIMIZED:
            # Minimize total changeover time
            sequenced = self._optimize_changeovers(self.pending_orders[:10])
            
        elif self.strategy == SequencingStrategy.CAMPAIGN_MODE:
            # Group same products together
            sequenced = self._create_campaigns(self.pending_orders)
            
        elif self.strategy == SequencingStrategy.PRIORITY_BASED:
            # Sort by priority and urgency
            self.pending_orders.sort(key=lambda o: (-o.priority, o.urgency), reverse=True)
            sequenced = self.pending_orders[:5]
            
        elif self.strategy == SequencingStrategy.DUE_DATE:
            # Earliest due date first
            self.pending_orders.sort(key=lambda o: o.due_date)
            sequenced = self.pending_orders[:5]
            
        else:
            sequenced = self.pending_orders[:5]
        
        # Remove sequenced orders from pending
        for order in sequenced:
            if order in self.pending_orders:
                self.pending_orders.remove(order)
            order.scheduled_start = self.env.now
        
        return sequenced
    
    def _optimize_changeovers(self, orders: List[ProductionOrder]) -> List[ProductionOrder]:
        """Optimize order sequence to minimize changeover time.
        
        Uses a greedy nearest-neighbor approach for simplicity.
        
        Args:
            orders: Orders to sequence
        
        Returns:
            Optimized order sequence
        """
        if not orders:
            return []
        
        sequenced = []
        remaining = orders.copy()
        
        # Start with current product if available
        if self.current_product:
            # Find orders for current product
            same_product = [o for o in remaining if o.product.product_id == self.current_product]
            if same_product:
                sequenced.append(same_product[0])
                remaining.remove(same_product[0])
        
        # If no current product or no matching orders, start with highest priority
        if not sequenced and remaining:
            sequenced.append(max(remaining, key=lambda o: o.priority))
            remaining.remove(sequenced[0])
        
        # Greedy selection: always pick next order with minimum changeover
        while remaining:
            last_product = sequenced[-1].product.product_id
            
            # Calculate changeover times to all remaining orders
            changeover_times = []
            for order in remaining:
                time = self.changeover_matrix.get_changeover_time(
                    last_product, order.product.product_id
                )
                changeover_times.append((order, time))
            
            # Select order with minimum changeover
            next_order = min(changeover_times, key=lambda x: x[1])[0]
            sequenced.append(next_order)
            remaining.remove(next_order)
        
        return sequenced
    
    def _create_campaigns(self, orders: List[ProductionOrder]) -> List[ProductionOrder]:
        """Create production campaigns by grouping same products.
        
        Args:
            orders: Orders to group into campaigns
        
        Returns:
            Orders sequenced in campaigns
        """
        # Group orders by product
        product_groups: Dict[str, List[ProductionOrder]] = {}
        for order in orders:
            product_id = order.product.product_id
            if product_id not in product_groups:
                product_groups[product_id] = []
            product_groups[product_id].append(order)
        
        # Sort groups by total volume (descending)
        sorted_groups = sorted(
            product_groups.items(),
            key=lambda x: sum(o.quantity for o in x[1]),
            reverse=True
        )
        
        # Create campaigns
        sequenced = []
        for product_id, group_orders in sorted_groups:
            # Sort orders within group by priority
            group_orders.sort(key=lambda o: -o.priority)
            
            # Add orders up to campaign size
            campaign_quantity = 0
            for order in group_orders:
                if campaign_quantity + order.quantity <= self.campaign_size:
                    sequenced.append(order)
                    campaign_quantity += order.quantity
                else:
                    break
            
            # Stop if we have enough orders
            if len(sequenced) >= 5:
                break
        
        return sequenced[:5]
    
    def _update_shift(self) -> None:
        """Update current shift based on simulation time."""
        # Simple 3-shift pattern
        shift_duration = 480.0  # 8 hours
        shifts_per_day = 3
        
        current_shift_index = int((self.env.now % (shift_duration * shifts_per_day)) / shift_duration) + 1
        
        if current_shift_index != self.current_shift:
            # Shift change
            self.emit_observable("shift_change", {
                "from_shift": self.current_shift,
                "to_shift": current_shift_index,
                "time": self.env.now
            })
            
            self.current_shift = current_shift_index
            self.shift_start_time = self.env.now
    
    def complete_order(self, order: ProductionOrder, completed_quantity: int, 
                      scrap_quantity: int = 0) -> None:
        """Mark an order as complete.
        
        Args:
            order: Order that was completed
            completed_quantity: Good units produced
            scrap_quantity: Scrapped units
        """
        order.completed_quantity = completed_quantity
        order.scrap_quantity = scrap_quantity
        order.actual_end = self.env.now
        
        self.completed_orders.append(order)
        self.orders_completed += 1
        
        # Update tardiness tracking
        if order.tardiness > 0:
            self.total_tardiness += order.tardiness
        
        self.emit_observable("order_completed", {
            "order_id": order.order_id,
            "product_id": order.product.product_id,
            "target_quantity": order.quantity,
            "completed_quantity": completed_quantity,
            "scrap_quantity": scrap_quantity,
            "tardiness": order.tardiness
        })
    
    def request_changeover(self, from_product: str, to_product: str) -> float:
        """Request changeover time for product switch.
        
        Args:
            from_product: Current product
            to_product: Next product
        
        Returns:
            Required changeover time in minutes
        """
        changeover_time = self.changeover_matrix.get_changeover_time(from_product, to_product)
        
        # Apply changeover reduction from controls
        reduction_factor = self.config.get_property("changeover_reduction_factor", 1.0)
        changeover_time *= reduction_factor
        
        # Track changeover
        self.total_changeover_time += changeover_time
        self.changeover_count += 1
        self.last_changeover_time = self.env.now
        self.current_product = to_product
        
        self.emit_observable("changeover_started", {
            "from_product": from_product,
            "to_product": to_product,
            "duration": changeover_time,
            "time": self.env.now
        })
        
        return changeover_time
    
    def get_schedule_metrics(self) -> Dict[str, float]:
        """Calculate scheduling performance metrics.
        
        Returns:
            Dictionary of scheduling KPIs
        """
        total_time = self.env.now if self.env.now > 0 else 1.0
        
        # Calculate schedule adherence
        if self.completed_orders:
            on_time = sum(1 for o in self.completed_orders if o.tardiness == 0)
            self.schedule_adherence = on_time / len(self.completed_orders)
        
        return {
            "orders_scheduled": self.orders_scheduled,
            "orders_completed": self.orders_completed,
            "orders_pending": len(self.pending_orders),
            "schedule_adherence": self.schedule_adherence,
            "average_tardiness": self.total_tardiness / max(1, self.orders_completed),
            "changeover_count": self.changeover_count,
            "total_changeover_time": self.total_changeover_time,
            "changeover_percentage": self.total_changeover_time / total_time,
            "current_strategy": self.strategy.value
        }
    
    def get_next_order(self) -> Optional[ProductionOrder]:
        """Get next order from schedule.
        
        Returns:
            Next production order or None
        """
        try:
            # Non-blocking get from order queue
            if len(self.order_queue.items) > 0:
                return self.order_queue.items[0]
        except:
            pass
        return None
    
    def start(self) -> None:
        """Start the scheduler process.
        
        Implements the abstract start method from BasePrimitive.
        """
        self.process = self.env.process(self.run())