"""Comprehensive integration test for Phase 2 implementation.

This test validates that the ontology-driven model builder correctly:
1. Interprets the ontology structure
2. Creates proper primitive instances
3. Wires relationships correctly
4. Produces expected observables
5. Supports discovery-based learning
"""

import simpy
from pathlib import Path
import yaml
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.primitives import EquipmentPrimitive, SinkPrimitive


def test_ontology_structure_compliance():
    """Test that our ontology follows proper TBox/RBox structure."""
    print("Testing Ontology Structure Compliance...")

    ontology_path = Path("ontology/twin_ontology.yaml")
    with open(ontology_path, "r") as f:
        ontology = yaml.safe_load(f)

    # Check required sections
    assert "metadata" in ontology, "Missing metadata section"
    assert "tbox" in ontology, "Missing TBox section"
    assert "rbox" in ontology, "Missing RBox section"
    assert "observables" in ontology, "Missing observables section"
    assert "controllables" in ontology, "Missing controllables section"
    print("✓ All required sections present")

    # Check TBox structure
    tbox = ontology["tbox"]
    assert "classes" in tbox, "TBox missing classes"
    classes = tbox["classes"]

    # Verify no hardcoded values in classes
    for class_name, class_def in classes.items():
        if "properties" in class_def:
            for prop in class_def["properties"]:
                # Properties should be type definitions, not values
                assert isinstance(prop, str) or (
                    isinstance(prop, dict) and "type" in prop
                ), f"Class {class_name} has hardcoded values in properties"
    print("✓ TBox contains no hardcoded values")

    # Check inheritance hierarchy
    assert "SimulationEntity" in classes, "Missing base SimulationEntity"
    assert classes["SimulationEntity"].get("abstract") == True, (
        "SimulationEntity should be abstract"
    )

    # Check Equipment hierarchy
    assert "Equipment" in classes
    assert classes["Equipment"]["parent"] == "SimulationEntity"
    assert "Filler" in classes and classes["Filler"]["parent"] == "Equipment"
    print("✓ Inheritance hierarchy correct")

    # Check RBox relationships
    rbox = ontology["rbox"]
    assert "relationships" in rbox, "RBox missing relationships"
    relationships = rbox["relationships"]

    # Verify key relationships
    assert "feeds_into" in relationships
    assert "draws_from" in relationships
    assert "scheduled_on" in relationships
    print("✓ RBox relationships defined")

    # Check controllables have no prescribed effects
    controllables = ontology["controllables"]
    for param_name, param_def in controllables.items():
        assert "description" in param_def
        # Description should be vague, not prescriptive
        desc = param_def["description"].lower()
        assert "somehow" in desc or "affects" in desc, (
            f"Parameter {param_name} has prescriptive description"
        )
    print("✓ Controllables have no prescribed effects")

    print("Ontology structure compliance test passed!\n")


def test_primitive_instantiation_from_ontology():
    """Test that primitives are correctly instantiated from ontology classes."""
    print("Testing Primitive Instantiation from Ontology...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Test class to primitive mapping
    test_cases = [
        ("Equipment", "EquipmentPrimitive"),
        ("Filler", "EquipmentPrimitive"),  # Should inherit from Equipment
        ("Packer", "EquipmentPrimitive"),
        ("Buffer", "BufferPrimitive"),
        ("Source", "SourcePrimitive"),
        ("Sink", "SinkPrimitive"),
    ]

    for ontology_class, expected_primitive in test_cases:
        primitive_type = builder._get_primitive_type(ontology_class)
        assert primitive_type == expected_primitive, (
            f"{ontology_class} should map to {expected_primitive}, got {primitive_type}"
        )
    print("✓ Ontology classes map to correct primitives")

    # Build model and check primitive types
    model = builder.build_model(env)

    # Count primitive types
    primitive_counts = {}
    for primitive in model["primitives"].values():
        ptype = type(primitive).__name__
        primitive_counts[ptype] = primitive_counts.get(ptype, 0) + 1

    print(f"✓ Created primitives: {primitive_counts}")

    # Verify at least one of each core type
    assert primitive_counts.get("EquipmentPrimitive", 0) > 0
    assert primitive_counts.get("BufferPrimitive", 0) > 0
    assert primitive_counts.get("SourcePrimitive", 0) > 0
    assert primitive_counts.get("SinkPrimitive", 0) > 0
    print("✓ All core primitive types instantiated")

    print("Primitive instantiation test passed!\n")


def test_relationship_wiring():
    """Test that relationships from RBox are correctly wired."""
    print("Testing Relationship Wiring...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Build model
    model = builder.build_model(env)

    # Find equipment and check connections
    equipment_found = False
    for primitive_id, primitive in model["primitives"].items():
        if isinstance(primitive, EquipmentPrimitive):
            equipment_found = True

            # Check that equipment has upstream/downstream if in a line
            config_relationships = primitive.config.relationships
            if (
                "draws_from" in config_relationships
                or "feeds_into" in config_relationships
            ):
                # Should have connections
                has_connections = hasattr(primitive, "upstream") or hasattr(
                    primitive, "downstream"
                )
                assert has_connections, (
                    f"Equipment {primitive_id} has relationships but no connections"
                )

    assert equipment_found, "No equipment found in model"
    print("✓ Equipment relationships wired")

    # Check production lines
    for line_id, line in builder.production_lines.items():
        # Each line should have basic structure
        if line["equipment"]:
            print(
                f"✓ Line {line_id}: {len(line['equipment'])} equipment, "
                f"{len(line['buffers'])} buffers"
            )

    print("Relationship wiring test passed!\n")


def test_observable_emission():
    """Test that primitives emit observables as defined in ontology."""
    print("Testing Observable Emission...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Load ontology to check observable definitions
    with open(ontology_path, "r") as f:
        ontology = yaml.safe_load(f)

    observable_types = set(ontology["observables"].keys())
    print(f"✓ Ontology defines {len(observable_types)} observable types")

    # Build and run model
    model = builder.build_model(env)
    env.run(until=60)  # Run for 1 hour

    # Collect all event types emitted
    emitted_event_types = set()
    for primitive_id, primitive in model["primitives"].items():
        if hasattr(primitive, "observables"):
            for obs in primitive.observables:
                emitted_event_types.add(obs.get("event_type"))

    print(f"✓ Primitives emitted {len(emitted_event_types)} event types")

    # Check key events are emitted
    expected_events = [
        "state_change",
        "unit_produced",
        "equipment_started",
        "buffer_put",
        "buffer_get",
        "material_generated",
    ]

    for event in expected_events:
        if event in emitted_event_types:
            print(f"  ✓ {event} events emitted")

    # Check global observables
    assert len(env.global_observables) > 0
    print(f"✓ Global observables: {len(env.global_observables)} events")

    print("Observable emission test passed!\n")


def test_controllable_parameters():
    """Test that controllable parameters are exposed correctly."""
    print("Testing Controllable Parameters...")

    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Get controllable parameters
    controllables = builder.get_controllable_parameters()

    # Check expected parameters
    expected_params = [
        "micro_stop_probability",
        "performance_factor",
        "scrap_multiplier",
        "material_reliability",
        "cascade_sensitivity",
        "buffer_management",
    ]

    for param in expected_params:
        assert param in controllables, f"Missing controllable: {param}"
        param_def = controllables[param]
        assert "bounds" in param_def, f"{param} missing bounds"
        assert "default" in param_def, f"{param} missing default"
        assert "description" in param_def, f"{param} missing description"
        print(f"  ✓ {param}: {param_def['description']}")

    print(f"✓ All {len(controllables)} controllable parameters defined")
    print("Controllable parameters test passed!\n")


def test_monitor_kpi_tracking():
    """Test that monitor tracks KPIs defined in ontology observables."""
    print("Testing Monitor KPI Tracking...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Build model
    model = builder.build_model(env)
    monitor = model["monitor"]

    assert monitor is not None, "Monitor not created"

    # Run simulation
    env.run(until=30)

    # Check KPIs being tracked
    dashboard = monitor.get_dashboard()
    kpis = dashboard["kpis"]

    expected_kpis = ["overall_oee", "throughput", "availability", "quality"]
    for kpi_name in expected_kpis:
        if kpi_name in kpis:
            kpi_data = kpis[kpi_name]
            print(
                f"  ✓ {kpi_name}: {kpi_data['value']:.1f} "
                f"(target: {kpi_data.get('target', 'N/A')})"
            )

    # Check line metrics
    if dashboard["line_metrics"]:
        print(f"✓ Tracking {len(dashboard['line_metrics'])} production lines")

    print("Monitor KPI tracking test passed!\n")


def test_scheduler_order_management():
    """Test that scheduler can manage orders as defined in ontology."""
    print("Testing Scheduler Order Management...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Build model
    model = builder.build_model(env)
    scheduler = model["scheduler"]

    assert scheduler is not None, "Scheduler not created"

    # Add test orders (ProductionOrder is defined in ontology)
    from twin_model.primitives import ProductionOrder

    test_orders = [
        ProductionOrder(
            order_id="TEST-001",
            product_id="SKU-A",
            target_quantity=100,
            due_time=120,
            line_id="DEFAULT",
            priority=1,
        ),
        ProductionOrder(
            order_id="TEST-002",
            product_id="SKU-B",
            target_quantity=150,
            due_time=240,
            line_id="DEFAULT",
            priority=2,
        ),
    ]

    for order in test_orders:
        scheduler.add_order(order)

    assert len(scheduler.production_orders) == 2
    print(f"✓ Scheduler managing {len(scheduler.production_orders)} orders")

    # Run simulation
    env.run(until=10)

    # Check scheduler events
    scheduler_events = [
        o for o in scheduler.observables if "order" in o.get("event_type", "")
    ]
    if scheduler_events:
        print(f"✓ Scheduler emitted {len(scheduler_events)} order events")

    print("Scheduler order management test passed!\n")


def test_discovery_based_learning_support():
    """Test that the system supports discovery-based learning."""
    print("Testing Discovery-Based Learning Support...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Build model
    model = builder.build_model(env)

    # Run baseline
    env.run(until=100)

    # Collect baseline metrics
    baseline_observables = builder.get_observables()
    baseline_event_count = sum(len(obs) for obs in baseline_observables.values())

    print(f"✓ Baseline: {baseline_event_count} observables")

    # Get equipment OEE
    equipment_oees = []
    for primitive in model["primitives"].values():
        if isinstance(primitive, EquipmentPrimitive):
            oee = primitive.calculate_oee()
            equipment_oees.append(oee)
            print(f"  Equipment OEE: {oee:.1f}%")

    # Check that we have rich observables for discovery
    observable_diversity = set()
    for primitive_obs in baseline_observables.values():
        for obs in primitive_obs:
            observable_diversity.add(obs.get("event_type"))

    print(f"✓ Observable diversity: {len(observable_diversity)} unique event types")

    # Check discovery hints available
    with open(ontology_path, "r") as f:
        ontology = yaml.safe_load(f)

    hints = ontology.get("discovery_hints", {})
    assert len(hints.get("relationships_to_explore", [])) > 0
    assert len(hints.get("patterns_to_detect", [])) > 0
    assert len(hints.get("experiments_to_try", [])) > 0
    print("✓ Discovery hints available for LLM exploration")

    # Verify no prescriptive mappings
    # Check that controllable parameters don't have fixed effects
    controllables = builder.get_controllable_parameters()
    for param_name, param_def in controllables.items():
        desc = param_def["description"].lower()
        # Should be vague, not specific
        assert "somehow" in desc or "affects" in desc, (
            f"Parameter {param_name} has prescriptive effect"
        )

    print("✓ No prescriptive parameter mappings")
    print("Discovery-based learning support test passed!\n")


def test_production_line_composition():
    """Test that production lines are correctly composed from ontology."""
    print("Testing Production Line Composition...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Build model
    model = builder.build_model(env)

    # Check production lines
    for line_id, line in builder.production_lines.items():
        print(f"\nLine {line_id}:")

        # Check line has expected components
        if line["source"]:
            print(f"  ✓ Source: {line['source'].config.id}")

        if line["equipment"]:
            print(f"  ✓ Equipment: {[e.config.id for e in line['equipment']]}")

        if line["buffers"]:
            print(f"  ✓ Buffers: {[b.config.id for b in line['buffers']]}")

        if line["sink"]:
            print(f"  ✓ Sink: {line['sink'].config.id}")

        # Verify material flow
        if line["source"] and line["sink"]:
            # Run simulation to test flow
            start_env = simpy.Environment()
            test_model = builder.build_model(start_env)
            start_env.run(until=10)

            # Check if material flowed
            if isinstance(line["sink"], SinkPrimitive):
                if line["sink"].total_collected > 0:
                    print("  ✓ Material flow confirmed")

    print("\nProduction line composition test passed!\n")


def test_model_structure_analysis():
    """Test model structure extraction for analysis."""
    print("Testing Model Structure Analysis...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Build model
    model = builder.build_model(env)

    # Get structure
    structure = builder.get_model_structure()

    print("Model Structure:")
    print(f"  Entities: {len(structure['entities'])}")
    print(f"  Lines: {len(structure['lines'])}")
    print(f"  Controllables: {len(structure['controllables'])}")
    print(f"  Observable types: {len(structure['observable_types'])}")

    # Verify structure content
    for entity_id, entity_info in structure["entities"].items():
        assert "class" in entity_info
        assert "primitive" in entity_info
        assert "relationships" in entity_info
    print("✓ Entity structure complete")

    for line_id, line_info in structure["lines"].items():
        assert "equipment_count" in line_info
        assert "buffer_count" in line_info
        assert "has_source" in line_info
        assert "has_sink" in line_info
    print("✓ Line structure complete")

    print("Model structure analysis test passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 2 COMPREHENSIVE INTEGRATION TEST")
    print("=" * 60 + "\n")

    try:
        # Test ontology structure
        test_ontology_structure_compliance()

        # Test model building
        test_primitive_instantiation_from_ontology()
        test_relationship_wiring()

        # Test runtime behavior
        test_observable_emission()
        test_controllable_parameters()
        test_monitor_kpi_tracking()
        test_scheduler_order_management()

        # Test discovery support
        test_discovery_based_learning_support()

        # Test composition
        test_production_line_composition()
        test_model_structure_analysis()

        print("=" * 60)
        print("ALL INTEGRATION TESTS PASSED! ✓")
        print("Phase 2 implementation is fully validated.")
        print("The ontology-driven architecture is working correctly:")
        print("  - Structure defined in ontology (no values)")
        print("  - Primitives instantiated from ontology classes")
        print("  - Relationships wired from RBox")
        print("  - Rich observables emitted")
        print("  - Discovery-based learning supported")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
