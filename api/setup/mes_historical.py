#!/usr/bin/env python3
"""
MES Historical Data Generation Module
Generates manufacturing data with realistic OEE values based on configuration
"""

import pandas as pd
import numpy as np
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict
import os
import sys

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)


class MESHistoricalDataGenerator:
    """Generator for MES historical data with realistic anomalies and KPIs"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.product_master = config.get('product_master', {})
        self.equipment_config = config.get('equipment_configuration', {})
        self.downtime_reasons = config.get('downtime_reason_mapping', {})
        self.anomaly_config = config.get('anomaly_injection', {})
        self.production_schedule = config.get('production_schedule', {})
        self.product_specs = config.get('product_specifications', {})
        self.energy_config = config.get('energy_consumption', {})

    def get_product_master(self) -> pd.DataFrame:
        """Returns a DataFrame of product master data from configuration"""
        products = []
        for product_id, product_info in self.product_master.items():
            products.append({
                "ProductID": product_id,
                "ProductName": product_info['name'],
                "TargetRate_units_per_5min": product_info['target_rate_units_per_5min'],
                "StandardCost_per_unit": product_info['standard_cost_per_unit'],
                "SalePrice_per_unit": product_info['sale_price_per_unit'],
                "NormalScrapRate": product_info.get('normal_scrap_rate', 
                                                   self.product_specs.get('normal_scrap_rate', 0.02))
            })
        return pd.DataFrame(products)

    def get_equipment_master(self) -> pd.DataFrame:
        """Returns a DataFrame of equipment master data from configuration"""
        equipment = []
        for line_id, line_info in self.equipment_config.get('lines', {}).items():
            line_num = int(line_id.replace('LINE', ''))
            for eq_info in line_info.get('equipment_sequence', []):
                equipment.append({
                    "EquipmentID": eq_info['id'],
                    "EquipmentName": f"{eq_info['type']} {line_info['name']}",
                    "LineID": line_num,
                    "EquipmentType": eq_info['type']
                })
        return pd.DataFrame(equipment)

    def generate_production_orders(self, products_df: pd.DataFrame, start_date: datetime, 
                                   end_date: datetime) -> pd.DataFrame:
        """Generates a list of production orders for each line using configuration"""
        orders = []
        order_id_counter = 1000
        
        # Get number of lines from config
        num_lines = len(self.equipment_config.get('lines', {}))
        
        for line in range(1, num_lines + 1):
            current_time = start_date
            while current_time < end_date:
                product = products_df.sample(1).iloc[0]
                
                # Use configured run duration range
                run_duration_hours = random.uniform(
                    self.production_schedule.get('run_duration_hours', {}).get('min', 4),
                    self.production_schedule.get('run_duration_hours', {}).get('max', 12)
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
                    self.production_schedule.get('changeover_gap_minutes', {}).get('min', 30),
                    self.production_schedule.get('changeover_gap_minutes', {}).get('max', 60)
                )
                current_time = end_time + timedelta(minutes=gap_minutes)
        
        return pd.DataFrame(orders)

    def get_shift_number(self, current_time: datetime) -> int:
        """Determine shift number based on time (1: 6am-2pm, 2: 2pm-10pm, 3: 10pm-6am)"""
        hour = current_time.hour
        if 6 <= hour < 14:
            return 1
        elif 14 <= hour < 22:
            return 2
        else:
            return 3

    def apply_anomalies(self, equip_id: str, current_time: datetime, order_info: Dict[str, Any],
                       changeover_start_times: List[datetime], performance_drop_tracker: Dict[str, Any],
                       last_cleaning_times: Dict[str, datetime]) -> Tuple[str, Optional[str], int, int, Optional[datetime]]:
        """Apply configured anomalies to determine equipment status and production rates"""
        
        product_config = self.product_master.get(order_info['ProductID'], {})
        
        # Check scheduled maintenance
        if self.anomaly_config.get('scheduled_maintenance', {}).get('enabled', False):
            for pattern in self.anomaly_config['scheduled_maintenance'].get('patterns', []):
                if (equip_id == pattern['equipment_id'] and 
                    current_time.weekday() == pattern['day_of_week'] and
                    current_time.hour == pattern['hour'] and
                    current_time.minute < pattern['duration_minutes']):
                    return "Stopped", pattern['downtime_reason'], 0, 0, current_time + timedelta(minutes=pattern['duration_minutes'])
        
        # Check cleaning cycles
        if self.anomaly_config.get('cleaning_cycles', {}).get('enabled', False):
            cleaning = self.anomaly_config['cleaning_cycles']
            if equip_id not in last_cleaning_times:
                last_cleaning_times[equip_id] = current_time
            
            hours_since_cleaning = (current_time - last_cleaning_times[equip_id]).total_seconds() / 3600
            if hours_since_cleaning >= cleaning['frequency_hours']:
                last_cleaning_times[equip_id] = current_time
                return "Stopped", cleaning['downtime_reason'], 0, 0, current_time + timedelta(minutes=cleaning['duration_minutes'])
        
        # Check major mechanical failure
        if self.anomaly_config.get('major_mechanical_failure', {}).get('enabled', False):
            failure = self.anomaly_config['major_mechanical_failure']
            start_dt = datetime.strptime(failure['start_datetime'], '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(failure['end_datetime'], '%Y-%m-%d %H:%M:%S')
            
            if equip_id == failure['equipment_id'] and start_dt <= current_time <= end_dt:
                return "Stopped", failure['downtime_reason'], 0, 0, end_dt
        
        # Check various anomaly patterns
        anomaly_patterns = [
            'frequent_micro_stops', 'minor_stops_line1', 'recurring_jams_line1', 
            'electrical_issues', 'quality_control_stops'
        ]
        
        for pattern_name in anomaly_patterns:
            if self.anomaly_config.get(pattern_name, {}).get('enabled', False):
                anomaly = self.anomaly_config[pattern_name]
                if equip_id == anomaly['equipment_id']:
                    if random.random() < anomaly['probability_per_5min']:
                        duration = random.uniform(
                            anomaly['duration_range_minutes']['min'],
                            anomaly['duration_range_minutes']['max']
                        )
                        downtime_end = current_time + timedelta(minutes=duration)
                        return "Stopped", anomaly['downtime_reason'], 0, 0, downtime_end
        
        # Check operator issues (night shift)
        if self.anomaly_config.get('operator_issues_shift3', {}).get('enabled', False):
            opr = self.anomaly_config['operator_issues_shift3']
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
        if self.anomaly_config.get('material_starvation_patterns', {}).get('enabled', False):
            for pattern in self.anomaly_config['material_starvation_patterns'].get('equipment_patterns', []):
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
        
        # Check equipment-specific micro-stop patterns
        micro_stop_patterns = ['random_sensor_issues', 'filler_micro_stops', 'palletizer_micro_stops']
        for pattern_name in micro_stop_patterns:
            if self.anomaly_config.get(pattern_name, {}).get('enabled', False):
                for pattern in self.anomaly_config[pattern_name].get('equipment_patterns', []):
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
        shift = self.get_shift_number(current_time)
        shift_key = f"shift{shift}"
        if shift_key in self.product_specs.get('performance_variation', {}):
            shift_range = self.product_specs['performance_variation'][shift_key]
            actual_rate *= random.uniform(shift_range['min'], shift_range['max'])
        
        # Check performance bottleneck
        if (self.anomaly_config.get('performance_bottleneck', {}).get('enabled', False) and 
            'performance_issue_lines' in product_config):
            line_id = f"LINE{order_info['LineID']}"
            if line_id in product_config['performance_issue_lines']:
                perf_range = product_config['performance_degradation']
                actual_rate *= random.uniform(perf_range['min'], perf_range['max'])
        
        # Check random performance drops
        perf_drops = self.product_specs.get('random_performance_drops', {})
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
        
        if equip_type_name in self.product_specs.get('equipment_efficiency', {}):
            eff_range = self.product_specs['equipment_efficiency'][equip_type_name]
            actual_rate *= random.uniform(eff_range['min'], eff_range['max'])
        
        # Calculate good and scrap units
        good_units = int(actual_rate)
        
        # Determine scrap rate
        scrap_rate = product_config.get('normal_scrap_rate', 
                                       self.product_specs.get('normal_scrap_rate', 0.02))
        
        # Check if in startup period (first 30 minutes after changeover)
        for co_time in changeover_start_times:
            if current_time >= co_time and current_time < co_time + timedelta(minutes=30):
                scrap_rate = product_config.get('startup_scrap_rate', scrap_rate * 2)
                break
        
        # Check quality issues
        if (self.anomaly_config.get('quality_issues', {}).get('enabled', False) and 
            'quality_issue_scrap_rate' in product_config):
            scrap_rate = product_config['quality_issue_scrap_rate']
        
        # Check changeover scrap spike
        if self.anomaly_config.get('changeover_scrap_spike', {}).get('enabled', False):
            for co_time in changeover_start_times:
                spike_config = self.anomaly_config['changeover_scrap_spike']
                if (current_time >= co_time and 
                    current_time < co_time + timedelta(minutes=spike_config['duration_minutes'])):
                    scrap_rate *= spike_config['scrap_multiplier']
                    break
        
        # Check quality variation during normal production
        if self.anomaly_config.get('quality_variation_normal', {}).get('enabled', False):
            qual_var = self.anomaly_config['quality_variation_normal']
            if random.random() < qual_var['probability_per_5min']:
                scrap_rate *= qual_var['scrap_rate_multiplier']
        
        # Check quality degradation at end of run
        if self.anomaly_config.get('quality_end_of_run', {}).get('enabled', False):
            end_run_config = self.anomaly_config['quality_end_of_run']
            hours_before = end_run_config['hours_before_changeover']
            for co_time in changeover_start_times:
                if co_time > current_time:  # This is the next changeover
                    time_until_changeover = (co_time - current_time).total_seconds() / 3600
                    if time_until_changeover <= hours_before:
                        scrap_rate *= end_run_config['scrap_rate_multiplier']
                    break
        
        scrap_units = int(good_units * scrap_rate / (1 - scrap_rate)) if scrap_rate < 1 else 0
        
        return "Running", None, good_units, scrap_units, None

    def calculate_kpis(self, status: str, good_units: int, scrap_units: int, target_rate: float) -> Dict[str, float]:
        """Calculate instantaneous KPIs for 5-minute intervals"""
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

    def calculate_energy_consumption(self, status: str, equipment_type: str, product_id: Optional[str],
                                   performance_score: float, is_micro_stop: bool = False) -> float:
        """Calculate energy consumption for 5-minute interval based on equipment status and performance"""
        
        base_consumption = self.energy_config.get('base_consumption_kw', {})
        
        # Get base consumption for equipment type
        equip_energy = base_consumption.get(equipment_type, {})
        if status == "Running":
            base_kw = equip_energy.get('running', 15.0)  # Default 15kW if not specified
        else:
            base_kw = equip_energy.get('idle', 1.5)  # Default 1.5kW idle
        
        # Apply performance impact (non-linear scaling)
        if status == "Running" and performance_score > 0:
            perf_factor = performance_score / 100.0
            scaling_factor = self.energy_config.get('performance_impact', {}).get('scaling_factor', 0.8)
            # Energy doesn't scale linearly with performance
            energy_factor = 1.0 - (1.0 - perf_factor) * scaling_factor
            base_kw *= energy_factor
        
        # Apply product-specific factor
        product_factors = self.energy_config.get('product_specific_factors', {})
        if product_id and product_id in product_factors:
            product_multiplier = product_factors[product_id].get('energy_multiplier', 1.0)
            base_kw *= product_multiplier
        
        # Apply micro-stop penalty (startup surge)
        if is_micro_stop:
            micro_stop_config = self.energy_config.get('micro_stop_penalty', {})
            surge_multiplier = micro_stop_config.get('startup_surge_multiplier', 1.5)
            base_kw *= surge_multiplier
        
        # Convert to kWh for 5-minute interval (5/60 hours)
        energy_kwh = base_kw * (5.0 / 60.0)
        
        return round(energy_kwh, 3)

    def generate_mes_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Main function to generate the complete MES dataset with inline KPIs"""
        
        logger.info("Generating MES historical data...")
        logger.info("Loading master data from configuration...")
        products_df = self.get_product_master()
        equipment_df = self.get_equipment_master()
        
        logger.info("Generating production schedule...")
        orders_df = self.generate_production_orders(products_df, start_date, end_date)
        
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
        
        logger.info("Starting data generation loop...")
        total_intervals = int((end_date - start_date).total_seconds() / 60 / 5)
        intervals_processed = 0
        
        progress_interval = self.config.get('historical_data_generation', {}).get('progress_reporting_interval', 200)
        
        while current_time <= end_date:
            intervals_processed += 1
            if intervals_processed % progress_interval == 0:
                progress = (intervals_processed / total_intervals) * 100
                logger.info(f"  Progress: {progress:.1f}% ({intervals_processed}/{total_intervals} 5-min intervals)")
            
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
                    idle_energy = self.calculate_energy_consumption(
                        status="Stopped",
                        equipment_type=equip["EquipmentType"],
                        product_id=None,
                        performance_score=0,
                        is_micro_stop=False
                    )
                    
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
                        "OEE_Score": 0.0,
                        "Energy_Consumption_kWh": idle_energy
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
                    status, reason, good_units, scrap_units, downtime_end = self.apply_anomalies(
                        equip_id, current_time, order_info, changeover_start_times,
                        performance_drop_tracker, last_cleaning_times
                    )
                    
                    if downtime_end:
                        downtime_tracker[equip_id] = {"end": downtime_end, "reason": reason}
                
                # Check cascade failures (downstream equipment starves when upstream stops)
                if self.anomaly_config.get('cascade_failures', {}).get('enabled', False):
                    cascade_config = self.anomaly_config['cascade_failures']
                    
                    # Check if this is a trigger equipment (upstream) that just stopped
                    if equip_id in cascade_config['trigger_equipment'] and status == "Stopped":
                        line_id = equip["LineID"]
                        cascade_key = f"LINE{line_id}"
                        if cascade_key not in cascade_tracker:
                            cascade_tracker[cascade_key] = current_time
                    
                    # Check if this is a trigger equipment that just restarted
                    elif equip_id in cascade_config['trigger_equipment'] and status == "Running":
                        line_id = equip["LineID"]
                        cascade_key = f"LINE{line_id}"
                        if cascade_key in cascade_tracker:
                            del cascade_tracker[cascade_key]
                    
                    # Check if this is downstream equipment that should be starved
                    elif equip_id not in cascade_config['trigger_equipment'] and status == "Running":
                        line_id = equip["LineID"]
                        cascade_key = f"LINE{line_id}"
                        if cascade_key in cascade_tracker:
                            time_since_upstream_stop = (current_time - cascade_tracker[cascade_key]).total_seconds() / 60
                            if time_since_upstream_stop >= cascade_config['cascade_delay_minutes']:
                                if random.random() < cascade_config['downstream_stop_probability']:
                                    status = "Stopped"
                                    reason = "UNP-MAT"  # Material starvation
                                    good_units, scrap_units = 0, 0
                
                # Calculate instantaneous KPIs
                kpis = self.calculate_kpis(status, good_units, scrap_units, order_info["TargetRate_units_per_5min"])
                
                # Calculate energy consumption
                is_micro_stop = (status == "Stopped" and 
                               equip_id in downtime_tracker and 
                               (downtime_tracker[equip_id]["end"] - current_time).total_seconds() / 60 < 2)
                
                energy_consumption = self.calculate_energy_consumption(
                    status=status,
                    equipment_type=equip["EquipmentType"],
                    product_id=order_info["ProductID"],
                    performance_score=kpis['Performance_Score'],
                    is_micro_stop=is_micro_stop
                )
                
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
                    "OEE_Score": kpis['OEE_Score'],
                    # Energy consumption
                    "Energy_Consumption_kWh": energy_consumption
                }
                all_logs.append(log_entry)
            
            current_time += timedelta(minutes=5)
        
        logger.info(f"Generated {len(all_logs)} log entries")
        return pd.DataFrame(all_logs)

    def save_to_database(self, df: pd.DataFrame, table_name: str, run_id: Optional[str] = None) -> bool:
        """Save DataFrame to database table"""
        try:
            # Import here to avoid circular imports
            from sqlalchemy import create_engine
            
            # Check if models are available
            try:
                from api.models import MESData, SimulationData, TwinRun
                from sqlmodel import Session, SQLModel, select
            except ImportError:
                logger.error("Database models not available - cannot save to database")
                return False
            
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
                    logger.error("run_id is required for simulation_data table")
                    return False
                df_db['run_id'] = run_id
            
            # Create database connection
            db_path = self.config.get('database', {}).get('path', 'data/mes_database.db')
            if not os.path.isabs(db_path):
                # Convert to absolute path relative to project root
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                db_path = os.path.join(project_root, db_path)
            
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
                
                # Convert DataFrame to model objects in batches
                batch_size = self.config.get('historical_data_generation', {}).get('batch_size', 1000)
                for i in range(0, len(df_db), batch_size):
                    batch = df_db.iloc[i:i+batch_size]
                    for _, row in batch.iterrows():
                        try:
                            if table_name == 'mes_data':
                                record = MESData(**row.to_dict())
                            else:
                                record = SimulationData(**row.to_dict())
                            session.add(record)
                        except Exception as e:
                            logger.warning(f"Failed to create record: {e}")
                    
                    session.commit()
                    logger.debug(f"Saved batch {i//batch_size + 1}/{(len(df_db)-1)//batch_size + 1}")
                
                logger.info(f"Saved {len(df_db)} records to {table_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            return False

    def save_to_csv(self, df: pd.DataFrame, filename: str) -> bool:
        """Save DataFrame to CSV file"""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(filename)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            df.to_csv(filename, index=False)
            logger.info(f"Saved {len(df)} records to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to CSV: {e}")
            return False

    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for the dataset"""
        try:
            summary = {
                "total_records": len(df),
                "lines": df['LineID'].nunique() if 'LineID' in df else 0,
                "equipment": df['EquipmentID'].nunique() if 'EquipmentID' in df else 0,
                "products": df['ProductID'].nunique() if 'ProductID' in df else 0,
                "production_orders": df['ProductionOrderID'].nunique() if 'ProductionOrderID' in df else 0,
            }
            
            # KPI Summary
            if all(col in df.columns for col in ['Availability_Score', 'Performance_Score', 'Quality_Score', 'OEE_Score']):
                summary["kpi_averages"] = {
                    "availability": df['Availability_Score'].mean(),
                    "performance": df['Performance_Score'].mean(),
                    "quality": df['Quality_Score'].mean(),
                    "oee": df['OEE_Score'].mean()
                }
                
                # OEE Distribution
                summary["oee_distribution"] = {
                    "world_class_85_plus": len(df[df['OEE_Score'] >= 85]) / len(df) * 100,
                    "good_65_to_85": len(df[(df['OEE_Score'] >= 65) & (df['OEE_Score'] < 85)]) / len(df) * 100,
                    "fair_50_to_65": len(df[(df['OEE_Score'] >= 50) & (df['OEE_Score'] < 65)]) / len(df) * 100,
                    "poor_below_50": len(df[df['OEE_Score'] < 50]) / len(df) * 100
                }
            
            # Downtime analysis
            if 'MachineStatus' in df.columns:
                downtime_records = df[df['MachineStatus'] != 'Running']
                if len(downtime_records) > 0:
                    summary["downtime"] = {
                        "total_events": len(downtime_records),
                        "percentage": len(downtime_records) / len(df) * 100,
                        "top_reasons": downtime_records['DowntimeReason'].value_counts().head().to_dict()
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate summary statistics: {e}")
            return {"error": str(e)}