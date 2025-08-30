"""Test changeover modeling and optimization.

This module tests product changeover times, setup scrap, and
campaign optimization strategies.
"""

import logging
from pathlib import Path

import simpy

from twin_model.control.control_manager import ControlManager
from twin_model.model_builder import OntologyDrivenModelBuilder as ModelBuilder
from twin_model.primitives.scheduler import (
    ProductionOrder,
    SchedulerPrimitive,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_changeover_matrix():
    """Test product-to-product changeover time calculations."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Changeover Matrix")
    logger.info("=" * 60)

    # Create environment
    env = simpy.Environment()

    # Set up paths
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")

    # Initialize control manager
    control_mgr = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml",
    )

    # Create model builder
    builder = ModelBuilder(env=env, ontology_path=ontology_path, manifest_dir=manifest_dir, control_manager=control_mgr)

    # Build model
    model = builder.build_model()

    # Get scheduler
    scheduler = None
    for prim_id, primitive in model["primitives"].items():
        if isinstance(primitive, SchedulerPrimitive):
            scheduler = primitive
            break

    if not scheduler:
        logger.error("No scheduler found!")
        return

    # Test changeover times
    test_cases = [
        ("SKU-1001", "SKU-1001"),  # Same product
        ("SKU-1001", "SKU-1002"),  # Same family (Beverages)
        ("SKU-1001", "SKU-2001"),  # Different family (Beverages -> Juices)
        ("SKU-1001", "SKU-3001"),  # Different family (Beverages -> Kids)
        ("SKU-2001", "SKU-3001"),  # Different family (Juices -> Kids)
    ]

    logger.info("\nChangeover Times:")
    logger.info("-" * 40)
    for from_prod, to_prod in test_cases:
        time = scheduler.changeover_matrix.get_changeover_time(from_prod, to_prod)
        from_family = scheduler.products[from_prod].family if from_prod in scheduler.products else "Unknown"
        to_family = scheduler.products[to_prod].family if to_prod in scheduler.products else "Unknown"

        logger.info(f"{from_prod} ({from_family}) -> {to_prod} ({to_family}): {time:.1f} min")

    # Test allergen changeovers (should be longer)
    logger.info("\nAllergen Changeovers:")
    logger.info("-" * 40)
    allergen_tests = [
        ("SKU-3001", "SKU-1001"),  # Kids (allergen) -> Beverages
        ("SKU-1001", "SKU-3001"),  # Beverages -> Kids (allergen)
    ]

    for from_prod, to_prod in allergen_tests:
        time = scheduler.changeover_matrix.get_changeover_time(from_prod, to_prod)
        from_family = scheduler.products[from_prod].family if from_prod in scheduler.products else "Unknown"
        to_family = scheduler.products[to_prod].family if to_prod in scheduler.products else "Unknown"

        logger.info(f"{from_prod} ({from_family}) -> {to_prod} ({to_family}): {time:.1f} min")


def test_changeover_execution():
    """Test changeover execution in production."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Changeover Execution")
    logger.info("=" * 60)

    # Create environment
    env = simpy.Environment()

    # Set up paths
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")

    # Initialize control manager
    control_mgr = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml",
    )

    # Create model builder
    builder = ModelBuilder(env=env, ontology_path=ontology_path, manifest_dir=manifest_dir, control_manager=control_mgr)

    # Build model
    model = builder.build_model()

    # Get scheduler and sources
    scheduler = None
    sources = {}

    for prim_id, primitive in model["primitives"].items():
        if isinstance(primitive, SchedulerPrimitive):
            scheduler = primitive
            # Store scheduler reference in environment for sources
            env.scheduler = scheduler
            env.control_manager = control_mgr
        elif prim_id.startswith("SOURCE"):
            sources[prim_id] = primitive

    if not scheduler:
        logger.error("No scheduler found!")
        return

    # Create orders with different products to trigger changeovers
    orders = [
        ProductionOrder(
            order_id="ORD-CO-001",
            product=scheduler.products["SKU-1001"],
            quantity=50,  # Small order to finish quickly
            due_date=120,
            priority=1,
            release_date=0,
        ),
        ProductionOrder(
            order_id="ORD-CO-002",
            product=scheduler.products["SKU-2001"],  # Different family
            quantity=50,
            due_date=240,
            priority=1,
            release_date=0,
        ),
        ProductionOrder(
            order_id="ORD-CO-003",
            product=scheduler.products["SKU-3001"],  # Allergen family
            quantity=50,
            due_date=360,
            priority=1,
            release_date=0,
        ),
    ]

    # Assign all to LINE1 for testing
    for order in orders:
        order.line_id = "LINE1"
        scheduler.add_order(order)

    # Track changeover events
    changeover_events = []

    def track_changeover(data):
        changeover_events.append({"time": env.now, "data": data})

    # Subscribe to changeover events from sources
    for source_id, source in sources.items():
        if hasattr(source, "observables"):
            if "changeover_started" not in source.observables:
                source.observables["changeover_started"] = []
            source.observables["changeover_started"].append(track_changeover)

            if "changeover_completed" not in source.observables:
                source.observables["changeover_completed"] = []
            source.observables["changeover_completed"].append(track_changeover)

    # Run simulation
    env.run(until=180)  # Run for 3 hours

    # Report results
    logger.info("\n" + "-" * 40)
    logger.info("Changeover Events:")
    logger.info("-" * 40)

    for event in changeover_events:
        time = event["time"]
        data = event["data"]
        if "duration" in data:
            logger.info(
                f"[{time:.1f}] Changeover started: {data.get('from_product', 'None')} -> "
                f"{data.get('to_product', 'Unknown')} ({data['duration']:.1f} min)"
            )
        else:
            logger.info(f"[{time:.1f}] Changeover completed: Now producing {data.get('product', 'Unknown')}")
            if "setup_scrap" in data:
                logger.info(f"  Setup units: {data.get('setup_units', 0)}, Scrapped: {data.get('setup_scrap', 0)}")

    # Check source metrics
    logger.info("\n" + "-" * 40)
    logger.info("Source Changeover Metrics:")
    logger.info("-" * 40)

    for source_id, source in sources.items():
        if source.changeover_count > 0:
            logger.info(f"{source_id}:")
            logger.info(f"  Changeovers: {source.changeover_count}")
            logger.info(f"  Total changeover time: {source.total_changeover_time:.1f} min")
            logger.info(f"  Setup units scrapped: {source.setup_units_scrapped}")
            availability = (env.now - source.total_changeover_time) / env.now * 100
            logger.info(f"  Availability (excl. changeover): {availability:.1f}%")


def test_smed_impact():
    """Test impact of SMED (changeover reduction) on productivity."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing SMED Impact on Changeovers")
    logger.info("=" * 60)

    results = {}

    for smed_level in [0, 1, 2]:
        logger.info(f"\n--- SMED Level {smed_level} ---")

        # Create environment
        env = simpy.Environment()

        # Set up paths
        ontology_path = Path("ontology/twin_ontology.yaml")
        manifest_dir = Path("manifests")

        # Initialize control manager
        control_mgr = ControlManager(
            ontology_path=ontology_path,
            mappings_path=Path("ontology/control_mappings.yaml"),
            settings_path=manifest_dir / "control_settings.yaml",
        )

        # Set SMED level
        control_mgr.set_control_value("changeover_reduction_level", smed_level)

        # Create model builder
        builder = ModelBuilder(
            env=env, ontology_path=ontology_path, manifest_dir=manifest_dir, control_manager=control_mgr
        )

        # Build model
        model = builder.build_model()

        # Store references
        env.control_manager = control_mgr

        # Get scheduler and sources
        scheduler = None
        sources = {}

        for prim_id, primitive in model["primitives"].items():
            if isinstance(primitive, SchedulerPrimitive):
                scheduler = primitive
                env.scheduler = scheduler
            elif prim_id.startswith("SOURCE"):
                sources[prim_id] = primitive

        # Create mixed product orders
        products = ["SKU-1001", "SKU-2001", "SKU-3001", "SKU-1002", "SKU-2002"]
        orders = []

        for i, product_id in enumerate(products * 2):  # 10 orders total
            order = ProductionOrder(
                order_id=f"ORD-SMED-{i + 1:03d}",
                product=scheduler.products[product_id],
                quantity=30,  # Small batches to trigger more changeovers
                due_date=480,
                priority=1,
                release_date=0,
            )
            order.line_id = "LINE1"
            orders.append(order)
            scheduler.add_order(order)

        # Run simulation
        env.run(until=240)  # 4 hours

        # Collect metrics
        total_changeover_time = 0
        total_units = 0

        for source_id, source in sources.items():
            if source.line_id == "LINE1":
                total_changeover_time = source.total_changeover_time
                total_units = source.total_generated
                break

        results[smed_level] = {
            "changeover_time": total_changeover_time,
            "units_produced": total_units,
            "productivity": total_units / 240 if env.now > 0 else 0,
        }

        logger.info(f"Total changeover time: {total_changeover_time:.1f} min")
        logger.info(f"Units produced: {total_units}")
        logger.info(f"Productivity: {results[smed_level]['productivity']:.2f} units/min")

    # Compare results
    logger.info("\n" + "-" * 40)
    logger.info("SMED Impact Summary:")
    logger.info("-" * 40)

    if results[0]["changeover_time"] > 0:
        for level in [1, 2]:
            time_reduction = (1 - results[level]["changeover_time"] / results[0]["changeover_time"]) * 100
            productivity_gain = ((results[level]["productivity"] / results[0]["productivity"]) - 1) * 100

            logger.info(f"SMED Level {level}:")
            logger.info(f"  Changeover time reduction: {time_reduction:.1f}%")
            logger.info(f"  Productivity improvement: {productivity_gain:.1f}%")


def test_campaign_optimization():
    """Test campaign mode vs mixed production."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Campaign Optimization")
    logger.info("=" * 60)

    # Test mixed production first
    logger.info("\n--- Mixed Production (Changeover Optimized) ---")
    env1 = simpy.Environment()

    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")

    control_mgr1 = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml",
    )

    builder1 = ModelBuilder(
        env=env1, ontology_path=ontology_path, manifest_dir=manifest_dir, control_manager=control_mgr1
    )

    model1 = builder1.build_model()

    # Set strategy to changeover_optimized
    scheduler1 = None
    for prim_id, primitive in model1["primitives"].items():
        if isinstance(primitive, SchedulerPrimitive):
            scheduler1 = primitive
            scheduler1.strategy = "changeover_optimized"
            env1.scheduler = scheduler1
            break

    # Create diverse orders
    order_sequence = ["SKU-1001", "SKU-2001", "SKU-3001", "SKU-1002", "SKU-2002"] * 3
    for i, product_id in enumerate(order_sequence):
        order = ProductionOrder(
            order_id=f"ORD-MIX-{i + 1:03d}",
            product=scheduler1.products[product_id],
            quantity=40,
            due_date=720,
            priority=1,
            release_date=0,
        )
        order.line_id = "LINE1"
        scheduler1.add_order(order)

    env1.run(until=480)

    mixed_changeovers = scheduler1.changeover_count
    mixed_changeover_time = scheduler1.total_changeover_time

    logger.info(f"Changeovers: {mixed_changeovers}")
    logger.info(f"Total changeover time: {mixed_changeover_time:.1f} min")

    # Test campaign mode
    logger.info("\n--- Campaign Mode Production ---")
    env2 = simpy.Environment()

    control_mgr2 = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml",
    )

    builder2 = ModelBuilder(
        env=env2, ontology_path=ontology_path, manifest_dir=manifest_dir, control_manager=control_mgr2
    )

    model2 = builder2.build_model()

    # Set strategy to campaign mode
    scheduler2 = None
    for prim_id, primitive in model2["primitives"].items():
        if isinstance(primitive, SchedulerPrimitive):
            scheduler2 = primitive
            scheduler2.strategy = "campaign_mode"
            env2.scheduler = scheduler2
            break

    # Create same orders but will be grouped in campaigns
    for i, product_id in enumerate(order_sequence):
        order = ProductionOrder(
            order_id=f"ORD-CAMP-{i + 1:03d}",
            product=scheduler2.products[product_id],
            quantity=40,
            due_date=720,
            priority=1,
            release_date=0,
        )
        order.line_id = "LINE1"
        scheduler2.add_order(order)

    env2.run(until=480)

    campaign_changeovers = scheduler2.changeover_count
    campaign_changeover_time = scheduler2.total_changeover_time

    logger.info(f"Changeovers: {campaign_changeovers}")
    logger.info(f"Total changeover time: {campaign_changeover_time:.1f} min")

    # Compare results
    logger.info("\n" + "-" * 40)
    logger.info("Campaign Optimization Impact:")
    logger.info("-" * 40)

    if mixed_changeovers > 0:
        changeover_reduction = (1 - campaign_changeovers / mixed_changeovers) * 100
        time_savings = mixed_changeover_time - campaign_changeover_time

        logger.info(f"Changeover reduction: {changeover_reduction:.1f}%")
        logger.info(f"Time saved: {time_savings:.1f} min")
        logger.info(f"Availability improvement: {time_savings / 480 * 100:.1f}%")


def main():
    """Run all changeover tests."""
    test_changeover_matrix()
    test_changeover_execution()
    test_smed_impact()
    test_campaign_optimization()

    logger.info("\n" + "=" * 60)
    logger.info("Changeover Modeling Tests Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
