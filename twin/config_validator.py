"""
Configuration Validator for Virtual Twin Simulations
Ensures parameter changes are correctly reflected in generated configurations
"""

import json
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class ConfigValidator:
    """
    Validates that transformed configurations will produce expected simulation effects
    """
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_config(self, config: Dict[str, Any], parameters: Optional[Dict[str, float]] = None) -> bool:
        """
        Validate a configuration for simulation
        
        Args:
            config: The configuration dictionary to validate
            parameters: Optional parameter values that were applied
            
        Returns:
            True if valid, False otherwise
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        # Check required sections
        if not self._validate_structure(config):
            return False
        
        # Validate parameter application if provided
        if parameters:
            if not self._validate_parameter_application(config, parameters):
                return False
        
        # Validate value ranges
        if not self._validate_ranges(config):
            return False
        
        # Log results
        if self.validation_errors:
            for error in self.validation_errors:
                logger.error(f"Config validation error: {error}")
            return False
        
        if self.validation_warnings:
            for warning in self.validation_warnings:
                logger.warning(f"Config validation warning: {warning}")
        
        return True
    
    def _validate_structure(self, config: Dict[str, Any]) -> bool:
        """Validate the configuration has required structure"""
        required_sections = [
            'product_master',
            'equipment_configuration',
            'anomaly_injection',
            'product_specifications'
        ]
        
        for section in required_sections:
            if section not in config:
                self.validation_errors.append(f"Missing required section: {section}")
                return False
        
        return True
    
    def _validate_parameter_application(self, config: Dict[str, Any], parameters: Dict[str, float]) -> bool:
        """Validate that parameters were correctly applied to config"""
        
        # Check micro_stop_probability application
        if 'micro_stop_probability' in parameters:
            expected = parameters['micro_stop_probability']
            actual = config.get('anomaly_injection', {}).get('frequent_micro_stops', {}).get('probability_per_5min')
            
            if actual is None:
                self.validation_errors.append("micro_stop_probability not applied to config")
                return False
            
            if abs(actual - expected) > 0.001:
                self.validation_errors.append(
                    f"micro_stop_probability mismatch: expected {expected}, got {actual}"
                )
                return False
        
        # Check performance_factor application
        if 'performance_factor' in parameters:
            perf = parameters['performance_factor']
            equipment_eff = config.get('product_specifications', {}).get('equipment_efficiency', {})
            
            if not equipment_eff:
                self.validation_errors.append("performance_factor not applied to equipment_efficiency")
                return False
            
            # Check that efficiency ranges were scaled appropriately
            for eq_type, ranges in equipment_eff.items():
                if ranges.get('max', 0) > 1.0:
                    self.validation_warnings.append(
                        f"{eq_type} max efficiency > 1.0: {ranges.get('max')}"
                    )
        
        # Check scrap_multiplier application
        if 'scrap_multiplier' in parameters:
            scrap_mult = parameters['scrap_multiplier']
            quality_var = config.get('anomaly_injection', {}).get('quality_variation_normal', {})
            
            if 'scrap_rate_multiplier' not in quality_var:
                self.validation_errors.append("scrap_multiplier not applied to quality_variation")
                return False
            
            if abs(quality_var['scrap_rate_multiplier'] - scrap_mult) > 0.001:
                self.validation_errors.append(
                    f"scrap_multiplier mismatch: expected {scrap_mult}, got {quality_var['scrap_rate_multiplier']}"
                )
                return False
        
        return True
    
    def _validate_ranges(self, config: Dict[str, Any]) -> bool:
        """Validate that all values are within acceptable ranges"""
        
        # Check probability values are between 0 and 1
        probabilities = []
        
        # Collect all probability values
        anomaly = config.get('anomaly_injection', {})
        for pattern_name, pattern_data in anomaly.items():
            if isinstance(pattern_data, dict):
                if 'probability_per_5min' in pattern_data:
                    probabilities.append((pattern_name, pattern_data['probability_per_5min']))
                
                # Check equipment patterns
                if 'equipment_patterns' in pattern_data:
                    for eq_pattern in pattern_data['equipment_patterns']:
                        if 'probability_per_5min' in eq_pattern:
                            probabilities.append(
                                (f"{pattern_name}:{eq_pattern.get('equipment_id', 'unknown')}", 
                                 eq_pattern['probability_per_5min'])
                            )
        
        # Validate probabilities
        for name, prob in probabilities:
            if not 0.0 <= prob <= 1.0:
                self.validation_errors.append(
                    f"Invalid probability for {name}: {prob} (must be 0.0-1.0)"
                )
                return False
        
        # Check scrap rates are reasonable (0-50%)
        for product_id, product_data in config.get('product_master', {}).items():
            scrap_rate = product_data.get('normal_scrap_rate', 0)
            if scrap_rate > 0.5:
                self.validation_warnings.append(
                    f"High scrap rate for {product_id}: {scrap_rate*100:.1f}%"
                )
            if scrap_rate < 0:
                self.validation_errors.append(
                    f"Negative scrap rate for {product_id}: {scrap_rate}"
                )
                return False
        
        return True
    
    def get_report(self) -> Dict[str, Any]:
        """Get a detailed validation report"""
        return {
            'valid': len(self.validation_errors) == 0,
            'errors': self.validation_errors,
            'warnings': self.validation_warnings
        }
    
    def validate_config_file(self, config_path: str) -> bool:
        """Validate a configuration file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return self.validate_config(config)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.validation_errors.append(f"Failed to load config file: {e}")
            return False


def validate_parameter_bounds(parameters: Dict[str, float]) -> Tuple[bool, List[str]]:
    """
    Validate that parameter values are within their defined bounds
    
    Args:
        parameters: Dictionary of parameter names to values
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Define parameter bounds
    bounds = {
        'micro_stop_probability': (0.05, 0.50),
        'performance_factor': (0.50, 1.00),
        'scrap_multiplier': (0.5, 5.0),
        'material_reliability': (0.50, 1.00),
        'cascade_sensitivity': (0.0, 1.0)
    }
    
    for param_name, value in parameters.items():
        if param_name in bounds:
            min_val, max_val = bounds[param_name]
            if not min_val <= value <= max_val:
                errors.append(
                    f"{param_name}={value} out of bounds [{min_val}, {max_val}]"
                )
    
    return len(errors) == 0, errors
