twin_model.primitives.equipment
===============================

.. py:module:: twin_model.primitives.equipment

.. autoapi-nested-parse::

   Equipment primitive for processing materials in manufacturing.

   This module provides a generic equipment primitive that can represent
   any type of processing equipment (Filler, Packer, Palletizer, etc.).
   It emits rich observables for pattern discovery including state transitions,
   production events, failures, and performance variations.



Classes
-------

.. autoapisummary::

   twin_model.primitives.equipment.EquipmentState
   twin_model.primitives.equipment.FailureMode
   twin_model.primitives.equipment.EquipmentPrimitive


Module Contents
---------------

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



.. py:class:: FailureMode

   Definition of a failure mode for equipment.

   .. attribute:: name

      Failure mode identifier (micro_stop, major_failure, etc.)

   .. attribute:: probability_per_5min

      Probability of occurrence per time interval

   .. attribute:: duration_range

      Min and max duration in minutes

   .. attribute:: downtime_code

      Associated downtime reason code

   .. attribute:: cascade_probability

      Probability of causing downstream failures

   .. attribute:: recovery_time_factor

      Multiplier for recovery time based on context


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: probability_per_5min
      :type:  float


   .. py:attribute:: duration_range
      :type:  Tuple[float, float]


   .. py:attribute:: downtime_code
      :type:  str


   .. py:attribute:: cascade_probability
      :type:  float
      :value: 0.0



   .. py:attribute:: recovery_time_factor
      :type:  float
      :value: 1.0



.. py:class:: EquipmentPrimitive(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig, upstream: Optional[Any] = None, downstream: Optional[Any] = None, sampling_config: Optional[twin_model.primitives.base.SamplingConfig] = None)

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



