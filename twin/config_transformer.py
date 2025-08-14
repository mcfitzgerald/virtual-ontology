"""Config Transformer Module
Maps actionable parameters to mes_data_config.json for simulation
"""

import json
import copy
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from .actionable_parameters import ActionableParameters
from .config_manager import ConfigurationManager
from .config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class ConfigTransformer:
    """Transforms actionable parameters into configuration overlays
    for the MES data generator
    """
    
    def __init__(self, 
                 base_config_path: Optional[str] = None,
                 db_path: Optional[str] = None) -> None:
        """Initialize the ConfigTransformer.
        
        Args:
            base_config_path: Path to base MES data config. If None, uses path from configuration.
            db_path: Path to SQLite database. If None, uses path from configuration.
            
        Raises:
            KeyError: If required paths not found in configuration.

        """
        self.loader = ConfigLoader()
        self.config = self.loader.config
        
        if base_config_path is None:
            base_config_path = self.config["paths"]["base_config"]
        if db_path is None:
            db_path = self.config["database"]["path"]
            
        self.base_config_path: Path = Path(base_config_path)
        self.base_config: Dict[str, Any] = self._load_base_config()
        self.config_manager: ConfigurationManager = ConfigurationManager(db_path)
        
    def _load_base_config(self) -> Dict[str, Any]:
        """Load the base MES configuration"""
        with open(self.base_config_path, 'r') as f:
            return json.load(f)
    
    def apply_parameters(
        self, 
        parameters: ActionableParameters,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Apply actionable parameters to create a new configuration
        
        Args:
            parameters: ActionableParameters instance with current values
            save_path: Optional path to save the transformed config
            
        Returns:
            Transformed configuration dictionary

        """
        # Start with a deep copy of base config
        config: Dict[str, Any] = copy.deepcopy(self.base_config)
        
        # Get parameter values
        values: Dict[str, float] = parameters.get_all_values()
        
        # 1. Apply micro_stop_probability
        micro_stop_prob: float = values["micro_stop_probability"]
        
        # Update frequent micro-stops
        config["anomaly_injection"]["frequent_micro_stops"]["probability_per_5min"] = micro_stop_prob
        config["anomaly_injection"]["frequent_micro_stops"]["description"] = (
            f"Micro-stops with probability {micro_stop_prob:.2f} (adjusted by virtual twin)"
        )
        
        # Update minor stops on Line 1  
        config["anomaly_injection"]["minor_stops_line1"]["probability_per_5min"] = micro_stop_prob * self.config["micro_stops"]["minor_stops_line1_multiplier"]
        
        # Update recurring jams
        config["anomaly_injection"]["recurring_jams_line1"]["probability_per_5min"] = micro_stop_prob * self.config["micro_stops"]["recurring_jams_line1_multiplier"]
        
        # Update filler micro-stops
        for pattern in config["anomaly_injection"]["filler_micro_stops"]["equipment_patterns"]:
            pattern["probability_per_5min"] = micro_stop_prob * self.config["micro_stops"]["filler_micro_stops_multiplier"]
        
        # Update palletizer micro-stops
        for pattern in config["anomaly_injection"]["palletizer_micro_stops"]["equipment_patterns"]:
            pattern["probability_per_5min"] = micro_stop_prob * self.config["micro_stops"]["palletizer_micro_stops_multiplier"]
        
        # 2. Apply performance_factor
        perf_factor: float = values["performance_factor"]
        
        # Update equipment efficiency ranges
        config["product_specifications"]["equipment_efficiency"] = {
            "Filler": {
                "min": max(0.5, perf_factor * self.config["equipment_multipliers"]["efficiency"]["filler"]["min_multiplier"]),
                "max": min(1.0, perf_factor * self.config["equipment_multipliers"]["efficiency"]["filler"]["max_multiplier"])
            },
            "Packer": {
                "min": max(0.5, perf_factor * self.config["equipment_multipliers"]["efficiency"]["packer"]["min_multiplier"]),
                "max": min(1.0, perf_factor * self.config["equipment_multipliers"]["efficiency"]["packer"]["max_multiplier"])
            },
            "Palletizer": {
                "min": max(0.5, perf_factor * self.config["equipment_multipliers"]["efficiency"]["palletizer"]["min_multiplier"]),
                "max": min(1.0, perf_factor * self.config["equipment_multipliers"]["efficiency"]["palletizer"]["max_multiplier"])
            }
        }
        
        # Update shift performance variations
        config["product_specifications"]["performance_variation"] = {
            "shift1": {"min": perf_factor * self.config["equipment_multipliers"]["shift_performance"]["shift1"]["min_multiplier"], "max": min(1.0, perf_factor * self.config["equipment_multipliers"]["shift_performance"]["shift1"]["max_multiplier"])},
            "shift2": {"min": perf_factor * self.config["equipment_multipliers"]["shift_performance"]["shift2"]["min_multiplier"], "max": perf_factor * self.config["equipment_multipliers"]["shift_performance"]["shift2"]["max_multiplier"]},
            "shift3": {"min": perf_factor * self.config["equipment_multipliers"]["shift_performance"]["shift3"]["min_multiplier"], "max": perf_factor * self.config["equipment_multipliers"]["shift_performance"]["shift3"]["max_multiplier"]}
        }
        
        # Update random performance drops
        config["product_specifications"]["random_performance_drops"]["degradation_factor"] = {
            "min": max(self.config["equipment_multipliers"]["performance_degradation"]["floor"], perf_factor * self.config["equipment_multipliers"]["performance_degradation"]["min_multiplier"]),
            "max": perf_factor * self.config["equipment_multipliers"]["performance_degradation"]["max_multiplier"]
        }
        
        # 3. Apply scrap_multiplier
        scrap_mult: float = values["scrap_multiplier"]
        
        # Update quality variations
        config["anomaly_injection"]["quality_variation_normal"]["scrap_rate_multiplier"] = scrap_mult
        
        # Update end-of-run quality degradation
        config["anomaly_injection"]["quality_end_of_run"]["scrap_rate_multiplier"] = scrap_mult * self.config["scrap_rates"]["end_of_run_multiplier"]
        
        # Update changeover scrap spike
        config["anomaly_injection"]["changeover_scrap_spike"]["scrap_multiplier"] = scrap_mult * self.config["scrap_rates"]["changeover_spike_multiplier"]
        
        # Update product-specific scrap rates
        for sku, product_data in config["product_master"].items():
            if "normal_scrap_rate" in product_data:
                # Apply multiplier but keep reasonable bounds
                base_rate: float = product_data["normal_scrap_rate"]
                product_data["normal_scrap_rate"] = min(self.config["scrap_rates"]["normal_scrap_max"], base_rate * scrap_mult)
            if "startup_scrap_rate" in product_data:
                startup_rate: float = product_data["startup_scrap_rate"]
                product_data["startup_scrap_rate"] = min(self.config["scrap_rates"]["startup_scrap_max"], startup_rate * scrap_mult)
        
        # 4. Apply material_reliability
        mat_reliability: float = values["material_reliability"]
        starvation_prob: float = max(self.config["material_cascade"]["starvation_prob_min"], (1.0 - mat_reliability) * self.config["material_cascade"]["starvation_prob_multiplier"])
        
        # Update material starvation patterns
        for pattern in config["anomaly_injection"]["material_starvation_patterns"]["equipment_patterns"]:
            pattern["probability_per_5min"] = starvation_prob
        
        # 5. Apply cascade_sensitivity
        cascade_sens: float = values["cascade_sensitivity"]
        
        # Update cascade failure probability
        config["anomaly_injection"]["cascade_failures"]["downstream_stop_probability"] = cascade_sens
        config["anomaly_injection"]["cascade_failures"]["cascade_delay_minutes"] = int(self.config["material_cascade"]["cascade_delay_base"] * (1 - cascade_sens) + self.config["material_cascade"]["cascade_delay_offset"])
        
        # Add metadata about transformation
        from datetime import datetime
        config["twin_metadata"] = {
            "transformed_by": "virtual_twin",
            "parameters_applied": values,
            "transformation_timestamp": datetime.now().isoformat()
        }
        
        # Save to database if path provided (for backward compatibility)
        if save_path:
            # Save to database
            config_id: str = self.config_manager.store_config(
                config,
                config_type='full',
                description=f"Parameters applied: {values}"
            )
            logger.info(f"Stored config in database: {config_id}")
            
            # Also save to file if explicit path given (for compatibility)
            if save_path != 'auto':
                with open(save_path, 'w') as f:
                    json.dump(config, f, indent=2)
                logger.info(f"Also saved to file: {save_path}")
        
        return config
    
    def create_scenario(
        self,
        scenario_name: str,
        parameter_changes: Dict[str, float]
    ) -> Dict[str, Any]:
        """Create a specific scenario configuration
        
        Args:
            scenario_name: Name of the scenario
            parameter_changes: Dictionary of parameter names and their new values
            
        Returns:
            Scenario configuration

        """
        # Create parameters instance
        params: ActionableParameters = ActionableParameters()
        
        # Apply changes
        for name, value in parameter_changes.items():
            params.set_value(name, value)
        
        # Transform config
        config: Dict[str, Any] = self.apply_parameters(params)
        
        # Add scenario metadata
        config["scenario"] = {
            "name": scenario_name,
            "description": f"Virtual twin scenario: {scenario_name}",
            "parameter_changes": parameter_changes
        }
        
        return config
    
    def create_optimization_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Create standard optimization scenarios for comparison
        
        Returns:
            Dictionary of scenario configurations

        """
        scenarios: Dict[str, Dict[str, Any]] = {}
        
        # Baseline scenario
        params_baseline: ActionableParameters = ActionableParameters()
        scenarios["baseline"] = {
            "config": self.apply_parameters(params_baseline),
            "description": "Current state baseline",
            "parameters": params_baseline.get_all_values()
        }
        
        # Improved maintenance scenario
        scenarios["improved_maintenance"] = self.create_scenario(
            "Improved Maintenance",
            self.config["scenarios"]["improved_maintenance"]
        )
        
        # Better quality control scenario
        scenarios["better_quality"] = self.create_scenario(
            "Better Quality Control",
            self.config["scenarios"]["better_quality"]
        )
        
        # Optimized supply chain scenario
        scenarios["optimized_supply"] = self.create_scenario(
            "Optimized Supply Chain",
            self.config["scenarios"]["optimized_supply"]
        )
        
        # Best case scenario (all improvements)
        scenarios["best_case"] = self.create_scenario(
            "Best Case - All Improvements",
            self.config["scenarios"]["best_case"]
        )
        
        # Worst case scenario (degraded performance)
        scenarios["worst_case"] = self.create_scenario(
            "Worst Case - Degraded Performance",
            self.config["scenarios"]["worst_case"]
        )
        
        return scenarios
