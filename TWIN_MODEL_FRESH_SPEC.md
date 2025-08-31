# Twin Model Fresh Specification
## Pure Container-Based Continuous Flow Simulation

### Executive Summary

Complete ground-up rewrite of the twin model simulation system using SimPy Containers exclusively for continuous flow modeling. This specification defines a clean, configuration-driven architecture that accurately simulates high-throughput production systems with realistic OEE metrics.

**Core Philosophy**: Model actual production flow, not artificial sequential processing.

### Project Context (Preserved from Original)

#### Ontology-Driven Architecture
The system is built on an ontology-driven approach where:
- Equipment types and behaviors are defined in `ontology/twin_ontology.yaml`
- Control mappings are specified in `ontology/control_mappings.yaml`
- Equipment instances are declared in `manifests/equipment_manifest.yaml`
- Production lines are configured in `manifests/production_manifest.yaml`
- System-wide defaults are in configuration files

#### Target Output Format
The simulation must produce MES-style records matching the format in `ORIGINAL_2WEEK.csv`:
- **Time-bucketed records** (5-minute intervals)
- **Per-equipment metrics** including OEE components
- **Production tracking** with good/scrap units
- **Order and product information**
- **Machine status and downtime reasons**

Example record structure:
```
Timestamp,ProductionOrderID,LineID,EquipmentID,EquipmentType,ProductID,
ProductName,MachineStatus,DowntimeReason,GoodUnitsProduced,ScrapUnitsProduced,
TargetRate_units_per_5min,StandardCost_per_unit,SalePrice_per_unit,
Availability_Score,Performance_Score,Quality_Score,OEE_Score
```

#### Business Objectives
1. Generate realistic synthetic MES data for ML training
2. Model actual production constraints and bottlenecks
3. Support what-if analysis for production optimization
4. Maintain configuration-driven flexibility for different scenarios

### System Requirements

#### Functional Requirements
1. **Continuous Flow Processing**: Model production as volume/time, not discrete units
2. **Natural Bottleneck Emergence**: Constraints arise from capacity limits, not sequencing
3. **Realistic OEE Metrics**: Achieve 40-50% OEE (not 7% from sequential processing)
4. **Configuration-Driven**: Zero hardcoded values - everything from YAML
5. **Observable-Rich**: Emit comprehensive events for monitoring and analysis

#### Non-Functional Requirements
1. **PEP Compliance**: Full adherence to PEP 8 (style), PEP 257 (docstrings), PEP 484 (type hints)
2. **Test Coverage**: >90% coverage with comprehensive unit and integration tests
3. **Performance**: Handle 100+ equipment nodes with <1s simulation startup
4. **Maintainability**: Clean separation of concerns, no mixed paradigms
5. **Documentation**: Complete API documentation with usage examples

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Configuration Layer                      │
│  (ontology.yaml, manifests.yaml, system_config.yaml)        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Model Builder                           │
│  (Interprets config, creates primitives, wires connections) │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Simulation Layer                          │
│  ┌─────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐  │
│  │ Source  │→ │ Equipment │→ │ Equipment │→ │   Sink   │  │
│  │(Container)│ │(Container)│  │(Container)│  │(Container)│  │
│  └─────────┘  └───────────┘  └───────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Transduction Layer                         │
│        (Converts observables to MES-style records)          │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Base Flow Primitive

```python
# twin_model/primitives/base_flow.py

@dataclass
class FlowCapacity:
    """Defines flow capacity constraints."""
    max_input_rate: float      # units/minute
    max_output_rate: float     # units/minute  
    internal_capacity: float   # units
    initial_level: float = 0.0

@dataclass
class FlowState(Enum):
    """Equipment flow states."""
    IDLE = "idle"
    FLOWING = "flowing"
    STARVED_UPSTREAM = "starved_upstream"
    BLOCKED_DOWNSTREAM = "blocked_downstream"
    FAILED = "failed"
    MAINTENANCE = "maintenance"
    CHANGEOVER = "changeover"

class BaseFlowPrimitive(ABC):
    """Base class for all flow-based primitives."""
    
    def __init__(
        self,
        env: simpy.Environment,
        config: Dict[str, Any],
        flow_capacity: FlowCapacity
    ) -> None:
        self.env = env
        self.config = config
        self.flow_capacity = flow_capacity
        
        # Container buffers for continuous flow
        self.input_buffer: Optional[simpy.Container] = None
        self.output_buffer: Optional[simpy.Container] = None
        
        # Flow tracking
        self.current_state = FlowState.IDLE
        self.flow_metrics = FlowMetrics()
        self.observables: List[Dict[str, Any]] = []
    
    @abstractmethod
    def process_flow(self) -> Generator[Any, None, None]:
        """Main flow processing logic."""
        pass
```

#### 2. Equipment Flow Primitive

```python
# twin_model/primitives/equipment_flow.py

@dataclass
class ProcessingParameters:
    """Equipment processing parameters."""
    nominal_rate: float          # units/minute at 100% performance
    quality_rate: float          # fraction of good output (0-1)
    performance_factor: float    # actual vs nominal (0-1)
    batch_size: float           # minimum processing batch
    processing_interval: float   # time between batch processing

@dataclass  
class FailureParameters:
    """Equipment failure parameters."""
    mtbf: float                 # mean time between failures (minutes)
    mttr: float                 # mean time to repair (minutes)
    micro_stop_rate: float      # micro-stops per hour
    micro_stop_duration: float  # average micro-stop duration (seconds)

class EquipmentFlow(BaseFlowPrimitive):
    """Equipment with continuous flow processing."""
    
    def __init__(
        self,
        env: simpy.Environment,
        config: Dict[str, Any],
        flow_capacity: FlowCapacity,
        processing: ProcessingParameters,
        failures: FailureParameters
    ) -> None:
        super().__init__(env, config, flow_capacity)
        self.processing = processing
        self.failures = failures
        
        # Internal buffer for material accumulation
        self.internal_buffer = simpy.Container(
            env,
            capacity=flow_capacity.internal_capacity,
            init=flow_capacity.initial_level
        )
        
        # State tracking
        self.is_failed = False
        self.is_processing = False
        self.current_product = "default"
        
    def process_flow(self) -> Generator[Any, None, None]:
        """Process material in continuous batches."""
        while True:
            # Calculate batch volume based on rate and interval
            target_volume = self.processing.nominal_rate * self.processing.processing_interval
            target_volume *= self.processing.performance_factor
            
            # Check material availability
            if self.input_buffer and self.input_buffer.level >= self.processing.batch_size:
                # Pull from input
                actual_volume = min(target_volume, self.input_buffer.level)
                yield self.input_buffer.get(actual_volume)
                
                # Process (with time delay)
                self.current_state = FlowState.FLOWING
                yield self.env.timeout(self.processing.processing_interval)
                
                # Apply quality split
                good_output = actual_volume * self.processing.quality_rate
                scrap = actual_volume * (1 - self.processing.quality_rate)
                
                # Push to output
                if self.output_buffer:
                    if self.output_buffer.capacity - self.output_buffer.level >= good_output:
                        yield self.output_buffer.put(good_output)
                    else:
                        self.current_state = FlowState.BLOCKED_DOWNSTREAM
                        
                # Track metrics
                self.flow_metrics.total_input += actual_volume
                self.flow_metrics.total_output += good_output
                self.flow_metrics.total_scrap += scrap
                
                # Emit observable
                self.emit_observable("batch_processed", {
                    "volume_in": actual_volume,
                    "volume_out": good_output,
                    "scrap": scrap,
                    "rate": self.processing.nominal_rate * self.processing.performance_factor,
                    "state": self.current_state.value
                })
            else:
                # Starved - no material to process
                self.current_state = FlowState.STARVED_UPSTREAM
                yield self.env.timeout(self.processing.processing_interval)
```

#### 3. Source Flow Primitive

```python
# twin_model/primitives/source_flow.py

@dataclass
class ProductionOrder:
    """Production order for material generation."""
    order_id: str
    product_id: str
    target_volume: float
    due_time: float
    priority: int = 0
    completed_volume: float = 0.0

class SourceFlow(BaseFlowPrimitive):
    """Source generating continuous material flow."""
    
    def __init__(
        self,
        env: simpy.Environment,
        config: Dict[str, Any],
        flow_capacity: FlowCapacity,
        generation_rate: float
    ) -> None:
        super().__init__(env, config, flow_capacity)
        self.generation_rate = generation_rate
        self.order_queue: List[ProductionOrder] = []
        self.current_order: Optional[ProductionOrder] = None
        
    def process_flow(self) -> Generator[Any, None, None]:
        """Generate material based on orders or continuously."""
        while True:
            if self.current_order:
                # Order-based generation
                remaining = self.current_order.target_volume - self.current_order.completed_volume
                volume = min(
                    self.generation_rate * 0.1,  # 0.1 minute interval
                    remaining,
                    self.output_buffer.capacity - self.output_buffer.level
                )
                
                if volume > 0:
                    yield self.output_buffer.put(volume)
                    self.current_order.completed_volume += volume
                    
                    if self.current_order.completed_volume >= self.current_order.target_volume:
                        self.emit_observable("order_completed", {
                            "order_id": self.current_order.order_id,
                            "volume": self.current_order.target_volume
                        })
                        self.current_order = self._get_next_order()
            else:
                # Continuous generation
                volume = min(
                    self.generation_rate * 0.1,
                    self.output_buffer.capacity - self.output_buffer.level
                )
                if volume > 0:
                    yield self.output_buffer.put(volume)
                    
            yield self.env.timeout(0.1)  # Generation interval
```

#### 4. Sink Flow Primitive

```python
# twin_model/primitives/sink_flow.py

class SinkFlow(BaseFlowPrimitive):
    """Sink collecting finished products and calculating OEE."""
    
    def __init__(
        self,
        env: simpy.Environment,
        config: Dict[str, Any],
        flow_capacity: FlowCapacity,
        collection_rate: float
    ) -> None:
        super().__init__(env, config, flow_capacity)
        self.collection_rate = collection_rate
        self.total_collected = 0.0
        self.production_windows: List[ProductionWindow] = []
        
    def process_flow(self) -> Generator[Any, None, None]:
        """Collect products and track metrics."""
        while True:
            available = self.input_buffer.level if self.input_buffer else 0
            
            if available > 0:
                volume = min(self.collection_rate * 0.1, available)
                yield self.input_buffer.get(volume)
                self.total_collected += volume
                
                self.emit_observable("products_collected", {
                    "volume": volume,
                    "total": self.total_collected,
                    "rate": volume / 0.1
                })
                
            yield self.env.timeout(0.1)
    
    def calculate_oee(self, window_minutes: float = 60) -> Tuple[float, float, float, float]:
        """Calculate OEE components for time window."""
        # Get data for window
        window_start = max(0, self.env.now - window_minutes)
        window_data = [w for w in self.production_windows if w.timestamp >= window_start]
        
        if not window_data:
            return 0.0, 0.0, 0.0, 0.0
            
        # Availability = (Total Time - Downtime) / Total Time
        total_time = window_minutes
        downtime = sum(w.downtime for w in window_data)
        availability = (total_time - downtime) / total_time * 100
        
        # Performance = Actual Rate / Nominal Rate
        actual_volume = sum(w.volume for w in window_data)
        nominal_volume = self.collection_rate * (total_time - downtime)
        performance = (actual_volume / nominal_volume * 100) if nominal_volume > 0 else 0
        
        # Quality = Good Output / Total Output
        good_volume = sum(w.good_volume for w in window_data)
        quality = (good_volume / actual_volume * 100) if actual_volume > 0 else 0
        
        # OEE = Availability × Performance × Quality
        oee = (availability * performance * quality) / 10000
        
        return oee, availability, performance, quality
```

### Configuration Structure

#### System Configuration
```yaml
# config/system_config.yaml

flow_control:
  default_interval: 0.1           # Processing interval (minutes)
  default_batch_size: 10.0        # Minimum batch size
  default_buffer_capacity: 1000.0  # Default buffer capacity
  
performance:
  nominal_rates:                  # Units per minute by equipment type
    Filler: 250.0
    Packer: 245.0
    Palletizer: 240.0
    
quality:
  default_rates:                  # Quality rate by equipment type
    Filler: 0.95
    Packer: 0.94
    Palletizer: 0.96
    
failures:
  distributions:
    exponential:                  # For time between failures
      micro_stop: 10.0           # Minutes between micro-stops
      minor_failure: 120.0       # Minutes between minor failures
      major_failure: 1440.0      # Minutes between major failures
    
monitoring:
  observable_buffer_size: 10000
  metric_window: 60.0            # OEE calculation window (minutes)
  sampling_interval: 1.0         # Metric sampling interval
```

#### Equipment Manifest
```yaml
# manifests/equipment_manifest.yaml

equipment:
  LINE1-FILLER-01:
    type: Filler
    line_id: LINE1
    position: 1
    
    flow_capacity:
      max_input_rate: 260.0      # Slightly higher than nominal
      max_output_rate: 250.0     # Nominal rate
      internal_capacity: 500.0   # Internal buffer
      initial_level: 0.0
      
    processing:
      nominal_rate: 250.0        # Units/minute
      quality_rate: 0.95
      performance_factor: 1.0    # Can be adjusted by controls
      batch_size: 10.0
      processing_interval: 0.1
      
    failures:
      mtbf: 60.0
      mttr: 5.0
      micro_stop_rate: 6.0       # Per hour
      micro_stop_duration: 10.0  # Seconds
      
  LINE1-PACKER-01:
    type: Packer
    line_id: LINE1
    position: 2
    
    flow_capacity:
      max_input_rate: 250.0
      max_output_rate: 245.0
      internal_capacity: 400.0
      initial_level: 0.0
      
    # ... similar structure
```

### Model Builder

```python
# twin_model/model_builder.py

class FlowModelBuilder:
    """Builds flow-based simulation model from configuration."""
    
    def __init__(
        self,
        env: simpy.Environment,
        config_dir: Path,
        manifest_dir: Path
    ) -> None:
        self.env = env
        self.config = self._load_config(config_dir)
        self.manifests = self._load_manifests(manifest_dir)
        self.primitives: Dict[str, BaseFlowPrimitive] = {}
        
    def build_model(self) -> Dict[str, Any]:
        """Build complete simulation model."""
        # Create primitives
        self._create_sources()
        self._create_equipment()
        self._create_sinks()
        
        # Wire connections with shared buffers
        self._wire_connections()
        
        # Start processes
        self._start_processes()
        
        return {
            "primitives": self.primitives,
            "env": self.env,
            "config": self.config
        }
        
    def _wire_connections(self) -> None:
        """Wire equipment with shared Container buffers."""
        for line_id, line_config in self.manifests["lines"].items():
            equipment_list = self._get_line_equipment(line_id)
            
            # Sort by position
            equipment_list.sort(key=lambda e: e.config["position"])
            
            # Connect with shared buffers
            for i in range(len(equipment_list) - 1):
                current = equipment_list[i]
                next_eq = equipment_list[i + 1]
                
                # Create shared buffer
                capacity = min(
                    current.flow_capacity.max_output_rate * 10,  # 10 minutes of production
                    next_eq.flow_capacity.max_input_rate * 10,
                    self.config["flow_control"]["default_buffer_capacity"]
                )
                
                shared_buffer = simpy.Container(self.env, capacity=capacity, init=0)
                
                # Connect
                current.output_buffer = shared_buffer
                next_eq.input_buffer = shared_buffer
```

### Transduction Layer

```python
# twin_model/transduction/flow_transducer.py

class FlowTransducer:
    """Converts flow observables to MES-style records."""
    
    def __init__(self, time_bucket: float = 5.0):
        self.time_bucket = time_bucket  # Minutes
        
    def process_observables(
        self,
        observables: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Convert observables to MES DataFrame."""
        # Group by time buckets
        buckets = self._create_time_buckets(observables)
        
        records = []
        for bucket_time, bucket_data in buckets.items():
            record = {
                "Timestamp": bucket_time,
                "VolumeProduced": sum(o["volume_out"] for o in bucket_data if "volume_out" in o),
                "ScrapVolume": sum(o["scrap"] for o in bucket_data if "scrap" in o),
                "AverageRate": np.mean([o["rate"] for o in bucket_data if "rate" in o]),
                "Availability": self._calculate_availability(bucket_data),
                "Performance": self._calculate_performance(bucket_data),
                "Quality": self._calculate_quality(bucket_data)
            }
            record["OEE"] = (
                record["Availability"] * 
                record["Performance"] * 
                record["Quality"] / 10000
            )
            records.append(record)
            
        return pd.DataFrame(records)
```

### Testing Strategy

#### Unit Tests
```python
# tests/unit/test_flow_primitives.py

def test_continuous_flow():
    """Test continuous flow processing."""
    env = simpy.Environment()
    
    # Create equipment with known parameters
    equipment = EquipmentFlow(
        env=env,
        config={"id": "TEST-01"},
        flow_capacity=FlowCapacity(100, 100, 500),
        processing=ProcessingParameters(100, 0.95, 1.0, 10, 0.1),
        failures=FailureParameters(1000, 10, 0, 0)
    )
    
    # Add material
    equipment.input_buffer = simpy.Container(env, 1000, init=500)
    equipment.output_buffer = simpy.Container(env, 1000, init=0)
    
    # Run
    env.process(equipment.process_flow())
    env.run(until=10)
    
    # Verify continuous production
    assert equipment.flow_metrics.total_output > 900  # ~95 units/min * 10 min * 0.95 quality
    assert equipment.flow_metrics.total_scrap > 45   # ~5% scrap
```

#### Integration Tests
```python
# tests/integration/test_oee_validation.py

def test_oee_achievement():
    """Test that flow model achieves realistic OEE."""
    env = simpy.Environment()
    
    # Build model from config
    builder = FlowModelBuilder(
        env=env,
        config_dir=Path("config"),
        manifest_dir=Path("manifests")
    )
    model = builder.build_model()
    
    # Run for 8 hours
    env.run(until=480)
    
    # Get sink and calculate OEE
    sink = model["primitives"]["LINE1-SINK-01"]
    oee, avail, perf, qual = sink.calculate_oee(window_minutes=480)
    
    # Verify realistic OEE
    assert 40 <= oee <= 50, f"OEE {oee:.1f}% not in realistic range"
    assert 65 <= avail <= 75
    assert 70 <= perf <= 80
    assert 92 <= qual <= 98
```

### Migration Strategy

1. **Archive Current Implementation**
   ```bash
   mv twin_model twin_model_store_based_archive
   ```

2. **Create Fresh Structure**
   ```bash
   twin_model/
   ├── __init__.py
   ├── primitives/
   │   ├── __init__.py
   │   ├── base_flow.py
   │   ├── equipment_flow.py
   │   ├── source_flow.py
   │   └── sink_flow.py
   ├── model_builder.py
   ├── transduction/
   │   ├── __init__.py
   │   └── flow_transducer.py
   ├── monitoring/
   │   ├── __init__.py
   │   └── flow_monitor.py
   └── tests/
       ├── unit/
       └── integration/
   ```

3. **Implementation Order**
   - Week 1: Core primitives (base, equipment, source, sink)
   - Week 2: Model builder and wiring
   - Week 3: Transduction and monitoring
   - Week 4: Testing and validation

### Success Criteria

1. **Architecture**
   - ✅ Pure Container-based (no Store/Queue objects)
   - ✅ Configuration-driven (zero hardcoding)
   - ✅ Clean separation of concerns

2. **Metrics**
   - ✅ OEE: 40-50% (vs current 7%)
   - ✅ Availability: 65-75%
   - ✅ Performance: 70-80%
   - ✅ Quality: 92-98%

3. **Code Quality**
   - ✅ 100% type hints on public methods
   - ✅ PEP 8 compliance (ruff check passes)
   - ✅ Complete docstrings (PEP 257)
   - ✅ >90% test coverage

4. **Performance**
   - ✅ <1s startup for 100 equipment nodes
   - ✅ <100MB memory for 8-hour simulation
   - ✅ Real-time factor >10x (8 hours simulated in <48 minutes)

### Next Steps

1. **Review and approve this specification**
2. **Archive current implementation**
3. **Start fresh implementation following this spec**
4. **Use TDD approach - write tests first**
5. **Implement incrementally with validation at each step**

This specification provides a complete blueprint for a clean, maintainable, and realistic production flow simulation system.