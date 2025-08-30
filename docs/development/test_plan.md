# Comprehensive Testing Plan for Twin Simulation

## Overview

This document outlines a comprehensive testing strategy for the Virtual Twin Model simulation system, covering all aspects from unit testing of primitives to end-to-end validation of production scenarios.

## System Architecture Context

The twin simulation operates within a broader ontology-driven architecture:

```
1. ONTOLOGY LAYER (Semantic Definition)
   ├── MES Ontology (Historical Data Structure)
   ├── Twin Ontology (Simulation Concepts)
   └── Control Mappings (Parameter Relationships)
           ↓
2. SIMULATION LAYER (Digital Twin)
   ├── SimPy Discrete Event Simulation
   ├── Primitives (Equipment, Source, Sink, Scheduler)
   └── Observable Events (Rich Internal State)
           ↓
3. TRANSDUCTION LAYER (MES Format)
   ├── MES Transducer (Observable → MES Format)
   ├── 5-minute Buckets (Production Snapshots)
   └── KPI Calculation (OEE, Performance)
           ↓
4. DATABASE LAYER (Storage & Analysis)
   ├── Historical MES Data (mes_data table)
   ├── Simulation Results (twin_runs)
   └── SQL-based Analysis (Pattern Discovery)
```

## Phase 1: Unit Testing - Core Primitives

### Objective
Verify individual primitive behaviors in isolation

### 1.1 Equipment Primitive Tests
- **State Transitions**: Validate IDLE → RUNNING → STOPPED → MAINTENANCE cycles
- **Failure Generation**: Verify MTBF/MTTR distributions (exponential/lognormal)
- **Internal Queue Management**: Test queue capacity limits and overflow handling
- **Performance Degradation**: Validate wear-based performance reduction
- **Product-Specific Rates**: Verify different processing speeds per product

### 1.2 Source Primitive Tests
- **Order Dispatch**: Test order reception from scheduler
- **Changeover Execution**: Validate state machine during product switches
- **Setup Scrap Generation**: Verify scrap rates during startup
- **Production Rate Control**: Test speed adjustments based on controls
- **Order Completion Logic**: Validate progress tracking and completion signals

### 1.3 Scheduler Primitive Tests
- **Changeover Matrix Calculations**: Test product-to-product transition times
- **Order Queue Management**: Verify FIFO/priority-based dispatch
- **Campaign Optimization**: Test batching logic for similar products
- **Product Family Clustering**: Validate allergen/complexity grouping
- **SMED Effect Application**: Test changeover time reductions

### 1.4 Control Manager Tests
- **Mapping Functions**: Test linear, exponential, logarithmic, stepped transformations
- **Parameter Effects**: Validate control → parameter calculations
- **Control Range Validation**: Test boundary conditions and constraints
- **Multi-Control Interactions**: Verify combined control effects

## Phase 2: Integration Testing - System Behavior

### Objective
Verify component interactions and data flow

### 2.1 Material Flow Tests
- **Equipment Connections**: Validate direct equipment-to-equipment flow
- **Queue Dynamics**: Test blocking/starvation scenarios
- **Bottleneck Identification**: Verify throughput constraints
- **Line Balancing**: Test capacity utilization across equipment

### 2.2 Production Order Tests
- **Order Lifecycle**:
  - Creation in scheduler
  - Dispatch to appropriate source
  - Progress tracking during production
  - Completion and metrics collection
- **Multi-Line Coordination**: Test parallel order execution
- **Order Priority Handling**: Validate rush orders and deadlines
- **Partial Order Completion**: Test interruption and resumption

### 2.3 Production Order Scheduling Tests
- **Schedule Generation**:
  - Test daily/weekly production schedules
  - Validate sequence optimization
  - Verify capacity constraints
- **Dynamic Rescheduling**:
  - Test response to equipment failures
  - Validate order insertion/cancellation
  - Verify schedule recovery after disruptions
- **Campaign Planning**:
  - Test product family grouping
  - Validate minimum campaign sizes
  - Verify allergen segregation rules
- **Multi-Line Scheduling**:
  - Test load balancing across lines
  - Validate product-line compatibility
  - Verify parallel schedule execution

### 2.4 Changeover Modeling Tests
- **Transition Times**: Validate matrix-based calculations
- **Setup Scrap**: Test product-specific scrap rates
- **Campaign vs Mixed**: Compare batched vs interleaved production
- **SMED Optimization**: Verify reduction levels (0%, 50%, 70%)

### 2.5 Control Effects Tests
- **Operator Training**: performance_factor, scrap_rate, micro_stop_recovery
- **PM Compliance**: mtbf, availability, failure_probability
- **Line Speed**: base_rate, energy_consumption, quality
- **Changeover Reduction**: changeover_duration, setup_scrap_rate

## Phase 3: MES Transduction Testing

### Objective
Verify data format conversion and KPI accuracy

### 3.1 Observable to MES Conversion
- **Time Bucket Aggregation**: Test 5-minute interval generation
- **State Duration Calculation**: Verify uptime/downtime tracking
- **Production Counting**: Validate good/scrap unit tallies
- **Downtime Categorization**: Test failure reason mapping

### 3.2 KPI Calculation Tests
- **OEE Components**:
  - Availability = Runtime / Planned Time
  - Performance = Actual Rate / Ideal Rate
  - Quality = Good Units / Total Units
- **Aggregation Levels**: Equipment, Line, Plant
- **Time-Based Metrics**: Shift, Daily, Weekly
- **Product-Specific Yields**: Per-SKU quality rates

### 3.3 Data Format Validation
- **Schema Compliance**: Verify column names and types
- **Timestamp Formatting**: ISO 8601 compliance
- **NULL Handling**: Test missing data scenarios
- **Data Consistency**: Cross-validate related fields

## Phase 4: Statistical Validation

### Objective
Verify simulation outputs match expected distributions

### 4.1 Failure Pattern Analysis
- **MTBF Distribution**: Validate exponential distribution fit
- **MTTR Distribution**: Verify lognormal distribution fit
- **Micro-Stop Patterns**: Test frequency and duration distributions
- **Failure Clustering**: Validate time-based correlations

### 4.2 Production Metrics
- **Throughput Variance**: Test coefficient of variation
- **Quality Distribution**: Validate normal distribution assumptions
- **Changeover Durations**: Verify consistency with matrix
- **Utilization Patterns**: Test Little's Law compliance

### 4.3 Control Response Curves
- **Sensitivity Analysis**: Measure ∂Output/∂Control for each parameter
- **Non-Linear Validation**: Test logarithmic and exponential responses
- **Interaction Effects**: Verify cross-control dependencies
- **Optimization Convergence**: Test gradient descent behavior

## Phase 5: End-to-End Scenario Testing

### Objective
Validate complete workflows and use cases

### 5.1 Baseline Scenarios
- **24-Hour Production**: Single day with 3 shifts
- **7-Day Operation**: Week-long run with maintenance windows
- **Multi-Product Campaign**: 10+ SKUs with changeovers
- **Shift Patterns**: Day/night performance variations

### 5.2 Order Scheduling Scenarios
- **High-Mix Production**: 50+ SKUs, frequent changeovers
- **Rush Order Insertion**: Dynamic priority changes
- **Machine Breakdown Recovery**: Rescheduling after failures
- **Seasonal Demand Patterns**: Variable order volumes

### 5.3 Optimization Scenarios
- **Control Sweeps**: Grid search over control space
- **Multi-Objective**: OEE vs Cost optimization
- **Constraint Satisfaction**: Meeting delivery deadlines
- **Pareto Analysis**: Trade-off curve generation

### 5.4 Failure Scenarios
- **Cascading Failures**: Upstream equipment impact
- **Recovery Analysis**: Time to baseline after major failure
- **Maintenance Windows**: Planned vs unplanned downtime
- **Buffer Recovery**: Queue dynamics after starvation

### 5.5 Database Integration
- **Run Persistence**: Save/load simulation states
- **Pattern Discovery**: Query for anomalies
- **Recommendation Engine**: Generate optimization suggestions
- **Historical Comparison**: Validate against real data

## Phase 6: Performance and Scalability

### Objective
Ensure simulation efficiency at scale

### 6.1 Performance Benchmarks
- **Event Processing**: Target >10,000 events/second
- **Memory Profile**: <500MB for 24-hour simulation
- **CPU Utilization**: Linear scaling with equipment count
- **I/O Operations**: Minimize database writes

### 6.2 Scalability Tests
- **Multi-Line Scale**: 3, 5, 10 production lines
- **Time Horizons**: 1, 7, 30, 90 day simulations
- **Event Frequency**: 1000+ micro-stops/day
- **Order Volume**: 100, 1000, 10000 orders

### 6.3 Production Scheduling Scale
- **Large Order Books**: 1000+ orders pending
- **Complex Constraints**: 20+ scheduling rules
- **Multi-Facility**: Coordinate across plants
- **Real-Time Updates**: Dynamic schedule adjustments

## Test Implementation Strategy

### Test Framework Setup
```python
# pytest configuration
pytest.ini:
  - markers for test categories (unit, integration, e2e)
  - coverage targets (>90% for core, >80% overall)
  - performance benchmarks

# Fixtures
conftest.py:
  - Standard equipment configurations
  - Test data generators
  - Mock manifests and ontologies
```

### Test Data Management
- **Synthetic Data Generation**: Reproducible test datasets
- **Golden Datasets**: Validated reference outputs
- **Edge Cases**: Boundary conditions and error states
- **Performance Datasets**: Large-scale test scenarios

### Continuous Integration
- **Pre-Commit Hooks**: Run unit tests
- **PR Validation**: Integration test suite
- **Nightly Builds**: Full E2E scenarios
- **Weekly**: Performance and scale tests

## Success Criteria

### Coverage Metrics
- Unit Test Coverage: >90%
- Integration Coverage: >85%
- E2E Scenarios: 100% of critical paths

### Accuracy Metrics
- KPI Deviation: <5% from expected values
- Distribution Fit: p-value >0.05 for statistical tests
- Control Response: R² >0.95 for mapping functions

### Performance Metrics
- Simulation Speed: >100x real-time
- Memory Stability: No leaks over 7-day runs
- Scaling: Linear with equipment count
- Database: <100ms query response

### Production Scheduling Metrics
- Schedule Feasibility: 100% valid schedules
- Optimization Gap: <10% from theoretical optimum
- Rescheduling Time: <1 second for disruptions
- Order Fulfillment: >95% on-time delivery

## Test Execution Timeline

### Week 1-2: Unit Testing
- Implement primitive test suites
- Achieve coverage targets
- Document test cases

### Week 3-4: Integration Testing
- Material flow validation
- Order scheduling tests
- Control system verification

### Week 5: MES Transduction
- Format conversion tests
- KPI calculation validation
- Database integration

### Week 6: Statistical Validation
- Distribution fitting
- Response curve analysis
- Sensitivity testing

### Week 7-8: E2E Scenarios
- Baseline operations
- Optimization runs
- Failure recovery

### Week 9: Performance Testing
- Benchmarking
- Scalability validation
- Optimization

### Week 10: Documentation and Reporting
- Test report generation
- Performance dashboards
- Recommendations

## Risk Mitigation

### Technical Risks
- **Simulation Accuracy**: Validate against historical data
- **Performance Bottlenecks**: Profile and optimize critical paths
- **Integration Issues**: Mock external dependencies

### Process Risks
- **Test Maintenance**: Automated test generation where possible
- **False Positives**: Statistical significance testing
- **Environment Differences**: Containerized test environments

## Appendix: Test Case Examples

### Example 1: Changeover Time Validation
```python
def test_changeover_matrix_calculation():
    """Validate product-to-product changeover times"""
    scheduler = SchedulerPrimitiveV2(env, config)
    
    # Test same product (no changeover)
    assert scheduler.get_changeover_time("SKU-001", "SKU-001") == 0
    
    # Test same family (minor changeover)
    assert scheduler.get_changeover_time("SKU-001", "SKU-002") == 15
    
    # Test different family (major changeover)
    assert scheduler.get_changeover_time("SKU-001", "SKU-101") == 45
    
    # Test allergen contamination (extended changeover)
    assert scheduler.get_changeover_time("SKU-NUTS", "SKU-CLEAN") == 90
```

### Example 2: Order Scheduling Validation
```python
def test_production_order_scheduling():
    """Validate order dispatch and scheduling logic"""
    scheduler = SchedulerPrimitiveV2(env, config)
    source = SourcePrimitiveV2(env, source_config)
    
    # Create orders with different priorities
    orders = [
        ProductionOrder("ORD-001", "SKU-001", 1000, priority=1),
        ProductionOrder("ORD-002", "SKU-002", 500, priority=2),
        ProductionOrder("ORD-003", "SKU-001", 750, priority=1),
    ]
    
    # Schedule orders
    scheduler.add_orders(orders)
    schedule = scheduler.generate_schedule()
    
    # Validate sequence optimization
    assert schedule[0].order_id == "ORD-002"  # Highest priority
    assert schedule[1].order_id == "ORD-001"  # Same SKU as order 3
    assert schedule[2].order_id == "ORD-003"  # Batched with order 1
```

### Example 3: Control Effect Validation
```python
def test_operator_training_effect():
    """Validate operator training impact on performance"""
    control_mgr = ControlManager(mappings_path, settings_path)
    
    # Test performance improvement
    control_mgr.set_control("operator_training_hours", 0)
    assert control_mgr.get_parameter("performance_factor") == 1.0
    
    control_mgr.set_control("operator_training_hours", 40)
    assert 1.10 <= control_mgr.get_parameter("performance_factor") <= 1.12
    
    # Test diminishing returns
    control_mgr.set_control("operator_training_hours", 80)
    assert control_mgr.get_parameter("performance_factor") < 1.15
```

## Conclusion

This comprehensive testing plan ensures the Virtual Twin Model simulation system is thoroughly validated across all components, from individual primitives to complete production scenarios. Special attention is given to production order scheduling, which is validated through dedicated test scenarios covering schedule generation, dynamic rescheduling, campaign planning, and multi-line coordination.

The plan emphasizes both functional correctness and performance characteristics, ensuring the system can handle real-world production complexity while maintaining accuracy and efficiency.