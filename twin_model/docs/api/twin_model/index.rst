twin_model
==========

.. py:module:: twin_model

.. autoapi-nested-parse::

   Ontology-driven virtual twin model.

   This package provides an ontology-driven simulation framework for generating
   synthetic MES (Manufacturing Execution System) data using SimPy discrete event
   simulation with rich observables for pattern discovery.



Submodules
----------

.. toctree::
   :maxdepth: 1

   /api/twin_model/config/index
   /api/twin_model/model_builder/index
   /api/twin_model/primitives/index
   /api/twin_model/state_manager/index
   /api/twin_model/transduction/index


Classes
-------

.. autoapisummary::

   twin_model.BasePrimitive
   twin_model.PrimitiveConfig
   twin_model.Equipment
   twin_model.EquipmentState
   twin_model.Buffer
   twin_model.BufferItem
   twin_model.Source
   twin_model.ArrivalPattern
   twin_model.Sink
   twin_model.CollectedProduct
   twin_model.Scheduler
   twin_model.ScheduleEvent
   twin_model.ScheduleEventType
   twin_model.ProductionOrder
   twin_model.Monitor
   twin_model.KPIType
   twin_model.KPIMetric
   twin_model.OntologyDrivenModelBuilder
   twin_model.MESTransducer


Package Contents
----------------

.. py:class:: BasePrimitive(env: simpy.Environment, config: PrimitiveConfig, sampling_config: Optional[SamplingConfig] = None)

   Bases: :py:obj:`abc.ABC`


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


   .. py:attribute:: env


   .. py:attribute:: config


   .. py:attribute:: sampling_config


   .. py:attribute:: observable_buffer


   .. py:attribute:: observables


   .. py:attribute:: process
      :type:  Optional[simpy.Process]
      :value: None



   .. py:attribute:: is_initialized
      :type:  bool
      :value: False



   .. py:attribute:: is_running
      :type:  bool
      :value: False



   .. py:attribute:: events_emitted
      :type:  int
      :value: 0



   .. py:attribute:: events_sampled
      :type:  int
      :value: 0



   .. py:attribute:: event_batcher


   .. py:attribute:: metric_aggregator


   .. py:method:: start() -> None
      :abstractmethod:


      Start the primitive's processes.

      This method should be called after all primitives are created
      and wired together. It typically starts one or more SimPy
      processes that represent the primitive's behavior.



   .. py:method:: emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO') -> None

      Emit an observable event with sampling and performance optimization.

      This is the primary mechanism for primitives to communicate
      their state and behavior. Events are now sampled based on
      configuration to prevent memory exhaustion in long simulations.

      :param event_type: Type of event (state_change, production, failure, etc.)
      :param details: Event-specific details with rich context
      :param severity: Event severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)



   .. py:method:: get_observables(event_type: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[Dict[str, Any]]

      Retrieve observables with optional filtering from circular buffer.

      :param event_type: Filter by specific event type
      :param start_time: Filter events after this simulation time
      :param end_time: Filter events before this simulation time

      :returns: Filtered list of observable events



   .. py:method:: connect_to(other: BasePrimitive, relationship_type: str = 'feeds_into') -> None

      Connect this primitive to another via relationship.

      :param other: Target primitive to connect to
      :param relationship_type: Type of relationship (feeds_into, controls, monitors)



   .. py:method:: initialize() -> None

      Initialize primitive before starting processes.

      Override this method to perform setup that requires all
      primitives to be created first (e.g., wiring relationships).



   .. py:method:: shutdown() -> None

      Gracefully shutdown the primitive.

      Override this method to perform cleanup when simulation ends.



   .. py:method:: emit_metric(metric_name: str, value: float) -> Optional[Dict[str, Any]]

      Emit a metric value for aggregation.

      This method tracks numeric metrics over time windows using
      incremental statistics. Useful for KPIs like OEE, throughput, etc.

      :param metric_name: Name of the metric (e.g., "oee", "throughput")
      :param value: Numeric value to aggregate

      :returns: Completed window statistics if window finished, None otherwise



   .. py:method:: batch_emit_observable(event_type: str, details: Dict[str, Any], severity: str = 'INFO') -> Optional[List[Dict[str, Any]]]

      Emit observable through batcher for efficient processing.

      Events are grouped by type and time window to reduce processing
      overhead. Use this for high-frequency events that can be processed
      in batches.

      :param event_type: Type of event
      :param details: Event details
      :param severity: Event severity

      :returns: Completed batch if ready, None otherwise



   .. py:method:: process_batches() -> List[List[Dict[str, Any]]]

      Process any pending batches.

      Call this periodically to flush pending batches.

      :returns: List of completed batches



   .. py:method:: get_aggregated_metrics() -> Dict[str, Any]

      Get current aggregated metrics.

      :returns: Current window statistics and history



   .. py:method:: flush_observables() -> List[Dict[str, Any]]

      Flush observable buffer and return events.

      This method can be called periodically to persist events to external
      storage and free memory. Useful for long-running simulations.

      :returns: List of flushed events



   .. py:method:: get_performance_metrics() -> Dict[str, Any]

      Get detailed performance metrics for monitoring.

      :returns: Dictionary containing performance statistics



   .. py:method:: get_state() -> Dict[str, Any]

      Get current primitive state including performance metrics.

      :returns: Dictionary describing current primitive state and performance



.. py:class:: PrimitiveConfig

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


   .. py:attribute:: id
      :type:  str


   .. py:attribute:: type
      :type:  str


   .. py:attribute:: properties
      :type:  Dict[str, Any]


   .. py:attribute:: relationships
      :type:  Dict[str, List[str]]


   .. py:attribute:: metadata
      :type:  Dict[str, Any]


   .. py:method:: get_property(key: str, default: Any = None) -> Any

      Get a property value with optional default.

      :param key: Property name to retrieve
      :param default: Value to return if property not found

      :returns: Property value or default



   .. py:method:: validate() -> None

      Validate configuration against expected schema.

      :raises ValueError: If required properties are missing or invalid



.. py:class:: Equipment(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, upstream: Optional[Any] = None, downstream: Optional[Any] = None, sampling_config: Optional[twin_model.primitives.base.SamplingConfig] = None)

   Bases: :py:obj:`twin_model.primitives.base.BasePrimitive`


   Generic equipment that processes materials.

   Emits rich observables for pattern discovery including:
   - State transitions with context (buffer levels, runtime, product)
   - Production events with quality metrics
   - Failure events with contributing factors
   - Performance variations by shift/product
   - Energy consumption patterns
   - Cascade failure propagation

   Initialize equipment with buffers and performance optimization.

   :param env: SimPy environment
   :param config: Equipment configuration containing:
                  - base_rate: Units per minute nominal capacity
                  - mtbf: Mean time between failures in minutes
                  - mttr: Mean time to repair in minutes
                  - energy_consumption_rate: kWh per minute when running
   :param upstream: Input buffer (None for source equipment)
   :param downstream: Output buffer (None for sink equipment)
   :param sampling_config: Optional sampling configuration for performance


   .. py:attribute:: upstream
      :value: None



   .. py:attribute:: downstream
      :value: None



   .. py:attribute:: base_rate


   .. py:attribute:: mtbf


   .. py:attribute:: mttr


   .. py:attribute:: energy_rate


   .. py:attribute:: state


   .. py:attribute:: previous_state


   .. py:attribute:: state_start_time
      :value: 0.0



   .. py:attribute:: total_runtime
      :value: 0.0



   .. py:attribute:: cycles_since_maintenance
      :value: 0



   .. py:attribute:: units_produced
      :value: 0



   .. py:attribute:: units_scrapped
      :value: 0



   .. py:attribute:: current_product


   .. py:attribute:: current_order


   .. py:attribute:: current_shift
      :type:  Optional[str]
      :value: None



   .. py:attribute:: performance_factor
      :value: 1.0



   .. py:attribute:: quality_factor
      :value: 1.0



   .. py:attribute:: failure_modes
      :value: []



   .. py:attribute:: energy_consumed
      :value: 0.0



   .. py:attribute:: context_history
      :type:  List[Dict[str, Any]]
      :value: []



   .. py:method:: start() -> None

      Start the equipment process and failure process.



   .. py:method:: run() -> Generator

      Main equipment process for production.



   .. py:method:: failure_process() -> Generator

      Background process for random failures.



   .. py:method:: monitor_process() -> Generator

      Background process for periodic monitoring.



   .. py:method:: calculate_oee() -> float

      Calculate Overall Equipment Effectiveness.

      :returns: OEE percentage (0-100)



   .. py:method:: set_product(product_id: str, order_id: str) -> None

      Set current product being processed.

      :param product_id: Product identifier
      :param order_id: Production order identifier



   .. py:method:: set_shift(shift_id: str) -> None

      Set current shift.

      :param shift_id: Shift identifier



.. py:class:: EquipmentState

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Possible equipment states with detailed categorization.

   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: RUNNING
      :value: 'RUNNING'



   .. py:attribute:: STOPPED_FAILURE
      :value: 'STOPPED_FAILURE'



   .. py:attribute:: STOPPED_MAINTENANCE
      :value: 'STOPPED_MAINTENANCE'



   .. py:attribute:: STARVED
      :value: 'STARVED'



   .. py:attribute:: BLOCKED
      :value: 'BLOCKED'



   .. py:attribute:: IDLE
      :value: 'IDLE'



   .. py:attribute:: CHANGEOVER
      :value: 'CHANGEOVER'



   .. py:attribute:: STARTUP
      :value: 'STARTUP'



   .. py:attribute:: SHUTDOWN
      :value: 'SHUTDOWN'



.. py:class:: Buffer(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig)

   Bases: :py:obj:`twin_model.primitives.base.BasePrimitive`


   Generic buffer for material storage.

   Emits observables for:
   - Level changes (material in/out)
   - Dwell time distribution
   - Overflow/underflow events
   - Capacity utilization patterns
   - Product mix in buffer

   Initialize buffer with configuration.

   :param env: SimPy environment
   :param config: Buffer configuration containing:
                  - capacity: Maximum buffer capacity (units)
                  - initial_level: Starting inventory level
                  - buffer_type: Type of buffer (FIFO, LIFO, priority)
                  - min_level: Minimum level for warnings
                  - max_dwell_time: Maximum allowed dwell time


   .. py:attribute:: capacity


   .. py:attribute:: initial_level


   .. py:attribute:: buffer_type


   .. py:attribute:: min_level


   .. py:attribute:: max_dwell_time


   .. py:attribute:: total_items_in
      :value: 0



   .. py:attribute:: total_items_out
      :value: 0



   .. py:attribute:: max_level_reached
      :value: 0



   .. py:attribute:: min_level_reached


   .. py:attribute:: overflow_count
      :value: 0



   .. py:attribute:: underflow_count
      :value: 0



   .. py:attribute:: dwell_times
      :type:  List[float]
      :value: []



   .. py:attribute:: level


   .. py:attribute:: last_level_change
      :value: 0.0



   .. py:attribute:: product_counts
      :type:  Dict[str, int]


   .. py:method:: start() -> None

      Start buffer monitoring processes.



   .. py:method:: put(quantity: int = 1, product_id: Optional[str] = None, **kwargs) -> Generator

      Put items into buffer.

      :param quantity: Number of items to add
      :param product_id: Product identifier
      :param \*\*kwargs: Additional item metadata

      :Yields: Store put event



   .. py:method:: get(quantity: int = 1) -> Any

      Get items from buffer.

      :param quantity: Number of items to retrieve

      :Yields: Store get event

      :returns: List of retrieved items



   .. py:method:: monitor_process() -> Generator

      Background process for buffer monitoring.



   .. py:method:: is_full() -> bool

      Check if buffer is at capacity.

      :returns: True if buffer is full



   .. py:method:: is_empty() -> bool

      Check if buffer is empty.

      :returns: True if buffer is empty



   .. py:method:: get_utilization() -> float

      Get current buffer utilization.

      :returns: Utilization percentage (0-100)



   .. py:method:: get_statistics() -> Dict[str, Any]

      Get buffer statistics.

      :returns: Dictionary of buffer metrics



   .. py:method:: flush() -> List[BufferItem]

      Remove all items from buffer (e.g., for changeover).

      :returns: List of flushed items



.. py:class:: BufferItem

   Item stored in buffer with metadata for tracking.

   .. attribute:: product_id

      Product identifier

   .. attribute:: entry_time

      Simulation time when item entered buffer

   .. attribute:: quality

      Quality status (good/scrap)

   .. attribute:: metadata

      Additional item-specific data


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: entry_time
      :type:  float


   .. py:attribute:: quality
      :type:  str
      :value: 'good'



   .. py:attribute:: metadata
      :type:  Dict[str, Any]


.. py:class:: Source(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, downstream: Optional[Any] = None)

   Bases: :py:obj:`twin_model.primitives.base.BasePrimitive`


   Generic source that generates materials.

   Emits observables for:
   - Material generation events
   - Arrival pattern variations
   - Batch characteristics
   - Supply disruptions
   - Schedule adherence

   Initialize source with configuration.

   :param env: SimPy environment
   :param config: Source configuration containing:
                  - arrival_pattern: Type of arrival pattern
                  - arrival_rate: Base rate for arrivals (units/minute)
                  - batch_size: Size of batches if batch pattern
                  - schedule: Arrival schedule if scheduled pattern
                  - disruption_probability: Chance of supply disruption
   :param downstream: Output buffer or equipment


   .. py:attribute:: downstream
      :value: None



   .. py:attribute:: arrival_pattern


   .. py:attribute:: arrival_rate


   .. py:attribute:: batch_size


   .. py:attribute:: schedule


   .. py:attribute:: disruption_probability


   .. py:attribute:: product_mix


   .. py:attribute:: current_product
      :value: None



   .. py:attribute:: total_generated
      :value: 0



   .. py:attribute:: total_batches
      :value: 0



   .. py:attribute:: disruption_count
      :value: 0



   .. py:attribute:: blocked_count
      :value: 0



   .. py:attribute:: quality_rate


   .. py:attribute:: supply_variability


   .. py:method:: start() -> None

      Start the source generation process.



   .. py:method:: generate() -> Generator

      Main generation process for materials.



   .. py:method:: disruption_process() -> Generator

      Background process for random supply disruptions.



   .. py:method:: set_arrival_rate(rate: float) -> None

      Dynamically adjust arrival rate.

      :param rate: New arrival rate (units/minute)



   .. py:method:: set_product_mix(mix: Dict[str, float]) -> None

      Update product mix.

      :param mix: Dictionary of product IDs to weights



   .. py:method:: get_statistics() -> Dict[str, Any]

      Get source statistics.

      :returns: Dictionary of source metrics



.. py:class:: ArrivalPattern

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Types of arrival patterns for source generation.

   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: CONSTANT
      :value: 'CONSTANT'



   .. py:attribute:: EXPONENTIAL
      :value: 'EXPONENTIAL'



   .. py:attribute:: NORMAL
      :value: 'NORMAL'



   .. py:attribute:: BATCH
      :value: 'BATCH'



   .. py:attribute:: SCHEDULE
      :value: 'SCHEDULE'



   .. py:attribute:: STOCHASTIC
      :value: 'STOCHASTIC'



.. py:class:: Sink(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, upstream: Optional[Any] = None)

   Bases: :py:obj:`twin_model.primitives.base.BasePrimitive`


   Generic sink that collects finished products.

   Emits observables for:
   - Product collection events
   - Throughput metrics
   - Quality statistics
   - Order fulfillment
   - Delivery performance

   Initialize sink with configuration.

   :param env: SimPy environment
   :param config: Sink configuration containing:
                  - collection_rate: Maximum collection rate (units/minute)
                  - quality_threshold: Minimum quality score for acceptance
                  - target_throughput: Expected throughput for KPI
                  - order_tracking: Whether to track order fulfillment
   :param upstream: Input buffer or equipment


   .. py:attribute:: upstream
      :value: None



   .. py:attribute:: collection_rate


   .. py:attribute:: quality_threshold


   .. py:attribute:: target_throughput


   .. py:attribute:: order_tracking


   .. py:attribute:: collected_products
      :type:  List[CollectedProduct]
      :value: []



   .. py:attribute:: total_collected
      :value: 0



   .. py:attribute:: total_rejected
      :value: 0



   .. py:attribute:: products_by_type
      :type:  Dict[str, int]


   .. py:attribute:: products_by_order
      :type:  Dict[str, int]


   .. py:attribute:: throughput_history
      :type:  List[float]
      :value: []



   .. py:attribute:: quality_history
      :type:  List[float]
      :value: []



   .. py:attribute:: pending_orders
      :type:  Dict[str, Dict[str, Any]]


   .. py:attribute:: completed_orders
      :type:  List[Dict[str, Any]]
      :value: []



   .. py:method:: start() -> None

      Start the sink collection process.



   .. py:method:: collect() -> Generator

      Main collection process for products.



   .. py:method:: monitor_process() -> Generator

      Background monitoring process.



   .. py:method:: get_statistics() -> Dict[str, Any]

      Get sink statistics.

      :returns: Dictionary of sink metrics



   .. py:method:: get_order_metrics() -> Dict[str, Any]

      Get order fulfillment metrics.

      :returns: Dictionary of order-related metrics



.. py:class:: CollectedProduct

   Product collected by sink with metadata.

   .. attribute:: product_id

      Product identifier

   .. attribute:: order_id

      Associated production order

   .. attribute:: collection_time

      Simulation time when collected

   .. attribute:: quality

      Quality status

   .. attribute:: lead_time

      Time from order to collection

   .. attribute:: metadata

      Additional product data


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: order_id
      :type:  Optional[str]


   .. py:attribute:: collection_time
      :type:  float


   .. py:attribute:: quality
      :type:  str
      :value: 'good'



   .. py:attribute:: lead_time
      :type:  Optional[float]
      :value: None



   .. py:attribute:: metadata
      :type:  Dict[str, Any]


.. py:class:: Scheduler(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig)

   Bases: :py:obj:`twin_model.primitives.base.BasePrimitive`


   Scheduler for coordinating production activities.

   Emits observables for:
   - Order scheduling and completion
   - Changeover events
   - Shift transitions
   - Schedule adherence metrics
   - Order tardiness
   - Resource conflicts

   Initialize scheduler with configuration.

   :param env: SimPy environment
   :param config: Scheduler configuration containing:
                  - schedule_horizon: Planning horizon in minutes
                  - changeover_matrix: Product-to-product changeover times
                  - shift_schedule: Shift timing configuration
                  - maintenance_schedule: Planned maintenance windows
                  - optimization_mode: Scheduling algorithm to use


   .. py:attribute:: schedule_horizon


   .. py:attribute:: changeover_matrix


   .. py:attribute:: shift_schedule


   .. py:attribute:: maintenance_schedule


   .. py:attribute:: optimization_mode


   .. py:attribute:: schedule_events
      :type:  List[ScheduleEvent]
      :value: []



   .. py:attribute:: production_orders
      :type:  Dict[str, ProductionOrder]


   .. py:attribute:: active_order
      :type:  Optional[ProductionOrder]
      :value: None



   .. py:attribute:: orders_scheduled
      :value: 0



   .. py:attribute:: orders_completed
      :value: 0



   .. py:attribute:: total_changeover_time
      :type:  float
      :value: 0.0



   .. py:attribute:: schedule_adherence
      :value: 1.0



   .. py:attribute:: tardiness_total
      :type:  float
      :value: 0.0



   .. py:attribute:: current_product
      :type:  Optional[str]
      :value: None



   .. py:attribute:: current_shift
      :type:  Optional[str]
      :value: None



   .. py:attribute:: current_line
      :type:  Optional[str]
      :value: None



   .. py:attribute:: controlled_equipment
      :type:  Dict[str, Any]


   .. py:method:: start() -> None

      Start the scheduler process.



   .. py:method:: schedule_process() -> Generator

      Main scheduling process.



   .. py:method:: register_equipment(equipment_id: str, equipment: Any) -> None

      Register equipment to be controlled by scheduler.

      :param equipment_id: Equipment identifier
      :param equipment: Equipment primitive instance



   .. py:method:: add_order(order: ProductionOrder) -> None

      Add a production order to the schedule.

      :param order: Production order to add



   .. py:method:: load_schedule(schedule_data: List[Dict[str, Any]]) -> None

      Load a complete schedule.

      :param schedule_data: List of schedule events



   .. py:method:: optimize_schedule() -> None

      Optimize the current schedule based on mode.



   .. py:method:: monitor_process() -> Generator

      Background monitoring process.



   .. py:method:: get_statistics() -> Dict[str, Any]

      Get scheduler statistics.

      :returns: Dictionary of scheduler metrics



.. py:class:: ScheduleEvent

   A scheduled event in the production schedule.

   .. attribute:: event_type

      Type of scheduled event

   .. attribute:: start_time

      Scheduled start time (minutes from sim start)

   .. attribute:: duration

      Expected duration in minutes

   .. attribute:: product_id

      Product ID for production orders

   .. attribute:: order_id

      Production order ID

   .. attribute:: line_id

      Production line affected

   .. attribute:: priority

      Priority level (lower = higher priority)

   .. attribute:: metadata

      Additional event-specific data


   .. py:attribute:: event_type
      :type:  ScheduleEventType


   .. py:attribute:: start_time
      :type:  float


   .. py:attribute:: duration
      :type:  float


   .. py:attribute:: product_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: order_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: line_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: priority
      :type:  int
      :value: 5



   .. py:attribute:: metadata
      :type:  Dict[str, Any]


.. py:class:: ScheduleEventType

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Types of schedule events.

   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: PRODUCTION_ORDER
      :value: 'PRODUCTION_ORDER'



   .. py:attribute:: CHANGEOVER
      :value: 'CHANGEOVER'



   .. py:attribute:: MAINTENANCE
      :value: 'MAINTENANCE'



   .. py:attribute:: SHIFT_CHANGE
      :value: 'SHIFT_CHANGE'



   .. py:attribute:: BREAK
      :value: 'BREAK'



   .. py:attribute:: SHUTDOWN
      :value: 'SHUTDOWN'



.. py:class:: ProductionOrder

   Production order details.

   .. attribute:: order_id

      Unique order identifier

   .. attribute:: product_id

      Product to produce

   .. attribute:: target_quantity

      Target production quantity

   .. attribute:: due_time

      Due date/time for order completion

   .. attribute:: line_id

      Assigned production line

   .. attribute:: priority

      Order priority

   .. attribute:: status

      Current order status


   .. py:attribute:: order_id
      :type:  str


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: target_quantity
      :type:  int


   .. py:attribute:: due_time
      :type:  float


   .. py:attribute:: line_id
      :type:  str


   .. py:attribute:: priority
      :type:  int
      :value: 5



   .. py:attribute:: status
      :type:  str
      :value: 'pending'



   .. py:attribute:: actual_quantity
      :type:  int
      :value: 0



   .. py:attribute:: start_time
      :type:  Optional[float]
      :value: None



   .. py:attribute:: end_time
      :type:  Optional[float]
      :value: None



.. py:class:: Monitor(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig)

   Bases: :py:obj:`twin_model.primitives.base.BasePrimitive`


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


   .. py:attribute:: update_interval


   .. py:attribute:: aggregation_window


   .. py:attribute:: alert_thresholds


   .. py:attribute:: kpis
      :type:  Dict[str, KPIMetric]


   .. py:attribute:: monitored_primitives
      :type:  Dict[str, Any]


   .. py:attribute:: active_alerts
      :type:  List[Dict[str, Any]]
      :value: []



   .. py:attribute:: alert_history
      :type:  List[Dict[str, Any]]
      :value: []



   .. py:attribute:: line_metrics
      :type:  Dict[str, Dict[str, float]]


   .. py:attribute:: product_metrics
      :type:  Dict[str, Dict[str, float]]


   .. py:attribute:: shift_metrics
      :type:  Dict[str, Dict[str, float]]


   .. py:method:: start() -> None

      Start the monitoring process.



   .. py:method:: monitor_process() -> Generator

      Main monitoring process.



   .. py:method:: alert_process() -> Generator

      Process for managing alerts.



   .. py:method:: register_primitive(name: str, primitive: Any) -> None

      Register a primitive to monitor.

      :param name: Primitive identifier
      :param primitive: Primitive instance



   .. py:method:: get_kpi_value(kpi_name: str) -> Optional[float]

      Get current value of a KPI.

      :param kpi_name: Name of KPI

      :returns: Current KPI value or None



   .. py:method:: get_kpi_history(kpi_name: str, window: Optional[float] = None) -> List[Tuple[float, float]]

      Get historical values of a KPI.

      :param kpi_name: Name of KPI
      :param window: Time window to retrieve

      :returns: List of (timestamp, value) tuples



   .. py:method:: get_dashboard() -> Dict[str, Any]

      Get dashboard summary of all metrics.

      :returns: Dictionary with dashboard data



   .. py:method:: get_statistics() -> Dict[str, Any]

      Get monitor statistics.

      :returns: Dictionary of monitor metrics



.. py:class:: KPIType

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Types of KPIs tracked.

   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: OEE
      :value: 'OEE'



   .. py:attribute:: AVAILABILITY
      :value: 'AVAILABILITY'



   .. py:attribute:: PERFORMANCE
      :value: 'PERFORMANCE'



   .. py:attribute:: QUALITY
      :value: 'QUALITY'



   .. py:attribute:: THROUGHPUT
      :value: 'THROUGHPUT'



   .. py:attribute:: CYCLE_TIME
      :value: 'CYCLE_TIME'



   .. py:attribute:: LEAD_TIME
      :value: 'LEAD_TIME'



   .. py:attribute:: SCRAP_RATE
      :value: 'SCRAP_RATE'



   .. py:attribute:: ENERGY_CONSUMPTION
      :value: 'ENERGY_CONSUMPTION'



   .. py:attribute:: MTBF
      :value: 'MTBF'



   .. py:attribute:: MTTR
      :value: 'MTTR'



   .. py:attribute:: UTILIZATION
      :value: 'UTILIZATION'



.. py:class:: KPIMetric

   A KPI metric with history.

   .. attribute:: name

      KPI name

   .. attribute:: type

      KPI type

   .. attribute:: value

      Current value

   .. attribute:: target

      Target value

   .. attribute:: history

      Historical values

   .. attribute:: unit

      Measurement unit

   .. attribute:: aggregation

      How to aggregate (avg, sum, max, min)


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: type
      :type:  KPIType


   .. py:attribute:: value
      :type:  float
      :value: 0.0



   .. py:attribute:: target
      :type:  Optional[float]
      :value: None



   .. py:attribute:: history
      :type:  List[Tuple[float, float]]
      :value: []



   .. py:attribute:: unit
      :type:  str
      :value: ''



   .. py:attribute:: aggregation
      :type:  str
      :value: 'avg'



   .. py:method:: add_value(timestamp: float, value: float) -> None

      Add a value to history.



   .. py:method:: get_average(window: Optional[float] = None, current_time: Optional[float] = None) -> float

      Get average value over time window.



   .. py:method:: get_trend() -> str

      Get trend direction.



.. py:class:: OntologyDrivenModelBuilder(ontology_path: pathlib.Path, manifest_dir: Optional[pathlib.Path] = None)

   Builds SimPy models from ontology structure and manifests.

   This builder interprets the twin ontology to construct a simulation model,
   then configures it with values from manifests. It maintains separation
   between structure (ontology) and configuration (manifests).

   Initialize builder with ontology and manifest directory.

   :param ontology_path: Path to twin_ontology.yaml
   :param manifest_dir: Directory containing manifest files (optional)


   .. py:attribute:: PRIMITIVE_CLASSES


   .. py:attribute:: ontology_path


   .. py:attribute:: manifest_dir
      :value: None



   .. py:attribute:: ontology


   .. py:attribute:: manifests


   .. py:attribute:: entities
      :type:  Dict[str, ModelEntity]


   .. py:attribute:: primitives
      :type:  Dict[str, twin_model.primitives.BasePrimitive]


   .. py:attribute:: production_lines
      :type:  Dict[str, Dict[str, Any]]


   .. py:method:: build_model(env: simpy.Environment) -> Dict[str, Any]

      Build complete simulation model from ontology.

      :param env: SimPy environment for the model

      :returns:     - primitives: Instantiated primitive objects
                    - lines: Production line configurations
                    - scheduler: Scheduler primitive if created
                    - monitor: Monitor primitive if created
      :rtype: Dictionary containing



   .. py:method:: get_controllable_parameters() -> Dict[str, Any]

      Get controllable parameters from ontology.

      :returns: Dictionary of parameter names to definitions



   .. py:method:: apply_parameter_changes(parameters: Dict[str, float]) -> None

      Apply parameter changes to running model.

      :param parameters: Dictionary of parameter name to value



   .. py:method:: get_observables() -> Dict[str, List[Dict[str, Any]]]

      Get all observables from primitives.

      :returns: Dictionary of primitive ID to observable list



   .. py:method:: get_model_structure() -> Dict[str, Any]

      Get model structure for analysis.

      :returns: Dictionary describing model structure



.. py:class:: MESTransducer(time_bucket: int = 5)

   Converts SimPy observables to MES data format.

   The transducer extracts MES-visible events from the comprehensive
   observable stream and formats them into the standard MES structure.

   Initialize MES transducer.

   :param time_bucket: Time bucket in minutes (default 5 for 5-minute intervals)


   .. py:attribute:: time_bucket
      :value: 5



   .. py:attribute:: mes_records
      :type:  List[Dict[str, Any]]
      :value: []



   .. py:attribute:: equipment_states
      :type:  Dict[str, Dict[str, Any]]


   .. py:attribute:: bucket_metrics
      :type:  Dict[Tuple[int, str], Dict[str, Any]]


   .. py:method:: process_observables(observables: List[Dict[str, Any]], manifests: Optional[Dict[str, Any]] = None) -> pandas.DataFrame

      Process observables into MES format.

      :param observables: List of observable events from simulation
      :param manifests: Optional manifests for product/equipment details

      :returns: DataFrame in MES format



   .. py:method:: save_to_csv(df: pandas.DataFrame, filepath: pathlib.Path) -> None

      Save MES data to CSV file.

      :param df: MES DataFrame
      :param filepath: Output file path



   .. py:method:: generate_summary_statistics(df: pandas.DataFrame) -> Dict[str, Any]

      Generate summary statistics from MES data.

      :param df: MES DataFrame

      :returns: Dictionary of summary statistics



