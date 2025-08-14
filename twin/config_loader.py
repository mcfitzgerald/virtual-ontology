"""Configuration Loader for Virtual Twin
Loads configuration from YAML files with environment-specific overrides
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and manages configuration for the Virtual Twin system.
    
    Configuration is loaded in the following priority order:
    1. defaults.yaml (base configuration)
    2. Environment-specific config (e.g., production.yaml, development.yaml)
    3. Environment variables (prefixed with TWIN_)
    4. Runtime overrides
    """
    
    def __init__(
        self,
        config_dir: Optional[str] = None,
        environment: Optional[str] = None
    ) -> None:
        """Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
                       Defaults to twin/config relative to this file
            environment: Environment name (production, development, test)
                        Defaults to TWIN_ENV environment variable or 'development'

        """
        if config_dir is None:
            config_dir = str(Path(__file__).parent / "config")
        
        self.config_dir: Path = Path(config_dir)
        
        if environment is None:
            environment = os.environ.get("TWIN_ENV", "development")
        
        self.environment: str = environment
        self.config: Dict[str, Any] = {}
        
        # Load configuration
        self._load_config()
        
    def _load_config(self) -> None:
        """Load configuration from files and environment."""
        # Load defaults
        defaults_path = self.config_dir / "defaults.yaml"
        if defaults_path.exists():
            with open(defaults_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded default configuration from {defaults_path}")
        else:
            logger.warning(f"Default configuration not found at {defaults_path}")
        
        # Load environment-specific config if it exists
        env_config_path = self.config_dir / f"{self.environment}.yaml"
        if env_config_path.exists():
            with open(env_config_path, 'r') as f:
                env_config = yaml.safe_load(f) or {}
                self._deep_merge(self.config, env_config)
                logger.info(f"Loaded {self.environment} configuration from {env_config_path}")
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge override dictionary into base dictionary.
        
        Args:
            base: Base configuration dictionary (modified in place)
            override: Override configuration dictionary

        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
                
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides.
        
        Environment variables should be prefixed with TWIN_ and use double underscores
        for nested keys. For example:
        - TWIN_DATABASE_PATH -> config['database']['path']
        - TWIN_SIMULATION_MAX_WORKERS -> config['simulation']['max_workers']
        """
        prefix = "TWIN_"
        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix):
                # Remove prefix and convert to lowercase
                config_key = env_key[len(prefix):].lower()
                
                # Split by double underscore for nested keys
                keys = config_key.split("__")
                
                # Navigate to the correct position in config
                current = self.config
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Set the value (attempt to parse as number if possible)
                try:
                    # Try to parse as int
                    value: Any = int(env_value)
                except ValueError:
                    try:
                        # Try to parse as float
                        value = float(env_value)
                    except ValueError:
                        # Keep as string
                        value = env_value
                        
                current[keys[-1]] = value
                logger.info(f"Applied environment override: {env_key} = {value}")
                
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to the configuration key
                     e.g., "database.path" or "simulation.max_workers"
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config = ConfigLoader()
            >>> db_path = config.get("database.path")
            >>> max_workers = config.get("simulation.max_workers", 4)

        """
        keys = key_path.split(".")
        current = self.config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
                
        return current
        
    def get_parameter_config(self, param_name: str) -> Dict[str, Any]:
        """Get configuration for a specific actionable parameter.
        
        Args:
            param_name: Name of the parameter
            
        Returns:
            Dictionary with parameter configuration including bounds, default, etc.
            
        Raises:
            KeyError: If parameter is not found in configuration

        """
        params = self.get("parameters", {})
        if param_name not in params:
            raise KeyError(f"Parameter '{param_name}' not found in configuration")
        return params[param_name]
        
    def get_all_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get all parameter configurations.
        
        Returns:
            Dictionary of parameter configurations

        """
        return self.get("parameters", {})
        
    def get_scenario(self, scenario_name: str) -> Dict[str, float]:
        """Get a pre-configured scenario.
        
        Args:
            scenario_name: Name of the scenario
            
        Returns:
            Dictionary of parameter values for the scenario
            
        Raises:
            KeyError: If scenario is not found in configuration

        """
        scenarios = self.get("scenarios", {})
        if scenario_name not in scenarios:
            raise KeyError(f"Scenario '{scenario_name}' not found in configuration")
        return scenarios[scenario_name]
        
    def save_override(self, override_path: str) -> None:
        """Save current configuration to a file (useful for debugging).
        
        Args:
            override_path: Path to save the configuration

        """
        with open(override_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=True)
        logger.info(f"Saved configuration to {override_path}")
        
    def __repr__(self) -> str:
        """String representation of ConfigLoader."""
        return f"ConfigLoader(environment='{self.environment}', config_dir='{self.config_dir}')"


# Singleton instance for easy access
_config: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """Get the singleton configuration instance.
    
    Returns:
        ConfigLoader instance
        
    Example:
        >>> from twin.config_loader import get_config
        >>> config = get_config()
        >>> db_path = config.get("database.path")

    """
    global _config
    if _config is None:
        _config = ConfigLoader()
    return _config


def reload_config(environment: Optional[str] = None) -> ConfigLoader:
    """Reload configuration with a different environment.
    
    Args:
        environment: Environment name (production, development, test)
        
    Returns:
        New ConfigLoader instance

    """
    global _config
    _config = ConfigLoader(environment=environment)
    return _config