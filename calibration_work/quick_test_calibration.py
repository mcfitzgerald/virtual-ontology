"""Quick test to see impact of calibration parameters."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import yaml
import numpy as np
import pandas as pd
import simpy
import random
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction import MESTransducer


def test_baseline():
    """Test baseline performance with current parameters."""
    print("\n=== BASELINE TEST ===")
    
    # Set seed
    random.seed(42)
    np.random.seed(42)
    
    # Build model
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    builder = OntologyDrivenModelBuilder(
        ontology_path=ontology_path,
        manifest_dir=manifest_dir
    )
    
    env = simpy.Environment()
    model = builder.build_model(env)
    
    # Run for just 1 hour to be quick
    env.run(until=60)
    
    # Check a filler's production
    for prim_id, primitive in builder.primitives.items():
        if 'LINE1-FIL' in prim_id:
            total = primitive.units_produced + primitive.units_scrapped
            rate = total / 60  # units per minute
            efficiency = (rate / primitive.base_rate) * 100
            
            print(f"{prim_id}:")
            print(f"  Base rate: {primitive.base_rate} units/min")
            print(f"  Actual rate: {rate:.1f} units/min")
            print(f"  Efficiency: {efficiency:.1f}%")
            print(f"  Units produced: {primitive.units_produced}")
            print(f"  Units scrapped: {primitive.units_scrapped}")
            break


def test_improved():
    """Test with improved parameters."""
    print("\n=== IMPROVED PARAMETERS TEST ===")
    
    # Restore and modify manifest
    import shutil
    manifest_path = Path("manifests/equipment_manifest.yaml")
    backup_path = Path("manifests/equipment_manifest.yaml.pre_calibration")
    
    # Restore from backup
    shutil.copy(backup_path, manifest_path)
    
    # Load and modify
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)
    
    # Apply improvements
    improvements = {
        'arrival_rate': 150,  # Increase material supply
        'base_rate': 100,     # Increase equipment speed
        'buffer_multiplier': 2.0,  # Larger buffers
        'mtbf_multiplier': 3.0,    # Less failures
        'mttr_multiplier': 0.5,    # Faster repairs
    }
    
    # Apply to manifest
    for eq_id, eq_data in manifest['equipment'].items():
        if 'SRC' in eq_id:
            eq_data['arrival_rate'] = improvements['arrival_rate']
        
        if any(x in eq_id for x in ['FIL', 'PCK', 'PAL']):
            eq_data['base_rate'] = improvements['base_rate']
        
        if 'BUF' in eq_id and 'capacity' in eq_data:
            eq_data['capacity'] = int(eq_data['capacity'] * improvements['buffer_multiplier'])
    
    # Improve failure patterns
    for pattern in manifest.get('failure_patterns', {}).values():
        for failure in pattern.values():
            if 'mtbf' in failure:
                failure['mtbf'] = failure['mtbf'] * improvements['mtbf_multiplier']
            if 'mttr' in failure:
                failure['mttr'] = failure['mttr'] * improvements['mttr_multiplier']
            if 'probability_per_5min' in failure:
                failure['probability_per_5min'] = failure['probability_per_5min'] * 0.5
    
    # Save modified manifest
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f)
    
    print("Applied improvements:")
    for key, value in improvements.items():
        print(f"  {key}: {value}")
    
    # Test with improved parameters
    random.seed(42)
    np.random.seed(42)
    
    builder = OntologyDrivenModelBuilder(
        ontology_path=Path("ontology/twin_ontology.yaml"),
        manifest_dir=Path("manifests")
    )
    
    env = simpy.Environment()
    model = builder.build_model(env)
    
    # Run for 1 hour
    env.run(until=60)
    
    # Check results
    for prim_id, primitive in builder.primitives.items():
        if 'LINE1-FIL' in prim_id:
            total = primitive.units_produced + primitive.units_scrapped
            rate = total / 60
            efficiency = (rate / primitive.base_rate) * 100
            
            print(f"\n{prim_id} after improvements:")
            print(f"  Base rate: {primitive.base_rate} units/min")
            print(f"  Actual rate: {rate:.1f} units/min")
            print(f"  Efficiency: {efficiency:.1f}%")
            print(f"  Units produced: {primitive.units_produced}")
            print(f"  Units scrapped: {primitive.units_scrapped}")
            break
    
    # Restore original manifest
    shutil.copy(backup_path, manifest_path)
    print("\n✓ Original manifest restored")


def main():
    """Run quick calibration tests."""
    print("="*60)
    print("QUICK CALIBRATION TEST")
    print("="*60)
    
    # Test baseline
    test_baseline()
    
    # Test with improvements
    test_improved()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()