"""Configuration loader for scheduler settings.

This module provides utilities to load scheduler configuration
from YAML files, making the scheduler fully configurable.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import yaml

from .base_scheduler import SchedulerConfig, SchedulingConstraints

logger = logging.getLogger(__name__)


def load_scheduler_config(config_path: Path) -> SchedulerConfig:
    """Load scheduler configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        SchedulerConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    scheduler_data = data.get('scheduler_config', {})
    
    config = SchedulerConfig(
        min_order_duration_hours=scheduler_data.get('min_order_duration_hours', 2.0),
        max_order_duration_hours=scheduler_data.get('max_order_duration_hours', 8.0),
        typical_order_duration_hours=scheduler_data.get('typical_order_duration_hours', 4.0),
        efficiency_factor=scheduler_data.get('efficiency_factor', 0.7),
        min_priority=scheduler_data.get('min_priority', 1),
        max_priority=scheduler_data.get('max_priority', 10),
        default_priority=scheduler_data.get('default_priority', 5),
        same_family_changeover_minutes=scheduler_data.get('same_family_changeover_minutes', 15.0),
        different_family_changeover_minutes=scheduler_data.get('different_family_changeover_minutes', 30.0),
        cleaning_changeover_minutes=scheduler_data.get('cleaning_changeover_minutes', 45.0),
        allow_preemption=scheduler_data.get('allow_preemption', False),
        allow_splitting=scheduler_data.get('allow_splitting', False),
        maximize_campaign_length=scheduler_data.get('maximize_campaign_length', True)
    )
    
    logger.info(f"Loaded scheduler config from {config_path}")
    return config


def load_scheduling_constraints(config_path: Path) -> SchedulingConstraints:
    """Load scheduling constraints from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        SchedulingConstraints object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    constraints_data = data.get('scheduling_constraints', {})
    
    # Parse maintenance windows
    maintenance_windows = []
    for window in constraints_data.get('maintenance_windows', []):
        start = window.get('start_hour', 0) * 60  # Convert to minutes
        duration = window.get('duration_hours', 0) * 60
        maintenance_windows.append((start, start + duration))
    
    # Parse forbidden/preferred sequences
    forbidden_sequences = [
        tuple(seq) for seq in constraints_data.get('forbidden_sequences', [])
    ]
    preferred_sequences = [
        tuple(seq) for seq in constraints_data.get('preferred_sequences', [])
    ]
    
    constraints = SchedulingConstraints(
        horizon_hours=constraints_data.get('horizon_hours'),
        maintenance_windows=maintenance_windows if maintenance_windows else None,
        product_line_compatibility=constraints_data.get('product_line_compatibility'),
        line_product_restrictions=constraints_data.get('line_product_restrictions'),
        forbidden_sequences=forbidden_sequences if forbidden_sequences else None,
        preferred_sequences=preferred_sequences if preferred_sequences else None,
        max_concurrent_orders=constraints_data.get('max_concurrent_orders'),
        min_campaign_length=constraints_data.get('min_campaign_length_hours'),
        max_campaign_length=constraints_data.get('max_campaign_length_hours')
    )
    
    logger.info(f"Loaded scheduling constraints from {config_path}")
    return constraints


def load_complete_scheduler_config(
    config_path: Path
) -> Tuple[SchedulerConfig, SchedulingConstraints]:
    """Load both scheduler config and constraints from a single file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Tuple of (SchedulerConfig, SchedulingConstraints)
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    config = load_scheduler_config(config_path)
    constraints = load_scheduling_constraints(config_path)
    return config, constraints


def create_scheduler_from_config(
    env,
    config_path: Optional[Path] = None,
    catalog_path: Optional[Path] = None,
    random_seed: Optional[int] = None
):
    """Create a ProductionScheduler from configuration files.
    
    Args:
        env: SimPy environment
        config_path: Path to scheduler configuration YAML
        catalog_path: Path to product catalog YAML
        random_seed: Random seed for reproducibility
        
    Returns:
        Configured ProductionScheduler instance
    """
    from .production_scheduler import ProductionScheduler
    
    if config_path and config_path.exists():
        config, constraints = load_complete_scheduler_config(config_path)
        logger.info(f"Creating scheduler with config from {config_path}")
    else:
        config = SchedulerConfig()
        constraints = SchedulingConstraints()
        logger.info("Creating scheduler with default configuration")
    
    scheduler = ProductionScheduler(
        env=env,
        config=config,
        constraints=constraints,
        catalog_path=catalog_path,
        random_seed=random_seed
    )
    
    return scheduler


def validate_schedule_config(config_path: Path) -> List[str]:
    """Validate a scheduler configuration file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        List of validation warnings/errors (empty if valid)
    """
    warnings = []
    
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return [f"Failed to load YAML: {e}"]
    
    # Check required sections
    if 'scheduler_config' not in data:
        warnings.append("Missing 'scheduler_config' section")
    
    if 'scheduling_constraints' not in data:
        warnings.append("Missing 'scheduling_constraints' section")
    
    # Validate scheduler config
    scheduler_data = data.get('scheduler_config', {})
    
    min_duration = scheduler_data.get('min_order_duration_hours', 0)
    max_duration = scheduler_data.get('max_order_duration_hours', 0)
    if min_duration > max_duration:
        warnings.append(
            f"min_order_duration_hours ({min_duration}) > "
            f"max_order_duration_hours ({max_duration})"
        )
    
    efficiency = scheduler_data.get('efficiency_factor', 0.7)
    if not 0 < efficiency <= 1:
        warnings.append(f"efficiency_factor should be between 0 and 1, got {efficiency}")
    
    # Validate constraints
    constraints_data = data.get('scheduling_constraints', {})
    
    # Check product-line compatibility consistency
    product_lines = constraints_data.get('product_line_compatibility', {})
    line_products = constraints_data.get('line_product_restrictions', {})
    
    for product, lines in product_lines.items():
        for line in lines:
            if line in line_products:
                if product not in line_products[line]:
                    warnings.append(
                        f"Inconsistency: {product} allowed on line {line} "
                        f"but not in line_product_restrictions"
                    )
    
    # Check campaign length constraints
    min_campaign = constraints_data.get('min_campaign_length_hours', 0)
    max_campaign = constraints_data.get('max_campaign_length_hours', float('inf'))
    if min_campaign > max_campaign:
        warnings.append(
            f"min_campaign_length_hours ({min_campaign}) > "
            f"max_campaign_length_hours ({max_campaign})"
        )
    
    return warnings