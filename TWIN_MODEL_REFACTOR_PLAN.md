# Twin Model Refactor and Implementation Plan

## Executive Summary

This plan addresses critical issues in the virtual twin model that prevent achieving realistic KPIs (target: 60% OEE with balanced availability, performance, and quality). The refactor incorporates SimPy best practices, realistic failure modeling, and maintains the ontology-driven architecture.

## Coding notes
ok please implement @TWIN_MODEL_REFACTOR_PLAN.md and Comply with PEP 8 (Style Guide), PEP 257 (Docstring Convetions), PEP 484 (Type Hints). use context7 (search for simpy-mirror     │
│   for simpy docs). DO NOT CREATE ANY HARDCODES, leverage the configs and manifests.   

## Current Issues

### 1. **Material Flow Logic Problem (Critical)**
- Equipment checks `upstream.level` but buffers use `self.store.items`
- This mismatch causes false starvation/blocking states
- Result: Equipment runs at ~10% performance despite parameter adjustments

### 2. **Unrealistic Failure Patterns**
- Single MTBF/MTTR values don't reflect real manufacturing
- Missing micro-stops, minor failures, and major breakdowns
- Availability too high (~94% vs 60% target)

### 3. **Not Production Order Driven**
- Continuous flow instead of scheduled production orders
- Doesn't match real MES-driven manufacturing

### 4. **Model Structure Issues**
- Over-complicated buffer connections
- SimPy best practices suggest direct equipment connections with internal queuing

---

## Phase 1: Fix Material Flow Logic (Immediate)

### 1.1 Buffer-Equipment Interface Fix

**File: `twin_model/primitives/buffer.py`**

```python
# Add property to expose store level correctly
@property
def level(self) -> int:
    """Current buffer level."""
    return len(self.store.items) if hasattr(self.store, 'items') else 0

@property
def is_full(self) -> bool:
    """Check if buffer is at capacity."""
    return self.level >= self.capacity
```

**File: `twin_model/primitives/equipment.py`**

```python
def run(self) -> Generator:
    """Main equipment process for production."""
    while self.is_running:
        try:
            # Fix: Check actual store level
            if self.upstream and self.upstream.level == 0:
                yield from self._handle_starved()
                continue
            
            # Fix: Check downstream capacity properly
            if self.downstream and self.downstream.is_full():
                yield from self._handle_blocked()
                continue
            
            # Process unit
            yield from self._process_unit()
```

### 1.2 Implement Proper SimPy Resource Pattern

**New approach using SimPy Container for material flow:**

```python
class EquipmentPrimitive(BasePrimitive):
    def __init__(self, env, config, upstream=None, downstream=None):
        # Use SimPy Container for internal buffer
        self.input_buffer = simpy.Container(env, 
            capacity=config.get_property('input_buffer_size', 10),
            init=0)
        self.output_buffer = simpy.Container(env, 
            capacity=config.get_property('output_buffer_size', 10),
            init=0)
```

---

## Phase 2: Implement Realistic Failure Modeling

### 2.1 Mixture Model for Failures

**Update Ontology: `ontology/twin_ontology.yaml`**

```yaml
failure_patterns:
  description: "Failure pattern definitions"
  properties:
    micro_stops:
      type: "failure_type"
      frequency: "high"  # Every 10-30 minutes
      duration_distribution: "lognormal"
      duration_params: {mean: 1.0, sigma: 0.5}  # 0.5-3 minutes
      probability: 0.80
      
    minor_failures:
      type: "failure_type"
      frequency: "medium"  # Every 2-8 hours
      duration_distribution: "gamma"
      duration_params: {shape: 2, scale: 5}  # 5-30 minutes
      probability: 0.15
      
    major_failures:
      type: "failure_type"
      frequency: "low"  # Every 24-168 hours
      duration_distribution: "weibull"
      duration_params: {shape: 2, scale: 60}  # 30+ minutes
      probability: 0.05
```

### 2.2 Failure Implementation

**File: `twin_model/primitives/equipment.py`**

```python
import numpy as np
from enum import Enum

class FailureType(Enum):
    MICRO_STOP = "micro_stop"
    MINOR_FAILURE = "minor_failure"
    MAJOR_FAILURE = "major_failure"

class EquipmentPrimitive(BasePrimitive):
    def __init__(self, env, config, ...):
        # Initialize failure parameters
        self.failure_distributions = self._load_failure_distributions(config)
        
    def _failure_process(self) -> Generator:
        """Realistic failure process with multiple failure types."""
        while self.is_running:
            # Determine next failure type and timing
            failure_type, time_to_failure = self._get_next_failure()
            
            # Wait until failure occurs
            yield self.env.timeout(time_to_failure)
            
            # Get repair duration based on failure type
            repair_duration = self._get_repair_duration(failure_type)
            
            # Interrupt the main process
            if self.process and self.process.is_alive:
                self.process.interrupt({
                    'type': failure_type,
                    'duration': repair_duration
                })
    
    def _get_next_failure(self) -> Tuple[FailureType, float]:
        """Sample next failure using competing risks model."""
        # Sample time for each failure type
        micro_time = np.random.exponential(20)  # Mean 20 minutes
        minor_time = np.random.exponential(240)  # Mean 4 hours
        major_time = np.random.exponential(2880)  # Mean 48 hours
        
        # Find which occurs first
        times = {
            FailureType.MICRO_STOP: micro_time,
            FailureType.MINOR_FAILURE: minor_time,
            FailureType.MAJOR_FAILURE: major_time
        }
        
        failure_type = min(times, key=times.get)
        return failure_type, times[failure_type]
    
    def _get_repair_duration(self, failure_type: FailureType) -> float:
        """Get repair duration based on failure type."""
        if failure_type == FailureType.MICRO_STOP:
            # Log-normal: mostly 0.5-3 minutes
            duration = np.random.lognormal(0.0, 0.5)
            return np.clip(duration, 0.5, 5.0)
            
        elif failure_type == FailureType.MINOR_FAILURE:
            # Gamma: 5-30 minutes
            duration = np.random.gamma(2, 5)
            return np.clip(duration, 5, 60)
            
        else:  # MAJOR_FAILURE
            # Weibull: 30+ minutes with long tail
            duration = np.random.weibull(2) * 60
            return max(30, duration)
```

---

## Phase 3: Implement Production Order Scheduling

### 3.1 Update Scheduler Primitive

**File: `twin_model/primitives/scheduler.py`**

```python
class ProductionOrder:
    """Represents a production order."""
    def __init__(self, order_id: str, product_id: str, 
                 quantity: int, due_time: float, priority: int = 0):
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.due_time = due_time
        self.priority = priority
        self.released = False
        self.completed_quantity = 0

class SchedulerPrimitive(BasePrimitive):
    def __init__(self, env, config):
        super().__init__(env, config)
        self.orders = []
        self.active_orders = {}
        
    def add_order(self, order: ProductionOrder):
        """Add a production order to the schedule."""
        self.orders.append(order)
        self.orders.sort(key=lambda x: (x.due_time, -x.priority))
    
    def run(self) -> Generator:
        """Main scheduling process."""
        while self.is_running:
            # Check for orders to release
            current_time = self.env.now
            
            for order in self.orders[:]:
                if not order.released and self._should_release(order, current_time):
                    # Release order to production
                    yield from self._release_order(order)
                    order.released = True
                    self.active_orders[order.order_id] = order
                    self.orders.remove(order)
            
            # Check every minute
            yield self.env.timeout(1.0)
    
    def _release_order(self, order: ProductionOrder) -> Generator:
        """Release an order to the appropriate production line."""
        # Find target line based on product
        line_id = self._get_line_for_product(order.product_id)
        
        # Send order to source
        source = self._get_source(line_id)
        if source:
            source.set_production_order(order)
        
        self.emit_observable(
            event_type="order_released",
            details={
                "order_id": order.order_id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "line": line_id
            }
        )
        
        yield self.env.timeout(0)
```

### 3.2 Update Source for Order-Driven Generation

**File: `twin_model/primitives/source.py`**

```python
class SourcePrimitive(BasePrimitive):
    def __init__(self, env, config, downstream=None):
        super().__init__(env, config)
        self.current_order = None
        self.order_queue = []
        
    def set_production_order(self, order: ProductionOrder):
        """Set a production order for this source."""
        self.order_queue.append(order)
        
    def run(self) -> Generator:
        """Order-driven material generation."""
        while self.is_running:
            # Check for new orders
            if not self.current_order and self.order_queue:
                self.current_order = self.order_queue.pop(0)
                self.units_remaining = self.current_order.quantity
            
            # Generate units for current order
            if self.current_order and self.units_remaining > 0:
                # Generate batch
                batch_size = min(self.batch_size, self.units_remaining)
                
                # Send downstream
                if self.downstream:
                    yield from self.downstream.put(
                        batch_size, 
                        product_id=self.current_order.product_id,
                        order_id=self.current_order.order_id
                    )
                
                self.units_remaining -= batch_size
                
                # Check if order complete
                if self.units_remaining <= 0:
                    self._complete_order()
                    self.current_order = None
                
                # Production rate delay
                yield self.env.timeout(batch_size / self.arrival_rate)
            else:
                # No active order, wait
                yield self.env.timeout(1.0)
```

---

## Phase 4: Simplify Model Structure (SimPy Best Practices)

### 4.1 Direct Equipment Connections

**Option A: Equipment with Internal Queues**

```python
class EquipmentPrimitive(BasePrimitive):
    def __init__(self, env, config):
        # Internal queues instead of external buffers
        self.input_queue = simpy.Store(env, capacity=config.get_property('queue_size', 20))
        self.output_queue = simpy.Store(env, capacity=config.get_property('queue_size', 20))
        
        # Direct connections to other equipment
        self.upstream_equipment = None
        self.downstream_equipment = None
    
    def connect_to(self, downstream_equipment):
        """Connect directly to downstream equipment."""
        self.downstream_equipment = downstream_equipment
        downstream_equipment.upstream_equipment = self
```

**Option B: Use SimPy Resources**

```python
class ProductionLine:
    def __init__(self, env, line_id: str):
        self.env = env
        self.line_id = line_id
        
        # Equipment as resources
        self.filler = simpy.Resource(env, capacity=1)
        self.packer = simpy.Resource(env, capacity=1)
        self.palletizer = simpy.Resource(env, capacity=1)
        
        # Material flow as containers
        self.raw_material = simpy.Container(env, capacity=1000, init=0)
        self.filled_units = simpy.Container(env, capacity=100, init=0)
        self.packed_units = simpy.Container(env, capacity=100, init=0)
        
    def process_order(self, order: ProductionOrder) -> Generator:
        """Process a production order through the line."""
        for i in range(order.quantity):
            # Request filler
            with self.filler.request() as req:
                yield req
                yield self.env.timeout(1.0 / self.filler_rate)
                yield self.filled_units.put(1)
            
            # Request packer
            with self.packer.request() as req:
                yield req
                yield self.filled_units.get(1)
                yield self.env.timeout(1.0 / self.packer_rate)
                yield self.packed_units.put(1)
```

---

## Phase 5: Update Manifests and Configuration

### 5.1 Equipment Manifest Changes

**File: `manifests/equipment_manifest.yaml`**

```yaml
equipment:
  LINE1-FIL:
    type: Filler
    base_rate: 85  # Units per minute at nominal
    # Remove performance_by_product - handle in code
    
    # Failure parameters (mixture model)
    failure_patterns:
      micro_stops:
        mean_time_between: 20  # minutes
        duration_mean: 1.0
        duration_sigma: 0.5
        
      minor_failures:
        mean_time_between: 240  # 4 hours
        duration_shape: 2
        duration_scale: 5
        
      major_failures:
        mean_time_between: 2880  # 48 hours
        duration_shape: 2
        duration_scale: 60
    
    # Internal queue sizes (if using Option A)
    input_queue_size: 20
    output_queue_size: 20
    
    # Quality parameters
    base_scrap_rate: 0.05  # 5% for 95% quality
```

### 5.2 Production Order Configuration

**New File: `manifests/production_schedule.yaml`**

```yaml
production_orders:
  - order_id: "ORD-001"
    product_id: "SKU-1001"
    quantity: 1000
    due_time: 480  # 8 hours
    priority: 1
    line_assignment: "LINE1"
    
  - order_id: "ORD-002"
    product_id: "SKU-2001"
    quantity: 1500
    due_time: 960  # 16 hours
    priority: 2
    line_assignment: "LINE2"
```

---

## Phase 6: Testing and Validation

### 6.1 Unit Tests

```python
# twin_model/tests/test_material_flow.py
def test_buffer_level_property():
    """Test that buffer level property works correctly."""
    env = simpy.Environment()
    config = PrimitiveConfig(id="TEST-BUF", properties={"capacity": 10})
    buffer = BufferPrimitive(env, config)
    
    assert buffer.level == 0
    env.process(buffer.put(5))
    env.run(until=1)
    assert buffer.level == 5

def test_equipment_starvation_detection():
    """Test equipment correctly detects starvation."""
    # Test that equipment properly checks upstream.level
    pass

# twin_model/tests/test_failure_patterns.py
def test_mixture_model_failures():
    """Test that failure mixture model generates correct distribution."""
    # Verify micro, minor, and major failures occur at expected rates
    pass
```

### 6.2 Integration Tests

```python
# twin_model/tests/test_production_order_flow.py
def test_order_driven_production():
    """Test complete order flow from scheduler to sink."""
    env = simpy.Environment()
    
    # Create production line
    builder = OntologyDrivenModelBuilder()
    model = builder.build_model(env)
    
    # Add production order
    order = ProductionOrder("ORD-TEST", "SKU-1001", 100, 60, 1)
    scheduler = builder.primitives['SCHEDULER-DEFAULT']
    scheduler.add_order(order)
    
    # Run simulation
    env.run(until=120)
    
    # Verify order completed
    sink = builder.primitives['LINE1-SINK']
    assert sink.total_collected >= 95  # Allow for some scrap
```

---

## Implementation Timeline

### Week 1: Critical Fixes
- [ ] Day 1-2: Fix material flow logic (Phase 1)
- [ ] Day 3-4: Implement failure mixture model (Phase 2.1-2.2)
- [ ] Day 5: Test and validate fixes

### Week 2: Structural Improvements
- [ ] Day 1-2: Implement production order scheduling (Phase 3)
- [ ] Day 3-4: Simplify model structure (Phase 4)
- [ ] Day 5: Update manifests and configuration (Phase 5)

### Week 3: Testing and Calibration
- [ ] Day 1-2: Write and run unit tests
- [ ] Day 3-4: Integration testing
- [ ] Day 5: Final calibration for 60% OEE target

---

## Expected Outcomes

### KPI Targets
- **OEE**: 60% (±5%)
  - **Availability**: 60% (realistic with failure mixture model)
  - **Performance**: 85% (fixed material flow logic)
  - **Quality**: 95% (base_scrap_rate = 0.05)

### Benefits
1. **Realistic Simulation**: Matches actual manufacturing patterns
2. **MES Alignment**: Order-driven production matches real MES data
3. **Optimization Ready**: Can test "what-if" scenarios effectively
4. **Ontology Driven**: Maintains ontology-based architecture

---

## Risk Mitigation

### Risk 1: Breaking Existing Functionality
- **Mitigation**: Implement changes incrementally with tests
- **Fallback**: Git branching strategy, can revert if needed

### Risk 2: Performance Issues with Complex Failure Model
- **Mitigation**: Profile and optimize critical paths
- **Fallback**: Simplify to two-tier failure model if needed

### Risk 3: Integration Complexity
- **Mitigation**: Keep clear interfaces between components
- **Fallback**: Phase implementation over longer timeline

---

## Notes on SimPy Best Practices (from research)

1. **Use Interrupts for Failures**: SimPy's interrupt mechanism is ideal for machine breakdowns
2. **Resource vs Container**: Use Resource for equipment, Container for material flow
3. **Direct Yielding**: Yield events directly rather than complex callback chains
4. **Process-Based Design**: Each major component should be a process
5. **Event Composition**: Use `&` and `|` operators for complex conditions

---

## Appendix: Key Code Patterns

### Pattern 1: Preemptive Resource for Maintenance
```python
repairman = simpy.PreemptiveResource(env, capacity=1)
with repairman.request(priority=1) as req:  # High priority for repairs
    yield req
    yield env.timeout(repair_time)
```

### Pattern 2: Container for Material Flow
```python
material_buffer = simpy.Container(env, capacity=1000, init=100)
yield material_buffer.get(10)  # Get 10 units
yield material_buffer.put(5)   # Put 5 units
```

### Pattern 3: Process Interruption
```python
try:
    yield env.timeout(processing_time)
except simpy.Interrupt as interrupt:
    # Handle interruption
    failure_info = interrupt.cause
```

---

This plan provides a comprehensive roadmap to fix the virtual twin model while maintaining the ontology-driven architecture and achieving realistic KPIs.