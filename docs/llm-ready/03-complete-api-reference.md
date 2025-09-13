# Complete API Reference

This document provides comprehensive API documentation for the Twin Model simulation framework.

## Table of Contents

1. [Core Classes](#core-classes)
2. [Flow Primitives](#flow-primitives)
3. [Control Components](#control-components)
4. [Scheduling Components](#scheduling-components)
5. [MES Integration](#mes-integration)
6. [Data Classes](#data-classes)

---

## Core Classes

### OntologyModelBuilder

Builds simulation models from ontology, manifest, and configuration files.

```python
class OntologyModelBuilder:
    def __init__(
        self,
        env: simpy.Environment,
        ontology_path: Path,
        manifest_path: Path,
        config_path: Path
    ) -> None:
        """Initialize the model builder.

        Args:
            env: SimPy environment
            ontology_path: Path to ontology YAML file
            manifest_path: Path to equipment manifest YAML file
            config_path: Path to configuration parameters YAML file
        """
```

#### Methods

- **`build_model() -> dict[str, Any]`**
  - Builds complete simulation model from configuration files
  - Returns dictionary containing:
    - `primitives`: Dictionary of all equipment instances
    - `lines`: Equipment organized by production line
    - `metadata`: Model metadata and configuration

- **`get_metrics() -> dict[str, Any]`**
  - Returns current metrics from all equipment
  - Includes OEE, availability, performance, quality for each equipment

---

## Flow Primitives

### BaseFlowPrimitive

Abstract base class for all flow-based primitives.

```python
class BaseFlowPrimitive(ABC):
    def __init__(
        self,
        env: simpy.Environment,
        equipment_id: str,
        config: dict[str, Any],
        flow_capacity: FlowCapacity
    ) -> None:
        """Initialize base flow primitive."""
```

#### Methods

- **`start() -> None`**
  - Start the flow process

- **`change_state(new_state: FlowState, downtime_reason: str = None) -> None`**
  - Change current state and update metrics
  - Parameters:
    - `new_state`: New flow state (IDLE, FLOWING, STARVED, BLOCKED, FAILED)
    - `downtime_reason`: Optional reason for downtime

- **`get_oee() -> float`**
  - Calculate Overall Equipment Effectiveness
  - Returns: OEE as percentage (0-100)

- **`get_availability() -> float`**
  - Calculate equipment availability
  - Returns: Availability as percentage (0-100)

- **`get_performance() -> float`**
  - Calculate equipment performance
  - Returns: Performance as percentage (0-100)

- **`get_quality() -> float`**
  - Calculate equipment quality
  - Returns: Quality as percentage (0-100)

### SourceFlow

Source generating continuous material flow.

```python
class SourceFlow(BaseFlowPrimitive):
    def __init__(
        self,
        env: simpy.Environment,
        equipment_id: str,
        config: dict[str, Any],
        flow_capacity: FlowCapacity,
        generation_params: dict[str, Any]
    ) -> None:
        """Initialize source flow."""
```

#### Methods

- **`add_order(order: ProductionOrder) -> None`**
  - Add a production order to the queue
  - Parameters:
    - `order`: Production order to add

- **`cancel_order(order_id: str) -> bool`**
  - Cancel a production order
  - Parameters:
    - `order_id`: ID of order to cancel
  - Returns: True if order was cancelled, False if not found

- **`get_queue_status() -> dict[str, Any]`**
  - Get current queue status
  - Returns: Dictionary with queue information

### EquipmentFlow

Equipment with continuous flow processing.

```python
class EquipmentFlow(BaseFlowPrimitive):
    def __init__(
        self,
        env: simpy.Environment,
        equipment_id: str,
        config: dict[str, Any],
        flow_capacity: FlowCapacity,
        processing_params: ProcessingParameters,
        failure_params: FailureParameters
    ) -> None:
        """Initialize equipment flow."""
```

#### Methods

- **`perform_changeover(new_product: str, changeover_time: float) -> None`**
  - Perform product changeover
  - Parameters:
    - `new_product`: New product identifier
    - `changeover_time`: Time required for changeover (minutes)

- **`get_metrics() -> dict[str, Any]`** (NEW)
  - Get comprehensive metrics including OEE
  - Returns dictionary with:
    - `total_input`: Total material input
    - `total_output`: Total material output
    - `total_scrap`: Total scrap generated
    - `oee`: Overall Equipment Effectiveness
    - `availability`: Equipment availability
    - `performance`: Equipment performance
    - `quality`: Equipment quality
    - `state`: Current equipment state
    - `utilization`: Equipment utilization

### SinkFlow

Sink collecting finished products and calculating OEE.

```python
class SinkFlow(BaseFlowPrimitive):
    def __init__(
        self,
        env: simpy.Environment,
        equipment_id: str,
        config: dict[str, Any],
        flow_capacity: FlowCapacity,
        nominal_rate: float = 50.0
    ) -> None:
        """Initialize sink flow."""
```

#### Methods

- **`calculate_window_oee(window_minutes: float) -> tuple[float, float, float, float]`**
  - Calculate OEE components for time window
  - Parameters:
    - `window_minutes`: Time window in minutes
  - Returns: Tuple of (OEE, Availability, Performance, Quality) as percentages

- **`get_production_summary() -> dict[str, Any]`**
  - Get production summary statistics
  - Returns: Dictionary with production metrics

- **`get_metrics() -> dict[str, Any]`** (NEW)
  - Get comprehensive metrics including OEE calculations
  - Returns dictionary with:
    - `total_collected`: Total units collected
    - `current_oee`: Current OEE
    - `availability`: Line availability
    - `performance`: Line performance
    - `quality`: Line quality
    - `production_rate`: Current production rate
    - `window_metrics`: Detailed window metrics

### AccumulationBuffer (NEW)

Dynamic accumulation buffer for managing material flow between equipment.

```python
class AccumulationBuffer(BaseFlowPrimitive):
    def __init__(
        self,
        env: simpy.Environment,
        config: dict[str, Any],
        flow_capacity: FlowCapacity,
        buffer_params: BufferParameters
    ) -> None:
        """Initialize accumulation buffer.

        Args:
            env: SimPy environment
            config: Configuration dictionary
            flow_capacity: Flow capacity constraints
            buffer_params: Buffer-specific parameters
        """
```

#### Methods

- **`connect(upstream: BaseFlowPrimitive, downstream: BaseFlowPrimitive) -> None`**
  - Connect buffer to upstream and downstream equipment
  - Parameters:
    - `upstream`: Upstream equipment
    - `downstream`: Downstream equipment

- **`process_flow() -> None`**
  - Main flow processing coroutine
  - Handles material transfer between equipment

- **`get_metrics() -> dict[str, Any]`**
  - Get current buffer metrics
  - Returns dictionary with:
    - `current_level`: Current material level
    - `utilization`: Buffer utilization percentage
    - `overflow_events`: Number of overflow events
    - `underflow_events`: Number of underflow events
    - `avg_dwell_time`: Average material residence time

---

## Control Components

### VCurveController (NEW)

Implements V-curve speed control based on Theory of Constraints principles.

```python
class VCurveController:
    def __init__(
        self,
        env: simpy.Environment,
        equipment: dict[str, BaseFlowPrimitive],
        params: VCurveParameters
    ) -> None:
        """Initialize V-curve controller.

        Args:
            env: SimPy environment
            equipment: Dictionary of equipment to control
            params: V-curve control parameters
        """
```

#### Methods

- **`start() -> None`**
  - Start the control process

- **`identify_constraint() -> str`**
  - Identify current constraint equipment
  - Returns: Equipment ID of the constraint

- **`calculate_speeds() -> dict[str, float]`**
  - Calculate V-curve speed adjustments
  - Returns: Dictionary of equipment IDs to speed multipliers

- **`apply_speed_adjustments(speeds: dict[str, float]) -> None`**
  - Apply calculated speeds to equipment
  - Parameters:
    - `speeds`: Dictionary of equipment IDs to speed multipliers

- **`get_metrics() -> dict[str, Any]`**
  - Get controller performance metrics
  - Returns dictionary with:
    - `constraint_equipment`: Current constraint ID
    - `constraint_starvation_rate`: Rate of constraint starvation
    - `constraint_blocking_rate`: Rate of constraint blocking
    - `speed_adjustments`: Current speed multipliers
    - `control_effectiveness`: Overall control effectiveness

---

## Scheduling Components

### SubOptimalScheduleGenerator (NEW)

Generates production schedules with configurable strategies.

```python
class SubOptimalScheduleGenerator:
    def __init__(
        self,
        config: Optional[ScheduleGeneratorConfig] = None,
        product_manifest_path: Optional[Path] = None,
        random_seed: Optional[int] = None
    ) -> None:
        """Initialize schedule generator.

        Args:
            config: Schedule generation configuration (optional)
            product_manifest_path: Path to product manifest YAML (optional)
            random_seed: Random seed for reproducibility (optional)
        """
```

#### Methods

- **`generate_schedule(duration_days: int, start_date: datetime) -> list[ProductionOrder]`**
  - Generate production schedule
  - Parameters:
    - `duration_days`: Duration of schedule in days
    - `start_date`: Start date for schedule
  - Returns: List of production orders

- **`calculate_changeover_time(from_product: str, to_product: str) -> float`**
  - Calculate changeover time between products
  - Parameters:
    - `from_product`: Current product
    - `to_product`: Next product
  - Returns: Changeover time in minutes

- **`optimize_sequence(orders: list[ProductionOrder]) -> list[ProductionOrder]`**
  - Optimize order sequence to minimize changeovers
  - Parameters:
    - `orders`: List of orders to optimize
  - Returns: Optimized list of orders

### ProductionScheduler

Manages production order scheduling and dispatching.

```python
class ProductionScheduler(BaseScheduler):
    def __init__(
        self,
        env: simpy.Environment,
        product_catalog: dict[str, Any],
        changeover_matrix: dict[str, dict[str, float]] = None,
        random_seed: int = None
    ) -> None:
        """Initialize production scheduler."""
```

#### Methods

- **`generate_order(line_id: str, scheduled_start: float, duration_hours: float) -> ProductionOrder`**
  - Generate a production order for a line
  - Parameters:
    - `line_id`: Production line ID
    - `scheduled_start`: Start time in simulation minutes
    - `duration_hours`: Order duration in hours
  - Returns: Generated production order

- **`get_changeover_time(from_product: str, to_product: str) -> float`**
  - Get changeover time between products
  - Parameters:
    - `from_product`: Current product ID
    - `to_product`: Next product ID
  - Returns: Changeover time in minutes

- **`get_current_order(line_id: str) -> ProductionOrder | None`**
  - Get current production order for a line
  - Parameters:
    - `line_id`: Production line ID
  - Returns: Current order or None if no active order

---

## MES Integration

### MESDataCollector

Collects simulation data and formats it for MES output.

```python
class MESDataCollector:
    def __init__(
        self,
        env: simpy.Environment,
        interval: float = 5.0,
        start_date: datetime = None
    ) -> None:
        """Initialize MES data collector.

        Args:
            env: SimPy environment
            interval: Collection interval in minutes (default 5)
            start_date: Simulation start date
        """
```

#### Methods

- **`register_equipment(equipment_id: str, equipment: BaseFlowPrimitive, equipment_type: str, line_id: str) -> None`**
  - Register equipment for monitoring
  - Parameters:
    - `equipment_id`: Unique equipment identifier
    - `equipment`: Equipment primitive to monitor
    - `equipment_type`: Type (Filler, Packer, etc.)
    - `line_id`: Production line ID

- **`update_production_order(equipment_id: str, order_id: str, product_id: str) -> None`**
  - Update current production order for equipment
  - Parameters:
    - `equipment_id`: Equipment identifier
    - `order_id`: Production order ID
    - `product_id`: Product being produced

- **`collect_current_data() -> None`** (NEW)
  - Collect data for current time point
  - Can be called manually for immediate data collection

- **`to_dataframe() -> pd.DataFrame`**
  - Convert collected records to pandas DataFrame
  - Returns: DataFrame with MES records

- **`save_to_csv(filepath: str) -> None`**
  - Save collected data to CSV file
  - Parameters:
    - `filepath`: Path to save CSV file

---

## Data Classes

### FlowCapacity

Defines flow capacity constraints for equipment.

```python
@dataclass
class FlowCapacity:
    max_input_rate: float = 100.0     # Units per minute
    max_output_rate: float = 100.0    # Units per minute
    internal_capacity: float = 1000.0 # Buffer capacity in units
    initial_level: float = 0.0        # Starting material level
```

### FlowState

Equipment flow states enumeration.

```python
class FlowState(Enum):
    IDLE = "IDLE"           # No production
    FLOWING = "FLOWING"     # Normal production
    STARVED = "STARVED"     # No input material
    BLOCKED = "BLOCKED"     # Output blocked
    FAILED = "FAILED"       # Equipment failed
    MAINTENANCE = "MAINTENANCE"  # Scheduled maintenance
    CHANGEOVER = "CHANGEOVER"   # Product changeover
```

### ProcessingParameters

Equipment processing configuration.

```python
@dataclass
class ProcessingParameters:
    nominal_rate: float = 50.0        # Design processing rate
    quality_rate: float = 0.95        # Quality percentage (0-1)
    performance_factor: float = 0.85  # Performance factor (0-1)
    batch_size: float = 10.0         # Minimum batch size (deprecated)
    processing_interval: float = 0.01 # Time between processing attempts
```

### FailureParameters

Equipment failure and maintenance parameters.

```python
@dataclass
class FailureParameters:
    mtbf: float = 120.0              # Mean time between failures (minutes)
    mttr: float = 10.0               # Mean time to repair (minutes)
    micro_stop_rate: float = 3.0     # Micro-stops per hour
    micro_stop_duration: float = 60.0 # Average micro-stop duration (seconds)
```

### BufferParameters (NEW)

Buffer configuration parameters.

```python
@dataclass
class BufferParameters:
    capacity: float = 1000.0          # Maximum buffer capacity (units)
    initial_level: float = 0.0        # Starting material level
    mode: str = "FIFO"               # Operation mode (FIFO/FILO)
    max_flow_rate: float = 100.0     # Maximum flow rate (units/min)
    warning_low: float = 0.2          # Low level warning threshold (0-1)
    warning_high: float = 0.8         # High level warning threshold (0-1)
    update_interval: float = 0.01     # Flow update interval (minutes)
```

### VCurveParameters (NEW)

V-curve controller configuration.

```python
@dataclass
class VCurveParameters:
    mode: str = "FIXED_CONSTRAINT"              # Control mode
    constraint_equipment: str = None            # Constraint equipment ID
    upstream_differential: float = 0.20         # Upstream speed increase
    downstream_differential: float = 0.15       # Downstream speed increase
    update_interval: float = 5.0               # Control update interval
    max_speed_multiplier: float = 1.4          # Maximum speed multiplier
    min_speed_multiplier: float = 0.85         # Minimum speed multiplier
```

### ProductionOrder

Production order for material generation.

```python
@dataclass
class ProductionOrder:
    order_id: str                    # Unique order identifier
    product_id: str                  # Product to produce
    target_volume: float             # Total volume to produce
    due_time: float                  # Order due time (simulation minutes)
    priority: int = 5                # Order priority (higher = more urgent)
    line_id: str = None              # Assigned production line
    scheduled_start: float = 0.0     # Scheduled start time
    actual_start: float = None       # Actual start time
    completed_volume: float = 0.0    # Completed volume
    status: str = "PENDING"          # Order status
```

### MESRecord

Single MES data record for a time interval.

```python
@dataclass
class MESRecord:
    timestamp: datetime              # Record timestamp
    equipment_id: str               # Equipment identifier
    line_id: str                    # Production line
    equipment_type: str             # Equipment type
    product_id: str                 # Current product
    order_id: str                   # Current order
    good_units: float               # Good units produced
    scrap_units: float              # Scrap units
    machine_status: str             # Machine status
    downtime_reason: str            # Downtime reason (if applicable)
    availability: float             # Availability percentage
    performance: float              # Performance percentage
    quality: float                  # Quality percentage
    oee: float                      # Overall Equipment Effectiveness
```

### ScheduleGeneratorConfig (NEW)

Configuration for schedule generation.

```python
@dataclass
class ScheduleGeneratorConfig:
    sequence_mode: str = "optimized"      # Sequencing strategy
    batch_sizing: str = "dynamic"         # Batch sizing strategy
    min_batch_hours: float = 4.0          # Minimum batch duration
    max_batch_hours: float = 12.0         # Maximum batch duration
    changeover_frequency_target: float = 0.15  # Target changeover percentage
    product_families: dict = None         # Product family definitions
```

---

## Usage Examples

### Basic Simulation Setup

```python
import simpy
from pathlib import Path
from twin_model import OntologyModelBuilder

# Create environment
env = simpy.Environment()

# Build model
builder = OntologyModelBuilder(
    env=env,
    ontology_path=Path("ontology/filling_line_ontology.yaml"),
    manifest_path=Path("manifests/equipment_manifest.yaml"),
    config_path=Path("config/tunable_parameters.yaml")
)

model = builder.build_model()

# Run simulation
env.run(until=480)  # 8 hours

# Get metrics
metrics = builder.get_metrics()
for equip_id, equip_metrics in metrics.items():
    print(f"{equip_id}: OEE={equip_metrics['oee']:.1%}")
```

### Using Buffer Management

```python
from twin_model.primitives.buffer_flow import AccumulationBuffer, BufferParameters

# Create buffer between equipment
buffer_params = BufferParameters(
    capacity=1000.0,
    mode="FIFO",
    max_flow_rate=100.0
)

buffer = AccumulationBuffer(
    env=env,
    config={"id": "BUF-001"},
    flow_capacity=FlowCapacity(),
    buffer_params=buffer_params
)

# Connect to equipment
buffer.connect(
    upstream=model['primitives']['LINE1-FIL'],
    downstream=model['primitives']['LINE1-PCK']
)
buffer.start()
```

### Implementing V-Curve Control

```python
from twin_model.control.vcurve_controller import VCurveController, VCurveParameters

# Setup V-curve control
vcurve_params = VCurveParameters(
    mode="FIXED_CONSTRAINT",
    constraint_equipment="LINE1-FIL",
    upstream_differential=0.20,
    downstream_differential=0.15
)

controller = VCurveController(
    env=env,
    equipment=model['primitives'],
    params=vcurve_params
)
controller.start()

# Run simulation
env.run(until=480)

# Check control effectiveness
metrics = controller.get_metrics()
print(f"Constraint protection: {100 - metrics['constraint_starvation_rate']*100:.1f}%")
```

### Generating Production Schedules

```python
from twin_model.scheduling.schedule_generator import SubOptimalScheduleGenerator, ScheduleGeneratorConfig
from datetime import datetime

# Configure schedule generation
config = ScheduleGeneratorConfig(
    sequence_mode="optimized",
    batch_sizing="dynamic",
    changeover_frequency_target=0.15
)

# Generate schedule
generator = SubOptimalScheduleGenerator(
    config=config,
    product_manifest_path=Path("manifests/product_manifest.yaml")
)

orders = generator.generate_schedule(
    duration_days=7,
    start_date=datetime(2025, 1, 1)
)

# Dispatch orders to production lines
for order in orders:
    source = model['primitives'][f"LINE{order.line_id}-SOURCE"]
    source.add_order(order)
```

### MES Data Collection

```python
from twin_model.transduction import MESDataCollector

# Setup MES collector
collector = MESDataCollector(
    env=env,
    interval=5.0,  # Collect every 5 minutes
    start_date=datetime(2025, 1, 1)
)

# Register equipment
for equip_id, equipment in model['primitives'].items():
    if "SOURCE" not in equip_id:  # Don't monitor sources
        line_id = equip_id.split('-')[0]
        equip_type = equip_id.split('-')[1]
        collector.register_equipment(
            equipment_id=equip_id,
            equipment=equipment,
            equipment_type=equip_type,
            line_id=line_id
        )

# Start collection
env.process(collector.collect_data())

# Run simulation
env.run(until=480)

# Save results
collector.save_to_csv("mes_output.csv")
```

---

## Error Handling

### Common Exceptions

- **`ValueError`**: Invalid configuration parameters
- **`KeyError`**: Missing required configuration keys
- **`TypeError`**: Type mismatch in configuration
- **`RuntimeError`**: Simulation runtime errors

### Best Practices

1. **Always validate configuration files** before building models
2. **Check equipment connections** match ontology constraints
3. **Monitor constraint equipment** when using V-curve control
4. **Set appropriate collection intervals** for MES data
5. **Use random seeds** for reproducible simulations

---

## Performance Considerations

### Optimization Tips

1. **Processing Intervals**: Keep processing intervals small (0.01) for smooth flow
2. **Buffer Sizing**: Size buffers to handle normal variation (10-20% of hourly rate)
3. **V-Curve Differentials**: Start with 15-20% upstream, 10-15% downstream
4. **MES Collection**: 5-minute intervals balance detail vs. performance
5. **Batch Sizing**: Dynamic batching typically outperforms fixed batching

### Memory Management

- Large simulations can generate significant MES data
- Consider periodic data export and clearing for long runs
- Use generators for order processing in large schedules

---

## Version History

- **v2.0.0**: Added buffer management, V-curve control, and schedule generation
- **v1.5.0**: Enhanced MES integration with state tracking fixes
- **v1.0.0**: Initial release with core flow primitives

---

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/your-org/twin-model
- Documentation: https://docs.twin-model.org
- Email: support@twin-model.org