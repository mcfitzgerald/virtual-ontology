twin_model.scheduling
=====================

.. py:module:: twin_model.scheduling

.. autoapi-nested-parse::

   Production scheduling module.



Submodules
----------

.. toctree::
   :maxdepth: 1

   /autoapi/twin_model/scheduling/base_scheduler/index
   /autoapi/twin_model/scheduling/campaign_optimizer/index
   /autoapi/twin_model/scheduling/config_loader/index
   /autoapi/twin_model/scheduling/cost_calculator/index
   /autoapi/twin_model/scheduling/product_manifest/index
   /autoapi/twin_model/scheduling/production_scheduler/index
   /autoapi/twin_model/scheduling/scheduler_integration/index
   /autoapi/twin_model/scheduling/sequential_scheduler/index


Classes
-------

.. autoapisummary::

   twin_model.scheduling.BaseScheduler
   twin_model.scheduling.SchedulerConfig
   twin_model.scheduling.SchedulingConstraints
   twin_model.scheduling.OrderStatus
   twin_model.scheduling.ProductionScheduler
   twin_model.scheduling.ProductionOrder
   twin_model.scheduling.ProductMix


Package Contents
----------------

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


