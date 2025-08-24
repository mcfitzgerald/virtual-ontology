"""Fix manifest to achieve realistic KPIs.

Target KPIs:
- OEE: ~60%
- Availability: ~60% (more failures needed)
- Performance: ~85% (fix product performance factors)
- Quality: ~95% (already good)
"""

import yaml
import shutil
from pathlib import Path


def fix_manifest_for_realistic_kpis():
    """Fix manifest parameters for realistic performance."""
    
    print("="*60)
    print("FIXING MANIFEST FOR REALISTIC KPIS")
    print("="*60)
    
    # Target KPIs
    targets = {
        'oee': 60.0,
        'availability': 60.0,  # Corrected from 85%
        'performance': 85.0,
        'quality': 95.0
    }
    
    print("\nTarget KPIs:")
    for k, v in targets.items():
        print(f"  {k}: {v:.1f}%")
    
    # Backup current manifest
    manifest_path = Path("manifests/equipment_manifest.yaml")
    backup_path = Path("manifests/equipment_manifest.yaml.before_fix")
    shutil.copy(manifest_path, backup_path)
    print(f"\n✓ Backed up to: {backup_path}")
    
    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)
    
    print("\nApplying fixes...")
    
    # FIX 1: Performance factors should be ABOVE 1.0 for normal performance
    # Current values (0.43-0.55) make equipment run at <50% speed
    # To achieve 85% performance, we need factors around 0.85-0.95
    # BUT: In the code, factor < 1.0 means SLOWER, so we need to INVERT the logic
    # Actually, let's set them to more reasonable values
    
    print("\n1. Fixing performance_by_product values...")
    print("   Current: 0.43-0.55 (causes <50% speed)")
    print("   Target: 0.80-0.95 (for ~85% performance)")
    
    for eq_id, eq_data in manifest['equipment'].items():
        if 'performance_by_product' in eq_data:
            # Current values are 0.43-0.55, which severely slow down production
            # Increase to 0.80-0.95 range for more realistic performance
            for product in eq_data['performance_by_product']:
                old_val = eq_data['performance_by_product'][product]
                # Scale up by ~1.8x to get from ~0.48 to ~0.86
                new_val = min(0.95, old_val * 1.8)
                eq_data['performance_by_product'][product] = round(new_val, 2)
                
                if 'LINE1-FIL' in eq_id and 'SKU-1001' in product:
                    print(f"   Example: {eq_id}/{product}: {old_val} → {new_val:.2f}")
    
    # FIX 2: Reduce MTBF to achieve 60% availability (more failures)
    # Current MTBF: 30-46 minutes (too reliable)
    # For 60% availability, we need more frequent failures
    
    print("\n2. Adjusting MTBF for 60% availability...")
    print("   Current: 30-46 minutes (too reliable)")
    print("   Target: 15-25 minutes (more failures)")
    
    for eq_id, eq_data in manifest['equipment'].items():
        if any(x in eq_id for x in ['FIL', 'PCK', 'PAL']):
            if 'mtbf' in eq_data:
                old_mtbf = eq_data['mtbf']
                # Reduce MTBF by ~40% to increase failure frequency
                new_mtbf = max(15, int(old_mtbf * 0.6))
                eq_data['mtbf'] = new_mtbf
                
                if 'LINE1-FIL' in eq_id:
                    print(f"   Example: {eq_id}: {old_mtbf} → {new_mtbf} minutes")
    
    # FIX 3: Increase failure probabilities in failure patterns
    print("\n3. Increasing failure probabilities...")
    
    for pattern_name, pattern in manifest.get('failure_patterns', {}).items():
        for failure_name, failure in pattern.items():
            if 'probability_per_5min' in failure:
                old_prob = failure['probability_per_5min']
                # Increase probability by 50% for more failures
                new_prob = min(0.3, old_prob * 1.5)
                failure['probability_per_5min'] = round(new_prob, 3)
                
                if pattern_name == 'Filler' and failure_name == 'micro_stops':
                    print(f"   Example: {pattern_name}/{failure_name}: {old_prob} → {new_prob:.3f}")
    
    # FIX 4: Moderate arrival and base rates
    print("\n4. Adjusting rates for balanced flow...")
    
    # Set arrival rate to match equipment capacity better
    for src_id in ['LINE1-SRC', 'LINE2-SRC', 'LINE3-SRC']:
        if src_id in manifest['equipment']:
            manifest['equipment'][src_id]['arrival_rate'] = 85  # Match target performance
    
    # Set base rates to reasonable levels
    for eq_id, eq_data in manifest['equipment'].items():
        if any(x in eq_id for x in ['FIL', 'PCK', 'PAL']):
            eq_data['base_rate'] = 80  # Slightly higher than current 75
    
    print("   Arrival rate: 85 units/min")
    print("   Equipment base rate: 80 units/min")
    
    # FIX 5: Adjust quality rates for 95% quality target
    print("\n5. Adjusting quality rates...")
    
    for eq_id, eq_data in manifest['equipment'].items():
        if any(x in eq_id for x in ['FIL', 'PCK', 'PAL']):
            # Current quality_rate is 0.63, which is too low
            # Set to 0.95 for 95% quality
            eq_data['quality_rate'] = 0.95
            # Also adjust base_scrap_rate
            eq_data['base_scrap_rate'] = 0.05  # 5% scrap for 95% quality
    
    print("   Quality rate: 0.95 (95% good units)")
    
    # Save fixed manifest
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    print("\n✓ Fixed manifest saved")
    
    # Save fix record
    fix_record = {
        'fixes_applied': {
            'performance_factors': 'Increased from 0.43-0.55 to 0.77-0.95',
            'mtbf': 'Reduced by 40% for more failures',
            'failure_probabilities': 'Increased by 50%',
            'arrival_rate': '85 units/min',
            'base_rate': '80 units/min',
            'quality_rate': '0.95 (95% quality)'
        },
        'expected_kpis': targets,
        'notes': [
            'Performance factors were causing <50% speed',
            'MTBF was too high, causing >95% availability',
            'Quality rates adjusted for 95% target',
            'Rates balanced for smooth flow'
        ]
    }
    
    with open('manifest_fixes.yaml', 'w') as f:
        yaml.dump(fix_record, f, default_flow_style=False)
    
    print("\n✓ Fix record saved to: manifest_fixes.yaml")
    
    print("\n" + "="*60)
    print("MANIFEST FIXED")
    print("="*60)
    print("\nExpected Results:")
    print("  • OEE: ~60% (balanced)")
    print("  • Availability: ~60% (realistic downtime)")
    print("  • Performance: ~85% (proper speed)")
    print("  • Quality: ~95% (low defects)")


if __name__ == "__main__":
    fix_manifest_for_realistic_kpis()