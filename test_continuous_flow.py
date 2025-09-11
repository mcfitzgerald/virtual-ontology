#!/usr/bin/env python
"""Test continuous flow implementation."""

import simpy
from pathlib import Path
from twin_model.ontology_model_builder import OntologyModelBuilder

def test_continuous_flow():
    """Test that equipment processes continuously without batch constraints."""
    
    print("=" * 80)
    print("CONTINUOUS FLOW TEST")
    print("=" * 80)
    
    # Create environment
    env = simpy.Environment()
    
    # Build model
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=Path("ontology/filling_line_ontology.yaml"),
        manifest_path=Path("manifests/equipment_manifest.yaml"),
        config_path=Path("config/calibrated_parameters.yaml")
    )
    
    model = builder.build_model()
    primitives = model['primitives']
    
    print(f"\n✅ Model built with {len(primitives)} primitives")
    
    # Check generation rates
    print("\n" + "-" * 80)
    print("SOURCE GENERATION RATES:")
    print("-" * 80)
    for equip_id, equipment in primitives.items():
        if "SOURCE" in equip_id and hasattr(equipment, 'generation_rate'):
            print(f"  {equip_id}: {equipment.generation_rate} units/min")
    
    # Run for short time
    print("\n" + "-" * 80)
    print("RUNNING 60 MINUTE TEST")
    print("-" * 80)
    
    env.run(until=60)
    
    # Check production
    total_output = 0
    for equip_id in primitives.keys():
        if "SINK" in equip_id:
            sink = primitives[equip_id]
            if hasattr(sink, 'total_collected'):
                collected = sink.total_collected
            else:
                collected = 0
            total_output += collected
            print(f"  {equip_id}: {collected:,.0f} units collected")
    
    print(f"\n  Total Production: {total_output:,.0f} units")
    print(f"  Rate: {total_output/60:.1f} units/min")
    
    # Check if continuous flow is working
    expected_min = 60 * 50  # At least 50 units/min across all lines
    if total_output > expected_min:
        print(f"\n✅ CONTINUOUS FLOW WORKING! Production exceeds {expected_min} units")
    else:
        print(f"\n⚠️ LOW PRODUCTION: Only {total_output} units (expected > {expected_min})")
    
    return total_output

if __name__ == "__main__":
    try:
        total = test_continuous_flow()
        print("\n" + "=" * 80)
        if total > 3000:
            print("✅ Continuous flow implementation successful!")
        else:
            print("⚠️ Production still low - check implementation")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()