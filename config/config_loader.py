"""Configuration loader for the Virtual Twin system."""
import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""
    pass

class ConfigLoader:
    """Load and validate configuration files."""
    
    @staticmethod
    def load_config(config_name: str) -> Dict[str, Any]:
        """
        Load a configuration file. FAILS if file doesn't exist.
        
        Args:
            config_name: Name of config file (without .yaml)
            
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationError: If config file missing or invalid
        """
        config_path = Path(f"config/{config_name}.yaml")
        
        if not config_path.exists():
            raise ConfigurationError(
                f"Required configuration file not found: {config_path}\n"
                f"Please ensure config/{config_name}.yaml exists."
            )
        
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                
            if config is None:
                raise ConfigurationError(f"Configuration file is empty: {config_path}")
                
            return config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {config_path}: {e}")
    
    @staticmethod
    def get_required(config: Dict, path: str, error_msg: str = None):
        """
        Get a required configuration value using dot notation.
        
        Args:
            config: Configuration dictionary
            path: Dot-separated path (e.g., "validation.buffer.min_size")
            error_msg: Custom error message
            
        Returns:
            Configuration value
            
        Raises:
            ConfigurationError: If path not found
        """
        keys = path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                if error_msg:
                    raise ConfigurationError(error_msg)
                else:
                    raise ConfigurationError(
                        f"Required configuration missing: {path}\n"
                        f"Please check config file structure."
                    )
        
        return value