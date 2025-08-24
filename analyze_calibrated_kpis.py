"""Analyze KPIs from calibrated simulation."""

import pandas as pd
import numpy as np

# Load calibrated results
calibrated_df = pd.read_csv('calibrated_simulation_results.csv')

# Load historical data
historical_df = pd.read_csv('archive/misc/data/mes_data_with_kpis.csv')

print("="*60)
print("CALIBRATED MODEL KPI ANALYSIS")
print("="*60)

# Calculate calibrated KPIs
valid_calibrated = calibrated_df[calibrated_df['OEE_Score'] > 0]
valid_historical = historical_df[historical_df['OEE_Score'] > 0]

calibrated_kpis = {
    'oee': valid_calibrated['OEE_Score'].mean(),
    'availability': valid_calibrated['Availability_Score'].mean(),
    'performance': valid_calibrated['Performance_Score'].mean(),
    'quality': valid_calibrated['Quality_Score'].mean(),
    'downtime_pct': (calibrated_df['MachineStatus'] == 'Stopped').mean() * 100,
    'scrap_rate': (calibrated_df['ScrapUnitsProduced'].sum() / 
                  (calibrated_df['GoodUnitsProduced'].sum() + 
                   calibrated_df['ScrapUnitsProduced'].sum()) * 100)
}

historical_kpis = {
    'oee': valid_historical['OEE_Score'].mean(),
    'availability': valid_historical['Availability_Score'].mean(),
    'performance': valid_historical['Performance_Score'].mean(),
    'quality': valid_historical['Quality_Score'].mean(),
    'downtime_pct': (historical_df['MachineStatus'] == 'Stopped').mean() * 100,
    'scrap_rate': (historical_df['ScrapUnitsProduced'].sum() / 
                  (historical_df['GoodUnitsProduced'].sum() + 
                   historical_df['ScrapUnitsProduced'].sum()) * 100)
}

# Display comparison
print("\n{:<20} {:>12} {:>12} {:>12} {:>8}".format(
    "Metric", "Calibrated", "Historical", "Gap", "Status"
))
print("-" * 70)

for key in ['oee', 'availability', 'performance', 'quality', 'downtime_pct', 'scrap_rate']:
    calibrated = calibrated_kpis[key]
    historical = historical_kpis[key]
    gap = calibrated - historical
    
    # Determine status
    if abs(gap) < 5:
        status = "✓ GOOD"
    elif abs(gap) < 15:
        status = "⚠ CLOSE"
    else:
        status = "✗ MISS"
    
    print("{:<20} {:>11.1f}% {:>11.1f}% {:>11.1f}% {:>8}".format(
        key.upper(), calibrated, historical, gap, status
    ))

# Production summary
print("\n" + "-"*60)
print("PRODUCTION SUMMARY")
print("-"*60)

total_good = calibrated_df['GoodUnitsProduced'].sum()
total_scrap = calibrated_df['ScrapUnitsProduced'].sum()
total_units = total_good + total_scrap

print(f"\nCalibrated Model (1 day):")
print(f"  Total good units: {total_good:,}")
print(f"  Total scrap units: {total_scrap:,}")
print(f"  Total units: {total_units:,}")
print(f"  Records generated: {len(calibrated_df):,}")

# Calculate improvement from baseline
print("\n" + "="*60)
print("CALIBRATION IMPACT")
print("="*60)

baseline_oee = 5.8  # Original uncalibrated
calibrated_oee = calibrated_kpis['oee']
target_oee = historical_kpis['oee']

print(f"\nOEE Progression:")
print(f"  1. Baseline (uncalibrated): {baseline_oee:.1f}%")
print(f"  2. Current (calibrated): {calibrated_oee:.1f}%")
print(f"  3. Target (historical): {target_oee:.1f}%")

improvement = calibrated_oee - baseline_oee
remaining_gap = target_oee - calibrated_oee

print(f"\nProgress:")
print(f"  Improvement achieved: +{improvement:.1f} percentage points")
print(f"  Remaining gap: {remaining_gap:.1f} percentage points")
print(f"  Progress to target: {(improvement/(target_oee-baseline_oee)*100):.1f}%")

# Final assessment
print("\n" + "="*60)
print("CALIBRATION ASSESSMENT")
print("="*60)

if calibrated_oee > 60:
    print("\n✓ EXCELLENT: Calibration achieved near-target performance!")
    print("  The model is now closely matching historical KPIs.")
elif calibrated_oee > 40:
    print("\n✓ GOOD: Calibration significantly improved the model.")
    print("  Minor fine-tuning could close the remaining gap.")
elif calibrated_oee > 20:
    print("\n⚠ PARTIAL: Calibration made progress but needs refinement.")
else:
    print("\n✗ INSUFFICIENT: Further calibration required.")

# Recommendations
print("\nRecommendations:")
if remaining_gap > 20:
    print("  • Consider further increasing arrival rates")
    print("  • Review equipment cycle times and constraints")
    print("  • Analyze blocking/starvation patterns")
elif remaining_gap > 10:
    print("  • Fine-tune buffer sizes")
    print("  • Adjust failure patterns")
    print("  • Optimize product mix")
else:
    print("  • Model is well-calibrated")
    print("  • Ready for scenario testing")
    print("  • Can be used for optimization studies")