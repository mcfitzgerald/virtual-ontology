"""Config Transformer Module
Applies scaling parameters to baseline configuration for simulation.
All parameters are treated as multipliers where 1.0 = baseline.
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
            # Try YAML first, then JSON
            yaml_path = self.config["paths"].get("base_config", "twin/config/generator.yaml")
            if yaml_path.endswith('.json'):
                yaml_path = yaml_path.replace('.json', '.yaml')
            if Path(yaml_path).exists():
                base_config_path = yaml_path
            else:
                base_config_path = self.config["paths"]["base_config"]
        
        if db_path is None:
            db_path = self.config["database"]["path"]
            
        self.base_config_path: Path = Path(base_config_path)
        self.base_config: Dict[str, Any] = self._load_base_config()
        self.config_manager: ConfigurationManager = ConfigurationManager(db_path)
        
        # Store baseline values for scaling
        self.baseline_values: Dict[str, Any] = self._extract_baseline_values()
        
    def _load_base_config(self) -> Dict[str, Any]:
        """Load the base MES configuration from JSON or YAML."""
        if self.base_config_path.suffix in ['.yaml', '.yml']:
            import yaml
            with open(self.base_config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            with open(self.base_config_path, 'r') as f:
                return json.load(f)
    
    def _extract_baseline_values(self) -> Dict[str, Any]:
        """Extract baseline values from configuration.
        
        Returns:
            Dictionary of baseline values for scaling
        """
        baseline: Dict[str, Any] = {}
        
        # Extract from YAML baseline_values section if present
        if 'baseline_values' in self.base_config:
            return self.base_config['baseline_values']
        
        # Otherwise extract from existing JSON structure
        if 'anomaly_injection' in self.base_config:
            anomalies = self.base_config['anomaly_injection']
            
            # Extract micro-stop probabilities
            baseline['micro_stops'] = {}
            if 'frequent_micro_stops' in anomalies:
                baseline['micro_stops']['frequent'] = anomalies['frequent_micro_stops'].get('probability_per_5min', 0.35)
            if 'minor_stops_line1' in anomalies:
                baseline['micro_stops']['minor_line1'] = anomalies['minor_stops_line1'].get('probability_per_5min', 0.20)
            if 'recurring_jams_line1' in anomalies:
                baseline['micro_stops']['jams_line1'] = anomalies['recurring_jams_line1'].get('probability_per_5min', 0.15)
            
            # Extract other baseline values
            if 'material_starvation_patterns' in anomalies:
                baseline['material_starvation'] = anomalies['material_starvation_patterns'].get('equipment_patterns', [])
            
            if 'cascade_failures' in anomalies:
                baseline['cascade_sensitivity'] = anomalies['cascade_failures'].get('downstream_stop_probability', 0.30)
        
        # Extract performance baselines
        if 'product_specifications' in self.base_config:
            specs = self.base_config['product_specifications']
            if 'equipment_efficiency' in specs:
                baseline['equipment_efficiency'] = specs['equipment_efficiency']
            if 'performance_variation' in specs:
                baseline['shift_performance'] = specs['performance_variation']
        
        return baseline
    
    def apply_parameters(
        self, 
        parameters: ActionableParameters,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Apply scaling parameters to create a new configuration.
        
        All parameters are treated as multipliers where 1.0 = baseline.
        
        Args:
            parameters: ActionableParameters instance with scaling values
            save_path: Optional path to save the transformed config
            
        Returns:
            Transformed configuration dictionary with scaled values

        """
        # Start with a deep copy of base config
        config: Dict[str, Any] = copy.deepcopy(self.base_config)
        
        # Normalize config structure for compatibility between YAML and JSON formats
        
        # 1. Map products.master to product_master
        if 'products' in config and 'master' in config.get('products', {}):
            config['product_master'] = config['products']['master']
        elif 'product_master' not in config:
            logger.warning("No product master data found in config")
        
        # 2. Map equipment to equipment_configuration
        if 'equipment' in config and 'equipment_configuration' not in config:
            config['equipment_configuration'] = config['equipment']
        
        # 3. Map downtime_reasons to downtime_reason_mapping if needed
        if 'downtime_reasons' in config and 'downtime_reason_mapping' not in config:
            config['downtime_reason_mapping'] = config['downtime_reasons']
        
        # 4. Map energy to energy_consumption if needed
        if 'energy' in config and 'energy_consumption' not in config:
            config['energy_consumption'] = config['energy']
        
        # 5. Map anomalies to anomaly_injection if needed
        if 'anomalies' in config and 'anomaly_injection' not in config:
            config['anomaly_injection'] = config['anomalies']
        
        # Ensure product_specifications exists with required fields
        if 'product_specifications' not in config:
            config['product_specifications'] = {}
            
        # Map scrap rates from YAML format
        if 'products' in config and 'scrap_rates' in config.get('products', {}):
            config['product_specifications'].update(config['products']['scrap_rates'])
        
        # Ensure required fields exist with defaults if not present
        if 'normal_scrap_rate' not in config['product_specifications']:
            config['product_specifications']['normal_scrap_rate'] = 0.02
            
        if 'equipment_efficiency' not in config['product_specifications']:
            # Default equipment efficiency ranges
            config['product_specifications']['equipment_efficiency'] = {
                'Filler': {'min': 0.75, 'max': 0.92},
                'Packer': {'min': 0.70, 'max': 0.90},
                'Palletizer': {'min': 0.72, 'max': 0.88}
            }
            
        if 'performance_variation' not in config['product_specifications']:
            # Default shift performance variation
            config['product_specifications']['performance_variation'] = {
                'shift_1': {'min': 0.90, 'max': 1.00},
                'shift_2': {'min': 0.95, 'max': 1.00},
                'shift_3': {'min': 0.85, 'max': 0.95}
            }
        
        # Get parameter values (scaling factors)
        values: Dict[str, float] = parameters.get_all_values()
        
        # Track parameter changes for transparency
        self._track_parameter_changes(config, values)
        
        # 1. Apply micro_stop_probability (now a scaling factor)
        micro_stop_scale: float = values.get("micro_stop_probability", 1.0)
        
        # Apply scaling to baseline values
        if 'micro_stops' in self.baseline_values:
            for stop_id, stop_data in self.baseline_values['micro_stops'].items():
                # Handle both dict and float formats
                if isinstance(stop_data, dict):
                    base_prob = stop_data.get('probability_per_5min', 0.1)
                else:
                    base_prob = float(stop_data)
                scaled_prob = base_prob * micro_stop_scale
                
                # Find and update the corresponding anomaly injection
                if stop_id in config.get('anomaly_injection', {}):
                    config['anomaly_injection'][stop_id]['probability_per_5min'] = scaled_prob
                    config['anomaly_injection'][stop_id]['description'] = (
                        f"Scaled from baseline {base_prob:.3f} by factor {micro_stop_scale:.2f}"
                    )
        
        # Apply to patterns from old config structure if needed
        if 'anomaly_injection' in config:
            # Scale frequent micro-stops
            if 'frequent_micro_stops' in config['anomaly_injection']:
                base = self.baseline_values.get('micro_stops', {}).get('frequent', 0.35)
                config['anomaly_injection']['frequent_micro_stops']['probability_per_5min'] = base * micro_stop_scale
            
            # Scale minor stops
            if 'minor_stops_line1' in config['anomaly_injection']:
                base = self.baseline_values.get('micro_stops', {}).get('minor_line1', 0.20)
                config['anomaly_injection']['minor_stops_line1']['probability_per_5min'] = base * micro_stop_scale
            
            # Scale recurring jams
            if 'recurring_jams_line1' in config['anomaly_injection']:
                base = self.baseline_values.get('micro_stops', {}).get('jams_line1', 0.15)
                config['anomaly_injection']['recurring_jams_line1']['probability_per_5min'] = base * micro_stop_scale
            
            # Scale equipment pattern micro-stops
            for pattern_type in ['filler_micro_stops', 'palletizer_micro_stops']:
                if pattern_type in config['anomaly_injection']:
                    if 'equipment_patterns' in config['anomaly_injection'][pattern_type]:
                        for pattern in config['anomaly_injection'][pattern_type]['equipment_patterns']:
                            if 'probability_per_5min' in pattern:
                                # Assume baseline if not found
                                base_prob = pattern.get('baseline_probability', pattern['probability_per_5min'])
                                pattern['probability_per_5min'] = base_prob * micro_stop_scale
                                pattern['baseline_probability'] = base_prob  # Store for reference
        
        # 2. Apply performance_factor (now a scaling factor)
        perf_scale: float = values.get("performance_factor", 1.0)
        
        # Scale equipment efficiency from baseline
        if 'equipment_efficiency' in self.baseline_values:
            if 'product_specifications' not in config:
                config['product_specifications'] = {}
            
            config['product_specifications']['equipment_efficiency'] = {}
            for equipment, efficiency in self.baseline_values['equipment_efficiency'].items():
                config['product_specifications']['equipment_efficiency'][equipment] = {
                    'min': max(0.5, efficiency.get('min', 0.75) * perf_scale),
                    'max': min(1.0, efficiency.get('max', 0.95) * perf_scale)
                }
        
        # Scale shift performance from baseline
        if 'shift_performance' in self.baseline_values:
            config['product_specifications']['performance_variation'] = {}
            for shift, performance in self.baseline_values['shift_performance'].items():
                config['product_specifications']['performance_variation'][shift] = {
                    'min': max(0.5, performance.get('min', 0.8) * perf_scale),
                    'max': min(1.0, performance.get('max', 1.0) * perf_scale)
                }
        
        # Scale performance drops if present
        if 'performance_drops' in self.baseline_values:
            if 'random_performance_drops' not in config['product_specifications']:
                config['product_specifications']['random_performance_drops'] = {}
            
            base_factor = self.baseline_values['performance_drops'].get('degradation_factor', {'min': 0.6, 'max': 0.8})
            config['product_specifications']['random_performance_drops']['degradation_factor'] = {
                'min': max(0.3, base_factor.get('min', 0.6) * perf_scale),
                'max': min(1.0, base_factor.get('max', 0.8) * perf_scale)
            }
        
        # 3. Apply scrap_multiplier (now a scaling factor)
        scrap_scale: float = values.get("scrap_multiplier", 1.0)
        
        # Scale quality variations
        if 'anomaly_injection' in config:
            if 'quality_variation_normal' in config['anomaly_injection']:
                config['anomaly_injection']['quality_variation_normal']['scrap_rate_multiplier'] = scrap_scale
            
            if 'quality_end_of_run' in config['anomaly_injection']:
                config['anomaly_injection']['quality_end_of_run']['scrap_rate_multiplier'] = scrap_scale * 1.5
            
            if 'changeover_scrap_spike' in config['anomaly_injection']:
                config['anomaly_injection']['changeover_scrap_spike']['scrap_multiplier'] = scrap_scale * 1.5
        
        # Scale product-specific scrap rates from baseline
        if 'scrap_rates' in self.baseline_values and 'product_master' in config:
            for sku, product_data in config['product_master'].items():
                # Scale normal scrap rates
                if sku in self.baseline_values['scrap_rates'].get('normal', {}):
                    base_rate = self.baseline_values['scrap_rates']['normal'][sku]
                    product_data['normal_scrap_rate'] = min(0.15, base_rate * scrap_scale)
                
                # Scale startup scrap rates
                if sku in self.baseline_values['scrap_rates'].get('startup', {}):
                    base_rate = self.baseline_values['scrap_rates']['startup'][sku]
                    product_data['startup_scrap_rate'] = min(0.20, base_rate * scrap_scale)
        
        # 4. Apply material_reliability (now a scaling factor)
        mat_scale: float = values.get("material_reliability", 1.0)
        
        # Material reliability inversely affects starvation (higher reliability = lower starvation)
        starvation_scale: float = 2.0 - mat_scale  # 1.0 reliability = 1.0x baseline, 0.5 = 1.5x baseline
        
        # Scale material starvation patterns from baseline
        if 'material_starvation' in self.baseline_values:
            if 'anomaly_injection' not in config:
                config['anomaly_injection'] = {}
            
            patterns = []
            for pattern in self.baseline_values.get('material_starvation', []):
                if isinstance(pattern, dict):
                    scaled_pattern = pattern.copy()
                    base_prob = pattern.get('probability_per_5min', 0.15)
                    scaled_pattern['probability_per_5min'] = base_prob * starvation_scale
                    patterns.append(scaled_pattern)
            
            if patterns:
                config['anomaly_injection']['material_starvation_patterns'] = {
                    'enabled': True,
                    'equipment_patterns': patterns,
                    'description': f"Material starvation scaled by reliability factor {mat_scale:.2f}"
                }
        
        # GENERIC EVENT PROCESSING - Handle ANY event type from baseline_values
        # This allows adding new event types without modifying this code
        event_types_to_process = [
            'mechanical_failures',
            'electrical_failures',
            # Add any new event types here - or better, discover them dynamically
        ]
        
        # Actually, let's be even more generic - process ALL baseline_values that look like event patterns
        for event_type, event_data in self.baseline_values.items():
            # Skip already processed types and non-event types
            if event_type in ['micro_stops', 'material_starvation', 'changeover_schedule', 
                              'cascade_sensitivity', 'shift_performance', 'scrap_rates',
                              'equipment_efficiency']:
                continue
                
            # Check if this looks like an event pattern (list of dicts with probability)
            if isinstance(event_data, list) and event_data:
                first_item = event_data[0] if event_data else {}
                if isinstance(first_item, dict) and 'probability_per_5min' in first_item:
                    # This is an event pattern! Process it
                    if 'anomaly_injection' not in config:
                        config['anomaly_injection'] = {}
                    
                    # For now, no scaling on these generic events (scale factor = 1.0)
                    # Could add parameter mapping if needed: event_type -> parameter_name
                    scale_factor = 1.0
                    
                    # Apply any relevant scaling based on event type
                    if 'failure' in event_type.lower() or 'jam' in event_type.lower():
                        # These might be affected by maintenance (micro_stop_probability)
                        scale_factor = micro_stop_scale
                    
                    patterns = []
                    for pattern in event_data:
                        if isinstance(pattern, dict):
                            scaled_pattern = pattern.copy()
                            if 'probability_per_5min' in scaled_pattern:
                                base_prob = scaled_pattern['probability_per_5min']
                                scaled_pattern['probability_per_5min'] = base_prob * scale_factor
                            patterns.append(scaled_pattern)
                    
                    if patterns:
                        config['anomaly_injection'][f'{event_type}_patterns'] = {
                            'enabled': True,
                            'equipment_patterns': patterns,
                            'description': f"{event_type.replace('_', ' ').title()} (scaled by {scale_factor:.2f})"
                        }
        
        # 5. Apply cascade_sensitivity (now a scaling factor for coupling)
        cascade_scale: float = values.get("cascade_sensitivity", 1.0)
        
        # Scale cascade sensitivity from baseline
        base_cascade = self.baseline_values.get('cascade_sensitivity', 0.30)
        
        if 'anomaly_injection' not in config:
            config['anomaly_injection'] = {}
        
        # Define equipment flow for proper cascade modeling
        equipment_flows = {
            'LINE1': ['LINE1-FIL', 'LINE1-PCK', 'LINE1-PAL'],
            'LINE2': ['LINE2-FIL', 'LINE2-PCK', 'LINE2-PAL'],
            'LINE3': ['LINE3-FIL', 'LINE3-PCK', 'LINE3-PAL']
        }
        
        config['anomaly_injection']['cascade_failures'] = {
            'enabled': True,
            'downstream_stop_probability': min(1.0, base_cascade * cascade_scale),
            'cascade_delay_minutes': 5,  # Keep constant
            'equipment_flows': equipment_flows,  # Production flow sequences
            'description': f"Cascade sensitivity scaled from baseline {base_cascade:.2f} by factor {cascade_scale:.2f}"
        }
        
        # Add metadata about transformation
        from datetime import datetime
        config["twin_metadata"] = {
            "transformed_by": "virtual_twin_scaling",
            "parameters_applied": values,
            "baseline_values_used": True,
            "scaling_interpretation": {
                param: f"{value:.2f}x baseline" 
                for param, value in values.items()
            },
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
        """Create a specific scenario configuration.
        
        Args:
            scenario_name: Name of the scenario
            parameter_changes: Dictionary of parameter names and their scaling values
            
        Returns:
            Scenario configuration with scaled values

        """
        # Create parameters instance
        params: ActionableParameters = ActionableParameters()
        
        # Apply changes (all are scaling factors)
        for name, value in parameter_changes.items():
            params.set_value(name, value)
        
        # Transform config
        config: Dict[str, Any] = self.apply_parameters(params)
        
        # Add scenario metadata
        config["scenario"] = {
            "name": scenario_name,
            "description": f"Virtual twin scenario: {scenario_name}",
            "parameter_changes": parameter_changes,
            "interpretation": {
                param: f"{value:.0f}% of baseline" if value != 1.0 else "baseline"
                for param, value in parameter_changes.items()
            }
        }
        
        return config
    
    def _track_parameter_changes(
        self,
        config: Dict[str, Any],
        values: Dict[str, float]
    ) -> None:
        """Track parameter changes for transparency.
        
        Args:
            config: Configuration being modified
            values: Parameter scaling values applied
        """
        if 'parameter_tracking' not in config:
            config['parameter_tracking'] = {}
        
        config['parameter_tracking']['scaling_factors'] = values
        config['parameter_tracking']['baseline_source'] = str(self.base_config_path)
        config['parameter_tracking']['changes'] = []
        
        # Log each parameter change
        for param, value in values.items():
            if value != 1.0:  # Only track non-baseline values
                percent_change = (value - 1.0) * 100
                config['parameter_tracking']['changes'].append({
                    'parameter': param,
                    'scaling_factor': value,
                    'percent_change': f"{percent_change:+.0f}%",
                    'interpretation': self._interpret_parameter(param, value)
                })
    
    def _interpret_parameter(
        self,
        param_name: str,
        value: float
    ) -> str:
        """Interpret what a parameter scaling means.
        
        Args:
            param_name: Name of the parameter
            value: Scaling value
            
        Returns:
            Human-readable interpretation
        """
        if value == 1.0:
            return "No change from baseline"
        
        interpretations = {
            'micro_stop_probability': (
                f"Equipment issues {'reduced' if value < 1.0 else 'increased'} to {value*100:.0f}% of baseline"
            ),
            'performance_factor': (
                f"Performance {'improved' if value > 1.0 else 'degraded'} to {value*100:.0f}% of baseline"
            ),
            'scrap_multiplier': (
                f"Scrap rates {'reduced' if value < 1.0 else 'increased'} to {value*100:.0f}% of baseline"
            ),
            'material_reliability': (
                f"Material supply {'improved' if value > 1.0 else 'degraded'} to {value*100:.0f}% of baseline"
            ),
            'cascade_sensitivity': (
                f"Equipment coupling {'reduced' if value < 1.0 else 'increased'} to {value*100:.0f}% of baseline"
            )
        }
        
        return interpretations.get(param_name, f"Scaled to {value*100:.0f}% of baseline")
    
    def create_optimization_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Create standard optimization scenarios for comparison
        
        Returns:
            Dictionary of scenario configurations

        """
        scenarios: Dict[str, Dict[str, Any]] = {}
        
        # Baseline scenario (all parameters at 1.0)
        params_baseline: ActionableParameters = ActionableParameters()
        # Ensure all parameters are at 1.0 (baseline)
        for param_name in params_baseline.parameters.keys():
            params_baseline.set_value(param_name, 1.0)
        
        scenarios["baseline"] = {
            "config": self.apply_parameters(params_baseline),
            "description": "Current state baseline (all scaling factors = 1.0)",
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
