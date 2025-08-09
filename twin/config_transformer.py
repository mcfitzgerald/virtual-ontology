"""
Config Transformer Module
Maps actionable parameters to mes_data_config.json for simulation
"""

import json
import copy
from typing import Dict, Any, Optional
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from actionable_parameters import ActionableParameters


class ConfigTransformer:
    """
    Transforms actionable parameters into configuration overlays
    for the MES data generator
    """
    
    def __init__(self, base_config_path: str = "synthetic_data_generator/mes_data_config.json"):
        self.base_config_path = Path(base_config_path)
        self.base_config = self._load_base_config()
        
    def _load_base_config(self) -> Dict[str, Any]:
        """Load the base MES configuration"""
        with open(self.base_config_path, 'r') as f:
            return json.load(f)
    
    def apply_parameters(
        self, 
        parameters: ActionableParameters,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply actionable parameters to create a new configuration
        
        Args:
            parameters: ActionableParameters instance with current values
            save_path: Optional path to save the transformed config
            
        Returns:
            Transformed configuration dictionary
        """
        # Start with a deep copy of base config
        config = copy.deepcopy(self.base_config)
        
        # Get parameter values
        values = parameters.get_all_values()
        
        # 1. Apply micro_stop_probability
        micro_stop_prob = values["micro_stop_probability"]
        
        # Update frequent micro-stops
        config["anomaly_injection"]["frequent_micro_stops"]["probability_per_5min"] = micro_stop_prob
        config["anomaly_injection"]["frequent_micro_stops"]["description"] = (
            f"Micro-stops with probability {micro_stop_prob:.2f} (adjusted by virtual twin)"
        )
        
        # Update minor stops on Line 1
        config["anomaly_injection"]["minor_stops_line1"]["probability_per_5min"] = micro_stop_prob * 0.8
        
        # Update recurring jams
        config["anomaly_injection"]["recurring_jams_line1"]["probability_per_5min"] = micro_stop_prob * 0.75
        
        # Update filler micro-stops
        for pattern in config["anomaly_injection"]["filler_micro_stops"]["equipment_patterns"]:
            pattern["probability_per_5min"] = micro_stop_prob * 0.5
        
        # Update palletizer micro-stops
        for pattern in config["anomaly_injection"]["palletizer_micro_stops"]["equipment_patterns"]:
            pattern["probability_per_5min"] = micro_stop_prob * 0.25
        
        # 2. Apply performance_factor
        perf_factor = values["performance_factor"]
        
        # Update equipment efficiency ranges
        config["product_specifications"]["equipment_efficiency"] = {
            "Filler": {
                "min": max(0.5, perf_factor * 0.88),  # Scale from base
                "max": min(1.0, perf_factor * 1.08)
            },
            "Packer": {
                "min": max(0.5, perf_factor * 0.82),
                "max": min(1.0, perf_factor * 1.06)
            },
            "Palletizer": {
                "min": max(0.5, perf_factor * 0.94),
                "max": min(1.0, perf_factor * 1.12)
            }
        }
        
        # Update shift performance variations
        config["product_specifications"]["performance_variation"] = {
            "shift1": {"min": perf_factor * 0.95, "max": min(1.0, perf_factor * 1.05)},
            "shift2": {"min": perf_factor * 0.90, "max": perf_factor},
            "shift3": {"min": perf_factor * 0.85, "max": perf_factor * 0.95}
        }
        
        # Update random performance drops
        config["product_specifications"]["random_performance_drops"]["degradation_factor"] = {
            "min": max(0.3, perf_factor * 0.70),
            "max": perf_factor * 0.94
        }
        
        # 3. Apply scrap_multiplier
        scrap_mult = values["scrap_multiplier"]
        
        # Update quality variations
        config["anomaly_injection"]["quality_variation_normal"]["scrap_rate_multiplier"] = scrap_mult
        
        # Update end-of-run quality degradation
        config["anomaly_injection"]["quality_end_of_run"]["scrap_rate_multiplier"] = scrap_mult * 1.5
        
        # Update changeover scrap spike
        config["anomaly_injection"]["changeover_scrap_spike"]["scrap_multiplier"] = scrap_mult * 1.5
        
        # Update product-specific scrap rates
        for sku, product_data in config["product_master"].items():
            if "normal_scrap_rate" in product_data:
                # Apply multiplier but keep reasonable bounds
                base_rate = product_data["normal_scrap_rate"]
                product_data["normal_scrap_rate"] = min(0.15, base_rate * scrap_mult)
            if "startup_scrap_rate" in product_data:
                base_rate = product_data["startup_scrap_rate"]
                product_data["startup_scrap_rate"] = min(0.20, base_rate * scrap_mult)
        
        # 4. Apply material_reliability
        mat_reliability = values["material_reliability"]
        starvation_prob = max(0.01, (1.0 - mat_reliability) * 0.5)  # Scale down for realism
        
        # Update material starvation patterns
        for pattern in config["anomaly_injection"]["material_starvation_patterns"]["equipment_patterns"]:
            pattern["probability_per_5min"] = starvation_prob
        
        # 5. Apply cascade_sensitivity
        cascade_sens = values["cascade_sensitivity"]
        
        # Update cascade failure probability
        config["anomaly_injection"]["cascade_failures"]["downstream_stop_probability"] = cascade_sens
        config["anomaly_injection"]["cascade_failures"]["cascade_delay_minutes"] = int(10 * (1 - cascade_sens) + 1)
        
        # Add metadata about transformation
        from datetime import datetime
        config["twin_metadata"] = {
            "transformed_by": "virtual_twin",
            "parameters_applied": values,
            "transformation_timestamp": datetime.now().isoformat()
        }
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(config, f, indent=2)
        
        return config
    
    def create_scenario(
        self,
        scenario_name: str,
        parameter_changes: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Create a specific scenario configuration
        
        Args:
            scenario_name: Name of the scenario
            parameter_changes: Dictionary of parameter names and their new values
            
        Returns:
            Scenario configuration
        """
        # Create parameters instance
        params = ActionableParameters()
        
        # Apply changes
        for name, value in parameter_changes.items():
            params.set_value(name, value)
        
        # Transform config
        config = self.apply_parameters(params)
        
        # Add scenario metadata
        config["scenario"] = {
            "name": scenario_name,
            "description": f"Virtual twin scenario: {scenario_name}",
            "parameter_changes": parameter_changes
        }
        
        return config
    
    def create_optimization_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """
        Create standard optimization scenarios for comparison
        
        Returns:
            Dictionary of scenario configurations
        """
        scenarios = {}
        
        # Baseline scenario
        params_baseline = ActionableParameters()
        scenarios["baseline"] = {
            "config": self.apply_parameters(params_baseline),
            "description": "Current state baseline",
            "parameters": params_baseline.get_all_values()
        }
        
        # Improved maintenance scenario
        scenarios["improved_maintenance"] = self.create_scenario(
            "Improved Maintenance",
            {
                "micro_stop_probability": 0.10,  # 50% reduction
                "performance_factor": 0.90  # Small improvement
            }
        )
        
        # Better quality control scenario
        scenarios["better_quality"] = self.create_scenario(
            "Better Quality Control",
            {
                "scrap_multiplier": 1.2,  # 40% reduction from default 2.0
                "performance_factor": 0.85  # Maintain current
            }
        )
        
        # Optimized supply chain scenario
        scenarios["optimized_supply"] = self.create_scenario(
            "Optimized Supply Chain",
            {
                "material_reliability": 0.95,  # Improve from 0.85
                "cascade_sensitivity": 0.3  # Reduce from 0.5
            }
        )
        
        # Best case scenario (all improvements)
        scenarios["best_case"] = self.create_scenario(
            "Best Case - All Improvements",
            {
                "micro_stop_probability": 0.08,
                "performance_factor": 0.95,
                "scrap_multiplier": 1.1,
                "material_reliability": 0.98,
                "cascade_sensitivity": 0.2
            }
        )
        
        # Worst case scenario (degraded performance)
        scenarios["worst_case"] = self.create_scenario(
            "Worst Case - Degraded Performance",
            {
                "micro_stop_probability": 0.35,
                "performance_factor": 0.60,
                "scrap_multiplier": 3.5,
                "material_reliability": 0.60,
                "cascade_sensitivity": 0.8
            }
        )
        
        return scenarios


def demonstrate_config_transformation():
    """Demonstrate configuration transformation"""
    transformer = ConfigTransformer()
    
    print("CONFIGURATION TRANSFORMER DEMONSTRATION")
    print("=" * 60)
    
    # Create and show scenarios
    scenarios = transformer.create_optimization_scenarios()
    
    for scenario_name, scenario_data in scenarios.items():
        if isinstance(scenario_data, dict) and "parameters" in scenario_data:
            params = scenario_data["parameters"]
        elif isinstance(scenario_data, dict) and "scenario" in scenario_data:
            params = scenario_data["scenario"]["parameter_changes"]
        else:
            params = {}
        
        print(f"\nScenario: {scenario_name}")
        print("-" * 40)
        
        if params:
            for param_name, value in params.items():
                print(f"  {param_name}: {value:.3f}")
    
    # Save a specific scenario
    improved_maintenance = scenarios["improved_maintenance"]
    save_path = "twin/scenario_improved_maintenance.json"
    
    with open(save_path, 'w') as f:
        json.dump(improved_maintenance, f, indent=2)
    
    print(f"\nSaved improved maintenance scenario to: {save_path}")
    
    # Show impact on specific config sections
    print("\nIMPACT ON KEY CONFIG SECTIONS:")
    print("-" * 40)
    
    baseline = scenarios["baseline"]["config"] if "config" in scenarios["baseline"] else scenarios["baseline"]
    improved = scenarios["improved_maintenance"]
    
    if "anomaly_injection" in baseline and "anomaly_injection" in improved:
        print("\nMicro-stop probability changes:")
        print(f"  Baseline: {baseline['anomaly_injection']['frequent_micro_stops']['probability_per_5min']:.3f}")
        print(f"  Improved: {improved['anomaly_injection']['frequent_micro_stops']['probability_per_5min']:.3f}")
    
    if "product_specifications" in baseline and "product_specifications" in improved:
        print("\nEquipment efficiency (Filler) changes:")
        print(f"  Baseline: {baseline['product_specifications']['equipment_efficiency']['Filler']}")
        print(f"  Improved: {improved['product_specifications']['equipment_efficiency']['Filler']}")


if __name__ == "__main__":
    demonstrate_config_transformation()