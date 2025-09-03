"""Production cost calculator for optimization.

This module provides comprehensive cost calculation for production
scheduling optimization, including production, changeover, inventory,
and quality costs.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .product_manifest import ProductManifest, Product
from .production_scheduler import ProductionOrder

logger = logging.getLogger(__name__)


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for analysis."""
    
    production_cost: float = 0.0
    changeover_cost: float = 0.0
    inventory_cost: float = 0.0
    quality_cost: float = 0.0
    waste_cost: float = 0.0
    labor_cost: float = 0.0
    energy_cost: float = 0.0
    overtime_cost: float = 0.0
    expedite_cost: float = 0.0
    total_cost: float = 0.0
    
    def calculate_total(self) -> float:
        """Calculate total cost from components."""
        self.total_cost = (
            self.production_cost +
            self.changeover_cost +
            self.inventory_cost +
            self.quality_cost +
            self.waste_cost +
            self.labor_cost +
            self.energy_cost +
            self.overtime_cost +
            self.expedite_cost
        )
        return self.total_cost
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'production': self.production_cost,
            'changeover': self.changeover_cost,
            'inventory': self.inventory_cost,
            'quality': self.quality_cost,
            'waste': self.waste_cost,
            'labor': self.labor_cost,
            'energy': self.energy_cost,
            'overtime': self.overtime_cost,
            'expedite': self.expedite_cost,
            'total': self.total_cost
        }


class ProductionCostCalculator:
    """Calculates comprehensive production costs for optimization."""
    
    def __init__(
        self,
        product_manifest: ProductManifest,
        labor_cost_per_hour: float = 25.0,
        energy_cost_per_kwh: float = 0.12,
        overtime_threshold_hours: float = 8.0,
        overtime_multiplier: float = 1.5
    ):
        """Initialize cost calculator.
        
        Args:
            product_manifest: Product manifest with specifications
            labor_cost_per_hour: Base labor cost per hour
            energy_cost_per_kwh: Energy cost per kilowatt-hour
            overtime_threshold_hours: Hours before overtime kicks in
            overtime_multiplier: Multiplier for overtime costs
        """
        self.manifest = product_manifest
        self.labor_cost_per_hour = labor_cost_per_hour
        self.energy_cost_per_kwh = energy_cost_per_kwh
        self.overtime_threshold_hours = overtime_threshold_hours
        self.overtime_multiplier = overtime_multiplier
        
        # Load cost factors from manifest if available
        if self.manifest.cost_factors:
            self.labor_cost_per_hour = self.manifest.cost_factors.get(
                'labor_cost_per_hour', labor_cost_per_hour
            )
            self.energy_cost_per_kwh = self.manifest.cost_factors.get(
                'energy_cost_per_kwh', energy_cost_per_kwh
            )
            self.overtime_multiplier = self.manifest.cost_factors.get(
                'overtime_cost_multiplier', overtime_multiplier
            )
    
    def calculate_order_cost(
        self,
        order: ProductionOrder,
        line_id: str,
        include_changeover: bool = True,
        previous_product: Optional[str] = None
    ) -> CostBreakdown:
        """Calculate total cost for a production order.
        
        Args:
            order: Production order to cost
            line_id: Production line ID
            include_changeover: Whether to include changeover costs
            previous_product: Previous product for changeover calculation
            
        Returns:
            Detailed cost breakdown
        """
        costs = CostBreakdown()
        
        product = self.manifest.get_product(order.product_id)
        if not product:
            logger.warning(f"Product {order.product_id} not found in manifest")
            return costs
        
        # Production costs
        costs.production_cost = self._calculate_production_cost(
            product, order.target_volume
        )
        
        # Labor costs
        duration_hours = order.scheduled_duration / 60.0
        costs.labor_cost = self._calculate_labor_cost(
            duration_hours, line_id
        )
        
        # Overtime costs if applicable
        if duration_hours > self.overtime_threshold_hours:
            overtime_hours = duration_hours - self.overtime_threshold_hours
            costs.overtime_cost = (
                overtime_hours * self.labor_cost_per_hour * 
                (self.overtime_multiplier - 1.0)
            )
        
        # Changeover costs
        if include_changeover and previous_product:
            costs.changeover_cost = self._calculate_changeover_cost(
                previous_product, order.product_id, line_id
            )
        
        # Waste costs
        costs.waste_cost = self._calculate_waste_cost(
            product, order.target_volume
        )
        
        # Quality costs
        costs.quality_cost = self._calculate_quality_cost(
            product, order.target_volume
        )
        
        # Inventory holding costs
        costs.inventory_cost = self._calculate_inventory_cost(
            product, order.target_volume, duration_hours
        )
        
        # Energy costs
        costs.energy_cost = self._calculate_energy_cost(
            product, order.target_volume, line_id
        )
        
        # Expedite costs if high priority
        if order.priority >= 8:
            expedite_multiplier = self.manifest.cost_factors.get(
                'expedite_cost_multiplier', 1.5
            )
            costs.expedite_cost = costs.production_cost * (expedite_multiplier - 1.0)
        
        costs.calculate_total()
        return costs
    
    def _calculate_production_cost(
        self,
        product: Product,
        volume: float
    ) -> float:
        """Calculate direct production costs.
        
        Args:
            product: Product specification
            volume: Production volume
            
        Returns:
            Production cost
        """
        unit_cost = (
            product.economics.material_cost +
            product.economics.packaging_cost +
            product.economics.overhead_cost
        )
        return volume * unit_cost
    
    def _calculate_labor_cost(
        self,
        duration_hours: float,
        line_id: str
    ) -> float:
        """Calculate labor costs.
        
        Args:
            duration_hours: Production duration in hours
            line_id: Production line ID
            
        Returns:
            Labor cost
        """
        # Could adjust by line if different lines have different staffing
        return duration_hours * self.labor_cost_per_hour
    
    def _calculate_changeover_cost(
        self,
        from_product_id: str,
        to_product_id: str,
        line_id: str
    ) -> float:
        """Calculate changeover costs.
        
        Args:
            from_product_id: Current product
            to_product_id: Next product
            line_id: Production line
            
        Returns:
            Changeover cost
        """
        # Get base changeover cost from manifest
        base_cost = self.manifest.get_changeover_cost(from_product_id, to_product_id)
        
        # Add time-based labor cost
        changeover_time_hours = self.manifest.get_changeover_time(
            from_product_id, to_product_id
        ) / 60.0
        labor_cost = changeover_time_hours * self.labor_cost_per_hour
        
        return base_cost + labor_cost
    
    def _calculate_waste_cost(
        self,
        product: Product,
        volume: float
    ) -> float:
        """Calculate waste and scrap costs.
        
        Args:
            product: Product specification
            volume: Production volume
            
        Returns:
            Waste cost
        """
        # Startup and shutdown waste
        waste_units = (
            product.production.startup_waste_units +
            product.production.shutdown_waste_units
        )
        
        # Expected scrap during production
        scrap_units = volume * product.production.scrap_rate
        
        # Total waste cost
        total_waste = waste_units + scrap_units
        waste_cost = total_waste * product.economics.total_standard_cost
        
        # Add disposal cost
        waste_weight_kg = total_waste * product.physical.fill_weight_g / 1000
        disposal_cost_per_kg = self.manifest.cost_factors.get(
            'waste_disposal_cost_per_kg', 0.05
        )
        disposal_cost = waste_weight_kg * disposal_cost_per_kg
        
        return waste_cost + disposal_cost
    
    def _calculate_quality_cost(
        self,
        product: Product,
        volume: float
    ) -> float:
        """Calculate quality inspection and defect costs.
        
        Args:
            product: Product specification
            volume: Production volume
            
        Returns:
            Quality cost
        """
        # Inspection costs
        inspection_cost_per_sample = self.manifest.cost_factors.get(
            'quality_inspection_cost_per_sample', 2.0
        )
        samples = volume * product.quality.sampling_rate
        inspection_cost = samples * inspection_cost_per_sample
        
        # Expected defect costs
        defect_cost = 0.0
        for defect_type, defect_info in product.quality.defect_categories.items():
            # Assume defect rate proportional to (1 - quality_rate)
            defect_rate = (1 - product.production.quality_rate) / len(
                product.quality.defect_categories
            )
            defect_units = volume * defect_rate
            defect_cost += defect_units * defect_info.get('cost', 0)
        
        return inspection_cost + defect_cost
    
    def _calculate_inventory_cost(
        self,
        product: Product,
        volume: float,
        duration_hours: float
    ) -> float:
        """Calculate inventory holding costs.
        
        Args:
            product: Product specification
            volume: Production volume
            duration_hours: Production duration
            
        Returns:
            Inventory holding cost
        """
        # Assume linear production and consumption
        average_inventory = volume / 2
        holding_days = duration_hours / 24
        
        holding_cost = (
            average_inventory *
            product.economics.holding_cost_per_day *
            holding_days
        )
        
        return holding_cost
    
    def _calculate_energy_cost(
        self,
        product: Product,
        volume: float,
        line_id: str
    ) -> float:
        """Calculate energy costs.
        
        Args:
            product: Product specification
            volume: Production volume
            line_id: Production line
            
        Returns:
            Energy cost
        """
        # Estimate energy consumption based on production rate
        # This is simplified - could be made more sophisticated
        production_time_hours = volume / (product.production.nominal_rate_per_min * 60)
        
        # Assume 10 kW base load per line (simplified)
        power_consumption_kw = 10.0
        
        # Adjust for line efficiency
        efficiency = self.manifest.get_line_efficiency(product.product_id, line_id)
        if efficiency:
            power_consumption_kw /= efficiency
        
        energy_kwh = production_time_hours * power_consumption_kw
        energy_cost = energy_kwh * self.energy_cost_per_kwh
        
        return energy_cost
    
    def calculate_schedule_cost(
        self,
        schedule: Dict[str, List[ProductionOrder]]
    ) -> Dict[str, Any]:
        """Calculate total cost for entire schedule.
        
        Args:
            schedule: Production schedule by line
            
        Returns:
            Cost summary with breakdown
        """
        total_costs = CostBreakdown()
        line_costs = {}
        product_costs = {}
        
        for line_id, orders in schedule.items():
            line_breakdown = CostBreakdown()
            previous_product = None
            
            for order in orders:
                # Calculate order cost
                order_cost = self.calculate_order_cost(
                    order=order,
                    line_id=line_id,
                    include_changeover=True,
                    previous_product=previous_product
                )
                
                # Accumulate line costs
                line_breakdown.production_cost += order_cost.production_cost
                line_breakdown.changeover_cost += order_cost.changeover_cost
                line_breakdown.inventory_cost += order_cost.inventory_cost
                line_breakdown.quality_cost += order_cost.quality_cost
                line_breakdown.waste_cost += order_cost.waste_cost
                line_breakdown.labor_cost += order_cost.labor_cost
                line_breakdown.energy_cost += order_cost.energy_cost
                line_breakdown.overtime_cost += order_cost.overtime_cost
                line_breakdown.expedite_cost += order_cost.expedite_cost
                
                # Track by product
                if order.product_id not in product_costs:
                    product_costs[order.product_id] = CostBreakdown()
                
                product_costs[order.product_id].production_cost += order_cost.production_cost
                product_costs[order.product_id].total_cost += order_cost.total_cost
                
                previous_product = order.product_id
            
            line_breakdown.calculate_total()
            line_costs[line_id] = line_breakdown
            
            # Accumulate total
            total_costs.production_cost += line_breakdown.production_cost
            total_costs.changeover_cost += line_breakdown.changeover_cost
            total_costs.inventory_cost += line_breakdown.inventory_cost
            total_costs.quality_cost += line_breakdown.quality_cost
            total_costs.waste_cost += line_breakdown.waste_cost
            total_costs.labor_cost += line_breakdown.labor_cost
            total_costs.energy_cost += line_breakdown.energy_cost
            total_costs.overtime_cost += line_breakdown.overtime_cost
            total_costs.expedite_cost += line_breakdown.expedite_cost
        
        total_costs.calculate_total()
        
        # Calculate cost metrics
        total_volume = sum(
            order.target_volume
            for orders in schedule.values()
            for order in orders
        )
        
        total_time = sum(
            order.scheduled_duration
            for orders in schedule.values()
            for order in orders
        )
        
        return {
            'total_cost': total_costs.total_cost,
            'cost_breakdown': total_costs.to_dict(),
            'cost_per_unit': total_costs.total_cost / total_volume if total_volume > 0 else 0,
            'cost_per_hour': total_costs.total_cost / (total_time / 60) if total_time > 0 else 0,
            'line_costs': {
                line_id: costs.to_dict()
                for line_id, costs in line_costs.items()
            },
            'product_costs': {
                product_id: costs.to_dict()
                for product_id, costs in product_costs.items()
            },
            'changeover_percentage': (
                total_costs.changeover_cost / total_costs.total_cost * 100
                if total_costs.total_cost > 0 else 0
            )
        }
    
    def compare_schedules(
        self,
        schedule1: Dict[str, List[ProductionOrder]],
        schedule2: Dict[str, List[ProductionOrder]],
        names: Tuple[str, str] = ("Schedule 1", "Schedule 2")
    ) -> Dict[str, Any]:
        """Compare costs between two schedules.
        
        Args:
            schedule1: First schedule
            schedule2: Second schedule
            names: Names for the schedules
            
        Returns:
            Comparison results
        """
        cost1 = self.calculate_schedule_cost(schedule1)
        cost2 = self.calculate_schedule_cost(schedule2)
        
        comparison = {
            names[0]: cost1,
            names[1]: cost2,
            'savings': cost1['total_cost'] - cost2['total_cost'],
            'savings_percentage': (
                (cost1['total_cost'] - cost2['total_cost']) / cost1['total_cost'] * 100
                if cost1['total_cost'] > 0 else 0
            ),
            'better_schedule': names[1] if cost2['total_cost'] < cost1['total_cost'] else names[0]
        }
        
        # Component-wise comparison
        breakdown1 = cost1['cost_breakdown']
        breakdown2 = cost2['cost_breakdown']
        
        comparison['component_savings'] = {
            component: breakdown1[component] - breakdown2[component]
            for component in breakdown1
        }
        
        return comparison
    
    def find_cost_drivers(
        self,
        schedule: Dict[str, List[ProductionOrder]]
    ) -> List[Dict[str, Any]]:
        """Identify main cost drivers in schedule.
        
        Args:
            schedule: Production schedule
            
        Returns:
            List of cost drivers sorted by impact
        """
        drivers = []
        
        for line_id, orders in schedule.items():
            previous_product = None
            
            for order in orders:
                order_cost = self.calculate_order_cost(
                    order=order,
                    line_id=line_id,
                    include_changeover=True,
                    previous_product=previous_product
                )
                
                # Identify significant cost components
                if order_cost.changeover_cost > order_cost.total_cost * 0.2:
                    drivers.append({
                        'type': 'changeover',
                        'line': line_id,
                        'from_product': previous_product,
                        'to_product': order.product_id,
                        'cost': order_cost.changeover_cost,
                        'percentage': order_cost.changeover_cost / order_cost.total_cost * 100
                    })
                
                if order_cost.overtime_cost > 0:
                    drivers.append({
                        'type': 'overtime',
                        'line': line_id,
                        'order': order.order_id,
                        'product': order.product_id,
                        'cost': order_cost.overtime_cost,
                        'duration_hours': order.scheduled_duration / 60
                    })
                
                if order_cost.waste_cost > order_cost.total_cost * 0.1:
                    drivers.append({
                        'type': 'waste',
                        'line': line_id,
                        'order': order.order_id,
                        'product': order.product_id,
                        'cost': order_cost.waste_cost,
                        'percentage': order_cost.waste_cost / order_cost.total_cost * 100
                    })
                
                previous_product = order.product_id
        
        # Sort by cost impact
        drivers.sort(key=lambda x: x['cost'], reverse=True)
        
        return drivers