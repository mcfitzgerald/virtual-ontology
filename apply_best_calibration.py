"""Apply best calibration parameters based on analysis."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import yaml
import shutil


def apply_calibration():
    """Apply best calibration parameters to manifest."""
    
    # Best parameters from analysis
    # These parameters aim to match historical KPIs:
    # Target: OEE=67.9%, Performance=75.1%, Availability=100%
    best_params = {
        'arrival_rate': 140,      # Increased from 100 to prevent starvation
        'base_rate': 90,          # Increased from 70 to improve performance
        'buffer_mult': 2.0,       # Double buffer sizes to prevent blocking
        'mtbf_mult': 3.0,         # Triple MTBF to reduce failures
        'mttr_mult': 0.5,         # Halve MTTR for faster repairs
    }
    
    print("="*60)
    print("APPLYING BEST CALIBRATION PARAMETERS")
    print("="*60)
    
    print("\nParameters to apply:")
    for k, v in best_params.items():
        print(f"  {k}: {v}")
    
    # Backup original
    manifest_path = Path("manifests/equipment_manifest.yaml")
    backup_path = Path("manifests/equipment_manifest.yaml.pre_calibration")
    
    if not backup_path.exists():
        shutil.copy(manifest_path, backup_path)
        print(f"\n✓ Created backup: {backup_path}")
    
    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)
    
    # Apply arrival rate to sources
    for src_id in ['LINE1-SRC', 'LINE2-SRC', 'LINE3-SRC']:
        if src_id in manifest['equipment']:
            original = manifest['equipment'][src_id].get('arrival_rate', 100)
            manifest['equipment'][src_id]['arrival_rate'] = best_params['arrival_rate']
            print(f"\n{src_id}:")
            print(f"  arrival_rate: {original} → {best_params['arrival_rate']}")
    
    # Apply base rate to equipment
    print("\nEquipment base rates:")
    for eq_id, eq_data in manifest['equipment'].items():
        if any(x in eq_id for x in ['FIL', 'PCK', 'PAL']):
            original = eq_data.get('base_rate', 70)
            eq_data['base_rate'] = best_params['base_rate']
            if 'FIL' in eq_id and 'LINE1' in eq_id:  # Show one example
                print(f"  {eq_id}: {original} → {best_params['base_rate']}")
    
    # Apply buffer capacity multiplier
    print("\nBuffer capacities (multiplied by {:.1f}):".format(best_params['buffer_mult']))
    for buf_id, buf_data in manifest['equipment'].items():
        if 'BUF' in buf_id and 'capacity' in buf_data:
            original = buf_data['capacity']
            # Assuming current values are already baseline, multiply them
            buf_data['capacity'] = int(original * best_params['buffer_mult'])
            if 'LINE1-BUF-1' in buf_id:  # Show one example
                print(f"  {buf_id}: {original} → {buf_data['capacity']}")
    
    # Apply MTBF/MTTR adjustments
    print("\nFailure pattern adjustments:")
    print(f"  MTBF multiplied by {best_params['mtbf_mult']}")
    print(f"  MTTR multiplied by {best_params['mttr_mult']}")
    
    for pattern_name, pattern in manifest.get('failure_patterns', {}).items():
        for failure_name, failure in pattern.items():
            if 'mtbf' in failure:
                original_mtbf = failure['mtbf']
                failure['mtbf'] = original_mtbf * best_params['mtbf_mult']
                
            if 'mttr' in failure:
                original_mttr = failure['mttr']
                failure['mttr'] = original_mttr * best_params['mttr_mult']
            
            # Also reduce micro-stop probabilities
            if 'probability_per_5min' in failure:
                original_prob = failure['probability_per_5min']
                failure['probability_per_5min'] = original_prob * 0.5  # Reduce by half
    
    # Save calibrated manifest
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    print("\n✓ Calibrated manifest saved to:", manifest_path)
    
    # Save calibration record
    calibration_record = {
        'parameters_applied': best_params,
        'target_kpis': {
            'oee': 67.9,
            'availability': 100.0,
            'performance': 75.1,
            'quality': 91.2,
            'downtime_pct': 30.6,
            'scrap_rate': 8.9
        },
        'notes': [
            'Arrival rate increased to prevent equipment starvation',
            'Base rate increased to improve performance',
            'Buffer sizes doubled to prevent blocking',
            'MTBF tripled to reduce failure frequency',
            'MTTR halved for faster repairs',
            'Micro-stop probabilities reduced by 50%'
        ]
    }
    
    with open('calibration_applied.yaml', 'w') as f:
        yaml.dump(calibration_record, f, default_flow_style=False)
    
    print("✓ Calibration record saved to: calibration_applied.yaml")
    
    print("\n" + "="*60)
    print("CALIBRATION COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Run 'python generate_baseline.py' to test calibrated model")
    print("2. Compare output KPIs with historical targets")
    print("3. Fine-tune if needed")


if __name__ == "__main__":
    apply_calibration()