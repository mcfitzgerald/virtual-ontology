"""Test the balanced calibration model."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import pandas as pd
import numpy as np
import random
import simpy
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction import MESTransducer


def test_balanced_model():
    """Run simulation with balanced calibration."""
    
    print("="*60)
    print("TESTING BALANCED CALIBRATION")
    print("="*60)
    
    # Set seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    # Target KPIs (balanced)
    target_kpis = {
        'oee': 60.0,
        'availability': 85.0,
        'performance': 85.0,
        'quality': 83.0,
        'downtime_pct': 15.0,
        'scrap_rate': 17.0
    }
    
    print("\nTarget KPIs (Balanced):")
    for key, value in target_kpis.items():
        print(f"  {key}: {value:.1f}%")
    
    # Build and run model
    print("\nRunning 1-day simulation with balanced parameters...")
    
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
    
    # Collect production statistics by line
    print("\n" + "-"*60)
    print("PRODUCTION LINE PERFORMANCE")
    print("-"*60)
    
    total_produced = 0
    total_scrapped = 0
    total_downtime = 0
    equipment_count = 0
    
    for line_num in [1, 2, 3]:
        line_produced = 0
        line_scrapped = 0
        line_efficiency = []
        
        for prim_id, primitive in builder.primitives.items():
            if f'LINE{line_num}' in prim_id:
                if hasattr(primitive, 'units_produced'):
                    line_produced += primitive.units_produced
                    line_scrapped += primitive.units_scrapped
                    
                    if any(x in prim_id for x in ['FIL', 'PCK', 'PAL']):
                        total_downtime += getattr(primitive, 'total_downtime', 0)
                        equipment_count += 1
                        
                        # Calculate efficiency
                        total_units = primitive.units_produced + primitive.units_scrapped
                        rate = total_units / simulation_minutes
                        eff = (rate / primitive.base_rate) * 100 if hasattr(primitive, 'base_rate') else 0
                        line_efficiency.append(eff)
        
        total_produced += line_produced
        total_scrapped += line_scrapped
        
        print(f"\nLINE {line_num}:")
        print(f"  Good units: {line_produced:,}")
        print(f"  Scrap units: {line_scrapped:,}")
        print(f"  Avg efficiency: {np.mean(line_efficiency) if line_efficiency else 0:.1f}%")
    
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
    
    # Display KPI comparison
    print("\n" + "="*60)
    print("KPI COMPARISON (BALANCED CALIBRATION)")
    print("="*60)
    
    print("\n{:<20} {:>12} {:>12} {:>12} {:>8}".format(
        "Metric", "Achieved", "Target", "Gap", "Status"
    ))
    print("-" * 70)
    
    for key in ['oee', 'availability', 'performance', 'quality']:
        achieved = achieved_kpis[key]
        target = target_kpis[key]
        gap = achieved - target
        
        # Determine status
        if abs(gap) < 10:
            status = "✓ GOOD"
        elif abs(gap) < 20:
            status = "⚠ CLOSE"
        else:
            status = "✗ MISS"
        
        print("{:<20} {:>11.1f}% {:>11.1f}% {:>11.1f}% {:>8}".format(
            key.upper(), achieved, target, gap, status
        ))
    
    # Calculate component balance
    print("\n" + "-"*60)
    print("OEE COMPONENT BALANCE")
    print("-"*60)
    
    if achieved_kpis['availability'] > 0 and achieved_kpis['performance'] > 0 and achieved_kpis['quality'] > 0:
        calculated_oee = (achieved_kpis['availability'] * 
                         achieved_kpis['performance'] * 
                         achieved_kpis['quality']) / 10000
        
        print(f"\nCalculated OEE: {achieved_kpis['availability']:.1f}% × "
              f"{achieved_kpis['performance']:.1f}% × "
              f"{achieved_kpis['quality']:.1f}% = {calculated_oee:.1f}%")
        print(f"Reported OEE: {achieved_kpis['oee']:.1f}%")
        
        # Check balance
        components = [achieved_kpis['availability'], achieved_kpis['performance'], achieved_kpis['quality']]
        std_dev = np.std(components)
        
        print(f"\nComponent spread (std dev): {std_dev:.1f}%")
        if std_dev < 10:
            print("✓ Well-balanced OEE components")
        elif std_dev < 20:
            print("⚠ Moderately balanced components")
        else:
            print("✗ Unbalanced components")
    
    # Overall assessment
    print("\n" + "="*60)
    print("BALANCED CALIBRATION ASSESSMENT")
    print("="*60)
    
    oee_gap = abs(achieved_kpis['oee'] - target_kpis['oee'])
    
    if oee_gap < 10:
        print("\n✓ EXCELLENT: Balanced calibration achieved target!")
        print("  Model has realistic, well-balanced KPIs.")
    elif oee_gap < 20:
        print("\n✓ GOOD: Calibration is close to balanced targets.")
        print("  Minor adjustments may improve balance.")
    elif oee_gap < 40:
        print("\n⚠ PARTIAL: Progress toward balanced KPIs.")
        print("  Further tuning needed for target achievement.")
    else:
        print("\n✗ INSUFFICIENT: Significant gap from targets.")
        print("  Review parameter settings and constraints.")
    
    # Save results
    mes_df.to_csv('balanced_simulation_results.csv', index=False)
    print(f"\n✓ Results saved to: balanced_simulation_results.csv")
    print(f"  Generated {len(mes_df)} MES records")
    
    # Summary
    print("\nProduction Summary:")
    print(f"  Total good units: {total_produced:,}")
    print(f"  Total scrap units: {total_scrapped:,}")
    print(f"  Overall scrap rate: {(total_scrapped/(total_produced+total_scrapped)*100):.1f}%")
    
    return achieved_kpis


if __name__ == "__main__":
    test_balanced_model()