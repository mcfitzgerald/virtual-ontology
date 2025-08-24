"""Run calibrated simulation and analyze results."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import pandas as pd
import numpy as np
import random
import simpy
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction import MESTransducer


def run_calibrated_simulation():
    """Run simulation with calibrated parameters."""
    
    print("="*60)
    print("RUNNING CALIBRATED SIMULATION")
    print("="*60)
    
    # Set seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    # Load historical targets
    historical_df = pd.read_csv('archive/misc/data/mes_data_with_kpis.csv')
    valid_hist = historical_df[historical_df['OEE_Score'] > 0]
    
    target_kpis = {
        'oee': valid_hist['OEE_Score'].mean(),
        'availability': valid_hist['Availability_Score'].mean(),
        'performance': valid_hist['Performance_Score'].mean(),
        'quality': valid_hist['Quality_Score'].mean(),
        'downtime_pct': (historical_df['MachineStatus'] == 'Stopped').mean() * 100,
        'scrap_rate': (historical_df['ScrapUnitsProduced'].sum() / 
                      (historical_df['GoodUnitsProduced'].sum() + 
                       historical_df['ScrapUnitsProduced'].sum()) * 100)
    }
    
    print("\nTarget KPIs (Historical):")
    for key, value in target_kpis.items():
        print(f"  {key}: {value:.1f}%")
    
    # Build and run calibrated model
    print("\nRunning 1-day simulation with calibrated parameters...")
    
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    builder = OntologyDrivenModelBuilder(
        ontology_path=ontology_path,
        manifest_dir=manifest_dir
    )
    
    env = simpy.Environment()
    model = builder.build_model(env)
    
    # Run for 1 day
    simulation_minutes = 1 * 24 * 60
    env.run(until=simulation_minutes)
    
    # Collect production statistics
    print("\n" + "-"*60)
    print("PRODUCTION LINE PERFORMANCE")
    print("-"*60)
    
    line_stats = {}
    for line_num in [1, 2, 3]:
        line_data = {
            'produced': 0,
            'scrapped': 0,
            'downtime': 0,
            'efficiency': []
        }
        
        for prim_id, primitive in builder.primitives.items():
            if f'LINE{line_num}' in prim_id:
                if hasattr(primitive, 'units_produced'):
                    line_data['produced'] += primitive.units_produced
                    line_data['scrapped'] += primitive.units_scrapped
                    line_data['downtime'] += getattr(primitive, 'total_downtime', 0)
                    
                    # Calculate efficiency for equipment
                    if any(x in prim_id for x in ['FIL', 'PCK', 'PAL']):
                        total = primitive.units_produced + primitive.units_scrapped
                        rate = total / simulation_minutes
                        eff = (rate / primitive.base_rate) * 100 if hasattr(primitive, 'base_rate') else 0
                        line_data['efficiency'].append(eff)
        
        line_stats[f'LINE{line_num}'] = line_data
        
        # Print line summary
        total_units = line_data['produced'] + line_data['scrapped']
        avg_efficiency = np.mean(line_data['efficiency']) if line_data['efficiency'] else 0
        
        print(f"\nLINE {line_num}:")
        print(f"  Good units: {line_data['produced']:,}")
        print(f"  Scrap units: {line_data['scrapped']:,}")
        print(f"  Total units: {total_units:,}")
        print(f"  Avg equipment efficiency: {avg_efficiency:.1f}%")
    
    # Collect observables for KPI calculation
    all_observables = []
    for primitive_id, primitive in builder.primitives.items():
        if hasattr(primitive, 'get_observables'):
            observables = primitive.get_observables()
            for obs in observables:
                obs['primitive_id'] = primitive_id
                all_observables.append(obs)
    
    # Transduce to MES format
    transducer = MESTransducer(time_bucket=5)
    mes_df = transducer.process_observables(all_observables, builder.manifests)
    
    # Calculate achieved KPIs
    print("\n" + "="*60)
    print("KPI COMPARISON")
    print("="*60)
    
    if len(mes_df) > 0:
        valid = mes_df[mes_df['OEE_Score'] > 0]
        
        achieved_kpis = {
            'oee': valid['OEE_Score'].mean() if len(valid) > 0 else 0,
            'availability': valid['Availability_Score'].mean() if len(valid) > 0 else 0,
            'performance': valid['Performance_Score'].mean() if len(valid) > 0 else 0,
            'quality': valid['Quality_Score'].mean() if len(valid) > 0 else 0,
            'downtime_pct': (mes_df['MachineStatus'] == 'Stopped').mean() * 100,
            'scrap_rate': (mes_df['ScrapUnitsProduced'].sum() / 
                          (mes_df['GoodUnitsProduced'].sum() + 
                           mes_df['ScrapUnitsProduced'].sum() + 0.01) * 100)
        }
    else:
        achieved_kpis = {k: 0 for k in target_kpis.keys()}
    
    # Display comparison
    print("\n{:<20} {:>12} {:>12} {:>12} {:>8}".format(
        "Metric", "Achieved", "Target", "Gap", "Status"
    ))
    print("-" * 70)
    
    for key in ['oee', 'availability', 'performance', 'quality']:
        achieved = achieved_kpis[key]
        target = target_kpis[key]
        gap = achieved - target
        
        # Determine status
        if abs(gap) < 5:
            status = "✓ GOOD"
            color = ""
        elif abs(gap) < 15:
            status = "⚠ CLOSE"
            color = ""
        else:
            status = "✗ MISS"
            color = ""
        
        print("{:<20} {:>11.1f}% {:>11.1f}% {:>11.1f}% {:>8}".format(
            key.upper(), achieved, target, gap, status
        ))
    
    # Overall assessment
    print("\n" + "="*60)
    print("CALIBRATION EFFECTIVENESS")
    print("="*60)
    
    oee_improvement = achieved_kpis['oee'] - 5.8  # Original baseline was ~5.8%
    
    print(f"\nOEE Journey:")
    print(f"  Baseline (uncalibrated): 5.8%")
    print(f"  Current (calibrated): {achieved_kpis['oee']:.1f}%")
    print(f"  Target (historical): {target_kpis['oee']:.1f}%")
    print(f"  Improvement: +{oee_improvement:.1f} percentage points")
    
    # Calculate overall success
    oee_gap = abs(achieved_kpis['oee'] - target_kpis['oee'])
    
    if oee_gap < 5:
        print("\n✓ EXCELLENT: Calibration achieved target KPIs!")
    elif oee_gap < 15:
        print("\n✓ GOOD: Calibration significantly improved performance.")
        print("  Minor fine-tuning may help close the remaining gap.")
    elif oee_gap < 30:
        print("\n⚠ PARTIAL: Calibration improved but needs more tuning.")
    else:
        print("\n✗ INSUFFICIENT: Calibration needs significant adjustment.")
    
    # Save results
    mes_df.to_csv('calibrated_simulation_results.csv', index=False)
    print(f"\n✓ Results saved to: calibrated_simulation_results.csv")
    print(f"  Generated {len(mes_df)} MES records")
    
    return achieved_kpis, target_kpis


if __name__ == "__main__":
    run_calibrated_simulation()