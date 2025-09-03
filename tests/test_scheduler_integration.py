"""Test scheduler integration with simulation."""

import sys
from pathlib import Path
import simpy
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from twin_model.scheduling.scheduler_integration import SchedulerSimulationBridge
from twin_model.scheduling.product_manifest import ProductManifest
from twin_model.scheduling.base_scheduler import SchedulerConfig, SchedulingConstraints
from twin_model.primitives.source_flow import SourceFlow


def test_sequential_scheduler():
    """Test sequential scheduler integration."""
    print("\n=== Testing Sequential Scheduler ===")
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Load product manifest
    manifest = ProductManifest()
    manifest.load_from_yaml(Path("config/product_manifest.yaml"))
    
    # Create scheduler bridge
    bridge = SchedulerSimulationBridge(
        env=env,
        scheduler_type="sequential",
        product_manifest=manifest
    )
    
    # Create mock sources for lines (simplified - normally these would be real SourceFlow instances)
    for line_id in ['Line1', 'Line2', 'Line3']:
        # Create a simple mock source
        source = type('MockSource', (), {'add_order': lambda self, order: None})()
        bridge.register_line_source(line_id, source)
    
    # Generate orders
    orders = bridge.generate_orders(num_orders=10)
    print(f"Generated {len(orders)} orders")
    
    # Schedule orders
    schedule = bridge.schedule_orders(orders, horizon_hours=48)
    
    # Print schedule
    for line_id, line_orders in schedule.items():
        print(f"\n{line_id}:")
        for order in line_orders[:3]:  # Show first 3 orders per line
            print(f"  {order.order_id}: {order.product_id} @ {order.scheduled_start:.1f} min")
            print(f"    Volume: {order.target_volume}, Duration: {order.scheduled_duration:.1f} min")
    
    # Get metrics
    metrics = bridge.get_schedule_metrics()
    print(f"\nMetrics:")
    print(f"  Orders scheduled: {metrics['orders_scheduled']}")
    print(f"  Lines utilized: {metrics.get('lines_utilized', 'N/A')}")
    
    return bridge


def test_campaign_optimizer():
    """Test campaign optimizer integration."""
    print("\n=== Testing Campaign Optimizer ===")
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Load product manifest
    manifest = ProductManifest()
    manifest.load_from_yaml(Path("config/product_manifest.yaml"))
    
    # Create scheduler bridge with campaign optimizer
    bridge = SchedulerSimulationBridge(
        env=env,
        scheduler_type="campaign",
        product_manifest=manifest
    )
    
    # Register mock lines
    for line_id in ['Line1', 'Line2', 'Line3']:
        source = type('MockSource', (), {'add_order': lambda self, order: None})()
        bridge.register_line_source(line_id, source)
    
    # Generate orders with product repetition for campaigns
    products = ['SKU-1001', 'SKU-1001', 'SKU-2001', 'SKU-2001', 'SKU-3001']
    orders = []
    for i in range(15):
        order_idx = len(orders) + 1
        product_id = products[i % len(products)]
        
        product = manifest.get_product(product_id)
        from twin_model.scheduling.production_scheduler import ProductionOrder
        from twin_model.scheduling.base_scheduler import OrderStatus
        orders.append(ProductionOrder(
            order_id=f"ORD-{order_idx:04d}",
            product_id=product_id,
            product_name=product.name if product else product_id,
            target_volume=10000 + (i * 1000),
            line_id="TBD",
            scheduled_start=0,
            scheduled_duration=1,  # Will be recalculated
            priority=5 + (i % 3),
            status=OrderStatus.PENDING
        ))
    
    # Schedule with campaign optimization
    schedule = bridge.schedule_orders(orders, horizon_hours=72, optimize=True)
    
    # Print campaign groups
    for line_id, line_orders in schedule.items():
        if not line_orders:
            continue
        print(f"\n{line_id} Campaigns:")
        
        current_product = None
        campaign_start = None
        campaign_orders = []
        
        for order in line_orders:
            if order.product_id != current_product:
                # Print previous campaign
                if campaign_orders:
                    total_volume = sum(o.target_volume for o in campaign_orders)
                    duration = campaign_orders[-1].scheduled_start + campaign_orders[-1].scheduled_duration - campaign_start
                    print(f"  Campaign: {current_product}")
                    print(f"    Orders: {len(campaign_orders)}, Volume: {total_volume:,}")
                    print(f"    Start: {campaign_start:.1f}, Duration: {duration:.1f} min")
                
                # Start new campaign
                current_product = order.product_id
                campaign_start = order.scheduled_start
                campaign_orders = [order]
            else:
                campaign_orders.append(order)
        
        # Print last campaign
        if campaign_orders:
            total_volume = sum(o.target_volume for o in campaign_orders)
            duration = campaign_orders[-1].scheduled_start + campaign_orders[-1].scheduled_duration - campaign_start
            print(f"  Campaign: {current_product}")
            print(f"    Orders: {len(campaign_orders)}, Volume: {total_volume:,}")
            print(f"    Start: {campaign_start:.1f}, Duration: {duration:.1f} min")
    
    # Get metrics
    metrics = bridge.get_schedule_metrics()
    print(f"\nCampaign Metrics:")
    print(f"  Total campaigns: {metrics.get('total_campaigns', 'N/A')}")
    print(f"  Avg campaign length: {metrics.get('average_campaign_length_hours', 0):.1f} hours")
    print(f"  Total changeover time: {metrics.get('total_changeover_time_minutes', 0):.1f} min")
    
    return bridge


def test_line_efficiency():
    """Test that line efficiency mapping works correctly."""
    print("\n=== Testing Line Efficiency ===")
    
    # Load product manifest
    manifest = ProductManifest()
    manifest.load_from_yaml(Path("config/product_manifest.yaml"))
    
    # Test efficiency lookups with different line ID formats
    test_cases = [
        ('SKU-1001', 'Line1'),
        ('SKU-1001', '1'),
        ('SKU-2001', 'Line2'),
        ('SKU-2001', '2'),
        ('SKU-3001', 'Line3'),
        ('SKU-3001', '3'),
    ]
    
    for product_id, line_id in test_cases:
        efficiency = manifest.get_line_efficiency(product_id, line_id)
        product = manifest.get_product(product_id)
        
        if efficiency is not None:
            print(f"{product_id} on {line_id}: {efficiency:.1%} efficiency")
        else:
            print(f"{product_id} on {line_id}: Not compatible")
    
    return manifest


def test_schedule_optimization():
    """Test schedule optimization with cost calculation."""
    print("\n=== Testing Schedule Optimization ===")
    
    # Create environment and load manifest
    env = simpy.Environment()
    manifest = ProductManifest()
    manifest.load_from_yaml(Path("config/product_manifest.yaml"))
    
    # Create config with constraints
    config = SchedulerConfig(
        same_family_changeover_minutes=15,
        different_family_changeover_minutes=30,
        cleaning_changeover_minutes=45
    )
    
    constraints = SchedulingConstraints(
        product_line_compatibility={
            'SKU-1001': ['Line1', 'Line2'],
            'SKU-1002': ['Line1', 'Line2'],
            'SKU-2001': ['Line2', 'Line3'],
            'SKU-2002': ['Line1', 'Line2', 'Line3'],
            'SKU-3001': ['Line2', 'Line3'],
            'SKU-3002': ['Line1', 'Line2', 'Line3']
        }
    )
    
    # Create bridge with campaign optimizer
    bridge = SchedulerSimulationBridge(
        env=env,
        scheduler_type="campaign",
        config=config,
        constraints=constraints,
        product_manifest=manifest
    )
    
    # Register lines
    for line_id in ['Line1', 'Line2', 'Line3']:
        source = type('MockSource', (), {'add_order': lambda self, order: None})()
        bridge.register_line_source(line_id, source)
    
    # Generate diverse orders
    orders = bridge.generate_orders(num_orders=20)
    
    # Schedule without optimization
    schedule_no_opt = bridge.schedule_orders(orders, optimize=False)
    metrics_no_opt = bridge.get_schedule_metrics()
    
    # Reset and schedule with optimization
    bridge.metrics['orders_scheduled'] = 0
    schedule_opt = bridge.schedule_orders(orders, optimize=True)
    metrics_opt = bridge.get_schedule_metrics()
    
    print("\nWithout Optimization:")
    print(f"  Total cost: ${metrics_no_opt.get('total_cost', 0):.2f}")
    print(f"  Changeover time: {metrics_no_opt.get('total_changeover_time_minutes', 0):.1f} min")
    
    print("\nWith Optimization:")
    print(f"  Total cost: ${metrics_opt.get('total_cost', 0):.2f}")
    print(f"  Changeover time: {metrics_opt.get('total_changeover_time_minutes', 0):.1f} min")
    
    if 'total_cost' in metrics_no_opt and 'total_cost' in metrics_opt:
        savings = metrics_no_opt['total_cost'] - metrics_opt['total_cost']
        print(f"\nOptimization Savings: ${savings:.2f}")
    
    return bridge


def test_disruption_handling():
    """Test disruption handling and rescheduling."""
    print("\n=== Testing Disruption Handling ===")
    
    # Setup
    env = simpy.Environment()
    manifest = ProductManifest()
    manifest.load_from_yaml(Path("config/product_manifest.yaml"))
    
    bridge = SchedulerSimulationBridge(
        env=env,
        scheduler_type="sequential",
        product_manifest=manifest
    )
    
    # Register lines
    for line_id in ['Line1', 'Line2', 'Line3']:
        source = type('MockSource', (), {'add_order': lambda self, order: None})()
        bridge.register_line_source(line_id, source)
    
    # Generate and schedule orders
    orders = bridge.generate_orders(num_orders=12)
    initial_schedule = bridge.schedule_orders(orders)
    
    print("\nInitial Schedule:")
    for line_id, line_orders in initial_schedule.items():
        if line_orders:
            print(f"  {line_id}: {len(line_orders)} orders")
    
    # Simulate time passing
    env.run(until=120)  # Run for 2 hours
    
    # Trigger disruption on Line2
    print(f"\nDisruption at time {env.now:.1f} minutes")
    new_schedule = bridge.handle_disruption(
        disruption_type="equipment_failure",
        affected_lines=['Line2'],
        duration_minutes=60
    )
    
    print("\nRescheduled after disruption:")
    for line_id, line_orders in new_schedule.items():
        if line_orders:
            print(f"  {line_id}: {len(line_orders)} orders")
            # Show first rescheduled order
            if line_orders:
                first_order = line_orders[0]
                print(f"    First: {first_order.order_id} @ {first_order.scheduled_start:.1f} min")
    
    return bridge


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("SCHEDULER INTEGRATION TESTS")
    print("=" * 60)
    
    # Run tests
    test_line_efficiency()
    test_sequential_scheduler()
    test_campaign_optimizer()
    test_schedule_optimization()
    test_disruption_handling()
    
    print("\n" + "=" * 60)
    print("ALL INTEGRATION TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()