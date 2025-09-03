"""Campaign-based scheduling optimizer.

Groups orders by product to minimize changeovers and maximize
campaign efficiency.
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from collections import defaultdict
import itertools

from .base_scheduler import BaseScheduler, SchedulerConfig, SchedulingConstraints, OrderStatus
from .production_scheduler import ProductionOrder
from .product_manifest import ProductManifest
from .cost_calculator import ProductionCostCalculator

logger = logging.getLogger(__name__)


@dataclass
class Campaign:
    """Represents a production campaign for a single product."""
    
    product_id: str
    orders: List[ProductionOrder]
    total_volume: float
    total_duration: float
    line_id: Optional[str] = None
    scheduled_start: Optional[float] = None
    
    def add_order(self, order: ProductionOrder) -> None:
        """Add order to campaign."""
        self.orders.append(order)
        self.total_volume += order.target_volume
        self.total_duration += order.scheduled_duration


class CampaignOptimizer(BaseScheduler):
    """Campaign-based scheduling optimizer.
    
    Groups orders by product to create campaigns that minimize
    changeovers and maximize efficiency.
    """
    
    def __init__(
        self,
        config: Optional[SchedulerConfig] = None,
        constraints: Optional[SchedulingConstraints] = None,
        product_manifest: Optional[ProductManifest] = None
    ):
        """Initialize campaign optimizer.
        
        Args:
            config: Scheduler configuration
            constraints: Scheduling constraints
            product_manifest: Product specifications
        """
        self.config = config or SchedulerConfig()
        self.constraints = constraints or SchedulingConstraints()
        self.product_manifest = product_manifest
        self.current_orders: Dict[str, ProductionOrder] = {}
        self.completed_orders: List[ProductionOrder] = []
        self.line_schedules: Dict[str, List[ProductionOrder]] = {}
        self.campaigns: List[Campaign] = []
    
    def generate_schedule(
        self,
        orders: List[ProductionOrder],
        lines: List[str],
        horizon_hours: Optional[float] = None,
        start_time: float = 0.0
    ) -> Dict[str, List[ProductionOrder]]:
        """Generate schedule using campaign optimization.
        
        Args:
            orders: List of production orders to schedule
            lines: Available production lines
            horizon_hours: Planning horizon in hours
            start_time: Start time for scheduling (simulation minutes)
            
        Returns:
            Schedule by line
        """
        # Group orders into campaigns by product
        campaigns = self._create_campaigns(orders)
        
        # Sort campaigns by priority and volume
        campaigns = self._prioritize_campaigns(campaigns)
        
        # Initialize schedule for each line
        schedule: Dict[str, List[ProductionOrder]] = {
            line: [] for line in lines
        }
        
        # Track next available time for each line (in minutes)
        line_availability: Dict[str, float] = {
            line: start_time for line in lines
        }
        
        # Track last product on each line for changeover calculation
        last_product_on_line: Dict[str, Optional[str]] = {
            line: None for line in lines
        }
        
        # Schedule campaigns
        for campaign in campaigns:
            # Find best line for campaign
            best_line = self._find_best_line_for_campaign(
                campaign, lines, line_availability, last_product_on_line
            )
            
            if not best_line:
                logger.warning(f"Could not schedule campaign for product {campaign.product_id}")
                continue
            
            # Calculate changeover time if needed
            changeover_time = 0.0
            last_product = last_product_on_line[best_line]
            if last_product and last_product != campaign.product_id:
                changeover_time = self._calculate_changeover_time(
                    last_product, campaign.product_id
                )
            
            # Schedule all orders in campaign
            campaign_start = line_availability[best_line] + changeover_time
            current_time = campaign_start
            
            for order in campaign.orders:
                order.line_id = best_line
                order.scheduled_start = current_time
                
                # Calculate duration based on product rate
                if self.product_manifest:
                    product = self.product_manifest.get_product(order.product_id)
                    if product:
                        rate_per_min = product.production.nominal_rate_per_min
                        # Apply line efficiency if available
                        efficiency = self._get_line_efficiency(order.product_id, best_line)
                        effective_rate = rate_per_min * efficiency
                        
                        if effective_rate > 0:
                            order.scheduled_duration = order.target_volume / effective_rate
                        else:
                            order.scheduled_duration = self.config.typical_order_duration_hours * 60
                    else:
                        order.scheduled_duration = self.config.typical_order_duration_hours * 60
                else:
                    order.scheduled_duration = self.config.typical_order_duration_hours * 60
                
                schedule[best_line].append(order)
                current_time += order.scheduled_duration
            
            # Update line availability and last product
            line_availability[best_line] = current_time
            last_product_on_line[best_line] = campaign.product_id
            
            # Check horizon constraint
            if horizon_hours and current_time > (start_time + horizon_hours * 60):
                logger.info(f"Reached planning horizon at {current_time} minutes")
                break
        
        self.line_schedules = schedule
        self.campaigns = campaigns
        return schedule
    
    def optimize_schedule(
        self,
        current_schedule: Dict[str, List[ProductionOrder]],
        cost_calculator: Optional[ProductionCostCalculator] = None
    ) -> Dict[str, List[ProductionOrder]]:
        """Optimize existing schedule using campaign resequencing.
        
        Args:
            current_schedule: Current schedule to optimize
            cost_calculator: Cost calculator for evaluation
            
        Returns:
            Optimized schedule
        """
        if not cost_calculator:
            logger.warning("No cost calculator provided - returning original schedule")
            return current_schedule
        
        best_schedule = current_schedule
        best_cost = cost_calculator.calculate_schedule_cost(current_schedule)['total_cost']
        
        # Try different campaign sequences on each line
        for line_id, orders in current_schedule.items():
            if len(orders) <= 1:
                continue
            
            # Group consecutive orders by product into mini-campaigns
            mini_campaigns = []
            current_campaign = [orders[0]]
            
            for i in range(1, len(orders)):
                if orders[i].product_id == orders[i-1].product_id:
                    current_campaign.append(orders[i])
                else:
                    mini_campaigns.append(current_campaign)
                    current_campaign = [orders[i]]
            mini_campaigns.append(current_campaign)
            
            # Try different permutations of mini-campaigns (limit to reasonable number)
            max_permutations = min(24, len(list(itertools.permutations(mini_campaigns))))
            tested = 0
            
            for perm in itertools.permutations(mini_campaigns):
                if tested >= max_permutations:
                    break
                tested += 1
                
                # Flatten permutation back to order list
                new_order_sequence = []
                for campaign in perm:
                    new_order_sequence.extend(campaign)
                
                # Update scheduled times
                current_time = orders[0].scheduled_start  # Keep same start time
                for order in new_order_sequence:
                    order.scheduled_start = current_time
                    current_time += order.scheduled_duration
                
                # Create test schedule
                test_schedule = current_schedule.copy()
                test_schedule[line_id] = new_order_sequence
                
                # Evaluate cost
                test_cost = cost_calculator.calculate_schedule_cost(test_schedule)['total_cost']
                
                if test_cost < best_cost:
                    best_cost = test_cost
                    best_schedule = test_schedule
                    logger.info(f"Found better sequence on {line_id}: cost reduced to ${best_cost:.2f}")
        
        return best_schedule
    
    def reschedule(
        self,
        disruption_time: float,
        disruption_type: str,
        affected_resources: List[str],
        current_schedule: Dict[str, List[ProductionOrder]]
    ) -> Dict[str, List[ProductionOrder]]:
        """Reschedule after disruption using campaign regrouping.
        
        Args:
            disruption_time: When disruption occurred (simulation time)
            disruption_type: Type of disruption
            affected_resources: Affected lines/resources
            current_schedule: Current schedule
            
        Returns:
            Updated schedule
        """
        logger.info(f"Campaign rescheduling due to {disruption_type} at time {disruption_time}")
        
        # Collect unfinished orders
        unfinished_orders = []
        for line_id, orders in current_schedule.items():
            for order in orders:
                if order.scheduled_start > disruption_time:
                    unfinished_orders.append(order)
                elif (order.scheduled_start <= disruption_time < 
                      order.scheduled_start + order.scheduled_duration):
                    # Order was in progress
                    progress = (disruption_time - order.scheduled_start) / order.scheduled_duration
                    remaining_volume = order.target_volume * (1 - progress)
                    
                    if remaining_volume > 0:
                        new_order = ProductionOrder(
                            order_id=f"{order.order_id}_R",
                            product_id=order.product_id,
                            product_name=order.product_name,
                            target_volume=remaining_volume,
                            line_id=order.line_id,
                            scheduled_start=0,
                            scheduled_duration=1,  # Will be recalculated (set to 1 for validation)
                            priority=order.priority + 1,
                            status=OrderStatus.PENDING
                        )
                        unfinished_orders.append(new_order)
        
        # Get available lines
        available_lines = [
            line for line in current_schedule.keys()
            if line not in affected_resources
        ]
        
        # Reschedule with campaign optimization
        if available_lines:
            return self.generate_schedule(
                orders=unfinished_orders,
                lines=available_lines,
                start_time=disruption_time + 60
            )
        else:
            logger.warning("No available lines for rescheduling")
            return current_schedule
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get scheduler performance metrics.
        
        Returns:
            Metrics dictionary
        """
        total_orders = sum(len(orders) for orders in self.line_schedules.values())
        total_campaigns = len(self.campaigns)
        total_changeover_time = 0.0
        campaign_lengths = []
        
        for line_id, orders in self.line_schedules.items():
            last_product = None
            campaign_start = None
            
            for i, order in enumerate(orders):
                if last_product and last_product != order.product_id:
                    # Campaign ended
                    if campaign_start is not None:
                        campaign_length = order.scheduled_start - campaign_start
                        campaign_lengths.append(campaign_length / 60)  # Convert to hours
                    
                    # Add changeover time
                    total_changeover_time += self._calculate_changeover_time(
                        last_product, order.product_id
                    )
                    campaign_start = order.scheduled_start
                elif campaign_start is None:
                    campaign_start = order.scheduled_start
                
                last_product = order.product_id
        
        metrics = {
            'total_orders_scheduled': total_orders,
            'total_campaigns': total_campaigns,
            'lines_utilized': len([l for l, o in self.line_schedules.items() if o]),
            'total_changeover_time_minutes': total_changeover_time,
            'average_changeover_minutes': (
                total_changeover_time / total_campaigns if total_campaigns > 0 else 0
            ),
            'average_campaign_length_hours': (
                sum(campaign_lengths) / len(campaign_lengths) if campaign_lengths else 0
            ),
            'min_campaign_length_hours': min(campaign_lengths) if campaign_lengths else 0,
            'max_campaign_length_hours': max(campaign_lengths) if campaign_lengths else 0
        }
        
        return metrics
    
    def _create_campaigns(self, orders: List[ProductionOrder]) -> List[Campaign]:
        """Group orders into campaigns by product.
        
        Args:
            orders: List of orders to group
            
        Returns:
            List of campaigns
        """
        campaigns_dict: Dict[str, Campaign] = {}
        
        for order in orders:
            if order.product_id not in campaigns_dict:
                campaigns_dict[order.product_id] = Campaign(
                    product_id=order.product_id,
                    orders=[],
                    total_volume=0,
                    total_duration=0
                )
            campaigns_dict[order.product_id].add_order(order)
        
        return list(campaigns_dict.values())
    
    def _prioritize_campaigns(self, campaigns: List[Campaign]) -> List[Campaign]:
        """Prioritize campaigns for scheduling.
        
        Args:
            campaigns: List of campaigns to prioritize
            
        Returns:
            Sorted list of campaigns
        """
        # Calculate campaign priority score
        for campaign in campaigns:
            # Average priority of orders in campaign
            avg_priority = sum(o.priority for o in campaign.orders) / len(campaign.orders)
            # Boost for larger campaigns (economies of scale)
            volume_boost = min(campaign.total_volume / 10000, 2.0)
            campaign.priority_score = avg_priority + volume_boost
        
        # Sort by priority score (higher first)
        return sorted(campaigns, key=lambda c: c.priority_score, reverse=True)
    
    def _find_best_line_for_campaign(
        self,
        campaign: Campaign,
        lines: List[str],
        line_availability: Dict[str, float],
        last_product_on_line: Dict[str, Optional[str]]
    ) -> Optional[str]:
        """Find best line for campaign considering efficiency and changeover.
        
        Args:
            campaign: Campaign to schedule
            lines: Available lines
            line_availability: Current availability of each line
            last_product_on_line: Last product scheduled on each line
            
        Returns:
            Best line ID or None if no compatible line
        """
        compatible_lines = self._get_compatible_lines(campaign.product_id, lines)
        
        if not compatible_lines:
            return None
        
        best_line = None
        best_score = float('inf')
        
        for line in compatible_lines:
            # Calculate score (lower is better)
            # Start with availability time
            score = line_availability[line]
            
            # Add changeover penalty
            last_product = last_product_on_line[line]
            if last_product and last_product != campaign.product_id:
                changeover_time = self._calculate_changeover_time(
                    last_product, campaign.product_id
                )
                score += changeover_time * 2  # Weight changeover heavily
            
            # Subtract efficiency bonus
            efficiency = self._get_line_efficiency(campaign.product_id, line)
            score -= efficiency * 100  # Bonus for higher efficiency
            
            if score < best_score:
                best_score = score
                best_line = line
        
        return best_line
    
    def _get_line_efficiency(self, product_id: str, line_id: str) -> float:
        """Get efficiency of product on line.
        
        Args:
            product_id: Product ID
            line_id: Line ID
            
        Returns:
            Efficiency factor (0-1)
        """
        if self.product_manifest:
            efficiency = self.product_manifest.get_line_efficiency(product_id, line_id)
            if efficiency is not None:
                return efficiency
        
        # Default efficiency from config
        return self.config.efficiency_factor
    
    def _get_compatible_lines(self, product_id: str, available_lines: List[str]) -> List[str]:
        """Get lines compatible with product.
        
        Args:
            product_id: Product ID
            available_lines: List of available lines
            
        Returns:
            List of compatible lines
        """
        compatible = []
        
        # Check constraints first
        if self.constraints.product_line_compatibility:
            if product_id in self.constraints.product_line_compatibility:
                allowed = self.constraints.product_line_compatibility[product_id]
                compatible = [l for l in available_lines if l in allowed]
        
        # Check product manifest for line efficiency
        if not compatible and self.product_manifest:
            product = self.product_manifest.get_product(product_id)
            if product and product.production.efficiency_by_line:
                compatible = [
                    l for l in available_lines
                    if l in product.production.efficiency_by_line
                    and product.production.efficiency_by_line[l] is not None
                    and product.production.efficiency_by_line[l] > 0
                ]
        
        # Fall back to all lines if no compatibility info
        if not compatible:
            compatible = available_lines
        
        return compatible
    
    def _calculate_changeover_time(self, from_product: str, to_product: str) -> float:
        """Calculate changeover time between products.
        
        Args:
            from_product: Current product ID
            to_product: Next product ID
            
        Returns:
            Changeover time in minutes
        """
        if self.product_manifest:
            return self.product_manifest.get_changeover_time(from_product, to_product)
        
        # Use config defaults
        if from_product == to_product:
            return 0.0
        
        from_family = from_product.split('-')[0] if '-' in from_product else from_product
        to_family = to_product.split('-')[0] if '-' in to_product else to_product
        
        if from_family == to_family:
            return self.config.same_family_changeover_minutes
        else:
            return self.config.different_family_changeover_minutes