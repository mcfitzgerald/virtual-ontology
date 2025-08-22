# Twin Model Logging Strategy and OEE Fix Implementation Plan

## Overview
This document outlines a comprehensive logging strategy for the twin_model framework and the required fixes for OEE calculation issues. The implementation will follow best practices using Context7 documentation and maintain high code quality standards.

## Part 1: Logging Strategy

### 1.1 Logging Architecture

#### Core Principles
- **Structured Logging**: Use consistent log formats with contextual information
- **Hierarchical Loggers**: Module-specific loggers inheriting from root configuration
- **Performance-Aware**: Minimal overhead in production mode
- **Debug-Friendly**: Rich information in debug mode
- **Traceable**: Include correlation IDs for tracking events through the system

#### Logger Hierarchy
```
twin_model (root)
├── twin_model.primitives
│   ├── twin_model.primitives.equipment
│   ├── twin_model.primitives.buffer
│   └── twin_model.primitives.source
├── twin_model.transduction
│   └── twin_model.transduction.mes_transducer
├── twin_model.model_builder
└── twin_model.state_manager
```

### 1.2 Implementation Requirements

#### Configuration File (`twin_model/logging_config.py`)
```python
"""
Centralized logging configuration for the twin_model framework.

Use Context7 to find best practices for:
- Python logging configuration
- Structured logging with context
- Performance-efficient logging
- Log rotation and management
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

class LogLevel(Enum):
    """Logging levels for different scenarios."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class SimulationLogger:
    """
    Centralized logger configuration for simulation framework.
    
    Features:
    - Hierarchical logger structure
    - File and console handlers
    - Structured logging with context
    - Performance monitoring
    - Event correlation
    
    Use Context7: Python logging best practices, structured logging
    """
    
    @classmethod
    def setup_logging(
        cls,
        log_dir: Path = Path("logs"),
        log_level: LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
        max_bytes: int = 10_485_760,  # 10MB
        backup_count: int = 5,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Configure logging for the entire twin_model framework.
        
        Args:
            log_dir: Directory for log files
            log_level: Minimum log level to capture
            enable_console: Enable console output
            enable_file: Enable file output
            max_bytes: Maximum size per log file
            backup_count: Number of backup files to keep
            correlation_id: Optional correlation ID for tracking
            
        Context7 Topics:
        - Python logging.config
        - Rotating file handlers
        - Custom formatters
        """
        pass
```

#### Logger Usage Pattern
```python
"""
Standard logger usage pattern for all modules.

Each module should:
1. Import the module logger
2. Use structured logging with context
3. Include performance metrics where relevant
4. Follow consistent message formats
"""

import logging
from typing import Dict, Any
import time

# Module-level logger
logger = logging.getLogger(__name__)

class ExamplePrimitive:
    """Example showing logging best practices."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with logging.
        
        Context7: Python class initialization logging patterns
        """
        self.id = config.get('id', 'unknown')
        logger.info(
            "Initializing primitive",
            extra={
                'primitive_id': self.id,
                'primitive_type': self.__class__.__name__,
                'config': config
            }
        )
    
    def process_event(self, event: Dict[str, Any]) -> None:
        """
        Process event with performance logging.
        
        Context7: Performance logging patterns, metrics collection
        """
        start_time = time.perf_counter()
        logger.debug(
            "Processing event",
            extra={
                'primitive_id': self.id,
                'event_type': event.get('event_type'),
                'timestamp': event.get('timestamp')
            }
        )
        
        try:
            # Process event
            self._do_processing(event)
            
            elapsed = time.perf_counter() - start_time
            logger.debug(
                "Event processed successfully",
                extra={
                    'primitive_id': self.id,
                    'event_type': event.get('event_type'),
                    'processing_time_ms': elapsed * 1000
                }
            )
            
        except Exception as e:
            logger.error(
                "Event processing failed",
                extra={
                    'primitive_id': self.id,
                    'event_type': event.get('event_type'),
                    'error': str(e)
                },
                exc_info=True
            )
            raise
```

### 1.3 Specific Logging Points

#### Equipment Primitive Logging
```python
"""
Critical logging points for equipment primitives.

Track:
- State transitions with duration
- Production events
- Failure events
- Performance metrics
"""

# In equipment.py
logger.info(
    "State transition",
    extra={
        'equipment_id': self.id,
        'old_state': old_state,
        'new_state': new_state,
        'duration_in_state': duration,
        'timestamp': self.env.now
    }
)

logger.debug(
    "Unit produced",
    extra={
        'equipment_id': self.id,
        'product_id': product_id,
        'quality': quality,
        'cycle_time': cycle_time
    }
)
```

#### MES Transducer Logging
```python
"""
Critical logging points for MES transduction.

Track:
- Event processing counts
- State tracking issues
- Runtime calculations
- KPI calculations
"""

# In mes_transducer.py
logger.warning(
    "Units produced but no runtime recorded",
    extra={
        'equipment_id': equipment_id,
        'good_units': metrics['good_units'],
        'runtime_minutes': metrics['runtime_minutes'],
        'bucket': bucket,
        'action': 'inferring_runtime'
    }
)

logger.debug(
    "Performance calculation",
    extra={
        'equipment_id': equipment_id,
        'actual_units': actual_units,
        'target_rate': target_rate,
        'runtime_minutes': runtime_minutes,
        'calculated_performance': performance
    }
)
```

### 1.4 Debug Mode Features

#### Event Inspector
```python
"""
Event inspection utilities for debugging.

Context7: Python debugging utilities, data inspection patterns
"""

from typing import List, Dict, Any, Tuple
import pandas as pd
from collections import Counter

class EventInspector:
    """Analyze and debug event streams."""
    
    @staticmethod
    def analyze_event_distribution(
        events: List[Dict[str, Any]], 
        sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze distribution of event types.
        
        Returns detailed statistics about events.
        """
        logger.info(f"Analyzing {len(events)} events")
        
        # Event type distribution
        event_types = Counter(e.get('event_type') for e in events)
        
        # State change analysis
        state_changes = [e for e in events if e.get('event_type') == 'state_change']
        
        # Production analysis
        production_events = [
            e for e in events 
            if e.get('event_type') in ['unit_produced', 'unit_scrapped']
        ]
        
        analysis = {
            'total_events': len(events),
            'event_types': dict(event_types),
            'state_changes': len(state_changes),
            'production_events': len(production_events),
            'unique_primitives': len(set(e.get('primitive_id') for e in events))
        }
        
        logger.info(
            "Event analysis complete",
            extra={'analysis': analysis}
        )
        
        return analysis
```

## Part 2: OEE Calculation Fixes

### 2.1 Root Cause Analysis

The OEE calculation fails because:
1. **Missing Runtime Tracking**: Equipment produces units but `runtime_minutes` = 0
2. **State Not Updated**: Equipment shows "Idle" even when producing
3. **Performance Calculation**: Divides by zero when runtime = 0
4. **Event Sampling**: Critical state_change events may be filtered out

### 2.2 Fix Implementation

#### Fix 1: MES Transducer Runtime Inference
```python
"""
Fix runtime tracking in MES transducer.

When units are produced but no runtime is recorded,
infer that equipment was running.

Context7: Data validation, inference patterns
"""

def _process_bucket_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process and validate bucket metrics before KPI calculation.
    
    Fixes:
    - Infer runtime when units produced
    - Correct state when production detected
    - Validate data consistency
    """
    # Fix: If units produced but no runtime, infer runtime
    if (metrics['good_units'] > 0 or metrics['scrap_units'] > 0) and metrics['runtime_minutes'] == 0:
        logger.warning(
            "Inferring runtime from production",
            extra={
                'good_units': metrics['good_units'],
                'scrap_units': metrics['scrap_units'],
                'original_runtime': 0,
                'inferred_runtime': self.time_bucket
            }
        )
        metrics['runtime_minutes'] = self.time_bucket
        metrics['last_status'] = 'Running'
    
    # Fix: Ensure status matches activity
    if metrics['good_units'] > 0 and metrics['last_status'] == 'Idle':
        logger.warning(
            "Correcting status from Idle to Running due to production",
            extra={'good_units': metrics['good_units']}
        )
        metrics['last_status'] = 'Running'
    
    return metrics
```

#### Fix 2: Performance Calculation Safety
```python
"""
Fix performance calculation to handle edge cases.

Context7: Safe division patterns, numerical stability
"""

def _calculate_performance(
    self,
    metrics: Dict[str, Any],
    equipment_info: Dict[str, Any],
    product_info: Dict[str, Any]
) -> float:
    """
    Calculate performance score with safety checks.
    
    Handles:
    - Zero runtime but units produced
    - Missing target rates
    - Data inconsistencies
    """
    try:
        # Get target rate with fallback
        target_rate = product_info.get('target_rate_units_per_5min', 350)
        
        # Calculate actual production
        actual_units = metrics['good_units'] + metrics['scrap_units']
        
        # Determine effective runtime
        if actual_units > 0 and metrics['runtime_minutes'] == 0:
            # Units produced but no runtime recorded - use full bucket
            logger.debug("Using full bucket time for performance calculation")
            effective_runtime = self.time_bucket
        else:
            effective_runtime = metrics['runtime_minutes']
        
        # Calculate performance
        if target_rate > 0 and effective_runtime > 0:
            adjusted_target = (target_rate * effective_runtime) / self.time_bucket
            performance = (actual_units / adjusted_target) * 100
            
            logger.debug(
                "Performance calculated",
                extra={
                    'actual_units': actual_units,
                    'adjusted_target': adjusted_target,
                    'performance': performance,
                    'runtime': effective_runtime
                }
            )
            
            return min(110, max(0, performance))
        
        return 0.0
        
    except Exception as e:
        logger.error(
            "Performance calculation failed",
            extra={'error': str(e), 'metrics': metrics},
            exc_info=True
        )
        return 0.0
```

#### Fix 3: Event Emission Verification
```python
"""
Ensure critical events are emitted and not filtered.

Context7: Event-driven architecture, event sourcing patterns
"""

class EquipmentPrimitive(BasePrimitive):
    """Enhanced equipment primitive with verified event emission."""
    
    def _change_state(self, new_state: str) -> None:
        """
        Change equipment state with guaranteed event emission.
        
        Ensures state_change events are:
        1. Always emitted
        2. Include duration
        3. Not filtered by sampling for critical states
        """
        old_state = self.state
        duration = self.env.now - self.last_state_change
        
        # Mark critical events to bypass sampling
        is_critical = new_state in ['RUNNING', 'STOPPED_FAILURE']
        
        # Emit state change event
        self.emit_observable({
            'event_type': 'state_change',
            'old_state': old_state,
            'new_state': new_state,
            'duration_in_state': duration,
            'timestamp': self.env.now,
            'critical': is_critical  # Flag for sampling bypass
        })
        
        logger.info(
            "State changed",
            extra={
                'equipment_id': self.config.id,
                'old_state': old_state,
                'new_state': new_state,
                'duration': duration
            }
        )
        
        self.state = new_state
        self.last_state_change = self.env.now
```

### 2.3 Testing Strategy

#### Unit Tests
```python
"""
Comprehensive unit tests for OEE calculations.

Context7: Python unittest, pytest best practices
"""

import pytest
from twin_model.transduction.mes_transducer import MESTransducer

class TestOEECalculations:
    """Test OEE calculation fixes."""
    
    def test_performance_with_zero_runtime(self):
        """Test performance calculation when runtime is zero but units produced."""
        transducer = MESTransducer()
        
        metrics = {
            'good_units': 100,
            'scrap_units': 5,
            'runtime_minutes': 0,
            'downtime_minutes': 0
        }
        
        equipment_info = {'base_rate': 60}
        product_info = {'target_rate_units_per_5min': 350}
        
        performance = transducer._calculate_performance(
            metrics, equipment_info, product_info
        )
        
        assert performance > 0, "Performance should be > 0 when units produced"
        assert performance <= 110, "Performance should be capped at 110%"
    
    def test_runtime_inference(self):
        """Test runtime is inferred when units are produced."""
        transducer = MESTransducer()
        
        metrics = {
            'good_units': 50,
            'runtime_minutes': 0,
            'last_status': 'Idle'
        }
        
        fixed_metrics = transducer._process_bucket_metrics(metrics)
        
        assert fixed_metrics['runtime_minutes'] > 0
        assert fixed_metrics['last_status'] == 'Running'
```

#### Integration Tests
```python
"""
Integration tests for end-to-end OEE calculation.

Context7: Integration testing patterns, test data generation
"""

def test_30_day_simulation_oee():
    """Test that 30-day simulation produces reasonable OEE values."""
    
    # Run 1-day test simulation
    run_id, csv_path, kpis = run_test_simulation(days=1)
    
    # Verify KPIs are reasonable
    assert 5 <= kpis['mean_oee'] <= 85, f"OEE {kpis['mean_oee']} out of range"
    assert 10 <= kpis['mean_performance'] <= 100
    assert 70 <= kpis['mean_availability'] <= 100
    assert 90 <= kpis['mean_quality'] <= 100
    
    # Verify data consistency
    df = pd.read_csv(csv_path)
    assert (df['OEE_Score'] > 0).any(), "Should have non-zero OEE values"
    assert (df['Performance_Score'] > 0).any(), "Should have non-zero performance"
```

### 2.4 Documentation Standards

#### Docstring Format
```python
"""
Use Google-style docstrings with comprehensive information.

Context7: Google Python style guide, docstring best practices
"""

def process_simulation_data(
    self,
    data: pd.DataFrame,
    config: Dict[str, Any],
    validate: bool = True
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Process simulation data and calculate KPIs.
    
    This function takes raw simulation data and calculates
    key performance indicators including OEE, availability,
    performance, and quality scores.
    
    Args:
        data: DataFrame containing simulation events with columns:
            - timestamp: Event timestamp (datetime)
            - equipment_id: Equipment identifier (str)
            - event_type: Type of event (str)
            - value: Event value (float)
        config: Configuration dictionary containing:
            - time_bucket: Aggregation period in minutes (int)
            - target_rates: Target production rates (dict)
        validate: Whether to validate input data (bool)
    
    Returns:
        Tuple containing:
            - Processed DataFrame with MES format
            - Dictionary of KPIs with keys:
                - mean_oee: Average OEE percentage
                - mean_availability: Average availability
                - mean_performance: Average performance
                - mean_quality: Average quality
    
    Raises:
        ValueError: If data validation fails
        KeyError: If required columns are missing
    
    Example:
        >>> data = pd.read_csv('simulation_events.csv')
        >>> config = {'time_bucket': 5, 'target_rates': {...}}
        >>> mes_data, kpis = processor.process_simulation_data(data, config)
        >>> print(f"OEE: {kpis['mean_oee']:.1f}%")
    
    Note:
        This function implements fixes for zero-runtime issues
        where equipment produces units but runtime is not recorded.
        See issue #123 for details.
    
    Context7 References:
        - pandas DataFrame processing best practices
        - KPI calculation standards for manufacturing
    """
```

#### Inline Comments
```python
"""
Use clear, informative inline comments.

Context7: Code commenting best practices
"""

def calculate_oee(self, metrics: Dict[str, Any]) -> float:
    """Calculate Overall Equipment Effectiveness."""
    
    # OEE = Availability × Performance × Quality
    # Each component is a percentage (0-100)
    
    # Calculate availability: (Total Time - Downtime) / Total Time
    # This measures how often equipment is available to run
    availability = self._calculate_availability(metrics)
    
    # Calculate performance: Actual Production / Theoretical Production
    # This measures speed losses and minor stops
    performance = self._calculate_performance(metrics)
    
    # Calculate quality: Good Units / Total Units
    # This measures production quality and scrap rate
    quality = self._calculate_quality(metrics)
    
    # OEE is the product of all three metrics
    # Convert from percentage^3 to percentage
    oee = (availability * performance * quality) / 10000
    
    logger.debug(
        "OEE calculated",
        extra={
            'availability': availability,
            'performance': performance,
            'quality': quality,
            'oee': oee
        }
    )
    
    return oee
```

## Part 3: Implementation Order

### Phase 1: Logging Infrastructure (Priority 1)
1. Create `twin_model/logging_config.py`
2. Add logger initialization to all modules
3. Add structured logging to critical paths
4. Create event inspector utilities
5. Test logging with existing simulation

### Phase 2: OEE Fixes (Priority 1)
1. Fix MES transducer runtime inference
2. Fix performance calculation safety
3. Add comprehensive logging to calculations
4. Add unit tests for calculations
5. Run test simulation to verify fixes

### Phase 3: Event Emission Verification (Priority 2)
1. Audit equipment primitive event emission
2. Ensure state_change events include duration
3. Add critical event flagging
4. Verify sampling doesn't filter critical events
5. Add integration tests

### Phase 4: Documentation and Testing (Priority 2)
1. Update all docstrings to Google style
2. Add comprehensive inline comments
3. Create debugging guide
4. Add performance benchmarks
5. Document known issues and fixes

## Part 4: Context7 Usage Guidelines

### Required Context7 Lookups

1. **Logging Best Practices**
   - Python logging module configuration
   - Structured logging patterns
   - Log rotation and management
   - Performance-efficient logging

2. **Testing Patterns**
   - pytest best practices
   - Unit testing for calculations
   - Integration testing for simulations
   - Test data generation

3. **Documentation Standards**
   - Google Python style guide
   - Docstring formatting
   - API documentation
   - Code commenting best practices

4. **Performance Optimization**
   - Profiling Python code
   - Memory-efficient data structures
   - Event processing patterns
   - Numerical stability

5. **Error Handling**
   - Exception handling patterns
   - Error recovery strategies
   - Graceful degradation
   - Error logging best practices

## Part 5: Success Criteria

### Logging Success
- [ ] All modules have configured loggers
- [ ] Critical paths have structured logging
- [ ] Debug mode provides detailed event analysis
- [ ] Log files are rotated and manageable
- [ ] Performance impact < 5% in production mode

### OEE Fix Success
- [ ] OEE values between 10-85% (realistic range)
- [ ] Performance scores > 0 when units produced
- [ ] No division by zero errors
- [ ] State tracking matches production
- [ ] All KPIs calculable from simulation data

### Code Quality Success
- [ ] All functions have comprehensive docstrings
- [ ] Critical logic has inline comments
- [ ] Test coverage > 80% for calculations
- [ ] No linting errors (ruff, mypy)
- [ ] Documentation builds without warnings

## Part 6: Rollback Plan

If issues arise during implementation:

1. **Logging Issues**: Can disable file logging, use console only
2. **OEE Calculation Issues**: Revert to simple calculation, log warnings
3. **Performance Issues**: Reduce logging level, disable debug features
4. **Integration Issues**: Use feature flags to enable/disable fixes

## Appendix: Quick Reference

### Logger Names
```python
# Standard logger names for each module
LOGGER_NAMES = {
    'primitives.equipment': 'twin_model.primitives.equipment',
    'primitives.buffer': 'twin_model.primitives.buffer',
    'transduction': 'twin_model.transduction.mes_transducer',
    'model_builder': 'twin_model.model_builder',
    'state_manager': 'twin_model.state_manager'
}
```

### Log Levels by Scenario
```python
# Recommended log levels
LOG_LEVELS = {
    'development': logging.DEBUG,
    'testing': logging.INFO,
    'production': logging.WARNING,
    'debugging_issue': logging.DEBUG,
    'performance_testing': logging.ERROR
}
```

### Critical Metrics to Log
```python
# Always log these metrics
CRITICAL_METRICS = [
    'state_changes',
    'production_events',
    'failure_events',
    'runtime_calculations',
    'performance_calculations',
    'oee_calculations',
    'memory_usage',
    'processing_time'
]
```

---

## Next Steps

1. Review this plan and adjust as needed
2. Start new Claude Code session for implementation
3. Use Context7 for all specified lookups
4. Implement in phases with testing between each
5. Document progress and any deviations from plan

**Remember**: 
- Use Context7 for best practices
- Maintain comprehensive documentation
- Test each component thoroughly
- Keep performance impact minimal
- Ensure backward compatibility