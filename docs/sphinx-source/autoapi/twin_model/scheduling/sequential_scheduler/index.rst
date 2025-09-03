twin_model.scheduling.sequential_scheduler
==========================================

.. py:module:: twin_model.scheduling.sequential_scheduler

.. autoapi-nested-parse::

   Sequential scheduler implementation.

   Simple FIFO scheduling algorithm that processes orders in sequence,
   respecting line compatibility and basic constraints.



Attributes
----------

.. autoapisummary::

   twin_model.scheduling.sequential_scheduler.logger


Classes
-------

.. autoapisummary::

   twin_model.scheduling.sequential_scheduler.SequentialScheduler


Module Contents
---------------

.. py:data:: logger

.. py:class:: SequentialScheduler(config: Optional[twin_model.scheduling.base_scheduler.SchedulerConfig] = None, constraints: Optional[twin_model.scheduling.base_scheduler.SchedulingConstraints] = None, product_manifest: Optional[twin_model.scheduling.product_manifest.ProductManifest] = None)

   Bases: :py:obj:`twin_model.scheduling.base_scheduler.BaseScheduler`


   Sequential FIFO scheduler implementation.

   Schedules orders in priority/FIFO order, respecting line compatibility
   and maintenance windows.


   .. py:attribute:: config


   .. py:attribute:: constraints


   .. py:attribute:: product_manifest
      :value: None



   .. py:attribute:: current_orders
      :type:  Dict[str, twin_model.scheduling.production_scheduler.ProductionOrder]


   .. py:attribute:: completed_orders
      :type:  List[twin_model.scheduling.production_scheduler.ProductionOrder]
      :value: []



   .. py:attribute:: line_schedules
      :type:  Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]


   .. py:method:: generate_schedule(orders: List[twin_model.scheduling.production_scheduler.ProductionOrder], lines: List[str], horizon_hours: Optional[float] = None, start_time: float = 0.0) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]

      Generate schedule using sequential FIFO algorithm.

      :param orders: List of production orders to schedule
      :param lines: Available production lines
      :param horizon_hours: Planning horizon in hours
      :param start_time: Start time for scheduling (simulation minutes)

      :returns: Schedule by line



   .. py:method:: optimize_schedule(current_schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]], cost_calculator: Optional[Any] = None) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]

      Optimize existing schedule (no-op for sequential scheduler).

      Sequential scheduler doesn't optimize, just returns current schedule.

      :param current_schedule: Current schedule to optimize
      :param cost_calculator: Cost calculator for evaluation

      :returns: Same schedule (no optimization)



   .. py:method:: reschedule(disruption_time: float, disruption_type: str, affected_resources: List[str], current_schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]

      Reschedule after disruption.

      :param disruption_time: When disruption occurred (simulation time)
      :param disruption_type: Type of disruption
      :param affected_resources: Affected lines/resources
      :param current_schedule: Current schedule

      :returns: Updated schedule



   .. py:method:: get_metrics() -> Dict[str, Any]

      Get scheduler performance metrics.

      :returns: Metrics dictionary



