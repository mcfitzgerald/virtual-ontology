twin_model.scheduling.scheduler_integration
===========================================

.. py:module:: twin_model.scheduling.scheduler_integration

.. autoapi-nested-parse::

   Integration module for schedulers with SimPy simulation.

   Connects scheduling algorithms to the simulation environment,
   managing order dispatch and tracking.



Attributes
----------

.. autoapisummary::

   twin_model.scheduling.scheduler_integration.logger


Classes
-------

.. autoapisummary::

   twin_model.scheduling.scheduler_integration.SchedulerSimulationBridge


Module Contents
---------------

.. py:data:: logger

.. py:class:: SchedulerSimulationBridge(env: simpy.Environment, scheduler_type: str = 'sequential', config: Optional[twin_model.scheduling.base_scheduler.SchedulerConfig] = None, constraints: Optional[twin_model.scheduling.base_scheduler.SchedulingConstraints] = None, product_manifest: Optional[twin_model.scheduling.product_manifest.ProductManifest] = None)

   Bridge between schedulers and SimPy simulation.

   Manages the interaction between scheduling algorithms and
   the simulation environment, handling order dispatch and tracking.


   .. py:attribute:: env


   .. py:attribute:: config


   .. py:attribute:: constraints


   .. py:attribute:: product_manifest
      :value: None



   .. py:attribute:: scheduler


   .. py:attribute:: cost_calculator
      :value: None



   .. py:attribute:: pending_orders
      :type:  List[twin_model.scheduling.production_scheduler.ProductionOrder]
      :value: []



   .. py:attribute:: active_orders
      :type:  Dict[str, twin_model.scheduling.production_scheduler.ProductionOrder]


   .. py:attribute:: completed_orders
      :type:  List[twin_model.scheduling.production_scheduler.ProductionOrder]
      :value: []



   .. py:attribute:: line_sources
      :type:  Dict[str, twin_model.primitives.source_flow.SourceFlow]


   .. py:attribute:: metrics


   .. py:method:: register_line_source(line_id: str, source: twin_model.primitives.source_flow.SourceFlow) -> None

      Register a source flow for a production line.

      :param line_id: Line identifier
      :param source: SourceFlow instance for the line



   .. py:method:: generate_orders(num_orders: int, products: Optional[List[str]] = None, horizon_hours: float = 168) -> List[twin_model.scheduling.production_scheduler.ProductionOrder]

      Generate random production orders.

      :param num_orders: Number of orders to generate
      :param products: List of product IDs (uses manifest if not provided)
      :param horizon_hours: Planning horizon in hours

      :returns: List of generated orders



   .. py:method:: schedule_orders(orders: Optional[List[twin_model.scheduling.production_scheduler.ProductionOrder]] = None, horizon_hours: Optional[float] = None, optimize: bool = True) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]

      Schedule production orders.

      :param orders: Orders to schedule (uses pending orders if not provided)
      :param horizon_hours: Planning horizon
      :param optimize: Whether to optimize the schedule

      :returns: Schedule by line



   .. py:method:: dispatch_schedule(schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]) -> None

      Dispatch scheduled orders to production lines.

      :param schedule: Schedule to dispatch



   .. py:method:: run_scheduled_production(duration_hours: float = 168) -> None

      Run production according to schedule.

      This is a SimPy process that manages scheduled production.

      :param duration_hours: Duration to run production



   .. py:method:: handle_disruption(disruption_type: str, affected_lines: List[str], duration_minutes: float = 60) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]

      Handle production disruption by rescheduling.

      :param disruption_type: Type of disruption
      :param affected_lines: Affected production lines
      :param duration_minutes: Expected disruption duration

      :returns: Updated schedule



   .. py:method:: get_schedule_metrics() -> Dict[str, Any]

      Get comprehensive scheduling metrics.

      :returns: Metrics dictionary



   .. py:method:: export_schedule(filename: str = 'schedule.csv') -> None

      Export current schedule to CSV file.

      :param filename: Output filename



