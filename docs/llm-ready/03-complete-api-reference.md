# Twin Model Documentation

Twin Model is an ontology-driven simulation framework for manufacturing
systems using SimPy containers.

## Key Features

- **Ontology-driven architecture** - Separates structure, instances, and
  parameters
- **Container-based flow simulation** - Continuous material flow with
  SimPy
- **Real-time monitoring** - Track OEE, throughput, and quality metrics
- **Flexible configuration** - YAML-based configuration system

Architecture Overview \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--

The system uses three configuration files:

1.  **Ontology** (`ontology.yaml`) - Defines equipment types and their
    properties
2.  **Manifest** (`manifest.yaml`) - Declares equipment instances and
    topology
3.  **Config** (`config.yaml`) - Contains tunable simulation parameters

::: {.toctree maxdepth="2" caption="Contents:"}
ontology_guide api/modules
:::

# Indices and tables

- `genindex`{.interpreted-text role="ref"}
- `modindex`{.interpreted-text role="ref"}
- `search`{.interpreted-text role="ref"}

# Ontology-Driven Architecture Guide

## Overview

Twin Model uses an ontology-driven architecture that separates concerns
into three distinct layers:

1.  **Structure** - What types of equipment exist (Ontology)
2.  **Instances** - Which specific equipment is deployed (Manifest)
3.  **Parameters** - How equipment is configured (Config)

This separation enables:

- Clear separation of concerns
- Reusable equipment definitions
- Easy parameter tuning without structural changes
- Version-controlled configuration management

## The Three Configuration Files

### Ontology File (Structure)

Defines equipment types and their properties:

    equipment_types:
      FillingStation:
        base_class: "EquipmentFlow"
        properties:
          nominal_rate: "float"
          quality_rate: "float"
        capabilities:
          - "filling"
          - "quality_inspection"

### Manifest File (Instances)

Declares specific equipment instances:

    equipment:
      LINE1-FIL:
        type: "FillingStation"
        line_id: "LINE1"
        position: 10
        equipment_model: "ACME_FILLER_5000"

### Config File (Parameters)

Contains tunable simulation parameters:

    equipment_parameters:
      LINE1-FIL:
        nominal_rate: 50.0
        quality_rate: 0.95
        mtbf: 15.0
        mttr: 8.0

Flow Primitives \-\-\-\-\-\-\-\-\-\-\-\-\--

The framework provides three base flow primitives:

### SourceFlow

Generates material into the system:

- Continuous or batch production
- Product order support
- Configurable generation rates

### EquipmentFlow

Processes material through equipment:

- Input/output buffers
- Internal processing buffer
- Quality and performance factors
- Failure modeling (MTBF/MTTR)
- Micro-stops simulation

### SinkFlow

Collects material and calculates metrics:

- OEE calculation (Availability, Performance, Quality)
- Production window tracking
- Throughput monitoring

Building Models \-\-\-\-\-\-\-\-\-\-\-\-\--

The OntologyModelBuilder constructs simulation models from the three
configuration files:

    from twin_model import OntologyModelBuilder

    builder = OntologyModelBuilder(
        ontology_path="ontology.yaml",
        manifest_path="manifest.yaml",
        config_path="config.yaml"
    )

    model = builder.build_model()
    builder.run_simulation(duration=60)

Monitoring and Metrics \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--

The FlowMonitor tracks real-time metrics:

- Material levels in buffers
- Flow rates between equipment
- Equipment states (running, blocked, starved)
- Quality metrics
- OEE components

Example Configuration \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--

See the `docs/llm/examples/` directory for complete example
configurations:

- `ontology.yaml` - Equipment type definitions
- `manifest.yaml` - Production line topology
- `config.yaml` - Tunable parameters

Best Practices \-\-\-\-\-\-\-\-\-\-\-\--

1.  **Ontology Design**: Define reusable equipment types with clear
    properties
2.  **Manifest Structure**: Use consistent naming conventions for
    equipment IDs
3.  **Parameter Tuning**: Start with baseline scenarios and create
    variants
4.  **Monitoring**: Set appropriate sampling intervals for metrics
    collection
5.  **Validation**: Use tests to verify model behavior matches
    expectations

# twin_model

::: {.toctree maxdepth="4"}
twin_model
:::

# twin_model package

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model
:::

## Subpackages

::: {.toctree maxdepth="4"}
twin_model.monitoring twin_model.primitives twin_model.tests
:::

## Submodules

::: {.toctree maxdepth="4"}
twin_model.ontology_model_builder
:::

# twin_model.monitoring package

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.monitoring
:::

## Submodules

::: {.toctree maxdepth="4"}
twin_model.monitoring.flow_monitor
:::

# twin_model.monitoring.flow_monitor module

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.monitoring.flow_monitor
:::

# twin_model.primitives package

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.primitives
:::

## Submodules

::: {.toctree maxdepth="4"}
twin_model.primitives.base_flow twin_model.primitives.equipment_flow
twin_model.primitives.sink_flow twin_model.primitives.source_flow
:::

# twin_model.primitives.base_flow module

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.primitives.base_flow
:::

# twin_model.primitives.equipment_flow module

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.primitives.equipment_flow
:::

# twin_model.primitives.sink_flow module

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.primitives.sink_flow
:::

# twin_model.primitives.source_flow module

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.primitives.source_flow
:::

# twin_model.tests package

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.tests
:::

## Subpackages

::: {.toctree maxdepth="4"}
twin_model.tests.integration twin_model.tests.unit
:::

# twin_model.tests.integration package

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.tests.integration
:::

## Submodules

::: {.toctree maxdepth="4"}
twin_model.tests.integration.test_oee_alignment
:::

# twin_model.tests.integration.test_oee_alignment module

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.tests.integration.test_oee_alignment
:::

# twin_model.tests.unit package

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.tests.unit
:::

## Submodules

::: {.toctree maxdepth="4"}
twin_model.tests.unit.test_container_flow
:::

# twin_model.tests.unit.test_container_flow module

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.tests.unit.test_container_flow
:::

# twin_model.ontology_model_builder module

::: {.automodule members="" undoc-members="" show-inheritance=""}
twin_model.ontology_model_builder
:::

# twin_model

::: autoapi-nested-parse
Twin Model - Container-based continuous flow simulation framework.
:::

## Submodules

::: {.toctree maxdepth="1"}
/autoapi/twin_model/monitoring/index
/autoapi/twin_model/ontology_model_builder/index
/autoapi/twin_model/primitives/index
:::

## Classes

::: autoapisummary
twin_model.OntologyModelBuilder twin_model.BaseFlowPrimitive
twin_model.EquipmentFlow twin_model.FailureParameters
twin_model.FlowCapacity twin_model.FlowMetrics twin_model.FlowState
twin_model.OEEMetrics twin_model.ProcessingParameters
twin_model.ProductionOrder twin_model.ProductionWindow
twin_model.SinkFlow twin_model.SourceFlow
:::

## Package Contents

> Builds simulation models from ontology, manifests, and config.
>
> > Build complete simulation model.
> >
> > returns
> > :   Dictionary containing primitives and metadata
>
> > Get current metrics from all equipment.
> >
> > returns
> > :   Dictionary of metrics by equipment

> Bases: `abc.ABC`{.interpreted-text role="py:obj"}
>
> Base class for all flow-based primitives.
>
> > Start the flow process.
>
> > Change current state and update metrics.
> >
> > param new_state
> > :   New flow state
>
> > Emit an observable event.
> >
> > param event_type
> > :   Type of event
> >
> > param data
> > :   Event data
>
> > Calculate equipment utilization.
> >
> > returns
> > :   Utilization as percentage (0-100)
>
> > Calculate equipment availability.
> >
> > returns
> > :   Availability as percentage (0-100)
>
> > Calculate equipment performance.
> >
> > returns
> > :   Performance as percentage (0-100), capped at 110%
>
> > Calculate equipment quality.
> >
> > returns
> > :   Quality as percentage (0-100)
>
> > Calculate Overall Equipment Effectiveness.
> >
> > returns
> > :   OEE as percentage (0-100)

> Bases:
> `twin_model.primitives.base_flow.BaseFlowPrimitive`{.interpreted-text
> role="py:obj"}
>
> Equipment with continuous flow processing.
>
> > Process material in continuous batches.
>
> > Simulate random failures.
>
> > Simulate micro-stops.
>
> > Perform product changeover.
> >
> > param new_product
> > :   New product identifier
> >
> > param changeover_time
> > :   Time required for changeover (minutes)

> Equipment failure parameters.

> Defines flow capacity constraints for equipment.

> Tracks flow metrics for analysis.
>
> > Update duration tracking for state changes.

> Bases: `enum.Enum`{.interpreted-text role="py:obj"}
>
> Equipment flow states.

> OEE metrics for a time period.
>
> > Convert to dictionary.

> Equipment processing parameters.

> Production order for material generation.

> Represents a production time window for metrics calculation.

> Bases:
> `twin_model.primitives.base_flow.BaseFlowPrimitive`{.interpreted-text
> role="py:obj"}
>
> Sink collecting finished products and calculating OEE.
>
> > Collect products and track metrics.
>
> > Track production windows for OEE calculation.
>
> > Calculate OEE components for time window.
> >
> > param window_minutes
> > :   Time window in minutes
> >
> > returns
> > :   Tuple of (OEE, Availability, Performance, Quality) as
> >     percentages
>
> > Get production summary statistics.
> >
> > returns
> > :   Dictionary with production summary
>
> > Set current product being collected.
> >
> > param product_id
> > :   Product identifier

> Bases:
> `twin_model.primitives.base_flow.BaseFlowPrimitive`{.interpreted-text
> role="py:obj"}
>
> Source generating continuous material flow.
>
> > Generate material based on orders or continuously.
>
> > Add a production order to the queue.
> >
> > param order
> > :   Production order to add
>
> > Cancel a production order.
> >
> > param order_id
> > :   ID of order to cancel
> >
> > returns
> > :   True if order was cancelled, False if not found
>
> > Get current queue status.
> >
> > returns
> > :   Dictionary with queue status information

# twin_model.monitoring.flow_monitor

::: autoapi-nested-parse
Flow monitor for real-time monitoring and bottleneck detection.

This module provides the FlowMonitor class that monitors production flow
in real-time and identifies bottlenecks and performance issues.
:::

## Attributes

::: autoapisummary
twin_model.monitoring.flow_monitor.logger
:::

## Classes

::: autoapisummary
twin_model.monitoring.flow_monitor.FlowSnapshot
twin_model.monitoring.flow_monitor.BottleneckInfo
twin_model.monitoring.flow_monitor.FlowMonitor
:::

## Module Contents

> Snapshot of flow metrics at a point in time.

> Information about a detected bottleneck.

> Monitors flow and detects bottlenecks in real-time.
>
> > Register primitives to monitor.
> >
> > param primitives
> > :   Dictionary of primitive instances
> >
> > param topology
> > :   Connection topology (optional)
>
> > Start monitoring process.
>
> > Get current monitoring status.
> >
> > returns
> > :   Dictionary with current status information
>
> > Get history of detected bottlenecks.
> >
> > returns
> > :   List of bottleneck records

# twin_model.monitoring

::: autoapi-nested-parse
Monitoring module for real-time flow analysis and bottleneck detection.
:::

## Submodules

::: {.toctree maxdepth="1"}
/autoapi/twin_model/monitoring/flow_monitor/index
:::

## Classes

::: autoapisummary
twin_model.monitoring.BottleneckInfo twin_model.monitoring.FlowMonitor
twin_model.monitoring.FlowSnapshot
:::

## Package Contents

> Information about a detected bottleneck.

> Monitors flow and detects bottlenecks in real-time.
>
> > Register primitives to monitor.
> >
> > param primitives
> > :   Dictionary of primitive instances
> >
> > param topology
> > :   Connection topology (optional)
>
> > Start monitoring process.
>
> > Get current monitoring status.
> >
> > returns
> > :   Dictionary with current status information
>
> > Get history of detected bottlenecks.
> >
> > returns
> > :   List of bottleneck records

> Snapshot of flow metrics at a point in time.

# twin_model.ontology_model_builder

::: autoapi-nested-parse
Ontology-driven model builder for twin simulation.

This module builds simulation models using: - Ontology for structure and
validation - Manifests for equipment instances - Config for tunable
parameters
:::

## Attributes

::: autoapisummary
twin_model.ontology_model_builder.logger
:::

## Classes

::: autoapisummary
twin_model.ontology_model_builder.OntologyModelBuilder
:::

## Module Contents

> Builds simulation models from ontology, manifests, and config.
>
> > Build complete simulation model.
> >
> > returns
> > :   Dictionary containing primitives and metadata
>
> > Get current metrics from all equipment.
> >
> > returns
> > :   Dictionary of metrics by equipment

# twin_model.primitives.base_flow

::: autoapi-nested-parse
Base flow primitive for container-based continuous flow simulation.

This module provides the foundation for all flow-based simulation
primitives using SimPy Containers exclusively for continuous flow
modeling.
:::

## Classes

::: autoapisummary
twin_model.primitives.base_flow.FlowCapacity
twin_model.primitives.base_flow.FlowState
twin_model.primitives.base_flow.FlowMetrics
twin_model.primitives.base_flow.BaseFlowPrimitive
:::

## Module Contents

> Defines flow capacity constraints for equipment.

> Bases: `enum.Enum`{.interpreted-text role="py:obj"}
>
> Equipment flow states.

> Tracks flow metrics for analysis.
>
> > Update duration tracking for state changes.

> Bases: `abc.ABC`{.interpreted-text role="py:obj"}
>
> Base class for all flow-based primitives.
>
> > Start the flow process.
>
> > Change current state and update metrics.
> >
> > param new_state
> > :   New flow state
>
> > Emit an observable event.
> >
> > param event_type
> > :   Type of event
> >
> > param data
> > :   Event data
>
> > Calculate equipment utilization.
> >
> > returns
> > :   Utilization as percentage (0-100)
>
> > Calculate equipment availability.
> >
> > returns
> > :   Availability as percentage (0-100)
>
> > Calculate equipment performance.
> >
> > returns
> > :   Performance as percentage (0-100), capped at 110%
>
> > Calculate equipment quality.
> >
> > returns
> > :   Quality as percentage (0-100)
>
> > Calculate Overall Equipment Effectiveness.
> >
> > returns
> > :   OEE as percentage (0-100)

# twin_model.primitives.equipment_flow

::: autoapi-nested-parse
Equipment flow primitive for continuous processing simulation.

This module implements equipment with continuous flow processing using
SimPy Containers, modeling realistic production constraints and
failures.
:::

## Classes

::: autoapisummary
twin_model.primitives.equipment_flow.ProcessingParameters
twin_model.primitives.equipment_flow.FailureParameters
twin_model.primitives.equipment_flow.EquipmentFlow
:::

## Module Contents

> Equipment processing parameters.

> Equipment failure parameters.

> Bases:
> `twin_model.primitives.base_flow.BaseFlowPrimitive`{.interpreted-text
> role="py:obj"}
>
> Equipment with continuous flow processing.
>
> > Process material in continuous batches.
>
> > Simulate random failures.
>
> > Simulate micro-stops.
>
> > Perform product changeover.
> >
> > param new_product
> > :   New product identifier
> >
> > param changeover_time
> > :   Time required for changeover (minutes)

# twin_model.primitives

::: autoapi-nested-parse
Flow primitives for container-based continuous flow simulation.
:::

## Submodules

::: {.toctree maxdepth="1"}
/autoapi/twin_model/primitives/base_flow/index
/autoapi/twin_model/primitives/equipment_flow/index
/autoapi/twin_model/primitives/sink_flow/index
/autoapi/twin_model/primitives/source_flow/index
:::

## Classes

::: autoapisummary
twin_model.primitives.BaseFlowPrimitive
twin_model.primitives.FlowCapacity twin_model.primitives.FlowMetrics
twin_model.primitives.FlowState twin_model.primitives.EquipmentFlow
twin_model.primitives.FailureParameters
twin_model.primitives.ProcessingParameters
twin_model.primitives.OEEMetrics twin_model.primitives.ProductionWindow
twin_model.primitives.SinkFlow twin_model.primitives.ProductionOrder
twin_model.primitives.SourceFlow
:::

## Package Contents

> Bases: `abc.ABC`{.interpreted-text role="py:obj"}
>
> Base class for all flow-based primitives.
>
> > Start the flow process.
>
> > Change current state and update metrics.
> >
> > param new_state
> > :   New flow state
>
> > Emit an observable event.
> >
> > param event_type
> > :   Type of event
> >
> > param data
> > :   Event data
>
> > Calculate equipment utilization.
> >
> > returns
> > :   Utilization as percentage (0-100)
>
> > Calculate equipment availability.
> >
> > returns
> > :   Availability as percentage (0-100)
>
> > Calculate equipment performance.
> >
> > returns
> > :   Performance as percentage (0-100), capped at 110%
>
> > Calculate equipment quality.
> >
> > returns
> > :   Quality as percentage (0-100)
>
> > Calculate Overall Equipment Effectiveness.
> >
> > returns
> > :   OEE as percentage (0-100)

> Defines flow capacity constraints for equipment.

> Tracks flow metrics for analysis.
>
> > Update duration tracking for state changes.

> Bases: `enum.Enum`{.interpreted-text role="py:obj"}
>
> Equipment flow states.

> Bases:
> `twin_model.primitives.base_flow.BaseFlowPrimitive`{.interpreted-text
> role="py:obj"}
>
> Equipment with continuous flow processing.
>
> > Process material in continuous batches.
>
> > Simulate random failures.
>
> > Simulate micro-stops.
>
> > Perform product changeover.
> >
> > param new_product
> > :   New product identifier
> >
> > param changeover_time
> > :   Time required for changeover (minutes)

> Equipment failure parameters.

> Equipment processing parameters.

> OEE metrics for a time period.
>
> > Convert to dictionary.

> Represents a production time window for metrics calculation.

> Bases:
> `twin_model.primitives.base_flow.BaseFlowPrimitive`{.interpreted-text
> role="py:obj"}
>
> Sink collecting finished products and calculating OEE.
>
> > Collect products and track metrics.
>
> > Track production windows for OEE calculation.
>
> > Calculate OEE components for time window.
> >
> > param window_minutes
> > :   Time window in minutes
> >
> > returns
> > :   Tuple of (OEE, Availability, Performance, Quality) as
> >     percentages
>
> > Get production summary statistics.
> >
> > returns
> > :   Dictionary with production summary
>
> > Set current product being collected.
> >
> > param product_id
> > :   Product identifier

> Production order for material generation.

> Bases:
> `twin_model.primitives.base_flow.BaseFlowPrimitive`{.interpreted-text
> role="py:obj"}
>
> Source generating continuous material flow.
>
> > Generate material based on orders or continuously.
>
> > Add a production order to the queue.
> >
> > param order
> > :   Production order to add
>
> > Cancel a production order.
> >
> > param order_id
> > :   ID of order to cancel
> >
> > returns
> > :   True if order was cancelled, False if not found
>
> > Get current queue status.
> >
> > returns
> > :   Dictionary with queue status information

# twin_model.primitives.sink_flow

::: autoapi-nested-parse
Sink flow primitive for collecting finished products and calculating
OEE.

This module implements sinks that collect finished products and provide
comprehensive OEE (Overall Equipment Effectiveness) calculations.
:::

## Classes

::: autoapisummary
twin_model.primitives.sink_flow.ProductionWindow
twin_model.primitives.sink_flow.OEEMetrics
twin_model.primitives.sink_flow.SinkFlow
:::

## Module Contents

> Represents a production time window for metrics calculation.

> OEE metrics for a time period.
>
> > Convert to dictionary.

> Bases:
> `twin_model.primitives.base_flow.BaseFlowPrimitive`{.interpreted-text
> role="py:obj"}
>
> Sink collecting finished products and calculating OEE.
>
> > Collect products and track metrics.
>
> > Track production windows for OEE calculation.
>
> > Calculate OEE components for time window.
> >
> > param window_minutes
> > :   Time window in minutes
> >
> > returns
> > :   Tuple of (OEE, Availability, Performance, Quality) as
> >     percentages
>
> > Get production summary statistics.
> >
> > returns
> > :   Dictionary with production summary
>
> > Set current product being collected.
> >
> > param product_id
> > :   Product identifier

# twin_model.primitives.source_flow

::: autoapi-nested-parse
Source flow primitive for continuous material generation.

This module implements sources that generate continuous material flow
based on production orders or continuous generation patterns.
:::

## Classes

::: autoapisummary
twin_model.primitives.source_flow.ProductionOrder
twin_model.primitives.source_flow.SourceFlow
:::

## Module Contents

> Production order for material generation.

> Bases:
> `twin_model.primitives.base_flow.BaseFlowPrimitive`{.interpreted-text
> role="py:obj"}
>
> Source generating continuous material flow.
>
> > Generate material based on orders or continuously.
>
> > Add a production order to the queue.
> >
> > param order
> > :   Production order to add
>
> > Cancel a production order.
> >
> > param order_id
> > :   ID of order to cancel
> >
> > returns
> > :   True if order was cancelled, False if not found
>
> > Get current queue status.
> >
> > returns
> > :   Dictionary with queue status information
