"""Actionable Parameters Module for Virtual Twin
Defines the 5 tunable parameters that serve as proxies for real-world improvements
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Union
from enum import Enum
import json
import numpy as np
from numpy.typing import NDArray
from pathlib import Path
import os


class ParameterType(Enum):
    """Types of actionable parameters"""

    PROBABILITY = "probability"  # 0.0 to 1.0
    FACTOR = "factor"  # Multiplier
    RATE = "rate"  # Per unit time
    SENSITIVITY = "sensitivity"  # Response strength


@dataclass
class ActionableParameter:
    """A tunable parameter that can be adjusted in simulation to model operational changes
    """

    name: str
    description: str
    bounds: Tuple[float, float]
    default_value: float
    unit: str  # QUDT URI
    parameter_type: ParameterType
    causal_effect: str
    invariants: List[str] = field(default_factory=list)
    
    def validate(self, value: float) -> bool:
        """Check if value is within bounds"""
        return self.bounds[0] <= value <= self.bounds[1]
    
    def normalize(self, value: float) -> float:
        """Normalize value to [0, 1] range"""
        min_val, max_val = self.bounds
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)
    
    def denormalize(self, normalized: float) -> float:
        """Convert from [0, 1] back to parameter range"""
        min_val, max_val = self.bounds
        return min_val + normalized * (max_val - min_val)


class ActionableParameters:
    """The 5 key parameters that control virtual twin behavior
    These serve as proxies for real-world operational improvements
    
    Configuration is REQUIRED - all parameter definitions must come from config
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize actionable parameters from configuration.
        Configuration is required - will raise error if not available.
        
        Args:
            config_path: Optional path to JSON config file for parameter definitions.
                        If not provided, will use ConfigLoader.

        """
        if config_path:
            self.config = None
            self.parameters = self._load_parameters_from_config(config_path)
        else:
            # Always use ConfigLoader - no fallbacks
            from .config_loader import get_config
            self.config = get_config()  # Will raise error if config not available
            self.parameters = self._load_from_config_loader()
            
        self.current_values: Dict[str, float] = {
            p.name: p.default_value for p in self.parameters.values()
        }
        
    def _load_from_config_loader(self) -> Dict[str, ActionableParameter]:
        """Load parameters from ConfigLoader
        
        Returns:
            Dictionary of parameter name to ActionableParameter
            
        Raises:
            RuntimeError: If ConfigLoader not initialized
            KeyError: If required config keys are missing

        """
        if not self.config:
            raise RuntimeError("ConfigLoader not initialized")
            
        params_config = self.config.get_all_parameters()
        if not params_config:
            raise ValueError("No parameters defined in configuration")
            
        parameters: Dict[str, ActionableParameter] = {}
        
        for param_name, param_data in params_config.items():
            # All fields are required - no defaults
            try:
                # Get parameter type enum - required field
                type_str = param_data['type']
                param_type = ParameterType.FACTOR
                if type_str == 'probability':
                    param_type = ParameterType.PROBABILITY
                elif type_str == 'rate':
                    param_type = ParameterType.RATE
                elif type_str == 'sensitivity':
                    param_type = ParameterType.SENSITIVITY
                elif type_str == 'factor':
                    param_type = ParameterType.FACTOR
                else:
                    raise ValueError(f"Unknown parameter type: {type_str}")
                    
                parameters[param_name] = ActionableParameter(
                    name=param_name,
                    description=param_data['description'],  # Required
                    bounds=(
                        param_data['bounds']['min'],  # Required
                        param_data['bounds']['max']   # Required
                    ),
                    default_value=param_data['default'],  # Required
                    unit=param_data['unit'],  # Required
                    parameter_type=param_type,
                    causal_effect=param_data.get('causal_effect', ''),  # Optional
                    invariants=param_data.get('invariants', [])  # Optional
                )
            except KeyError as e:
                raise KeyError(f"Missing required field for parameter '{param_name}': {e}")
            
        return parameters
    
    
    def _load_parameters_from_config(self, config_path: str) -> Dict[str, ActionableParameter]:
        """Load parameter definitions from configuration file
        
        Args:
            config_path: Path to JSON configuration file
            
        Returns:
            Dictionary of parameter name to ActionableParameter
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON

        """
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        parameters: Dict[str, ActionableParameter] = {}
        for param_name, param_config in config.items():
            parameters[param_name] = ActionableParameter(
                name=param_name,
                description=param_config['description'],
                bounds=tuple(param_config['bounds']),
                default_value=param_config['default_value'],
                unit=param_config.get('unit', 'http://qudt.org/vocab/unit/UNITLESS'),
                parameter_type=ParameterType(param_config.get('type', 'factor')),
                causal_effect=param_config.get('causal_effect', ''),
                invariants=param_config.get('invariants', [])
            )
        return parameters
    
    def set_value(self, parameter_name: str, value: float) -> None:
        """Set the value of a parameter with validation
        
        Args:
            parameter_name: Name of the parameter to set
            value: New value for the parameter
            
        Raises:
            KeyError: If parameter_name is not recognized
            ValueError: If value is outside valid bounds

        """
        if parameter_name not in self.parameters:
            raise KeyError(f"Unknown parameter: {parameter_name}")
        
        param = self.parameters[parameter_name]
        if not param.validate(value):
            raise ValueError(
                f"Value {value} is outside bounds {param.bounds} for {parameter_name}"
            )
        
        self.current_values[parameter_name] = value
    
    def get_value(self, parameter_name: str) -> float:
        """Get the current value of a parameter
        
        Args:
            parameter_name: Name of the parameter
            
        Returns:
            Current value of the parameter
            
        Raises:
            KeyError: If parameter_name is not recognized

        """
        if parameter_name not in self.current_values:
            raise KeyError(f"Unknown parameter: {parameter_name}")
        return self.current_values[parameter_name]
    
    def get_all_values(self) -> Dict[str, float]:
        """Get all current parameter values"""
        return self.current_values.copy()
    
    def get_all(self) -> Dict[str, float]:
        """Alias for get_all_values() for backward compatibility"""
        return self.get_all_values()
    
    def reset(self, parameter_name: Optional[str] = None) -> None:
        """Reset parameter(s) to default values
        
        Args:
            parameter_name: Specific parameter to reset, or None to reset all

        """
        if parameter_name:
            if parameter_name not in self.parameters:
                raise KeyError(f"Unknown parameter: {parameter_name}")
            self.current_values[parameter_name] = self.parameters[parameter_name].default_value
        else:
            for name, param in self.parameters.items():
                self.current_values[name] = param.default_value
    
    def get_normalized_vector(self) -> NDArray[np.float64]:
        """Get all parameters as a normalized vector [0, 1]
        
        Returns:
            Numpy array of normalized parameter values

        """
        values: List[float] = []
        for name in sorted(self.parameters.keys()):
            param = self.parameters[name]
            normalized = param.normalize(self.current_values[name])
            values.append(normalized)
        return np.array(values, dtype=np.float64)
    
    def set_from_normalized_vector(self, vector: NDArray[np.float64]) -> None:
        """Set all parameters from a normalized vector
        
        Args:
            vector: Numpy array of normalized values [0, 1]
            
        Raises:
            ValueError: If vector length doesn't match number of parameters

        """
        param_names = sorted(self.parameters.keys())
        if len(vector) != len(param_names):
            raise ValueError(
                f"Vector length {len(vector)} doesn't match "
                f"number of parameters {len(param_names)}"
            )
        
        for i, name in enumerate(param_names):
            param = self.parameters[name]
            value = param.denormalize(float(vector[i]))
            self.current_values[name] = value
    
    def get_bounds_for_optimization(self) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Get parameter bounds as arrays for optimization algorithms
        
        Returns:
            Tuple of (lower_bounds, upper_bounds) as numpy arrays

        """
        lower_bounds: List[float] = []
        upper_bounds: List[float] = []
        
        for name in sorted(self.parameters.keys()):
            param = self.parameters[name]
            lower_bounds.append(param.bounds[0])
            upper_bounds.append(param.bounds[1])
        
        return (
            np.array(lower_bounds, dtype=np.float64),
            np.array(upper_bounds, dtype=np.float64)
        )
    
    def describe(self) -> str:
        """Get human-readable description of all parameters and their current values
        
        Returns:
            Formatted string describing all parameters

        """
        lines: List[str] = ["Actionable Parameters:"]
        lines.append("=" * 60)
        
        for name, param in self.parameters.items():
            current = self.current_values[name]
            lines.append(f"\n{name}:")
            lines.append(f"  Description: {param.description}")
            lines.append(f"  Current Value: {current:.3f}")
            lines.append(f"  Bounds: {param.bounds}")
            lines.append(f"  Default: {param.default_value}")
            lines.append(f"  Type: {param.parameter_type.value}")
            lines.append(f"  Effect: {param.causal_effect}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary representation
        
        Returns:
            Dictionary containing parameter definitions and current values

        """
        return {
            "parameters": {
                name: {
                    "description": param.description,
                    "bounds": param.bounds,
                    "default": param.default_value,
                    "current": self.current_values[name],
                    "unit": param.unit,
                    "type": param.parameter_type.value,
                    "effect": param.causal_effect,
                    "invariants": param.invariants
                }
                for name, param in self.parameters.items()
            }
        }
    
    def to_config_overlay(self) -> Dict[str, Any]:
        """Convert current values to configuration overlay format
        
        Returns:
            Dictionary in format expected by ConfigTransformer

        """
        config_overlay: Dict[str, Any] = {
            "equipment_configuration": {
                "lines": {}
            },
            "simulation_parameters": {},
            "product_specifications": {}
        }
        
        # Get available lines from config
        if self.config:
            available_lines = self.config.get("lines.available", [])
        else:
            # If using external config, assume standard lines
            available_lines = ["LINE1", "LINE2", "LINE3"]
        
        # Map micro_stop_probability
        if "micro_stop_probability" in self.current_values:
            prob = self.current_values["micro_stop_probability"]
            # Apply to all configured lines
            for line_key in available_lines:
                if line_key not in config_overlay["equipment_configuration"]["lines"]:
                    config_overlay["equipment_configuration"]["lines"][line_key] = {}
                config_overlay["equipment_configuration"]["lines"][line_key]["micro_stop_probability"] = prob
        
        # Map performance_factor
        if "performance_factor" in self.current_values:
            config_overlay["simulation_parameters"]["performance_factor"] = self.current_values["performance_factor"]
        
        # Map scrap_multiplier
        if "scrap_multiplier" in self.current_values:
            config_overlay["product_specifications"]["scrap_multiplier"] = self.current_values["scrap_multiplier"]
        
        # Map material_reliability
        if "material_reliability" in self.current_values:
            config_overlay["simulation_parameters"]["material_reliability"] = self.current_values["material_reliability"]
        
        # Map cascade_sensitivity
        if "cascade_sensitivity" in self.current_values:
            config_overlay["simulation_parameters"]["cascade_sensitivity"] = self.current_values["cascade_sensitivity"]
        
        return config_overlay
    
    def validate_all(self) -> Tuple[bool, List[str]]:
        """Validate all current parameter values
        
        Returns:
            Tuple of (is_valid, list_of_errors)

        """
        errors: List[str] = []
        
        for name, param in self.parameters.items():
            value = self.current_values[name]
            if not param.validate(value):
                errors.append(
                    f"{name}: Value {value} outside bounds {param.bounds}"
                )
        
        return len(errors) == 0, errors
    
    def __repr__(self) -> str:
        """String representation of ActionableParameters"""
        return f"ActionableParameters({list(self.parameters.keys())})"
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return self.describe()