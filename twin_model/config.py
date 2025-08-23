"""Configuration system for performance optimization.

This module provides configuration management for simulation performance
settings, including presets for different scenarios and validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List, Union
from enum import Enum
from pathlib import Path
import json
import yaml
import sys
import os

# Add parent directory to path to import config_loader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config_loader import ConfigLoader, ConfigurationError
from twin_model.primitives.base import SimulationMode

# Load configuration at module initialization
try:
    _config = ConfigLoader.load_config("twin_model")
except ConfigurationError as e:
    raise ConfigurationError(
        f"Failed to load required twin_model configuration: {e}\n"
        "Please ensure config/twin_model.yaml exists and is valid."
    )


class ConfigPreset(Enum):
    """Pre-defined configuration presets for common scenarios."""

    DEVELOPMENT = "development"  # Full data collection for debugging
    PRODUCTION = "production"  # Balanced performance and data
    FAST = "fast"  # Minimal data for speed
    MEMORY_OPTIMIZED = "memory_optimized"  # Aggressive memory limits
    LONG_RUNNING = "long_running"  # Optimized for 30+ day simulations
    REAL_TIME = "real_time"  # For real-time digital twin scenarios


@dataclass
class PerformanceConfig:
    """Performance configuration for simulations.

    Controls memory usage, sampling, and optimization settings
    for different simulation scenarios. All settings can be
    customized or loaded from presets.

    Attributes:
        observable_buffer_size: Max events per primitive buffer
        sampling_rate: Event sampling frequency (1 = keep all, 100 = keep 1%)
        aggregation_interval: Minutes between metric aggregations
        flush_interval: Minutes between database flushes
        cache_max_size: Max events per cache file
        enable_global_observables: Use global event collection
        simulation_mode: Data collection mode (DETAILED/PRODUCTION/FAST)
        max_memory_mb: Memory usage limit before warning
        enable_progress: Show progress updates during simulation
        checkpoint_interval: Minutes between auto-checkpoints
        chunk_size_days: Days per execution chunk
        batch_size: Events per batch for processing
        enable_monitoring: Enable health monitoring
        monitoring_interval: Minutes between health checks
    """

    # Memory settings - loaded from config
    observable_buffer_size: int = field(
        default_factory=lambda: ConfigLoader.get_required(_config, "performance_defaults.observable_buffer_size")
    )
    cache_max_size: int = field(
        default_factory=lambda: ConfigLoader.get_required(_config, "performance_defaults.cache_max_size")
    )
    max_memory_mb: float = field(
        default_factory=lambda: ConfigLoader.get_required(_config, "performance_defaults.max_memory_mb")
    )

    # Sampling settings - loaded from config
    sampling_rate: int = field(
        default_factory=lambda: ConfigLoader.get_required(_config, "performance_defaults.sampling_rate")
    )
    simulation_mode: SimulationMode = SimulationMode.PRODUCTION
    enable_global_observables: bool = False

    # Processing settings - loaded from config
    aggregation_interval: float = field(
        default_factory=lambda: ConfigLoader.get_required(_config, "performance_defaults.aggregation_interval")
    )
    flush_interval: float = field(
        default_factory=lambda: ConfigLoader.get_required(_config, "performance_defaults.flush_interval")
    )
    batch_size: int = field(
        default_factory=lambda: ConfigLoader.get_required(_config, "performance_defaults.batch_size")
    )

    # Execution settings - loaded from config
    enable_progress: bool = True
    checkpoint_interval: Optional[float] = field(
        default_factory=lambda: ConfigLoader.get_required(_config, "performance_defaults.checkpoint_interval")
    )
    chunk_size_days: float = field(
        default_factory=lambda: ConfigLoader.get_required(_config, "performance_defaults.chunk_size_days")
    )

    # Monitoring settings - loaded from config
    enable_monitoring: bool = True
    monitoring_interval: float = field(
        default_factory=lambda: ConfigLoader.get_required(_config, "performance_defaults.monitoring_interval")
    )

    # Metadata
    name: str = "custom"
    description: str = ""

    @classmethod
    def from_preset(cls, preset: Union[ConfigPreset, str]) -> "PerformanceConfig":
        """Create configuration from a preset.

        Args:
            preset: Preset name or ConfigPreset enum

        Returns:
            PerformanceConfig instance with preset values
        """
        if isinstance(preset, str):
            preset = ConfigPreset(preset)

        # Load preset configuration from config file
        preset_config = ConfigLoader.get_required(_config, f"presets.{preset.value}")

        # Map simulation modes based on preset name
        mode_mapping = {
            "development": SimulationMode.DETAILED,
            "production": SimulationMode.PRODUCTION,
            "fast": SimulationMode.FAST,
            "memory_optimized": SimulationMode.FAST,
            "long_running": SimulationMode.PRODUCTION,
            "real_time": SimulationMode.PRODUCTION,
        }

        # Create config from preset values
        return cls(
            name=preset.value,
            description=f"Preset configuration: {preset.value}",
            observable_buffer_size=preset_config["observable_buffer_size"],
            cache_max_size=preset_config["cache_max_size"],
            max_memory_mb=preset_config["max_memory_mb"],
            sampling_rate=preset_config["sampling_rate"],
            simulation_mode=mode_mapping.get(preset.value, SimulationMode.PRODUCTION),
            enable_global_observables=(preset.value == "development"),
            aggregation_interval=preset_config["aggregation_interval"],
            flush_interval=preset_config["flush_interval"],
            batch_size=preset_config["batch_size"],
            enable_progress=(preset.value != "fast"),
            checkpoint_interval=preset_config.get("checkpoint_interval"),
            chunk_size_days=preset_config["chunk_size_days"],
            enable_monitoring=(preset.value != "fast"),
            monitoring_interval=preset_config["monitoring_interval"],
        )

        # OLD CODE REMOVED - now loading from config
        # Configuration is now loaded from config files

        return None  # This line should never be reached due to earlier return

    @classmethod
    def from_json(cls, path: Union[str, Path]) -> "PerformanceConfig":
        """Load configuration from JSON file.

        Args:
            path: Path to configuration file

        Returns:
            PerformanceConfig instance

        Raises:
            ValueError: If configuration is invalid
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r") as f:
            data = json.load(f)

        # Handle simulation mode enum
        if "simulation_mode" in data:
            mode_str = data["simulation_mode"]
            if isinstance(mode_str, str):
                data["simulation_mode"] = SimulationMode[mode_str.upper()]

        config = cls(**data)

        # Validate
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        return config

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "PerformanceConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to configuration file

        Returns:
            PerformanceConfig instance
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Handle simulation mode enum
        if "simulation_mode" in data:
            mode_str = data["simulation_mode"]
            if isinstance(mode_str, str):
                data["simulation_mode"] = SimulationMode[mode_str.upper()]

        config = cls(**data)

        # Validate
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        return config

    def to_json(self, path: Union[str, Path]) -> None:
        """Save configuration to JSON file.

        Args:
            path: Path to save configuration
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(self)
        # Convert enum to string
        data["simulation_mode"] = self.simulation_mode.value

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def to_yaml(self, path: Union[str, Path]) -> None:
        """Save configuration to YAML file.

        Args:
            path: Path to save configuration
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(self)
        # Convert enum to string
        data["simulation_mode"] = self.simulation_mode.value

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def validate(self) -> List[str]:
        """Validate configuration settings.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        # Get validation thresholds from config
        val_config = ConfigLoader.get_required(_config, "validation")

        # Buffer size validation
        if self.observable_buffer_size < val_config["buffer"]["min_size"]:
            errors.append(f"observable_buffer_size must be at least {val_config['buffer']['min_size']}")
        if self.observable_buffer_size > val_config["buffer"]["max_size"]:
            errors.append(f"observable_buffer_size too large (max {val_config['buffer']['max_size']})")

        # Cache size validation
        if self.cache_max_size < val_config["cache"]["min_size"]:
            errors.append(f"cache_max_size must be at least {val_config['cache']['min_size']}")

        # Memory validation
        if self.max_memory_mb < val_config["memory"]["min_mb"]:
            errors.append(f"max_memory_mb must be at least {val_config['memory']['min_mb']}MB")
        if self.max_memory_mb > val_config["memory"]["max_mb"]:
            errors.append(f"max_memory_mb unrealistic (>{val_config['memory']['max_mb']}MB)")

        # Sampling rate validation
        if self.sampling_rate < val_config["sampling"]["min_rate"]:
            errors.append(f"sampling_rate must be at least {val_config['sampling']['min_rate']}")
        if self.sampling_rate > val_config["sampling"]["max_rate"]:
            errors.append(f"sampling_rate too high (max {val_config['sampling']['max_rate']})")

        # Interval validation
        if self.aggregation_interval <= 0:
            errors.append("aggregation_interval must be positive")
        if self.flush_interval <= 0:
            errors.append("flush_interval must be positive")

        # Batch size validation
        if self.batch_size < val_config["batch"]["min_size"]:
            errors.append(f"batch_size must be at least {val_config['batch']['min_size']}")
        if self.batch_size > val_config["batch"]["max_size"]:
            errors.append(f"batch_size too large (max {val_config['batch']['max_size']})")

        # Chunk size validation
        if self.chunk_size_days <= 0:
            errors.append("chunk_size_days must be positive")
        if self.chunk_size_days > val_config["chunk"]["max_days"]:
            errors.append(f"chunk_size_days too large (max {val_config['chunk']['max_days']})")

        # Logical consistency checks
        if self.flush_interval < self.aggregation_interval:
            errors.append("flush_interval should be >= aggregation_interval")

        if self.cache_max_size < self.batch_size:
            errors.append("cache_max_size should be >= batch_size")

        # Allow small floating point differences
        if self.checkpoint_interval and (self.checkpoint_interval + 0.1) < self.chunk_size_days * 1440:
            errors.append("checkpoint_interval should be >= chunk_size")

        # Mode consistency
        if self.simulation_mode == SimulationMode.FAST and self.sampling_rate == 1:
            errors.append("FAST mode incompatible with sampling_rate=1")

        if self.simulation_mode == SimulationMode.DETAILED and self.sampling_rate > 10:
            errors.append("DETAILED mode should have sampling_rate <= 10")

        return errors

    def estimate_memory_usage(self, num_primitives: int, simulation_days: int) -> Dict[str, float]:
        """Estimate memory usage for given simulation parameters.

        Args:
            num_primitives: Number of primitives in simulation
            simulation_days: Duration of simulation in days

        Returns:
            Dictionary with memory estimates in MB
        """
        # Base estimates from config
        event_size = ConfigLoader.get_required(_config, "events.default_size_bytes")
        metric_size = ConfigLoader.get_required(_config, "events.metric_size_bytes")

        # Buffer memory per primitive
        buffer_memory = num_primitives * self.observable_buffer_size * event_size

        # Cache memory (limited by max_size)
        cache_memory = min(
            self.cache_max_size * event_size,
            simulation_days * 1440 * 60 * event_size / self.sampling_rate,  # Total events
        )

        # Aggregation memory
        windows = (simulation_days * 1440) / self.aggregation_interval
        aggregation_memory = windows * num_primitives * metric_size

        # Convert to MB
        estimates = {
            "buffer_mb": buffer_memory / (1024 * 1024),
            "cache_mb": cache_memory / (1024 * 1024),
            "aggregation_mb": aggregation_memory / (1024 * 1024),
            "total_mb": (buffer_memory + cache_memory + aggregation_memory) / (1024 * 1024),
        }

        return estimates

    def recommend_settings(
        self, num_primitives: int, simulation_days: int, available_memory_mb: float
    ) -> "PerformanceConfig":
        """Recommend configuration based on simulation parameters.

        Args:
            num_primitives: Number of primitives
            simulation_days: Simulation duration
            available_memory_mb: Available memory budget

        Returns:
            Recommended PerformanceConfig
        """
        # Calculate data volume (currently not used for preset selection)
        # total_minutes = simulation_days * 1440
        # events_per_minute = num_primitives * ConfigLoader.get_required(_config, 'validation.buffer.min_size')
        # total_events = total_minutes * events_per_minute

        # Choose preset based on scale - using config thresholds
        val_config = ConfigLoader.get_required(_config, "validation")

        if simulation_days <= 1 and num_primitives <= val_config["buffer"]["min_size"]:
            config = PerformanceConfig.from_preset(ConfigPreset.DEVELOPMENT)
        elif simulation_days <= 7 and num_primitives <= 50:
            config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
        elif simulation_days >= 30:
            config = PerformanceConfig.from_preset(ConfigPreset.LONG_RUNNING)
        elif available_memory_mb < 100:
            config = PerformanceConfig.from_preset(ConfigPreset.MEMORY_OPTIMIZED)
        else:
            config = PerformanceConfig.from_preset(ConfigPreset.FAST)

        # Adjust based on memory
        estimated = config.estimate_memory_usage(num_primitives, simulation_days)

        if estimated["total_mb"] > available_memory_mb:
            # Reduce memory usage
            scale_factor = available_memory_mb / estimated["total_mb"]
            val_config = ConfigLoader.get_required(_config, "validation")
            config.observable_buffer_size = max(
                val_config["buffer"]["min_size"], int(config.observable_buffer_size * scale_factor)
            )
            config.cache_max_size = max(val_config["cache"]["min_size"], int(config.cache_max_size * scale_factor))
            config.sampling_rate = min(val_config["sampling"]["max_rate"], int(config.sampling_rate / scale_factor))

        config.max_memory_mb = available_memory_mb * 0.8  # Use 80% of available

        return config

    def get_summary(self) -> str:
        """Get human-readable configuration summary.

        Returns:
            Configuration summary string
        """
        lines = [
            f"Performance Configuration: {self.name}",
            f"  {self.description}",
            "",
            "Memory Settings:",
            f"  Buffer size: {self.observable_buffer_size} events",
            f"  Cache size: {self.cache_max_size} events",
            f"  Memory limit: {self.max_memory_mb:.0f} MB",
            "",
            "Sampling Settings:",
            f"  Mode: {self.simulation_mode.value}",
            f"  Sampling rate: 1/{self.sampling_rate} ({100 / self.sampling_rate:.1f}%)",
            f"  Global observables: {self.enable_global_observables}",
            "",
            "Processing Settings:",
            f"  Aggregation: every {self.aggregation_interval:.0f} minutes",
            f"  Database flush: every {self.flush_interval:.0f} minutes",
            f"  Batch size: {self.batch_size} events",
            "",
            "Execution Settings:",
            f"  Progress: {self.enable_progress}",
            f"  Checkpoints: {'every ' + str(int(self.checkpoint_interval)) + ' min' if self.checkpoint_interval else 'disabled'}",
            f"  Chunk size: {self.chunk_size_days} days",
            "",
            "Monitoring:",
            f"  Enabled: {self.enable_monitoring}",
            f"  Interval: every {self.monitoring_interval:.0f} minutes",
        ]

        return "\n".join(lines)
