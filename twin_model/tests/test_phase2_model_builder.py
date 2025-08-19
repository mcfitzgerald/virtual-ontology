"""Test Phase 2: Validate ontology-driven model builder.

This test validates that the model builder correctly interprets
the ontology to instantiate and wire primitives.
"""

import simpy
from pathlib import Path
from twin_model.model_builder import OntologyDrivenModelBuilder, ModelEntity
from twin_model.primitives import (
    EquipmentPrimitive,
    BufferPrimitive,
    SourcePrimitive,
    SinkPrimitive,
    SchedulerPrimitive,
    MonitorPrimitive,
)


def test_ontology_loading():
    """Test that ontology loads correctly."""
    print("Testing Ontology Loading...")

    ontology_path = Path("ontology/twin_ontology.yaml")

    # Create builder
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Check ontology loaded
    assert builder.ontology is not None
    assert "tbox" in builder.ontology
    assert "rbox" in builder.ontology
    print("✓ Ontology loaded successfully")

    # Check TBox classes
    tbox = builder.ontology["tbox"]
    assert "classes" in tbox
    assert "Equipment" in tbox["classes"]
    assert "Buffer" in tbox["classes"]
    print("✓ TBox classes found")

    # Check RBox relationships
    rbox = builder.ontology["rbox"]
    assert "relationships" in rbox
    assert "feeds_into" in rbox["relationships"]
    print("✓ RBox relationships found")

    # Check controllables
    assert "controllables" in builder.ontology
    assert "micro_stop_probability" in builder.ontology["controllables"]
    print("✓ Controllable parameters defined")

    print("Ontology loading tests passed!\n")


def test_primitive_type_mapping():
    """Test primitive type resolution from ontology classes."""
    print("Testing Primitive Type Mapping...")

    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Test equipment types
    assert builder._get_primitive_type("Equipment") == "EquipmentPrimitive"
    assert builder._get_primitive_type("Filler") == "EquipmentPrimitive"
    assert builder._get_primitive_type("Packer") == "EquipmentPrimitive"
    print("✓ Equipment types map to EquipmentPrimitive")

    # Test other types
    assert builder._get_primitive_type("Buffer") == "BufferPrimitive"
    assert builder._get_primitive_type("Source") == "SourcePrimitive"
    assert builder._get_primitive_type("Sink") == "SinkPrimitive"
    print("✓ Other types map correctly")

    print("Primitive type mapping tests passed!\n")


def test_default_model_building():
    """Test building a model without manifests."""
    print("Testing Default Model Building...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")

    # Build model without manifests
    builder = OntologyDrivenModelBuilder(ontology_path)
    model = builder.build_model(env)

    # Check model components
    assert "primitives" in model
    assert "lines" in model
    assert "scheduler" in model
    assert "monitor" in model
    print("✓ Model structure created")

    # Check primitives were created
    assert len(model["primitives"]) > 0
    print(f"✓ Created {len(model['primitives'])} primitives")

    # Check primitive types
    has_source = any(
        isinstance(p, SourcePrimitive) for p in model["primitives"].values()
    )
    has_equipment = any(
        isinstance(p, EquipmentPrimitive) for p in model["primitives"].values()
    )
    has_buffer = any(
        isinstance(p, BufferPrimitive) for p in model["primitives"].values()
    )
    has_sink = any(isinstance(p, SinkPrimitive) for p in model["primitives"].values())

    assert has_source, "Should have at least one source"
    assert has_equipment, "Should have at least one equipment"
    assert has_buffer, "Should have at least one buffer"
    assert has_sink, "Should have at least one sink"
    print("✓ All primitive types present")

    # Check scheduler and monitor
    assert model["scheduler"] is not None
    assert isinstance(model["scheduler"], SchedulerPrimitive)
    print("✓ Scheduler created")

    assert model["monitor"] is not None
    assert isinstance(model["monitor"], MonitorPrimitive)
    print("✓ Monitor created")

    # Check that primitives are started
    for primitive in model["primitives"].values():
        assert primitive.is_running
    print("✓ All primitives started")

    print("Default model building tests passed!\n")


def test_model_with_custom_entities():
    """Test building a model with custom entities."""
    print("Testing Model with Custom Entities...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")

    # Create builder
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Add custom entities
    custom_entities = [
        ModelEntity(
            id="CUSTOM-SRC",
            ontology_class="Source",
            primitive_type="SourcePrimitive",
            properties={"arrival_rate": 100.0},
            relationships={"feeds_into": ["CUSTOM-BUF1"]},
        ),
        ModelEntity(
            id="CUSTOM-BUF1",
            ontology_class="Buffer",
            primitive_type="BufferPrimitive",
            properties={"capacity": 200},
            relationships={"feeds_into": ["CUSTOM-EQ1"]},
        ),
        ModelEntity(
            id="CUSTOM-EQ1",
            ontology_class="Filler",
            primitive_type="EquipmentPrimitive",
            properties={"base_rate": 90.0, "line_id": "CUSTOM_LINE"},
            relationships={
                "draws_from": ["CUSTOM-BUF1"],
                "feeds_into": ["CUSTOM-SINK"],
            },
        ),
        ModelEntity(
            id="CUSTOM-SINK",
            ontology_class="Sink",
            primitive_type="SinkPrimitive",
            properties={"target_throughput": 85.0},
            relationships={"draws_from": ["CUSTOM-EQ1"]},
        ),
    ]

    # Override entities
    builder.entities = {e.id: e for e in custom_entities}

    # Build model
    builder._instantiate_primitives(env)
    builder._wire_relationships()
    builder._create_production_lines()

    # Check primitives created
    assert len(builder.primitives) == 4
    assert "CUSTOM-SRC" in builder.primitives
    assert "CUSTOM-EQ1" in builder.primitives
    print("✓ Custom entities instantiated")

    # Check relationships wired
    eq = builder.primitives["CUSTOM-EQ1"]
    assert eq.upstream == builder.primitives["CUSTOM-BUF1"]
    print("✓ Relationships wired correctly")

    # Check production line created
    assert "CUSTOM_LINE" in builder.production_lines
    line = builder.production_lines["CUSTOM_LINE"]
    assert len(line["equipment"]) == 1
    print("✓ Production line created")

    print("Custom entities test passed!\n")


def test_model_structure_extraction():
    """Test extracting model structure for analysis."""
    print("Testing Model Structure Extraction...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")

    builder = OntologyDrivenModelBuilder(ontology_path)
    model = builder.build_model(env)

    # Get model structure
    structure = builder.get_model_structure()

    assert "entities" in structure
    assert "lines" in structure
    assert "controllables" in structure
    assert "observable_types" in structure
    print("✓ Structure extracted")

    # Check controllables
    controllables = structure["controllables"]
    assert "micro_stop_probability" in controllables
    assert "performance_factor" in controllables
    print(f"✓ Found {len(controllables)} controllable parameters")

    # Check observable types
    observables = structure["observable_types"]
    assert "equipment_state" in observables
    assert "oee_score" in observables
    print(f"✓ Found {len(observables)} observable types")

    print("Model structure extraction test passed!\n")


def test_simulation_execution():
    """Test that the built model can run a simulation."""
    print("Testing Simulation Execution...")

    env = simpy.Environment()
    ontology_path = Path("ontology/twin_ontology.yaml")

    # Build and run model
    builder = OntologyDrivenModelBuilder(ontology_path)
    model = builder.build_model(env)

    # Run simulation
    env.run(until=30)

    print(f"✓ Simulation ran for {env.now} minutes")

    # Check that observables were generated
    all_observables = builder.get_observables()
    total_events = sum(len(obs) for obs in all_observables.values())
    assert total_events > 0
    print(f"✓ Generated {total_events} observable events")

    # Check global observables
    assert hasattr(env, "global_observables")
    assert len(env.global_observables) > 0
    print(f"✓ Global observables: {len(env.global_observables)} events")

    # Check production occurred
    equipment_primitives = [
        p for p in model["primitives"].values() if isinstance(p, EquipmentPrimitive)
    ]

    if equipment_primitives:
        total_production = sum(eq.units_produced for eq in equipment_primitives)
        print(f"✓ Total production: {total_production} units")

    # Check monitor captured KPIs
    if model["monitor"]:
        dashboard = model["monitor"].get_dashboard()
        assert "kpis" in dashboard
        print(f"✓ Monitor tracking {len(dashboard['kpis'])} KPIs")

    print("Simulation execution test passed!\n")


def test_discovery_hints():
    """Test that discovery hints are available."""
    print("Testing Discovery Hints...")

    ontology_path = Path("ontology/twin_ontology.yaml")
    builder = OntologyDrivenModelBuilder(ontology_path)

    # Check discovery hints in ontology
    hints = builder.ontology.get("discovery_hints", {})

    assert "relationships_to_explore" in hints
    assert "patterns_to_detect" in hints
    assert "experiments_to_try" in hints
    print("✓ Discovery hints available")

    # Check hint content
    relationships = hints["relationships_to_explore"]
    assert len(relationships) > 0
    print(f"✓ {len(relationships)} relationships to explore")

    patterns = hints["patterns_to_detect"]
    assert len(patterns) > 0
    print(f"✓ {len(patterns)} patterns to detect")

    experiments = hints["experiments_to_try"]
    assert len(experiments) > 0
    print(f"✓ {len(experiments)} experiments suggested")

    print("Discovery hints test passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 2 ONTOLOGY-DRIVEN MODEL BUILDER TEST")
    print("=" * 60 + "\n")

    try:
        test_ontology_loading()
        test_primitive_type_mapping()
        test_default_model_building()
        test_model_with_custom_entities()
        test_model_structure_extraction()
        test_simulation_execution()
        test_discovery_hints()

        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("Phase 2 Ontology-Driven Model Builder is working correctly.")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
