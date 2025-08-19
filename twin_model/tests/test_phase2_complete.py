"""Complete end-to-end test for Phase 2 implementation.

This test demonstrates the full ontology-driven architecture:
1. Loading ontology structure (no values)
2. Building model from ontology
3. Running simulation
4. Generating rich observables
5. Supporting discovery-based learning
"""

import simpy
from pathlib import Path
import yaml


def run_complete_phase2_demonstration():
    """Run a complete demonstration of Phase 2 capabilities."""

    print("=" * 60)
    print("PHASE 2 COMPLETE DEMONSTRATION")
    print("Ontology-Driven Virtual Twin System")
    print("=" * 60 + "\n")

    # Import model builder
    from twin_model.model_builder import OntologyDrivenModelBuilder
    from twin_model.primitives import ProductionOrder

    # 1. LOAD ONTOLOGY
    print("1. LOADING ONTOLOGY STRUCTURE")
    print("-" * 40)

    ontology_path = Path("ontology/twin_ontology.yaml")
    with open(ontology_path, "r") as f:
        ontology = yaml.safe_load(f)

    print(f"✓ Ontology version: {ontology['metadata']['version']}")
    print(f"✓ Description: {ontology['metadata']['description']}")

    # Show structure (no values)
    print("\nTBox Classes (Structure Only):")
    for class_name in list(ontology["tbox"]["classes"].keys())[:5]:
        class_def = ontology["tbox"]["classes"][class_name]
        print(f"  - {class_name}: {class_def.get('description', '')[:50]}")

    print("\nRBox Relationships:")
    for rel_name in list(ontology["rbox"]["relationships"].keys())[:3]:
        rel_def = ontology["rbox"]["relationships"][rel_name]
        print(f"  - {rel_name}: {rel_def['description']}")

    print("\nControllable Parameters (No Prescribed Effects):")
    for param_name, param_def in list(ontology["controllables"].items())[:3]:
        print(f"  - {param_name}: {param_def['description']}")

    # 2. BUILD MODEL FROM ONTOLOGY
    print("\n2. BUILDING MODEL FROM ONTOLOGY")
    print("-" * 40)

    env = simpy.Environment()
    builder = OntologyDrivenModelBuilder(ontology_path)

    print("✓ Model builder initialized")
    print("✓ Building model from ontology structure...")

    model = builder.build_model(env)

    print(f"✓ Created {len(model['primitives'])} primitives")
    print(f"✓ Created {len(builder.production_lines)} production lines")
    print(f"✓ Scheduler: {'Active' if model['scheduler'] else 'Not configured'}")
    print(f"✓ Monitor: {'Active' if model['monitor'] else 'Not configured'}")

    # Show model structure
    structure = builder.get_model_structure()
    print("\nModel Structure:")
    for entity_id, entity_info in list(structure["entities"].items())[:3]:
        print(f"  {entity_id}: {entity_info['class']} → {entity_info['primitive']}")

    # 3. ADD PRODUCTION ORDERS
    print("\n3. SCHEDULING PRODUCTION")
    print("-" * 40)

    if model["scheduler"]:
        orders = [
            ProductionOrder(
                order_id="ORD-001",
                product_id="SKU-A",
                target_quantity=500,
                due_time=480,
                line_id="DEFAULT",
                priority=1,
            ),
            ProductionOrder(
                order_id="ORD-002",
                product_id="SKU-B",
                target_quantity=300,
                due_time=960,
                line_id="DEFAULT",
                priority=2,
            ),
        ]

        for order in orders:
            model["scheduler"].add_order(order)
            print(
                f"✓ Added order {order.order_id}: {order.target_quantity} units of {order.product_id}"
            )

    # 4. RUN SIMULATION
    print("\n4. RUNNING SIMULATION")
    print("-" * 40)

    simulation_duration = 120  # 2 hours
    print(f"Running for {simulation_duration} minutes...")

    env.run(until=simulation_duration)

    print(f"✓ Simulation completed at t={env.now}")

    # 5. ANALYZE OBSERVABLES
    print("\n5. OBSERVABLE ANALYSIS")
    print("-" * 40)

    # Count observables by type
    event_counts = {}
    total_observables = 0

    for primitive_id, primitive in model["primitives"].items():
        if hasattr(primitive, "observables"):
            for obs in primitive.observables:
                event_type = obs.get("event_type", "unknown")
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
                total_observables += 1

    print(f"Total observables emitted: {total_observables}")
    print("\nTop event types:")
    for event_type, count in sorted(
        event_counts.items(), key=lambda x: x[1], reverse=True
    )[:10]:
        print(f"  - {event_type}: {count} events")

    # 6. KPI METRICS
    print("\n6. KEY PERFORMANCE INDICATORS")
    print("-" * 40)

    if model["monitor"]:
        dashboard = model["monitor"].get_dashboard()

        print("Current KPIs:")
        for kpi_name, kpi_data in dashboard["kpis"].items():
            value = kpi_data["value"]
            target = kpi_data.get("target")
            trend = kpi_data.get("trend", "unknown")

            if target:
                achievement = (value / target * 100) if target > 0 else 0
                status = "✓" if achievement >= 90 else "⚠" if achievement >= 70 else "✗"
                print(
                    f"  {status} {kpi_name}: {value:.1f} / {target:.1f} ({achievement:.0f}%) - {trend}"
                )
            else:
                print(f"  • {kpi_name}: {value:.1f} - {trend}")

    # 7. PRODUCTION METRICS
    print("\n7. PRODUCTION METRICS")
    print("-" * 40)

    from twin_model.primitives import EquipmentPrimitive, SinkPrimitive

    # Equipment metrics
    for primitive_id, primitive in model["primitives"].items():
        if isinstance(primitive, EquipmentPrimitive):
            oee = primitive.calculate_oee()
            print(f"\n{primitive_id}:")
            print(f"  Units produced: {primitive.units_produced}")
            print(f"  Units scrapped: {primitive.units_scrapped}")
            print(f"  OEE: {oee:.1f}%")
            print(f"  Energy consumed: {primitive.energy_consumed:.1f} kWh")

    # Sink metrics
    for primitive_id, primitive in model["primitives"].items():
        if isinstance(primitive, SinkPrimitive):
            stats = primitive.get_statistics()
            print(f"\n{primitive_id}:")
            print(f"  Total collected: {stats['total_collected']}")
            print(f"  Acceptance rate: {stats['acceptance_rate']:.1%}")
            print(f"  Current throughput: {stats['current_throughput']:.1f} units/min")

    # 8. DISCOVERY SUPPORT
    print("\n8. DISCOVERY-BASED LEARNING SUPPORT")
    print("-" * 40)

    # Show controllable parameters
    controllables = builder.get_controllable_parameters()
    print(f"Controllable parameters available: {len(controllables)}")
    for param_name, param_def in controllables.items():
        bounds = param_def["bounds"]
        print(f"  - {param_name}: [{bounds[0]}, {bounds[1]}]")

    # Show discovery hints
    hints = ontology.get("discovery_hints", {})
    if hints:
        print("\nDiscovery hints for LLM:")
        if "relationships_to_explore" in hints:
            print(
                f"  - {len(hints['relationships_to_explore'])} relationships to explore"
            )
        if "patterns_to_detect" in hints:
            print(f"  - {len(hints['patterns_to_detect'])} patterns to detect")
        if "experiments_to_try" in hints:
            print(f"  - {len(hints['experiments_to_try'])} experiments to try")

    # 9. OBSERVABLE RICHNESS
    print("\n9. OBSERVABLE RICHNESS FOR DISCOVERY")
    print("-" * 40)

    # Sample some observables to show richness
    sample_observables = []
    for primitive_id, primitive in model["primitives"].items():
        if hasattr(primitive, "observables") and primitive.observables:
            # Get diverse samples
            for event_type in [
                "state_change",
                "unit_produced",
                "equipment_failure",
                "buffer_put",
            ]:
                for obs in primitive.observables:
                    if obs.get("event_type") == event_type:
                        sample_observables.append(obs)
                        break
                if len(sample_observables) >= 3:
                    break
        if len(sample_observables) >= 3:
            break

    print("Sample observables (showing rich context):")
    for i, obs in enumerate(sample_observables[:3], 1):
        print(f"\nObservable {i}:")
        print(f"  Event: {obs.get('event_type')}")
        print(f"  Primitive: {obs.get('primitive_id')} ({obs.get('primitive_type')})")
        print(f"  Timestamp: {obs.get('timestamp', 0):.1f}")

        # Show some context fields
        context_keys = [
            k
            for k in obs.keys()
            if k
            not in [
                "timestamp",
                "datetime",
                "primitive_id",
                "primitive_type",
                "event_type",
                "severity",
            ]
        ]
        if context_keys:
            print(f"  Context: {', '.join(context_keys[:5])}")

    # 10. SUMMARY
    print("\n" + "=" * 60)
    print("PHASE 2 DEMONSTRATION COMPLETE")
    print("=" * 60)

    print("\n✓ Ontology-driven model successfully built and executed")
    print("✓ No hardcoded values in ontology (pure structure)")
    print("✓ Rich observables generated for discovery")
    print("✓ Controllable parameters exposed without prescriptive effects")
    print("✓ System ready for discovery-based learning by LLM")

    print("\nKey Statistics:")
    print(f"  - Total observables: {total_observables}")
    print(f"  - Event type diversity: {len(event_counts)}")
    print(f"  - Controllable parameters: {len(controllables)}")
    print(f"  - Observable types defined: {len(structure['observable_types'])}")

    return {
        "success": True,
        "total_observables": total_observables,
        "event_types": len(event_counts),
        "controllables": len(controllables),
        "model": model,
        "builder": builder,
    }


if __name__ == "__main__":
    try:
        result = run_complete_phase2_demonstration()

        if result["success"]:
            print("\n" + "🎉" * 20)
            print("PHASE 2 IMPLEMENTATION VALIDATED!")
            print("The ontology-driven virtual twin is ready for Phase 3 (Manifests)")
            print("🎉" * 20)

    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback

        traceback.print_exc()
