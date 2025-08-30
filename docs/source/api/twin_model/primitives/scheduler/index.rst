twin_model.primitives.scheduler
===============================

Enhanced scheduler primitive with smart production sequencing.

This module provides advanced scheduling capabilities including:
- Product sequencing strategies (random, changeover-optimized, campaign)
- Changeover matrices for product-to-product transition times
- Shift-specific scheduling
- ABC analysis for prioritization
- Control system integration


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




ChangeoverMatrix
~~~~~~~~~~~~~~~~

Product-to-product changeover times.


**Attributes:**

- **base_times** (attribute): 
- **products** (attribute): 

**Methods:**

.. method:: get_changeover_time(from_product: str, to_product: str)

   Get changeover time between products.

   :param from_product: Current product
   :param to_product: Next product

   :returns: Changeover time in minutes




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




SequencingStrategy
~~~~~~~~~~~~~~~~~~

Product sequencing strategies.


**Attributes:**

- **CAMPAIGN_MODE** (attribute): 
- **CHANGEOVER_OPTIMIZED** (attribute): 
- **DUE_DATE** (attribute): 
- **PRIORITY_BASED** (attribute): 
- **RANDOM** (attribute): 

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






