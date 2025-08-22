twin.cost_impact_calculator
===========================

.. py:module:: twin.cost_impact_calculator

.. autoapi-nested-parse::

   Cost Impact Calculator with PyMC for Bayesian Monte Carlo ROI Simulation
   Provides probabilistic financial validation for virtual twin recommendations



Classes
-------

.. autoapisummary::

   twin.cost_impact_calculator.CostParameters
   twin.cost_impact_calculator.CostImpactCalculator


Module Contents
---------------

.. py:class:: CostParameters

   Financial parameters for ROI calculation - no defaults, all required


   .. py:attribute:: labor_cost_per_hour
      :type:  float


   .. py:attribute:: energy_cost_per_kwh
      :type:  float


   .. py:attribute:: material_cost_per_unit
      :type:  float


   .. py:attribute:: downtime_cost_per_hour
      :type:  float


   .. py:attribute:: scrap_cost_per_unit
      :type:  float


   .. py:attribute:: rework_cost_per_unit
      :type:  float


   .. py:attribute:: parameter_change_cost
      :type:  float


   .. py:attribute:: training_cost
      :type:  float


   .. py:attribute:: monitoring_cost_per_week
      :type:  float


   .. py:attribute:: discount_rate
      :type:  float


   .. py:attribute:: confidence_level
      :type:  float


.. py:class:: CostImpactCalculator(db_path: Optional[str] = None, cost_params: Optional[CostParameters] = None)

   Calculates financial impact of virtual twin recommendations
   using PyMC for Bayesian Monte Carlo simulation with proper uncertainty quantification

   Configuration is REQUIRED - all cost parameters must come from config

   Initialize CostImpactCalculator.
   Configuration is required - will raise error if not available.

   :param db_path: Path to SQLite database (uses config if None)
   :param cost_params: Optional CostParameters (uses config if None)

   :raises RuntimeError: If configuration is not available
   :raises ValueError: If required config values are missing


   .. py:attribute:: config
      :value: None



   .. py:attribute:: db_path
      :type:  str
      :value: None



   .. py:attribute:: cost_params
      :type:  CostParameters
      :value: None



   .. py:method:: calculate_roi(baseline_run_id: str, improved_run_id: str, n_simulations: Optional[int] = None, time_horizon_weeks: Optional[int] = None, include_uncertainty: bool = True) -> Dict[str, Any]

      Calculate ROI using PyMC Bayesian Monte Carlo simulation

      :param baseline_run_id: Run ID for baseline scenario
      :param improved_run_id: Run ID for improved scenario
      :param n_simulations: Number of Monte Carlo simulations (uses config default if None)
      :param time_horizon_weeks: Time horizon for ROI calculation (uses config default if None)
      :param include_uncertainty: Whether to add uncertainty to parameters

      :returns: Dictionary with ROI metrics and credible intervals



   .. py:method:: calculate_scenario_impact(scenario: str, baseline_kpis: Dict[str, float], parameter_changes: Dict[str, float], n_simulations: int = 1000) -> Dict[str, Any]

      Calculate financial impact of a specific scenario using PyMC

      :param scenario: Scenario name (e.g., "reduce_micro_stops_30%")
      :param baseline_kpis: Baseline KPI values
      :param parameter_changes: Parameter changes for scenario
      :param n_simulations: Number of simulations

      :returns: Financial impact with credible intervals



   .. py:method:: format_roi_report(roi_summary: Dict[str, Any]) -> str

      Format ROI summary as a readable report with Bayesian credible intervals



