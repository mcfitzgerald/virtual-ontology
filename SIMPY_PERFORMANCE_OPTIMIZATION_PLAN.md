# SimPy Performance Optimization Implementation Plan

## Executive Summary
This plan addresses critical performance bottlenecks preventing 30-day simulations from completing. Research indicates memory accumulation from unbounded observable lists is the primary issue, with millions of events causing GB-level memory usage and processing overhead.

## Root Cause Analysis

### Identified Bottlenecks
1. **Memory Accumulation**: Every primitive appends observables to ever-growing lists without cleanup
2. **Duplicate Storage**: Observables stored both locally (`self.observables`) and globally (`env.global_observables`)
3. **Excessive Event Generation**: 30 equipment pieces × thousands of events/minute × 43,200 minutes = millions of records
4. **Inefficient Data Structures**: Python lists performing poorly with millions of entries
5. **No Sampling/Aggregation**: Every single event recorded at full detail

### Performance Impact
- Current: 1-hour simulation barely completes, 30-day simulation times out
- Memory: GB-level usage causing system thrashing
- PyPy: Makes SimPy 2x SLOWER (confirmed by research)

## Implementation Phases

### Phase 1: Critical Memory Optimizations
**Objective**: Prevent memory exhaustion and enable basic long simulations

#### 1.1 Implement Circular Buffers
**File**: `twin_model/primitives/base.py`

**Implementation**:
```python
from collections import deque
from typing import Optional, Dict, Any, List, Deque
from enum import Enum

class ObservableBuffer:
    """Circular buffer for observables with automatic flushing.
    
    Attributes:
        buffer: Deque with maximum length for circular behavior
        buffer_size: Maximum number of events to keep in memory
        flush_callback: Optional callback for flushing data
    """
    
    def __init__(self, 
                 buffer_size: int = 1000,
                 flush_callback: Optional[Callable] = None) -> None:
        """Initialize circular buffer.
        
        Args:
            buffer_size: Maximum events to keep (default 1000)
            flush_callback: Optional function to call on flush
        """
        self.buffer: Deque[Dict[str, Any]] = deque(maxlen=buffer_size)
        self.flush_callback = flush_callback
        self.total_events: int = 0
```

**Requirements**:
- Use type hints for all parameters and return values
- Add comprehensive docstrings following Google style
- Include inline comments for complex logic
- Consult Context7 for `collections.deque` best practices

#### 1.2 Add Sampling Configuration
**File**: `twin_model/primitives/base.py`

**Implementation**:
```python
class SimulationMode(str, Enum):
    """Simulation data collection modes.
    
    Modes:
        DETAILED: Full observables, every event
        PRODUCTION: Sampled data at intervals
        FAST: Minimal logging, KPIs only
    """
    DETAILED = "detailed"
    PRODUCTION = "production"
    FAST = "fast"

class SamplingConfig:
    """Configuration for observable sampling.
    
    Attributes:
        mode: Simulation mode (DETAILED, PRODUCTION, FAST)
        sampling_rate: Record every Nth event (1 = all events)
        aggregation_interval: Seconds between aggregations
        critical_events: Event types to always record
    """
    
    def __init__(self,
                 mode: SimulationMode = SimulationMode.PRODUCTION,
                 sampling_rate: int = 10,
                 aggregation_interval: float = 300.0) -> None:
        """Initialize sampling configuration.
        
        Args:
            mode: Data collection mode
            sampling_rate: Event sampling rate (default every 10th)
            aggregation_interval: Aggregation window in seconds
        """
        self.mode = mode
        self.sampling_rate = sampling_rate
        self.aggregation_interval = aggregation_interval
        self.critical_events = {"failure", "state_change", "maintenance"}
```

#### 1.3 Optimize emit_observable Method
**File**: `twin_model/primitives/base.py`

**Requirements**:
- Add sampling logic based on configuration
- Implement critical event bypass
- Add event counting without storage
- Use Context7 to research Python performance optimization patterns

### Phase 2: Event Processing Optimization

#### 2.1 Batch Event Processing
**File**: `twin_model/primitives/base.py`

**Implementation**:
```python
class EventBatcher:
    """Batch similar events for efficient processing.
    
    Groups events by type and time window to reduce
    individual callbacks and improve performance.
    
    Attributes:
        batch_window: Time window for batching (seconds)
        batch_size: Maximum events per batch
        pending_batches: Dict of pending event batches
    """
    
    def add_event(self, 
                  event: Dict[str, Any],
                  timestamp: float) -> Optional[List[Dict[str, Any]]]:
        """Add event to batch, return batch if ready.
        
        Args:
            event: Event data to batch
            timestamp: Current simulation time
            
        Returns:
            Completed batch if ready, None otherwise
        """
        # Implementation with type hints and comments
        pass
```

#### 2.2 Implement Aggregated Observables
**File**: `twin_model/primitives/aggregator.py` (new file)

**Requirements**:
- Create aggregator class for time-windowed summaries
- Include mean, min, max, count for numeric values
- Implement efficient incremental updates
- Research incremental statistics algorithms via Context7

### Phase 3: Storage and I/O Optimization

#### 3.1 Implement Write-Through Cache
**File**: `twin_model/storage/cache.py` (new file)

**Implementation**:
```python
from pathlib import Path
import numpy as np
from typing import Optional, Union, BinaryIO

class ObservableCache:
    """Write-through cache for simulation observables.
    
    Uses memory-mapped files for efficient storage without
    keeping all data in RAM. Supports numpy arrays for
    performance.
    
    Attributes:
        cache_dir: Directory for cache files
        mmap_file: Memory-mapped file handle
        write_index: Current write position
    """
    
    def __init__(self, 
                 cache_dir: Union[str, Path],
                 max_size: int = 10_000_000) -> None:
        """Initialize cache with memory mapping.
        
        Args:
            cache_dir: Directory for cache storage
            max_size: Maximum cache entries
        """
        # Use Context7 to research numpy memmap best practices
        pass
```

#### 3.2 Add Database Flushing
**File**: `database/repositories.py`

**Requirements**:
- Implement batch insert for observables
- Add async flushing to avoid blocking simulation
- Include transaction management for data integrity
- Research SQLAlchemy bulk operations via Context7

### Phase 4: Simulation Control Enhancements

#### 4.1 Add Progress Reporting
**File**: `twin_model/simulation_runner.py` (new file)

**Implementation**:
```python
from typing import Protocol, Optional, Callable
import time

class ProgressCallback(Protocol):
    """Protocol for progress reporting callbacks.
    
    Allows flexible progress reporting without coupling
    to specific implementation.
    """
    
    def __call__(self, 
                 current_time: float,
                 total_time: float,
                 events_processed: int,
                 memory_usage_mb: float) -> None:
        """Report simulation progress.
        
        Args:
            current_time: Current simulation time
            total_time: Total simulation duration
            events_processed: Number of events processed
            memory_usage_mb: Current memory usage in MB
        """
        ...

class SimulationRunner:
    """Enhanced simulation runner with progress and control.
    
    Provides chunked execution, progress reporting, and
    pause/resume capabilities for long simulations.
    """
    
    def run_chunked(self,
                    total_days: int,
                    chunk_size_days: float = 1.0,
                    progress_callback: Optional[ProgressCallback] = None) -> None:
        """Run simulation in chunks with progress reporting.
        
        Args:
            total_days: Total simulation duration
            chunk_size_days: Size of each chunk
            progress_callback: Optional progress reporter
        """
        # Implementation with memory monitoring
        pass
```

#### 4.2 Implement State Persistence
**File**: `twin_model/state_manager.py` (new file)

**Requirements**:
- Save simulation state between chunks
- Support pause/resume functionality
- Include state validation and recovery
- Use Context7 to research Python pickle alternatives

### Phase 5: Configuration and Testing

#### 5.1 Create Configuration System
**File**: `twin_model/config.py` (new file)

**Implementation**:
```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
from pathlib import Path

@dataclass
class PerformanceConfig:
    """Performance configuration for simulations.
    
    Controls memory usage, sampling, and optimization
    settings for different simulation scenarios.
    
    Attributes:
        observable_buffer_size: Max events per primitive
        sampling_rate: Event sampling frequency
        aggregation_interval: Time between aggregations
        flush_interval: Database flush frequency
        enable_global_observables: Use global event collection
        simulation_mode: Data collection mode
        max_memory_mb: Memory usage limit
        enable_progress: Show progress updates
    """
    
    observable_buffer_size: int = 1000
    sampling_rate: int = 10
    aggregation_interval: float = 300.0
    flush_interval: float = 600.0
    enable_global_observables: bool = False
    simulation_mode: SimulationMode = SimulationMode.PRODUCTION
    max_memory_mb: float = 1000.0
    enable_progress: bool = True
    
    @classmethod
    def from_json(cls, path: Union[str, Path]) -> 'PerformanceConfig':
        """Load configuration from JSON file.
        
        Args:
            path: Path to configuration file
            
        Returns:
            PerformanceConfig instance
        """
        # Implementation with validation
        pass
    
    def validate(self) -> List[str]:
        """Validate configuration settings.
        
        Returns:
            List of validation errors, empty if valid
        """
        # Check for conflicts and invalid values
        pass
```

#### 5.2 Performance Testing Suite
**File**: `tests/test_performance.py` (new file)

**Requirements**:
- Create benchmarks for different simulation sizes
- Measure memory usage over time
- Compare modes (DETAILED vs PRODUCTION vs FAST)
- Generate performance regression reports
- Use Context7 to research Python memory profiling tools

### Phase 6: Integration and Optimization

#### 6.1 Update Database Integration
**File**: `database/integration.py`

**Modifications**:
- Accept PerformanceConfig parameter
- Implement batched observable storage
- Add memory monitoring and limits
- Include automatic mode switching on memory pressure

#### 6.2 Profile-Guided Optimization
**File**: `tools/profile_simulation.py` (new file)

**Requirements**:
- Create profiling harness for simulations
- Identify hot paths and bottlenecks
- Generate flame graphs and reports
- Research cProfile and memory_profiler via Context7

## Implementation Guidelines

### Code Quality Requirements

1. **Type Hints**: Every function must have complete type annotations
   ```python
   def process_events(
       events: List[Dict[str, Any]],
       config: PerformanceConfig,
       callback: Optional[Callable[[int], None]] = None
   ) -> Tuple[List[Dict[str, Any]], int]:
   ```

2. **Docstrings**: Use Google style for all classes and functions
   ```python
   """Short description.
   
   Longer description if needed, explaining purpose
   and important details.
   
   Args:
       param1: Description with type info
       param2: Another parameter
       
   Returns:
       Description of return value
       
   Raises:
       ValueError: When validation fails
   """
   ```

3. **Comments**: Add inline comments for complex logic
   ```python
   # Use circular buffer to prevent unbounded growth
   # while maintaining recent event history
   self.buffer = deque(maxlen=buffer_size)
   ```

4. **Context7 Usage**: Before implementing each component:
   - Search Context7 for best practices
   - Look up performance patterns
   - Research alternative approaches
   - Document Context7 references in comments

### Testing Strategy

1. **Unit Tests**: Test each optimization in isolation
2. **Integration Tests**: Verify components work together
3. **Performance Tests**: Measure improvements quantitatively
4. **Regression Tests**: Ensure functionality isn't broken

### Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| 30-day simulation time | Timeout | <5 minutes | Wall clock time |
| Memory usage (30 days) | >4GB | <500MB | Peak RSS |
| Events/second processed | ~1,000 | >10,000 | Profiler |
| Data quality (sampling) | 100% | 10% with full critical | Event counts |

## Migration Path

### Step 1: Backward Compatibility
- Add feature flags for new optimizations
- Default to current behavior
- Allow gradual migration

### Step 2: Validation
- Compare outputs between modes
- Ensure KPIs remain accurate
- Validate statistical properties

### Step 3: Deployment
- Start with FAST mode for testing
- Move to PRODUCTION for normal use
- Reserve DETAILED for debugging

## Alternative Approaches (If Needed)

If performance targets aren't met:

1. **Cython Compilation**
   - Compile hot paths to C
   - Focus on event queue operations
   - Research via Context7: "Cython SimPy optimization"

2. **Multiprocessing**
   - Split simulation into parallel chunks
   - Use shared memory for state
   - Consider Ray or Dask frameworks

3. **Alternative Frameworks**
   - JaamSim (Java-based, very fast)
   - DESMO (Python with C++ core)
   - Custom C++ engine with Python bindings

## Notes for Implementation

- Start with Phase 1 - it provides immediate relief
- Each phase can be tested independently
- Use Context7 extensively for implementation details
- Maintain backward compatibility throughout
- Document performance improvements at each step
- Create benchmarks before and after each optimization

## Context7 Research Topics

Before implementing each phase, research these topics in Context7:

1. "Python collections deque performance"
2. "NumPy memory mapping large arrays"
3. "SQLAlchemy bulk insert optimization"
4. "Python memory profiling tools"
5. "Incremental statistics algorithms"
6. "Python pickle alternatives for large objects"
7. "Cython SimPy performance optimization"
8. "Python async IO for simulations"

This plan provides a clear path from the current timeout issues to a performant system capable of 30-day simulations in under 5 minutes.