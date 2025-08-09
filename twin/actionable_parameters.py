"""
Actionable Parameters Module for Virtual Twin
Defines the 5 tunable parameters that serve as proxies for real-world improvements
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import json
import numpy as np


class ParameterType(Enum):
    """Types of actionable parameters"""
    PROBABILITY = "probability"  # 0.0 to 1.0
    FACTOR = "factor"  # Multiplier
    RATE = "rate"  # Per unit time
    SENSITIVITY = "sensitivity"  # Response strength


@dataclass
class ActionableParameter:
    """
    A tunable parameter that can be adjusted in simulation to model operational changes
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
        return (value - min_val) / (max_val - min_val)
    
    def denormalize(self, normalized: float) -> float:
        """Convert from [0, 1] back to parameter range"""
        min_val, max_val = self.bounds
        return min_val + normalized * (max_val - min_val)


class ActionableParameters:
    """
    The 5 key parameters that control virtual twin behavior
    These serve as proxies for real-world operational improvements
    """
    
    def __init__(self):
        self.parameters = self._initialize_parameters()
        self.current_values = {p.name: p.default_value for p in self.parameters.values()}
        
    def _initialize_parameters(self) -> Dict[str, ActionableParameter]:
        """Initialize the 5 actionable parameters"""
        return {
            "micro_stop_probability": ActionableParameter(
                name="micro_stop_probability",
                description="Probability of micro-stops (proxy for equipment maintenance quality)",
                bounds=(0.05, 0.50),
                default_value=0.20,
                unit="http://qudt.org/vocab/unit/UNITLESS",  # Probability is dimensionless
                parameter_type=ParameterType.PROBABILITY,
                causal_effect="Higher values reduce availability score",
                invariants=[
                    "Must be between 0.05 and 0.50",
                    "Affects all equipment types",
                    "Inversely correlated with maintenance quality"
                ]
            ),
            
            "performance_factor": ActionableParameter(
                name="performance_factor",
                description="Performance multiplier (proxy for operator skill and equipment calibration)",
                bounds=(0.50, 1.00),
                default_value=0.85,
                unit="http://qudt.org/vocab/unit/UNITLESS",
                parameter_type=ParameterType.FACTOR,
                causal_effect="Scales actual throughput vs target throughput",
                invariants=[
                    "Must be between 0.50 and 1.00",
                    "1.0 means ideal performance",
                    "Affected by operator training and equipment condition"
                ]
            ),
            
            "scrap_multiplier": ActionableParameter(
                name="scrap_multiplier",
                description="Scrap rate multiplier (proxy for quality control procedures)",
                bounds=(1.0, 5.0),
                default_value=2.0,
                unit="http://qudt.org/vocab/unit/UNITLESS",
                parameter_type=ParameterType.FACTOR,
                causal_effect="Increases defect rate, reduces quality score",
                invariants=[
                    "Must be >= 1.0",
                    "Multiplies base scrap rate",
                    "Lower is better"
                ]
            ),
            
            "material_reliability": ActionableParameter(
                name="material_reliability",
                description="Material batch reliability (proxy for supply chain coordination)",
                bounds=(0.50, 1.00),
                default_value=0.85,
                unit="http://qudt.org/vocab/unit/UNITLESS",
                parameter_type=ParameterType.PROBABILITY,
                causal_effect="Probability of receiving good material batch",
                invariants=[
                    "Must be between 0.50 and 1.00",
                    "Affects material starvation events",
                    "Improved by better supplier coordination"
                ]
            ),
            
            "cascade_sensitivity": ActionableParameter(
                name="cascade_sensitivity",
                description="Line coupling strength (proxy for buffer capacity)",
                bounds=(0.0, 1.0),
                default_value=0.5,
                unit="http://qudt.org/vocab/unit/UNITLESS",
                parameter_type=ParameterType.SENSITIVITY,
                causal_effect="Controls propagation of blockages and starvation",
                invariants=[
                    "0.0 means no cascade (infinite buffers)",
                    "1.0 means immediate cascade (no buffers)",
                    "Affects downstream equipment when upstream stops"
                ]
            )
        }
    
    def get_parameter(self, name: str) -> ActionableParameter:
        """Get a specific parameter by name"""
        if name not in self.parameters:
            raise ValueError(f"Unknown parameter: {name}")
        return self.parameters[name]
    
    def set_value(self, name: str, value: float) -> None:
        """Set a parameter value with validation"""
        param = self.get_parameter(name)
        if not param.validate(value):
            raise ValueError(
                f"Value {value} out of bounds [{param.bounds[0]}, {param.bounds[1]}] "
                f"for parameter {name}"
            )
        self.current_values[name] = value
    
    def get_value(self, name: str) -> float:
        """Get current value of a parameter"""
        return self.current_values[name]
    
    def get_all_values(self) -> Dict[str, float]:
        """Get all current parameter values"""
        return self.current_values.copy()
    
    def set_all_values(self, values: Dict[str, float]) -> None:
        """Set multiple parameter values at once"""
        for name, value in values.items():
            self.set_value(name, value)
    
    def reset_to_defaults(self) -> None:
        """Reset all parameters to default values"""
        for param in self.parameters.values():
            self.current_values[param.name] = param.default_value
    
    def get_normalized_vector(self) -> np.ndarray:
        """Get parameters as normalized vector for optimization"""
        vector = []
        for name in sorted(self.parameters.keys()):
            param = self.parameters[name]
            value = self.current_values[name]
            normalized = param.normalize(value)
            vector.append(normalized)
        return np.array(vector)
    
    def set_from_normalized_vector(self, vector: np.ndarray) -> None:
        """Set parameters from normalized optimization vector"""
        if len(vector) != len(self.parameters):
            raise ValueError(f"Vector length {len(vector)} doesn't match parameter count {len(self.parameters)}")
        
        for i, name in enumerate(sorted(self.parameters.keys())):
            param = self.parameters[name]
            denormalized = param.denormalize(vector[i])
            self.current_values[name] = denormalized
    
    def get_bounds_for_optimization(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get lower and upper bounds as numpy arrays for optimization"""
        lower = []
        upper = []
        for name in sorted(self.parameters.keys()):
            param = self.parameters[name]
            lower.append(param.bounds[0])
            upper.append(param.bounds[1])
        return np.array(lower), np.array(upper)
    
    def calculate_impact(self, parameter_name: str, change_percent: float) -> Dict[str, float]:
        """
        Calculate expected impact of changing a parameter
        
        Args:
            parameter_name: Name of parameter to change
            change_percent: Percentage change (-100 to +100)
            
        Returns:
            Dictionary of expected KPI impacts
        """
        param = self.get_parameter(parameter_name)
        current = self.current_values[parameter_name]
        
        # Calculate new value
        change_factor = 1 + (change_percent / 100)
        new_value = current * change_factor
        
        # Clamp to bounds
        new_value = max(param.bounds[0], min(param.bounds[1], new_value))
        
        # Estimate impacts based on causal relationships
        impacts = {}
        
        if parameter_name == "micro_stop_probability":
            # Micro-stops directly affect availability
            availability_impact = -50 * (new_value - current)  # -50% availability per unit increase
            impacts["availability"] = availability_impact
            impacts["oee"] = availability_impact * 0.33  # OEE is product of 3 factors
            
        elif parameter_name == "performance_factor":
            # Performance factor directly scales throughput
            performance_impact = 100 * (new_value - current)
            impacts["performance"] = performance_impact
            impacts["oee"] = performance_impact * 0.33
            
        elif parameter_name == "scrap_multiplier":
            # Scrap affects quality score
            quality_impact = -20 * (new_value - current)  # -20% quality per unit increase
            impacts["quality"] = quality_impact
            impacts["oee"] = quality_impact * 0.33
            
        elif parameter_name == "material_reliability":
            # Material reliability affects starvation events
            availability_impact = 30 * (new_value - current)  # 30% availability per unit increase
            impacts["availability"] = availability_impact
            impacts["oee"] = availability_impact * 0.33
            
        elif parameter_name == "cascade_sensitivity":
            # Cascade affects downstream availability
            cascade_impact = -15 * (new_value - current)  # -15% availability per unit increase
            impacts["availability"] = cascade_impact
            impacts["oee"] = cascade_impact * 0.33
        
        return impacts
    
    def to_config_overlay(self) -> Dict[str, Any]:
        """
        Convert current parameters to config overlay for data generator
        
        Returns:
            Dictionary that can be merged with mes_data_config.json
        """
        config_overlay = {
            "anomaly_injection": {}
        }
        
        # Map micro_stop_probability to specific equipment patterns
        micro_stop_prob = self.current_values["micro_stop_probability"]
        config_overlay["anomaly_injection"]["frequent_micro_stops"] = {
            "enabled": True,
            "probability_per_5min": micro_stop_prob,
            "description": f"Micro-stops with probability {micro_stop_prob}"
        }
        
        # Map performance_factor to equipment efficiency
        perf_factor = self.current_values["performance_factor"]
        config_overlay["product_specifications"] = {
            "equipment_efficiency": {
                "Filler": {"min": perf_factor * 0.75, "max": perf_factor * 0.92},
                "Packer": {"min": perf_factor * 0.70, "max": perf_factor * 0.90},
                "Palletizer": {"min": perf_factor * 0.80, "max": perf_factor * 0.95}
            }
        }
        
        # Map scrap_multiplier
        scrap_mult = self.current_values["scrap_multiplier"]
        config_overlay["anomaly_injection"]["quality_variation_normal"] = {
            "enabled": True,
            "scrap_rate_multiplier": scrap_mult,
            "description": f"Quality variation with multiplier {scrap_mult}"
        }
        
        # Map material_reliability to starvation patterns
        mat_reliability = self.current_values["material_reliability"]
        starvation_prob = 1.0 - mat_reliability  # Inverse relationship
        config_overlay["anomaly_injection"]["material_starvation_patterns"] = {
            "enabled": True,
            "probability_modifier": starvation_prob,
            "description": f"Material issues with probability {starvation_prob}"
        }
        
        # Map cascade_sensitivity
        cascade_sens = self.current_values["cascade_sensitivity"]
        config_overlay["anomaly_injection"]["cascade_failures"] = {
            "enabled": True,
            "downstream_stop_probability": cascade_sens,
            "description": f"Cascade sensitivity {cascade_sens}"
        }
        
        return config_overlay
    
    def describe(self) -> str:
        """Generate human-readable description of current parameter settings"""
        lines = ["ACTIONABLE PARAMETERS CONFIGURATION", "=" * 50]
        
        for name in sorted(self.parameters.keys()):
            param = self.parameters[name]
            value = self.current_values[name]
            normalized = param.normalize(value)
            
            lines.append(f"\n{param.name}:")
            lines.append(f"  Description: {param.description}")
            lines.append(f"  Current Value: {value:.3f} ({normalized*100:.1f}% of range)")
            lines.append(f"  Bounds: [{param.bounds[0]}, {param.bounds[1]}]")
            lines.append(f"  Causal Effect: {param.causal_effect}")
        
        return "\n".join(lines)


def demonstrate_parameters():
    """Demonstrate actionable parameters"""
    params = ActionableParameters()
    
    print(params.describe())
    
    print("\n\nSETTING IMPROVED MAINTENANCE SCENARIO:")
    print("-" * 50)
    
    # Simulate improved maintenance
    params.set_value("micro_stop_probability", 0.10)  # Reduce from 0.20 to 0.10
    params.set_value("performance_factor", 0.95)  # Improve from 0.85 to 0.95
    
    print(f"Micro-stop probability: {params.get_value('micro_stop_probability')}")
    print(f"Performance factor: {params.get_value('performance_factor')}")
    
    # Calculate impacts
    print("\nEXPECTED IMPACTS:")
    micro_stop_impact = params.calculate_impact("micro_stop_probability", -50)  # 50% reduction
    print(f"Reducing micro-stops by 50%: {micro_stop_impact}")
    
    perf_impact = params.calculate_impact("performance_factor", 11.76)  # From 0.85 to 0.95
    print(f"Improving performance by 11.76%: {perf_impact}")
    
    # Generate config overlay
    print("\nCONFIG OVERLAY FOR SIMULATION:")
    print(json.dumps(params.to_config_overlay(), indent=2))


if __name__ == "__main__":
    demonstrate_parameters()