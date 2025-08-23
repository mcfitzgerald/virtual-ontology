"""Base primitive class for SimPy-based building blocks.

This module defines the foundational primitive that all other primitives
extend. It provides core functionality for observable emission and
configuration management.
"""

from typing import Dict, Any, Optional, List, Callable, Deque, Set, Tuple, DefaultDict
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from collections import deque, defaultdict
from enum import Enum
import simpy
from datetime import datetime
import math
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import configuration
try:
    from config.config_loader import ConfigLoader
    _twin_config = ConfigLoader.load_config('twin_model')
except:
    # Fallback for testing
    _twin_config = {
        'events': {'batcher_batch_size': 100},
        'monitoring': {
            'memory_threshold_mb': 500.0,
            'event_rate_threshold': 100.0,
            'check_interval': 60.0
        }
    }

# Import centralized logging
try:
    from twin_model.logging_config import SimulationLogger
    logger = SimulationLogger.get_logger(__name__)
except ImportError:
    # Fallback to standard logging if logging_config not available
    logger = logging.getLogger(__name__)


@dataclass
class PrimitiveConfig:
    """Configuration for a primitive instance.

    This dataclass holds all configuration values loaded from manifests,
    providing a clean separation between structure (ontology) and
    values (manifests).

    Attributes:
        id: Unique identifier for this primitive instance
        type: Type of primitive (Equipment, Buffer, Source, etc.)
        properties: Type-checked properties from manifest
        relationships: Dict of relationship type to related primitive IDs
        metadata: Additional context for debugging and analysis
    """

    id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value with optional default.

        Args:
            key: Property name to retrieve
            default: Value to return if property not found

        Returns:
            Property value or default
        """
        return self.properties.get(key, default)

    def validate(self) -> None:
        """Validate configuration against expected schema.

        Raises:
            ValueError: If required properties are missing or invalid
        """
        if not self.id:
            raise ValueError("Primitive ID is required")
        if not self.type:
            raise ValueError("Primitive type is required")


class SimulationMode(str, Enum):
    """Simulation data collection modes.
    
    Modes:
        DETAILED: Full observables, every event recorded
        PRODUCTION: Sampled data at configurable intervals
        FAST: Minimal logging, critical events and KPIs only
    """
    DETAILED = "detailed"
    PRODUCTION = "production"
    FAST = "fast"


class SamplingConfig:
    """Configuration for observable sampling and performance optimization.
    
    This class controls how events are collected and stored during simulation,
    providing trade-offs between data completeness and performance.
    
    Attributes:
        mode: Simulation mode controlling data collection strategy
        sampling_rate: Record every Nth event (1 = all events)
        aggregation_interval: Time window for aggregating metrics (minutes)
        critical_events: Event types that bypass sampling (always recorded)
        buffer_size: Maximum events to keep in memory per primitive
        enable_global_observables: Whether to emit to global event bus
    """
    
    def __init__(
        self,
        mode: SimulationMode = SimulationMode.PRODUCTION,
        sampling_rate: int = 10,
        aggregation_interval: float = 5.0,
        buffer_size: int = 1000,
        enable_global_observables: bool = False
    ) -> None:
        """Initialize sampling configuration.
        
        Args:
            mode: Data collection mode (DETAILED, PRODUCTION, or FAST)
            sampling_rate: Event sampling frequency (1 = every event, 10 = every 10th)
            aggregation_interval: Time window for metric aggregation in minutes
            buffer_size: Maximum events to keep in circular buffer
            enable_global_observables: Whether to duplicate events to global bus
        """
        self.mode = mode
        self.sampling_rate = max(1, sampling_rate)  # Ensure at least 1
        self.aggregation_interval = aggregation_interval
        self.buffer_size = buffer_size
        self.enable_global_observables = enable_global_observables
        
        # Critical events always recorded regardless of sampling
        self.critical_events: Set[str] = {
            "failure",
            "equipment_failure", 
            "state_change",
            "maintenance",
            "planned_maintenance",
            "changeover",
            "cascade_failure_triggered"
        }
        
        # Event counter for sampling decisions
        self.event_counter: int = 0
        
    def should_record_event(self, event_type: str, is_critical: bool = False) -> bool:
        """Determine if an event should be recorded based on sampling config.
        
        Args:
            event_type: Type of event being emitted
            is_critical: Override flag to mark event as critical
            
        Returns:
            True if event should be recorded, False otherwise
        """
        # Always record if explicitly marked as critical
        if is_critical:
            return True
            
        # Always record critical events
        if event_type in self.critical_events:
            return True
            
        # In FAST mode, only record critical events
        if self.mode == SimulationMode.FAST:
            return False
            
        # In DETAILED mode, record everything
        if self.mode == SimulationMode.DETAILED:
            return True
            
        # In PRODUCTION mode, apply sampling
        self.event_counter += 1
        return self.event_counter % self.sampling_rate == 0


class ObservableBuffer:
    """Circular buffer for observables with automatic memory management.
    
    Uses collections.deque with maxlen for efficient circular buffer behavior.
    When the buffer is full, oldest events are automatically discarded.
    Optionally supports flushing to external storage via callback.
    
    Attributes:
        buffer: Deque with maximum length for circular behavior  
        buffer_size: Maximum number of events to keep in memory
        flush_callback: Optional callback for persisting data
        total_events: Counter of all events seen (including discarded)
        discarded_events: Counter of events dropped due to buffer overflow
    """
    
    def __init__(
        self, 
        buffer_size: int = 1000,
        flush_callback: Optional[Callable[[List[Dict[str, Any]]], None]] = None
    ) -> None:
        """Initialize circular buffer with optional flush callback.
        
        Args:
            buffer_size: Maximum events to keep (default 1000)
            flush_callback: Optional function to call when flushing data
        """
        # Use deque with maxlen for automatic circular buffer behavior
        # As noted in Python docs, when maxlen is set, older items are
        # automatically discarded when buffer is full
        self.buffer: Deque[Dict[str, Any]] = deque(maxlen=buffer_size)
        self.buffer_size = buffer_size
        self.flush_callback = flush_callback
        self.total_events: int = 0
        self.discarded_events: int = 0
        
    def append(self, event: Dict[str, Any]) -> None:
        """Add event to buffer, potentially discarding oldest.
        
        Args:
            event: Event dictionary to add to buffer
        """
        # Track if we're about to discard an event
        if len(self.buffer) == self.buffer_size:
            self.discarded_events += 1
            
        self.buffer.append(event)
        self.total_events += 1
        
    def flush(self) -> List[Dict[str, Any]]:
        """Flush buffer contents and optionally persist via callback.
        
        Returns:
            List of flushed events
        """
        if not self.buffer:
            return []
            
        # Convert deque to list for processing
        events = list(self.buffer)
        
        # Call flush callback if provided
        if self.flush_callback:
            try:
                self.flush_callback(events)
            except Exception as e:
                # Log error but don't fail simulation
                logger.warning(f"Flush callback failed: {e}", exc_info=True)
                
        # Clear buffer after flush
        self.buffer.clear()
        
        return events
        
    def get_recent(self, n: int) -> List[Dict[str, Any]]:
        """Get n most recent events without removing them.
        
        Args:
            n: Number of recent events to retrieve
            
        Returns:
            List of n most recent events (or all if fewer than n)
        """
        if n >= len(self.buffer):
            return list(self.buffer)
        
        # Use negative indexing to get last n items efficiently
        return list(self.buffer)[-n:]
        
    def get_stats(self) -> Dict[str, int]:
        """Get buffer statistics for monitoring.
        
        Returns:
            Dictionary with buffer statistics
        """
        return {
            "buffer_size": self.buffer_size,
            "current_count": len(self.buffer),
            "total_events": self.total_events,
            "discarded_events": self.discarded_events,
            "utilization_percent": (len(self.buffer) / self.buffer_size * 100) if self.buffer_size > 0 else 0
        }


class EventBatcher:
    """Batch similar events for efficient processing.
    
    Groups events by type and time window to reduce individual callbacks
    and improve performance. This reduces the overhead of processing
    each event individually, especially useful for high-frequency events.
    
    Attributes:
        batch_window: Time window for batching (simulation minutes)
        batch_size: Maximum events per batch before forcing flush
        pending_batches: Dict of pending event batches by type and window
        current_window: Current time window being processed
    """
    
    def __init__(
        self,
        batch_window: float = 5.0,
        batch_size: int = 100
    ) -> None:
        """Initialize event batcher with window and size parameters.
        
        Args:
            batch_window: Time window for grouping events (default 5 minutes)
            batch_size: Maximum batch size before forcing flush (default 100)
        """
        self.batch_window = batch_window
        self.batch_size = batch_size
        self.pending_batches: DefaultDict[Tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
        self.current_window: int = 0
        
    def add_event(
        self, 
        event: Dict[str, Any],
        timestamp: float
    ) -> Optional[List[Dict[str, Any]]]:
        """Add event to batch, return batch if ready.
        
        Groups events by type and time window. Returns completed batches
        when either the window changes or batch size is exceeded.
        
        Args:
            event: Event data to batch
            timestamp: Current simulation time
            
        Returns:
            Completed batch if ready, None otherwise
        """
        # Calculate time window for this event
        window = int(timestamp // self.batch_window)
        event_type = event.get("event_type", "unknown")
        
        # Key for batching (event type + time window)
        batch_key = (event_type, window)
        
        # Check if we've moved to a new window
        if window > self.current_window:
            # Flush all batches from previous windows
            flushed = self._flush_old_windows(window)
            self.current_window = window
            if flushed:
                # Return the first batch, others will be returned on subsequent calls
                return flushed[0] if flushed else None
        
        # Add event to its batch
        self.pending_batches[batch_key].append(event)
        
        # Check if batch size exceeded
        if len(self.pending_batches[batch_key]) >= self.batch_size:
            # Flush this specific batch
            batch = self.pending_batches[batch_key]
            del self.pending_batches[batch_key]
            return batch
            
        return None
        
    def _flush_old_windows(self, new_window: int) -> List[List[Dict[str, Any]]]:
        """Flush all batches from windows older than the current one.
        
        Args:
            new_window: The new current window number
            
        Returns:
            List of flushed batches
        """
        flushed_batches = []
        
        # Find all batches from old windows
        keys_to_flush = [
            key for key in self.pending_batches
            if key[1] < new_window
        ]
        
        # Flush each old batch
        for key in keys_to_flush:
            if self.pending_batches[key]:  # Only flush non-empty batches
                flushed_batches.append(self.pending_batches[key])
            del self.pending_batches[key]
            
        return flushed_batches
        
    def flush_all(self) -> List[List[Dict[str, Any]]]:
        """Force flush all pending batches.
        
        Returns:
            List of all flushed batches
        """
        all_batches = []
        
        for batch in self.pending_batches.values():
            if batch:  # Only include non-empty batches
                all_batches.append(batch)
                
        self.pending_batches.clear()
        
        return all_batches
        
    def get_stats(self) -> Dict[str, Any]:
        """Get batcher statistics.
        
        Returns:
            Dictionary with batching statistics
        """
        total_pending = sum(len(batch) for batch in self.pending_batches.values())
        
        return {
            "batch_window": self.batch_window,
            "batch_size": self.batch_size,
            "current_window": self.current_window,
            "pending_batch_count": len(self.pending_batches),
            "total_pending_events": total_pending,
            "batches_by_type": {
                event_type: len(batch)
                for (event_type, _), batch in self.pending_batches.items()
            }
        }


class IncrementalAggregator:
    """Incremental statistics aggregator for time-windowed metrics.
    
    Efficiently computes running statistics without storing all data points.
    Uses Welford's algorithm for numerically stable variance calculation.
    This allows for constant memory usage regardless of data size.
    
    Attributes:
        window_size: Time window for aggregation (simulation minutes)
        metrics: Dict of metric aggregators by name
        current_window_start: Start time of current aggregation window
    """
    
    def __init__(self, window_size: float = 5.0) -> None:
        """Initialize aggregator with window size.
        
        Args:
            window_size: Time window for aggregation in minutes (default 5)
        """
        self.window_size = window_size
        self.metrics: Dict[str, 'MetricAggregator'] = {}
        self.current_window_start: float = 0.0
        self.completed_windows: List[Dict[str, Any]] = []
        
    def add_value(
        self,
        metric_name: str,
        value: float,
        timestamp: float
    ) -> Optional[Dict[str, Any]]:
        """Add value to aggregator, return window summary if complete.
        
        Args:
            metric_name: Name of the metric being tracked
            value: Numeric value to add
            timestamp: Current simulation time
            
        Returns:
            Completed window statistics if window finished, None otherwise
        """
        # Check if we need to start a new window
        window_end = self.current_window_start + self.window_size
        
        if timestamp >= window_end:
            # Complete current window and start new one
            summary = self._complete_window(timestamp)
            self.current_window_start = (timestamp // self.window_size) * self.window_size
            
            # Add value to new window
            self._ensure_metric(metric_name).add(value)
            
            return summary
        else:
            # Add to current window
            self._ensure_metric(metric_name).add(value)
            return None
            
    def _ensure_metric(self, metric_name: str) -> 'MetricAggregator':
        """Ensure metric aggregator exists.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            MetricAggregator for the metric
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = MetricAggregator()
        return self.metrics[metric_name]
        
    def _complete_window(self, timestamp: float) -> Dict[str, Any]:
        """Complete current window and return statistics.
        
        Args:
            timestamp: Current simulation time
            
        Returns:
            Dictionary of aggregated statistics for the window
        """
        summary = {
            "window_start": self.current_window_start,
            "window_end": self.current_window_start + self.window_size,
            "timestamp": timestamp,
            "metrics": {}
        }
        
        # Collect statistics from each metric
        for metric_name, aggregator in self.metrics.items():
            stats = aggregator.get_stats()
            if stats["count"] > 0:  # Only include metrics with data
                summary["metrics"][metric_name] = stats
                
        # Reset aggregators for next window
        self.metrics.clear()
        
        # Store completed window
        self.completed_windows.append(summary)
        
        return summary
        
    def get_current_stats(self) -> Dict[str, Any]:
        """Get statistics for current incomplete window.
        
        Returns:
            Current window statistics
        """
        return {
            "window_start": self.current_window_start,
            "window_size": self.window_size,
            "metrics": {
                name: agg.get_stats()
                for name, agg in self.metrics.items()
            }
        }
        
    def get_history(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get last n completed windows.
        
        Args:
            n: Number of windows to retrieve
            
        Returns:
            List of completed window summaries
        """
        return self.completed_windows[-n:] if n > 0 else []


class MetricAggregator:
    """Single metric aggregator using Welford's algorithm.
    
    Computes mean, variance, min, max incrementally without storing values.
    This provides O(1) memory usage and numerically stable calculations.
    
    Reference: Welford, B. P. (1962). "Note on a method for calculating 
    corrected sums of squares and products". Technometrics. 4 (3): 419–420.
    """
    
    def __init__(self) -> None:
        """Initialize empty aggregator."""
        self.count: int = 0
        self.mean: float = 0.0
        self.m2: float = 0.0  # Sum of squared differences from mean
        self.min_value: Optional[float] = None
        self.max_value: Optional[float] = None
        
    def add(self, value: float) -> None:
        """Add value using Welford's online algorithm.
        
        Args:
            value: Numeric value to add to aggregation
        """
        self.count += 1
        
        # Update min/max
        if self.min_value is None or value < self.min_value:
            self.min_value = value
        if self.max_value is None or value > self.max_value:
            self.max_value = value
            
        # Welford's algorithm for mean and variance
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2
        
    def get_stats(self) -> Dict[str, float]:
        """Get current aggregated statistics.
        
        Returns:
            Dictionary with count, mean, variance, stddev, min, max
        """
        if self.count == 0:
            return {
                "count": 0,
                "mean": 0.0,
                "variance": 0.0,
                "stddev": 0.0,
                "min": 0.0,
                "max": 0.0
            }
            
        variance = self.m2 / self.count if self.count > 0 else 0.0
        stddev = math.sqrt(variance) if variance > 0 else 0.0
        
        return {
            "count": self.count,
            "mean": self.mean,
            "variance": variance,
            "stddev": stddev,
            "min": self.min_value or 0.0,
            "max": self.max_value or 0.0
        }
        
    def merge(self, other: 'MetricAggregator') -> None:
        """Merge another aggregator into this one.
        
        Uses parallel algorithm for combining statistics.
        
        Args:
            other: Another MetricAggregator to merge
        """
        if other.count == 0:
            return
            
        if self.count == 0:
            # Just copy the other aggregator
            self.count = other.count
            self.mean = other.mean
            self.m2 = other.m2
            self.min_value = other.min_value
            self.max_value = other.max_value
            return
            
        # Combine using parallel algorithm
        combined_count = self.count + other.count
        delta = other.mean - self.mean
        
        # Update mean
        combined_mean = self.mean + delta * other.count / combined_count
        
        # Update M2 (sum of squared differences)
        combined_m2 = self.m2 + other.m2 + delta * delta * self.count * other.count / combined_count
        
        # Update min/max
        if other.min_value is not None:
            if self.min_value is None or other.min_value < self.min_value:
                self.min_value = other.min_value
        if other.max_value is not None:
            if self.max_value is None or other.max_value > self.max_value:
                self.max_value = other.max_value
                
        # Store combined values
        self.count = combined_count
        self.mean = combined_mean
        self.m2 = combined_m2


class ProgressCallback(ABC):
    """Abstract base class for progress reporting.
    
    Implement this class to create custom progress reporters
    for long-running simulations. Callbacks are invoked periodically
    during simulation execution.
    """
    
    @abstractmethod
    def __call__(self,
                 current_time: float,
                 total_time: float,
                 events_processed: int,
                 memory_usage_mb: float,
                 **kwargs: Any) -> None:
        """Report simulation progress.
        
        Args:
            current_time: Current simulation time
            total_time: Total simulation duration
            events_processed: Number of events processed so far
            memory_usage_mb: Current memory usage in MB
            **kwargs: Additional metrics (e.g., cache_size, db_inserts)
        """
        pass


class ConsoleProgressReporter(ProgressCallback):
    """Console-based progress reporter with configurable intervals.
    
    Prints progress updates to console showing percentage complete,
    time remaining, memory usage, and event processing rate.
    
    Attributes:
        report_interval: Seconds between progress reports
        last_report_time: Last time progress was reported
        start_time: Real-world start time of simulation
    """
    
    def __init__(self, report_interval: float = 5.0) -> None:
        """Initialize console reporter.
        
        Args:
            report_interval: Seconds between progress reports
        """
        import time
        self.report_interval = report_interval
        self.last_report_time: float = 0
        self.start_time: float = time.time()
        self.last_events: int = 0
        
    def __call__(self,
                 current_time: float,
                 total_time: float,
                 events_processed: int,
                 memory_usage_mb: float,
                 **kwargs: Any) -> None:
        """Report progress to console.
        
        Args:
            current_time: Current simulation time
            total_time: Total simulation duration
            events_processed: Number of events processed
            memory_usage_mb: Current memory usage
            **kwargs: Additional metrics
        """
        import time
        
        now = time.time()
        if now - self.last_report_time < self.report_interval:
            return
            
        # Calculate metrics
        progress = (current_time / total_time) * 100 if total_time > 0 else 0
        elapsed = now - self.start_time
        
        # Estimate time remaining
        if current_time > 0:
            rate = current_time / elapsed
            remaining = (total_time - current_time) / rate if rate > 0 else 0
        else:
            remaining = 0
            
        # Calculate event rate
        events_delta = events_processed - self.last_events
        time_delta = now - self.last_report_time if self.last_report_time > 0 else elapsed
        event_rate = events_delta / time_delta if time_delta > 0 else 0
        
        # Format output
        print(f"  Progress: {progress:5.1f}% | "
              f"Time: {current_time:.0f}/{total_time:.0f} | "
              f"ETA: {remaining:.1f}s | "
              f"Memory: {memory_usage_mb:.1f}MB | "
              f"Events: {events_processed:,} ({event_rate:.0f}/s)")
        
        # Print additional metrics if provided
        if kwargs:
            extra = " | ".join(f"{k}: {v}" for k, v in kwargs.items())
            print(f"    {extra}")
        
        self.last_report_time = now
        self.last_events = events_processed


class SimulationMonitor:
    """Monitor simulation health and performance metrics.
    
    Tracks memory usage, event rates, and simulation performance
    to detect issues and provide diagnostics during execution.
    
    Attributes:
        env: SimPy environment
        memory_threshold_mb: Memory warning threshold
        event_rate_threshold: Minimum acceptable event rate
        check_interval: Minutes between health checks
        metrics: Performance metrics dictionary
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 memory_threshold_mb: float = None,
                 event_rate_threshold: float = None,
                 check_interval: float = None) -> None:
        """Initialize simulation monitor.
        
        Args:
            env: SimPy environment to monitor
            memory_threshold_mb: Memory usage warning threshold (from config if None)
            event_rate_threshold: Minimum events/second threshold (from config if None)
            check_interval: Simulation minutes between checks (from config if None)
        """
        self.env = env
        # Use config values if not provided
        self.memory_threshold_mb = memory_threshold_mb or _twin_config['monitoring']['memory_threshold_mb']
        self.event_rate_threshold = event_rate_threshold or _twin_config['monitoring']['event_rate_threshold']
        self.check_interval = check_interval or _twin_config['monitoring']['check_interval']
        
        # Metrics tracking
        self.metrics: Dict[str, Any] = {
            "start_time": None,
            "events_total": 0,
            "memory_samples": [],
            "event_rate_samples": [],
            "warnings": []
        }
        
        # Start monitoring process
        self.env.process(self._monitor_process())
        
    def _monitor_process(self) -> simpy.events.Process:
        """Background process for health monitoring.
        
        Yields:
            Timeout events for periodic checking
        """
        import tracemalloc
        import time
        
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            
        self.metrics["start_time"] = time.time()
        last_events = 0
        last_check = time.time()
        
        while True:
            yield self.env.timeout(self.check_interval)
            
            # Memory check
            current, peak = tracemalloc.get_traced_memory()
            memory_mb = current / (1024 * 1024)
            self.metrics["memory_samples"].append({
                "time": self.env.now,
                "memory_mb": memory_mb
            })
            
            if memory_mb > self.memory_threshold_mb:
                warning = f"High memory usage: {memory_mb:.1f}MB at t={self.env.now}"
                self.metrics["warnings"].append(warning)
                print(f"  ⚠️  {warning}")
            
            # Event rate check
            now = time.time()
            time_delta = now - last_check
            event_delta = self.metrics["events_total"] - last_events
            
            if time_delta > 0:
                event_rate = event_delta / time_delta
                self.metrics["event_rate_samples"].append({
                    "time": self.env.now,
                    "rate": event_rate
                })
                
                if event_rate < self.event_rate_threshold and self.env.now > 0:
                    warning = f"Low event rate: {event_rate:.1f}/s at t={self.env.now}"
                    self.metrics["warnings"].append(warning)
                    print(f"  ⚠️  {warning}")
            
            last_events = self.metrics["events_total"]
            last_check = now
    
    def record_event(self) -> None:
        """Record that an event was processed."""
        self.metrics["events_total"] += 1
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get current monitoring metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        import time
        
        elapsed = time.time() - self.metrics["start_time"] if self.metrics["start_time"] else 0
        
        return {
            "simulation_time": self.env.now,
            "real_time_seconds": elapsed,
            "speed_factor": self.env.now / elapsed if elapsed > 0 else 0,
            "total_events": self.metrics["events_total"],
            "avg_event_rate": self.metrics["events_total"] / elapsed if elapsed > 0 else 0,
            "memory_current_mb": self.metrics["memory_samples"][-1]["memory_mb"] if self.metrics["memory_samples"] else 0,
            "memory_max_mb": max(s["memory_mb"] for s in self.metrics["memory_samples"]) if self.metrics["memory_samples"] else 0,
            "warnings": self.metrics["warnings"]
        }


class BasePrimitive(ABC):
    """Base class for all SimPy primitives.

    All primitives must emit observables for discovery-based learning.
    This base class provides core functionality for:
    - Observable emission and storage
    - Configuration management
    - SimPy environment integration
    - Common event patterns

    The observable stream is the primary mechanism through which the
    LLM discovers relationships and patterns without prescriptive rules.
    """

    def __init__(
        self, 
        env: simpy.Environment, 
        config: PrimitiveConfig,
        sampling_config: Optional[SamplingConfig] = None
    ) -> None:
        """Initialize primitive with configuration and performance optimization.

        Args:
            env: SimPy environment for discrete event simulation
            config: Primitive configuration from manifest
            sampling_config: Optional sampling configuration for performance
        """
        self.env = env
        self.config = config
        self.config.validate()
        
        # Set up logging
        self.logger = logger
        
        # Performance configuration
        self.sampling_config = sampling_config or SamplingConfig()
        
        # Replace unbounded list with circular buffer for memory efficiency
        # This prevents memory exhaustion in long simulations
        self.observable_buffer = ObservableBuffer(
            buffer_size=self.sampling_config.buffer_size
        )
        
        # Keep reference to old interface for compatibility (read-only view)
        # This will be deprecated in future versions
        self.observables = self.observable_buffer.buffer

        # Process handle for the main process if any
        self.process: Optional[simpy.Process] = None

        # Track primitive state for debugging
        self.is_initialized: bool = False
        self.is_running: bool = False
        
        # Performance metrics
        self.events_emitted: int = 0
        self.events_sampled: int = 0
        
        # Event batching for performance (Phase 2.1)
        self.event_batcher = EventBatcher(
            batch_window=self.sampling_config.aggregation_interval,
            batch_size=_twin_config['events']['batcher_batch_size']
        )
        
        # Incremental aggregation for metrics (Phase 2.2)
        self.metric_aggregator = IncrementalAggregator(
            window_size=self.sampling_config.aggregation_interval
        )
        
        # Log initialization
        logger.info(
            f"Initialized {self.__class__.__name__}",
            extra={'extra_data': {
                'primitive_id': self.config.id,
                'primitive_type': self.config.type,
                'buffer_size': self.sampling_config.buffer_size,
                'sampling_rate': self.sampling_config.sampling_rate,
                'mode': self.sampling_config.mode.value
            }}
        )

    @abstractmethod
    def start(self) -> None:
        """Start the primitive's processes.

        This method should be called after all primitives are created
        and wired together. It typically starts one or more SimPy
        processes that represent the primitive's behavior.
        """
        pass

    def emit_observable(
        self, event_type: str, details: Dict[str, Any], severity: str = "INFO", is_critical: bool = False
    ) -> None:
        """Emit an observable event with sampling and performance optimization.

        This is the primary mechanism for primitives to communicate
        their state and behavior. Events are now sampled based on
        configuration to prevent memory exhaustion in long simulations.

        Args:
            event_type: Type of event (state_change, production, failure, etc.)
            details: Event-specific details with rich context
            severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            is_critical: Mark event as critical to bypass sampling
        """
        # Track total events for metrics
        self.events_emitted += 1
        
        # Check if event is explicitly marked as critical in details
        if not is_critical and details and isinstance(details, dict):
            is_critical = details.get('critical', False)
        
        # Apply sampling logic to reduce memory pressure
        if not self.sampling_config.should_record_event(event_type, is_critical):
            # Event filtered by sampling - skip recording
            return
            
        # Event passed sampling - track it
        self.events_sampled += 1
        
        # Log debug-level event emission
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Event emitted: {event_type}",
                extra={'extra_data': {
                    'primitive_id': self.config.id,
                    'event_type': event_type,
                    'timestamp': self.env.now,
                    'details': details
                }}
            )
        
        # Build observable with all context
        observable = {
            "timestamp": self.env.now,
            "datetime": datetime.fromtimestamp(
                self.env.now * 60
            ),  # Convert minutes to datetime
            "primitive_id": self.config.id,
            "primitive_type": self.config.type,
            "event_type": event_type,
            "severity": severity,
            **details,
        }
        
        # Add to circular buffer (automatically discards oldest if full)
        self.observable_buffer.append(observable)

        # Conditionally emit to global event bus based on configuration
        # This reduces duplication and memory usage
        if self.sampling_config.enable_global_observables and hasattr(self.env, "global_observables"):
            # Only emit critical events to global bus in PRODUCTION mode
            if self.sampling_config.mode == SimulationMode.PRODUCTION:
                if event_type in self.sampling_config.critical_events:
                    self.env.global_observables.append(observable)
            else:
                self.env.global_observables.append(observable)

    def get_observables(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve observables with optional filtering from circular buffer.

        Args:
            event_type: Filter by specific event type
            start_time: Filter events after this simulation time
            end_time: Filter events before this simulation time

        Returns:
            Filtered list of observable events
        """
        # Get all events from buffer (already limited by buffer size)
        result = list(self.observable_buffer.buffer)

        if event_type:
            result = [o for o in result if o["event_type"] == event_type]

        if start_time is not None:
            result = [o for o in result if o["timestamp"] >= start_time]

        if end_time is not None:
            result = [o for o in result if o["timestamp"] <= end_time]

        return result

    def connect_to(
        self, other: "BasePrimitive", relationship_type: str = "feeds_into"
    ) -> None:
        """Connect this primitive to another via relationship.

        Args:
            other: Target primitive to connect to
            relationship_type: Type of relationship (feeds_into, controls, monitors)
        """
        if relationship_type not in self.config.relationships:
            self.config.relationships[relationship_type] = []

        if other.config.id not in self.config.relationships[relationship_type]:
            self.config.relationships[relationship_type].append(other.config.id)

        self.emit_observable(
            event_type="relationship_established",
            details={
                "relationship_type": relationship_type,
                "target_id": other.config.id,
                "target_type": other.config.type,
            },
        )

    def initialize(self) -> None:
        """Initialize primitive before starting processes.

        Override this method to perform setup that requires all
        primitives to be created first (e.g., wiring relationships).
        """
        self.is_initialized = True
        self.emit_observable(
            event_type="primitive_initialized",
            details={
                "properties": self.config.properties,
                "relationships": self.config.relationships,
            },
        )

    def shutdown(self) -> None:
        """Gracefully shutdown the primitive.

        Override this method to perform cleanup when simulation ends.
        """
        self.is_running = False
        self.emit_observable(
            event_type="primitive_shutdown", details={"final_state": self.get_state()}
        )

    def emit_metric(
        self,
        metric_name: str,
        value: float
    ) -> Optional[Dict[str, Any]]:
        """Emit a metric value for aggregation.
        
        This method tracks numeric metrics over time windows using
        incremental statistics. Useful for KPIs like OEE, throughput, etc.
        
        Args:
            metric_name: Name of the metric (e.g., "oee", "throughput")
            value: Numeric value to aggregate
            
        Returns:
            Completed window statistics if window finished, None otherwise
        """
        return self.metric_aggregator.add_value(
            metric_name,
            value,
            self.env.now
        )
        
    def batch_emit_observable(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: str = "INFO"
    ) -> Optional[List[Dict[str, Any]]]:
        """Emit observable through batcher for efficient processing.
        
        Events are grouped by type and time window to reduce processing
        overhead. Use this for high-frequency events that can be processed
        in batches.
        
        Args:
            event_type: Type of event
            details: Event details
            severity: Event severity
            
        Returns:
            Completed batch if ready, None otherwise
        """
        # Build the event
        event = {
            "timestamp": self.env.now,
            "datetime": datetime.fromtimestamp(self.env.now * 60),
            "primitive_id": self.config.id,
            "primitive_type": self.config.type,
            "event_type": event_type,
            "severity": severity,
            **details,
        }
        
        # Add to batcher
        return self.event_batcher.add_event(event, self.env.now)
        
    def process_batches(self) -> List[List[Dict[str, Any]]]:
        """Process any pending batches.
        
        Call this periodically to flush pending batches.
        
        Returns:
            List of completed batches
        """
        return self.event_batcher.flush_all()
        
    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get current aggregated metrics.
        
        Returns:
            Current window statistics and history
        """
        return {
            "current": self.metric_aggregator.get_current_stats(),
            "history": self.metric_aggregator.get_history(10)
        }

    def flush_observables(self) -> List[Dict[str, Any]]:
        """Flush observable buffer and return events.
        
        This method can be called periodically to persist events to external
        storage and free memory. Useful for long-running simulations.
        
        Returns:
            List of flushed events
        """
        return self.observable_buffer.flush()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics for monitoring.
        
        Returns:
            Dictionary containing performance statistics
        """
        buffer_stats = self.observable_buffer.get_stats()
        
        return {
            "events_emitted": self.events_emitted,
            "events_sampled": self.events_sampled,
            "events_discarded": buffer_stats["discarded_events"],
            "sampling_efficiency": self.events_sampled / self.events_emitted if self.events_emitted > 0 else 0,
            "buffer_utilization": buffer_stats["utilization_percent"],
            "memory_saved_percent": (1 - self.events_sampled / self.events_emitted) * 100 if self.events_emitted > 0 else 0,
            "mode": self.sampling_config.mode.value,
            "sampling_rate": self.sampling_config.sampling_rate
        }

    def get_state(self) -> Dict[str, Any]:
        """Get current primitive state including performance metrics.

        Returns:
            Dictionary describing current primitive state and performance
        """
        buffer_stats = self.observable_buffer.get_stats()
        
        return {
            "id": self.config.id,
            "type": self.config.type,
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "relationships": self.config.relationships,
            # Performance metrics
            "events_emitted": self.events_emitted,
            "events_sampled": self.events_sampled,
            "sampling_rate": self.events_sampled / self.events_emitted if self.events_emitted > 0 else 0,
            # Buffer statistics
            "buffer_current_count": buffer_stats["current_count"],
            "buffer_total_events": buffer_stats["total_events"],
            "buffer_discarded_events": buffer_stats["discarded_events"],
            "buffer_utilization_percent": buffer_stats["utilization_percent"]
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"{self.__class__.__name__}(id={self.config.id}, type={self.config.type})"
        )
