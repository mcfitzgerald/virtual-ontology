twin_model.primitives.scheduler
===============================

.. py:module:: twin_model.primitives.scheduler

.. autoapi-nested-parse::

   Scheduler primitive for production order management.

   This module provides a scheduler primitive that manages production orders,
   product changeovers, shift schedules, and maintenance windows. It coordinates
   the timing and sequencing of production activities.



Classes
-------

.. autoapisummary::

   twin_model.primitives.scheduler.ScheduleEventType
   twin_model.primitives.scheduler.ScheduleEvent
   twin_model.primitives.scheduler.ProductionOrder
   twin_model.primitives.scheduler.SchedulerPrimitive


Module Contents
---------------

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



.. py:class:: SchedulerPrimitive(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig)

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



