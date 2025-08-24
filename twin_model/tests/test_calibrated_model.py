"""Test calibrated model and compare with historical KPIs."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import pandas as pd
import numpy as np
import random
import simpy
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction import MESTransducer


def test_calibrated_model():
    """Run calibrated model and calculate KPIs."""
    
    print("="*60)
    print("TESTING CALIBRATED MODEL")
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
    
    print("\nTarget KPIs (from historical data):")
    for key, value in target_kpis.items():
        print(f"  {key}: {value:.1f}%")
    
    # Build and run calibrated model
    print("\nRunning calibrated model simulation (7 days)...")
    
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    builder = OntologyDrivenModelBuilder(
        ontology_path=ontology_path,
        manifest_dir=manifest_dir
    )
    
    env = simpy.Environment()
    model = builder.build_model(env)
    
    # Run for 7 days
    simulation_minutes = 7 * 24 * 60
    env.run(until=simulation_minutes)
    
    # Collect observables
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
    
    print("\nAchieved KPIs (calibrated model):")
    for key in target_kpis.keys():
        achieved = achieved_kpis[key]
        target = target_kpis[key]
        gap = achieved - target
        symbol = "✓" if abs(gap) < 10 else "✗"
        print(f"  {key}: {achieved:.1f}% (target: {target:.1f}%, gap: {gap:+.1f}%) {symbol}")
    
    # Save results
    mes_df.to_csv('calibrated_baseline_data.csv', index=False)
    print(f"\n✓ Calibrated data saved to: calibrated_baseline_data.csv")
    print(f"  Generated {len(mes_df)} records")
    
    # Production summary
    print("\nProduction Summary:")
    total_good = mes_df['GoodUnitsProduced'].sum()
    total_scrap = mes_df['ScrapUnitsProduced'].sum()
    total_units = total_good + total_scrap
    
    print(f"  Total good units: {total_good:,}")
    print(f"  Total scrap units: {total_scrap:,}")
    print(f"  Total units: {total_units:,}")
    print(f"  Scrap rate: {(total_scrap/total_units*100):.1f}%")
    
    # Calculate improvement from baseline
    print("\n" + "="*60)
    print("CALIBRATION IMPACT")
    print("="*60)
    
    # Original baseline (before calibration) was around 5.8% OEE
    baseline_oee = 5.8
    improvement = achieved_kpis['oee'] - baseline_oee
    
    print(f"\nOEE Improvement:")
    print(f"  Before calibration: {baseline_oee:.1f}%")
    print(f"  After calibration: {achieved_kpis['oee']:.1f}%")
    print(f"  Improvement: {improvement:+.1f} percentage points")
    print(f"  Target: {target_kpis['oee']:.1f}%")
    
    if achieved_kpis['oee'] > 60:
        print("\n✓ Calibration successful! Model is approaching historical performance.")
    elif achieved_kpis['oee'] > 40:
        print("\n⚠ Partial success. Model improved significantly but needs fine-tuning.")
    else:
        print("\n✗ Model still needs significant calibration work.")
    
    return achieved_kpis, target_kpis


if __name__ == "__main__":
    test_calibrated_model()