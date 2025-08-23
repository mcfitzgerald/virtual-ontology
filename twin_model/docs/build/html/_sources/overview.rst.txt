Overview
========

The Virtual Ontology Twin Model is an advanced simulation framework that generates synthetic manufacturing data through ontology-driven discrete event simulation.

Core Concepts
-------------

Ontology-Driven Design
~~~~~~~~~~~~~~~~~~~~~~

The twin model uses ontological structures to define:

* **System Architecture**: How components connect and interact
* **Component Behavior**: Rules and parameters for each primitive
* **Data Semantics**: Meaning and relationships of generated data
* **Pattern Templates**: Expected patterns for discovery

This approach ensures:

* Consistent model structure across deployments
* Separation of structure from configuration
* Reusable component definitions
* Traceable data lineage

Simulation Primitives
~~~~~~~~~~~~~~~~~~~~~

The framework provides six core primitives:

1. **Equipment**: Production units with configurable processing times
2. **Buffer**: Storage units with capacity and flow control
3. **Source**: Item generators with arrival patterns
4. **Sink**: Product collectors with quality assessment
5. **Scheduler**: Order and maintenance coordinators
6. **Monitor**: KPI trackers and metric calculators

Each primitive:

* Extends :class:`twin_model.primitives.BasePrimitive`
* Has configurable parameters via :class:`twin_model.primitives.PrimitiveConfig`
* Generates events for pattern discovery
* Maintains internal state for analysis

Model Building Process
----------------------

Ontology Loading
~~~~~~~~~~~~~~~~

The :class:`twin_model.model_builder.OntologyDrivenModelBuilder` loads:

.. code-block:: yaml

   # twin_ontology.yaml
   twin_model:
     primitives:
       Equipment:
         properties:
           - processing_time
           - failure_rate
           - mttr
         relationships:
           - feeds_to: Buffer
   
     patterns:
       bottleneck:
         indicators:
           - high_buffer_occupancy
           - low_equipment_availability

Manifest Configuration
~~~~~~~~~~~~~~~~~~~~~~

Manifests provide concrete values:

.. code-block:: yaml

   # equipment_manifest.yaml
   equipment:
     Line1_Equipment1:
       type: Assembly
       processing_time: 5.0
       failure_rate: 0.01
       mttr: 30.0
       capacity: 100

Model Instantiation
~~~~~~~~~~~~~~~~~~~

The builder creates and wires components:

1. Parse ontology structure
2. Load manifest configurations
3. Instantiate primitives
4. Establish relationships
5. Configure monitors

Simulation Execution
--------------------

Event Processing
~~~~~~~~~~~~~~~~

SimPy manages discrete events:

* Item arrivals
* Processing starts/completions
* Equipment failures/repairs
* Buffer fills/empties
* Order completions

State Tracking
~~~~~~~~~~~~~~

The :class:`twin_model.state_manager.StateManager` maintains:

* Current primitive states
* Event history
* KPI metrics
* Pattern occurrences

Data Generation
~~~~~~~~~~~~~~~

Events are transduced to MES format:

.. code-block:: python

   # Raw event
   {
       "time": 100.5,
       "primitive": "Equipment1",
       "event": "processing_complete",
       "item": "Product_123"
   }
   
   # MES record
   {
       "Timestamp": "2024-01-01T10:00:30",
       "EquipmentID": "Equipment1",
       "MachineStatus": "Running",
       "GoodUnitsProduced": 1,
       "OEE_Score": 85.5
   }

Key Performance Indicators
--------------------------

OEE Calculation
~~~~~~~~~~~~~~~

Overall Equipment Effectiveness:

.. math::

   OEE = Availability × Performance × Quality

Where:

* **Availability** = (Planned Time - Downtime) / Planned Time
* **Performance** = Actual Output / Theoretical Output
* **Quality** = Good Units / Total Units

Monitoring Architecture
~~~~~~~~~~~~~~~~~~~~~~~

The :class:`twin_model.primitives.MonitorPrimitive` tracks:

* Real-time metrics
* Rolling averages
* Trend detection
* Threshold alerts

Pattern Discovery Support
-------------------------

Event Patterns
~~~~~~~~~~~~~~

The model generates patterns for:

* Equipment bottlenecks
* Quality degradation
* Maintenance clustering
* Production cascades

Observable Generation
~~~~~~~~~~~~~~~~~~~~~

Rich observables include:

* State transitions
* Queue lengths
* Processing durations
* Failure sequences
* Product flows

Pattern Templates
~~~~~~~~~~~~~~~~~

Ontology defines expected patterns:

.. code-block:: yaml

   patterns:
     cascade_failure:
       trigger: equipment_failure
       propagation: downstream_buffers
       impact: production_stoppage
       probability: 0.15

Integration Points
------------------

With Database Module
~~~~~~~~~~~~~~~~~~~~

* Store simulation results
* Load historical parameters
* Save discovered patterns
* Track experiments

With Configuration System
~~~~~~~~~~~~~~~~~~~~~~~~~

* Load runtime parameters
* Override manifest values
* Set simulation duration
* Configure logging

With Analysis Tools
~~~~~~~~~~~~~~~~~~~~

* Export to pandas DataFrames
* Generate matplotlib visualizations
* Produce statistics reports
* Create pattern datasets

Performance Optimization
------------------------

Efficient Simulation
~~~~~~~~~~~~~~~~~~~~

* Event-driven processing (no polling)
* Lazy evaluation of metrics
* Batch event processing
* Memory-efficient state tracking

Scalability Features
~~~~~~~~~~~~~~~~~~~~

* Parallel simulation runs
* Distributed primitive execution
* Incremental state updates
* Compressed event storage

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # twin_model.yaml
   simulation:
     max_events: 1000000
     batch_size: 1000
     state_checkpoint_interval: 100
     metric_update_frequency: 10

Error Handling
--------------

Failure Recovery
~~~~~~~~~~~~~~~~

* Graceful degradation on primitive failures
* State rollback capabilities
* Event replay from checkpoints
* Detailed error logging

Validation
~~~~~~~~~~

* Ontology schema validation
* Manifest consistency checks
* Parameter range verification
* Relationship integrity

Extensibility
-------------

Custom Primitives
~~~~~~~~~~~~~~~~~

Create new primitives by extending base:

.. code-block:: python

   from twin_model.primitives import BasePrimitive
   
   class CustomPrimitive(BasePrimitive):
       def process(self):
           # Custom logic
           pass

Pattern Definitions
~~~~~~~~~~~~~~~~~~~

Add custom patterns to ontology:

.. code-block:: yaml

   custom_patterns:
     my_pattern:
       detection: custom_algorithm
       parameters:
         threshold: 0.8

Transduction Rules
~~~~~~~~~~~~~~~~~~

Define custom MES mappings:

.. code-block:: python

   from twin_model.transduction import MESTransducer
   
   class CustomTransducer(MESTransducer):
       def transduce_event(self, event):
           # Custom transformation
           return mes_record