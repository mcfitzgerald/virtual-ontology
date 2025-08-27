"""Test production order system.

This module tests the production order dispatch and tracking system.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import simpy

from twin_model.control.control_manager import ControlManager
from twin_model.model_builder import OntologyDrivenModelBuilderV2 as ModelBuilder
from twin_model.primitives.scheduler import (
    Product,
    ProductCategory,
    ProductionOrder,
    SchedulerPrimitiveV2,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_orders(scheduler: SchedulerPrimitiveV2) -> List[ProductionOrder]:
    """Create test production orders.
    
    Args:
        scheduler: Scheduler to get product definitions from
    
    Returns:
        List of test orders
    """
    orders = []
    
    # Create products if not already defined
    if not scheduler.products:
        scheduler.products = {
            "SKU-1001": Product(
                product_id="SKU-1001",
                category=ProductCategory.A,
                family="Beverages",
                volume_rank=1,
                margin=0.35,
                complexity=0.3,
                typical_batch_size=100,
                min_batch_size=50,
                max_batch_size=500
            ),
            "SKU-2001": Product(
                product_id="SKU-2001",
                category=ProductCategory.B,
                family="Juices",
                volume_rank=3,
                margin=0.45,
                complexity=0.5,
                typical_batch_size=75,
                min_batch_size=30,
                max_batch_size=300
            ),
            "SKU-3001": Product(
                product_id="SKU-3001",
                category=ProductCategory.C,
                family="Kids",
                volume_rank=5,
                margin=0.25,
                complexity=0.4,
                typical_batch_size=150,
                min_batch_size=75,
                max_batch_size=600
            ),
        }
    
    # Create orders for different lines
    orders.append(ProductionOrder(
        order_id="ORD-TEST-001",
        product=scheduler.products["SKU-1001"],
        quantity=500,
        due_date=240,  # Due at 4 hours
        priority=1,
        release_date=0
    ))
    orders[-1].line_id = "LINE1"  # Add line assignment
    
    orders.append(ProductionOrder(
        order_id="ORD-TEST-002",
        product=scheduler.products["SKU-2001"],
        quantity=300,
        due_date=360,  # Due at 6 hours
        priority=2,
        release_date=0
    ))
    orders[-1].line_id = "LINE2"
    
    orders.append(ProductionOrder(
        order_id="ORD-TEST-003",
        product=scheduler.products["SKU-3001"],
        quantity=750,
        due_date=480,  # Due at 8 hours
        priority=1,
        release_date=0
    ))
    orders[-1].line_id = "LINE3"
    
    # Second order for LINE1 (should queue)
    orders.append(ProductionOrder(
        order_id="ORD-TEST-004",
        product=scheduler.products["SKU-2001"],
        quantity=400,
        due_date=600,  # Due at 10 hours
        priority=3,
        release_date=240  # Release at 4 hours
    ))
    orders[-1].line_id = "LINE1"
    
    return orders


def test_order_dispatch():
    """Test order dispatch to sources."""
    logger.info("\n" + "="*60)
    logger.info("Testing Order Dispatch System")
    logger.info("="*60)
    
    # Create environment
    env = simpy.Environment()
    
    # Set up paths
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    # Initialize control manager
    control_mgr = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml"
    )
    
    # Create model builder
    builder = ModelBuilder(
        env=env,
        ontology_path=ontology_path,
        manifest_dir=manifest_dir,
        control_manager=control_mgr
    )
    
    # Build model
    model = builder.build_model()
    
    # Get scheduler
    scheduler = None
    for prim_id, primitive in model['primitives'].items():
        if isinstance(primitive, SchedulerPrimitiveV2):
            scheduler = primitive
            break
    
    if not scheduler:
        logger.error("No scheduler found in model!")
        return
    
    # Create test orders
    orders = create_test_orders(scheduler)
    
    # Add orders to scheduler
    for order in orders:
        scheduler.add_order(order)
    
    logger.info(f"Added {len(orders)} orders to scheduler")
    
    # Run simulation for a short time
    sim_duration = 60  # 1 hour to test dispatch
    env.run(until=sim_duration)
    
    # Check results
    logger.info("\n" + "-"*40)
    logger.info("Order Dispatch Results:")
    logger.info("-"*40)
    
    # Check active orders per line
    for line_id, order in scheduler.active_orders.items():
        if order:
            logger.info(f"{line_id}: Processing {order.order_id} ({order.product.product_id})")
            logger.info(f"  Started: {order.actual_start:.1f} min")
            logger.info(f"  Progress: {order.completed_quantity}/{order.quantity} units")
    
    # Check sources
    for line_id, source in scheduler.line_sources.items():
        if source.current_order:
            logger.info(f"\nSource {source.config.id} (Line {line_id}):")
            logger.info(f"  Current order: {source.current_order.order_id}")
            logger.info(f"  Units remaining: {source.units_remaining}")
            logger.info(f"  Total generated: {source.total_generated}")
        if source.order_queue:
            logger.info(f"  Queued orders: {[o.order_id for o in source.order_queue]}")
    
    logger.info(f"\nScheduler stats:")
    logger.info(f"  Orders scheduled: {scheduler.orders_scheduled}")
    logger.info(f"  Orders completed: {scheduler.orders_completed}")
    logger.info(f"  Pending orders: {len(scheduler.pending_orders)}")


def test_order_completion():
    """Test order completion and metrics."""
    logger.info("\n" + "="*60)
    logger.info("Testing Order Completion")
    logger.info("="*60)
    
    # Create environment
    env = simpy.Environment()
    
    # Set up paths
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    # Initialize control manager
    control_mgr = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml"
    )
    
    # Create model builder
    builder = ModelBuilder(
        env=env,
        ontology_path=ontology_path,
        manifest_dir=manifest_dir,
        control_manager=control_mgr
    )
    
    # Build model
    model = builder.build_model()
    
    # Get scheduler
    scheduler = None
    for prim_id, primitive in model['primitives'].items():
        if isinstance(primitive, SchedulerPrimitiveV2):
            scheduler = primitive
            break
    
    # Create a small order for quick completion
    if scheduler:
        scheduler.products["TEST-SKU"] = Product(
            product_id="TEST-SKU",
            category=ProductCategory.A,
            family="Test",
            volume_rank=1,
            margin=0.5,
            complexity=0.1,
            typical_batch_size=10,
            min_batch_size=5,
            max_batch_size=20
        )
        
        test_order = ProductionOrder(
            order_id="ORD-QUICK-001",
            product=scheduler.products["TEST-SKU"],
            quantity=50,  # Small quantity for quick completion
            due_date=60,
            priority=1,
            release_date=0
        )
        test_order.line_id = "LINE1"
        
        scheduler.add_order(test_order)
        
        # Run for enough time to complete the order
        env.run(until=10)  # 10 minutes should be enough for 50 units
        
        # Check completion
        logger.info("\n" + "-"*40)
        logger.info("Order Completion Results:")
        logger.info("-"*40)
        
        if scheduler.completed_orders:
            for order in scheduler.completed_orders:
                logger.info(f"Completed: {order.order_id}")
                logger.info(f"  Quantity: {order.completed_quantity}/{order.quantity}")
                logger.info(f"  Duration: {order.actual_end - order.actual_start:.1f} min")
                logger.info(f"  Tardiness: {order.tardiness:.1f} min")
        else:
            logger.info("No orders completed yet")
            if "LINE1" in scheduler.active_orders:
                active = scheduler.active_orders["LINE1"]
                if active:
                    logger.info(f"Active order: {active.order_id}")
                    logger.info(f"  Progress: {active.completed_quantity}/{active.quantity}")


def test_continuous_vs_order_mode():
    """Test continuous generation vs order-driven modes."""
    logger.info("\n" + "="*60)
    logger.info("Testing Continuous vs Order-Driven Modes")
    logger.info("="*60)
    
    # Test order-driven mode (default)
    logger.info("\n--- Order-Driven Mode ---")
    env1 = simpy.Environment()
    
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    control_mgr1 = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml"
    )
    
    builder1 = ModelBuilder(
        env=env1,
        ontology_path=ontology_path,
        manifest_dir=manifest_dir,
        control_manager=control_mgr1
    )
    
    model1 = builder1.build_model()
    
    # Find a source and check its mode
    for prim_id, primitive in model1['primitives'].items():
        if prim_id.startswith("SOURCE"):
            logger.info(f"Source {prim_id}:")
            logger.info(f"  Order mode: {primitive.order_mode}")
            logger.info(f"  Line: {primitive.line_id}")
            break
    
    # Run briefly
    env1.run(until=5)
    
    # Check generation (should be minimal without orders)
    for prim_id, primitive in model1['primitives'].items():
        if prim_id.startswith("SOURCE"):
            logger.info(f"  Units generated (no orders): {primitive.total_generated}")
            break
    
    # Test continuous mode
    logger.info("\n--- Continuous Mode ---")
    env2 = simpy.Environment()
    
    control_mgr2 = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml"
    )
    
    builder2 = ModelBuilder(
        env=env2,
        ontology_path=ontology_path,
        manifest_dir=manifest_dir,
        control_manager=control_mgr2
    )
    
    model2 = builder2.build_model()
    
    # Switch a source to continuous mode
    for prim_id, primitive in model2['primitives'].items():
        if prim_id.startswith("SOURCE"):
            primitive.order_mode = False  # Switch to continuous
            logger.info(f"Source {prim_id} switched to continuous mode")
            break
    
    # Run briefly
    env2.run(until=5)
    
    # Check generation (should have generated units)
    for prim_id, primitive in model2['primitives'].items():
        if prim_id.startswith("SOURCE"):
            logger.info(f"  Units generated (continuous): {primitive.total_generated}")
            expected = primitive.arrival_rate * 5  # 5 minutes
            logger.info(f"  Expected ~{expected:.0f} units at rate {primitive.arrival_rate}/min")
            break


def main():
    """Run all tests."""
    test_order_dispatch()
    test_order_completion()
    test_continuous_vs_order_mode()
    
    logger.info("\n" + "="*60)
    logger.info("Production Order Tests Complete!")
    logger.info("="*60)


if __name__ == "__main__":
    main()