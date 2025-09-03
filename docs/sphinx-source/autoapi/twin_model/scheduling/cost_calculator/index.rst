twin_model.scheduling.cost_calculator
=====================================

.. py:module:: twin_model.scheduling.cost_calculator

.. autoapi-nested-parse::

   Production cost calculator for optimization.

   This module provides comprehensive cost calculation for production
   scheduling optimization, including production, changeover, inventory,
   and quality costs.



Attributes
----------

.. autoapisummary::

   twin_model.scheduling.cost_calculator.logger


Classes
-------

.. autoapisummary::

   twin_model.scheduling.cost_calculator.CostBreakdown
   twin_model.scheduling.cost_calculator.ProductionCostCalculator


Module Contents
---------------

.. py:data:: logger

.. py:class:: CostBreakdown

   Detailed cost breakdown for analysis.


   .. py:attribute:: production_cost
      :type:  float
      :value: 0.0



   .. py:attribute:: changeover_cost
      :type:  float
      :value: 0.0



   .. py:attribute:: inventory_cost
      :type:  float
      :value: 0.0



   .. py:attribute:: quality_cost
      :type:  float
      :value: 0.0



   .. py:attribute:: waste_cost
      :type:  float
      :value: 0.0



   .. py:attribute:: labor_cost
      :type:  float
      :value: 0.0



   .. py:attribute:: energy_cost
      :type:  float
      :value: 0.0



   .. py:attribute:: overtime_cost
      :type:  float
      :value: 0.0



   .. py:attribute:: expedite_cost
      :type:  float
      :value: 0.0



   .. py:attribute:: total_cost
      :type:  float
      :value: 0.0



   .. py:method:: calculate_total() -> float

      Calculate total cost from components.



   .. py:method:: to_dict() -> Dict[str, float]

      Convert to dictionary.



.. py:class:: ProductionCostCalculator(product_manifest: twin_model.scheduling.product_manifest.ProductManifest, labor_cost_per_hour: float = 25.0, energy_cost_per_kwh: float = 0.12, overtime_threshold_hours: float = 8.0, overtime_multiplier: float = 1.5)

   Calculates comprehensive production costs for optimization.


   .. py:attribute:: manifest


   .. py:attribute:: labor_cost_per_hour
      :value: 25.0



   .. py:attribute:: energy_cost_per_kwh
      :value: 0.12



   .. py:attribute:: overtime_threshold_hours
      :value: 8.0



   .. py:attribute:: overtime_multiplier
      :value: 1.5



   .. py:method:: calculate_order_cost(order: twin_model.scheduling.production_scheduler.ProductionOrder, line_id: str, include_changeover: bool = True, previous_product: Optional[str] = None) -> CostBreakdown

      Calculate total cost for a production order.

      :param order: Production order to cost
      :param line_id: Production line ID
      :param include_changeover: Whether to include changeover costs
      :param previous_product: Previous product for changeover calculation

      :returns: Detailed cost breakdown



   .. py:method:: calculate_schedule_cost(schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]) -> Dict[str, Any]

      Calculate total cost for entire schedule.

      :param schedule: Production schedule by line

      :returns: Cost summary with breakdown



   .. py:method:: compare_schedules(schedule1: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]], schedule2: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]], names: Tuple[str, str] = ('Schedule 1', 'Schedule 2')) -> Dict[str, Any]

      Compare costs between two schedules.

      :param schedule1: First schedule
      :param schedule2: Second schedule
      :param names: Names for the schedules

      :returns: Comparison results



   .. py:method:: find_cost_drivers(schedule: Dict[str, List[twin_model.scheduling.production_scheduler.ProductionOrder]]) -> List[Dict[str, Any]]

      Identify main cost drivers in schedule.

      :param schedule: Production schedule

      :returns: List of cost drivers sorted by impact



