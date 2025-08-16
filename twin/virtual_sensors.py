"""Virtual Sensor Layer - Derives observations from production data

This module implements the virtual sensor abstraction layer that observes
and derives metrics from MES production data, rather than generating
synthetic sensor readings. This addresses the reality that many facilities 
have excellent MES data but lack comprehensive IoT sensor infrastructure.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class SensorObservation:
    """Represents a single observation from a virtual sensor."""
    sensor_id: str
    equipment_id: str
    timestamp: datetime
    observable_property: str
    value: float
    unit: str
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class VirtualSensor(ABC):
    """Base class for virtual sensors that observe production data."""
    
    def __init__(self, sensor_type: str, config: Optional[Dict] = None):
        """Initialize virtual sensor.
        
        Args:
            sensor_type: Type identifier for the sensor
            config: Optional configuration dictionary
        """
        self.sensor_type = sensor_type
        self.config = config or {}
    
    @abstractmethod
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        """Derive observations from production data.
        
        Args:
            production_data: DataFrame containing MES/simulation data
            
        Returns:
            List of sensor observations
        """
        pass
    
    def _validate_required_columns(self, df: pd.DataFrame, required: List[str]) -> bool:
        """Validate that required columns exist in DataFrame.
        
        Args:
            df: DataFrame to validate
            required: List of required column names
            
        Returns:
            True if all required columns exist
            
        Raises:
            ValueError: If required columns are missing
        """
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns for {self.sensor_type}: {missing}")
        return True


class PowerMeterSensor(VirtualSensor):
    """Virtual power meter that derives energy consumption from production patterns."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize power meter sensor.
        
        Args:
            config: Configuration with energy parameters
        """
        super().__init__("power_meter", config)
        
        # Get energy parameters from config
        sensor_config = self.config.get('virtual_sensors', {}).get('power_meter', {})
        self.base_power = sensor_config.get('base_power_kwh', {
            'Filler': 85.0,
            'Packer': 75.0, 
            'Palletizer': 65.0
        })
        
        self.idle_power = sensor_config.get('idle_power_kwh', {
            'Filler': 15.0,
            'Packer': 12.0,
            'Palletizer': 10.0
        })
        
        # Get confidence from config
        confidence_levels = self.config.get('virtual_sensors', {}).get('confidence_levels', {})
        self.confidence = confidence_levels.get('power_consumption', 0.95)
        
        self.product_power_factor = self.config.get('product_power_factor', {
            'P001': 1.0,   # Standard
            'P002': 1.15,  # Heavier
            'P003': 0.9,   # Lighter
            'P004': 1.2,   # Premium
            'P005': 1.05   # Standard Plus
        })
        
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        """Calculate energy consumption from production patterns.
        
        Args:
            production_data: DataFrame with production data
            
        Returns:
            List of power consumption observations
        """
        required_cols = ['equipment_id', 'equipment_type', 'machine_status',
                        'performance_score', 'product_id', 'timestamp']
        self._validate_required_columns(production_data, required_cols)
        
        observations = []
        
        for _, row in production_data.iterrows():
            energy_kwh = self._calculate_energy(
                status=row['machine_status'],
                equipment_type=row['equipment_type'],
                performance=row['performance_score'],
                product_id=row.get('product_id')
            )
            
            observations.append(SensorObservation(
                sensor_id=f"PWR-{row['equipment_id']}",
                equipment_id=row['equipment_id'],
                timestamp=pd.to_datetime(row['timestamp']),
                observable_property='power_consumption',
                value=round(energy_kwh, 3),
                unit='kWh',
                confidence=self.confidence,
                metadata={
                    'equipment_type': row['equipment_type'],
                    'machine_status': row['machine_status'],
                    'calculation_method': 'derived_from_production'
                }
            ))
            
        return observations
    
    def _calculate_energy(self, status: str, equipment_type: str, 
                         performance: float, product_id: Optional[str] = None) -> float:
        """Calculate energy consumption for a 5-minute interval.
        
        Args:
            status: Machine status (Running/Stopped)
            equipment_type: Type of equipment
            performance: Performance score (0-100)
            product_id: Product being produced
            
        Returns:
            Energy consumption in kWh
        """
        if status == 'Stopped':
            # Idle power consumption
            return self.idle_power.get(equipment_type, 10.0) * (5/60)  # 5-min interval
        
        # Running power consumption
        base = self.base_power.get(equipment_type, 70.0)
        
        # Adjust for performance (lower performance = more energy per unit)
        perf_factor = 2.0 - (performance / 100.0) if performance > 0 else 2.0
        
        # Adjust for product type
        product_factor = self.product_power_factor.get(product_id, 1.0) if product_id else 1.0
        
        # Calculate for 5-minute interval
        energy_kwh = base * perf_factor * product_factor * (5/60)
        
        return energy_kwh


class ThroughputSensor(VirtualSensor):
    """Observes production rate vs target to identify efficiency."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize throughput sensor."""
        super().__init__("throughput", config)
        confidence_levels = self.config.get('virtual_sensors', {}).get('confidence_levels', {})
        self.confidence = confidence_levels.get('throughput_efficiency', 1.0)
        
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        """Observe throughput efficiency from production data.
        
        Args:
            production_data: DataFrame with production data
            
        Returns:
            List of throughput observations
        """
        required_cols = ['equipment_id', 'machine_status', 'good_units_produced',
                        'target_rate_units_per_5min', 'timestamp']
        self._validate_required_columns(production_data, required_cols)
        
        observations = []
        
        for _, row in production_data.iterrows():
            if row['machine_status'] == 'Running' and row['target_rate_units_per_5min'] > 0:
                throughput_ratio = row['good_units_produced'] / row['target_rate_units_per_5min']
                
                observations.append(SensorObservation(
                    sensor_id=f"THR-{row['equipment_id']}",
                    equipment_id=row['equipment_id'],
                    timestamp=pd.to_datetime(row['timestamp']),
                    observable_property='throughput_efficiency',
                    value=round(throughput_ratio, 4),
                    unit='ratio',
                    confidence=self.confidence,
                    metadata={
                        'good_units': row['good_units_produced'],
                        'target_units': row['target_rate_units_per_5min']
                    }
                ))
                
        return observations


class DefectRateSensor(VirtualSensor):
    """Observes quality through scrap patterns."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize defect rate sensor."""
        super().__init__("defect_rate", config)
        confidence_levels = self.config.get('virtual_sensors', {}).get('confidence_levels', {})
        self.confidence = confidence_levels.get('defect_rate', 1.0)
        
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        """Observe defect rates from production data.
        
        Args:
            production_data: DataFrame with production data
            
        Returns:
            List of defect rate observations
        """
        required_cols = ['equipment_id', 'good_units_produced',
                        'scrap_units_produced', 'timestamp']
        self._validate_required_columns(production_data, required_cols)
        
        observations = []
        
        for _, row in production_data.iterrows():
            total_units = row['good_units_produced'] + row['scrap_units_produced']
            if total_units > 0:
                defect_rate = row['scrap_units_produced'] / total_units
                
                observations.append(SensorObservation(
                    sensor_id=f"QUA-{row['equipment_id']}",
                    equipment_id=row['equipment_id'],
                    timestamp=pd.to_datetime(row['timestamp']),
                    observable_property='defect_rate',
                    value=round(defect_rate, 4),
                    unit='ratio',
                    confidence=self.confidence,
                    metadata={
                        'scrap_units': row['scrap_units_produced'],
                        'total_units': total_units,
                        'quality_score': row.get('quality_score', None)
                    }
                ))
                
        return observations


class BottleneckDetector(VirtualSensor):
    """Identifies production bottlenecks from OEE patterns."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize bottleneck detector."""
        super().__init__("bottleneck", config)
        sensor_config = self.config.get('virtual_sensors', {}).get('bottleneck_detector', {})
        self.window_size = sensor_config.get('window_size', 12)
        self.significance_threshold = sensor_config.get('significance_threshold', 0.9)
        confidence_levels = self.config.get('virtual_sensors', {}).get('confidence_levels', {})
        self.confidence = confidence_levels.get('bottleneck_indicator', 0.8)
        
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        """Identify bottlenecks from OEE patterns.
        
        Args:
            production_data: DataFrame with production data
            
        Returns:
            List of bottleneck observations
        """
        required_cols = ['equipment_id', 'oee_score', 'timestamp', 'line_id']
        self._validate_required_columns(production_data, required_cols)
        
        observations = []
        
        # Analyze by line and time window
        for line_id in production_data['line_id'].unique():
            line_data = production_data[production_data['line_id'] == line_id]
            
            # Group by time windows
            line_data_sorted = line_data.sort_values('timestamp')
            
            for i in range(0, len(line_data_sorted), self.window_size):
                window_data = line_data_sorted.iloc[i:i+self.window_size]
                if len(window_data) < 3:  # Need minimum data points
                    continue
                    
                # Calculate average OEE by equipment in this window
                equipment_oee = window_data.groupby('equipment_id')['oee_score'].mean()
                
                if len(equipment_oee) > 0:
                    min_oee_equipment = equipment_oee.idxmin()
                    avg_oee = equipment_oee.mean()
                    
                    # Each equipment gets a bottleneck score
                    for equipment_id, oee in equipment_oee.items():
                        # Bottleneck score: 1.0 if lowest OEE and significantly below average
                        is_bottleneck = 1.0 if (equipment_id == min_oee_equipment and 
                                               oee < avg_oee * self.significance_threshold) else 0.0
                        
                        observations.append(SensorObservation(
                            sensor_id=f"BTN-{equipment_id}",
                            equipment_id=equipment_id,
                            timestamp=window_data['timestamp'].max(),
                            observable_property='bottleneck_indicator',
                            value=is_bottleneck,
                            unit='boolean',
                            confidence=self.confidence,
                            metadata={
                                'oee': round(oee, 2),
                                'line_avg_oee': round(avg_oee, 2),
                                'line_id': line_id,
                                'window_size': len(window_data)
                            }
                        ))
                        
        return observations


class LineCouplingMonitor(VirtualSensor):
    """Monitors equipment coupling and cascade effects."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize line coupling monitor."""
        super().__init__("line_coupling", config)
        sensor_config = self.config.get('virtual_sensors', {}).get('line_coupling', {})
        self.cascade_threshold = sensor_config.get('cascade_threshold', 0.7)
        confidence_levels = self.config.get('virtual_sensors', {}).get('confidence_levels', {})
        self.confidence = confidence_levels.get('line_coupling_strength', 0.9)
        
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        """Monitor cascade effects between equipment.
        
        Args:
            production_data: DataFrame with production data
            
        Returns:
            List of coupling strength observations
        """
        required_cols = ['equipment_id', 'machine_status', 'timestamp', 
                        'line_id', 'downtime_reason']
        self._validate_required_columns(production_data, required_cols)
        
        observations = []
        
        # Analyze by line
        for line_id in production_data['line_id'].unique():
            line_data = production_data[production_data['line_id'] == line_id].sort_values('timestamp')
            
            # Look for cascade patterns (multiple equipment down within same time window)
            for timestamp in line_data['timestamp'].unique():
                time_slice = line_data[line_data['timestamp'] == timestamp]
                
                # Count equipment status
                total_equipment = len(time_slice)
                stopped_equipment = len(time_slice[time_slice['machine_status'] == 'Stopped'])
                
                if total_equipment > 0:
                    coupling_strength = stopped_equipment / total_equipment
                    
                    # Check for cascade pattern (upstream failure)
                    cascade_detected = 0.0
                    if stopped_equipment > 1:
                        # Check if downstream equipment has 'upstream' related downtime
                        upstream_related = time_slice[
                            time_slice['downtime_reason'].isin(['DT006', 'DT007'])  # Upstream/downstream codes
                        ]
                        if len(upstream_related) > 0:
                            cascade_detected = 1.0
                    
                    # One observation per line per timestamp
                    observations.append(SensorObservation(
                        sensor_id=f"LCP-{line_id}",
                        equipment_id=f"LINE-{line_id}",
                        timestamp=pd.to_datetime(timestamp),
                        observable_property='line_coupling_strength',
                        value=round(coupling_strength, 3),
                        unit='ratio',
                        confidence=self.confidence,
                        metadata={
                            'stopped_count': stopped_equipment,
                            'total_count': total_equipment,
                            'cascade_detected': cascade_detected
                        }
                    ))
                    
        return observations


class DowntimePatternSensor(VirtualSensor):
    """Analyzes downtime patterns and trends."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize downtime pattern sensor."""
        super().__init__("downtime_pattern", config)
        confidence_levels = self.config.get('virtual_sensors', {}).get('confidence_levels', {})
        self.confidence = confidence_levels.get('downtime_frequency', 1.0)
        
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        """Analyze downtime patterns from production data.
        
        Args:
            production_data: DataFrame with production data
            
        Returns:
            List of downtime pattern observations
        """
        required_cols = ['equipment_id', 'machine_status', 'downtime_reason', 'timestamp']
        self._validate_required_columns(production_data, required_cols)
        
        observations = []
        
        # Analyze downtime patterns by equipment
        for equipment_id in production_data['equipment_id'].unique():
            equip_data = production_data[production_data['equipment_id'] == equipment_id]
            
            # Calculate rolling downtime frequency (last hour)
            equip_data_sorted = equip_data.sort_values('timestamp')
            
            # Use a sliding window approach
            window_size = 12  # 1 hour (12 x 5-minute intervals)
            
            for i in range(len(equip_data_sorted)):
                # Get window of data
                start_idx = max(0, i - window_size + 1)
                window = equip_data_sorted.iloc[start_idx:i+1]
                
                # Calculate downtime frequency in window
                downtime_count = len(window[window['machine_status'] == 'Stopped'])
                downtime_frequency = downtime_count / len(window)
                
                # Identify most common downtime reason
                downtime_data = window[window['machine_status'] == 'Stopped']
                if len(downtime_data) > 0:
                    reason_counts = downtime_data['downtime_reason'].value_counts()
                    primary_reason = reason_counts.index[0] if len(reason_counts) > 0 else None
                else:
                    primary_reason = None
                
                observations.append(SensorObservation(
                    sensor_id=f"DTP-{equipment_id}",
                    equipment_id=equipment_id,
                    timestamp=equip_data_sorted.iloc[i]['timestamp'],
                    observable_property='downtime_frequency',
                    value=round(downtime_frequency, 3),
                    unit='ratio',
                    confidence=self.confidence,
                    metadata={
                        'window_size': len(window),
                        'downtime_events': downtime_count,
                        'primary_reason': primary_reason
                    }
                ))
                
        return observations


class VirtualSensorObserver:
    """Orchestrates all virtual sensors to observe production data."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the virtual sensor observer.
        
        Args:
            config: Configuration dictionary for sensors
        """
        self.config = config or {}
        
        # Initialize all virtual sensors
        self.sensors = [
            PowerMeterSensor(config),
            ThroughputSensor(config),
            DefectRateSensor(config),
            BottleneckDetector(config),
            LineCouplingMonitor(config),
            DowntimePatternSensor(config)
        ]
        
        logger.info(f"Initialized {len(self.sensors)} virtual sensors")
        
    def observe_production(self, production_data: pd.DataFrame, 
                          sensors: Optional[List[str]] = None) -> pd.DataFrame:
        """Run virtual sensors and collect observations.
        
        Args:
            production_data: DataFrame containing production data
            sensors: Optional list of sensor types to run (runs all if None)
            
        Returns:
            DataFrame of sensor observations
        """
        if production_data.empty:
            logger.warning("Empty production data provided to virtual sensors")
            return pd.DataFrame()
            
        all_observations = []
        sensors_to_run = self.sensors
        
        # Filter sensors if specific ones requested
        if sensors:
            sensors_to_run = [s for s in self.sensors if s.sensor_type in sensors]
            
        # Run each sensor
        for sensor in sensors_to_run:
            try:
                logger.debug(f"Running {sensor.sensor_type} sensor")
                observations = sensor.observe(production_data)
                all_observations.extend(observations)
                logger.debug(f"  Generated {len(observations)} observations")
            except Exception as e:
                logger.error(f"Error in {sensor.sensor_type} sensor: {e}")
                continue
                
        # Convert to DataFrame
        if all_observations:
            df = pd.DataFrame([{
                'sensor_id': obs.sensor_id,
                'equipment_id': obs.equipment_id,
                'timestamp': obs.timestamp,
                'observable_property': obs.observable_property,
                'value': obs.value,
                'unit': obs.unit,
                'confidence': obs.confidence,
                'metadata': str(obs.metadata) if obs.metadata else None
            } for obs in all_observations])
            
            logger.info(f"Generated {len(df)} total sensor observations")
            return df
        else:
            logger.warning("No sensor observations generated")
            return pd.DataFrame()
    
    def get_sensor_summary(self, observations_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics from sensor observations.
        
        Args:
            observations_df: DataFrame of sensor observations
            
        Returns:
            Dictionary of summary statistics
        """
        if observations_df.empty:
            return {}
            
        summary = {
            'total_observations': len(observations_df),
            'unique_sensors': observations_df['sensor_id'].nunique(),
            'unique_equipment': observations_df['equipment_id'].nunique(),
            'time_range': {
                'start': observations_df['timestamp'].min(),
                'end': observations_df['timestamp'].max()
            },
            'by_property': observations_df['observable_property'].value_counts().to_dict(),
            'avg_confidence': observations_df['confidence'].mean()
        }
        
        # Add property-specific summaries
        for prop in observations_df['observable_property'].unique():
            prop_data = observations_df[observations_df['observable_property'] == prop]
            summary[f'{prop}_stats'] = {
                'mean': prop_data['value'].mean(),
                'std': prop_data['value'].std(),
                'min': prop_data['value'].min(),
                'max': prop_data['value'].max()
            }
            
        return summary