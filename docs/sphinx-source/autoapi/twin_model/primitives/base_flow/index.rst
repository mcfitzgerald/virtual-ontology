twin_model.primitives.base_flow
===============================

.. py:module:: twin_model.primitives.base_flow

.. autoapi-nested-parse::

   Base flow primitive for container-based continuous flow simulation.

   This module provides the foundation for all flow-based simulation primitives
   using SimPy Containers exclusively for continuous flow modeling.



Classes
-------

.. autoapisummary::

   twin_model.primitives.base_flow.FlowCapacity
   twin_model.primitives.base_flow.FlowState
   twin_model.primitives.base_flow.FlowMetrics
   twin_model.primitives.base_flow.BaseFlowPrimitive


Module Contents
---------------

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


