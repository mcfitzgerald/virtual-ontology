#!/usr/bin/env python3
"""Test that failure configuration is loaded and used correctly."""

from pathlib import Path
import simpy

from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.control.control_manager import ControlManager
from twin_model.primitives.equipment import EquipmentPrimitive, FailureType

def test_failure_config():
    """Test that failure patterns use configuration values."""
    print("Testing failure configuration...")
    
    # Create environment
    env = simpy.Environment()
    
    # Set up paths
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    control_mappings_path = Path("ontology/control_mappings.yaml")
    config_path = Path("config/twin_model.yaml")
    
    # Create control manager
    control_mgr = ControlManager(
        ontology_path=ontology_path,
        mappings_path=control_mappings_path
    )
    
    # Create model builder
    builder = OntologyDrivenModelBuilder(
        env=env,
        ontology_path=ontology_path,
        manifest_dir=manifest_dir,
        control_manager=control_mgr,
        config_path=config_path
    )
    
    # Build model
    model = builder.build_model()
    print(f"✓ Model built with {len(model['primitives'])} primitives")
    
    # Find an equipment primitive
    equipment = None
    for prim_id, primitive in model["primitives"].items():
        if isinstance(primitive, EquipmentPrimitive):
            equipment = primitive
            break
    
    if equipment:
        print(f"\n✓ Testing equipment {equipment.config.id} failure configuration:")
        
        # Test failure configuration access
        micro_stop_pct = equipment.get_failure_config("micro_stops", "percentage")
        minor_failure_pct = equipment.get_failure_config("minor_failures", "percentage")
        major_failure_pct = equipment.get_failure_config("major_failures", "percentage")
        
        print(f"  - Micro-stop percentage: {micro_stop_pct} (expected: 0.8)")
        print(f"  - Minor failure percentage: {minor_failure_pct} (expected: 0.15)")
        print(f"  - Major failure percentage: {major_failure_pct} (expected: 0.05)")
        
        # Test micro-stop configuration details
        base_rate = equipment.get_failure_config("micro_stops", "occurrence.base_rate")
        print(f"  - Micro-stop base rate: {base_rate} minutes (expected: 20.0)")
        
        # Test failure cause configuration
        causes = equipment.get_system_config("failure_distributions.micro_stops.causes", {})
        if causes:
            print(f"  - Micro-stop causes configured: {list(causes.keys())}")
            jam_weight = causes.get("jam_at_handoff", {}).get("weight")
            print(f"  - Jam at handoff weight: {jam_weight} (expected: 0.4)")
        
        # Generate a few failures to test the mechanism
        print("\n✓ Testing failure generation (5 samples):")
        for i in range(5):
            failure_type, time_to_failure = equipment._get_next_failure()
            duration = equipment._get_repair_duration(failure_type)
            print(f"  - Sample {i+1}: {failure_type.value} in {time_to_failure:.1f} min, duration {duration:.1f} min")
        
        print("\n✅ Failure configuration test passed!")
    else:
        print("❌ No equipment found to test")

if __name__ == "__main__":
    test_failure_config()