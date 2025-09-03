twin_model.scheduling.production_scheduler
==========================================

.. py:module:: twin_model.scheduling.production_scheduler

.. autoapi-nested-parse::

   Production order scheduling for MES simulation.

   This module provides production order management and scheduling
   to match the patterns observed in the target MES data.



Attributes
----------

.. autoapisummary::

   twin_model.scheduling.production_scheduler.logger


Classes
-------

.. autoapisummary::

   twin_model.scheduling.production_scheduler.ProductionOrder
   twin_model.scheduling.production_scheduler.ProductMix
   twin_model.scheduling.production_scheduler.ProductionScheduler


Module Contents
---------------

.. py:data:: logger

.. py:class:: ProductionOrder

   Production order with scheduling information.


   .. py:attribute:: order_id
      :type:  str


   .. py:attribute:: product_id
      :type:  str


   .. py:attribute:: product_name
      :type:  str


   .. py:attribute:: target_volume
      :type:  float


   .. py:attribute:: line_id
      :type:  str


   .. py:attribute:: scheduled_start
      :type:  float


   .. py:attribute:: scheduled_duration
      :type:  float


   .. py:attribute:: priority
      :type:  int
      :value: 5



   .. py:attribute:: status
      :type:  twin_model.scheduling.base_scheduler.OrderStatus


   .. py:attribute:: actual_start
      :type:  Optional[float]
      :value: None



   .. py:attribute:: actual_end
      :type:  Optional[float]
      :value: None



   .. py:attribute:: completed_volume
      :type:  float
      :value: 0.0



   .. py:attribute:: scrap_volume
      :type:  float
      :value: 0.0



.. py:class:: ProductMix

   Product mix configuration for a production line.


   .. py:attribute:: line_id
      :type:  str


   .. py:attribute:: products
      :type:  List[str]


   .. py:attribute:: weights
      :type:  List[float]


.. py:class:: ProductionScheduler(env: simpy.Environment, config: Optional[twin_model.scheduling.base_scheduler.SchedulerConfig] = None, constraints: Optional[twin_model.scheduling.base_scheduler.SchedulingConstraints] = None, catalog_path: Optional[pathlib.Path] = None, random_seed: Optional[int] = None)

   Bases: :py:obj:`twin_model.scheduling.base_scheduler.BaseScheduler`


   Concrete implementation of scheduler for MES simulation.

   This scheduler creates and manages production orders to match
   the patterns observed in the target MES data, implementing
   a simple sequential scheduling algorithm with configurable
   product mixes and changeover times.


   .. py:attribute:: random


   .. py:attribute:: order_counter
      :value: 1000



   .. py:attribute:: line_schedules
      :type:  Dict[str, List[ProductionOrder]]


   .. py:attribute:: current_production
      :type:  Dict[str, Optional[ProductionOrder]]


   .. py:attribute:: product_mixes


   .. py:attribute:: changeover_matrix


   .. py:method:: generate_order(line_id: str, scheduled_start: float, duration_hours: float = 4.0) -> ProductionOrder

      Generate a production order for a line.

      :param line_id: Production line ID
      :param scheduled_start: Start time in simulation minutes
      :param duration_hours: Order duration in hours

      :returns: Generated production order



   .. py:method:: generate_initial_schedule(simulation_duration: float)

      Generate initial production schedule for entire simulation.

      :param simulation_duration: Total simulation duration in minutes



   .. py:method:: get_changeover_time(from_product: str, to_product: str) -> float

      Get changeover time between products.

      :param from_product: Current product ID
      :param to_product: Next product ID

      :returns: Changeover time in minutes



   .. py:method:: get_current_order(line_id: str) -> Optional[ProductionOrder]

      Get current production order for a line.

      :param line_id: Production line ID

      :returns: Current order or None if no active order



   .. py:method:: update_order_progress(order_id: str, good_units: float, scrap_units: float)

      Update production progress for an order.

      :param order_id: Order ID
      :param good_units: Good units produced
      :param scrap_units: Scrap units produced



   .. py:method:: schedule_changeover(line_id: str) -> Generator

      Schedule a changeover process for a line.

      :param line_id: Production line ID

      :Yields: SimPy timeout for changeover duration



   .. py:method:: get_statistics() -> Dict[str, Any]

      Get scheduler statistics.

      :returns: Dictionary of statistics



   .. py:method:: generate_schedule(lines: List[str], products: List[str], duration: float, **kwargs) -> Dict[str, List[ProductionOrder]]

      Generate production schedule for given lines and products.

      This implementation uses a simple sequential scheduling algorithm
      with product mix based on historical patterns.

      :param lines: List of production line IDs
      :param products: List of product IDs to schedule
      :param duration: Planning horizon in minutes
      :param \*\*kwargs: Additional parameters (e.g., 'use_product_mix')

      :returns: Dictionary mapping line IDs to ordered lists of production orders



   .. py:method:: optimize_schedule(current_schedule: Dict[str, List[ProductionOrder]], objective: str = 'minimize_changeover', **kwargs) -> Dict[str, List[ProductionOrder]]

      Optimize an existing schedule based on given objective.

      This is a simple implementation that reorders products to
      minimize changeover time within each line.

      :param current_schedule: Current schedule to optimize
      :param objective: Optimization objective
      :param \*\*kwargs: Additional optimization parameters

      :returns: Optimized schedule



   .. py:method:: reschedule(disruption_time: float, disruption_type: str, affected_resources: List[str], **kwargs) -> Dict[str, List[ProductionOrder]]

      Reschedule production after a disruption.

      This implementation delays affected orders and reschedules
      remaining production.

      :param disruption_time: Time when disruption occurred
      :param disruption_type: Type of disruption
      :param affected_resources: List of affected line/equipment IDs
      :param \*\*kwargs: Additional disruption details

      :returns: Updated schedule



