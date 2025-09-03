"""Test product manifest integration with scheduler and cost calculator."""

import sys
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from twin_model.scheduling.product_manifest import ProductManifest
from twin_model.scheduling.cost_calculator import ProductionCostCalculator
from twin_model.scheduling.production_scheduler import ProductionOrder, OrderStatus
from datetime import datetime, timedelta


def test_product_manifest_loading():
    """Test loading product manifest from YAML."""
    print("\n=== Testing Product Manifest Loading ===")
    
    manifest_path = Path("config/product_manifest.yaml")
    manifest = ProductManifest()
    manifest.load_from_yaml(manifest_path)
    
    # Test product retrieval
    products = ['SKU-1001', 'SKU-2001', 'SKU-3001']
    for product_id in products:
        product = manifest.get_product(product_id)
        print(f"\n{product_id}: {product.name}")
        print(f"  - Base cost: ${product.economics.total_standard_cost:.2f}")
        print(f"  - Sale price: ${product.economics.sale_price:.2f}")
        print(f"  - Target rate: {product.production.target_rate_5min} units/5min")
    
    return manifest


def test_changeover_calculations(manifest: ProductManifest):
    """Test changeover time and cost calculations."""
    print("\n=== Testing Changeover Calculations ===")
    
    test_pairs = [
        ('SKU-1001', 'SKU-1002'),  # Same family (water to juice)
        ('SKU-1001', 'SKU-2001'),  # Different group
        ('SKU-2001', 'SKU-3001'),  # With cleaning
    ]
    
    for from_product, to_product in test_pairs:
        time = manifest.get_changeover_time(from_product, to_product)
        cost = manifest.get_changeover_cost(from_product, to_product)
        print(f"\n{from_product} → {to_product}:")
        print(f"  - Time: {time:.0f} minutes")
        print(f"  - Cost: ${cost:.2f}")
    
    return manifest


def test_line_efficiency(manifest: ProductManifest):
    """Test line efficiency lookups."""
    print("\n=== Testing Line Efficiency ===")
    
    products = ['SKU-1001', 'SKU-2001', 'SKU-3001']
    lines = ['Line1', 'Line2', 'Line3']
    
    for product_id in products:
        print(f"\n{product_id}:")
        for line_id in lines:
            efficiency = manifest.get_line_efficiency(product_id, line_id)
            if efficiency:
                print(f"  - {line_id}: {efficiency:.1%} efficiency")
            else:
                print(f"  - {line_id}: Not compatible")


def test_cost_calculator(manifest: ProductManifest):
    """Test cost calculator with sample orders."""
    print("\n=== Testing Cost Calculator ===")
    
    calculator = ProductionCostCalculator(manifest)
    
    # Create sample orders using the correct ProductionOrder structure
    from twin_model.scheduling.production_scheduler import ProductionOrder
    
    orders = [
        ProductionOrder(
            order_id="ORD-001",
            product_id="SKU-1001",
            product_name="8oz Water Bottle",
            target_volume=10000,
            line_id="Line2",
            scheduled_start=0.0,
            scheduled_duration=240.0,  # 4 hours in minutes
            priority=5,
            status=OrderStatus.PENDING
        ),
        ProductionOrder(
            order_id="ORD-002",
            product_id="SKU-2001",
            product_name="12oz Soda",
            target_volume=15000,
            line_id="Line2",
            scheduled_start=240.0,
            scheduled_duration=360.0,  # 6 hours in minutes
            priority=7,
            status=OrderStatus.PENDING
        ),
    ]
    
    # Calculate costs for each order
    for i, order in enumerate(orders):
        previous_product = orders[i-1].product_id if i > 0 else None
        line_id = order.line_id
        
        cost_breakdown = calculator.calculate_order_cost(
            order=order,
            line_id=line_id,
            include_changeover=True,
            previous_product=previous_product
        )
        
        print(f"\n{order.order_id} ({order.product_id}):")
        print(f"  - Production cost: ${cost_breakdown.production_cost:.2f}")
        print(f"  - Changeover cost: ${cost_breakdown.changeover_cost:.2f}")
        print(f"  - Inventory cost: ${cost_breakdown.inventory_cost:.2f}")
        print(f"  - Total cost: ${cost_breakdown.total_cost:.2f}")
        unit_cost = cost_breakdown.total_cost / order.target_volume if order.target_volume > 0 else 0
        print(f"  - Unit cost: ${unit_cost:.4f}")


def test_campaign_cost_calculation(manifest: ProductManifest):
    """Test campaign cost calculations."""
    print("\n=== Testing Campaign Cost Calculation ===")
    
    # Test individual product campaigns
    test_campaigns = [
        ('SKU-1001', 50000, 8.0, 'Line1'),
        ('SKU-2001', 40000, 6.0, 'Line2'),
        ('SKU-3001', 30000, 4.0, 'Line3'),
    ]
    
    for product_id, volume, duration_hours, line_id in test_campaigns:
        campaign_cost = manifest.calculate_campaign_cost(
            product_id=product_id,
            volume=volume,
            duration_hours=duration_hours,
            line_id=line_id
        )
        
        product = manifest.get_product(product_id)
        print(f"\nCampaign: {product.name} on {line_id}")
        print(f"  - Volume: {volume:,} units")
        print(f"  - Duration: {duration_hours:.1f} hours")
        print(f"  - Cost breakdown:")
        for key, value in campaign_cost.items():
            print(f"    - {key}: ${value:.2f}")


def test_schedule_cost_comparison():
    """Test comparing two different schedules."""
    print("\n=== Testing Schedule Cost Comparison ===")
    
    from twin_model.scheduling.production_scheduler import ProductionOrder
    
    manifest = ProductManifest()
    manifest.load_from_yaml(Path("config/product_manifest.yaml"))
    calculator = ProductionCostCalculator(manifest)
    
    # Schedule 1: Poor sequencing (many changeovers)
    schedule1 = {
        'Line1': [
            ProductionOrder("S1-1", "SKU-1001", "8oz Water", 10000, "Line1", 0.0, 240.0, 5, OrderStatus.PENDING),
            ProductionOrder("S1-2", "SKU-2001", "12oz Soda", 10000, "Line1", 240.0, 240.0, 5, OrderStatus.PENDING),
            ProductionOrder("S1-3", "SKU-1001", "8oz Water", 10000, "Line1", 480.0, 240.0, 5, OrderStatus.PENDING),
        ]
    }
    
    # Schedule 2: Better sequencing (grouped by product)
    schedule2 = {
        'Line1': [
            ProductionOrder("S2-1", "SKU-1001", "8oz Water", 10000, "Line1", 0.0, 240.0, 5, OrderStatus.PENDING),
            ProductionOrder("S2-2", "SKU-1001", "8oz Water", 10000, "Line1", 240.0, 240.0, 5, OrderStatus.PENDING),
            ProductionOrder("S2-3", "SKU-2001", "12oz Soda", 10000, "Line1", 480.0, 240.0, 5, OrderStatus.PENDING),
        ]
    }
    
    # Calculate costs
    cost1 = calculator.calculate_schedule_cost(schedule1)
    cost2 = calculator.calculate_schedule_cost(schedule2)
    
    # Compare
    comparison = calculator.compare_schedules(schedule1, schedule2)
    
    print("\nSchedule 1 (poor sequencing):")
    print(f"  - Total cost: ${cost1['total_cost']:.2f}")
    print(f"  - Changeover cost: ${cost1['cost_breakdown']['changeover']:.2f}")
    
    print("\nSchedule 2 (better sequencing):")
    print(f"  - Total cost: ${cost2['total_cost']:.2f}")
    print(f"  - Changeover cost: ${cost2['cost_breakdown']['changeover']:.2f}")
    
    print(f"\nSavings with better sequencing: ${comparison['savings']:.2f}")
    changeover_savings = comparison['component_savings'].get('changeover', 0) if 'component_savings' in comparison else 0
    print(f"Changeover reduction: ${changeover_savings:.2f}")


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("PRODUCT MANIFEST INTEGRATION TESTS")
    print("=" * 60)
    
    # Run tests
    manifest = test_product_manifest_loading()
    test_changeover_calculations(manifest)
    test_line_efficiency(manifest)
    test_cost_calculator(manifest)
    test_campaign_cost_calculation(manifest)
    test_schedule_cost_comparison()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()