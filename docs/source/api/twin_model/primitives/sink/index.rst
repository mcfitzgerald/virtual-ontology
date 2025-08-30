twin_model.primitives.sink
==========================

Sink primitive for collecting from equipment output queues.

This module provides sink primitives that collect directly from
equipment output queues. NO BUFFERS - direct connection only.


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




CollectedProduct
~~~~~~~~~~~~~~~~

Represents a collected finished product.


**Attributes:**

- **collected_time** (attribute): 
- **order_id** (attribute): 
- **product_id** (attribute): 
- **quality** (attribute): 
- **source_equipment** (attribute): 


OrderTracking
~~~~~~~~~~~~~

Tracks order completion.


**Attributes:**

- **collected_quantity** (attribute): 
- **completion_time** (attribute): 
- **order_id** (attribute): 
- **start_time** (attribute): 
- **target_quantity** (attribute): 


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




SamplingConfig
~~~~~~~~~~~~~~

Configuration for observable sampling and performance optimization.

This class controls how events are collected and stored during simulation,
providing trade-offs between data completeness and performance.

.. attribute:: mode

   Simulation mode controlling data collection strategy

.. attribute:: sampling_rate

   Record every Nth event (1 = all events)

.. attribute:: aggregation_interval

   Time window for aggregating metrics (minutes)

.. attribute:: critical_events

   Event types that bypass sampling (always recorded)

.. attribute:: buffer_size

   Maximum events to keep in memory per primitive

.. attribute:: enable_global_observables

   Whether to emit to global event bus

Initialize sampling configuration.

:param mode: Data collection mode (DETAILED, PRODUCTION, or FAST)
:param sampling_rate: Event sampling frequency (1 = every event, 10 = every 10th)
:param aggregation_interval: Time window for metric aggregation in minutes
:param buffer_size: Maximum events to keep in circular buffer
:param enable_global_observables: Whether to duplicate events to global bus


**Attributes:**

- **aggregation_interval** (attribute): 
- **buffer_size** (attribute): 
- **critical_events** (attribute): 
- **enable_global_observables** (attribute): 
- **event_counter** (attribute): 
- **mode** (attribute): 
- **sampling_rate** (attribute): 

**Methods:**

.. method:: __init__(mode: SimulationMode = SimulationMode.PRODUCTION, sampling_rate: int = 10, aggregation_interval: float = 5.0, buffer_size: int = 1000, enable_global_observables: bool = False)

   Initialize sampling configuration.

   :param mode: Data collection mode (DETAILED, PRODUCTION, or FAST)
   :param sampling_rate: Event sampling frequency (1 = every event, 10 = every 10th)
   :param aggregation_interval: Time window for metric aggregation in minutes
   :param buffer_size: Maximum events to keep in circular buffer
   :param enable_global_observables: Whether to duplicate events to global bus



.. method:: should_record_event(event_type: str, is_critical: bool = False)

   Determine if an event should be recorded based on sampling config.

   :param event_type: Type of event being emitted
   :param is_critical: Override flag to mark event as critical

   :returns: True if event should be recorded, False otherwise




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






