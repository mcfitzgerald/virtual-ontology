"""Parameter effects module for simulation parameter management.

This module defines how simulation parameters affect the actual behavior
of equipment and other primitives in the virtual twin model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

import numpy as np


class ParameterCategory(Enum):
    """Categories of simulation parameters."""
    
    FAILURE = "failure"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SCHEDULING = "scheduling"
    MAINTENANCE = "maintenance"
    RESOURCE = "resource"


@dataclass
class ParameterEffect:
    """Defines how a parameter affects simulation behavior."""
    
    name: str
    category: ParameterCategory
    description: str
    base_value: float
    current_value: float
    unit: Optional[str] = None
    bounds: tuple[float, float] = (0.0, float('inf'))
    affects_primitives: List[str] = field(default_factory=list)
    application_function: Optional[Callable] = None


class ParameterEffectsManager:
    """Manages how simulation parameters affect model behavior.
    
    This class:
    1. Defines all simulation parameters
    2. Tracks current parameter values
    3. Applies parameters to primitives
    4. Validates parameter interactions
    5. Provides parameter recommendations
    """
    
    def __init__(self):
        """Initialize parameter effects manager."""
        self.parameters: Dict[str, ParameterEffect] = {}
        self._define_parameters()
    
    def _define_parameters(self) -> None:
        """Define all simulation parameters and their effects."""
        
        # ==================== FAILURE PARAMETERS ====================
        self.parameters['micro_stop_probability'] = ParameterEffect(
            name='micro_stop_probability',
            category=ParameterCategory.FAILURE,
            description='Probability of micro-stops per 5-minute interval',
            base_value=0.3,
            current_value=0.3,
            unit='probability',
            bounds=(0.05, 0.8),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['micro_stop_frequency'] = ParameterEffect(
            name='micro_stop_frequency',
            category=ParameterCategory.FAILURE,
            description='Frequency multiplier for micro-stops',
            base_value=1.0,
            current_value=1.0,
            unit='multiplier',
            bounds=(0.1, 5.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['micro_stop_recovery_time'] = ParameterEffect(
            name='micro_stop_recovery_time',
            category=ParameterCategory.FAILURE,
            description='Time multiplier for recovering from micro-stops',
            base_value=1.0,
            current_value=1.0,
            unit='multiplier',
            bounds=(0.3, 3.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['minor_failure_probability'] = ParameterEffect(
            name='minor_failure_probability',
            category=ParameterCategory.FAILURE,
            description='Probability of minor failures',
            base_value=0.05,
            current_value=0.05,
            unit='probability',
            bounds=(0.01, 0.3),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['major_failure_probability'] = ParameterEffect(
            name='major_failure_probability',
            category=ParameterCategory.FAILURE,
            description='Probability of major failures',
            base_value=0.02,
            current_value=0.02,
            unit='probability',
            bounds=(0.001, 0.1),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['mtbf'] = ParameterEffect(
            name='mtbf',
            category=ParameterCategory.FAILURE,
            description='Mean time between failures',
            base_value=480.0,
            current_value=480.0,
            unit='minutes',
            bounds=(10.0, 2880.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['mttr'] = ParameterEffect(
            name='mttr',
            category=ParameterCategory.FAILURE,
            description='Mean time to repair',
            base_value=30.0,
            current_value=30.0,
            unit='minutes',
            bounds=(1.0, 480.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        # ==================== PERFORMANCE PARAMETERS ====================
        self.parameters['performance_factor'] = ParameterEffect(
            name='performance_factor',
            category=ParameterCategory.PERFORMANCE,
            description='Equipment performance vs theoretical maximum',
            base_value=0.85,
            current_value=0.85,
            unit='ratio',
            bounds=(0.5, 1.2),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['base_rate'] = ParameterEffect(
            name='base_rate',
            category=ParameterCategory.PERFORMANCE,
            description='Base production rate',
            base_value=60.0,
            current_value=60.0,
            unit='units/minute',
            bounds=(10.0, 200.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['operator_skill_factor'] = ParameterEffect(
            name='operator_skill_factor',
            category=ParameterCategory.PERFORMANCE,
            description='Operator skill multiplier',
            base_value=1.0,
            current_value=1.0,
            unit='multiplier',
            bounds=(0.5, 1.5),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['equipment_wear_rate'] = ParameterEffect(
            name='equipment_wear_rate',
            category=ParameterCategory.PERFORMANCE,
            description='Equipment wear and degradation factor',
            base_value=1.0,
            current_value=1.0,
            unit='multiplier',
            bounds=(0.8, 2.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        # ==================== QUALITY PARAMETERS ====================
        self.parameters['scrap_rate'] = ParameterEffect(
            name='scrap_rate',
            category=ParameterCategory.QUALITY,
            description='Percentage of production scrapped',
            base_value=0.05,
            current_value=0.05,
            unit='ratio',
            bounds=(0.01, 0.3),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['false_reject_rate'] = ParameterEffect(
            name='false_reject_rate',
            category=ParameterCategory.QUALITY,
            description='Rate of false quality rejections',
            base_value=0.02,
            current_value=0.02,
            unit='ratio',
            bounds=(0.0, 0.1),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['setup_scrap_rate'] = ParameterEffect(
            name='setup_scrap_rate',
            category=ParameterCategory.QUALITY,
            description='Scrap rate during changeover/startup',
            base_value=0.15,
            current_value=0.15,
            unit='ratio',
            bounds=(0.05, 0.5),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        # ==================== SCHEDULING PARAMETERS ====================
        self.parameters['changeover_duration'] = ParameterEffect(
            name='changeover_duration',
            category=ParameterCategory.SCHEDULING,
            description='Time for product changeover',
            base_value=30.0,
            current_value=30.0,
            unit='minutes',
            bounds=(5.0, 120.0),
            affects_primitives=['EquipmentPrimitiveV2', 'SchedulerPrimitive']
        )
        
        self.parameters['changeover_frequency'] = ParameterEffect(
            name='changeover_frequency',
            category=ParameterCategory.SCHEDULING,
            description='Frequency of changeovers',
            base_value=1.0,
            current_value=1.0,
            unit='multiplier',
            bounds=(0.3, 2.0),
            affects_primitives=['SchedulerPrimitive']
        )
        
        self.parameters['schedule_adherence'] = ParameterEffect(
            name='schedule_adherence',
            category=ParameterCategory.SCHEDULING,
            description='How well production follows schedule',
            base_value=0.7,
            current_value=0.7,
            unit='ratio',
            bounds=(0.3, 0.95),
            affects_primitives=['SchedulerPrimitive']
        )
        
        self.parameters['inventory_variance'] = ParameterEffect(
            name='inventory_variance',
            category=ParameterCategory.SCHEDULING,
            description='Variance in inventory levels',
            base_value=1.0,
            current_value=1.0,
            unit='multiplier',
            bounds=(0.5, 3.0),
            affects_primitives=['SourcePrimitiveV2', 'SinkPrimitiveV2']
        )
        
        # ==================== MAINTENANCE PARAMETERS ====================
        self.parameters['maintenance_effectiveness'] = ParameterEffect(
            name='maintenance_effectiveness',
            category=ParameterCategory.MAINTENANCE,
            description='Effectiveness of maintenance activities',
            base_value=1.0,
            current_value=1.0,
            unit='multiplier',
            bounds=(0.5, 1.5),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['equipment_degradation_rate'] = ParameterEffect(
            name='equipment_degradation_rate',
            category=ParameterCategory.MAINTENANCE,
            description='Rate of equipment degradation',
            base_value=1.0,
            current_value=1.0,
            unit='multiplier',
            bounds=(0.5, 2.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['sensor_drift_factor'] = ParameterEffect(
            name='sensor_drift_factor',
            category=ParameterCategory.MAINTENANCE,
            description='Sensor calibration drift factor',
            base_value=1.0,
            current_value=1.0,
            unit='multiplier',
            bounds=(0.8, 2.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        # ==================== RESOURCE PARAMETERS ====================
        self.parameters['issue_response_time'] = ParameterEffect(
            name='issue_response_time',
            category=ParameterCategory.RESOURCE,
            description='Time to respond to issues',
            base_value=5.0,
            current_value=5.0,
            unit='minutes',
            bounds=(1.0, 30.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['break_coverage_factor'] = ParameterEffect(
            name='break_coverage_factor',
            category=ParameterCategory.RESOURCE,
            description='Coverage during operator breaks',
            base_value=0.7,
            current_value=0.7,
            unit='ratio',
            bounds=(0.0, 1.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
        
        self.parameters['parallel_task_capability'] = ParameterEffect(
            name='parallel_task_capability',
            category=ParameterCategory.RESOURCE,
            description='Ability to handle parallel tasks',
            base_value=0.5,
            current_value=0.5,
            unit='ratio',
            bounds=(0.0, 1.0),
            affects_primitives=['EquipmentPrimitiveV2']
        )
    
    def get_parameter(self, name: str) -> Optional[ParameterEffect]:
        """Get a parameter by name.
        
        Args:
            name: Parameter name
        
        Returns:
            ParameterEffect or None if not found
        """
        return self.parameters.get(name)
    
    def set_parameter_value(self, name: str, value: float) -> None:
        """Set a parameter value.
        
        Args:
            name: Parameter name
            value: New value
        
        Raises:
            ValueError: If parameter doesn't exist or value out of bounds
        """
        if name not in self.parameters:
            raise ValueError(f"Unknown parameter: {name}")
        
        param = self.parameters[name]
        min_val, max_val = param.bounds
        
        if value < min_val or value > max_val:
            raise ValueError(f"Value {value} out of bounds [{min_val}, {max_val}] for {name}")
        
        param.current_value = value
    
    def get_parameters_by_category(self, category: ParameterCategory) -> Dict[str, ParameterEffect]:
        """Get all parameters in a category.
        
        Args:
            category: Parameter category
        
        Returns:
            Dictionary of parameters in category
        """
        return {name: param for name, param in self.parameters.items() 
                if param.category == category}
    
    def get_parameters_for_primitive(self, primitive_type: str) -> Dict[str, ParameterEffect]:
        """Get parameters that affect a specific primitive type.
        
        Args:
            primitive_type: Type of primitive (e.g., 'EquipmentPrimitiveV2')
        
        Returns:
            Dictionary of relevant parameters
        """
        return {name: param for name, param in self.parameters.items()
                if primitive_type in param.affects_primitives}
    
    def apply_to_config(self, config: Dict[str, Any], primitive_type: str) -> Dict[str, Any]:
        """Apply current parameter values to a primitive configuration.
        
        Args:
            config: Primitive configuration dictionary
            primitive_type: Type of primitive
        
        Returns:
            Updated configuration with parameter values
        """
        relevant_params = self.get_parameters_for_primitive(primitive_type)
        
        for name, param in relevant_params.items():
            # Apply parameter value to config
            config[name] = param.current_value
        
        return config
    
    def update_from_control_manager(self, computed_parameters: Dict[str, float]) -> None:
        """Update parameter values from control manager output.
        
        Args:
            computed_parameters: Dictionary of computed parameter values
        """
        for name, value in computed_parameters.items():
            if name in self.parameters:
                try:
                    self.set_parameter_value(name, value)
                except ValueError as e:
                    # Log warning but continue
                    print(f"Warning: {e}")
    
    def get_all_current_values(self) -> Dict[str, float]:
        """Get current values of all parameters.
        
        Returns:
            Dictionary of parameter name to current value
        """
        return {name: param.current_value for name, param in self.parameters.items()}
    
    def reset_to_base_values(self) -> None:
        """Reset all parameters to their base values."""
        for param in self.parameters.values():
            param.current_value = param.base_value
    
    def validate_parameter_set(self) -> List[str]:
        """Validate current parameter set for conflicts or issues.
        
        Returns:
            List of validation warnings/errors
        """
        warnings = []
        
        # Check for conflicting parameters
        if self.parameters['micro_stop_probability'].current_value > 0.5 and \
           self.parameters['performance_factor'].current_value > 1.0:
            warnings.append("High micro-stop probability with high performance factor is unrealistic")
        
        if self.parameters['scrap_rate'].current_value > 0.2 and \
           self.parameters['operator_skill_factor'].current_value > 1.2:
            warnings.append("High scrap rate despite high operator skill is inconsistent")
        
        if self.parameters['mtbf'].current_value < 60 and \
           self.parameters['maintenance_effectiveness'].current_value > 1.2:
            warnings.append("Low MTBF despite high maintenance effectiveness is inconsistent")
        
        return warnings
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for parameter improvements.
        
        Returns:
            List of parameter adjustment recommendations
        """
        recommendations = []
        
        # Check for parameters that could be improved
        if self.parameters['micro_stop_probability'].current_value > 0.4:
            recommendations.append({
                'parameter': 'micro_stop_probability',
                'current': self.parameters['micro_stop_probability'].current_value,
                'recommended': 0.2,
                'reason': 'High micro-stop rate indicates need for sensor calibration or jam reduction',
                'expected_impact': 'Could improve OEE by 5-10%'
            })
        
        if self.parameters['changeover_duration'].current_value > 45:
            recommendations.append({
                'parameter': 'changeover_duration',
                'current': self.parameters['changeover_duration'].current_value,
                'recommended': 20,
                'reason': 'Long changeovers could benefit from SMED implementation',
                'expected_impact': 'Could reduce downtime by 25 minutes per changeover'
            })
        
        if self.parameters['scrap_rate'].current_value > 0.08:
            recommendations.append({
                'parameter': 'scrap_rate',
                'current': self.parameters['scrap_rate'].current_value,
                'recommended': 0.03,
                'reason': 'High scrap rate suggests quality control issues',
                'expected_impact': 'Could improve quality rate by 5%'
            })
        
        return recommendations