"""Test the fixed model with realistic KPIs."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import pandas as pd
import numpy as np
import random
import simpy
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction import MESTransducer


def test_fixed_model():
    """Run simulation with fixed parameters."""
    
    print("="*60)
    print("TESTING FIXED MODEL")
    print("="*60)
    
    # Set seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    # Target KPIs
    target_kpis = {
        'oee': 60.0,
        'availability': 60.0,  # Realistic downtime
        'performance': 85.0,   # Fixed performance factors
        'quality': 95.0        # High quality
    }
    
    print("\nTarget KPIs:")
    for key, value in target_kpis.items():
        print(f"  {key}: {value:.1f}%")
    
    print("\nRunning 1-day simulation with fixed parameters...")
    print("  - Performance factors: 0.77-0.95 (fixed from 0.43-0.55)")
    print("  - MTBF: 18-27 minutes (reduced for more failures)")
    print("  - Failure probabilities: Increased by 50%")
    print("  - Quality rate: 0.95")
    
    # Build and run model
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
    
    # Calculate KPIs
    if len(mes_df) > 0:
        valid = mes_df[mes_df['OEE_Score'] > 0]
        
        achieved_kpis = {
            'oee': valid['OEE_Score'].mean() if len(valid) > 0 else 0,
            'availability': valid['Availability_Score'].mean() if len(valid) > 0 else 0,
            'performance': valid['Performance_Score'].mean() if len(valid) > 0 else 0,
            'quality': valid['Quality_Score'].mean() if len(valid) > 0 else 0,
        }
    else:
        achieved_kpis = {k: 0 for k in target_kpis.keys()}
    
    # Display results
    print("\n" + "="*60)
    print("RESULTS - FIXED MODEL")
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
    
    # Calculate actual OEE from components
    calculated_oee = (achieved_kpis['availability'] * 
                     achieved_kpis['performance'] * 
                     achieved_kpis['quality']) / 10000
    
    print(f"\nCalculated OEE: {achieved_kpis['availability']:.1f}% × "
          f"{achieved_kpis['performance']:.1f}% × "
          f"{achieved_kpis['quality']:.1f}% = {calculated_oee:.1f}%")
    
    # Production summary
    total_good = mes_df['GoodUnitsProduced'].sum()
    total_scrap = mes_df['ScrapUnitsProduced'].sum()
    total_units = total_good + total_scrap
    
    print("\nProduction Summary:")
    print(f"  Total good units: {total_good:,}")
    print(f"  Total scrap units: {total_scrap:,}")
    print(f"  Total units: {total_units:,}")
    print(f"  Scrap rate: {(total_scrap/total_units*100) if total_units > 0 else 0:.1f}%")
    
    # Overall assessment
    print("\n" + "="*60)
    print("ASSESSMENT")
    print("="*60)
    
    oee_gap = abs(achieved_kpis['oee'] - target_kpis['oee'])
    
    if oee_gap < 10:
        print("\n✓ SUCCESS: Model achieves realistic KPIs!")
        print("  • OEE around 60%")
        print("  • Balanced availability, performance, and quality")
        print("  • Ready for production simulation")
    elif oee_gap < 20:
        print("\n⚠ CLOSE: Model is near target KPIs")
        print("  • Minor adjustments may help")
        print("  • Check individual component gaps")
    else:
        print("\n✗ NEEDS WORK: Significant gap remains")
        print("  • Review parameter adjustments")
        print("  • Check for remaining bottlenecks")
    
    # Save results
    mes_df.to_csv('fixed_model_results.csv', index=False)
    print(f"\n✓ Results saved to: fixed_model_results.csv")
    
    return achieved_kpis


if __name__ == "__main__":
    test_fixed_model()