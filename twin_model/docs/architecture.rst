Architecture
============

System Design
-------------

The Twin Model framework follows an ontology-driven architecture that separates structure from configuration.

Core Design Principles
^^^^^^^^^^^^^^^^^^^^^^

1. **Separation of Concerns**
   - Ontology defines structure (classes, relationships)
   - Manifests provide configuration (values, parameters)
   - Primitives implement behavior (simulation logic)

2. **Discovery-Based Learning**
   - No prescribed parameter-effect mappings
   - Rich observables for pattern discovery
   - Controllable parameters for experimentation

3. **Event-Driven Simulation**
   - All state changes emit observable events
   - Comprehensive event streams for analysis
   - Time-stamped events for reconstruction

Component Architecture
----------------------

Ontology Layer
^^^^^^^^^^^^^^

The ontology (`twin_ontology.yaml`) defines:

**TBox (Terminological Box)**
   - Class hierarchy (Equipment, Buffer, Source, etc.)
   - Properties for each class
   - Primitive mappings

**RBox (Relational Box)**
   - Relationships between entities (feeds_into, draws_from)
   - Cardinality constraints
   - Transitive properties

**Observables**
   - Measurable properties (equipment_state, buffer_level)
   - Aggregation methods (sum, avg, current)
   - Event types (state_change, unit_produced)

**Controllables**
   - Adjustable parameters (performance_factor, scrap_multiplier)
   - Bounds and defaults
   - No prescribed effects

Primitive Layer
^^^^^^^^^^^^^^^

Base primitives that implement simulation behavior:

.. code-block:: python

   class BasePrimitive:
       """Foundation for all simulation primitives"""
       - Event emission
       - State management
       - Observable collection
       - Performance optimization

   class EquipmentPrimitive(BasePrimitive):
       """Manufacturing equipment simulation"""
       - Production processing
       - Failure modeling
       - Quality control
       - Energy consumption

   class BufferPrimitive(BasePrimitive):
       """Material storage simulation"""
       - FIFO/LIFO policies
       - Capacity management
       - Dwell time tracking

Model Builder
^^^^^^^^^^^^^

The `OntologyDrivenModelBuilder` orchestrates model construction:

1. **Parse Ontology**: Load structure definitions
2. **Load Manifests**: Apply configuration values
3. **Instantiate Primitives**: Create simulation objects
4. **Wire Relationships**: Connect primitives
5. **Start Simulation**: Initialize all components

Performance Optimization
------------------------

Memory Management
^^^^^^^^^^^^^^^^^

**Circular Buffers**
   - Fixed-size buffers with automatic overflow
   - `collections.deque` with maxlen parameter
   - Prevents unbounded memory growth

**Sampling Strategies**
   - DETAILED: Full event capture
   - PRODUCTION: Balanced sampling
   - FAST: Aggressive filtering

Event Processing
^^^^^^^^^^^^^^^^

**Batching**
   - Group events by type and time window
   - Reduce processing overhead by 99%
   - Configurable batch sizes

**Incremental Aggregation**
   - Welford's algorithm for stable statistics
   - Running averages without storing all values
   - Memory-efficient metric calculation

Storage Optimization
^^^^^^^^^^^^^^^^^^^^

**Write-Through Cache**
   - Memory-mapped files for disk backing
   - Automatic flushing at thresholds
   - numpy arrays for efficient storage

**Database Integration**
   - Batch inserts (20,000+ events/second)
   - Async processing pipelines
   - Compressed storage formats

Data Flow Architecture
----------------------

.. code-block:: text

   ┌──────────────┐
   │   Ontology   │──────┐
   └──────────────┘      │
                         ▼
   ┌──────────────┐  ┌──────────────┐
   │  Manifests   │─▶│Model Builder │
   └──────────────┘  └──────────────┘
                         │
                         ▼
                   ┌──────────────┐
                   │  Primitives  │
                   └──────────────┘
                         │
                    ┌────┴────┐
                    ▼         ▼
            ┌──────────┐ ┌──────────┐
            │Observable│ │  SimPy   │
            │ Buffer   │ │  Events  │
            └──────────┘ └──────────┘
                    │         │
                    └────┬────┘
                         ▼
                 ┌──────────────┐
                 │ Transducer   │
                 └──────────────┘
                         │
                         ▼
                 ┌──────────────┐
                 │  MES Format  │
                 └──────────────┘
                         │
                         ▼
                 ┌──────────────┐
                 │   Database   │
                 └──────────────┘

Event System
------------

Event Types
^^^^^^^^^^^

**State Events**
   - state_change: Equipment state transitions
   - equipment_failure: Failure occurrences
   - maintenance_start/complete: Maintenance activities

**Production Events**
   - unit_produced: Successful production
   - unit_scrapped: Quality failures
   - batch_complete: Batch completions

**Flow Events**
   - material_consumed: Input consumption
   - buffer_level: Storage changes
   - equipment_blocked/starved: Flow constraints

Event Structure
^^^^^^^^^^^^^^^

.. code-block:: python

   {
       'timestamp': 1234.5,           # Simulation time
       'event_type': 'unit_produced',  # Event category
       'primitive_id': 'LINE1-FIL',    # Source primitive
       'primitive_type': 'Equipment',  # Primitive class
       'state': 'RUNNING',             # Current state
       'value': 1,                     # Event value
       'metadata': {                   # Additional data
           'product_id': 'SKU-1001',
           'order_id': 'ORD-1000',
           'quality': 0.98
       }
   }

Configuration System
--------------------

Three-Level Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Ontology Level**: Structure and relationships
2. **Manifest Level**: Instance-specific values
3. **Runtime Level**: Dynamic adjustments

Performance Presets
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   DEVELOPMENT = {
       'buffer_size': 10000,
       'sampling_rate': 1,
       'mode': DETAILED
   }
   
   PRODUCTION = {
       'buffer_size': 1000,
       'sampling_rate': 10,
       'mode': PRODUCTION
   }
   
   LONG_RUNNING = {
       'buffer_size': 500,
       'sampling_rate': 50,
       'mode': PRODUCTION
   }

Extensibility
-------------

Adding New Primitives
^^^^^^^^^^^^^^^^^^^^^

1. Inherit from `BasePrimitive`
2. Implement required methods (`run`, `start`)
3. Define observable events
4. Register in model builder

Custom Transducers
^^^^^^^^^^^^^^^^^^

1. Process observable stream
2. Extract domain-specific metrics
3. Format for target system
4. Implement aggregation logic

Integration Points
^^^^^^^^^^^^^^^^^^

- **Input**: Ontology, manifests, parameters
- **Processing**: SimPy events, observables
- **Output**: MES data, KPIs, patterns
- **Storage**: Database, files, streams