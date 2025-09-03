"""Production order scheduling for MES simulation.

This module provides production order management and scheduling
to match the patterns observed in the target MES data.
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Generator
import simpy
from pathlib import Path
import yaml

from .base_scheduler import BaseScheduler, SchedulerConfig, SchedulingConstraints, OrderStatus

logger = logging.getLogger(__name__)


@dataclass
class ProductionOrder:
    """Production order with scheduling information."""
    
    order_id: str
    product_id: str
    product_name: str
    target_volume: float
    line_id: str
    scheduled_start: float  # Simulation time in minutes
    scheduled_duration: float  # Expected duration in minutes
    priority: int = 5  # 1-10, higher is more urgent
    status: OrderStatus = OrderStatus.PENDING
    actual_start: Optional[float] = None
    actual_end: Optional[float] = None
    completed_volume: float = 0.0
    scrap_volume: float = 0.0
    
    def __post_init__(self):
        """Validate order parameters."""
        if self.target_volume <= 0:
            raise ValueError(f"Target volume must be positive, got {self.target_volume}")
        if self.scheduled_duration <= 0:
            raise ValueError(f"Scheduled duration must be positive, got {self.scheduled_duration}")
        if not 1 <= self.priority <= 10:
            raise ValueError(f"Priority must be between 1 and 10, got {self.priority}")


@dataclass
class ProductMix:
    """Product mix configuration for a production line."""
    
    line_id: str
    products: List[str]  # List of product IDs
    weights: List[float]  # Probability weights for each product
    
    def __post_init__(self):
        """Validate product mix."""
        if len(self.products) != len(self.weights):
            raise ValueError("Products and weights must have same length")
        if not all(w > 0 for w in self.weights):
            raise ValueError("All weights must be positive")
        # Normalize weights to sum to 1
        total = sum(self.weights)
        self.weights = [w / total for w in self.weights]


class ProductionScheduler(BaseScheduler):
    """Concrete implementation of scheduler for MES simulation.
    
    This scheduler creates and manages production orders to match
    the patterns observed in the target MES data, implementing
    a simple sequential scheduling algorithm with configurable
    product mixes and changeover times.
    """
    
    def _default_product_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Return default product catalog."""
        return {
        "SKU-1001": {
            "name": "8oz Water Bottle",
            "rate_per_5min": 475,
            "lines": ["1", "2"],
            "typical_batch": 50000
        },
        "SKU-1002": {
            "name": "8oz Juice",
            "rate_per_5min": 475,
            "lines": ["1", "2"],
            "typical_batch": 40000
        },
        "SKU-2001": {
            "name": "12oz Soda",
            "rate_per_5min": 475,
            "lines": ["2", "3"],
            "typical_batch": 60000
        },
        "SKU-2002": {
            "name": "16oz Energy Drink",
            "rate_per_5min": 450,
            "lines": ["1", "2", "3"],
            "typical_batch": 45000
        },
        "SKU-3001": {
            "name": "20oz Sports Drink",
            "rate_per_5min": 450,
            "lines": ["2", "3"],
            "typical_batch": 35000
        },
        "SKU-3002": {
            "name": "1L Juice",
            "rate_per_5min": 425,
            "lines": ["1", "2", "3"],
            "typical_batch": 30000
        }
        }
    
    def _load_product_catalog(self, path: Path) -> Dict[str, Dict[str, Any]]:
        """Load product catalog from YAML file.
        
        Args:
            path: Path to YAML file
            
        Returns:
            Product catalog dictionary
        """
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        catalog = {}
        for product_id, product_data in data.get('products', {}).items():
            catalog[product_id] = {
                'name': product_data.get('name', product_id),
                'rate_per_5min': product_data.get('target_rate_5min', 450),
                'lines': [str(l) for l in product_data.get('allowed_lines', [])],
                'typical_batch': product_data.get('typical_batch_size', 40000)
            }
        
        return catalog
    
    def __init__(
        self,
        env: simpy.Environment,
        config: Optional[SchedulerConfig] = None,
        constraints: Optional[SchedulingConstraints] = None,
        catalog_path: Optional[Path] = None,
        random_seed: Optional[int] = None
    ):
        """Initialize production scheduler.
        
        Args:
            env: SimPy environment
            config: Scheduler configuration
            constraints: Scheduling constraints
            catalog_path: Path to product catalog YAML
            random_seed: Random seed for reproducibility
        """
        super().__init__(env, config, constraints)
        self.random = random.Random(random_seed)
        
        # Order tracking
        self.order_counter = 1000
        self.line_schedules: Dict[str, List[ProductionOrder]] = {
            "1": [],
            "2": [],
            "3": []
        }
        
        # Current production on each line
        self.current_production: Dict[str, Optional[ProductionOrder]] = {
            "1": None,
            "2": None,
            "3": None
        }
        
        # Load product catalog
        if catalog_path and catalog_path.exists():
            self.product_catalog = self._load_product_catalog(catalog_path)
        else:
            self.product_catalog = self._default_product_catalog()
        
        # Product mix based on target data analysis
        self.product_mixes = self._setup_product_mixes()
        
        # Changeover times (minutes)
        self.changeover_matrix = self._setup_changeover_matrix()
        
    def _setup_product_mixes(self) -> Dict[str, ProductMix]:
        """Set up product mix for each line based on target data."""
        return {
            "1": ProductMix(
                line_id="1",
                products=["SKU-1001", "SKU-1002", "SKU-2002", "SKU-3002"],
                weights=[0.35, 0.25, 0.25, 0.15]  # Based on target distribution
            ),
            "2": ProductMix(
                line_id="2",
                products=["SKU-2001", "SKU-1001", "SKU-3001", "SKU-2002", "SKU-1002", "SKU-3002"],
                weights=[0.30, 0.20, 0.15, 0.15, 0.10, 0.10]
            ),
            "3": ProductMix(
                line_id="3",
                products=["SKU-2001", "SKU-2002", "SKU-3001", "SKU-3002"],
                weights=[0.35, 0.30, 0.20, 0.15]
            )
        }
    
    def _setup_changeover_matrix(self) -> Dict[Tuple[str, str], float]:
        """Set up changeover times between products (minutes)."""
        matrix = {}
        products = list(self.PRODUCT_CATALOG.keys())
        
        for from_product in products:
            for to_product in products:
                if from_product == to_product:
                    matrix[(from_product, to_product)] = 0
                elif from_product[:7] == to_product[:7]:  # Same product family
                    matrix[(from_product, to_product)] = self.config.same_family_changeover_minutes
                else:
                    matrix[(from_product, to_product)] = self.config.different_family_changeover_minutes
        
        return matrix
    
    def generate_order(
        self,
        line_id: str,
        scheduled_start: float,
        duration_hours: float = 4.0
    ) -> ProductionOrder:
        """Generate a production order for a line.
        
        Args:
            line_id: Production line ID
            scheduled_start: Start time in simulation minutes
            duration_hours: Order duration in hours
            
        Returns:
            Generated production order
        """
        # Select product based on line's product mix
        product_mix = self.product_mixes[line_id]
        product_id = self.random.choices(
            product_mix.products,
            weights=product_mix.weights
        )[0]
        
        product_info = self.product_catalog[product_id]
        
        # Calculate target volume based on duration and rate
        rate_per_min = product_info["rate_per_5min"] / 5.0
        duration_minutes = duration_hours * 60
        
        # Apply efficiency factor and variation to batch size
        base_volume = rate_per_min * duration_minutes * self.config.efficiency_factor
        variation = self.random.uniform(0.8, 1.2)
        target_volume = base_volume * variation
        
        # Generate order ID
        order_id = f"ORD-{self.order_counter}"
        self.order_counter += 1
        
        # Create order
        order = ProductionOrder(
            order_id=order_id,
            product_id=product_id,
            product_name=product_info["name"],
            target_volume=target_volume,
            line_id=line_id,
            scheduled_start=scheduled_start,
            scheduled_duration=duration_minutes,
            priority=self.random.randint(
                self.config.min_priority, 
                self.config.max_priority
            )
        )
        
        self.orders[order_id] = order
        self.line_schedules[line_id].append(order)
        self.total_orders_created += 1
        
        logger.debug(
            f"Created order {order_id}: {product_id} on Line {line_id}, "
            f"{target_volume:.0f} units, {duration_hours:.1f} hours"
        )
        
        return order
    
    def generate_initial_schedule(self, simulation_duration: float):
        """Generate initial production schedule for entire simulation.
        
        Args:
            simulation_duration: Total simulation duration in minutes
        """
        logger.info(f"Generating production schedule for {simulation_duration/60:.1f} hours")
        
        # Generate orders for each line
        for line_id in ["1", "2", "3"]:
            current_time = 0.0
            
            while current_time < simulation_duration:
                # Order duration varies based on configuration
                duration_hours = self.random.uniform(
                    self.config.min_order_duration_hours,
                    self.config.max_order_duration_hours
                )
                
                # Create order
                order = self.generate_order(
                    line_id=line_id,
                    scheduled_start=current_time,
                    duration_hours=duration_hours
                )
                
                # Add changeover time
                changeover_time = 0
                if len(self.line_schedules[line_id]) > 1:
                    prev_order = self.line_schedules[line_id][-2]
                    changeover_time = self.get_changeover_time(
                        prev_order.product_id,
                        order.product_id
                    )
                
                current_time += order.scheduled_duration + changeover_time
        
        # Sort schedules by start time
        for line_id in self.line_schedules:
            self.line_schedules[line_id].sort(key=lambda o: o.scheduled_start)
        
        logger.info(f"Generated {self.total_orders_created} production orders")
        for line_id, orders in self.line_schedules.items():
            logger.info(f"  Line {line_id}: {len(orders)} orders")
    
    def get_changeover_time(self, from_product: str, to_product: str) -> float:
        """Get changeover time between products.
        
        Args:
            from_product: Current product ID
            to_product: Next product ID
            
        Returns:
            Changeover time in minutes
        """
        return self.changeover_matrix.get((from_product, to_product), 30)
    
    def get_current_order(self, line_id: str) -> Optional[ProductionOrder]:
        """Get current production order for a line.
        
        Args:
            line_id: Production line ID
            
        Returns:
            Current order or None if no active order
        """
        # Check if we need to start a new order
        current_order = self.current_production[line_id]
        
        if current_order is None or current_order.status == OrderStatus.COMPLETED:
            # Find next scheduled order
            for order in self.line_schedules[line_id]:
                if order.status == OrderStatus.PENDING and order.scheduled_start <= self.env.now:
                    # Start this order
                    order.status = OrderStatus.IN_PROGRESS
                    order.actual_start = self.env.now
                    self.current_production[line_id] = order
                    logger.info(
                        f"Line {line_id} starting order {order.order_id}: "
                        f"{order.product_id} ({order.target_volume:.0f} units)"
                    )
                    return order
        
        return self.current_production[line_id]
    
    def update_order_progress(
        self,
        order_id: str,
        good_units: float,
        scrap_units: float
    ):
        """Update production progress for an order.
        
        Args:
            order_id: Order ID
            good_units: Good units produced
            scrap_units: Scrap units produced
        """
        if order_id not in self.orders:
            return
        
        order = self.orders[order_id]
        order.completed_volume += good_units
        order.scrap_volume += scrap_units
        
        # Check if order is complete
        if order.completed_volume >= order.target_volume:
            order.status = OrderStatus.COMPLETED
            order.actual_end = self.env.now
            self.total_orders_completed += 1
            
            # Clear from current production
            if self.current_production.get(order.line_id) == order:
                self.current_production[order.line_id] = None
            
            logger.info(
                f"Order {order_id} completed: {order.completed_volume:.0f} good units, "
                f"{order.scrap_volume:.0f} scrap units"
            )
    
    def schedule_changeover(self, line_id: str) -> Generator:
        """Schedule a changeover process for a line.
        
        Args:
            line_id: Production line ID
            
        Yields:
            SimPy timeout for changeover duration
        """
        current_order = self.current_production[line_id]
        
        # Find next order
        next_order = None
        for order in self.line_schedules[line_id]:
            if order.status == OrderStatus.PENDING:
                next_order = order
                break
        
        if current_order and next_order:
            changeover_time = self.get_changeover_time(
                current_order.product_id,
                next_order.product_id
            )
            
            if changeover_time > 0:
                logger.info(
                    f"Line {line_id} changeover: {current_order.product_id} -> "
                    f"{next_order.product_id} ({changeover_time:.0f} minutes)"
                )
                yield self.env.timeout(changeover_time)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_orders": self.total_orders_created,
            "completed_orders": self.total_orders_completed,
            "completion_rate": (
                self.total_orders_completed / self.total_orders_created * 100
                if self.total_orders_created > 0 else 0
            ),
            "orders_by_line": {},
            "orders_by_product": {}
        }
        
        # Orders by line
        for line_id, orders in self.line_schedules.items():
            stats["orders_by_line"][line_id] = {
                "total": len(orders),
                "completed": sum(1 for o in orders if o.status == OrderStatus.COMPLETED),
                "in_progress": sum(1 for o in orders if o.status == OrderStatus.IN_PROGRESS),
                "pending": sum(1 for o in orders if o.status == OrderStatus.PENDING)
            }
        
        # Orders by product
        for order in self.orders.values():
            product_id = order.product_id
            if product_id not in stats["orders_by_product"]:
                stats["orders_by_product"][product_id] = {
                    "total": 0,
                    "completed": 0,
                    "total_volume": 0,
                    "scrap_volume": 0
                }
            
            stats["orders_by_product"][product_id]["total"] += 1
            if order.status == OrderStatus.COMPLETED:
                stats["orders_by_product"][product_id]["completed"] += 1
            stats["orders_by_product"][product_id]["total_volume"] += order.completed_volume
            stats["orders_by_product"][product_id]["scrap_volume"] += order.scrap_volume
        
        return stats
    
    # Implementation of abstract methods from BaseScheduler
    
    def generate_schedule(
        self,
        lines: List[str],
        products: List[str],
        duration: float,
        **kwargs
    ) -> Dict[str, List[ProductionOrder]]:
        """Generate production schedule for given lines and products.
        
        This implementation uses a simple sequential scheduling algorithm
        with product mix based on historical patterns.
        
        Args:
            lines: List of production line IDs
            products: List of product IDs to schedule
            duration: Planning horizon in minutes
            **kwargs: Additional parameters (e.g., 'use_product_mix')
            
        Returns:
            Dictionary mapping line IDs to ordered lists of production orders
        """
        use_product_mix = kwargs.get('use_product_mix', True)
        
        # Clear existing schedules for specified lines
        for line_id in lines:
            self.line_schedules[line_id] = []
        
        # Generate orders for each line
        for line_id in lines:
            current_time = 0.0
            
            while current_time < duration:
                # Select product
                if use_product_mix and line_id in self.product_mixes:
                    # Use configured product mix
                    product_mix = self.product_mixes[line_id]
                    # Filter to only requested products
                    available_products = [p for p in product_mix.products if p in products]
                    if available_products:
                        product_id = self.random.choice(available_products)
                    else:
                        # No valid products for this line
                        break
                else:
                    # Random selection from available products
                    valid_products = [
                        p for p in products 
                        if line_id in self.product_catalog.get(p, {}).get('lines', [])
                    ]
                    if not valid_products:
                        break
                    product_id = self.random.choice(valid_products)
                
                # Generate order duration
                duration_hours = self.random.uniform(
                    self.config.min_order_duration_hours,
                    self.config.max_order_duration_hours
                )
                
                # Create order
                order = self.generate_order(
                    line_id=line_id,
                    scheduled_start=current_time,
                    duration_hours=duration_hours
                )
                
                # Add changeover time for next iteration
                if len(self.line_schedules[line_id]) > 1:
                    prev_order = self.line_schedules[line_id][-2]
                    changeover_time = self.get_changeover_time(
                        prev_order.product_id,
                        order.product_id
                    )
                    current_time += order.scheduled_duration + changeover_time
                else:
                    current_time += order.scheduled_duration
        
        # Sort schedules by start time
        for line_id in lines:
            self.line_schedules[line_id].sort(key=lambda o: o.scheduled_start)
        
        return {line_id: self.line_schedules[line_id] for line_id in lines}
    
    def optimize_schedule(
        self,
        current_schedule: Dict[str, List[ProductionOrder]],
        objective: str = "minimize_changeover",
        **kwargs
    ) -> Dict[str, List[ProductionOrder]]:
        """Optimize an existing schedule based on given objective.
        
        This is a simple implementation that reorders products to
        minimize changeover time within each line.
        
        Args:
            current_schedule: Current schedule to optimize
            objective: Optimization objective
            **kwargs: Additional optimization parameters
            
        Returns:
            Optimized schedule
        """
        if objective == "minimize_changeover":
            optimized = {}
            
            for line_id, orders in current_schedule.items():
                if len(orders) <= 2:
                    # Too few orders to optimize
                    optimized[line_id] = orders
                    continue
                
                # Group orders by product
                product_groups = {}
                for order in orders:
                    if order.product_id not in product_groups:
                        product_groups[order.product_id] = []
                    product_groups[order.product_id].append(order)
                
                # Build optimized sequence (campaign-based)
                new_sequence = []
                current_time = 0.0
                
                # Sort product groups by total volume (largest campaigns first)
                sorted_products = sorted(
                    product_groups.items(),
                    key=lambda x: sum(o.target_volume for o in x[1]),
                    reverse=True
                )
                
                for product_id, product_orders in sorted_products:
                    # Sort orders within product by priority
                    product_orders.sort(key=lambda o: o.priority, reverse=True)
                    
                    for order in product_orders:
                        # Update timing
                        order.scheduled_start = current_time
                        current_time += order.scheduled_duration
                        new_sequence.append(order)
                    
                    # Add changeover time if not last product
                    if product_id != sorted_products[-1][0]:
                        next_product = sorted_products[
                            sorted_products.index((product_id, product_orders)) + 1
                        ][0]
                        changeover = self.get_changeover_time(product_id, next_product)
                        current_time += changeover
                
                optimized[line_id] = new_sequence
            
            return optimized
        
        elif objective == "maximize_throughput":
            # Sort by processing rate (highest rate products first)
            optimized = {}
            
            for line_id, orders in current_schedule.items():
                sorted_orders = sorted(
                    orders,
                    key=lambda o: self.product_catalog.get(
                        o.product_id, {}
                    ).get('rate_per_5min', 0),
                    reverse=True
                )
                
                # Update timing
                current_time = 0.0
                for order in sorted_orders:
                    order.scheduled_start = current_time
                    current_time += order.scheduled_duration
                
                optimized[line_id] = sorted_orders
            
            return optimized
        
        else:
            # Unknown objective, return original schedule
            logger.warning(f"Unknown optimization objective: {objective}")
            return current_schedule
    
    def reschedule(
        self,
        disruption_time: float,
        disruption_type: str,
        affected_resources: List[str],
        **kwargs
    ) -> Dict[str, List[ProductionOrder]]:
        """Reschedule production after a disruption.
        
        This implementation delays affected orders and reschedules
        remaining production.
        
        Args:
            disruption_time: Time when disruption occurred
            disruption_type: Type of disruption
            affected_resources: List of affected line/equipment IDs
            **kwargs: Additional disruption details
            
        Returns:
            Updated schedule
        """
        disruption_duration = kwargs.get('duration', 60.0)  # Default 1 hour
        
        updated_schedules = {}
        
        for line_id, orders in self.line_schedules.items():
            if line_id not in affected_resources:
                # Line not affected
                updated_schedules[line_id] = orders
                continue
            
            updated_orders = []
            delay_remaining = False
            
            for order in orders:
                if order.status == OrderStatus.COMPLETED:
                    # Already completed, no change
                    updated_orders.append(order)
                
                elif order.status == OrderStatus.IN_PROGRESS:
                    if order.scheduled_start <= disruption_time:
                        # Order interrupted by disruption
                        # Calculate remaining work
                        completed_fraction = (
                            (disruption_time - order.scheduled_start) / 
                            order.scheduled_duration
                        )
                        remaining_duration = (
                            order.scheduled_duration * (1 - completed_fraction)
                        )
                        
                        # Reschedule remaining work after disruption
                        order.scheduled_start = disruption_time + disruption_duration
                        order.scheduled_duration = remaining_duration
                        updated_orders.append(order)
                        delay_remaining = True
                
                elif order.status == OrderStatus.PENDING:
                    if delay_remaining or order.scheduled_start >= disruption_time:
                        # Delay this and all subsequent orders
                        order.scheduled_start += disruption_duration
                        delay_remaining = True
                    updated_orders.append(order)
            
            updated_schedules[line_id] = updated_orders
        
        # Update internal schedules
        self.line_schedules = updated_schedules
        
        return updated_schedules