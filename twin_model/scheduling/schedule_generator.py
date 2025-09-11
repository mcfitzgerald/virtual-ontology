"""Production Schedule Generator for Sub-Optimal Baseline.

This module generates realistic but sub-optimal production schedules
that naturally lead to 45-55% OEE through poor sequencing and planning.
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import yaml

from .production_scheduler import ProductionOrder, OrderStatus

logger = logging.getLogger(__name__)


@dataclass
class ScheduleGeneratorConfig:
    """Configuration for schedule generation."""
    
    # Scheduling strategy
    sequence_mode: str = "random"  # random, family_grouping, optimized
    batch_sizing: str = "fixed"  # fixed, dynamic, optimal
    
    # Batch size constraints (hours)
    min_batch_hours: float = 2.0  # Too short - causes excessive changeovers
    max_batch_hours: float = 6.0  # Too short for efficient production
    
    # Product mix percentages
    product_mix: Dict[str, float] = None
    
    # Changeover penalties
    changeover_frequency_target: float = 0.15  # Target 15% changeover time
    
    # Line assignment strategy
    line_assignment: str = "random"  # random, capability_based, optimized
    
    def __post_init__(self):
        """Set default product mix if not provided."""
        if self.product_mix is None:
            self.product_mix = {
                "SKU-1001": 0.20,  # 20% Water
                "SKU-1002": 0.15,  # 15% Juice
                "SKU-2001": 0.30,  # 30% Soda
                "SKU-2002": 0.20,  # 20% Energy
                "SKU-3001": 0.10,  # 10% Sports
                "SKU-3002": 0.05,  # 5% Premium Juice
            }


class SubOptimalScheduleGenerator:
    """Generates sub-optimal production schedules for baseline MES data."""
    
    def __init__(
        self,
        config: Optional[ScheduleGeneratorConfig] = None,
        product_manifest_path: Optional[Path] = None,
        random_seed: Optional[int] = None
    ):
        """Initialize schedule generator.
        
        Args:
            config: Generator configuration
            product_manifest_path: Path to product manifest YAML
            random_seed: Random seed for reproducibility
        """
        self.config = config or ScheduleGeneratorConfig()
        self.product_info = {}
        self.line_capabilities = {}
        
        if random_seed:
            random.seed(random_seed)
        
        # Load product information
        if product_manifest_path and product_manifest_path.exists():
            self._load_product_manifest(product_manifest_path)
        else:
            self._setup_default_products()
    
    def _load_product_manifest(self, manifest_path: Path):
        """Load product information from manifest."""
        try:
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
            
            products = manifest.get('products', {})
            
            for product_id, product_data in products.items():
                self.product_info[product_id] = {
                    'name': product_data.get('name', product_id),
                    'family': product_data.get('family', 'default'),
                    'nominal_rate': product_data.get('production', {}).get('nominal_rate_per_min', 95),
                    'line_compatibility': product_data.get('line_compatibility', {}),
                    'changeover_group': product_data.get('changeover', {}).get('group', 'default')
                }
            
            logger.info(f"Loaded {len(self.product_info)} products from manifest")
            
        except Exception as e:
            logger.error(f"Failed to load product manifest: {e}")
            self._setup_default_products()
    
    def _setup_default_products(self):
        """Set up default product information."""
        self.product_info = {
            "SKU-1001": {
                'name': "8oz Water Bottle",
                'family': 'water',
                'nominal_rate': 95,
                'changeover_group': 'water',
                'line_compatibility': {
                    'LINE1': {'capable': True, 'efficiency': 0.95},
                    'LINE2': {'capable': True, 'efficiency': 0.92},
                    'LINE3': {'capable': False, 'efficiency': 0.0}
                }
            },
            "SKU-1002": {
                'name': "8oz Juice",
                'family': 'juice',
                'nominal_rate': 95,
                'changeover_group': 'juice',
                'line_compatibility': {
                    'LINE1': {'capable': True, 'efficiency': 0.90},
                    'LINE2': {'capable': True, 'efficiency': 0.93},
                    'LINE3': {'capable': False, 'efficiency': 0.0}
                }
            },
            "SKU-2001": {
                'name': "12oz Soda",
                'family': 'soda',
                'nominal_rate': 95,
                'changeover_group': 'soda',
                'line_compatibility': {
                    'LINE1': {'capable': False, 'efficiency': 0.0},
                    'LINE2': {'capable': True, 'efficiency': 0.94},
                    'LINE3': {'capable': True, 'efficiency': 0.96}
                }
            },
            "SKU-2002": {
                'name': "16oz Energy Drink",
                'family': 'energy',
                'nominal_rate': 90,
                'changeover_group': 'energy',
                'line_compatibility': {
                    'LINE1': {'capable': True, 'efficiency': 0.88},
                    'LINE2': {'capable': True, 'efficiency': 0.91},
                    'LINE3': {'capable': True, 'efficiency': 0.93}
                }
            },
            "SKU-3001": {
                'name': "20oz Sports Drink",
                'family': 'sports',
                'nominal_rate': 90,
                'changeover_group': 'sports',
                'line_compatibility': {
                    'LINE1': {'capable': False, 'efficiency': 0.0},
                    'LINE2': {'capable': True, 'efficiency': 0.89},
                    'LINE3': {'capable': True, 'efficiency': 0.92}
                }
            },
            "SKU-3002": {
                'name': "1L Juice",
                'family': 'premium_juice',
                'nominal_rate': 85,
                'changeover_group': 'juice',
                'line_compatibility': {
                    'LINE1': {'capable': True, 'efficiency': 0.85},
                    'LINE2': {'capable': True, 'efficiency': 0.88},
                    'LINE3': {'capable': True, 'efficiency': 0.90}
                }
            }
        }
    
    def generate_schedule(
        self,
        duration_days: int = 14,
        start_date: Optional[datetime] = None
    ) -> List[ProductionOrder]:
        """Generate a sub-optimal production schedule.
        
        Args:
            duration_days: Number of days to schedule
            start_date: Start date for schedule
            
        Returns:
            List of production orders
        """
        if not start_date:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        orders = []
        order_counter = 1000
        current_time = 0.0  # Minutes from start
        total_minutes = duration_days * 24 * 60
        
        # Track what's running on each line
        line_status = {
            "LINE1": {"product": None, "until": 0},
            "LINE2": {"product": None, "until": 0},
            "LINE3": {"product": None, "until": 0}
        }
        
        while current_time < total_minutes:
            # Find available lines
            available_lines = [
                line for line, status in line_status.items()
                if status["until"] <= current_time
            ]
            
            if not available_lines:
                # Jump to next line availability
                next_available = min(status["until"] for status in line_status.values())
                current_time = next_available
                continue
            
            # Choose a line (sub-optimally)
            if self.config.line_assignment == "random":
                line = random.choice(available_lines)
            else:
                line = available_lines[0]
            
            # Choose a product (sub-optimally)
            product = self._choose_product_suboptimally(line, line_status[line]["product"])
            
            if not product:
                # Skip this line for now
                line_status[line]["until"] = current_time + 60  # Try again in an hour
                continue
            
            # Determine batch size (sub-optimally)
            batch_hours = self._determine_batch_size_suboptimally(product)
            batch_minutes = batch_hours * 60
            
            # Calculate production volume
            product_info = self.product_info[product]
            nominal_rate = product_info['nominal_rate']
            line_efficiency = product_info['line_compatibility'].get(line, {}).get('efficiency', 0.9)
            
            # Apply sub-optimal performance factor
            performance_factor = random.uniform(0.75, 0.85)  # Sub-optimal performance
            
            effective_rate = nominal_rate * line_efficiency * performance_factor
            target_volume = effective_rate * batch_minutes
            
            # Create order
            order = ProductionOrder(
                order_id=f"ORD-{order_counter}",
                product_id=product,
                product_name=product_info['name'],
                target_volume=target_volume,
                line_id=line.replace("LINE", ""),  # Convert LINE1 to 1
                scheduled_start=current_time,
                scheduled_duration=batch_minutes,
                priority=random.randint(3, 7),  # Random priority
                status=OrderStatus.PENDING
            )
            
            orders.append(order)
            
            # Update line status
            line_status[line] = {
                "product": product,
                "until": current_time + batch_minutes
            }
            
            order_counter += 1
            current_time = line_status[line]["until"]
            
            # Add random delays between orders (inefficiency)
            if random.random() < 0.2:  # 20% chance of delay
                delay = random.uniform(15, 45)  # 15-45 minute delays
                line_status[line]["until"] += delay
        
        logger.info(f"Generated {len(orders)} production orders over {duration_days} days")
        
        # Calculate changeover metrics
        self._log_changeover_metrics(orders)
        
        return orders
    
    def _choose_product_suboptimally(
        self,
        line: str,
        previous_product: Optional[str]
    ) -> Optional[str]:
        """Choose next product sub-optimally to increase changeovers.
        
        Args:
            line: Production line ID
            previous_product: Previously produced product
            
        Returns:
            Selected product ID or None
        """
        # Get capable products for this line
        capable_products = []
        for product_id, info in self.product_info.items():
            compatibility = info['line_compatibility'].get(line, {})
            if compatibility.get('capable', False):
                capable_products.append(product_id)
        
        if not capable_products:
            return None
        
        if self.config.sequence_mode == "random":
            # Random selection (causes excessive changeovers)
            weights = [self.config.product_mix.get(p, 0.1) for p in capable_products]
            return random.choices(capable_products, weights=weights)[0]
        
        elif self.config.sequence_mode == "worst_case":
            # Deliberately choose products that require cleaning
            if previous_product:
                prev_group = self.product_info[previous_product]['changeover_group']
                
                # Find products from different groups
                different_group = [
                    p for p in capable_products
                    if self.product_info[p]['changeover_group'] != prev_group
                ]
                
                if different_group:
                    weights = [self.config.product_mix.get(p, 0.1) for p in different_group]
                    return random.choices(different_group, weights=weights)[0]
        
        # Default to weighted random
        weights = [self.config.product_mix.get(p, 0.1) for p in capable_products]
        return random.choices(capable_products, weights=weights)[0]
    
    def _determine_batch_size_suboptimally(self, product: str) -> float:
        """Determine batch size sub-optimally (too small).
        
        Args:
            product: Product ID
            
        Returns:
            Batch size in hours
        """
        if self.config.batch_sizing == "fixed":
            # Fixed small batches (causes frequent changeovers)
            return random.uniform(
                self.config.min_batch_hours,
                self.config.max_batch_hours
            )
        
        elif self.config.batch_sizing == "random":
            # Random sizes with bias toward small
            base_size = random.uniform(
                self.config.min_batch_hours,
                self.config.max_batch_hours
            )
            # Bias toward smaller batches
            return base_size * random.uniform(0.6, 1.0)
        
        else:
            # Default to configured range
            return random.uniform(
                self.config.min_batch_hours,
                self.config.max_batch_hours
            )
    
    def _log_changeover_metrics(self, orders: List[ProductionOrder]):
        """Log changeover metrics for validation.
        
        Args:
            orders: List of production orders
        """
        # Group orders by line
        lines = {}
        for order in orders:
            line = f"LINE{order.line_id}"
            if line not in lines:
                lines[line] = []
            lines[line].append(order)
        
        total_changeovers = 0
        total_changeover_time = 0
        total_production_time = sum(order.scheduled_duration for order in orders)
        
        for line, line_orders in lines.items():
            # Sort by start time
            line_orders.sort(key=lambda x: x.scheduled_start)
            
            # Count changeovers
            for i in range(1, len(line_orders)):
                if line_orders[i].product_id != line_orders[i-1].product_id:
                    total_changeovers += 1
                    
                    # Estimate changeover time
                    prev_group = self.product_info[line_orders[i-1].product_id]['changeover_group']
                    curr_group = self.product_info[line_orders[i].product_id]['changeover_group']
                    
                    if prev_group == curr_group:
                        changeover_time = 15  # Same group
                    else:
                        changeover_time = 45  # Different group
                    
                    total_changeover_time += changeover_time
        
        changeover_percentage = (total_changeover_time / (total_production_time + total_changeover_time)) * 100
        
        logger.info(f"Schedule metrics:")
        logger.info(f"  - Total orders: {len(orders)}")
        logger.info(f"  - Total changeovers: {total_changeovers}")
        logger.info(f"  - Changeover time: {total_changeover_time:.0f} minutes")
        logger.info(f"  - Production time: {total_production_time:.0f} minutes")
        logger.info(f"  - Changeover percentage: {changeover_percentage:.1f}%")
        
        if changeover_percentage < 10:
            logger.warning("Changeover percentage is low - schedule may be too optimal")
        elif changeover_percentage > 20:
            logger.warning("Changeover percentage is very high - schedule may be too sub-optimal")