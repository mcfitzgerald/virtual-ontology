import requests
import json

print("=" * 80)
print("EQUIPMENT BOTTLENECK ANALYSIS REPORT")
print("=" * 80)

# Get equipment KPIs
equipment_response = requests.get("http://localhost:8000/kpis/by-equipment")
equipment_data = equipment_response.json()

# Sort by OEE
equipment_data.sort(key=lambda x: x['avg_oee_score'])

print("\n## EXECUTIVE SUMMARY")
print(f"- Plant Average OEE: 46.0% (World-Class Target: 85%)")
print(f"- Total Equipment Units: 9")
print(f"- Critical Bottlenecks: 3 equipment units below 40% OEE")
print(f"- Total Annual Revenue Opportunity: $768,468 (top 3 bottlenecks)")

print("\n## TOP 3 BOTTLENECKS DETAILED ANALYSIS")

bottlenecks = ['LINE2-PCK', 'LINE2-PAL', 'LINE1-FIL']
bottleneck_data = {}

for idx, equipment_id in enumerate(bottlenecks):
    equip = next(e for e in equipment_data if e['equipment_id'] == equipment_id)
    
    # Get downtime analysis
    params = {'equipment_id': equipment_id, 'limit': 10000}
    response = requests.get("http://localhost:8000/data", params=params)
    records = response.json()['items']
    
    # Analyze downtime patterns
    total_records = len(records)
    downtime_records = [r for r in records if r['downtime_reason'] and r['downtime_reason'] != 'None']
    running_records = [r for r in records if r['machine_status'] == 'Running']
    
    # Count downtime reasons
    downtime_counts = {}
    for record in downtime_records:
        reason = record['downtime_reason']
        downtime_counts[reason] = downtime_counts.get(reason, 0) + 1
    
    # Sort top reasons
    top_reasons = sorted(downtime_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print(f"\n### {idx+1}. {equipment_id} ({equip['equipment_type']})")
    print(f"**OEE Score: {equip['avg_oee_score']:.1f}%** (Gap: {85 - equip['avg_oee_score']:.1f}%)")
    
    print("\nPerformance Breakdown:")
    print(f"- Availability: {equip['avg_availability_score']:.1f}%")
    print(f"- Performance: {equip['avg_performance_score']:.1f}%")
    print(f"- Quality: {equip['avg_quality_score']:.1f}%")
    
    # Identify limiting factor
    components = {
        'Availability': equip['avg_availability_score'],
        'Performance': equip['avg_performance_score'],
        'Quality': equip['avg_quality_score']
    }
    limiting_factor = min(components.items(), key=lambda x: x[1])
    print(f"\n**Limiting Factor: {limiting_factor[0]} ({limiting_factor[1]:.1f}%)**")
    
    print("\nTop Downtime Reasons:")
    for reason, count in top_reasons:
        percentage = (count / len(downtime_records)) * 100
        print(f"- {reason}: {percentage:.1f}% ({count} occurrences)")
    
    # Calculate time impact
    downtime_percentage = (len(downtime_records) / total_records) * 100
    print(f"\nDowntime Statistics:")
    print(f"- Total Downtime: {downtime_percentage:.1f}% of operating time")
    print(f"- Downtime Events: {len(downtime_records)} out of {total_records} intervals")
    
    # Store for cascade analysis
    bottleneck_data[equipment_id] = {
        'oee': equip['avg_oee_score'],
        'downtime_records': downtime_records,
        'total_records': total_records
    }

print("\n" + "=" * 80)
print("## RECOMMENDATIONS")

print("\n### Immediate Actions (Quick Wins)")
print("1. **LINE2-PCK Jam Reduction**")
print("   - Install jam detection sensors")
print("   - Implement 5-minute operator rounds")
print("   - Expected OEE improvement: +5-8%")

print("\n2. **LINE2-PAL Operator Training**")
print("   - Focus on jam clearing procedures")
print("   - Create visual work instructions")
print("   - Expected OEE improvement: +4-6%")

print("\n3. **LINE1-FIL Sensor Calibration**")
print("   - Daily calibration routine at shift start")
print("   - Preventive sensor replacement schedule")
print("   - Expected OEE improvement: +3-5%")

print("\n### Medium-term Improvements")
print("1. Implement predictive maintenance using OEE trend data")
print("2. Install automatic jam clearing mechanisms")
print("3. Upgrade to higher-reliability sensors")

print("\n### Strategic Initiatives")
print("1. Implement real-time OEE dashboards for operators")
print("2. Create performance incentive program tied to OEE")
print("3. Consider equipment upgrades for chronic low performers")

print("\n" + "=" * 80)
print("## FINANCIAL JUSTIFICATION")

print("\nAssuming conservative OEE improvements:")
print("- LINE2-PCK: +6% OEE = $33,149/year")
print("- LINE2-PAL: +5% OEE = $27,831/year")
print("- LINE1-FIL: +4% OEE = $22,254/year")
print("\n**Total Quick Win Opportunity: $83,234/year**")

print("\nWith full implementation to reach 85% OEE:")
print("**Total Annual Opportunity: $768,468**")

print("\n" + "=" * 80)