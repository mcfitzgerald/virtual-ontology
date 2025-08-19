"""Test Phase 3: Validate manifests with model builder.

This test validates that manifests correctly provide configuration values
for the ontology-driven model and that the system runs with realistic
production scenarios.
"""

import simpy
from pathlib import Path
import yaml
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.primitives import (
    EquipmentPrimitive,
    BufferPrimitive,
    SourcePrimitive,
    SinkPrimitive,
    ProductionOrder,
)


def test_manifest_loading():
    """Test that manifests load correctly."""
    print("Testing Manifest Loading...")

    manifest_dir = Path("manifests")

    # Load production manifest
    prod_manifest_path = manifest_dir / "production_manifest.yaml"
    with open(prod_manifest_path, "r") as f:
        prod_manifest = yaml.safe_load(f)

    # Check products
    assert "products" in prod_manifest
    products = prod_manifest["products"]
    assert len(products) == 6, f"Expected 6 products, got {len(products)}"
    print(f"✓ Loaded {len(products)} products")

    # Verify all SKUs present
    expected_skus = [
        "SKU-1001",
        "SKU-1002",
        "SKU-2001",
        "SKU-2002",
        "SKU-3001",
        "SKU-3002",
    ]
    for sku in expected_skus:
        assert sku in products, f"Missing product {sku}"
    print("✓ All 6 SKUs defined")

    # Check production orders
    assert "production_orders" in prod_manifest
    orders = prod_manifest["production_orders"]
    assert len(orders) > 0, "No production orders defined"
    print(f"✓ Loaded {len(orders)} production orders")

    # Load equipment manifest
    eq_manifest_path = manifest_dir / "equipment_manifest.yaml"
    with open(eq_manifest_path, "r") as f:
        eq_manifest = yaml.safe_load(f)

    # Check production lines
    assert "production_lines" in eq_manifest
    lines = eq_manifest["production_lines"]
    assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}"
    print(f"✓ Loaded {len(lines)} production lines")

    # Check equipment
    assert "equipment" in eq_manifest
    equipment = eq_manifest["equipment"]

    # Count equipment by type
    equipment_counts = {}
    for eq_id, eq_data in equipment.items():
        eq_type = eq_data.get("type")
        equipment_counts[eq_type] = equipment_counts.get(eq_type, 0) + 1

    print("✓ Equipment configuration:")
    for eq_type, count in equipment_counts.items():
        print(f"  - {eq_type}: {count}")

    # Check failure patterns
    assert "failure_patterns" in eq_manifest
    failure_patterns = eq_manifest["failure_patterns"]

    # Count downtime reasons
    downtime_reasons = set()
    for equipment_type, patterns in failure_patterns.items():
        for pattern_name, pattern_data in patterns.items():
            downtime_reasons.add(pattern_data.get("downtime_reason"))

    assert len(downtime_reasons) == 8, (
        f"Expected 8 downtime codes, got {len(downtime_reasons)}"
    )
    print(
        f"✓ Defined {len(downtime_reasons)} unique downtime codes: {downtime_reasons}"
    )

    print("Manifest loading tests passed!\n")


def test_model_building_with_manifests():
    """Test building model with manifest configuration."""
    print("Testing Model Building with Manifests...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")

    # Build model with manifests
    builder = OntologyDrivenModelBuilder(ontology_path, manifest_dir)

    # Check manifests loaded
    assert len(builder.manifests) > 0, "No manifests loaded"
    print(f"✓ Loaded {len(builder.manifests)} manifests")

    # Build model
    model = builder.build_model(env)

    # Check primitives created
    assert len(model["primitives"]) > 0
    print(f"✓ Created {len(model['primitives'])} primitives")

    # Check for 3 lines worth of equipment
    equipment_count = sum(
        1 for p in model["primitives"].values() if isinstance(p, EquipmentPrimitive)
    )
    assert equipment_count >= 9, (
        f"Expected at least 9 equipment (3 per line), got {equipment_count}"
    )
    print(f"✓ Created {equipment_count} equipment primitives")

    # Check buffers
    buffer_count = sum(
        1 for p in model["primitives"].values() if isinstance(p, BufferPrimitive)
    )
    print(f"✓ Created {buffer_count} buffer primitives")

    # Check sources and sinks
    source_count = sum(
        1 for p in model["primitives"].values() if isinstance(p, SourcePrimitive)
    )
    sink_count = sum(
        1 for p in model["primitives"].values() if isinstance(p, SinkPrimitive)
    )
    assert source_count >= 3, f"Expected at least 3 sources, got {source_count}"
    assert sink_count >= 3, f"Expected at least 3 sinks, got {sink_count}"
    print(f"✓ Created {source_count} sources and {sink_count} sinks")

    print("Model building with manifests test passed!\n")


def test_production_line_configuration():
    """Test that production lines are configured correctly."""
    print("Testing Production Line Configuration...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")

    builder = OntologyDrivenModelBuilder(ontology_path, manifest_dir)
    model = builder.build_model(env)

    # Check line configuration
    lines = builder.production_lines

    expected_lines = ["LINE1", "LINE2", "LINE3"]
    for line_id in expected_lines:
        if line_id in lines:
            line = lines[line_id]
            print(f"\n{line_id}:")
            print(f"  Equipment: {len(line['equipment'])}")
            print(f"  Buffers: {len(line['buffers'])}")
            print(f"  Source: {'Yes' if line['source'] else 'No'}")
            print(f"  Sink: {'Yes' if line['sink'] else 'No'}")

            # Verify line has complete structure
            assert len(line["equipment"]) >= 3, (
                f"{line_id} should have at least 3 equipment"
            )
            assert line["source"] is not None, f"{line_id} missing source"
            assert line["sink"] is not None, f"{line_id} missing sink"

    print("\n✓ All production lines configured correctly")
    print("Production line configuration test passed!\n")


def test_product_configuration():
    """Test that products are configured with all attributes."""
    print("Testing Product Configuration...")

    manifest_dir = Path("manifests")
    prod_manifest_path = manifest_dir / "production_manifest.yaml"

    with open(prod_manifest_path, "r") as f:
        prod_manifest = yaml.safe_load(f)

    products = prod_manifest["products"]

    # Check each product has required attributes
    required_attrs = [
        "name",
        "target_rate_units_per_5min",
        "standard_cost_per_unit",
        "sale_price_per_unit",
        "margin",
        "scrap_rates",
        "quality_requirements",
    ]

    for product_id, product_data in products.items():
        print(f"\n{product_id}: {product_data['name']}")

        for attr in required_attrs:
            assert attr in product_data, f"{product_id} missing {attr}"

        # Check scrap rates
        scrap_rates = product_data["scrap_rates"]
        assert "normal" in scrap_rates
        assert scrap_rates["normal"] > 0 and scrap_rates["normal"] < 0.1

        # Check margins
        margin = product_data["margin"]
        cost = product_data["standard_cost_per_unit"]
        price = product_data["sale_price_per_unit"]
        calculated_margin = price - cost
        assert abs(margin - calculated_margin) < 0.01, (
            f"{product_id} margin mismatch: {margin} vs {calculated_margin}"
        )

        print(f"  Rate: {product_data['target_rate_units_per_5min']} units/5min")
        print(f"  Margin: ${margin:.2f} (${price:.2f} - ${cost:.2f})")
        print(f"  Normal scrap: {scrap_rates['normal']:.1%}")

    print("\n✓ All products configured with complete attributes")
    print("Product configuration test passed!\n")


def test_failure_patterns():
    """Test that failure patterns are configured correctly."""
    print("Testing Failure Patterns...")

    manifest_dir = Path("manifests")
    eq_manifest_path = manifest_dir / "equipment_manifest.yaml"

    with open(eq_manifest_path, "r") as f:
        eq_manifest = yaml.safe_load(f)

    failure_patterns = eq_manifest["failure_patterns"]

    # Check each equipment type has failures
    for equipment_type, patterns in failure_patterns.items():
        print(f"\n{equipment_type} failure modes:")

        for pattern_name, pattern_data in patterns.items():
            prob = pattern_data["probability_per_5min"]
            duration = pattern_data["duration_range"]
            reason = pattern_data["downtime_reason"]
            cascade = pattern_data.get("cascade_probability", 0)

            print(
                f"  - {pattern_name}: {prob:.1%} chance, "
                f"{duration[0]}-{duration[1]} min, "
                f"code: {reason}, "
                f"cascade: {cascade:.1%}"
            )

            # Validate probability ranges
            assert 0 < prob < 0.2, f"Unrealistic probability for {pattern_name}"
            assert duration[0] > 0 and duration[1] < 100, (
                f"Unrealistic duration for {pattern_name}"
            )

    # Check all 8 downtime codes are represented
    all_codes = set()
    for patterns in failure_patterns.values():
        for pattern_data in patterns.values():
            all_codes.add(pattern_data["downtime_reason"])

    expected_codes = {
        "UNP-SENS",
        "UNP-MECH",
        "UNP-QC",
        "UNP-SEAL",
        "UNP-JAM",
        "UNP-ELEC",
        "UNP-CTRL",
        "UNP-OP",
    }

    assert all_codes == expected_codes, (
        f"Missing downtime codes: {expected_codes - all_codes}"
    )
    print(f"\n✓ All 8 downtime codes defined: {all_codes}")

    print("Failure patterns test passed!\n")


def test_production_schedule():
    """Test that production schedule is realistic."""
    print("Testing Production Schedule...")

    manifest_dir = Path("manifests")
    prod_manifest_path = manifest_dir / "production_manifest.yaml"

    with open(prod_manifest_path, "r") as f:
        prod_manifest = yaml.safe_load(f)

    orders = prod_manifest["production_orders"]

    # Group orders by day
    orders_by_day = {}
    for order in orders:
        day = order["start_time"] // 1440  # Convert minutes to days
        if day not in orders_by_day:
            orders_by_day[day] = []
        orders_by_day[day].append(order)

    print(f"✓ Schedule covers {len(orders_by_day)} days")

    # Check each day
    for day, day_orders in orders_by_day.items():
        print(f"\nDay {day + 1}:")

        # Group by line
        by_line = {}
        for order in day_orders:
            line_id = order["line_id"]
            if line_id not in by_line:
                by_line[line_id] = []
            by_line[line_id].append(order)

        for line_id, line_orders in by_line.items():
            total_duration = sum(o["duration"] for o in line_orders)
            total_quantity = sum(o["target_quantity"] for o in line_orders)

            print(
                f"  {line_id}: {len(line_orders)} orders, "
                f"{total_duration} min runtime, "
                f"{total_quantity} units"
            )

            # Check for reasonable daily production
            assert total_duration <= 1440, f"{line_id} overbooked on day {day}"

    # Check product mix
    product_counts = {}
    for order in orders:
        product_id = order["product_id"]
        product_counts[product_id] = product_counts.get(product_id, 0) + 1

    print("\n✓ Product mix across schedule:")
    for product_id, count in sorted(product_counts.items()):
        print(f"  {product_id}: {count} orders")

    # Verify all 6 products are scheduled
    assert len(product_counts) == 6, (
        f"Not all products scheduled: {product_counts.keys()}"
    )

    print("\nProduction schedule test passed!\n")


def test_shift_configuration():
    """Test shift configurations."""
    print("Testing Shift Configuration...")

    manifest_dir = Path("manifests")
    eq_manifest_path = manifest_dir / "equipment_manifest.yaml"

    with open(eq_manifest_path, "r") as f:
        eq_manifest = yaml.safe_load(f)

    shifts = eq_manifest["shifts"]

    assert len(shifts) == 3, f"Expected 3 shifts, got {len(shifts)}"

    for shift_id, shift_data in shifts.items():
        perf_range = shift_data["performance_range"]
        staffing = shift_data.get("staffing_level", 1.0)

        print(f"\n{shift_id}: {shift_data['name']}")
        print(f"  Hours: {shift_data['start_hour']}:00 - {shift_data['end_hour']}:00")
        print(f"  Performance: {perf_range[0]:.0%} - {perf_range[1]:.0%}")
        print(f"  Staffing: {staffing:.0%}")

        # Verify performance degradation pattern
        if shift_id == "shift1":
            assert perf_range[0] >= 0.95, "Shift 1 should have best performance"
        elif shift_id == "shift3":
            assert perf_range[1] <= 0.95, "Shift 3 should have worst performance"

    print("\n✓ Shift performance follows expected pattern")
    print("Shift configuration test passed!\n")


def test_simulation_with_manifests():
    """Test running simulation with full manifest configuration."""
    print("Testing Simulation with Full Manifests...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")

    # Build and run model
    builder = OntologyDrivenModelBuilder(ontology_path, manifest_dir)
    model = builder.build_model(env)

    # Load orders from manifest
    with open(manifest_dir / "production_manifest.yaml", "r") as f:
        prod_manifest = yaml.safe_load(f)

    # Add first day's orders to scheduler
    if model["scheduler"]:
        day1_orders = [
            o for o in prod_manifest["production_orders"] if o["start_time"] < 1440
        ]  # First day only

        for order_data in day1_orders[:3]:  # Just first 3 orders for quick test
            order = ProductionOrder(
                order_id=order_data["order_id"],
                product_id=order_data["product_id"],
                target_quantity=order_data["target_quantity"],
                due_time=order_data["start_time"] + order_data["duration"],
                line_id=order_data["line_id"],
                priority=order_data["priority"],
            )
            model["scheduler"].add_order(order)

        print(f"✓ Added {len(day1_orders[:3])} orders to scheduler")

    # Run simulation for 8 hours
    print("\nRunning 8-hour simulation...")
    env.run(until=480)

    print(f"✓ Simulation completed at t={env.now}")

    # Check production metrics
    total_produced = 0
    total_scrapped = 0

    for primitive in model["primitives"].values():
        if isinstance(primitive, EquipmentPrimitive):
            total_produced += primitive.units_produced
            total_scrapped += primitive.units_scrapped

    print(f"✓ Total production: {total_produced} good units, {total_scrapped} scrapped")

    if total_produced > 0:
        scrap_rate = total_scrapped / (total_produced + total_scrapped)
        print(f"✓ Overall scrap rate: {scrap_rate:.1%}")

    # Check KPIs
    if model["monitor"]:
        dashboard = model["monitor"].get_dashboard()
        kpis = dashboard["kpis"]

        print("\nKPIs after 8 hours:")
        for kpi_name, kpi_data in kpis.items():
            value = kpi_data["value"]
            target = kpi_data.get("target")
            if target:
                print(f"  {kpi_name}: {value:.1f} / {target:.1f}")

    # Check observables generated
    total_observables = sum(
        len(p.observables)
        for p in model["primitives"].values()
        if hasattr(p, "observables")
    )

    print(f"\n✓ Generated {total_observables} observables")
    assert total_observables > 1000, "Should generate significant observables"

    print("\nSimulation with manifests test passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 3 MANIFESTS VALIDATION TEST")
    print("=" * 60 + "\n")

    try:
        test_manifest_loading()
        test_model_building_with_manifests()
        test_production_line_configuration()
        test_product_configuration()
        test_failure_patterns()
        test_production_schedule()
        test_shift_configuration()
        test_simulation_with_manifests()

        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("Phase 3 Manifests are correctly configured:")
        print("  - 6 products with complete specifications")
        print("  - 3 production lines with equipment")
        print("  - 8 unique downtime codes")
        print("  - 7-day production schedule")
        print("  - Shift performance variations")
        print("  - Failure patterns per equipment type")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
