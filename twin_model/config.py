"""Configuration system for performance optimization.

This module provides configuration management for simulation performance
settings, including presets for different scenarios and validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pathlib import Path
import json
import yaml
from twin_model.primitives.base import SimulationMode


class ConfigPreset(Enum):
    """Pre-defined configuration presets for common scenarios."""
    
    DEVELOPMENT = "development"  # Full data collection for debugging
    PRODUCTION = "production"    # Balanced performance and data
    FAST = "fast"                # Minimal data for speed
    MEMORY_OPTIMIZED = "memory_optimized"  # Aggressive memory limits
    LONG_RUNNING = "long_running"  # Optimized for 30+ day simulations
    REAL_TIME = "real_time"      # For real-time digital twin scenarios


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
    
    # Memory settings
    observable_buffer_size: int = 1000
    cache_max_size: int = 100000
    max_memory_mb: float = 500.0
    
    # Sampling settings
    sampling_rate: int = 10
    simulation_mode: SimulationMode = SimulationMode.PRODUCTION
    enable_global_observables: bool = False
    
    # Processing settings
    aggregation_interval: float = 300.0  # 5 minutes
    flush_interval: float = 600.0  # 10 minutes
    batch_size: int = 1000
    
    # Execution settings
    enable_progress: bool = True
    checkpoint_interval: Optional[float] = 1440.0  # Daily
    chunk_size_days: float = 1.0
    
    # Monitoring settings
    enable_monitoring: bool = True
    monitoring_interval: float = 60.0  # Every hour
    
    # Metadata
    name: str = "custom"
    description: str = ""
    
    @classmethod
    def from_preset(cls, preset: Union[ConfigPreset, str]) -> 'PerformanceConfig':
        """Create configuration from a preset.
        
        Args:
            preset: Preset name or ConfigPreset enum
            
        Returns:
            PerformanceConfig instance with preset values
        """
        if isinstance(preset, str):
            preset = ConfigPreset(preset)
            
        configs = {
            ConfigPreset.DEVELOPMENT: cls(
                name="development",
                description="Full data collection for debugging",
                observable_buffer_size=10000,
                cache_max_size=1000000,
                max_memory_mb=2000.0,
                sampling_rate=1,  # Keep everything
                simulation_mode=SimulationMode.DETAILED,
                enable_global_observables=True,
                aggregation_interval=60.0,  # Every minute
                flush_interval=300.0,  # Every 5 minutes
                batch_size=100,
                enable_progress=True,
                checkpoint_interval=144.0,  # Every 2.4 hours (>= chunk size)
                chunk_size_days=0.1,  # Small chunks (144 minutes)
                enable_monitoring=True,
                monitoring_interval=10.0  # Frequent checks
            ),
            
            ConfigPreset.PRODUCTION: cls(
                name="production",
                description="Balanced performance and data collection",
                observable_buffer_size=1000,
                cache_max_size=100000,
                max_memory_mb=500.0,
                sampling_rate=10,  # Keep 10%
                simulation_mode=SimulationMode.PRODUCTION,
                enable_global_observables=False,
                aggregation_interval=300.0,  # 5 minutes
                flush_interval=600.0,  # 10 minutes
                batch_size=1000,
                enable_progress=True,
                checkpoint_interval=1440.0,  # Daily
                chunk_size_days=1.0,
                enable_monitoring=True,
                monitoring_interval=60.0
            ),
            
            ConfigPreset.FAST: cls(
                name="fast",
                description="Minimal data collection for maximum speed",
                observable_buffer_size=100,
                cache_max_size=10000,
                max_memory_mb=100.0,
                sampling_rate=100,  # Keep 1%
                simulation_mode=SimulationMode.FAST,
                enable_global_observables=False,
                aggregation_interval=1440.0,  # Daily
                flush_interval=2880.0,  # Every 2 days
                batch_size=10000,
                enable_progress=False,
                checkpoint_interval=None,  # No checkpoints
                chunk_size_days=7.0,  # Weekly chunks
                enable_monitoring=False,
                monitoring_interval=1440.0
            ),
            
            ConfigPreset.MEMORY_OPTIMIZED: cls(
                name="memory_optimized",
                description="Aggressive memory optimization",
                observable_buffer_size=50,
                cache_max_size=5000,
                max_memory_mb=50.0,
                sampling_rate=1000,  # Keep 0.1%
                simulation_mode=SimulationMode.FAST,
                enable_global_observables=False,
                aggregation_interval=60.0,  # Frequent aggregation
                flush_interval=120.0,  # Frequent flush
                batch_size=500,
                enable_progress=True,
                checkpoint_interval=720.0,  # Every 12 hours
                chunk_size_days=0.5,
                enable_monitoring=True,
                monitoring_interval=30.0  # Frequent memory checks
            ),
            
            ConfigPreset.LONG_RUNNING: cls(
                name="long_running",
                description="Optimized for 30+ day simulations",
                observable_buffer_size=500,
                cache_max_size=50000,
                max_memory_mb=200.0,
                sampling_rate=50,  # Keep 2%
                simulation_mode=SimulationMode.PRODUCTION,
                enable_global_observables=False,
                aggregation_interval=1440.0,  # Daily
                flush_interval=2880.0,  # Every 2 days
                batch_size=5000,
                enable_progress=True,
                checkpoint_interval=2880.0,  # Every 2 days
                chunk_size_days=2.0,
                enable_monitoring=True,
                monitoring_interval=720.0  # Every 12 hours
            ),
            
            ConfigPreset.REAL_TIME: cls(
                name="real_time",
                description="For real-time digital twin scenarios",
                observable_buffer_size=100,
                cache_max_size=1000,
                max_memory_mb=100.0,
                sampling_rate=1,  # Keep all recent
                simulation_mode=SimulationMode.PRODUCTION,
                enable_global_observables=False,
                aggregation_interval=1.0,  # Every minute
                flush_interval=5.0,  # Every 5 minutes
                batch_size=100,
                enable_progress=True,
                checkpoint_interval=60.0,  # Hourly (60 minutes)
                chunk_size_days=0.0417,  # 1 hour chunks (60 minutes)
                enable_monitoring=True,
                monitoring_interval=1.0  # Every minute
            )
        }
        
        return configs[preset]
    
    @classmethod
    def from_json(cls, path: Union[str, Path]) -> 'PerformanceConfig':
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
            
        with open(path, 'r') as f:
            data = json.load(f)
            
        # Handle simulation mode enum
        if 'simulation_mode' in data:
            mode_str = data['simulation_mode']
            if isinstance(mode_str, str):
                data['simulation_mode'] = SimulationMode[mode_str.upper()]
                
        config = cls(**data)
        
        # Validate
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
            
        return config
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> 'PerformanceConfig':
        """Load configuration from YAML file.
        
        Args:
            path: Path to configuration file
            
        Returns:
            PerformanceConfig instance
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
            
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            
        # Handle simulation mode enum
        if 'simulation_mode' in data:
            mode_str = data['simulation_mode']
            if isinstance(mode_str, str):
                data['simulation_mode'] = SimulationMode[mode_str.upper()]
                
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
        data['simulation_mode'] = self.simulation_mode.value
        
        with open(path, 'w') as f:
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
        data['simulation_mode'] = self.simulation_mode.value
        
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def validate(self) -> List[str]:
        """Validate configuration settings.
        
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        # Buffer size validation
        if self.observable_buffer_size < 10:
            errors.append("observable_buffer_size must be at least 10")
        if self.observable_buffer_size > 1000000:
            errors.append("observable_buffer_size too large (max 1M)")
            
        # Cache size validation
        if self.cache_max_size < 100:
            errors.append("cache_max_size must be at least 100")
            
        # Memory validation
        if self.max_memory_mb < 10:
            errors.append("max_memory_mb must be at least 10MB")
        if self.max_memory_mb > 100000:
            errors.append("max_memory_mb unrealistic (>100GB)")
            
        # Sampling rate validation
        if self.sampling_rate < 1:
            errors.append("sampling_rate must be at least 1")
        if self.sampling_rate > 10000:
            errors.append("sampling_rate too high (max 10000)")
            
        # Interval validation
        if self.aggregation_interval <= 0:
            errors.append("aggregation_interval must be positive")
        if self.flush_interval <= 0:
            errors.append("flush_interval must be positive")
            
        # Batch size validation
        if self.batch_size < 1:
            errors.append("batch_size must be at least 1")
        if self.batch_size > 100000:
            errors.append("batch_size too large (max 100k)")
            
        # Chunk size validation
        if self.chunk_size_days <= 0:
            errors.append("chunk_size_days must be positive")
        if self.chunk_size_days > 30:
            errors.append("chunk_size_days too large (max 30)")
            
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
        # Base estimates (bytes)
        event_size = 200  # Average event size
        metric_size = 50  # Average metric size
        
        # Buffer memory per primitive
        buffer_memory = num_primitives * self.observable_buffer_size * event_size
        
        # Cache memory (limited by max_size)
        cache_memory = min(
            self.cache_max_size * event_size,
            simulation_days * 1440 * 60 * event_size / self.sampling_rate  # Total events
        )
        
        # Aggregation memory
        windows = (simulation_days * 1440) / self.aggregation_interval
        aggregation_memory = windows * num_primitives * metric_size
        
        # Convert to MB
        estimates = {
            "buffer_mb": buffer_memory / (1024 * 1024),
            "cache_mb": cache_memory / (1024 * 1024),
            "aggregation_mb": aggregation_memory / (1024 * 1024),
            "total_mb": (buffer_memory + cache_memory + aggregation_memory) / (1024 * 1024)
        }
        
        return estimates
    
    def recommend_settings(self, num_primitives: int, simulation_days: int, 
                          available_memory_mb: float) -> 'PerformanceConfig':
        """Recommend configuration based on simulation parameters.
        
        Args:
            num_primitives: Number of primitives
            simulation_days: Simulation duration
            available_memory_mb: Available memory budget
            
        Returns:
            Recommended PerformanceConfig
        """
        # Calculate data volume
        total_minutes = simulation_days * 1440
        events_per_minute = num_primitives * 10  # Estimate
        total_events = total_minutes * events_per_minute
        
        # Choose preset based on scale
        if simulation_days <= 1 and num_primitives <= 10:
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
            config.observable_buffer_size = max(10, int(config.observable_buffer_size * scale_factor))
            config.cache_max_size = max(100, int(config.cache_max_size * scale_factor))
            config.sampling_rate = min(1000, int(config.sampling_rate / scale_factor))
            
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
            f"  Sampling rate: 1/{self.sampling_rate} ({100/self.sampling_rate:.1f}%)",
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
            f"  Interval: every {self.monitoring_interval:.0f} minutes"
        ]
        
        return "\n".join(lines)