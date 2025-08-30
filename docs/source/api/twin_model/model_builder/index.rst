twin_model.model_builder
========================

Ontology-driven model builder for SimPy simulations.

This module builds SimPy models from the twin ontology structure and manifests.
Key features:
- NO BUFFERS - only internal equipment queues
- Direct equipment-to-equipment connections
- Two-layer control system integration
- Proper ontology interpretation


Classes
-------

BasePrimitive
~~~~~~~~~~~~~

Base class for all SimPy primitives.

All primitives must emit observables for discovery-based learning.
This base class provides core functionality for:
- Observable emission and storage
- Configuration management
- SimPy environment integration
- Common event patterns

The observable stream is the primary mechanism through which the
LLM discovers relationships and patterns without prescriptive rules.

Initialize primitive with configuration and performance optimization.

:param env: SimPy environment for discrete event simulation
:param config: Primitive configuration from manifest
:param sampling_config: Optional sampling configuration for performance


**Attributes:**

- **__slots__** (attribute): 
- **config** (attribute): 
- **env** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **logger** (attribute): 
- **metric_aggregator** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **process** (attribute): 
- **sampling_config** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: PrimitiveConfig, sampling_config: Optional[SamplingConfig] = None)

   Initialize primitive with configuration and performance optimization.

   :param env: SimPy environment for discrete event simulation
   :param config: Primitive configuration from manifest
   :param sampling_config: Optional sampling configuration for performance



.. method:: __repr__()

   Return string representation for debugging.



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this primitive to another via relationship.

   :param other: Target primitive to connect to
   :param relationship_type: Type of relationship (feeds_into, controls, monitors)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the primitive's processes.

   This method should be called after all primitives are created
   and wired together. It typically starts one or more SimPy
   processes that represent the primitive's behavior.




ControlManager
~~~~~~~~~~~~~~

Manages the two-layer control system.

This class:
1. Loads control definitions from ontology
2. Loads control mappings from configuration
3. Applies current control settings
4. Computes simulation parameters from controls

Initialize control manager.

:param ontology_path: Path to twin ontology with control definitions
:param mappings_path: Path to control mappings configuration
:param settings_path: Optional path to current control settings


**Attributes:**

- **controls** (attribute): 
- **mappings** (attribute): 
- **mappings_config** (attribute): 
- **mappings_path** (attribute): 
- **ontology** (attribute): 
- **ontology_path** (attribute): 
- **settings_path** (attribute): 
- **state** (attribute): 

**Methods:**

.. method:: __init__(ontology_path: pathlib.Path, mappings_path: pathlib.Path, settings_path: Optional[pathlib.Path] = None)

   Initialize control manager.

   :param ontology_path: Path to twin ontology with control definitions
   :param mappings_path: Path to control mappings configuration
   :param settings_path: Optional path to current control settings



.. method:: _apply_bounds(params: Dict[str, float])

   Apply parameter bounds from configuration.

   :param params: Computed parameters

   :returns: Bounded parameters



.. method:: _apply_defaults()

   Apply default control values.



.. method:: _apply_mapping(control_value: Any, mapping: ParameterMapping)

   Apply a mapping function to transform control to parameter.

   :param control_value: Current control value
   :param mapping: Mapping configuration

   :returns: Computed parameter value



.. method:: _load_yaml(path: pathlib.Path)

   Load YAML configuration file.



.. method:: _parse_controls()

   Parse control definitions from ontology.



.. method:: _parse_mappings()

   Parse control to parameter mappings.



.. method:: apply_scenario(scenario_name: str)

   Apply a predefined scenario.

   :param scenario_name: Name of scenario to apply

   :returns: True if scenario was applied



.. method:: describe_control(name: str)

   Get human-readable description of a control.

   :param name: Control name

   :returns: Description string



.. method:: get_all_parameters()

   Get all computed parameters.

   :returns: Dictionary of parameter values



.. method:: get_control_value(name: str)

   Get current value of a control.

   :param name: Control name

   :returns: Current control value



.. method:: get_parameter(name: str, default: float = 0)

   Get computed simulation parameter.

   :param name: Parameter name
   :param default: Default value if not found

   :returns: Parameter value



.. method:: get_recommendations()

   Get recommendations for control improvements.

   :returns: List of recommendations with expected impact



.. method:: get_scenario(scenario_name: str)

   Get predefined scenario configuration.

   :param scenario_name: Name of scenario

   :returns: Scenario configuration or None



.. method:: load_settings(path: pathlib.Path)

   Load control settings from file.

   :param path: Path to control settings YAML



.. method:: save_settings(path: pathlib.Path)

   Save current control settings to file.

   :param path: Path to save settings



.. method:: set_control_value(name: str, value: Any)

   Set control value and recompute parameters.

   :param name: Control name
   :param value: New value



.. method:: update_parameters()

   Recompute all simulation parameters from current controls.




EntityDefinition
~~~~~~~~~~~~~~~~

Definition of an entity from ontology.


**Attributes:**

- **entity_class** (attribute): 
- **entity_id** (attribute): 
- **primitive_type** (attribute): 
- **properties** (attribute): 
- **relationships** (attribute): 


EquipmentPrimitive
~~~~~~~~~~~~~~~~~~

Equipment with internal queues only - no external buffers.

Key features:
- Internal input and output queues (SimPy Stores)
- Direct equipment-to-equipment connections
- Realistic failure modeling
- Product-specific performance
- State-based operation

Initialize equipment with internal queues.

:param env: SimPy environment
:param config: Equipment configuration
:param sampling_config: Optional sampling configuration


**Attributes:**

- **__slots__** (attribute): 
- **base_rate** (attribute): 
- **config** (attribute): 
- **current_order** (attribute): 
- **current_product** (attribute): 
- **downstream_equipment** (attribute): 
- **env** (attribute): 
- **equipment_type** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **failure_count** (attribute): 
- **failure_process** (attribute): 
- **input_queue** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **line_id** (attribute): 
- **logger** (attribute): 
- **major_failure_count** (attribute): 
- **metric_aggregator** (attribute): 
- **micro_stop_count** (attribute): 
- **micro_stop_duration_mean** (attribute): 
- **micro_stop_duration_sigma** (attribute): 
- **micro_stop_probability** (attribute): 
- **minor_failure_count** (attribute): 
- **mtbf** (attribute): 
- **mttr** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **output_queue** (attribute): 
- **performance_factor** (attribute): 
- **position** (attribute): 
- **previous_state** (attribute): 
- **process** (attribute): 
- **sampling_config** (attribute): 
- **scrap_rate** (attribute): 
- **state** (attribute): 
- **state_durations** (attribute): 
- **state_start_time** (attribute): 
- **units_produced** (attribute): 
- **units_scrapped** (attribute): 
- **upstream_equipment** (attribute): 
- **warmup_complete** (attribute): 
- **warmup_period** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, sampling_config: Optional[twin_model.primitives.base.SamplingConfig] = None)

   Initialize equipment with internal queues.

   :param env: SimPy environment
   :param config: Equipment configuration
   :param sampling_config: Optional sampling configuration



.. method:: __repr__()

   Return string representation for debugging.



.. method:: _change_state(new_state: EquipmentState)

   Change equipment state and track duration.

   :param new_state: New equipment state



.. method:: _failure_process()

   Generate equipment failures based on realistic patterns.



.. method:: _get_next_failure()

   Determine next failure using competing risks model.

   Based on research findings:
   - 80% of stops are micro-stops (jams, sensor trips, adjustments)
   - 15% are minor failures (component issues, calibration)
   - 5% are major failures (equipment breakdown)

   :returns: Tuple of (failure_type, time_to_failure)



.. method:: _get_repair_duration(failure_type: FailureType)

   Get repair duration based on failure type and root causes.

   Based on research:
   - Micro-stops (80%): 0.5-3 minutes (jams, sensor trips)
   - Minor failures (15%): 5-30 minutes (component adjust, calibration)
   - Major failures (5%): 30+ minutes (breakdown, part replacement)

   :param failure_type: Type of failure

   :returns: Repair duration in minutes



.. method:: _handle_blocked()

   Handle blocked state (output queue full).



.. method:: _handle_interrupt(interrupt: simpy.Interrupt)

   Handle process interruption.

   :param interrupt: Interruption cause



.. method:: _handle_starved()

   Handle starved state (no input material).



.. method:: _is_blocked()

   Check if equipment is blocked by downstream.

   :returns: True if blocked, False otherwise



.. method:: _process_unit()

   Process a single unit of production.



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: connect_to(other: twin_model.primitives.base.BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this equipment to downstream equipment.

   :param other: Next equipment in line
   :param relationship_type: Type of relationship (default: feeds_into)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_kpis()

   Calculate equipment KPIs.

   :returns: KPI dictionary



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_queue_status()

   Get current queue status.

   :returns: Queue status dictionary



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: run()

   Run main equipment process.



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the equipment processes.

   Implements the abstract start method from BasePrimitive.




LineConfiguration
~~~~~~~~~~~~~~~~~

Configuration for a production line.


**Attributes:**

- **equipment** (attribute): 
- **line_id** (attribute): 
- **sink** (attribute): 
- **source** (attribute): 

**Methods:**

.. method:: get_equipment_sequence()

   Get equipment sorted by position.




MonitorPrimitive
~~~~~~~~~~~~~~~~

Monitor for tracking system-wide KPIs and metrics.

Emits observables for:
- KPI updates and trends
- Target violations
- Performance alerts
- Aggregated metrics
- Real-time dashboards

Initialize monitor with configuration.

:param env: SimPy environment
:param config: Monitor configuration containing:
               - kpi_definitions: KPIs to track
               - update_interval: How often to update KPIs (minutes)
               - aggregation_window: Time window for aggregations
               - alert_thresholds: Thresholds for alerts
               - monitored_primitives: List of primitives to monitor


**Attributes:**

- **__slots__** (attribute): 
- **active_alerts** (attribute): 
- **aggregation_window** (attribute): 
- **alert_history** (attribute): 
- **alert_thresholds** (attribute): 
- **config** (attribute): 
- **env** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **kpis** (attribute): 
- **line_metrics** (attribute): 
- **logger** (attribute): 
- **metric_aggregator** (attribute): 
- **monitored_primitives** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **process** (attribute): 
- **product_metrics** (attribute): 
- **sampling_config** (attribute): 
- **shift_metrics** (attribute): 
- **update_interval** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig)

   Initialize monitor with configuration.

   :param env: SimPy environment
   :param config: Monitor configuration containing:
                  - kpi_definitions: KPIs to track
                  - update_interval: How often to update KPIs (minutes)
                  - aggregation_window: Time window for aggregations
                  - alert_thresholds: Thresholds for alerts
                  - monitored_primitives: List of primitives to monitor



.. method:: __repr__()

   Return string representation for debugging.



.. method:: _aggregate_availability(primitives: List[Any])

   Calculate aggregated availability for a group of primitives.



.. method:: _aggregate_cycle_time(primitives: List[Any])

   Calculate average cycle time for a group of primitives.



.. method:: _aggregate_oee(primitives: List[Any])

   Calculate aggregated OEE for a group of primitives.



.. method:: _aggregate_quality(primitives: List[Any])

   Calculate aggregated quality for a group of primitives.



.. method:: _aggregate_throughput(primitives: List[Any])

   Calculate aggregated throughput for a group of primitives.



.. method:: _aggregate_volume(primitives: List[Any])

   Calculate total volume for a group of primitives.



.. method:: _calculate_availability(primitive: Any)

   Calculate availability for a primitive.

   :param primitive: Primitive to calculate for

   :returns: Availability percentage



.. method:: _check_thresholds()

   Check KPIs against configured thresholds.



.. method:: _create_alert(kpi_name: str, severity: str, message: str)

   Create an alert.

   :param kpi_name: KPI that triggered alert
   :param severity: Alert severity
   :param message: Alert message



.. method:: _get_current_shift()

   Determine current shift based on time.



.. method:: _get_production_in_window(primitive: Any)

   Get production count in recent window.

   :param primitive: Primitive to check

   :returns: Production count in window



.. method:: _group_by_line()

   Group monitored primitives by production line.



.. method:: _group_by_product()

   Group monitored primitives by current product.



.. method:: _init_kpis()

   Initialize KPI definitions from config.



.. method:: _update_aggregations()

   Update aggregated metrics by line, product, shift.



.. method:: _update_kpis()

   Update all KPI values from monitored primitives.



.. method:: alert_process()

   Process for managing alerts.



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this primitive to another via relationship.

   :param other: Target primitive to connect to
   :param relationship_type: Type of relationship (feeds_into, controls, monitors)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_dashboard()

   Get dashboard summary of all metrics.

   :returns: Dictionary with dashboard data



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_kpi_history(kpi_name: str, window: Optional[float] = None)

   Get historical values of a KPI.

   :param kpi_name: Name of KPI
   :param window: Time window to retrieve

   :returns: List of (timestamp, value) tuples



.. method:: get_kpi_value(kpi_name: str)

   Get current value of a KPI.

   :param kpi_name: Name of KPI

   :returns: Current KPI value or None



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_statistics()

   Get monitor statistics.

   :returns: Dictionary of monitor metrics



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: monitor_process()

   Run monitoring process.



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: register_primitive(name: str, primitive: Any)

   Register a primitive to monitor.

   :param name: Primitive identifier
   :param primitive: Primitive instance



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the monitoring process.




OntologyDrivenModelBuilder
~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds SimPy models from ontology structure and manifests.

This builder:
1. Interprets the twin ontology to understand structure
2. Loads configuration from manifests
3. Creates primitives with internal queues only
4. Wires direct equipment connections
5. Integrates two-layer control system

Initialize model builder.

:param env: SimPy environment
:param ontology_path: Path to twin_ontology.yaml
:param manifest_dir: Directory containing manifest files
:param control_manager: Optional control manager for two-layer system
:param config_path: Optional path to twin_model.yaml config file


**Attributes:**

- **PRIMITIVE_CLASSES** (attribute): 
- **built** (attribute): 
- **classes** (attribute): 
- **config_path** (attribute): 
- **control_manager** (attribute): 
- **entities** (attribute): 
- **env** (attribute): 
- **lines** (attribute): 
- **manifest_dir** (attribute): 
- **manifests** (attribute): 
- **mappings** (attribute): 
- **ontology** (attribute): 
- **ontology_path** (attribute): 
- **primitives** (attribute): 
- **relationships** (attribute): 
- **system_config** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, ontology_path: pathlib.Path, manifest_dir: pathlib.Path, control_manager: Optional[twin_model.control.ControlManager] = None, config_path: Optional[pathlib.Path] = None)

   Initialize model builder.

   :param env: SimPy environment
   :param ontology_path: Path to twin_ontology.yaml
   :param manifest_dir: Directory containing manifest files
   :param control_manager: Optional control manager for two-layer system
   :param config_path: Optional path to twin_model.yaml config file



.. method:: _apply_control_parameters()

   Apply control system parameters to primitives.



.. method:: _create_monitors()

   Create monitors for KPI tracking.



.. method:: _create_primitives()

   Create SimPy primitives from entity definitions.



.. method:: _create_scheduler()

   Create scheduler with order management.



.. method:: _get_ontology_defaults(class_name: str)

   Get default property values from ontology class definition.

   :param class_name: Name of the class to get defaults for

   :returns: Dictionary of property defaults



.. method:: _load_entities()

   Load entity definitions from manifests.



.. method:: _load_manifests(manifest_dir: pathlib.Path)

   Load all manifest files from directory.



.. method:: _load_yaml(path: pathlib.Path)

   Load YAML file.



.. method:: _organize_lines()

   Organize entities into production lines.



.. method:: _parse_classes()

   Parse class definitions from TBox.



.. method:: _parse_mappings()

   Parse primitive mappings.



.. method:: _parse_relationships()

   Parse relationships from RBox.



.. method:: _wire_connections()

   Wire direct equipment-to-equipment connections using internal queues.

   This is the key architecture:
   - NO separate buffer entities
   - Direct equipment connections via internal queues
   - Source feeds first equipment's input queue
   - Sink collects from last equipment's output queue



.. method:: build_model()

   Build complete simulation model from ontology and manifests.

   :returns: Dictionary containing model components



.. method:: describe_model()

   Get human-readable description of the model.

   :returns: Description string



.. method:: get_line_status(line_id: str)

   Get current status of a production line.

   :param line_id: Line identifier

   :returns: Status dictionary



.. method:: start_processes()

   Start all simulation processes.




PrimitiveConfig
~~~~~~~~~~~~~~~

Configuration for a primitive instance.

This dataclass holds all configuration values loaded from manifests,
providing a clean separation between structure (ontology) and
values (manifests).

.. attribute:: id

   Unique identifier for this primitive instance

.. attribute:: type

   Type of primitive (Equipment, Buffer, Source, etc.)

.. attribute:: properties

   Type-checked properties from manifest

.. attribute:: relationships

   Dict of relationship type to related primitive IDs

.. attribute:: metadata

   Additional context for debugging and analysis


**Attributes:**

- **id** (attribute): 
- **metadata** (attribute): 
- **properties** (attribute): 
- **relationships** (attribute): 
- **type** (attribute): 

**Methods:**

.. method:: get_property(key: str, default: Any = None)

   Get a property value with optional default.

   :param key: Property name to retrieve
   :param default: Value to return if property not found

   :returns: Property value or default



.. method:: validate()

   Validate configuration against expected schema.

   :raises ValueError: If required properties are missing or invalid




Product
~~~~~~~

Product definition with changeover characteristics.


**Attributes:**

- **category** (attribute): 
- **complexity** (attribute): 
- **family** (attribute): 
- **margin** (attribute): 
- **max_batch_size** (attribute): 
- **min_batch_size** (attribute): 
- **product_id** (attribute): 
- **typical_batch_size** (attribute): 
- **volume_rank** (attribute): 


ProductCategory
~~~~~~~~~~~~~~~

ABC analysis categories.


**Attributes:**

- **A** (attribute): 
- **B** (attribute): 
- **C** (attribute): 

**Methods:**

.. method:: __copy__()



.. method:: __deepcopy__(memo)



.. method:: __dir__()

   Returns public methods and other interesting attributes.



.. method:: __format__(format_spec)



.. method:: __hash__()



.. method:: __init__(*args, **kwds)



.. method:: __new__(value)



.. method:: __reduce_ex__(proto)



.. method:: __repr__()



.. method:: __signature__()



.. method:: __str__()



.. method:: _generate_next_value_(name, start, count, last_values)

   Generate the next value when not given.

   name: the name of the member
   start: the initial start value or None
   count: the number of existing members
   last_values: the list of values assigned



.. method:: _missing_(value)



.. method:: name()

   The name of the Enum member.



.. method:: value()

   The value of the Enum member.




ProductionOrder
~~~~~~~~~~~~~~~

Enhanced production order with scheduling metadata.


**Attributes:**

- **actual_end** (attribute): 
- **actual_start** (attribute): 
- **completed_quantity** (attribute): 
- **due_date** (attribute): 
- **order_id** (attribute): 
- **priority** (attribute): 
- **product** (attribute): 
- **quantity** (attribute): 
- **release_date** (attribute): 
- **scheduled_start** (attribute): 
- **scrap_quantity** (attribute): 


SchedulerPrimitive
~~~~~~~~~~~~~~~~~~

Enhanced scheduler with intelligent production sequencing.

Key features:
- Multiple sequencing strategies
- Changeover optimization
- Campaign production support
- Shift-aware scheduling
- ABC prioritization
- Control system integration

Initialize enhanced scheduler.

:param env: SimPy environment
:param config: Scheduler configuration
:param sampling_config: Optional sampling configuration


**Attributes:**

- **__slots__** (attribute): 
- **active_orders** (attribute): 
- **campaign_size** (attribute): 
- **changeover_count** (attribute): 
- **changeover_matrix** (attribute): 
- **completed_orders** (attribute): 
- **config** (attribute): 
- **current_product** (attribute): 
- **current_shift** (attribute): 
- **env** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **last_changeover_time** (attribute): 
- **line_sources** (attribute): 
- **logger** (attribute): 
- **lookahead_horizon** (attribute): 
- **metric_aggregator** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **order_queue** (attribute): 
- **orders_completed** (attribute): 
- **orders_scheduled** (attribute): 
- **pending_orders** (attribute): 
- **process** (attribute): 
- **products** (attribute): 
- **sampling_config** (attribute): 
- **schedule_adherence** (attribute): 
- **shift_start_time** (attribute): 
- **shifts_config** (attribute): 
- **strategy** (attribute): 
- **total_changeover_time** (attribute): 
- **total_tardiness** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, sampling_config: Optional[twin_model.primitives.base.SamplingConfig] = None)

   Initialize enhanced scheduler.

   :param env: SimPy environment
   :param config: Scheduler configuration
   :param sampling_config: Optional sampling configuration



.. method:: __repr__()

   Return string representation for debugging.



.. method:: _create_campaigns(orders: List[ProductionOrder])

   Create production campaigns by grouping same products.

   :param orders: Orders to group into campaigns

   :returns: Orders sequenced in campaigns



.. method:: _initialize_changeover_matrix()

   Initialize product changeover matrix with realistic times.

   Changeover times based on:
   - Product family (cleaning requirements)
   - Complexity difference (setup adjustments)
   - Allergen considerations (deep cleaning)

   :returns: ChangeoverMatrix with product-to-product times



.. method:: _initialize_products()

   Initialize product catalog from configuration.



.. method:: _optimize_changeovers(orders: List[ProductionOrder])

   Optimize order sequence to minimize changeover time.

   Uses a greedy nearest-neighbor approach for simplicity.

   :param orders: Orders to sequence

   :returns: Optimized order sequence



.. method:: _sequence_orders()

   Sequence orders based on current strategy.

   :returns: List of orders in execution sequence



.. method:: _update_shift()

   Update current shift based on simulation time.



.. method:: add_order(order: ProductionOrder)

   Add a production order to the schedule.

   :param order: Production order to add



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: complete_order(order: ProductionOrder, completed_quantity: int, scrap_quantity: int = 0)

   Mark an order as complete.

   :param order: Order that was completed
   :param completed_quantity: Good units produced
   :param scrap_quantity: Scrapped units



.. method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this primitive to another via relationship.

   :param other: Target primitive to connect to
   :param relationship_type: Type of relationship (feeds_into, controls, monitors)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_next_order()

   Get next order from schedule.

   :returns: Next production order or None



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_schedule_metrics()

   Calculate scheduling performance metrics.

   :returns: Dictionary of scheduling KPIs



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: register_source(line_id: str, source: twin_model.primitives.source.SourcePrimitive)

   Register a source for a production line.

   :param line_id: Production line ID (e.g., 'LINE1')
   :param source: Source primitive for the line



.. method:: request_changeover(from_product: str, to_product: str)

   Request changeover time for product switch.

   :param from_product: Current product
   :param to_product: Next product

   :returns: Required changeover time in minutes



.. method:: run()

   Run scheduler process.



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the scheduler process.

   Implements the abstract start method from BasePrimitive.




SinkPrimitive
~~~~~~~~~~~~~

Sink that collects from equipment output queues.

Key features:
- Direct connection to last equipment's output queue
- Order tracking and completion
- Throughput monitoring
- Quality tracking
- Collection rate limiting

Initialize sink primitive.

:param env: SimPy environment
:param config: Sink configuration
:param upstream: Equipment output queue or equipment with output_queue
:param sampling_config: Optional sampling configuration


**Attributes:**

- **__slots__** (attribute): 
- **active_orders** (attribute): 
- **collected_products** (attribute): 
- **collection_rate** (attribute): 
- **completed_orders** (attribute): 
- **config** (attribute): 
- **env** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **is_collecting** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **line_id** (attribute): 
- **logger** (attribute): 
- **metric_aggregator** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **order_tracking_enabled** (attribute): 
- **process** (attribute): 
- **quality_threshold** (attribute): 
- **recent_collections** (attribute): 
- **sampling_config** (attribute): 
- **target_throughput** (attribute): 
- **throughput_window** (attribute): 
- **total_collected** (attribute): 
- **total_rejected** (attribute): 
- **total_units_collected** (attribute): 
- **upstream** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, upstream: Optional[Union[simpy.Store, Any]] = None, sampling_config: Optional[twin_model.primitives.base.SamplingConfig] = None)

   Initialize sink primitive.

   :param env: SimPy environment
   :param config: Sink configuration
   :param upstream: Equipment output queue or equipment with output_queue
   :param sampling_config: Optional sampling configuration



.. method:: __repr__()

   Return string representation for debugging.



.. method:: _clean_throughput_window()

   Remove old timestamps from throughput tracking.



.. method:: _collect_product()

   Collect a single product from upstream.



.. method:: _update_order_tracking(order_id: str)

   Update order tracking for collected product.

   :param order_id: Order identifier



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this primitive to another via relationship.

   :param other: Target primitive to connect to
   :param relationship_type: Type of relationship (feeds_into, controls, monitors)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_current_throughput()

   Calculate current throughput rate.

   :returns: Units per minute



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_order_status(order_id: Optional[str] = None)

   Get status of specific order or all orders.

   :param order_id: Optional specific order ID

   :returns: Order tracking information



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_products_by_order(order_id: str)

   Get all products collected for a specific order.

   :param order_id: Order identifier

   :returns: List of collected products



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_statistics()

   Get sink statistics.

   :returns: Statistics dictionary



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: register_order(order_id: str, target_quantity: int)

   Register a production order for tracking.

   :param order_id: Order identifier
   :param target_quantity: Expected quantity



.. method:: reset_statistics()

   Reset collection statistics.



.. method:: run()

   Run sink collection process.



.. method:: set_upstream(upstream: Union[simpy.Store, Any])

   Set upstream connection.

   :param upstream: Equipment output queue or equipment with output_queue



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the sink collection process.

   Implements the abstract start method from BasePrimitive.



.. method:: stop()

   Stop sink collection.




SourcePrimitive
~~~~~~~~~~~~~~~

Source that feeds directly into equipment input queues.

Key features:
- Direct connection to first equipment's input queue
- Order-driven generation
- Multiple arrival patterns
- Quality inspection at source
- Supply disruption modeling

Initialize source primitive.

:param env: SimPy environment
:param config: Source configuration
:param downstream: Equipment input queue or equipment with input_queue
:param sampling_config: Optional sampling configuration


**Attributes:**

- **__slots__** (attribute): 
- **arrival_pattern** (attribute): 
- **arrival_rate** (attribute): 
- **batch_size** (attribute): 
- **changeover_count** (attribute): 
- **changeover_start_time** (attribute): 
- **config** (attribute): 
- **current_order** (attribute): 
- **disruption_probability** (attribute): 
- **downstream** (attribute): 
- **env** (attribute): 
- **event_batcher** (attribute): 
- **events_emitted** (attribute): 
- **events_sampled** (attribute): 
- **is_changing_over** (attribute): 
- **is_disrupted** (attribute): 
- **is_initialized** (attribute): 
- **is_running** (attribute): 
- **last_product** (attribute): 
- **line_id** (attribute): 
- **logger** (attribute): 
- **metric_aggregator** (attribute): 
- **observable_buffer** (attribute): 
- **observables** (attribute): 
- **order_mode** (attribute): 
- **order_queue** (attribute): 
- **process** (attribute): 
- **quality_rate** (attribute): 
- **sampling_config** (attribute): 
- **setup_units_produced** (attribute): 
- **setup_units_scrapped** (attribute): 
- **supply_variability** (attribute): 
- **total_changeover_time** (attribute): 
- **total_generated** (attribute): 
- **total_rejected** (attribute): 
- **units_generated** (attribute): 
- **units_remaining** (attribute): 

**Methods:**

.. method:: __init__(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, downstream: Optional[Union[simpy.Store, Any]] = None, sampling_config: Optional[twin_model.primitives.base.SamplingConfig] = None)

   Initialize source primitive.

   :param env: SimPy environment
   :param config: Source configuration
   :param downstream: Equipment input queue or equipment with input_queue
   :param sampling_config: Optional sampling configuration



.. method:: __repr__()

   Return string representation for debugging.



.. method:: _complete_current_order()

   Complete the current production order.



.. method:: _continuous_generation()

   Generate material continuously.



.. method:: _execute_changeover()

   Execute product changeover process.

   :Yields: Changeover duration and setup production



.. method:: _generate_batch(size: int)

   Generate a batch of units.

   :param size: Batch size



.. method:: _generate_unit()

   Generate a single unit.

   Sets self.last_unit_generated to indicate success.



.. method:: _handle_disruption()

   Handle supply disruption.



.. method:: _order_driven_generation()

   Generate material based on production orders.



.. method:: add_order_to_queue(order: twin_model.primitives.scheduler.ProductionOrder)

   Add order to queue for processing.

   :param order: Production order to queue



.. method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO')

   Emit observable through batcher for efficient processing.

   Events are grouped by type and time window to reduce processing
   overhead. Use this for high-frequency events that can be processed
   in batches.

   :param event_type: Type of event
   :param details: Event details
   :param severity: Event severity

   :returns: Completed batch if ready, None otherwise



.. method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into')

   Connect this primitive to another via relationship.

   :param other: Target primitive to connect to
   :param relationship_type: Type of relationship (feeds_into, controls, monitors)



.. method:: emit_metric(metric_name: str, value: float)

   Emit a metric value for aggregation.

   This method tracks numeric metrics over time windows using
   incremental statistics. Useful for KPIs like OEE, throughput, etc.

   :param metric_name: Name of the metric (e.g., "oee", "throughput")
   :param value: Numeric value to aggregate

   :returns: Completed window statistics if window finished, None otherwise



.. method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO', is_critical: bool = False)

   Emit an observable event with sampling and performance optimization.

   This is the primary mechanism for primitives to communicate
   their state and behavior. Events are now sampled based on
   configuration to prevent memory exhaustion in long simulations.

   :param event_type: Type of event (state_change, production, failure, etc.)
   :param details: Event-specific details with rich context
   :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   :param is_critical: Mark event as critical to bypass sampling



.. method:: flush_observables()

   Flush observable buffer and return events.

   This method can be called periodically to persist events to external
   storage and free memory. Useful for long-running simulations.

   :returns: List of flushed events



.. method:: get_aggregated_metrics()

   Get current aggregated metrics.

   :returns: Current window statistics and history



.. method:: get_failure_config(failure_type: str, key: str, default: Any = None)

   Get failure configuration value.

   :param failure_type: Type of failure (micro_stops, minor_failures, major_failures)
   :param key: Configuration key within failure type
   :param default: Default value if not found

   :returns: Configuration value or default



.. method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None)

   Retrieve observables with optional filtering from circular buffer.

   :param event_type: Filter by specific event type
   :param start_time: Filter events after this simulation time
   :param end_time: Filter events before this simulation time

   :returns: Filtered list of observable events



.. method:: get_performance_metrics()

   Get detailed performance metrics for monitoring.

   :returns: Dictionary containing performance statistics



.. method:: get_state()

   Get current primitive state including performance metrics.

   :returns: Dictionary describing current primitive state and performance



.. method:: get_statistics()

   Get source statistics.

   :returns: Statistics dictionary



.. method:: get_system_config(key: str, default: Any = None)

   Get value from system configuration.

   :param key: Configuration key (supports dot notation like 'failure_distributions.micro_stops')
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: get_technical_config(key: str, default: Any = None)

   Get value from technical configuration.

   :param key: Configuration key (supports dot notation)
   :param default: Default value if key not found

   :returns: Configuration value or default



.. method:: initialize()

   Initialize primitive before starting processes.

   Override this method to perform setup that requires all
   primitives to be created first (e.g., wiring relationships).



.. method:: initialize_wip(level: float = 0.5)

   Initialize work-in-progress in downstream equipment.

   :param level: Fill level as fraction of capacity (0-1)



.. method:: process_batches()

   Process any pending batches.

   Call this periodically to flush pending batches.

   :returns: List of completed batches



.. method:: run()

   Run source generation process.



.. method:: set_downstream(downstream: Union[simpy.Store, Any])

   Set downstream connection.

   :param downstream: Equipment input queue or equipment with input_queue



.. method:: set_production_order(order: twin_model.primitives.scheduler.ProductionOrder)

   Set current production order and check if changeover is needed.

   :param order: Production order to process



.. method:: shutdown()

   Gracefully shutdown the primitive.

   Override this method to perform cleanup when simulation ends.



.. method:: start()

   Start the source generation process.

   Implements the abstract start method from BasePrimitive.



.. method:: stop()

   Stop source generation.






