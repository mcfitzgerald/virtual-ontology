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
/autoapi/twin_model/integration/index
/autoapi/twin_model/monitoring/index
/autoapi/twin_model/ontology_model_builder/index
/autoapi/twin_model/primitives/index
/autoapi/twin_model/scheduling/index
/autoapi/twin_model/transduction/index
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
> >
> > param downtime_reason
> > :   Optional reason for downtime (for FAILED/MAINTENANCE states)
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

# twin_model.integration

::: autoapi-nested-parse
Integration module for combining simulation components.
:::

## Submodules

::: {.toctree maxdepth="1"}
/autoapi/twin_model/integration/mes_integration/index
:::

## Classes

::: autoapisummary
twin_model.integration.MESSimulationCoordinator
:::

## Functions

::: autoapisummary
twin_model.integration.setup_mes_simulation
:::

## Package Contents

> Coordinates MES simulation components.
>
> This coordinator manages the interaction between: - Production
> scheduler (manages orders) - MES data collector (captures data) -
> Equipment primitives (execute production)
>
> > Main coordination process.

> Set up complete MES simulation.
>
> param env
> :   SimPy environment
>
> param model
> :   Model dictionary from OntologyModelBuilder
>
> param simulation_duration
> :   Total simulation duration in minutes
>
> param random_seed
> :   Random seed for reproducibility
>
> returns
> :   Dictionary with scheduler, collector, and coordinator

# twin_model.integration.mes_integration

::: autoapi-nested-parse
Integration module for MES simulation components.

This module provides integration between the production scheduler, MES
data collector, and simulation primitives.
:::

## Attributes

::: autoapisummary
twin_model.integration.mes_integration.logger
:::

## Classes

::: autoapisummary
twin_model.integration.mes_integration.MESSimulationCoordinator
:::

## Functions

::: autoapisummary
twin_model.integration.mes_integration.setup_mes_simulation
:::

## Module Contents

> Coordinates MES simulation components.
>
> This coordinator manages the interaction between: - Production
> scheduler (manages orders) - MES data collector (captures data) -
> Equipment primitives (execute production)
>
> > Main coordination process.

> Set up complete MES simulation.
>
> param env
> :   SimPy environment
>
> param model
> :   Model dictionary from OntologyModelBuilder
>
> param simulation_duration
> :   Total simulation duration in minutes
>
> param random_seed
> :   Random seed for reproducibility
>
> returns
> :   Dictionary with scheduler, collector, and coordinator

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
> >
> > param downtime_reason
> > :   Optional reason for downtime (for FAILED/MAINTENANCE states)
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
> >
> > param downtime_reason
> > :   Optional reason for downtime (for FAILED/MAINTENANCE states)
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

# twin_model.scheduling.base_scheduler

::: autoapi-nested-parse
Base scheduler abstract class for production scheduling.

This module provides the abstract interface for production schedulers,
enabling different scheduling algorithms to be plugged in.
:::

## Attributes

::: autoapisummary
twin_model.scheduling.base_scheduler.logger
:::

## Classes

::: autoapisummary
twin_model.scheduling.base_scheduler.OrderStatus
twin_model.scheduling.base_scheduler.SchedulerConfig
twin_model.scheduling.base_scheduler.SchedulingConstraints
twin_model.scheduling.base_scheduler.BaseScheduler
:::

## Module Contents

> Bases: `enum.Enum`{.interpreted-text role="py:obj"}
>
> Production order status.

> Configuration for scheduler behavior.

> Constraints for scheduling decisions.

> Bases: `abc.ABC`{.interpreted-text role="py:obj"}
>
> Abstract base class for production schedulers.
>
> This class defines the interface that all scheduling algorithms must
> implement, allowing for different scheduling strategies to be used
> interchangeably.
>
> > Validate that a schedule meets all constraints.
> >
> > param schedule
> > :   Schedule to validate
> >
> > returns
> > :   Tuple of (is_valid, list_of_violations)
>
> > Calculate metrics for a schedule.
> >
> > param schedule
> > :   Schedule to analyze
> >
> > returns
> > :   Dictionary of metrics
>
> > Export schedule in specified format.
> >
> > param schedule
> > :   Schedule to export
> >
> > param format
> > :   Export format (\'dict\', \'json\', \'gantt\')
> >
> > returns
> > :   Schedule in requested format

# twin_model.scheduling.campaign_optimizer

::: autoapi-nested-parse
Campaign-based scheduling optimizer.

Groups orders by product to minimize changeovers and maximize campaign
efficiency.
:::

## Attributes

::: autoapisummary
twin_model.scheduling.campaign_optimizer.logger
:::

## Classes

::: autoapisummary
twin_model.scheduling.campaign_optimizer.Campaign
twin_model.scheduling.campaign_optimizer.CampaignOptimizer
:::

## Module Contents

> Represents a production campaign for a single product.
>
> > Add order to campaign.

> Bases:
> `twin_model.scheduling.base_scheduler.BaseScheduler`{.interpreted-text
> role="py:obj"}
>
> Campaign-based scheduling optimizer.
>
> Groups orders by product to create campaigns that minimize changeovers
> and maximize efficiency.
>
> > Generate schedule using campaign optimization.
> >
> > param orders
> > :   List of production orders to schedule
> >
> > param lines
> > :   Available production lines
> >
> > param horizon_hours
> > :   Planning horizon in hours
> >
> > param start_time
> > :   Start time for scheduling (simulation minutes)
> >
> > returns
> > :   Schedule by line
>
> > Optimize existing schedule using campaign resequencing.
> >
> > param current_schedule
> > :   Current schedule to optimize
> >
> > param cost_calculator
> > :   Cost calculator for evaluation
> >
> > returns
> > :   Optimized schedule
>
> > Reschedule after disruption using campaign regrouping.
> >
> > param disruption_time
> > :   When disruption occurred (simulation time)
> >
> > param disruption_type
> > :   Type of disruption
> >
> > param affected_resources
> > :   Affected lines/resources
> >
> > param current_schedule
> > :   Current schedule
> >
> > returns
> > :   Updated schedule
>
> > Get scheduler performance metrics.
> >
> > returns
> > :   Metrics dictionary

# twin_model.scheduling.config_loader

::: autoapi-nested-parse
Configuration loader for scheduler settings.

This module provides utilities to load scheduler configuration from YAML
files, making the scheduler fully configurable.
:::

## Attributes

::: autoapisummary
twin_model.scheduling.config_loader.logger
:::

## Functions

::: autoapisummary
twin_model.scheduling.config_loader.load_scheduler_config
twin_model.scheduling.config_loader.load_scheduling_constraints
twin_model.scheduling.config_loader.load_complete_scheduler_config
twin_model.scheduling.config_loader.create_scheduler_from_config
twin_model.scheduling.config_loader.validate_schedule_config
:::

## Module Contents

> Load scheduler configuration from YAML file.
>
> param config_path
> :   Path to YAML configuration file
>
> returns
> :   SchedulerConfig object
>
> raises FileNotFoundError
> :   If config file doesn\'t exist
>
> raises ValueError
> :   If config file is invalid

> Load scheduling constraints from YAML file.
>
> param config_path
> :   Path to YAML configuration file
>
> returns
> :   SchedulingConstraints object
>
> raises FileNotFoundError
> :   If config file doesn\'t exist
>
> raises ValueError
> :   If config file is invalid

> Load both scheduler config and constraints from a single file.
>
> param config_path
> :   Path to YAML configuration file
>
> returns
> :   Tuple of (SchedulerConfig, SchedulingConstraints)
>
> raises FileNotFoundError
> :   If config file doesn\'t exist
>
> raises ValueError
> :   If config file is invalid

> Create a ProductionScheduler from configuration files.
>
> param env
> :   SimPy environment
>
> param config_path
> :   Path to scheduler configuration YAML
>
> param catalog_path
> :   Path to product catalog YAML
>
> param random_seed
> :   Random seed for reproducibility
>
> returns
> :   Configured ProductionScheduler instance

> Validate a scheduler configuration file.
>
> param config_path
> :   Path to YAML configuration file
>
> returns
> :   List of validation warnings/errors (empty if valid)

# twin_model.scheduling.cost_calculator

::: autoapi-nested-parse
Production cost calculator for optimization.

This module provides comprehensive cost calculation for production
scheduling optimization, including production, changeover, inventory,
and quality costs.
:::

## Attributes

::: autoapisummary
twin_model.scheduling.cost_calculator.logger
:::

## Classes

::: autoapisummary
twin_model.scheduling.cost_calculator.CostBreakdown
twin_model.scheduling.cost_calculator.ProductionCostCalculator
:::

## Module Contents

> Detailed cost breakdown for analysis.
>
> > Calculate total cost from components.
>
> > Convert to dictionary.

> Calculates comprehensive production costs for optimization.
>
> > Calculate total cost for a production order.
> >
> > param order
> > :   Production order to cost
> >
> > param line_id
> > :   Production line ID
> >
> > param include_changeover
> > :   Whether to include changeover costs
> >
> > param previous_product
> > :   Previous product for changeover calculation
> >
> > returns
> > :   Detailed cost breakdown
>
> > Calculate total cost for entire schedule.
> >
> > param schedule
> > :   Production schedule by line
> >
> > returns
> > :   Cost summary with breakdown
>
> > Compare costs between two schedules.
> >
> > param schedule1
> > :   First schedule
> >
> > param schedule2
> > :   Second schedule
> >
> > param names
> > :   Names for the schedules
> >
> > returns
> > :   Comparison results
>
> > Identify main cost drivers in schedule.
> >
> > param schedule
> > :   Production schedule
> >
> > returns
> > :   List of cost drivers sorted by impact

# twin_model.scheduling

::: autoapi-nested-parse
Production scheduling module.
:::

## Submodules

::: {.toctree maxdepth="1"}
/autoapi/twin_model/scheduling/base_scheduler/index
/autoapi/twin_model/scheduling/campaign_optimizer/index
/autoapi/twin_model/scheduling/config_loader/index
/autoapi/twin_model/scheduling/cost_calculator/index
/autoapi/twin_model/scheduling/product_manifest/index
/autoapi/twin_model/scheduling/production_scheduler/index
/autoapi/twin_model/scheduling/scheduler_integration/index
/autoapi/twin_model/scheduling/sequential_scheduler/index
:::

## Classes

::: autoapisummary
twin_model.scheduling.BaseScheduler
twin_model.scheduling.SchedulerConfig
twin_model.scheduling.SchedulingConstraints
twin_model.scheduling.OrderStatus
twin_model.scheduling.ProductionScheduler
twin_model.scheduling.ProductionOrder twin_model.scheduling.ProductMix
:::

## Package Contents

> Bases: `abc.ABC`{.interpreted-text role="py:obj"}
>
> Abstract base class for production schedulers.
>
> This class defines the interface that all scheduling algorithms must
> implement, allowing for different scheduling strategies to be used
> interchangeably.
>
> > Validate that a schedule meets all constraints.
> >
> > param schedule
> > :   Schedule to validate
> >
> > returns
> > :   Tuple of (is_valid, list_of_violations)
>
> > Calculate metrics for a schedule.
> >
> > param schedule
> > :   Schedule to analyze
> >
> > returns
> > :   Dictionary of metrics
>
> > Export schedule in specified format.
> >
> > param schedule
> > :   Schedule to export
> >
> > param format
> > :   Export format (\'dict\', \'json\', \'gantt\')
> >
> > returns
> > :   Schedule in requested format

> Configuration for scheduler behavior.

> Constraints for scheduling decisions.

> Bases: `enum.Enum`{.interpreted-text role="py:obj"}
>
> Production order status.

> Bases:
> `twin_model.scheduling.base_scheduler.BaseScheduler`{.interpreted-text
> role="py:obj"}
>
> Concrete implementation of scheduler for MES simulation.
>
> This scheduler creates and manages production orders to match the
> patterns observed in the target MES data, implementing a simple
> sequential scheduling algorithm with configurable product mixes and
> changeover times.
>
> > Generate a production order for a line.
> >
> > param line_id
> > :   Production line ID
> >
> > param scheduled_start
> > :   Start time in simulation minutes
> >
> > param duration_hours
> > :   Order duration in hours
> >
> > returns
> > :   Generated production order
>
> > Generate initial production schedule for entire simulation.
> >
> > param simulation_duration
> > :   Total simulation duration in minutes
>
> > Get changeover time between products.
> >
> > param from_product
> > :   Current product ID
> >
> > param to_product
> > :   Next product ID
> >
> > returns
> > :   Changeover time in minutes
>
> > Get current production order for a line.
> >
> > param line_id
> > :   Production line ID
> >
> > returns
> > :   Current order or None if no active order
>
> > Update production progress for an order.
> >
> > param order_id
> > :   Order ID
> >
> > param good_units
> > :   Good units produced
> >
> > param scrap_units
> > :   Scrap units produced
>
> > Schedule a changeover process for a line.
> >
> > param line_id
> > :   Production line ID
> >
> > Yields
> > :   SimPy timeout for changeover duration
>
> > Get scheduler statistics.
> >
> > returns
> > :   Dictionary of statistics
>
> > Generate production schedule for given lines and products.
> >
> > This implementation uses a simple sequential scheduling algorithm
> > with product mix based on historical patterns.
> >
> > param lines
> > :   List of production line IDs
> >
> > param products
> > :   List of product IDs to schedule
> >
> > param duration
> > :   Planning horizon in minutes
> >
> > param \*\*kwargs
> > :   Additional parameters (e.g., \'use_product_mix\')
> >
> > returns
> > :   Dictionary mapping line IDs to ordered lists of production
> >     orders
>
> > Optimize an existing schedule based on given objective.
> >
> > This is a simple implementation that reorders products to minimize
> > changeover time within each line.
> >
> > param current_schedule
> > :   Current schedule to optimize
> >
> > param objective
> > :   Optimization objective
> >
> > param \*\*kwargs
> > :   Additional optimization parameters
> >
> > returns
> > :   Optimized schedule
>
> > Reschedule production after a disruption.
> >
> > This implementation delays affected orders and reschedules remaining
> > production.
> >
> > param disruption_time
> > :   Time when disruption occurred
> >
> > param disruption_type
> > :   Type of disruption
> >
> > param affected_resources
> > :   List of affected line/equipment IDs
> >
> > param \*\*kwargs
> > :   Additional disruption details
> >
> > returns
> > :   Updated schedule

> Production order with scheduling information.

> Product mix configuration for a production line.

# twin_model.scheduling.product_manifest

::: autoapi-nested-parse
Product manifest loader and manager.

This module provides comprehensive product information management for
production scheduling and cost optimization.
:::

## Attributes

::: autoapisummary
twin_model.scheduling.product_manifest.logger
:::

## Classes

::: autoapisummary
twin_model.scheduling.product_manifest.PhysicalAttributes
twin_model.scheduling.product_manifest.ProductionAttributes
twin_model.scheduling.product_manifest.EconomicAttributes
twin_model.scheduling.product_manifest.ChangeoverAttributes
twin_model.scheduling.product_manifest.InventoryAttributes
twin_model.scheduling.product_manifest.QualityAttributes
twin_model.scheduling.product_manifest.ProductConstraints
twin_model.scheduling.product_manifest.Product
twin_model.scheduling.product_manifest.ProductManifest
:::

## Module Contents

> Physical characteristics of a product.

> Production characteristics and rates.

> Economic and cost attributes.

> Changeover requirements and costs.

> Inventory management parameters.

> Quality specifications and defect costs.

> Production constraints and requirements.

> Complete product specification.

> Manages product specifications and relationships.
>
> > Load product manifest from YAML file.
> >
> > param filepath
> > :   Path to YAML file
>
> > Get product by ID.
> >
> > param product_id
> > :   Product identifier
> >
> > returns
> > :   Product object or None if not found
>
> > Get changeover time between products.
> >
> > param from_product_id
> > :   Current product
> >
> > param to_product_id
> > :   Next product
> >
> > returns
> > :   Changeover time in minutes
>
> > Get changeover cost between products.
> >
> > param from_product_id
> > :   Current product
> >
> > param to_product_id
> > :   Next product
> >
> > returns
> > :   Changeover cost in currency units
>
> > Get efficiency of product on specific line.
> >
> > param product_id
> > :   Product identifier
> >
> > param line_id
> > :   Line identifier (e.g., \"Line1\", \"1\", etc.)
> >
> > returns
> > :   Efficiency factor (0-1) or None if not capable
>
> > Check if product can be produced on line.
> >
> > param product_id
> > :   Product identifier
> >
> > param line_id
> > :   Line identifier
> >
> > returns
> > :   True if capable, False otherwise
>
> > Get preferred production line for product.
> >
> > param product_id
> > :   Product identifier
> >
> > returns
> > :   Preferred line ID or None
>
> > Get all products in a family.
> >
> > param family
> > :   Family name
> >
> > returns
> > :   List of product IDs in the family
>
> > Calculate total cost of a production campaign.
> >
> > param product_id
> > :   Product to produce
> >
> > param volume
> > :   Production volume in units
> >
> > param duration_hours
> > :   Campaign duration in hours
> >
> > param line_id
> > :   Production line
> >
> > returns
> > :   Dictionary of cost components
>
> > Get summary of loaded products.
> >
> > returns
> > :   Summary dictionary

# twin_model.scheduling.production_scheduler

::: autoapi-nested-parse
Production order scheduling for MES simulation.

This module provides production order management and scheduling to match
the patterns observed in the target MES data.
:::

## Attributes

::: autoapisummary
twin_model.scheduling.production_scheduler.logger
:::

## Classes

::: autoapisummary
twin_model.scheduling.production_scheduler.ProductionOrder
twin_model.scheduling.production_scheduler.ProductMix
twin_model.scheduling.production_scheduler.ProductionScheduler
:::

## Module Contents

> Production order with scheduling information.

> Product mix configuration for a production line.

> Bases:
> `twin_model.scheduling.base_scheduler.BaseScheduler`{.interpreted-text
> role="py:obj"}
>
> Concrete implementation of scheduler for MES simulation.
>
> This scheduler creates and manages production orders to match the
> patterns observed in the target MES data, implementing a simple
> sequential scheduling algorithm with configurable product mixes and
> changeover times.
>
> > Generate a production order for a line.
> >
> > param line_id
> > :   Production line ID
> >
> > param scheduled_start
> > :   Start time in simulation minutes
> >
> > param duration_hours
> > :   Order duration in hours
> >
> > returns
> > :   Generated production order
>
> > Generate initial production schedule for entire simulation.
> >
> > param simulation_duration
> > :   Total simulation duration in minutes
>
> > Get changeover time between products.
> >
> > param from_product
> > :   Current product ID
> >
> > param to_product
> > :   Next product ID
> >
> > returns
> > :   Changeover time in minutes
>
> > Get current production order for a line.
> >
> > param line_id
> > :   Production line ID
> >
> > returns
> > :   Current order or None if no active order
>
> > Update production progress for an order.
> >
> > param order_id
> > :   Order ID
> >
> > param good_units
> > :   Good units produced
> >
> > param scrap_units
> > :   Scrap units produced
>
> > Schedule a changeover process for a line.
> >
> > param line_id
> > :   Production line ID
> >
> > Yields
> > :   SimPy timeout for changeover duration
>
> > Get scheduler statistics.
> >
> > returns
> > :   Dictionary of statistics
>
> > Generate production schedule for given lines and products.
> >
> > This implementation uses a simple sequential scheduling algorithm
> > with product mix based on historical patterns.
> >
> > param lines
> > :   List of production line IDs
> >
> > param products
> > :   List of product IDs to schedule
> >
> > param duration
> > :   Planning horizon in minutes
> >
> > param \*\*kwargs
> > :   Additional parameters (e.g., \'use_product_mix\')
> >
> > returns
> > :   Dictionary mapping line IDs to ordered lists of production
> >     orders
>
> > Optimize an existing schedule based on given objective.
> >
> > This is a simple implementation that reorders products to minimize
> > changeover time within each line.
> >
> > param current_schedule
> > :   Current schedule to optimize
> >
> > param objective
> > :   Optimization objective
> >
> > param \*\*kwargs
> > :   Additional optimization parameters
> >
> > returns
> > :   Optimized schedule
>
> > Reschedule production after a disruption.
> >
> > This implementation delays affected orders and reschedules remaining
> > production.
> >
> > param disruption_time
> > :   Time when disruption occurred
> >
> > param disruption_type
> > :   Type of disruption
> >
> > param affected_resources
> > :   List of affected line/equipment IDs
> >
> > param \*\*kwargs
> > :   Additional disruption details
> >
> > returns
> > :   Updated schedule

# twin_model.scheduling.scheduler_integration

::: autoapi-nested-parse
Integration module for schedulers with SimPy simulation.

Connects scheduling algorithms to the simulation environment, managing
order dispatch and tracking.
:::

## Attributes

::: autoapisummary
twin_model.scheduling.scheduler_integration.logger
:::

## Classes

::: autoapisummary
twin_model.scheduling.scheduler_integration.SchedulerSimulationBridge
:::

## Module Contents

> Bridge between schedulers and SimPy simulation.
>
> Manages the interaction between scheduling algorithms and the
> simulation environment, handling order dispatch and tracking.
>
> > Register a source flow for a production line.
> >
> > param line_id
> > :   Line identifier
> >
> > param source
> > :   SourceFlow instance for the line
>
> > Generate random production orders.
> >
> > param num_orders
> > :   Number of orders to generate
> >
> > param products
> > :   List of product IDs (uses manifest if not provided)
> >
> > param horizon_hours
> > :   Planning horizon in hours
> >
> > returns
> > :   List of generated orders
>
> > Schedule production orders.
> >
> > param orders
> > :   Orders to schedule (uses pending orders if not provided)
> >
> > param horizon_hours
> > :   Planning horizon
> >
> > param optimize
> > :   Whether to optimize the schedule
> >
> > returns
> > :   Schedule by line
>
> > Dispatch scheduled orders to production lines.
> >
> > param schedule
> > :   Schedule to dispatch
>
> > Run production according to schedule.
> >
> > This is a SimPy process that manages scheduled production.
> >
> > param duration_hours
> > :   Duration to run production
>
> > Handle production disruption by rescheduling.
> >
> > param disruption_type
> > :   Type of disruption
> >
> > param affected_lines
> > :   Affected production lines
> >
> > param duration_minutes
> > :   Expected disruption duration
> >
> > returns
> > :   Updated schedule
>
> > Get comprehensive scheduling metrics.
> >
> > returns
> > :   Metrics dictionary
>
> > Export current schedule to CSV file.
> >
> > param filename
> > :   Output filename

# twin_model.scheduling.sequential_scheduler

::: autoapi-nested-parse
Sequential scheduler implementation.

Simple FIFO scheduling algorithm that processes orders in sequence,
respecting line compatibility and basic constraints.
:::

## Attributes

::: autoapisummary
twin_model.scheduling.sequential_scheduler.logger
:::

## Classes

::: autoapisummary
twin_model.scheduling.sequential_scheduler.SequentialScheduler
:::

## Module Contents

> Bases:
> `twin_model.scheduling.base_scheduler.BaseScheduler`{.interpreted-text
> role="py:obj"}
>
> Sequential FIFO scheduler implementation.
>
> Schedules orders in priority/FIFO order, respecting line compatibility
> and maintenance windows.
>
> > Generate schedule using sequential FIFO algorithm.
> >
> > param orders
> > :   List of production orders to schedule
> >
> > param lines
> > :   Available production lines
> >
> > param horizon_hours
> > :   Planning horizon in hours
> >
> > param start_time
> > :   Start time for scheduling (simulation minutes)
> >
> > returns
> > :   Schedule by line
>
> > Optimize existing schedule (no-op for sequential scheduler).
> >
> > Sequential scheduler doesn\'t optimize, just returns current
> > schedule.
> >
> > param current_schedule
> > :   Current schedule to optimize
> >
> > param cost_calculator
> > :   Cost calculator for evaluation
> >
> > returns
> > :   Same schedule (no optimization)
>
> > Reschedule after disruption.
> >
> > param disruption_time
> > :   When disruption occurred (simulation time)
> >
> > param disruption_type
> > :   Type of disruption
> >
> > param affected_resources
> > :   Affected lines/resources
> >
> > param current_schedule
> > :   Current schedule
> >
> > returns
> > :   Updated schedule
>
> > Get scheduler performance metrics.
> >
> > returns
> > :   Metrics dictionary

# twin_model.transduction

::: autoapi-nested-parse
Transduction module for data collection and transformation.
:::

## Submodules

::: {.toctree maxdepth="1"}
/autoapi/twin_model/transduction/mes_collector/index
:::

## Classes

::: autoapisummary
twin_model.transduction.MESDataCollector
twin_model.transduction.MESRecord twin_model.transduction.ProductInfo
:::

## Package Contents

> Collects simulation data and formats it for MES output.
>
> This collector monitors equipment primitives and captures their state
> and production metrics at regular intervals (default 5 minutes).
>
> > Register equipment for monitoring.
> >
> > param equipment_id
> > :   Unique equipment identifier
> >
> > param equipment
> > :   Equipment primitive to monitor
> >
> > param equipment_type
> > :   Type (Filler, Packer, Palletizer)
> >
> > param line_id
> > :   Production line ID
>
> > Update current production order for equipment.
> >
> > param equipment_id
> > :   Equipment identifier
> >
> > param order_id
> > :   Production order ID
> >
> > param product_id
> > :   Product being produced
>
> > Collect data at regular intervals (coroutine).
>
> > Convert collected records to pandas DataFrame.
> >
> > returns
> > :   DataFrame with MES records
>
> > Save collected data to CSV file.
> >
> > param filepath
> > :   Path to save CSV file
>
> > Get summary statistics of collected data.
> >
> > returns
> > :   Dictionary with summary statistics

> Single MES data record for a 5-minute interval.

> Product information for MES records.

# twin_model.transduction.mes_collector

::: autoapi-nested-parse
MES Data Collector for capturing simulation events in MES format.

This module provides a data collector that captures simulation events
and formats them according to MES (Manufacturing Execution System)
standards.
:::

## Attributes

::: autoapisummary
twin_model.transduction.mes_collector.logger
:::

## Classes

::: autoapisummary
twin_model.transduction.mes_collector.MESRecord
twin_model.transduction.mes_collector.ProductInfo
twin_model.transduction.mes_collector.MESDataCollector
:::

## Module Contents

> Single MES data record for a 5-minute interval.

> Product information for MES records.

> Collects simulation data and formats it for MES output.
>
> This collector monitors equipment primitives and captures their state
> and production metrics at regular intervals (default 5 minutes).
>
> > Register equipment for monitoring.
> >
> > param equipment_id
> > :   Unique equipment identifier
> >
> > param equipment
> > :   Equipment primitive to monitor
> >
> > param equipment_type
> > :   Type (Filler, Packer, Palletizer)
> >
> > param line_id
> > :   Production line ID
>
> > Update current production order for equipment.
> >
> > param equipment_id
> > :   Equipment identifier
> >
> > param order_id
> > :   Production order ID
> >
> > param product_id
> > :   Product being produced
>
> > Collect data at regular intervals (coroutine).
>
> > Convert collected records to pandas DataFrame.
> >
> > returns
> > :   DataFrame with MES records
>
> > Save collected data to CSV file.
> >
> > param filepath
> > :   Path to save CSV file
>
> > Get summary statistics of collected data.
> >
> > returns
> > :   Dictionary with summary statistics

## twin_model.primitives.buffer_flow

### AccumulationBuffer

Dynamic accumulation buffer for managing material flow between equipment.

#### Overview

The `AccumulationBuffer` class provides inter-equipment flow management with:
- FIFO (First-In-First-Out) and FILO (First-In-Last-Out) operation modes
- Configurable capacity and flow rate constraints
- Overflow and underflow detection
- Dwell time tracking for material residence
- Real-time state monitoring and metrics

#### Class Definition

```python
class AccumulationBuffer(BaseFlowPrimitive):
    """Dynamic accumulation buffer between equipment."""
    
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
            config: Configuration dictionary with buffer settings
            flow_capacity: Flow capacity constraints
            buffer_params: Buffer-specific parameters
        """
```

#### Key Parameters

**BufferParameters**:
- `capacity`: Maximum buffer storage capacity (units)
- `initial_level`: Starting material level (units)
- `mode`: Operation mode ("FIFO" or "FILO")
- `max_flow_rate`: Maximum input/output flow rate (units/min)
- `warning_low`: Low level warning threshold (%)
- `warning_high`: High level warning threshold (%)
- `update_interval`: Flow update interval (minutes)

#### Methods

- `connect(upstream, downstream)`: Connect buffer to equipment
- `process_flow()`: Main flow processing coroutine
- `get_metrics()`: Get current buffer metrics
- `get_utilization()`: Calculate buffer utilization percentage

#### Usage Example

```python
from twin_model.primitives.buffer_flow import AccumulationBuffer, BufferParameters

# Create buffer parameters
buffer_params = BufferParameters(
    capacity=1000.0,
    initial_level=500.0,
    mode="FIFO",
    max_flow_rate=100.0,
    warning_low=0.2,
    warning_high=0.8
)

# Create buffer
buffer = AccumulationBuffer(
    env=env,
    config={"id": "BUF-001", "name": "Main Buffer"},
    flow_capacity=flow_capacity,
    buffer_params=buffer_params
)

# Connect to equipment
buffer.connect(upstream_equipment, downstream_equipment)
buffer.start()
```

## twin_model.control.vcurve_controller

### VCurveController

Implements V-curve speed control based on Theory of Constraints (TOC) principles.

#### Overview

The `VCurveController` manages production line speeds to protect the constraint (bottleneck) equipment by:
- Running upstream equipment faster to prevent constraint starvation
- Running downstream equipment faster to prevent constraint blocking
- Dynamically identifying and adapting to constraint changes
- Monitoring constraint protection metrics

#### Class Definition

```python
class VCurveController:
    """V-curve speed controller for production lines."""
    
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

#### Key Parameters

**VCurveParameters**:
- `mode`: Control mode ("FIXED_CONSTRAINT" or "DYNAMIC_CONSTRAINT")
- `constraint_equipment`: ID of constraint equipment (fixed mode)
- `upstream_differential`: Speed increase for upstream equipment (0.15-0.25)
- `downstream_differential`: Speed increase for downstream equipment (0.10-0.20)
- `update_interval`: Control update interval (minutes)
- `max_speed_multiplier`: Maximum speed multiplier (1.3-1.5)
- `min_speed_multiplier`: Minimum speed multiplier (0.8-0.9)

#### Control Modes

1. **FIXED_CONSTRAINT**: Constraint is predetermined and doesn't change
2. **DYNAMIC_CONSTRAINT**: Controller identifies constraint based on utilization

#### Methods

- `start()`: Start the control process
- `identify_constraint()`: Identify current constraint equipment
- `calculate_speeds()`: Calculate V-curve speed adjustments
- `apply_speed_adjustments()`: Apply calculated speeds to equipment
- `get_metrics()`: Get controller performance metrics

#### Usage Example

```python
from twin_model.control.vcurve_controller import VCurveController, VCurveParameters
from twin_model.control.vcurve_controller import VCurveMode

# Create V-curve parameters
vcurve_params = VCurveParameters(
    mode=VCurveMode.FIXED_CONSTRAINT,
    constraint_equipment="LINE1-FIL",
    upstream_differential=0.20,  # 20% faster upstream
    downstream_differential=0.15,  # 15% faster downstream
    update_interval=5.0,
    max_speed_multiplier=1.4,
    min_speed_multiplier=0.85
)

# Create controller
controller = VCurveController(
    env=env,
    equipment=equipment_dict,
    params=vcurve_params
)

# Start control
controller.start()

# Get metrics after running
metrics = controller.get_metrics()
print(f"Constraint starvation: {metrics['constraint_starvation_rate']*100:.1f}%")
print(f"Constraint blocking: {metrics['constraint_blocking_rate']*100:.1f}%")
```

## twin_model.scheduling.schedule_generator

### ScheduleGenerator

Generates production schedules with configurable optimization strategies.

#### Overview

The `ScheduleGenerator` creates production orders for simulation with:
- Multiple sequencing strategies (optimized, random, campaign)
- Configurable batch sizing (fixed, dynamic, economic)
- Changeover time consideration
- Product family grouping
- Demand-based prioritization

#### Class Definition

```python
class ScheduleGenerator:
    """Production schedule generator."""
    
    def __init__(
        self,
        config: ScheduleGeneratorConfig,
        product_manifest_path: Path,
        random_seed: int = None
    ) -> None:
        """Initialize schedule generator.
        
        Args:
            config: Schedule generation configuration
            product_manifest_path: Path to product manifest YAML
            random_seed: Random seed for reproducibility
        """
```

#### Key Configuration

**ScheduleGeneratorConfig**:
- `sequence_mode`: Order sequencing strategy ("optimized", "random", "campaign")
- `batch_sizing`: Batch size strategy ("fixed", "dynamic", "economic")
- `min_batch_hours`: Minimum batch duration (hours)
- `max_batch_hours`: Maximum batch duration (hours)
- `changeover_frequency_target`: Target changeover time percentage (0.10-0.20)
- `product_families`: Product family definitions for grouping

#### Sequencing Strategies

1. **Optimized**: Minimizes changeover time and groups similar products
2. **Random**: Random product sequencing (sub-optimal baseline)
3. **Campaign**: Long runs of same product family

#### Methods

- `generate_schedule()`: Generate production schedule
- `calculate_changeover_time()`: Calculate changeover between products
- `optimize_sequence()`: Optimize order sequence
- `get_metrics()`: Get schedule generation metrics

#### Usage Example

```python
from twin_model.scheduling.schedule_generator import (
    ScheduleGenerator, 
    ScheduleGeneratorConfig,
    ProductionOrder
)

# Create configuration
config = ScheduleGeneratorConfig(
    sequence_mode="optimized",
    batch_sizing="dynamic",
    min_batch_hours=4.0,
    max_batch_hours=12.0,
    changeover_frequency_target=0.15
)

# Create generator
generator = ScheduleGenerator(
    config=config,
    product_manifest_path=Path("config/product_manifest.yaml"),
    random_seed=42
)

# Generate 7-day schedule
orders = generator.generate_schedule(
    duration_days=7,
    start_date=datetime(2025, 1, 1)
)

# Process orders
for order in orders:
    print(f"Order {order.order_id}: {order.product_id} "
          f"on LINE{order.line_id} for {order.target_volume} units")
```

### SubOptimalScheduleGenerator

Specialized generator for creating deliberately sub-optimal schedules for baseline comparisons.

```python
class SubOptimalScheduleGenerator(ScheduleGenerator):
    """Generate sub-optimal schedules for baseline testing."""
    
    def generate_schedule(
        self,
        duration_days: int,
        start_date: datetime
    ) -> list[ProductionOrder]:
        """Generate sub-optimal schedule with poor sequencing."""
```

Features:
- Excessive changeovers through random sequencing
- Short batch sizes causing frequent equipment stops
- Poor product family grouping
- Misaligned line assignments

