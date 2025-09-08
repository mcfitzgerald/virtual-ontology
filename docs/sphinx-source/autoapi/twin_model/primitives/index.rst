twin_model.primitives
=====================

.. py:module:: twin_model.primitives

.. autoapi-nested-parse::

   Flow primitives for container-based continuous flow simulation.



Submodules
----------

.. toctree::
   :maxdepth: 1

   /autoapi/twin_model/primitives/base_flow/index
   /autoapi/twin_model/primitives/equipment_flow/index
   /autoapi/twin_model/primitives/sink_flow/index
   /autoapi/twin_model/primitives/source_flow/index


Classes
-------

.. autoapisummary::

   twin_model.primitives.BaseFlowPrimitive
   twin_model.primitives.FlowCapacity
   twin_model.primitives.FlowMetrics
   twin_model.primitives.FlowState
   twin_model.primitives.EquipmentFlow
   twin_model.primitives.FailureParameters
   twin_model.primitives.ProcessingParameters
   twin_model.primitives.OEEMetrics
   twin_model.primitives.ProductionWindow
   twin_model.primitives.SinkFlow
   twin_model.primitives.ProductionOrder
   twin_model.primitives.SourceFlow


Package Contents
----------------

.. py:class:: BaseFlowPrimitive(env: simpy.Environment, config: dict[str, Any], flow_capacity: FlowCapacity)

   Bases: :py:obj:`abc.ABC`


   Base class for all flow-based primitives.


   .. py:attribute:: env


   .. py:attribute:: config


   .. py:attribute:: flow_capacity


   .. py:attribute:: input_buffer
      :type:  simpy.Container | None
      :value: None



   .. py:attribute:: output_buffer
      :type:  simpy.Container | None
      :value: None



   .. py:attribute:: current_state


   .. py:attribute:: flow_metrics


   .. py:attribute:: observables
      :type:  list[dict[str, Any]]
      :value: []



   .. py:attribute:: downtime_reason
      :type:  str | None
      :value: None



   .. py:attribute:: failure_history
      :type:  list[tuple[float, str]]
      :value: []



   .. py:attribute:: process
      :type:  simpy.Process | None
      :value: None



   .. py:method:: process_flow() -> Generator[Any, None, None]
      :abstractmethod:


      Main flow processing logic.

      Must be implemented by subclasses to define specific
      flow processing behavior.



   .. py:method:: start() -> None

      Start the flow process.



   .. py:method:: change_state(new_state: FlowState, downtime_reason: str | None = None) -> None

      Change current state and update metrics.

      :param new_state: New flow state
      :param downtime_reason: Optional reason for downtime (for FAILED/MAINTENANCE states)



   .. py:method:: emit_observable(event_type: str, data: dict[str, Any]) -> None

      Emit an observable event.

      :param event_type: Type of event
      :param data: Event data



   .. py:method:: get_utilization() -> float

      Calculate equipment utilization.

      :returns: Utilization as percentage (0-100)



   .. py:method:: get_availability() -> float

      Calculate equipment availability.

      :returns: Availability as percentage (0-100)



   .. py:method:: get_performance() -> float

      Calculate equipment performance.

      :returns: Performance as percentage (0-100), capped at 110%



   .. py:method:: get_quality() -> float

      Calculate equipment quality.

      :returns: Quality as percentage (0-100)



   .. py:method:: get_oee() -> float

      Calculate Overall Equipment Effectiveness.

      :returns: OEE as percentage (0-100)



   .. py:property:: state
      :type: FlowState


      Current flow state.


   .. py:property:: total_input
      :type: float


      Total input processed.


   .. py:property:: total_output
      :type: float


      Total good output produced.


   .. py:property:: total_scrap
      :type: float


      Total scrap produced.


   .. py:property:: state_durations
      :type: dict[FlowState, float]


      State duration tracking.


.. py:class:: FlowCapacity

   Defines flow capacity constraints for equipment.


   .. py:attribute:: max_input_rate
      :type:  float


   .. py:attribute:: max_output_rate
      :type:  float


   .. py:attribute:: internal_capacity
      :type:  float


   .. py:attribute:: initial_level
      :type:  float
      :value: 0.0



.. py:class:: FlowMetrics

   Tracks flow metrics for analysis.


   .. py:attribute:: total_input
      :type:  float
      :value: 0.0



   .. py:attribute:: total_output
      :type:  float
      :value: 0.0



   .. py:attribute:: total_scrap
      :type:  float
      :value: 0.0



   .. py:attribute:: total_downtime
      :type:  float
      :value: 0.0



   .. py:attribute:: state_durations
      :type:  dict[FlowState, float]


   .. py:attribute:: last_state_change
      :type:  float
      :value: 0.0



   .. py:method:: update_state_duration(old_state: FlowState, new_time: float) -> None

      Update duration tracking for state changes.



.. py:class:: FlowState(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Equipment flow states.


   .. py:attribute:: IDLE
      :value: 'idle'



   .. py:attribute:: FLOWING
      :value: 'flowing'



   .. py:attribute:: STARVED_UPSTREAM
      :value: 'starved_upstream'



   .. py:attribute:: BLOCKED_DOWNSTREAM
      :value: 'blocked_downstream'



   .. py:attribute:: FAILED
      :value: 'failed'



   .. py:attribute:: MAINTENANCE
      :value: 'maintenance'



   .. py:attribute:: CHANGEOVER
      :value: 'changeover'



.. py:class:: EquipmentFlow(env: simpy.Environment, config: dict[str, Any], flow_capacity: twin_model.primitives.base_flow.FlowCapacity, processing: ProcessingParameters, failures: FailureParameters)

   Bases: :py:obj:`twin_model.primitives.base_flow.BaseFlowPrimitive`


   Equipment with continuous flow processing.


   .. py:attribute:: processing


   .. py:attribute:: failures


   .. py:attribute:: internal_buffer


   .. py:attribute:: is_failed
      :value: False



   .. py:attribute:: is_processing
      :value: False



   .. py:attribute:: current_product


   .. py:method:: process_flow() -> Generator[Any, None, None]

      Process material in continuous batches.



   .. py:method:: failure_process() -> Generator[Any, None, None]

      Simulate random failures.



   .. py:method:: micro_stop_process() -> Generator[Any, None, None]

      Simulate micro-stops.



   .. py:method:: changeover(new_product: str, changeover_time: float) -> Generator[Any, None, None]

      Perform product changeover.

      :param new_product: New product identifier
      :param changeover_time: Time required for changeover (minutes)



.. py:class:: FailureParameters

   Equipment failure parameters.


   .. py:attribute:: mtbf
      :type:  float


   .. py:attribute:: mttr
      :type:  float


   .. py:attribute:: micro_stop_rate
      :type:  float


   .. py:attribute:: micro_stop_duration
      :type:  float


.. py:class:: ProcessingParameters

   Equipment processing parameters.


   .. py:attribute:: nominal_rate
      :type:  float


   .. py:attribute:: quality_rate
      :type:  float


   .. py:attribute:: performance_factor
      :type:  float


   .. py:attribute:: batch_size
      :type:  float


   .. py:attribute:: processing_interval
      :type:  float


.. py:class:: OEEMetrics

   OEE metrics for a time period.


   .. py:attribute:: oee
      :type:  float


   .. py:attribute:: availability
      :type:  float


   .. py:attribute:: performance
      :type:  float


   .. py:attribute:: quality
      :type:  float


   .. py:attribute:: timestamp
      :type:  float


   .. py:attribute:: window_duration
      :type:  float


   .. py:method:: to_dict() -> dict[str, float]

      Convert to dictionary.



.. py:class:: ProductionWindow

   Represents a production time window for metrics calculation.


   .. py:attribute:: timestamp
      :type:  float


   .. py:attribute:: duration
      :type:  float


   .. py:attribute:: volume
      :type:  float


   .. py:attribute:: good_volume
      :type:  float


   .. py:attribute:: scrap_volume
      :type:  float


   .. py:attribute:: downtime
      :type:  float


   .. py:attribute:: product_id
      :type:  str
      :value: 'default'



   .. py:property:: quality_rate
      :type: float


      Calculate quality rate for this window.


.. py:class:: SinkFlow(env: simpy.Environment, config: dict[str, Any], flow_capacity: twin_model.primitives.base_flow.FlowCapacity, collection_rate: float, collection_interval: float = 0.1)

   Bases: :py:obj:`twin_model.primitives.base_flow.BaseFlowPrimitive`


   Sink collecting finished products and calculating OEE.


   .. py:attribute:: collection_rate


   .. py:attribute:: collection_interval
      :value: 0.1



   .. py:attribute:: total_collected
      :value: 0.0



   .. py:attribute:: total_good
      :value: 0.0



   .. py:attribute:: production_windows
      :type:  list[ProductionWindow]
      :value: []



   .. py:attribute:: current_window_start
      :value: 0.0



   .. py:attribute:: window_duration


   .. py:attribute:: oee_history
      :type:  list[OEEMetrics]
      :value: []



   .. py:attribute:: products_collected
      :type:  dict[str, float]


   .. py:attribute:: current_product


   .. py:attribute:: nominal_rate


   .. py:attribute:: upstream_equipment
      :type:  list[Any]
      :value: []



   .. py:method:: process_flow() -> Generator[Any, None, None]

      Collect products and track metrics.



   .. py:method:: window_tracker() -> Generator[Any, None, None]

      Track production windows for OEE calculation.



   .. py:method:: calculate_oee(window_minutes: float = 60) -> tuple[float, float, float, float]

      Calculate OEE components for time window.

      :param window_minutes: Time window in minutes

      :returns: Tuple of (OEE, Availability, Performance, Quality) as percentages



   .. py:method:: get_production_summary() -> dict[str, Any]

      Get production summary statistics.

      :returns: Dictionary with production summary



   .. py:method:: set_product(product_id: str) -> None

      Set current product being collected.

      :param product_id: Product identifier



.. py:class:: ProductionOrder

   Production order for material generation.


   .. py:attribute:: order_id
      :type:  str


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: target_volume
      :type:  float


   .. py:attribute:: due_time
      :type:  float


   .. py:attribute:: priority
      :type:  int
      :value: 0



   .. py:attribute:: completed_volume
      :type:  float
      :value: 0.0



   .. py:property:: remaining_volume
      :type: float


      Calculate remaining volume to complete.


   .. py:property:: completion_percentage
      :type: float


      Calculate order completion percentage.


.. py:class:: SourceFlow(env: simpy.Environment, config: dict[str, Any], flow_capacity: twin_model.primitives.base_flow.FlowCapacity, generation_rate: float, generation_interval: float = 0.1)

   Bases: :py:obj:`twin_model.primitives.base_flow.BaseFlowPrimitive`


   Source generating continuous material flow.


   .. py:attribute:: generation_rate


   .. py:attribute:: generation_interval
      :value: 0.1



   .. py:attribute:: order_queue
      :type:  list[ProductionOrder]
      :value: []



   .. py:attribute:: current_order
      :type:  ProductionOrder | None
      :value: None



   .. py:attribute:: completed_orders
      :type:  list[ProductionOrder]
      :value: []



   .. py:attribute:: continuous_mode


   .. py:attribute:: default_product


   .. py:method:: process_flow() -> Generator[Any, None, None]

      Generate material based on orders or continuously.



   .. py:method:: add_order(order: ProductionOrder) -> None

      Add a production order to the queue.

      :param order: Production order to add



   .. py:method:: cancel_order(order_id: str) -> bool

      Cancel a production order.

      :param order_id: ID of order to cancel

      :returns: True if order was cancelled, False if not found



   .. py:method:: get_queue_status() -> dict[str, Any]

      Get current queue status.

      :returns: Dictionary with queue status information



