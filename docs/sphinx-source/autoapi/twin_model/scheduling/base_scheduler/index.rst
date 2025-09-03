twin_model.scheduling.base_scheduler
====================================

.. py:module:: twin_model.scheduling.base_scheduler

.. autoapi-nested-parse::

   Base scheduler abstract class for production scheduling.

   This module provides the abstract interface for production schedulers,
   enabling different scheduling algorithms to be plugged in.



Attributes
----------

.. autoapisummary::

   twin_model.scheduling.base_scheduler.logger


Classes
-------

.. autoapisummary::

   twin_model.scheduling.base_scheduler.OrderStatus
   twin_model.scheduling.base_scheduler.SchedulerConfig
   twin_model.scheduling.base_scheduler.SchedulingConstraints
   twin_model.scheduling.base_scheduler.BaseScheduler


Module Contents
---------------

.. py:data:: logger

.. py:class:: OrderStatus(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Production order status.


   .. py:attribute:: PENDING
      :value: 'pending'



   .. py:attribute:: IN_PROGRESS
      :value: 'in_progress'



   .. py:attribute:: COMPLETED
      :value: 'completed'



   .. py:attribute:: CANCELLED
      :value: 'cancelled'



.. py:class:: SchedulerConfig

   Configuration for scheduler behavior.


   .. py:attribute:: min_order_duration_hours
      :type:  float
      :value: 2.0



   .. py:attribute:: max_order_duration_hours
      :type:  float
      :value: 8.0



   .. py:attribute:: typical_order_duration_hours
      :type:  float
      :value: 4.0



   .. py:attribute:: efficiency_factor
      :type:  float
      :value: 0.7



   .. py:attribute:: min_priority
      :type:  int
      :value: 1



   .. py:attribute:: max_priority
      :type:  int
      :value: 10



   .. py:attribute:: default_priority
      :type:  int
      :value: 5



   .. py:attribute:: same_family_changeover_minutes
      :type:  float
      :value: 15.0



   .. py:attribute:: different_family_changeover_minutes
      :type:  float
      :value: 30.0



   .. py:attribute:: cleaning_changeover_minutes
      :type:  float
      :value: 45.0



   .. py:attribute:: allow_preemption
      :type:  bool
      :value: False



   .. py:attribute:: allow_splitting
      :type:  bool
      :value: False



   .. py:attribute:: maximize_campaign_length
      :type:  bool
      :value: True



.. py:class:: SchedulingConstraints

   Constraints for scheduling decisions.


   .. py:attribute:: horizon_hours
      :type:  Optional[float]
      :value: None



   .. py:attribute:: maintenance_windows
      :type:  Optional[List[tuple[float, float]]]
      :value: None



   .. py:attribute:: product_line_compatibility
      :type:  Optional[Dict[str, List[str]]]
      :value: None



   .. py:attribute:: line_product_restrictions
      :type:  Optional[Dict[str, List[str]]]
      :value: None



   .. py:attribute:: forbidden_sequences
      :type:  Optional[List[tuple[str, str]]]
      :value: None



   .. py:attribute:: preferred_sequences
      :type:  Optional[List[tuple[str, str]]]
      :value: None



   .. py:attribute:: max_concurrent_orders
      :type:  Optional[int]
      :value: None



   .. py:attribute:: min_campaign_length
      :type:  Optional[float]
      :value: None



   .. py:attribute:: max_campaign_length
      :type:  Optional[float]
      :value: None



.. py:class:: BaseScheduler(env: simpy.Environment, config: Optional[SchedulerConfig] = None, constraints: Optional[SchedulingConstraints] = None)

   Bases: :py:obj:`abc.ABC`


   Abstract base class for production schedulers.

   This class defines the interface that all scheduling algorithms must implement,
   allowing for different scheduling strategies to be used interchangeably.


   .. py:attribute:: env


   .. py:attribute:: config


   .. py:attribute:: constraints


   .. py:attribute:: orders
      :type:  Dict[str, twin_model.scheduling.production_scheduler.ProductionOrder]


   .. py:attribute:: line_schedules
      :type:  Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]


   .. py:attribute:: total_orders_created
      :value: 0



   .. py:attribute:: total_orders_completed
      :value: 0



   .. py:attribute:: total_changeover_time
      :value: 0.0



   .. py:method:: generate_schedule(lines: List[str], products: List[str], duration: float, **kwargs) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]
      :abstractmethod:


      Generate production schedule for given lines and products.

      :param lines: List of production line IDs
      :param products: List of product IDs to schedule
      :param duration: Planning horizon in minutes
      :param \*\*kwargs: Additional algorithm-specific parameters

      :returns: Dictionary mapping line IDs to ordered lists of production orders



   .. py:method:: optimize_schedule(current_schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]], objective: str = 'minimize_changeover', **kwargs) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]
      :abstractmethod:


      Optimize an existing schedule based on given objective.

      :param current_schedule: Current schedule to optimize
      :param objective: Optimization objective (e.g., 'minimize_changeover', 'maximize_throughput')
      :param \*\*kwargs: Additional optimization parameters

      :returns: Optimized schedule



   .. py:method:: reschedule(disruption_time: float, disruption_type: str, affected_resources: List[str], **kwargs) -> Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]
      :abstractmethod:


      Reschedule production after a disruption.

      :param disruption_time: Time when disruption occurred
      :param disruption_type: Type of disruption (e.g., 'equipment_failure', 'material_shortage')
      :param affected_resources: List of affected line/equipment IDs
      :param \*\*kwargs: Additional disruption details

      :returns: Updated schedule



   .. py:method:: validate_schedule(schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]) -> tuple[bool, List[str]]

      Validate that a schedule meets all constraints.

      :param schedule: Schedule to validate

      :returns: Tuple of (is_valid, list_of_violations)



   .. py:method:: calculate_metrics(schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]) -> Dict[str, Any]

      Calculate metrics for a schedule.

      :param schedule: Schedule to analyze

      :returns: Dictionary of metrics



   .. py:method:: export_schedule(schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]], format: str = 'dict') -> Any

      Export schedule in specified format.

      :param schedule: Schedule to export
      :param format: Export format ('dict', 'json', 'gantt')

      :returns: Schedule in requested format



