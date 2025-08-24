"""Recalibrate model for realistic, balanced KPIs."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import yaml
import shutil


def recalibrate_for_balanced_kpis():
    """Recalibrate model for realistic OEE ~60% with balanced components."""
    
    print("="*60)
    print("RECALIBRATING FOR BALANCED KPIS")
    print("="*60)
    
    # Define realistic target KPIs
    # OEE = Availability × Performance × Quality
    # 60% = 85% × 85% × 83%
    target_kpis = {
        'oee': 60.0,
        'availability': 85.0,  # Some downtime is realistic
        'performance': 85.0,   # Some speed losses are normal
        'quality': 83.0,       # Some defects are expected
        'downtime_pct': 15.0,  # 15% downtime (100% - 85% availability)
        'scrap_rate': 17.0     # 17% scrap (100% - 83% quality)
    }
    
    print("\nRealistic Target KPIs:")
    for key, value in target_kpis.items():
        print(f"  {key}: {value:.1f}%")
    
    print(f"\nCalculated OEE: {0.85 * 0.85 * 0.83 * 100:.1f}%")
    
    # Parameters for balanced performance
    # More moderate adjustments than before
    balanced_params = {
        'arrival_rate': 110,      # Moderate increase (was 100 baseline)
        'base_rate': 75,          # Slight increase (was 70 baseline)
        'buffer_mult': 1.5,       # Moderate buffer increase
        'mtbf_mult': 1.5,         # Moderate reliability improvement
        'mttr_mult': 0.75,        # Moderate repair time reduction
    }
    
    print("\nBalanced Parameters:")
    for k, v in balanced_params.items():
        print(f"  {k}: {v}")
    
    # Backup current manifest
    manifest_path = Path("manifests/equipment_manifest.yaml")
    backup_path = Path("manifests/equipment_manifest.yaml.calibrated_v1")
    shutil.copy(manifest_path, backup_path)
    print(f"\n✓ Backed up current manifest to: {backup_path}")
    
    # Load original (pre-calibration) manifest
    original_backup = Path("manifests/equipment_manifest.yaml.pre_calibration")
    if original_backup.exists():
        shutil.copy(original_backup, manifest_path)
        print(f"✓ Restored original manifest from: {original_backup}")
    
    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)
    
    # Apply balanced parameters
    print("\nApplying balanced calibration...")
    
    # Sources - moderate arrival rate
    for src_id in ['LINE1-SRC', 'LINE2-SRC', 'LINE3-SRC']:
        if src_id in manifest['equipment']:
            manifest['equipment'][src_id]['arrival_rate'] = balanced_params['arrival_rate']
    
    # Equipment - moderate base rate increase
    for eq_id, eq_data in manifest['equipment'].items():
        if any(x in eq_id for x in ['FIL', 'PCK', 'PAL']):
            eq_data['base_rate'] = balanced_params['base_rate']
    
    # Buffers - moderate capacity increase
    for buf_id, buf_data in manifest['equipment'].items():
        if 'BUF' in buf_id and 'capacity' in buf_data:
            # Get original capacity (assuming current is baseline)
            original = buf_data['capacity']
            buf_data['capacity'] = int(original * balanced_params['buffer_mult'])
    
    # Failure patterns - moderate improvements
    for pattern_name, pattern in manifest.get('failure_patterns', {}).items():
        for failure_name, failure in pattern.items():
            # Increase MTBF moderately
            if 'mtbf' in failure:
                failure['mtbf'] = failure['mtbf'] * balanced_params['mtbf_mult']
            
            # Reduce MTTR moderately
            if 'mttr' in failure:
                failure['mttr'] = failure['mttr'] * balanced_params['mttr_mult']
            
            # Slightly reduce micro-stop probabilities
            if 'probability_per_5min' in failure:
                failure['probability_per_5min'] = failure['probability_per_5min'] * 0.8
    
    # Save recalibrated manifest
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    print("✓ Balanced calibration applied to manifest")
    
    # Save calibration record
    calibration_record = {
        'calibration_type': 'balanced_realistic',
        'target_kpis': target_kpis,
        'parameters_applied': balanced_params,
        'expected_results': {
            'oee': '~60%',
            'availability': '~85%',
            'performance': '~85%',
            'quality': '~83%'
        },
        'notes': [
            'Targeting realistic OEE of 60%',
            'Balanced contributions from all three OEE components',
            'Moderate parameter adjustments for stability',
            'Realistic downtime and scrap rates'
        ]
    }
    
    with open('balanced_calibration.yaml', 'w') as f:
        yaml.dump(calibration_record, f, default_flow_style=False)
    
    print("✓ Calibration record saved to: balanced_calibration.yaml")
    
    print("\n" + "="*60)
    print("RECALIBRATION COMPLETE")
    print("="*60)
    print("\nExpected Results:")
    print("  • OEE: ~60% (balanced across components)")
    print("  • Availability: ~85% (realistic downtime)")
    print("  • Performance: ~85% (achievable speed)")
    print("  • Quality: ~83% (acceptable defect rate)")
    
    return balanced_params, target_kpis


if __name__ == "__main__":
    recalibrate_for_balanced_kpis()