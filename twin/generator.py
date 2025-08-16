"""
Virtual Twin Data Generator Module
Generates manufacturing data with realistic OEE values based on configuration
Part of the Virtual Twin system for both baseline and simulation data generation
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import json
import yaml
import os
from collections import defaultdict
from typing import Dict, Any, Optional
from pathlib import Path

def load_config(config_file: str = 'mes_data_config.json') -> Dict[str, Any]:
    """Load configuration from JSON or YAML file.
    
    Args:
        config_file: Path to configuration file (JSON or YAML)
        
    Returns:
        Configuration dictionary
    """
    # If config_file is an absolute path, use it directly
    if os.path.isabs(config_file):
        config_path = config_file
    else:
        # Otherwise, look for it relative to this script's directory
        config_path = os.path.join(os.path.dirname(__file__), config_file)
    
    # Check if file exists with exact name first
    if not os.path.exists(config_path):
        # Try YAML version if JSON doesn't exist
        if config_path.endswith('.json'):
            yaml_path = config_path.replace('.json', '.yaml')
            if os.path.exists(yaml_path):
                config_path = yaml_path
    
    # Detect file type and load accordingly
    if config_path.endswith(('.yaml', '.yml')):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            # Apply scaling factors if present
            config = apply_scaling_factors(config)
            return config
    else:
        with open(config_path, 'r') as f:
            return json.load(f)

def apply_scaling_factors(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply scaling parameters to baseline values if present.
    
    Args:
        config: Raw configuration dictionary
        
    Returns:
        Configuration with scaled values
    """
    if 'scaling_parameters' not in config or 'baseline_values' not in config:
        return config
    
    # Get current scaling factors (default to 1.0)
    scaling = config.get('scaling_parameters', {})
    baseline = config.get('baseline_values', {})
    
    # Create anomaly_injection section from baseline values
    if 'anomaly_injection' not in config:
        config['anomaly_injection'] = {}
    
    # Apply maintenance_effectiveness to micro-stops
    maintenance_factor = scaling.get('maintenance_effectiveness', {}).get('current', 
                                    scaling.get('maintenance_effectiveness', {}).get('default', 1.0))
    
    if 'micro_stops' in baseline:
        for stop_id, stop_data in baseline['micro_stops'].items():
            # Create injection pattern with scaled probability
            base_prob = stop_data['probability_per_5min']
            scaled_prob = base_prob * maintenance_factor
            
            # Extract equipment ID from stop ID (e.g., LINE2_PCK_jam -> LINE2-PCK)
            parts = stop_id.split('_')
            if len(parts) >= 2:
                equipment_id = f"{parts[0]}-{parts[1]}"
                
                config['anomaly_injection'][stop_id] = {
                    'enabled': True,
                    'equipment_id': equipment_id,
                    'probability_per_5min': scaled_prob,
                    'downtime_reason': stop_data['downtime_reason'],
                    'duration_range_minutes': stop_data['duration_range_minutes'],
                    'description': f"Scaled from baseline {base_prob:.2f} by factor {maintenance_factor:.2f}"
                }
    
    # Apply operational_excellence to equipment efficiency
    ops_factor = scaling.get('operational_excellence', {}).get('current',
                           scaling.get('operational_excellence', {}).get('default', 1.0))
    
    if 'equipment_efficiency' in baseline:
        if 'product_specifications' not in config:
            config['product_specifications'] = {}
        
        config['product_specifications']['equipment_efficiency'] = {}
        for equipment_type, efficiency in baseline['equipment_efficiency'].items():
            config['product_specifications']['equipment_efficiency'][equipment_type] = {
                'min': max(0.5, efficiency['min'] * ops_factor),
                'max': min(1.0, efficiency['max'] * ops_factor)
            }
    
    # Apply operational_excellence to shift performance
    if 'shift_performance' in baseline:
        config['product_specifications']['performance_variation'] = {}
        for shift, performance in baseline['shift_performance'].items():
            config['product_specifications']['performance_variation'][shift] = {
                'min': max(0.5, performance['min'] * ops_factor),
                'max': min(1.0, performance['max'] * ops_factor)
            }
    
    # Apply quality_control_effectiveness to scrap rates
    quality_factor = scaling.get('quality_control_effectiveness', {}).get('current',
                               scaling.get('quality_control_effectiveness', {}).get('default', 1.0))
    
    if 'scrap_rates' in baseline and 'product_master' in config:
        for sku, product_data in config['product_master'].items():
            if sku in baseline['scrap_rates'].get('normal', {}):
                product_data['normal_scrap_rate'] = baseline['scrap_rates']['normal'][sku] * quality_factor
            if sku in baseline['scrap_rates'].get('startup', {}):
                product_data['startup_scrap_rate'] = baseline['scrap_rates']['startup'][sku] * quality_factor
    
    # Apply supply_chain_reliability to material starvation
    supply_factor = scaling.get('supply_chain_reliability', {}).get('current',
                              scaling.get('supply_chain_reliability', {}).get('default', 1.0))
    
    if 'material_starvation' in baseline:
        patterns = []
        for location, pattern in baseline['material_starvation'].items():
            # Lower reliability = higher starvation probability
            starvation_multiplier = 2.0 - supply_factor  # 1.0 reliability = 1.0x, 0.5 reliability = 1.5x
            patterns.append({
                'equipment_id': location.replace('_', '-'),
                'hour_range': pattern['hour_range'],
                'probability_per_5min': pattern['probability_per_5min'] * starvation_multiplier,
                'downtime_reason': pattern['downtime_reason'],
                'duration_range_minutes': pattern['duration_range_minutes']
            })
        
        config['anomaly_injection']['material_starvation_patterns'] = {
            'enabled': True,
            'equipment_patterns': patterns,
            'description': f"Material starvation scaled by supply reliability {supply_factor:.2f}"
        }
    
    # Apply line_decoupling_factor to cascade sensitivity
    decoupling_factor = scaling.get('line_decoupling_factor', {}).get('current',
                                  scaling.get('line_decoupling_factor', {}).get('default', 1.0))
    
    if 'cascade_failures' in baseline:
        # Higher decoupling = lower cascade probability
        cascade_reduction = 1.0 / decoupling_factor if decoupling_factor > 0 else 1.0
        config['anomaly_injection']['cascade_failures'] = {
            'enabled': True,
            'downstream_stop_probability': baseline['cascade_failures']['downstream_stop_probability'] * cascade_reduction,
            'cascade_delay_minutes': baseline['cascade_failures']['cascade_delay_minutes'],
            'description': f"Cascade sensitivity scaled by decoupling factor {decoupling_factor:.2f}"
        }
    
    # Copy over other baseline sections that don't need scaling
    if 'performance_drops' in baseline:
        config['product_specifications']['random_performance_drops'] = baseline['performance_drops']
    
    return config

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
    
    # GENERIC PATTERN PROCESSOR - Handle ANY event type ending in '_patterns'
    # This allows new event types to be added without modifying generator code
    for config_key, config_value in anomaly_config.items():
        if config_key.endswith('_patterns') and isinstance(config_value, dict):
            # Skip already handled patterns
            if config_key in ['material_starvation_patterns', 'random_sensor_issues']:
                continue
                
            if config_value.get('enabled', False):
                for pattern in config_value.get('equipment_patterns', []):
                    if equip_id == pattern['equipment_id']:
                        # Check if this is time-restricted
                        if 'hour_range' in pattern:
                            hour = current_time.hour
                            hour_range = pattern['hour_range']
                            if not (hour_range[0] <= hour < hour_range[1]):
                                continue
                        
                        # Roll the dice for this event
                        if random.random() < pattern.get('probability_per_5min', 0):
                            duration = random.uniform(
                                pattern['duration_range_minutes']['min'],
                                pattern['duration_range_minutes']['max']
                            )
                            downtime_end = current_time + timedelta(minutes=duration)
                            return "Stopped", pattern.get('downtime_reason', 'Unknown'), 0, 0, downtime_end
    
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


def calculate_energy_consumption(status, equipment_type, product_id, performance_score, config, is_micro_stop=False):
    """
    Calculate energy consumption for 5-minute interval based on equipment status and performance.
    
    NOTE: This function is preserved for use by the virtual sensor layer.
    Energy is no longer stored as raw data in MES/simulation tables, but is instead
    derived as an observation by the PowerMeterSensor in virtual_sensors.py.
    
    Args:
        status: Machine status (Running/Stopped)
        equipment_type: Type of equipment (Filler/Packer/Palletizer)
        product_id: Product being produced
        performance_score: Performance percentage (0-100)
        config: Configuration dictionary with energy parameters
        is_micro_stop: Whether this is a micro-stop (uses surge power)
    
    Returns:
        Energy consumption in kWh for the 5-minute interval
    """
    energy_config = config.get('energy_consumption', {})
    base_consumption = energy_config.get('base_consumption_kw', {})
    
    # Get base consumption for equipment type
    equip_energy = base_consumption.get(equipment_type, {})
    if status == "Running":
        base_kw = equip_energy.get('running', 15.0)  # Default 15kW if not specified
    else:
        base_kw = equip_energy.get('idle', 1.5)  # Default 1.5kW idle
    
    # Apply performance impact (non-linear scaling)
    if status == "Running" and performance_score > 0:
        perf_factor = performance_score / 100.0
        scaling_factor = energy_config.get('performance_impact', {}).get('scaling_factor', 0.8)
        # Energy doesn't scale linearly with performance
        # Running at 50% speed might use 70% of energy
        energy_factor = 1.0 - (1.0 - perf_factor) * scaling_factor
        base_kw *= energy_factor
    
    # Apply product-specific factor
    product_factors = energy_config.get('product_specific_factors', {})
    if product_id and product_id in product_factors:
        product_multiplier = product_factors[product_id].get('energy_multiplier', 1.0)
        base_kw *= product_multiplier
    
    # Apply micro-stop penalty (startup surge)
    if is_micro_stop:
        micro_stop_config = energy_config.get('micro_stop_penalty', {})
        surge_multiplier = micro_stop_config.get('startup_surge_multiplier', 1.5)
        base_kw *= surge_multiplier
    
    # Convert to kWh for 5-minute interval (5/60 hours)
    energy_kwh = base_kw * (5.0 / 60.0)
    
    return round(energy_kwh, 3)


def save_to_csv(df, filename=None):
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        filename: Optional filename, defaults to timestamped name
    
    Returns:
        str: Path to saved CSV file
    """
    import os
    from datetime import datetime
    
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'mes_data_{timestamp}.csv'
    
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'exports')
    os.makedirs(data_dir, exist_ok=True)
    
    filepath = os.path.join(data_dir, filename)
    df.to_csv(filepath, index=False)
    
    return filepath

def save_to_database(df, table_name, run_id=None):
    """Save DataFrame to database table"""
    from sqlalchemy import create_engine
    import sys
    import os
    # Add parent directory to path to import api models
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api.models import MESData, SimulationData, TwinRun
    from sqlmodel import Session, SQLModel
    from datetime import datetime
    
    # Prepare dataframe for database
    df_db = df.copy()
    
    # Rename columns to match database schema
    column_mapping = {
        'Timestamp': 'timestamp',
        'ProductionOrderID': 'production_order_id',
        'LineID': 'line_id',
        'EquipmentID': 'equipment_id',
        'EquipmentType': 'equipment_type',
        'ProductID': 'product_id',
        'ProductName': 'product_name',
        'MachineStatus': 'machine_status',
        'DowntimeReason': 'downtime_reason',
        'GoodUnitsProduced': 'good_units_produced',
        'ScrapUnitsProduced': 'scrap_units_produced',
        'TargetRate_units_per_5min': 'target_rate_units_per_5min',
        'StandardCost_per_unit': 'standard_cost_per_unit',
        'SalePrice_per_unit': 'sale_price_per_unit',
        'Availability_Score': 'availability_score',
        'Performance_Score': 'performance_score',
        'Quality_Score': 'quality_score',
        'OEE_Score': 'oee_score'
    }
    df_db.rename(columns=column_mapping, inplace=True)
    
    # Add run_id if this is simulation data
    if table_name == 'simulation_data':
        if not run_id:
            raise ValueError("run_id is required for simulation_data table")
        df_db['run_id'] = run_id
    
    # Create database connection
    # Allow database path to be configurable via environment variable
    db_path = os.environ.get('MES_DATABASE_PATH', 
                             os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mes_database.db"))
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Create tables if they don't exist
    SQLModel.metadata.create_all(engine)
    
    # Save to database
    with Session(engine) as session:
        # Clear existing data if writing to mes_data (master data)
        if table_name == 'mes_data':
            session.query(MESData).delete()
            session.commit()
        
        # Create twin_run record if needed for simulation data
        if table_name == 'simulation_data':
            # Check if run exists
            from sqlmodel import select
            statement = select(TwinRun).where(TwinRun.run_id == run_id)
            existing_run = session.exec(statement).first()
            if not existing_run:
                # Create new run record
                new_run = TwinRun(
                    run_id=run_id,
                    run_type='simulation',
                    seed=42,  # Default seed
                    generator_version='1.0.0',
                    parent_run_id=None,
                    started_at=datetime.now(),
                    finished_at=datetime.now(),
                    config_delta_json='{}',  # Empty config for now
                    status='completed'
                )
                session.add(new_run)
                session.commit()
        
        # Convert DataFrame to model objects
        for _, row in df_db.iterrows():
            if table_name == 'mes_data':
                record = MESData(**row.to_dict())
            else:
                record = SimulationData(**row.to_dict())
            session.add(record)
        
        session.commit()
        print(f"Saved {len(df_db)} records to {table_name}")


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
                # Note: Energy consumption is now calculated by virtual sensors
                # See virtual_sensors.py PowerMeterSensor for energy derivation
                
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
                
                # Get equipment flows for proper cascade modeling
                equipment_flows = cascade_config.get('equipment_flows', {
                    'LINE1': ['LINE1-FIL', 'LINE1-PCK', 'LINE1-PAL'],
                    'LINE2': ['LINE2-FIL', 'LINE2-PCK', 'LINE2-PAL'],
                    'LINE3': ['LINE3-FIL', 'LINE3-PCK', 'LINE3-PAL']
                })
                
                # Determine line and position in flow
                line_key = f"LINE{equip['LineID']}"
                equipment_flow = equipment_flows.get(line_key, [])
                
                # Check if this equipment just stopped (can trigger cascade)
                if equip_id in equipment_flow and status == "Stopped":
                    # Mark cascade start time for each downstream equipment
                    position = equipment_flow.index(equip_id)
                    downstream_equipment = equipment_flow[position + 1:]  # All equipment after this one
                    
                    for downstream_id in downstream_equipment:
                        cascade_key = f"{equip_id}_to_{downstream_id}"
                        if cascade_key not in cascade_tracker:
                            cascade_tracker[cascade_key] = current_time
                
                # Check if this equipment just restarted (clears cascade)
                elif equip_id in equipment_flow and status == "Running":
                    # Clear cascades originating from this equipment
                    position = equipment_flow.index(equip_id)
                    downstream_equipment = equipment_flow[position + 1:]
                    
                    for downstream_id in downstream_equipment:
                        cascade_key = f"{equip_id}_to_{downstream_id}"
                        if cascade_key in cascade_tracker:
                            del cascade_tracker[cascade_key]
                
                # Check if this equipment should be affected by an upstream cascade
                elif equip_id in equipment_flow and status == "Running":
                    # Check all potential upstream equipment that could affect this one
                    position = equipment_flow.index(equip_id)
                    upstream_equipment = equipment_flow[:position]  # All equipment before this one
                    
                    for upstream_id in upstream_equipment:
                        cascade_key = f"{upstream_id}_to_{equip_id}"
                        if cascade_key in cascade_tracker:
                            # Check if enough time has passed for cascade
                            time_since_upstream_stop = (current_time - cascade_tracker[cascade_key]).total_seconds() / 60
                            if time_since_upstream_stop >= cascade_config['cascade_delay_minutes']:
                                # Apply cascade failure with probability
                                if random.random() < cascade_config['downstream_stop_probability']:
                                    status = "Stopped"
                                    reason = "UNP-MAT"  # Material starvation
                                    good_units, scrap_units = 0, 0
                                    break  # Stop checking once we've cascaded
            
            # Calculate instantaneous KPIs
            kpis = calculate_kpis(status, good_units, scrap_units, order_info["TargetRate_units_per_5min"])
            
            # Calculate energy consumption
            # Check if this is a micro-stop (short downtime that just started)
            is_micro_stop = (status == "Stopped" and 
                           equip_id in downtime_tracker and 
                           (downtime_tracker[equip_id]["end"] - current_time).total_seconds() / 60 < 2)
            
            # Note: Energy consumption is now calculated by virtual sensors
            # See virtual_sensors.py PowerMeterSensor for energy derivation
            
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
    import argparse
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    parser = argparse.ArgumentParser(description='Generate MES data')
    parser.add_argument('--output', choices=['csv', 'db', 'both'], default='csv',
                        help='Output format: csv, db (database), or both')
    parser.add_argument('--table', choices=['mes_data', 'simulation_data'], default='mes_data',
                        help='Database table to write to (only for db/both output)')
    parser.add_argument('--run-id', type=str, default=None,
                        help='Simulation run ID (required for simulation_data table)')
    parser.add_argument('--start-date', type=str, default='2025-06-01',
                        help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2025-06-14',
                        help='End date (YYYY-MM-DD)')
    parser.add_argument('--config', type=str, default=None,
                        help='Path to custom configuration file (overrides default mes_data_config.json)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducible simulations')
    args = parser.parse_args()
    
    # Set random seed if provided
    if args.seed is not None:
        np.random.seed(args.seed)
        print(f"Using random seed: {args.seed}")
    
    # Load configuration
    if args.config:
        config = load_config(args.config)
        print(f"Using custom config: {args.config}")
    else:
        config = load_config()
        print("Using default config: mes_data_config.json")
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
    
    print(f"MES Data Generation using {config['ontology']['name']} v{config['ontology']['version']}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Output: {args.output}")
    if args.output in ['db', 'both']:
        print(f"Table: {args.table}")
        if args.table == 'simulation_data' and args.run_id:
            print(f"Run ID: {args.run_id}")
    print("-" * 60)
    
    # Generate data
    mes_data = generate_mes_data(start_date, end_date, config)
    
    # Save to CSV if requested
    if args.output in ['csv', 'both']:
        csv_file = save_to_csv(mes_data)
        print(f"\nData saved to {csv_file}")
    
    # Save to database if requested
    if args.output in ['db', 'both']:
        save_to_database(mes_data, args.table, args.run_id)
        print(f"\nData saved to database table: {args.table}")
    
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