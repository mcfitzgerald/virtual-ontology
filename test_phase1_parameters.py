#!/usr/bin/env python
"""Test Phase 1 parameter loading enhancements."""

import sys
import logging
from pathlib import Path
import simpy
from twin_model.ontology_model_builder import OntologyModelBuilder

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_parameter_loading():
    """Test the enhanced parameter loading with proper resolution."""
    
    # Create environment
    env = simpy.Environment()
    
    # Try to find valid config files
    ontology_path = Path("ontology/filling_line_ontology.yaml")
    manifest_path = Path("manifests/equipment_manifest.yaml")
    config_path = Path("config/tunable_parameters.yaml")
    
    # Check if files exist
    print("Checking for required files:")
    print(f"  Ontology: {ontology_path} - {'EXISTS' if ontology_path.exists() else 'MISSING'}")
    print(f"  Manifest: {manifest_path} - {'EXISTS' if manifest_path.exists() else 'MISSING'}")
    print(f"  Config: {config_path} - {'EXISTS' if config_path.exists() else 'MISSING'}")
    
    if not all([ontology_path.exists(), manifest_path.exists(), config_path.exists()]):
        print("\nMissing required files. Skipping test.")
        return
    
    print("\nBuilding model with enhanced parameter loading...")
    print("=" * 60)
    
    try:
        # Create builder
        builder = OntologyModelBuilder(
            env=env,
            ontology_path=ontology_path,
            manifest_path=manifest_path,
            config_path=config_path
        )
        
        # Build model - this will trigger our new parameter loading with logging
        model = builder.build_model()
        
        print("\n" + "=" * 60)
        print("Model built successfully!")
        print(f"Created {len(model['primitives'])} primitives")
        
        # Check some key equipment
        print("\nKey equipment created:")
        for equip_id in model['primitives'].keys():
            equip = model['primitives'][equip_id]
            equip_type = getattr(equip, 'equipment_type', 'Unknown')
            print(f"  - {equip_id}: {equip_type}")
            
            # Check specific rates for sources and sinks
            if hasattr(equip, 'generation_rate'):
                print(f"    Generation rate: {equip.generation_rate}")
            if hasattr(equip, 'collection_rate'):
                print(f"    Collection rate: {equip.collection_rate}")
            if hasattr(equip, 'processing_params'):
                print(f"    Nominal rate: {equip.processing_params.nominal_rate}")
                print(f"    Performance factor: {equip.processing_params.performance_factor}")
        
    except Exception as e:
        print(f"\nError during model building: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parameter_loading()