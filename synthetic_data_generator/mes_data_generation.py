#!/usr/bin/env python3
"""
Enhanced MES Data Generation Script with Full Configuration Support
Generates manufacturing data with realistic OEE values based on configuration
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict

def load_config(config_file='mes_data_config.json'):
    """Load configuration from JSON file."""
    config_path = os.path.join(os.path.dirname(__file__), config_file)
    with open(config_path, 'r') as f:
        return json.load(f)

def get_product_master(config):
    """Returns a DataFrame of product master data from configuration."""
    products = []
    for product_id, product_info in config['product_master'].items():
        products.append({
            "ProductID": product_id,
            "ProductName": product_info['name'],
            "TargetRate_units_per_5min": product_info['target_rate_units_per_5min'],
            "StandardCost_per_unit": product_info['standard_cost_per_unit'],
            "SalePrice_per_unit": product_info['sale_price_per_unit'],
            "NormalScrapRate": product_info.get('normal_scrap_rate', 
                                               config['product_specifications']['normal_scrap_rate'])
        })
    return pd.DataFrame(products)

def get_equipment_master(config):
    """Returns a DataFrame of equipment master data from configuration."""
    equipment = []
    for line_id, line_info in config['equipment_configuration']['lines'].items():
        line_num = int(line_id.replace('LINE', ''))
        for eq_info in line_info['equipment_sequence']:
            equipment.append({
                "EquipmentID": eq_info['id'],
                "EquipmentName": f"{eq_info['type']} {line_info['name']}",
                "LineID": line_num,
                "EquipmentType": eq_info['type']
            })
    return pd.DataFrame(equipment)

def get_downtime_reasons(config):
    """Returns a map of downtime reason codes and descriptions from configuration."""
    return {code: info['description'] 
            for code, info in config['downtime_reason_mapping'].items()}

def generate_production_orders(products_df, start_date, end_date, config):
    """Generates a list of production orders for each line using configuration."""
    orders = []
    order_id_counter = 1000
    schedule_config = config['production_schedule']
    
    # Get number of lines from config
    num_lines = len(config['equipment_configuration']['lines'])
    
    for line in range(1, num_lines + 1):
        current_time = start_date
        while current_time < end_date:
            product = products_df.sample(1).iloc[0]
            
            # Use configured run duration range
            run_duration_hours = random.uniform(
                schedule_config['run_duration_hours']['min'],
                schedule_config['run_duration_hours']['max']
            )
            end_time = current_time + timedelta(hours=run_duration_hours)
            if end_time > end_date:
                end_time = end_date
            
            orders.append({
                "ProductionOrderID": f"ORD-{order_id_counter}",
                "LineID": line,
                "ProductID": product["ProductID"],
                "StartTime": current_time,
                "EndTime": end_time,
            })
            order_id_counter += 1
            
            # Use configured changeover gap
            gap_minutes = random.randint(
                schedule_config['changeover_gap_minutes']['min'],
                schedule_config['changeover_gap_minutes']['max']
            )
            current_time = end_time + timedelta(minutes=gap_minutes)
    
    return pd.DataFrame(orders)

def get_shift_number(current_time):
    """Determine shift number based on time (1: 6am-2pm, 2: 2pm-10pm, 3: 10pm-6am)"""
    hour = current_time.hour
    if 6 <= hour < 14:
        return 1
    elif 14 <= hour < 22:
        return 2
    else:
        return 3

def apply_anomalies(equip_id, current_time, order_info, config, changeover_start_times, 
                   performance_drop_tracker, last_cleaning_times):
    """Apply configured anomalies to determine equipment status and production rates."""
    anomaly_config = config['anomaly_injection']
    product_config = config['product_master'].get(order_info['ProductID'], {})
    
    # Check scheduled maintenance
    if anomaly_config.get('scheduled_maintenance', {}).get('enabled', False):
        for pattern in anomaly_config['scheduled_maintenance'].get('patterns', []):
            if (equip_id == pattern['equipment_id'] and 
                current_time.weekday() == pattern['day_of_week'] and
                current_time.hour == pattern['hour'] and
                current_time.minute < pattern['duration_minutes']):
                return "Stopped", pattern['downtime_reason'], 0, 0, current_time + timedelta(minutes=pattern['duration_minutes'])
    
    # Check cleaning cycles
    if anomaly_config.get('cleaning_cycles', {}).get('enabled', False):
        cleaning = anomaly_config['cleaning_cycles']
        if equip_id not in last_cleaning_times:
            last_cleaning_times[equip_id] = current_time
        
        hours_since_cleaning = (current_time - last_cleaning_times[equip_id]).total_seconds() / 3600
        if hours_since_cleaning >= cleaning['frequency_hours']:
            last_cleaning_times[equip_id] = current_time
            return "Stopped", cleaning['downtime_reason'], 0, 0, current_time + timedelta(minutes=cleaning['duration_minutes'])
    
    # Check major mechanical failure
    if anomaly_config.get('major_mechanical_failure', {}).get('enabled', False):
        failure = anomaly_config['major_mechanical_failure']
        start_dt = datetime.strptime(failure['start_datetime'], '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(failure['end_datetime'], '%Y-%m-%d %H:%M:%S')
        
        if equip_id == failure['equipment_id'] and start_dt <= current_time <= end_dt:
            return "Stopped", failure['downtime_reason'], 0, 0, end_dt
    
    # Check frequent micro-stops
    if anomaly_config.get('frequent_micro_stops', {}).get('enabled', False):
        micro_stops = anomaly_config['frequent_micro_stops']
        if equip_id == micro_stops['equipment_id']:
            if random.random() < micro_stops['probability_per_5min']:
                duration = random.uniform(
                    micro_stops['duration_range_minutes']['min'],
                    micro_stops['duration_range_minutes']['max']
                )
                downtime_end = current_time + timedelta(minutes=duration)
                return "Stopped", micro_stops['downtime_reason'], 0, 0, downtime_end
    
    # Check additional anomaly patterns
    for anomaly_key in ['minor_stops_line1', 'recurring_jams_line1', 'electrical_issues', 
                       'quality_control_stops']:
        if anomaly_config.get(anomaly_key, {}).get('enabled', False):
            anomaly = anomaly_config[anomaly_key]
            if equip_id == anomaly['equipment_id']:
                if random.random() < anomaly['probability_per_5min']:
                    duration = random.uniform(
                        anomaly['duration_range_minutes']['min'],
                        anomaly['duration_range_minutes']['max']
                    )
                    downtime_end = current_time + timedelta(minutes=duration)
                    return "Stopped", anomaly['downtime_reason'], 0, 0, downtime_end
    
    # Check operator issues (night shift)
    if anomaly_config.get('operator_issues_shift3', {}).get('enabled', False):
        opr = anomaly_config['operator_issues_shift3']
        if equip_id == opr['equipment_id']:
            hour = current_time.hour
            hour_range = opr['hour_range']
            if hour >= hour_range[0] or hour < hour_range[1]:
                if random.random() < opr['probability_per_5min']:
                    duration = random.uniform(
                        opr['duration_range_minutes']['min'],
                        opr['duration_range_minutes']['max']
                    )
                    downtime_end = current_time + timedelta(minutes=duration)
                    return "Stopped", opr['downtime_reason'], 0, 0, downtime_end
    
    # Check material starvation patterns
    if anomaly_config.get('material_starvation_patterns', {}).get('enabled', False):
        for pattern in anomaly_config['material_starvation_patterns'].get('equipment_patterns', []):
            if equip_id == pattern['equipment_id']:
                hour = current_time.hour
                hour_range = pattern['hour_range']
                if hour_range[0] <= hour < hour_range[1]:
                    if random.random() < pattern['probability_per_5min']:
                        duration = random.uniform(
                            pattern['duration_range_minutes']['min'],
                            pattern['duration_range_minutes']['max']
                        )
                        downtime_end = current_time + timedelta(minutes=duration)
                        return "Stopped", pattern['downtime_reason'], 0, 0, downtime_end
    
    # Check random sensor issues
    if anomaly_config.get('random_sensor_issues', {}).get('enabled', False):
        for pattern in anomaly_config['random_sensor_issues'].get('equipment_patterns', []):
            if equip_id == pattern['equipment_id']:
                if random.random() < pattern['probability_per_5min']:
                    duration = random.uniform(
                        pattern['duration_range_minutes']['min'],
                        pattern['duration_range_minutes']['max']
                    )
                    downtime_end = current_time + timedelta(minutes=duration)
                    return "Stopped", pattern['downtime_reason'], 0, 0, downtime_end
    
    # Check filler micro stops
    if anomaly_config.get('filler_micro_stops', {}).get('enabled', False):
        for pattern in anomaly_config['filler_micro_stops'].get('equipment_patterns', []):
            if equip_id == pattern['equipment_id']:
                if random.random() < pattern['probability_per_5min']:
                    duration = random.uniform(
                        pattern['duration_range_minutes']['min'],
                        pattern['duration_range_minutes']['max']
                    )
                    downtime_end = current_time + timedelta(minutes=duration)
                    return "Stopped", pattern['downtime_reason'], 0, 0, downtime_end
    
    # Check palletizer micro stops
    if anomaly_config.get('palletizer_micro_stops', {}).get('enabled', False):
        for pattern in anomaly_config['palletizer_micro_stops'].get('equipment_patterns', []):
            if equip_id == pattern['equipment_id']:
                if random.random() < pattern['probability_per_5min']:
                    duration = random.uniform(
                        pattern['duration_range_minutes']['min'],
                        pattern['duration_range_minutes']['max']
                    )
                    downtime_end = current_time + timedelta(minutes=duration)
                    return "Stopped", pattern['downtime_reason'], 0, 0, downtime_end
    
    # If running, calculate production
    target_rate = order_info['TargetRate_units_per_5min']
    actual_rate = target_rate
    
    # Apply shift-based performance variation
    shift = get_shift_number(current_time)
    shift_key = f"shift{shift}"
    if shift_key in config['product_specifications'].get('performance_variation', {}):
        shift_range = config['product_specifications']['performance_variation'][shift_key]
        actual_rate *= random.uniform(shift_range['min'], shift_range['max'])
    
    # Check performance bottleneck
    if (anomaly_config.get('performance_bottleneck', {}).get('enabled', False) and 
        'performance_issue_lines' in product_config):
        line_id = f"LINE{order_info['LineID']}"
        if line_id in product_config['performance_issue_lines']:
            perf_range = product_config['performance_degradation']
            actual_rate *= random.uniform(perf_range['min'], perf_range['max'])
    
    # Check random performance drops
    perf_drops = config['product_specifications'].get('random_performance_drops', {})
    if perf_drops.get('enabled', False):
        if equip_id in performance_drop_tracker:
            # Currently in a performance drop
            if performance_drop_tracker[equip_id]['end_interval'] > 0:
                actual_rate *= performance_drop_tracker[equip_id]['factor']
                performance_drop_tracker[equip_id]['end_interval'] -= 1
            else:
                del performance_drop_tracker[equip_id]
        elif random.random() < perf_drops['probability_per_5min']:
            # Start a new performance drop
            duration = random.randint(
                perf_drops['duration_intervals']['min'],
                perf_drops['duration_intervals']['max']
            )
            factor = random.uniform(
                perf_drops['degradation_factor']['min'],
                perf_drops['degradation_factor']['max']
            )
            performance_drop_tracker[equip_id] = {
                'end_interval': duration,
                'factor': factor
            }
            actual_rate *= factor
    
    # Add normal variation based on equipment type
    equip_type = equip_id.split('-')[1]
    type_map = {'FIL': 'Filler', 'PCK': 'Packer', 'PAL': 'Palletizer'}
    equip_type_name = type_map.get(equip_type, 'Equipment')
    
    if equip_type_name in config['product_specifications']['equipment_efficiency']:
        eff_range = config['product_specifications']['equipment_efficiency'][equip_type_name]
        actual_rate *= random.uniform(eff_range['min'], eff_range['max'])
    
    # Calculate good and scrap units
    good_units = int(actual_rate)
    
    # Determine scrap rate
    scrap_rate = product_config.get('normal_scrap_rate', 
                                   config['product_specifications']['normal_scrap_rate'])
    
    # Check if in startup period (first 30 minutes after changeover)
    for co_time in changeover_start_times:
        if current_time >= co_time and current_time < co_time + timedelta(minutes=30):
            scrap_rate = product_config.get('startup_scrap_rate', scrap_rate * 2)
            break
    
    # Check quality issues
    if (anomaly_config.get('quality_issues', {}).get('enabled', False) and 
        'quality_issue_scrap_rate' in product_config):
        scrap_rate = product_config['quality_issue_scrap_rate']
    
    # Check changeover scrap spike
    if anomaly_config.get('changeover_scrap_spike', {}).get('enabled', False):
        for co_time in changeover_start_times:
            if (current_time >= co_time and 
                current_time < co_time + timedelta(minutes=anomaly_config['changeover_scrap_spike']['duration_minutes'])):
                scrap_rate *= anomaly_config['changeover_scrap_spike']['scrap_multiplier']
                break
    
    # Check quality variation during normal production
    if anomaly_config.get('quality_variation_normal', {}).get('enabled', False):
        if random.random() < anomaly_config['quality_variation_normal']['probability_per_5min']:
            scrap_rate *= anomaly_config['quality_variation_normal']['scrap_rate_multiplier']
    
    # Check quality degradation at end of run
    if anomaly_config.get('quality_end_of_run', {}).get('enabled', False):
        # Find next changeover time for this line
        hours_before = anomaly_config['quality_end_of_run']['hours_before_changeover']
        for co_time in changeover_start_times:
            if co_time > current_time:  # This is the next changeover
                time_until_changeover = (co_time - current_time).total_seconds() / 3600
                if time_until_changeover <= hours_before:
                    scrap_rate *= anomaly_config['quality_end_of_run']['scrap_rate_multiplier']
                break
    
    scrap_units = int(good_units * scrap_rate / (1 - scrap_rate))
    
    return "Running", None, good_units, scrap_units, None

def calculate_kpis(status, good_units, scrap_units, target_rate):
    """Calculate instantaneous KPIs for 5-minute intervals."""
    # Availability: 1 if running, 0 if stopped
    availability = 1.0 if status == "Running" else 0.0
    
    # Performance: actual rate / target rate (only when running)
    if status == "Running" and target_rate > 0:
        total_produced = good_units + scrap_units
        performance = min(total_produced / target_rate, 1.0)  # Cap at 100%
    else:
        performance = 0.0
    
    # Quality: good units / total units (only when producing)
    total_units = good_units + scrap_units
    if total_units > 0:
        quality = good_units / total_units
    else:
        quality = 1.0 if status == "Running" else 0.0
    
    # OEE: Product of all three
    oee = availability * performance * quality
    
    return {
        'Availability_Score': round(availability * 100, 1),
        'Performance_Score': round(performance * 100, 1),
        'Quality_Score': round(quality * 100, 1),
        'OEE_Score': round(oee * 100, 1)
    }


def generate_mes_data(start_date, end_date, config):
    """Main function to generate the complete MES dataset with inline KPIs."""
    
    print("Loading master data from configuration...")
    products_df = get_product_master(config)
    equipment_df = get_equipment_master(config)
    downtime_reasons = get_downtime_reasons(config)
    
    print("Generating production schedule...")
    orders_df = generate_production_orders(products_df, start_date, end_date, config)
    
    # Merge master data
    master_df = pd.merge(equipment_df, orders_df, on="LineID")
    master_df = pd.merge(master_df, products_df, on="ProductID")
    
    # Track changeover times for scrap spike anomaly
    changeover_start_times = []
    prev_order_by_line = {}
    
    for _, order in orders_df.iterrows():
        line_id = order['LineID']
        if line_id in prev_order_by_line:
            # This is a changeover
            changeover_start_times.append(order['StartTime'])
        prev_order_by_line[line_id] = order['ProductionOrderID']
    
    all_logs = []
    current_time = start_date
    downtime_tracker = {}  # Tracks ongoing downtimes
    performance_drop_tracker = {}  # Tracks performance drops
    last_cleaning_times = {}  # Tracks last cleaning time per equipment
    cascade_tracker = {}  # Tracks cascade failures from upstream equipment
    
    print("Starting data generation loop...")
    total_intervals = int((end_date - start_date).total_seconds() / 60 / 5)
    intervals_processed = 0
    
    while current_time <= end_date:
        intervals_processed += 1
        if intervals_processed % 200 == 0:
            progress = (intervals_processed / total_intervals) * 100
            print(f"  Progress: {progress:.1f}% ({intervals_processed}/{total_intervals} 5-min intervals)")
        
        # Process each piece of equipment
        for _, equip in equipment_df.iterrows():
            equip_id = equip["EquipmentID"]
            
            # Find active order
            active_order = master_df[
                (master_df["LineID"] == equip["LineID"]) &
                (master_df["StartTime"] <= current_time) &
                (master_df["EndTime"] > current_time)
            ]
            
            if active_order.empty:
                # Equipment is idle during changeover
                log_entry = {
                    "Timestamp": current_time,
                    "ProductionOrderID": None,
                    "LineID": equip["LineID"],
                    "EquipmentID": equip_id,
                    "EquipmentType": equip["EquipmentType"],
                    "ProductID": None,
                    "ProductName": None,
                    "MachineStatus": "Stopped",
                    "DowntimeReason": "PLN-CO",
                    "GoodUnitsProduced": 0,
                    "ScrapUnitsProduced": 0,
                    "TargetRate_units_per_5min": 0,
                    "StandardCost_per_unit": 0,
                    "SalePrice_per_unit": 0,
                    "Availability_Score": 0.0,
                    "Performance_Score": 0.0,
                    "Quality_Score": 0.0,
                    "OEE_Score": 0.0
                }
                all_logs.append(log_entry)
                continue
            
            order_info = active_order.iloc[0]
            
            # Check ongoing downtime
            if equip_id in downtime_tracker and downtime_tracker[equip_id]["end"] > current_time:
                status = "Stopped"
                reason = downtime_tracker[equip_id]["reason"]
                good_units, scrap_units = 0, 0
            else:
                if equip_id in downtime_tracker:
                    del downtime_tracker[equip_id]
                
                # Apply anomalies and get status
                status, reason, good_units, scrap_units, downtime_end = apply_anomalies(
                    equip_id, current_time, order_info, config, changeover_start_times,
                    performance_drop_tracker, last_cleaning_times
                )
                
                if downtime_end:
                    downtime_tracker[equip_id] = {"end": downtime_end, "reason": reason}
            
            # Check cascade failures (downstream equipment starves when upstream stops)
            if config.get('anomaly_injection', {}).get('cascade_failures', {}).get('enabled', False):
                cascade_config = config['anomaly_injection']['cascade_failures']
                
                # Check if this is a trigger equipment (upstream) that just stopped
                if equip_id in cascade_config['trigger_equipment'] and status == "Stopped":
                    # Mark cascade start time for downstream equipment on same line
                    line_id = equip["LineID"]
                    cascade_key = f"LINE{line_id}"
                    if cascade_key not in cascade_tracker:
                        cascade_tracker[cascade_key] = current_time
                
                # Check if this is a trigger equipment that just restarted
                elif equip_id in cascade_config['trigger_equipment'] and status == "Running":
                    # Clear cascade for this line
                    line_id = equip["LineID"]
                    cascade_key = f"LINE{line_id}"
                    if cascade_key in cascade_tracker:
                        del cascade_tracker[cascade_key]
                
                # Check if this is downstream equipment that should be starved
                elif equip_id not in cascade_config['trigger_equipment'] and status == "Running":
                    line_id = equip["LineID"]
                    cascade_key = f"LINE{line_id}"
                    if cascade_key in cascade_tracker:
                        # Check if enough time has passed for cascade
                        time_since_upstream_stop = (current_time - cascade_tracker[cascade_key]).total_seconds() / 60
                        if time_since_upstream_stop >= cascade_config['cascade_delay_minutes']:
                            # Apply cascade failure with probability
                            if random.random() < cascade_config['downstream_stop_probability']:
                                status = "Stopped"
                                reason = "UNP-MAT"  # Material starvation
                                good_units, scrap_units = 0, 0
            
            # Calculate instantaneous KPIs
            kpis = calculate_kpis(status, good_units, scrap_units, order_info["TargetRate_units_per_5min"])
            
            # Create log entry
            log_entry = {
                "Timestamp": current_time,
                "ProductionOrderID": order_info["ProductionOrderID"],
                "LineID": order_info["LineID"],
                "EquipmentID": equip_id,
                "EquipmentType": equip["EquipmentType"],
                "ProductID": order_info["ProductID"],
                "ProductName": order_info["ProductName"],
                "MachineStatus": status,
                "DowntimeReason": reason,
                "GoodUnitsProduced": good_units,
                "ScrapUnitsProduced": scrap_units,
                "TargetRate_units_per_5min": order_info["TargetRate_units_per_5min"],
                "StandardCost_per_unit": order_info["StandardCost_per_unit"],
                "SalePrice_per_unit": order_info["SalePrice_per_unit"],
                # Instantaneous KPIs
                "Availability_Score": kpis['Availability_Score'],
                "Performance_Score": kpis['Performance_Score'],
                "Quality_Score": kpis['Quality_Score'],
                "OEE_Score": kpis['OEE_Score']
            }
            all_logs.append(log_entry)
        
        current_time += timedelta(minutes=5)
    
    print(f"Generated {len(all_logs)} log entries")
    return pd.DataFrame(all_logs)

def main():
    """Main execution function."""
    # Load configuration
    config = load_config()
    
    # Define time period
    start_date = datetime(2025, 6, 1, 0, 0)
    end_date = datetime(2025, 6, 14, 23, 59)
    
    print(f"MES Data Generation using {config['ontology']['name']} v{config['ontology']['version']}")
    print(f"Period: {start_date} to {end_date}")
    print("-" * 60)
    
    # Generate data
    mes_data = generate_mes_data(start_date, end_date, config)
    
    # Save to CSV in the Data directory
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "mes_data_with_kpis.csv")
    mes_data.to_csv(output_file, index=False)
    print(f"\nData saved to {output_file}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"  Total records: {len(mes_data):,}")
    print(f"  Lines: {mes_data['LineID'].nunique()}")
    print(f"  Equipment: {mes_data['EquipmentID'].nunique()}")
    print(f"  Products: {mes_data['ProductID'].nunique()}")
    print(f"  Production Orders: {mes_data['ProductionOrderID'].nunique()}")
    
    # KPI Summary
    print("\nKPI Summary (Overall Averages):")
    print(f"  Availability: {mes_data['Availability_Score'].mean():.1f}%")
    print(f"  Performance: {mes_data['Performance_Score'].mean():.1f}%")
    print(f"  Quality: {mes_data['Quality_Score'].mean():.1f}%")
    print(f"  OEE: {mes_data['OEE_Score'].mean():.1f}%")
    
    # OEE Distribution
    print("\nOEE Distribution:")
    print(f"  OEE >= 85% (World Class): {len(mes_data[mes_data['OEE_Score'] >= 85])/len(mes_data)*100:.1f}%")
    print(f"  OEE 65-85% (Good): {len(mes_data[(mes_data['OEE_Score'] >= 65) & (mes_data['OEE_Score'] < 85)])/len(mes_data)*100:.1f}%")
    print(f"  OEE 50-65% (Fair): {len(mes_data[(mes_data['OEE_Score'] >= 50) & (mes_data['OEE_Score'] < 65)])/len(mes_data)*100:.1f}%")
    print(f"  OEE < 50% (Poor): {len(mes_data[mes_data['OEE_Score'] < 50])/len(mes_data)*100:.1f}%")
    
    # Downtime summary
    downtime_records = mes_data[mes_data['MachineStatus'] != 'Running']
    if len(downtime_records) > 0:
        print(f"\nDowntime Analysis:")
        print(f"  Total downtime events: {len(downtime_records):,}")
        print(f"  Downtime percentage: {len(downtime_records)/len(mes_data)*100:.1f}%")
        print("\n  Downtime by reason:")
        for reason, count in downtime_records['DowntimeReason'].value_counts().items():
            if reason:  # Skip None values
                desc = config['downtime_reason_mapping'].get(reason, {}).get('description', reason)
                print(f"    {reason}: {count:,} events - {desc}")
    
    # Shift performance analysis
    print("\nShift Performance Analysis:")
    for shift in [1, 2, 3]:
        shift_data = []
        for _, row in mes_data.iterrows():
            if pd.notna(row['Timestamp']):
                hour = pd.to_datetime(row['Timestamp']).hour
                if shift == 1 and 6 <= hour < 14:
                    shift_data.append(row)
                elif shift == 2 and 14 <= hour < 22:
                    shift_data.append(row)
                elif shift == 3 and (hour >= 22 or hour < 6):
                    shift_data.append(row)
        
        if shift_data:
            shift_df = pd.DataFrame(shift_data)
            print(f"  Shift {shift}: OEE {shift_df['OEE_Score'].mean():.1f}%")

if __name__ == "__main__":
    main()