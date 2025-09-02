Ontology-Driven Architecture Guide
===================================

Overview
--------

Twin Model uses an ontology-driven architecture that separates concerns into three distinct layers:

1. **Structure** - What types of equipment exist (Ontology)
2. **Instances** - Which specific equipment is deployed (Manifest)  
3. **Parameters** - How equipment is configured (Config)

This separation enables:

* Clear separation of concerns
* Reusable equipment definitions
* Easy parameter tuning without structural changes
* Version-controlled configuration management

The Three Configuration Files
-----------------------------

Ontology File (Structure)
~~~~~~~~~~~~~~~~~~~~~~~~~

Defines equipment types and their properties::

    equipment_types:
      FillingStation:
        base_class: "EquipmentFlow"
        properties:
          nominal_rate: "float"
          quality_rate: "float"
        capabilities:
          - "filling"
          - "quality_inspection"

Manifest File (Instances)
~~~~~~~~~~~~~~~~~~~~~~~~~

Declares specific equipment instances::

    equipment:
      LINE1-FIL:
        type: "FillingStation"
        line_id: "LINE1"
        position: 10
        equipment_model: "ACME_FILLER_5000"

Config File (Parameters)
~~~~~~~~~~~~~~~~~~~~~~~~

Contains tunable simulation parameters::

    equipment_parameters:
      LINE1-FIL:
        nominal_rate: 50.0
        quality_rate: 0.95
        mtbf: 15.0
        mttr: 8.0

Flow Primitives
--------------

The framework provides three base flow primitives:

SourceFlow
~~~~~~~~~~

Generates material into the system:

* Continuous or batch production
* Product order support
* Configurable generation rates

EquipmentFlow
~~~~~~~~~~~~~

Processes material through equipment:

* Input/output buffers
* Internal processing buffer
* Quality and performance factors
* Failure modeling (MTBF/MTTR)
* Micro-stops simulation

SinkFlow
~~~~~~~~

Collects material and calculates metrics:

* OEE calculation (Availability, Performance, Quality)
* Production window tracking
* Throughput monitoring

Building Models
--------------

The OntologyModelBuilder constructs simulation models from the three configuration files::

    from twin_model import OntologyModelBuilder
    
    builder = OntologyModelBuilder(
        ontology_path="ontology.yaml",
        manifest_path="manifest.yaml",
        config_path="config.yaml"
    )
    
    model = builder.build_model()
    builder.run_simulation(duration=60)

Monitoring and Metrics
---------------------

The FlowMonitor tracks real-time metrics:

* Material levels in buffers
* Flow rates between equipment
* Equipment states (running, blocked, starved)
* Quality metrics
* OEE components

Example Configuration
--------------------

See the ``docs/llm/examples/`` directory for complete example configurations:

* ``ontology.yaml`` - Equipment type definitions
* ``manifest.yaml`` - Production line topology
* ``config.yaml`` - Tunable parameters

Best Practices
-------------

1. **Ontology Design**: Define reusable equipment types with clear properties
2. **Manifest Structure**: Use consistent naming conventions for equipment IDs
3. **Parameter Tuning**: Start with baseline scenarios and create variants
4. **Monitoring**: Set appropriate sampling intervals for metrics collection
5. **Validation**: Use tests to verify model behavior matches expectations