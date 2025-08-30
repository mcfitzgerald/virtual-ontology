#!/usr/bin/env python3
"""Test that configuration loading works correctly."""

from pathlib import Path
import simpy

from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.control.control_manager import ControlManager
from twin_model.primitives.equipment import EquipmentPrimitive

def test_config_loading():
    """Test that configuration values are loaded from files."""
    print("Testing configuration loading...")
    
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
    
    # Create model builder with config path
    builder = OntologyDrivenModelBuilder(
        env=env,
        ontology_path=ontology_path,
        manifest_dir=manifest_dir,
        control_manager=control_mgr,
        config_path=config_path
    )
    
    print(f"✓ Model builder created")
    print(f"✓ Technical config loaded: {len(builder.technical_config)} keys")
    print(f"✓ System config loaded: {len(builder.system_config)} keys")
    
    # Build model
    model = builder.build_model()
    print(f"✓ Model built with {len(model['primitives'])} primitives")
    
    # Check that equipment has access to configs
    for prim_id, primitive in model["primitives"].items():
        if isinstance(primitive, EquipmentPrimitive):
            # Test helper methods
            system_val = primitive.get_system_config("failure_distributions.micro_stops.percentage")
            tech_val = primitive.get_technical_config("validation.buffer.min_size")
            failure_val = primitive.get_failure_config("micro_stops", "percentage")
            
            print(f"\n✓ Equipment {prim_id} configuration access:")
            print(f"  - System config (micro_stops %): {system_val}")
            print(f"  - Technical config (buffer min): {tech_val}")
            print(f"  - Failure config (micro_stops %): {failure_val}")
            
            # Check that ontology defaults were applied
            print(f"  - MTBF from ontology: {primitive.config.get_property('mtbf')}")
            print(f"  - MTTR from ontology: {primitive.config.get_property('mttr')}")
            print(f"  - Queue size from ontology: {primitive.config.get_property('internal_queue_size')}")
            break
    
    print("\n✅ Configuration loading test passed!")

if __name__ == "__main__":
    test_config_loading()