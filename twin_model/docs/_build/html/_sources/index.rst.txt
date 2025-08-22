.. Twin Model documentation master file

Twin Model Documentation
========================

A high-performance SimPy-based simulation framework for modeling manufacturing systems and digital twins.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   quickstart
   architecture
   performance
   api/index

Overview
--------

The Twin Model provides a flexible and extensible framework for building discrete-event simulations
of manufacturing systems with the following key features:

**Core Capabilities**

* **Ontology-Driven Architecture**: Structure defined by ontology, configuration by manifests
* **Modular Primitives**: Pre-built components for sources, equipment, buffers, and sinks
* **Rich Observables**: Comprehensive event emission for pattern discovery
* **Performance Optimized**: Handles 30-day simulations with <500MB memory

**Performance Features**

* **Memory Optimization**: Circular buffers and intelligent sampling
* **Event Processing**: Batching and incremental aggregation
* **Storage Optimization**: Write-through cache and memory-mapped files
* **State Management**: Checkpoint/resume capability
* **Adaptive Configuration**: 6 performance presets for different use cases

Key Components
--------------

**Primitives**
   Building blocks for simulation models:
   
   * ``EquipmentPrimitive``: Manufacturing equipment with failure modes
   * ``BufferPrimitive``: Material storage with configurable policies
   * ``SourcePrimitive``: Material generation with arrival patterns
   * ``SinkPrimitive``: Product collection and metrics
   * ``SchedulerPrimitive``: Production scheduling and optimization
   * ``MonitorPrimitive``: KPI tracking and aggregation

**Model Builder**
   Ontology-driven model construction that:
   
   * Interprets ontology structure
   * Instantiates and wires primitives
   * Applies manifest configurations
   * Creates production line structures

**Transduction Layer**
   Converts rich simulation events to MES-compatible format:
   
   * Extracts MES-visible events
   * Aggregates metrics by time buckets
   * Generates standard MES data structure

Performance Achievements
------------------------

After comprehensive optimization (6 phases):

* **Memory Usage**: 90%+ reduction (5.5MB → 0.5MB for standard simulations)
* **30-Day Simulations**: <500MB memory, <5 minutes completion
* **Event Processing**: 99% reduction through batching
* **Database Operations**: 20,000+ events/second insertion rate
* **Scalability**: Handles 50+ equipment primitives efficiently

Configuration Presets
---------------------

The system includes 6 optimized presets:

1. **DEVELOPMENT**: Full observables for debugging
2. **PRODUCTION**: Balanced performance and data retention
3. **FAST**: Maximum speed with aggressive sampling
4. **MEMORY_OPTIMIZED**: Minimal memory footprint
5. **LONG_RUNNING**: Optimized for 30+ day simulations
6. **REAL_TIME**: For real-time monitoring integration

Quick Example
-------------

.. code-block:: python

   from twin_model.model_builder import OntologyDrivenModelBuilder
   from twin_model.config import PerformanceConfig, ConfigPreset
   import simpy

   # Use optimized configuration
   config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
   
   # Build model from ontology
   builder = OntologyDrivenModelBuilder(
       ontology_path="ontology/twin_ontology.yaml",
       manifest_dir="manifests"
   )
   
   # Create and run simulation
   env = simpy.Environment()
   model = builder.build_model(env)
   env.run(until=7 * 24 * 60)  # 7 days
   
   # Get observables
   observables = builder.get_observables()

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`