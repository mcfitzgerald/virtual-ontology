# Twin Model Debugging Guide

## Overview
This guide provides troubleshooting strategies and solutions for common issues in the twin_model simulation framework.

## Logging Architecture

### Configuration
The framework uses Python's native logging module with hierarchical loggers:

```python
from twin_model.logging_config import SimulationLogger

# Setup logging
SimulationLogger.setup_logging(
    log_level="DEBUG",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    enable_file=True,    # Write to logs/twin_model.log
    json_format=False    # Human-readable format
)

# Get logger for module
logger = SimulationLogger.get_logger(__name__)
```

### Log Levels
- **DEBUG**: Detailed event emission, state transitions
- **INFO**: Normal operation, key state changes
- **WARNING**: Performance issues, data anomalies
- **ERROR**: Failures requiring attention
- **CRITICAL**: System-level failures

### Log Files
- `logs/twin_model.log`: Main application log
- `logs/twin_model_errors.log`: Error-only log
- `logs/twin_api.log`: API server log

## Common Issues and Solutions

### 1. Division by Zero in OEE Calculations

**Problem**: Runtime is 0 but units are produced, causing division by zero.

**Solution**: Runtime inference implemented in `MESTransducer`:
```python
# Infer runtime from production if needed
if (metrics["good_units"] > 0 or metrics["scrap_units"] > 0) and metrics["runtime_minutes"] == 0:
    logger.warning(f"Inferring runtime from production for {equipment_id}")
    metrics["runtime_minutes"] = self.time_bucket
```

### 2. Memory Exhaustion in Long Simulations

**Problem**: Observables buffer grows unbounded, causing OOM errors.

**Solution**: Circular buffer with configurable size:
```python
sampling = SamplingConfig(
    mode=SimulationMode.PRODUCTION,  # Sample events
    sampling_rate=10,                 # Keep every 10th event
    buffer_size=1000                  # Max events in memory
)
```

### 3. Missing Critical Events

**Problem**: Important events (failures, state changes) getting filtered by sampling.

**Solution**: Critical event flagging bypasses sampling:
```python
# Mark event as critical
self.emit_observable(
    event_type="equipment_failure",
    details={"reason": "breakdown"},
    is_critical=True  # Bypasses sampling
)
```

Default critical events:
- `state_change`
- `equipment_failure`
- `maintenance`
- `planned_maintenance`
- `changeover`
- `cascade_failure_triggered`

### 4. Event Analysis

**Problem**: Need to understand event patterns and anomalies.

**Solution**: Use EventInspector for analysis:
```python
from twin_model.logging_config import EventInspector

inspector = EventInspector()

# Analyze event distribution
stats = inspector.analyze_event_distribution(events)
print(f"Event types: {stats['event_types']}")
print(f"State transitions: {stats['state_transitions']}")

# Find anomalies
anomalies = inspector.find_anomalies(events)
for anomaly in anomalies:
    print(f"Issue: {anomaly['issues']} in event: {anomaly['event']}")
```

## Performance Monitoring

### Using Performance Decorator
```python
from twin_model.logging_config import log_performance

@log_performance
def expensive_operation():
    # Function execution time logged automatically
    pass
```

### Memory Usage Tracking
```python
# In simulation loop
if logger.isEnabledFor(logging.DEBUG):
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.debug(f"Memory usage: {memory_mb:.1f} MB")
```

## Debugging Strategies

### 1. Enable Detailed Logging
```python
# For debugging specific issues
SimulationLogger.setup_logging(log_level="DEBUG")
```

### 2. Track Event Flow
```python
# Log event emission
logger.debug(
    f"Event emitted: {event_type}",
    extra={'extra_data': {
        'primitive_id': self.config.id,
        'timestamp': self.env.now,
        'details': details
    }}
)
```

### 3. Monitor Buffer Statistics
```python
# Check buffer health
stats = equipment.observable_buffer.get_stats()
logger.info(f"Buffer stats: {stats}")
```

### 4. Use Correlation IDs
```python
# Track related events across the system
SimulationLogger.set_correlation_id("simulation-123")
# All subsequent logs include correlation_id
```

## Testing Strategies

### Unit Tests
Run specific test suites:
```bash
# Test OEE calculations
python -m unittest twin_model.tests.test_oee_calculations -v

# Test critical events
python -m unittest twin_model.tests.test_critical_events -v
```

### Integration Tests
```bash
# Full system test
python -m twin_model.test_final_verification
```

### Performance Tests
```python
# Measure simulation performance
import time
start = time.time()
runner.run_simulation(params, duration_days=30)
elapsed = time.time() - start
print(f"Simulation time: {elapsed:.2f} seconds")
```

## Known Issues and Workarounds

### Issue: State changes not appearing in observables
**Cause**: Circular buffer overflow pushing out early events.
**Workaround**: Increase buffer_size or use DETAILED mode for debugging.

### Issue: High memory usage in DETAILED mode
**Cause**: All events kept in memory.
**Workaround**: Use PRODUCTION mode with appropriate sampling_rate.

### Issue: Performance degradation with global observables
**Cause**: Duplicate event emission to global bus.
**Workaround**: Set `enable_global_observables=False` unless needed.

## Best Practices

1. **Always log state changes** at INFO level
2. **Use structured logging** with extra_data for context
3. **Monitor memory usage** in long-running simulations
4. **Test with different SimulationModes** to verify behavior
5. **Use EventInspector** to validate event streams
6. **Keep buffer sizes reasonable** (1000-10000 events)
7. **Mark critical events explicitly** to ensure capture

## Getting Help

1. Check logs in `logs/` directory
2. Enable DEBUG logging for detailed traces
3. Use EventInspector to analyze patterns
4. Review test cases for examples
5. Check this guide for common issues

## References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [SimPy Documentation](https://simpy.readthedocs.io/)
- Twin Model API Documentation: `http://localhost:8000/docs`