# SimPy-Based Manufacturing Generator Redesign

## Executive Summary

The current manufacturing data generator treats equipment as independent random event generators rather than a connected production line with material flow. This results in minimal parameter sensitivity and unrealistic system behavior. We are proceeding with rebuilding the generator (called `twin_model`) using SimPy discrete event simulation to model actual material flow, buffers, and equipment interactions.

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
- LINE1: configuration 1 (products, faults, etc)
- LINE2: configuration 2 (products, faults, etc)
- LINE3: configuration 3 (products, faults, etc)

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