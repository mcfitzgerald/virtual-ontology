twin.optimization_engine
========================

.. py:module:: twin.optimization_engine

.. autoapi-nested-parse::

   Twin Optimization Engine
   Multi-objective optimization using scipy's differential evolution algorithm
   Following VIRTUAL_TWIN_IMPLEMENTATION_PLAN_FINAL.md Phase 4 specifications



Attributes
----------

.. autoapisummary::

   twin.optimization_engine.logger


Classes
-------

.. autoapisummary::

   twin.optimization_engine.ActionableParameter
   twin.optimization_engine.OptimizationObjective
   twin.optimization_engine.OptimizationResult
   twin.optimization_engine.OptimizationEngine


Module Contents
---------------

.. py:data:: logger

.. py:class:: ActionableParameter

   Actionable parameter that can be tuned in the simulation
   Ref: VIRTUAL_TWIN_IMPLEMENTATION_PLAN_FINAL.md lines 114-122


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: bounds
      :type:  Tuple[float, float]


   .. py:attribute:: unit
      :type:  str


   .. py:attribute:: causal_effect
      :type:  str


   .. py:attribute:: invariants
      :type:  List[str]


   .. py:attribute:: current_value
      :type:  Optional[float]
      :value: None



.. py:class:: OptimizationObjective

   Single optimization objective


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: direction
      :type:  str


   .. py:attribute:: weight
      :type:  float
      :value: 1.0



   .. py:attribute:: target
      :type:  Optional[float]
      :value: None



.. py:class:: OptimizationResult

   Result from optimization run


   .. py:attribute:: parameters
      :type:  Dict[str, float]


   .. py:attribute:: objectives
      :type:  Dict[str, float]


   .. py:attribute:: success
      :type:  bool


   .. py:attribute:: message
      :type:  str


   .. py:attribute:: iterations
      :type:  int


   .. py:attribute:: evaluations
      :type:  int


   .. py:attribute:: pareto_rank
      :type:  Optional[int]
      :value: None



   .. py:attribute:: confidence_interval
      :type:  Optional[Tuple[float, float]]
      :value: None



   .. py:attribute:: run_id
      :type:  Optional[str]
      :value: None



.. py:class:: OptimizationEngine(simulation_runner: Optional[Any] = None)

   Multi-objective optimization engine using differential evolution
   Implements NSGA-II concepts for Pareto optimization

   Initialize optimization engine

   :param simulation_runner: Optional simulation runner for evaluating solutions


   .. py:attribute:: loader


   .. py:attribute:: config


   .. py:attribute:: PARAMETERS
      :type:  Dict[str, ActionableParameter]


   .. py:attribute:: simulation_runner
      :type:  Optional[Any]
      :value: None



   .. py:attribute:: evaluation_count
      :type:  int
      :value: 0



   .. py:attribute:: best_solution
      :type:  Optional[OptimizationResult]
      :value: None



   .. py:attribute:: pareto_front
      :type:  List[OptimizationResult]
      :value: []



   .. py:method:: optimize(objectives: List[OptimizationObjective], constraints: Optional[Dict[str, Any]] = None, population_size: Optional[int] = None, generations: Optional[int] = None, seed: Optional[int] = None, strategy: str = 'best1bin', mutation: Optional[Tuple[float, float]] = None, recombination: Optional[float] = None, workers: int = 1, callback: Optional[Callable] = None, verbose: bool = True) -> List[OptimizationResult]

      Run multi-objective optimization using differential evolution
      Following VIRTUAL_TWIN_IMPLEMENTATION_PLAN_FINAL.md lines 283-358

      :param objectives: List of optimization objectives
      :param constraints: Optional constraints on parameters or objectives
      :param population_size: Size of population for differential evolution
      :param generations: Number of generations to evolve
      :param seed: Random seed for reproducibility
      :param strategy: Evolution strategy ('best1bin', 'rand1bin', etc.)
      :param mutation: Mutation factor range
      :param recombination: Crossover probability
      :param workers: Number of parallel workers (-1 for all cores)
      :param callback: Optional callback function
      :param verbose: Whether to print progress

      :returns: List of Pareto-optimal solutions



   .. py:method:: optimize_multi_objective(objectives: List[OptimizationObjective], constraints: Optional[Dict[str, Any]] = None, population_size: Optional[int] = None, generations: Optional[int] = None, seed: Optional[int] = None, verbose: bool = True) -> List[OptimizationResult]

      True multi-objective optimization with Pareto front
      Uses multiple differential evolution runs with different weights

      This is a simplified version - full NSGA-II would be better
      but scipy doesn't have it built-in



   .. py:method:: validate_with_monte_carlo(solution: OptimizationResult, n_simulations: Optional[int] = None, confidence_level: Optional[float] = None) -> OptimizationResult

      Validate solution with Monte Carlo simulation
      Following VIRTUAL_TWIN_IMPLEMENTATION_PLAN_FINAL.md lines 351-357

      :param solution: Solution to validate
      :param n_simulations: Number of Monte Carlo runs
      :param confidence_level: Confidence level for interval

      :returns: Updated solution with confidence intervals



   .. py:method:: recommend_for_scenario(scenario: str, constraints: Optional[Dict[str, Any]] = None, verbose: bool = True) -> Dict[str, Any]

      Generate recommendation for a specific scenario using natural language

      :param scenario: Natural language description of optimization goal
      :param constraints: Optional constraints
      :param verbose: Whether to print progress

      :returns: Recommendation with parameters and expected improvements



