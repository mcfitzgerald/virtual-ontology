# SimPy-Based Manufacturing Generator Redesign

## Executive Summary

The current manufacturing data generator treats equipment as independent random event generators rather than a connected production line with material flow. This results in minimal parameter sensitivity and unrealistic system behavior. We are proceeding with rebuilding the generator (called `twin_model`) using SimPy discrete event simulation to model actual material flow, buffers, and equipment interactions.

**Status: APPROVED - Moving to Implementation**

## Problem Analysis

### Current Generator Issues

1. **No Material Flow**
   - Equipment operates independently without material tracking
   - Downstream equipment continues "producing" even when upstream is stopped
   - No actual product entities moving through the line

2. **No Buffer Management**
   - No Work-In-Process (WIP) inventory between stations
   - Cannot model starvation (upstream buffer empty) or blockage (downstream buffer full)
   - Equipment coupling is probabilistic rather than physical

3. **Weak Parameter Effects**
   - 4 out of 5 actionable parameters show <2% impact on OEE
   - Parameters adjust probabilities rather than system dynamics
   - Some parameters show opposite correlations from expected (material_reliability, cascade_sensitivity)

4. **Missing Dynamics**
   - No bottleneck emergence
   - No natural cascade effects
   - No queue buildup or depletion

### Test Results Summary

| Parameter | Expected Correlation | Actual Correlation | Effect Size |
|-----------|---------------------|-------------------|-------------|
| micro_stop_probability | Negative | ✓ -0.995 | 0.8% (weak) |
| performance_factor | Positive | ✓ +1.000 | 22.0% (strong) |
| scrap_multiplier | Negative | ✓ -0.972 | 0.9% (weak) |
| material_reliability | Positive | ✗ -0.999 | 1.1% (weak) |
| cascade_sensitivity | Negative | ✗ +0.981 | 1.7% (weak) |

## Proposed Solution: SimPy Discrete Event Simulation

### Why SimPy?

- **Industry Standard**: Widely used for manufacturing simulation
- **Material Flow**: Natural representation of products moving through equipment
- **Buffer Modeling**: Built-in Container/Store resources for WIP management
- **Event-Driven**: Realistic failure and maintenance modeling
- **Python Native**: Integrates with existing codebase

### Core Architecture

**Simplified to 3 equipment types per line (Filler, Packer, Palletizer):**

```
┌─────────┐     ┌────────┐     ┌─────────┐     ┌────────┐     ┌─────────┐     ┌────────┐     ┌───────────┐     ┌──────┐
│ Source  │────▶│Buffer 1│────▶│ Filler  │────▶│Buffer 2│────▶│ Packer  │────▶│Buffer 3│────▶│Palletizer │────▶│ Sink │
└─────────┘     └────────┘     └─────────┘     └────────┘     └─────────┘     └────────┘     └───────────┘     └──────┘
                                     │                              │                               │
                                     ▼                              ▼                               ▼
                              [Failure Process]            [Failure Process]               [Failure Process]
```

**Three Production Lines:**
- LINE1: Base configuration
- LINE2: Different parameters (speeds, failure rates)
- LINE3: Different parameters (speeds, failure rates)

All three lines share the same architecture but with different configuration parameters.

### Key Components

#### 1. Production Line Class
```python
class ProductionLine:
    env: simpy.Environment          # Simulation environment
    line_id: str                    # LINE1, LINE2, LINE3
    equipment: Dict[str, Equipment]  # All machines
    buffers: Dict[str, Buffer]      # Inter-equipment buffers
    source: MaterialSource           # Raw material arrival
    sink: ProductSink               # Finished goods
    mes_logger: MESLogger           # 5-minute state capture
```

#### 2. Equipment Model
```python
class Equipment:
    # State management
    state: EquipmentState  # Running/Stopped/Starved/Blocked
    
    # Physical connections
    upstream_buffer: simpy.Container
    downstream_buffer: simpy.Container
    
    # Performance characteristics
    base_rate: float        # Units per minute
    current_rate: float     # Actual rate (with variations)
    scrap_rate: float       # Quality loss
    
    # Reliability
    mtbf: float            # Mean time between failures
    mttr: float            # Mean time to repair
    
    # Processes (run concurrently)
    production_process()    # Main production loop
    failure_process()       # Random failures
    maintenance_process()   # Scheduled maintenance
```

#### 3. Buffer Model
```python
class Buffer:
    container: simpy.Container  # SimPy resource
    capacity: int              # Maximum units
    track_levels: List[int]    # Level history for analysis
```

#### 4. Material Flow
- Products are discrete entities (individual units)
- Each product moves through buffers sequentially
- Equipment must successfully GET from upstream and PUT to downstream
- Natural starvation when upstream empty
- Natural blockage when downstream full

### Parameter Mapping

| Parameter | Current Effect | SimPy Effect |
|-----------|---------------|--------------|
| **micro_stop_probability** | Scales random stop probability | Scales MTBF: `actual_mtbf = base_mtbf / parameter` |
| **performance_factor** | Scales production count | Scales processing rate: `actual_rate = base_rate * parameter` |
| **scrap_multiplier** | Scales scrap probability | Scales quality: `scrap_prob = base_scrap * parameter` |
| **material_reliability** | Scales material shortage events | Controls: 1) Source arrival rate, 2) Random material shortages |
| **cascade_sensitivity** | Probability of cascade | Controls buffer sizes: `buffer_size = base_size / parameter` |

### Expected Improvements

1. **Strong Parameter Sensitivity**
   - Buffer-based coupling creates real cascades
   - Material flow creates natural dependencies
   - Parameters directly affect physical dynamics

2. **Realistic Behaviors**
   - Bottlenecks emerge naturally
   - Starvation/blockage from actual buffer states
   - Production naturally limited by slowest equipment

3. **Better Optimization Target**
   - Parameters will have meaningful impact
   - Trade-offs become apparent (e.g., speed vs quality)
   - System dynamics create non-linear effects

## Implementation Plan

### Phase 1: Core SimPy Generator (30 minutes)
- [ ] Basic Equipment class with production process
- [ ] Buffer implementation with Container
- [ ] Simple line with Filler → Buffer → Packer → Buffer → Palletizer
- [ ] Material flow tracking (individual units)
- [ ] Basic OEE calculation from equipment states

### Phase 2: Stochastic Elements & Parameters (30 minutes)
- [ ] MTBF/MTTR-based failure processes using exponential distribution
- [ ] Performance variations (shift patterns, random fluctuations)
- [ ] Quality/scrap modeling
- [ ] Material shortage events
- [ ] Parameter mapping (5 actionable parameters)
- [ ] MES data logging every 5 minutes

### Phase 3: Multi-Line & Validation (ongoing)
- [ ] Clone to 3 lines with different configurations
- [ ] Validate OEE calculations match expected formulas
- [ ] Test parameter sensitivity (>5% impact target)
- [ ] Performance benchmarking (<60 seconds for 7-day simulation)
- [ ] MES output compatibility verification

## Design Decisions (RESOLVED)

1. **Entity Granularity**
   - **Decision**: Track individual units for accuracy
   - Mitigate memory usage by buffering monitoring data
   - Only log aggregated data every 5 minutes

2. **Buffer Sizing Formula**
   ```python
   # Finalized mapping from cascade_sensitivity
   base_buffer_size = hourly_rate * 0.5  # 30 minutes of production
   actual_buffer_size = base_buffer_size / cascade_sensitivity
   # cascade_sensitivity = 2.0 → small buffers → tight coupling
   # cascade_sensitivity = 0.5 → large buffers → loose coupling
   ```

3. **OEE Calculation**
   - Calculate from equipment states captured every 5 minutes:
   ```python
   # OEE = Availability × Performance × Quality
   availability = running_time / planned_time
   performance = actual_production / (running_time * ideal_rate)
   quality = good_units / total_units
   oee = availability * performance * quality
   ```

4. **Stochastic Failure Modeling**
   - Use exponential distribution for time between failures: `random.expovariate(1/mtbf)`
   - Use exponential distribution for repair time: `random.expovariate(1/mttr)`
   - Failures interrupt production process
   - Track downtime reasons for root cause analysis

5. **Anomaly Injection Pattern**
   - Base stochastic behavior defined in configuration
   - Special anomalies can be scheduled (e.g., major failure at specific time)
   - Performance degradation events
   - Material shortage patterns

## Immediate Next Steps

### Today: Implementation
1. **Phase 1 (NOW)**
   - Build core SimPy production line
   - Implement material flow with buffers
   - Basic equipment states and OEE tracking

2. **Phase 2 (NEXT)**
   - Add stochastic failures (MTBF/MTTR)
   - Implement parameter mappings
   - Add MES logging

3. **Validation**
   - Verify OEE calculations
   - Test parameter sensitivity
   - Compare with current generator output

## Decisions Made

1. **SimPy Approach**: ✅ **APPROVED**
   - Moving forward with implementation
   - Performance target: 2-3x current generator is acceptable

2. **Validation Approach**: **Statistical comparison**
   - Compare OEE distributions with current generator
   - Verify parameter correlations are correct
   - Ensure >5% parameter impact

3. **Migration Strategy**: **Build alongside, then replace**
   - New module called `twin_model`
   - Ensure MES output compatibility
   - Adapt ontology as needed for richer data

4. **Buffer Philosophy**: **Finite buffers with cascade_sensitivity control**
   - Buffers sized based on production rate and cascade parameter
   - Models realistic coupling between equipment

5. **Development Approach**: **In main codebase**
   - New module in `/twin/` directory
   - Reuse configuration structures where possible

## System Integration & Migration Considerations

### Component Adaptation Requirements

#### 1. SimulationRunner
**Current State**: Tightly coupled to current generator's synchronous time-stepping
**Required Changes**:
```python
class SimPySimulationRunner:
    """Adapter for SimPy-based simulations"""
    def run_simulation(self, parameters: ActionableParameters, duration_days: int):
        # Create SimPy environment
        env = simpy.Environment()
        
        # Build production lines with parameters
        lines = [ProductionLine(env, f"LINE{i}", parameters) for i in range(1,4)]
        
        # Run simulation
        env.run(until=duration_days * 24 * 60)  # Convert to minutes
        
        # Extract MES data from loggers
        return self._format_results(lines)
```

#### 2. OptimizationEngine
**Current State**: Treats simulation as black box
**Required Changes**: 
- None if SimulationRunner interface preserved
- Adjust timeout expectations (2-3x slower)
- Will benefit from stronger parameter effects (better convergence)

#### 3. RecommendationEngine
**Current State**: Uses NSGA-II for multi-objective optimization
**New Capabilities**:
- Buffer-based recommendations
- Bottleneck-aware suggestions
- Material flow optimization

#### 4. VirtualSensors
**Required Changes**:
- Retrain on new data patterns
- Add buffer level sensors
- Add bottleneck detection sensors
- Add material flow rate sensors

#### 5. CostImpactCalculator
**Required Changes**: 
- None if production counts remain in same format
- Could add WIP inventory holding costs

### Database Architecture Evolution

#### New Tables Needed
```sql
-- Buffer state tracking
CREATE TABLE buffer_states (
    timestamp TIMESTAMP,
    run_id TEXT,
    buffer_id TEXT,
    level INTEGER,
    capacity INTEGER,
    utilization REAL
);

-- Material flow tracking
CREATE TABLE material_flow (
    timestamp TIMESTAMP,
    run_id TEXT,
    source_equipment TEXT,
    destination_equipment TEXT,
    flow_rate REAL,
    cumulative_units INTEGER
);

-- Enhanced equipment states
ALTER TABLE simulation_data ADD COLUMN state_detail TEXT;
-- Values: 'RUNNING', 'STOPPED_FAILURE', 'STARVED', 'BLOCKED'
```

### Ontology Updates
```yaml
# New entities in twin_ontology_spec.yaml
MaterialFlow:
  properties:
    - flow_rate: "units per minute"
    - buffer_level: "current WIP"
    - bottleneck_indicator: "boolean"

EquipmentState:
  extended_states:
    - STARVED: "Waiting for material"
    - BLOCKED: "Cannot send downstream"
```

### Migration Strategy

Since the current generator is fundamentally broken (no material flow, <2% parameter effects):

1. **Direct Replacement**
   - Build SimPy model completely
   - No backward compatibility needed with broken model
   - Focus on correct physics

2. **Integration Updates**
   - Modify SimulationRunner for SimPy
   - Adjust optimization timeouts
   - Retrain virtual sensors

3. **Success Criteria**
   - All parameters show >5% OEE impact
   - Correct correlation directions
   - Natural bottlenecks and cascades

### End User Experience

#### What Stays the Same
- Claude Code interface
- 5 actionable parameters
- OEE metrics
- Optimization goals

#### What Improves (Transparently)
- Parameter sensitivity (>5% vs <2%)
- Realistic cascades
- Bottleneck insights
- Better optimization convergence

## References

- [SimPy Documentation](https://simpy.readthedocs.io/)
- [Manufacturing Line Optimization using DES](https://medium.com/zebrax/manufacturing-line-optimization-using-discrete-event-simulation-5090ecade303)
- [OEE Calculation Best Practices](https://www.oee.com/calculating-oee/)