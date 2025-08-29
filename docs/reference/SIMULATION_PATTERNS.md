# Simulation Patterns

## Overview

This guide documents common patterns and strategies for building effective production simulations with the Virtual Twin Model. These patterns represent best practices discovered through implementation and testing.

## Failure Modeling Patterns

### Exponential Distribution Pattern
Use exponential distribution for realistic failure timing:

```python
def _generate_failures(self) -> Generator:
    """Generate failures with exponential distribution"""
    while self.is_running:
        # Wait for next failure (exponential distribution)
        time_to_failure = random.expovariate(1.0 / self.mtbf)
        yield self.env.timeout(time_to_failure)
        
        if self.state == EquipmentState.RUNNING:
            # Trigger failure
            self._change_state(EquipmentState.FAILED)
            
            # Repair time (also exponential)
            repair_time = random.expovariate(1.0 / self.mttr)
            yield self.env.timeout(repair_time)
            
            # Resume operation
            self._change_state(EquipmentState.RUNNING)
```

### Micro-Stop Pattern
Model brief interruptions separately from major failures:

```python
def _generate_micro_stops(self) -> Generator:
    """Generate minor stoppages during processing"""
    while self.is_running:
        # Check each unit for micro-stop
        if random.random() < self.micro_stop_probability:
            self._change_state(EquipmentState.MICRO_STOP)
            
            # Brief stoppage (fixed duration)
            yield self.env.timeout(self.micro_stop_duration)
            
            self._change_state(EquipmentState.RUNNING)
            self.micro_stop_count += 1
        
        yield self.env.timeout(0.1)  # Check interval
```

### Cascading Failure Pattern
Model how upstream failures affect downstream equipment:

```python
def propagate_failure(self, source_equipment):
    """Handle cascading effects from upstream failure"""
    if source_equipment.state == EquipmentState.FAILED:
        # Gradual starvation
        yield self.env.timeout(self.input_queue.capacity / self.processing_rate)
        if self.input_queue.items == 0:
            self._change_state(EquipmentState.IDLE)
```

## Changeover Optimization Patterns

### Campaign Mode Pattern
Group similar products to minimize changeovers:

```python
def _sequence_orders_campaign(self) -> List[ProductionOrder]:
    """Group orders by product family"""
    # Sort orders by family, then by due date
    sorted_orders = sorted(self.pending_orders, 
                          key=lambda x: (x.product.family, x.due_date))
    
    # Create campaigns of similar products
    campaigns = []
    current_family = None
    current_campaign = []
    
    for order in sorted_orders:
        if order.product.family != current_family:
            if current_campaign:
                campaigns.append(current_campaign)
            current_family = order.product.family
            current_campaign = [order]
        else:
            current_campaign.append(order)
    
    if current_campaign:
        campaigns.append(current_campaign)
    
    # Flatten campaigns back to order list
    return [order for campaign in campaigns for order in campaign]
```

### Changeover Matrix Pattern
Use a matrix to define product-to-product changeover times:

```python
class ChangeoverMatrix:
    def __init__(self, products):
        self.products = products
        n = len(products)
        self.matrix = np.zeros((n, n))
        self._populate_matrix()
    
    def _populate_matrix(self):
        """Define changeover times based on product relationships"""
        for i, p1 in enumerate(self.products):
            for j, p2 in enumerate(self.products):
                if i == j:
                    self.matrix[i, j] = 0  # Same product
                elif p1.family == p2.family:
                    self.matrix[i, j] = 10  # Same family
                else:
                    # Different families - consider complexity
                    base_time = 20
                    complexity_factor = abs(p1.complexity - p2.complexity)
                    self.matrix[i, j] = base_time + complexity_factor * 30
```

### SMED Implementation Pattern
Apply Single-Minute Exchange of Die principles:

```python
def apply_smed_reduction(self, base_changeover_time, smed_level):
    """Apply SMED reduction to changeover time"""
    reductions = {
        0: 1.0,   # No SMED
        1: 0.5,   # Basic SMED - 50% reduction
        2: 0.3,   # Advanced SMED - 70% reduction
    }
    
    reduction_factor = reductions.get(smed_level, 1.0)
    
    # Apply reduction with minimum time constraint
    reduced_time = base_changeover_time * reduction_factor
    return max(reduced_time, 5.0)  # Minimum 5 minute changeover
```

## Production Scheduling Patterns

### Pull Production Pattern
Produce based on downstream demand:

```python
def pull_production_pattern(self):
    """Produce only when downstream has capacity"""
    while True:
        # Check downstream capacity
        downstream_space = (self.downstream.capacity - 
                          len(self.downstream.items))
        
        if downstream_space > 0:
            # Produce unit
            unit = yield from self._process_unit()
            yield self.downstream.put(unit)
        else:
            # Wait for downstream to clear
            yield self.env.timeout(1)
```

### Push Production Pattern
Produce at maximum rate regardless of downstream:

```python
def push_production_pattern(self):
    """Produce at full capacity"""
    while True:
        # Process continuously
        unit = yield from self._process_unit()
        
        # Try to push downstream
        if len(self.output_queue.items) < self.output_queue.capacity:
            yield self.output_queue.put(unit)
        else:
            # Output blocked - equipment stops
            self._change_state(EquipmentState.BLOCKED)
            yield self.env.timeout(1)
```

### Mixed Priority Pattern
Balance urgent orders with efficiency:

```python
def mixed_priority_scheduling(self):
    """Balance urgency with changeover efficiency"""
    
    # Separate urgent and normal orders
    urgent = [o for o in self.pending_orders if o.priority > 7]
    normal = [o for o in self.pending_orders if o.priority <= 7]
    
    # Process urgent orders first
    scheduled = sorted(urgent, key=lambda x: x.due_date)
    
    # Then optimize normal orders for changeovers
    if normal:
        optimized_normal = self._optimize_changeovers(normal)
        scheduled.extend(optimized_normal)
    
    return scheduled
```

## Performance Bottleneck Patterns

### Bottleneck Identification Pattern
Find the constraining equipment:

```python
def identify_bottleneck(production_line):
    """Find bottleneck based on queue sizes and utilization"""
    bottleneck_score = {}
    
    for equipment in production_line:
        # Calculate bottleneck indicators
        avg_queue = np.mean(equipment.queue_history)
        utilization = equipment.state_durations[RUNNING] / total_time
        starvation = equipment.state_durations[IDLE] / total_time
        
        # Composite score
        score = (avg_queue * 0.4 + 
                utilization * 0.4 + 
                (1 - starvation) * 0.2)
        
        bottleneck_score[equipment.id] = score
    
    # Highest score is likely bottleneck
    return max(bottleneck_score, key=bottleneck_score.get)
```

### Bottleneck Protection Pattern
Protect bottleneck from starvation:

```python
def protect_bottleneck(bottleneck_equipment):
    """Ensure bottleneck always has material"""
    
    # Increase upstream buffer
    upstream = bottleneck_equipment.upstream
    upstream.output_queue = simpy.Store(env, capacity=50)  # Larger buffer
    
    # Prioritize bottleneck maintenance
    bottleneck_equipment.mtbf *= 1.2  # Improve reliability
    bottleneck_equipment.mttr *= 0.8   # Faster repairs
    
    # Assign best operators
    bottleneck_equipment.performance_factor = 1.1
```

## Quality Control Patterns

### Progressive Quality Degradation
Model quality decline over time:

```python
def quality_degradation_pattern(self):
    """Quality degrades between maintenance"""
    base_quality = 0.98
    degradation_rate = 0.0001  # Per unit
    units_since_maintenance = 0
    
    while True:
        # Current quality rate
        current_quality = base_quality - (units_since_maintenance * 
                                         degradation_rate)
        current_quality = max(current_quality, 0.85)  # Floor
        
        # Process with degraded quality
        if random.random() < current_quality:
            yield self._process_good_unit()
        else:
            yield self._process_defect()
        
        units_since_maintenance += 1
```

### Statistical Process Control Pattern
Implement control limits:

```python
def spc_pattern(self):
    """Statistical process control monitoring"""
    measurements = deque(maxlen=30)  # Last 30 units
    
    while True:
        unit = yield from self._process_unit()
        measurement = self._measure_quality(unit)
        measurements.append(measurement)
        
        if len(measurements) >= 30:
            mean = np.mean(measurements)
            std = np.std(measurements)
            
            # Check control limits
            ucl = mean + 3 * std
            lcl = mean - 3 * std
            
            if measurement < lcl or measurement > ucl:
                self.emit_observable("out_of_control", {
                    "value": measurement,
                    "ucl": ucl,
                    "lcl": lcl
                })
```

## State Management Patterns

### State Transition Pattern
Clean state transitions with duration tracking:

```python
def state_transition_pattern(self, new_state):
    """Proper state transition with events"""
    
    # Finalize current state
    if self.current_state:
        duration = self.env.now - self.state_start_time
        self.state_durations[self.current_state] += duration
        
        # Emit transition event
        self.emit_observable("state_change", {
            "from": self.current_state,
            "to": new_state,
            "duration": duration
        })
    
    # Enter new state
    self.current_state = new_state
    self.state_start_time = self.env.now
    
    # State-specific actions
    self._on_state_enter(new_state)
```

### State Machine Pattern
Formal state machine implementation:

```python
class StateMachine:
    def __init__(self):
        self.transitions = {
            (IDLE, "material_available"): RUNNING,
            (RUNNING, "queue_empty"): IDLE,
            (RUNNING, "failure"): FAILED,
            (FAILED, "repaired"): RUNNING,
            (RUNNING, "maintenance_due"): MAINTENANCE,
            (MAINTENANCE, "complete"): RUNNING
        }
    
    def transition(self, current_state, event):
        """Get next state based on event"""
        key = (current_state, event)
        if key in self.transitions:
            return self.transitions[key]
        return current_state  # No transition
```

## Event Coordination Patterns

### Event Aggregation Pattern
Collect events for batch processing:

```python
class EventAggregator:
    def __init__(self, window_size=60):
        self.window_size = window_size
        self.events = []
        self.env = env
        self.env.process(self.aggregate())
    
    def aggregate(self):
        """Periodically process batched events"""
        while True:
            yield self.env.timeout(self.window_size)
            
            if self.events:
                summary = self._summarize_events(self.events)
                self.emit_observable("batch_summary", summary)
                self.events.clear()
    
    def add_event(self, event):
        """Add event to batch"""
        self.events.append((self.env.now, event))
```

### Event Filtering Pattern
Selective event propagation:

```python
def event_filter_pattern(self, event_type, data):
    """Filter events based on criteria"""
    
    # Define filter rules
    filters = {
        "state_change": lambda d: d["to"] in [FAILED, MAINTENANCE],
        "unit_scrapped": lambda d: d["scrap_rate"] > 0.05,
        "order_completed": lambda d: d["tardiness"] > 0
    }
    
    # Apply filter
    if event_type in filters:
        if filters[event_type](data):
            self.emit_observable(f"filtered_{event_type}", data)
```

## Optimization Patterns

### Parameter Sweep Pattern
Systematic parameter exploration:

```python
def parameter_sweep_pattern():
    """Test multiple parameter combinations"""
    results = []
    
    for training in [0, 20, 40, 60]:
        for maintenance in [50, 70, 90]:
            for speed in [80, 90, 100]:
                # Set controls
                controls = {
                    "operator_training_hours": training,
                    "pm_schedule_compliance": maintenance,
                    "line_speed_setting": speed
                }
                
                # Run simulation
                kpis = run_simulation(controls, duration=480)
                
                results.append({
                    "controls": controls,
                    "oee": kpis["oee"],
                    "cost": calculate_cost(controls)
                })
    
    # Find optimal
    return max(results, key=lambda x: x["oee"] - x["cost"]/1000)
```

### Adaptive Control Pattern
Adjust controls based on performance:

```python
def adaptive_control_pattern(self):
    """Dynamically adjust controls"""
    
    while True:
        # Monitor performance
        current_oee = self.get_current_oee()
        target_oee = 0.85
        
        if current_oee < target_oee * 0.95:
            # Performance below target
            if self.availability < 0.90:
                # Improve maintenance
                self.control_mgr.adjust_control(
                    "pm_schedule_compliance", delta=10
                )
            elif self.performance < 0.95:
                # Improve speed/training
                self.control_mgr.adjust_control(
                    "operator_training_hours", delta=8
                )
        
        yield self.env.timeout(60)  # Check hourly
```

## Testing Patterns

### Scenario Testing Pattern
Test specific scenarios systematically:

```python
def scenario_test_pattern():
    """Test predefined scenarios"""
    
    scenarios = {
        "baseline": {
            "controls": default_controls(),
            "expected_oee": (0.40, 0.60)
        },
        "optimized": {
            "controls": optimized_controls(),
            "expected_oee": (0.70, 0.85)
        },
        "degraded": {
            "controls": degraded_controls(),
            "expected_oee": (0.20, 0.35)
        }
    }
    
    for name, scenario in scenarios.items():
        result = run_scenario(scenario["controls"])
        assert scenario["expected_oee"][0] <= result["oee"] <= scenario["expected_oee"][1]
```

### Stress Testing Pattern
Test system limits:

```python
def stress_test_pattern():
    """Push system to limits"""
    
    # High load test
    high_load = {
        "arrival_rate": 150,  # 150% of capacity
        "duration": 240
    }
    
    # Failure cascade test
    failure_cascade = {
        "mtbf": 30,  # Very frequent failures
        "failure_correlation": 0.8  # High correlation
    }
    
    # Resource starvation test
    starvation = {
        "queue_sizes": 5,  # Very small queues
        "variability": 0.5  # High variability
    }
    
    for test in [high_load, failure_cascade, starvation]:
        result = run_stress_test(test)
        validate_graceful_degradation(result)
```

## Summary

These patterns provide:
- **Proven Solutions**: Battle-tested approaches
- **Realistic Modeling**: Industry-accurate behaviors
- **Performance**: Efficient implementations
- **Flexibility**: Adaptable to various scenarios
- **Testability**: Systematic validation approaches

Use these patterns as building blocks for complex simulation scenarios while adapting them to specific requirements.