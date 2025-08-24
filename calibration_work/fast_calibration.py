"""Fast calibration to find optimal parameters."""

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


def run_single_test(params: dict, sim_minutes: int = 60) -> dict:
    """Run a single parameter test."""
    # Set seed
    random.seed(42)
    np.random.seed(42)
    
    # Apply parameters to manifest
    manifest_path = Path("manifests/equipment_manifest.yaml")
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)
    
    # Apply parameters
    for src_id in ['LINE1-SRC', 'LINE2-SRC', 'LINE3-SRC']:
        if src_id in manifest['equipment']:
            manifest['equipment'][src_id]['arrival_rate'] = params['arrival_rate']
    
    for eq_id, eq_data in manifest['equipment'].items():
        if any(x in eq_id for x in ['FIL', 'PCK', 'PAL']):
            eq_data['base_rate'] = params['base_rate']
        
        if 'BUF' in eq_id and 'capacity' in eq_data:
            eq_data['capacity'] = int(eq_data['capacity'] * params['buffer_mult'])
    
    # Adjust failure patterns
    for pattern in manifest.get('failure_patterns', {}).values():
        for failure in pattern.values():
            if 'mtbf' in failure:
                failure['mtbf'] = failure['mtbf'] * params['mtbf_mult']
            if 'mttr' in failure:
                failure['mttr'] = failure['mttr'] * params['mttr_mult']
    
    # Save temporarily
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f)
    
    # Build and run
    builder = OntologyDrivenModelBuilder(
        ontology_path=Path("ontology/twin_ontology.yaml"),
        manifest_dir=Path("manifests")
    )
    
    env = simpy.Environment()
    model = builder.build_model(env)
    env.run(until=sim_minutes)
    
    # Calculate simple KPIs
    total_produced = 0
    total_scrapped = 0
    total_downtime = 0
    equipment_count = 0
    
    for prim_id, prim in builder.primitives.items():
        if 'FIL' in prim_id or 'PCK' in prim_id or 'PAL' in prim_id:
            total_produced += prim.units_produced
            total_scrapped += prim.units_scrapped
            total_downtime += prim.total_downtime
            equipment_count += 1
    
    # Calculate metrics
    total_units = total_produced + total_scrapped
    availability = ((sim_minutes * equipment_count - total_downtime) / 
                   (sim_minutes * equipment_count)) * 100 if equipment_count > 0 else 0
    
    # Estimate performance (assuming base_rate as ideal)
    ideal_production = params['base_rate'] * sim_minutes * equipment_count
    performance = (total_units / ideal_production) * 100 if ideal_production > 0 else 0
    
    quality = (total_produced / total_units) * 100 if total_units > 0 else 90
    
    oee = (availability * performance * quality) / 10000
    
    return {
        'oee': oee,
        'availability': availability,
        'performance': performance,
        'quality': quality,
        'total_units': total_units
    }


def main():
    """Run fast calibration tests."""
    print("="*60)
    print("FAST CALIBRATION TEST")
    print("="*60)
    
    # Target KPIs
    target_kpis = {
        'oee': 67.9,
        'availability': 100.0,
        'performance': 75.1,
        'quality': 91.2
    }
    
    print("\nTarget KPIs:")
    for k, v in target_kpis.items():
        print(f"  {k}: {v:.1f}%")
    
    # Save original manifest
    import shutil
    manifest_path = Path("manifests/equipment_manifest.yaml")
    backup_path = Path("manifests/equipment_manifest.yaml.backup")
    shutil.copy(manifest_path, backup_path)
    
    # Test configurations (focused set)
    test_configs = [
        # Baseline
        {'arrival_rate': 100, 'base_rate': 70, 'buffer_mult': 1.0, 'mtbf_mult': 1.0, 'mttr_mult': 1.0},
        # Improve performance
        {'arrival_rate': 150, 'base_rate': 85, 'buffer_mult': 1.5, 'mtbf_mult': 1.0, 'mttr_mult': 1.0},
        # Improve availability
        {'arrival_rate': 125, 'base_rate': 85, 'buffer_mult': 1.5, 'mtbf_mult': 2.0, 'mttr_mult': 0.7},
        # Balanced improvement
        {'arrival_rate': 140, 'base_rate': 90, 'buffer_mult': 2.0, 'mtbf_mult': 3.0, 'mttr_mult': 0.5},
        # Aggressive
        {'arrival_rate': 175, 'base_rate': 100, 'buffer_mult': 2.5, 'mtbf_mult': 4.0, 'mttr_mult': 0.3},
    ]
    
    best_config = None
    best_kpis = None
    best_error = float('inf')
    
    for i, config in enumerate(test_configs, 1):
        print(f"\nTest {i}: {config}")
        
        try:
            kpis = run_single_test(config, sim_minutes=120)  # 2 hours sim
            
            # Calculate error
            error = 0
            weights = {'oee': 2.0, 'performance': 1.5, 'availability': 1.0, 'quality': 0.5}
            for key, weight in weights.items():
                target = target_kpis[key]
                current = kpis[key]
                error += abs(target - current) * weight / target if target > 0 else 0
            
            print(f"  Results: OEE={kpis['oee']:.1f}%, Perf={kpis['performance']:.1f}%, Avail={kpis['availability']:.1f}%")
            print(f"  Error score: {error:.2f}")
            
            if error < best_error:
                best_error = error
                best_config = config
                best_kpis = kpis
                print("  ✓ New best!")
                
        except Exception as e:
            print(f"  Failed: {e}")
            continue
    
    # Restore original
    shutil.copy(backup_path, manifest_path)
    
    print("\n" + "="*60)
    print("CALIBRATION RESULTS")
    print("="*60)
    
    if best_config:
        print("\nBest Configuration:")
        for k, v in best_config.items():
            print(f"  {k}: {v}")
        
        print("\nAchieved KPIs:")
        for k in ['oee', 'availability', 'performance', 'quality']:
            achieved = best_kpis[k]
            target = target_kpis[k]
            gap = achieved - target
            print(f"  {k}: {achieved:.1f}% (target: {target:.1f}%, gap: {gap:+.1f}%)")
        
        # Save calibration results
        results = {
            'best_parameters': best_config,
            'achieved_kpis': best_kpis,
            'target_kpis': target_kpis,
            'error_score': best_error
        }
        
        with open('calibration_results.yaml', 'w') as f:
            yaml.dump(results, f)
        
        print("\n✓ Results saved to calibration_results.yaml")
        
        # Apply best config to manifest
        print("\nApplying best configuration to manifest...")
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        for src_id in ['LINE1-SRC', 'LINE2-SRC', 'LINE3-SRC']:
            if src_id in manifest['equipment']:
                manifest['equipment'][src_id]['arrival_rate'] = best_config['arrival_rate']
        
        for eq_id, eq_data in manifest['equipment'].items():
            if any(x in eq_id for x in ['FIL', 'PCK', 'PAL']):
                eq_data['base_rate'] = best_config['base_rate']
            
            if 'BUF' in eq_id and 'capacity' in eq_data:
                original = eq_data['capacity'] / best_config.get('buffer_mult', 1.0)
                eq_data['capacity'] = int(original * best_config['buffer_mult'])
        
        for pattern in manifest.get('failure_patterns', {}).values():
            for failure in pattern.values():
                if 'mtbf' in failure:
                    original = failure['mtbf'] / best_config.get('mtbf_mult', 1.0) 
                    failure['mtbf'] = original * best_config['mtbf_mult']
                if 'mttr' in failure:
                    original = failure['mttr'] / best_config.get('mttr_mult', 1.0)
                    failure['mttr'] = original * best_config['mttr_mult']
        
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f)
        
        print("✓ Manifest updated with calibrated parameters")
    else:
        print("\n✗ No successful configuration found")


if __name__ == "__main__":
    main()