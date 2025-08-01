import json
import matplotlib.pyplot as plt
import numpy as np
import requests

# Get equipment KPIs
response = requests.get("http://localhost:8000/kpis/by-equipment")
equipment_data = response.json()

# Sort by OEE to identify bottlenecks
equipment_data.sort(key=lambda x: x['avg_oee_score'])

# Extract data for visualization
equipment_ids = [e['equipment_id'] for e in equipment_data]
oee_scores = [e['avg_oee_score'] for e in equipment_data]
availability = [e['avg_availability_score'] for e in equipment_data]
performance = [e['avg_performance_score'] for e in equipment_data]
quality = [e['avg_quality_score'] for e in equipment_data]

# Create figure with subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Subplot 1: OEE Scores with World-Class Benchmark
x = np.arange(len(equipment_ids))
bars = ax1.bar(x, oee_scores, color='steelblue', alpha=0.8)
ax1.axhline(y=85, color='green', linestyle='--', label='World-Class OEE (85%)')
ax1.axhline(y=45.99, color='red', linestyle='--', label='Plant Average (45.99%)')

# Color code bars based on performance
for i, bar in enumerate(bars):
    if oee_scores[i] < 40:
        bar.set_color('red')
    elif oee_scores[i] < 50:
        bar.set_color('orange')
    else:
        bar.set_color('green')

ax1.set_ylabel('OEE Score (%)')
ax1.set_title('Equipment OEE Bottleneck Analysis - Sorted by OEE Score')
ax1.set_xticks(x)
ax1.set_xticklabels(equipment_ids, rotation=45)
ax1.legend()
ax1.grid(True, alpha=0.3)

# Add value labels on bars
for i, v in enumerate(oee_scores):
    ax1.text(i, v + 1, f'{v:.1f}%', ha='center', va='bottom', fontsize=9)

# Subplot 2: OEE Components Breakdown
width = 0.25
x2 = np.arange(len(equipment_ids))

ax2.bar(x2 - width, availability, width, label='Availability', color='skyblue')
ax2.bar(x2, performance, width, label='Performance', color='lightgreen')
ax2.bar(x2 + width, quality, width, label='Quality', color='salmon')

ax2.set_ylabel('Score (%)')
ax2.set_title('OEE Component Breakdown by Equipment')
ax2.set_xticks(x2)
ax2.set_xticklabels(equipment_ids, rotation=45)
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('equipment_bottleneck_analysis.png', dpi=300)
plt.show()

# Print bottleneck summary
print("\n=== EQUIPMENT BOTTLENECK ANALYSIS ===\n")
print("Top 3 Bottlenecks (Lowest OEE):")
for i in range(3):
    e = equipment_data[i]
    oee_gap = 85 - e['avg_oee_score']
    print(f"\n{i+1}. {e['equipment_id']} ({e['equipment_type']})")
    print(f"   OEE: {e['avg_oee_score']:.1f}% (Gap to World-Class: {oee_gap:.1f}%)")
    print(f"   Availability: {e['avg_availability_score']:.1f}%")
    print(f"   Performance: {e['avg_performance_score']:.1f}%")
    print(f"   Quality: {e['avg_quality_score']:.1f}%")
    
    # Identify biggest component issue
    components = {
        'Availability': e['avg_availability_score'],
        'Performance': e['avg_performance_score'],
        'Quality': e['avg_quality_score']
    }
    worst_component = min(components.items(), key=lambda x: x[1])
    print(f"   PRIMARY ISSUE: {worst_component[0]} ({worst_component[1]:.1f}%)")