# System Architecture

## Layered Architecture

The Virtual Twin Model follows a clean layered architecture:

```
┌─────────────────────────────────────┐
│         Application Layer           │
│    (User Scripts, Experiments)      │
├─────────────────────────────────────┤
│         Model Builder Layer         │
│   (OntologyDrivenModelBuilder)      │
├─────────────────────────────────────┤
│         Control Layer               │
│     (ControlManager, Mappings)      │
├─────────────────────────────────────┤
│       Simulation Layer              │
│    (Primitives, SimPy Events)       │
├─────────────────────────────────────┤
│      Configuration Layer            │
│  (Ontologies, Manifests, Config)    │
└─────────────────────────────────────┘
```

## Component Details

### Configuration Layer

**Purpose**: Define system structure and parameters

**Components**:
- `twin_ontology.yaml`: Equipment type definitions (TBox)
- `manifests/*.yaml`: Equipment instances and relationships
- `config/twin_model.yaml`: Technical configuration
- `control_mappings.yaml`: Control parameter effects

### Simulation Layer

**Purpose**: Core discrete event simulation

**Key Classes**:

#### BasePrimitive
- Base class for all simulation entities
- Manages SimPy processes and events
- Provides configuration access methods

#### EquipmentPrimitive
- Implements processing logic
- Handles failure generation and repair
- Maintains internal queue (NO BUFFERS)
- Calculates OEE metrics

#### SourcePrimitive
- Generates materials based on production orders
- Manages product changeovers
- Implements SMED improvements

#### SinkPrimitive
- Consumes finished products
- Tracks production metrics
- Validates quality

#### SchedulerPrimitive
- Manages production order queue
- Orchestrates source primitives
- Tracks order completion

### Control Layer

**Purpose**: Dynamic behavior modification

**Control Flow**:
1. User sets actionable control (e.g., "speed_setpoint" = 85)
2. ControlManager looks up parameter mappings
3. Effects calculated based on mapping type (linear, exponential, etc.)
4. Parameters updated in equipment primitives
5. Behavior changes take effect immediately

**Mapping Types**:
- `linear`: Direct proportional effect
- `inverse_linear`: Inverse relationship
- `exponential`: Exponential scaling
- `step`: Discrete levels
- `logarithmic`: Log-scale effects

### Model Builder Layer

**Purpose**: Construct simulation from configuration

**Process**:
1. Load ontology and manifests
2. Create primitive instances
3. Establish connections
4. Initialize control system
5. Configure metrics collection
6. Return ready-to-run model

## Data Flow

### Configuration Loading
```
Ontology → Manifest → Runtime Config → Primitive Properties
```

### Material Flow
```
Scheduler → Source → Equipment Chain → Sink
         ↓
    Production
      Order
```

### Control Updates
```
User Input → Control Manager → Parameter Effects → Equipment Behavior
```

## Event Coordination

SimPy events coordinate primitive interactions:

### Processing Events
- `start_processing`: Equipment begins work
- `end_processing`: Part complete
- `material_available`: Queue has items

### Failure Events
- `failure_occurs`: Equipment breakdown
- `repair_start`: Maintenance begins
- `repair_complete`: Equipment restored

### Order Events
- `order_released`: Production starts
- `changeover_required`: Product switch
- `order_complete`: Target met

## State Management

Equipment maintains multiple state dimensions:

### Operational State
- `IDLE`: Waiting for material
- `PROCESSING`: Active production
- `FAILED`: Breakdown occurred
- `MAINTENANCE`: Scheduled maintenance
- `CHANGEOVER`: Product switch

### Control State
- Active control values
- Parameter effects
- Override flags

### Metrics State
- Parts produced/rejected
- Uptime/downtime tracking
- Failure counts by type

## Extension Points

The architecture supports extensions via:

### Custom Primitives
Inherit from `BasePrimitive` to add new equipment types

### Control Mappings
Define new control parameters and effects

### Failure Models
Implement custom failure distributions

### Metrics Collectors
Add specialized performance tracking

## Performance Considerations

### Memory Efficiency
- Lazy loading of configuration
- Event-driven updates only
- Minimal state tracking

### Simulation Speed
- Direct equipment connections (no buffer overhead)
- Efficient SimPy event scheduling
- Batch processing where possible

### Scalability
- Modular primitive design
- Hierarchical configuration
- Distributed control possible