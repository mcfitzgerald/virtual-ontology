import requests
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# Get detailed data for our worst performers
bottlenecks = ['LINE2-PCK', 'LINE2-PAL', 'LINE1-FIL']

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for idx, equipment in enumerate(bottlenecks):
    # Query data for this equipment
    params = {
        'equipment_id': equipment,
        'limit': 10000
    }
    response = requests.get("http://localhost:8000/data", params=params)
    data = response.json()
    
    # Count downtime reasons
    downtime_counts = defaultdict(int)
    total_downtime_records = 0
    
    # The response has 'items' key containing the records
    records = data['items'] if 'items' in data else data
    
    for record in records:
        if record.get('downtime_reason') and record['downtime_reason'] != 'None':
            downtime_counts[record['downtime_reason']] += 1
            total_downtime_records += 1
    
    # Sort and get top reasons
    sorted_reasons = sorted(downtime_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    
    if sorted_reasons:
        reasons = [r[0] for r in sorted_reasons]
        counts = [r[1] for r in sorted_reasons]
        percentages = [c/total_downtime_records * 100 for c in counts]
        
        # Create bar chart
        ax = axes[idx]
        bars = ax.barh(reasons, percentages)
        
        # Color code by type
        for i, (reason, bar) in enumerate(zip(reasons, bars)):
            if 'Jam' in reason or 'Failure' in reason:
                bar.set_color('red')
            elif 'Changeover' in reason:
                bar.set_color('orange')
            elif 'Cleaning' in reason or 'Maintenance' in reason:
                bar.set_color('yellow')
            else:
                bar.set_color('gray')
        
        # Add value labels
        for i, (v, c) in enumerate(zip(percentages, counts)):
            ax.text(v + 0.5, i, f'{v:.1f}% ({c})', va='center')
        
        ax.set_xlabel('% of Downtime Events')
        ax.set_title(f'{equipment} - Top Downtime Reasons')
        ax.set_xlim(0, max(percentages) * 1.2)
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('bottleneck_downtime_reasons.png', dpi=300)
plt.show()

# Now let's calculate the financial impact
print("\n=== FINANCIAL IMPACT ANALYSIS ===\n")

# Get sample data to understand pricing
sample_response = requests.get("http://localhost:8000/data", params={'limit': 100})
sample_data = sample_response.json()['items']

# Calculate average prices from the data
sale_prices = [r['sale_price_per_unit'] for r in sample_data if r['sale_price_per_unit']]
standard_costs = [r['standard_cost_per_unit'] for r in sample_data if r['standard_cost_per_unit']]

avg_sale_price = sum(sale_prices) / len(sale_prices)
avg_standard_cost = sum(standard_costs) / len(standard_costs)
avg_margin = avg_sale_price - avg_standard_cost

print(f"Average Sale Price: ${avg_sale_price:.2f}")
print(f"Average Standard Cost: ${avg_standard_cost:.2f}")
print(f"Average Margin: ${avg_margin:.2f}")

# Calculate opportunity for each bottleneck
print("\n=== BOTTLENECK IMPROVEMENT OPPORTUNITIES ===\n")

for equipment in bottlenecks:
    # Get equipment data
    equipment_response = requests.get("http://localhost:8000/kpis/by-equipment")
    equipment_kpis = equipment_response.json()
    
    equip_data = next(e for e in equipment_kpis if e['equipment_id'] == equipment)
    
    # Estimate production capacity improvement
    current_oee = equip_data['avg_oee_score']
    target_oee = 85  # World-class
    oee_improvement = (target_oee - current_oee) / 100
    
    # Assuming 100 units/hour at 100% OEE (adjust based on your actual rates)
    base_rate = 100
    current_rate = base_rate * (current_oee / 100)
    improved_rate = base_rate * (target_oee / 100)
    additional_units_per_hour = improved_rate - current_rate
    
    # Calculate annual impact (24/7 operation minus 10% for maintenance)
    hours_per_year = 365 * 24 * 0.9
    annual_additional_units = additional_units_per_hour * hours_per_year
    annual_revenue_opportunity = annual_additional_units * avg_margin
    
    print(f"\n{equipment}:")
    print(f"  Current OEE: {current_oee:.1f}%")
    print(f"  OEE Gap: {target_oee - current_oee:.1f}%")
    print(f"  Additional Units/Hour: {additional_units_per_hour:.1f}")
    print(f"  Annual Revenue Opportunity: ${annual_revenue_opportunity:,.0f}")
    
    # Show top improvement areas
    if equipment == 'LINE2-PCK':
        print("  Top Fix: Reduce Equipment Jams (35% of downtime)")
        print("  Quick Win: Implement predictive jam detection")
    elif equipment == 'LINE2-PAL':
        print("  Top Fix: Address Minor Stoppages and Jams")
        print("  Quick Win: Operator training on jam clearing")
    elif equipment == 'LINE1-FIL':
        print("  Top Fix: Improve sensor calibration (micro-stops)")
        print("  Quick Win: Daily sensor calibration routine")