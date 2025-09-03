twin_model.scheduling.campaign_optimizer
========================================

.. py:module:: twin_model.scheduling.campaign_optimizer

.. autoapi-nested-parse::

   Campaign-based scheduling optimizer.

   Groups orders by product to minimize changeovers and maximize
   campaign efficiency.



Attributes
----------

.. autoapisummary::

   twin_model.scheduling.campaign_optimizer.logger


Classes
-------

.. autoapisummary::

   twin_model.scheduling.campaign_optimizer.Campaign
   twin_model.scheduling.campaign_optimizer.CampaignOptimizer


Module Contents
---------------

.. py:data:: logger

.. py:class:: Campaign

   Represents a production campaign for a single product.


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: orders
      :type:  List[twin_model.scheduling.production_scheduler.ProductionOrder]


   .. py:attribute:: total_volume
      :type:  float


   .. py:attribute:: total_duration
      :type:  float


   .. py:attribute:: line_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: scheduled_start
      :type:  Optional[float]
      :value: None



   .. py:method:: add_order(order: twin_model.scheduling.production_scheduler.ProductionOrder) -> None

      Add order to campaign.



.. py:class:: CampaignOptimizer(config: Optional[twin_model.scheduling.base_scheduler.SchedulerConfig] = None, constraints: Optional[twin_model.scheduling.base_scheduler.SchedulingConstraints] = None, product_manifest: Optional[twin_model.scheduling.product_manifest.ProductManifest] = None)

   Bases: :py:obj:`twin_model.scheduling.base_scheduler.BaseScheduler`


   Campaign-based scheduling optimizer.

   Groups orders by product to create campaigns that minimize
   changeovers and maximize efficiency.


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


   .. py:attribute:: campaigns
      :type:  List[Campaign]
      :value: []



   .. py:method:: generate_schedule(orders: List[twin_model.scheduling.production_scheduler.ProductionOrder], lines: List[str], horizon_hours: Optional[float] = None, start_time: float = 0.0) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]

      Generate schedule using campaign optimization.

      :param orders: List of production orders to schedule
      :param lines: Available production lines
      :param horizon_hours: Planning horizon in hours
      :param start_time: Start time for scheduling (simulation minutes)

      :returns: Schedule by line



   .. py:method:: optimize_schedule(current_schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]], cost_calculator: Optional[twin_model.scheduling.cost_calculator.ProductionCostCalculator] = None) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]

      Optimize existing schedule using campaign resequencing.

      :param current_schedule: Current schedule to optimize
      :param cost_calculator: Cost calculator for evaluation

      :returns: Optimized schedule



   .. py:method:: reschedule(disruption_time: float, disruption_type: str, affected_resources: List[str], current_schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]

      Reschedule after disruption using campaign regrouping.

      :param disruption_time: When disruption occurred (simulation time)
      :param disruption_type: Type of disruption
      :param affected_resources: Affected lines/resources
      :param current_schedule: Current schedule

      :returns: Updated schedule



   .. py:method:: get_metrics() -> Dict[str, Any]

      Get scheduler performance metrics.

      :returns: Metrics dictionary



