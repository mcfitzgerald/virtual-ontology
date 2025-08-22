twin.recommendation_engine
==========================

.. py:module:: twin.recommendation_engine

.. autoapi-nested-parse::

   Recommendation Engine with Multi-Objective Optimization using pymoo
   Uses NSGA-II algorithm for finding Pareto-optimal configurations



Classes
-------

.. autoapisummary::

   twin.recommendation_engine.Objective
   twin.recommendation_engine.OptimizationResult
   twin.recommendation_engine.ManufacturingProblem
   twin.recommendation_engine.RecommendationEngine


Module Contents
---------------

.. py:class:: Objective

   Optimization objective definition


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: direction
      :type:  str


   .. py:attribute:: kpi_name
      :type:  str


   .. py:attribute:: weight
      :type:  float
      :value: 1.0



   .. py:attribute:: constraint
      :type:  Optional[Tuple[float, float]]
      :value: None



.. py:class:: OptimizationResult

   Result from multi-objective optimization


   .. py:attribute:: parameters
      :type:  Dict[str, float]


   .. py:attribute:: objectives
      :type:  Dict[str, float]


   .. py:attribute:: pareto_rank
      :type:  int


   .. py:attribute:: crowding_distance
      :type:  float


   .. py:attribute:: feasible
      :type:  bool


   .. py:attribute:: run_id
      :type:  Optional[str]
      :value: None



.. py:class:: ManufacturingProblem(simulation_runner: twin.simulation_runner.SimulationRunner, objectives: List[Objective], constraints: Optional[Dict[str, Tuple[float, float]]] = None, use_simulation: bool = False)

   Bases: :py:obj:`pymoo.core.problem.Problem`


   Multi-objective optimization problem for manufacturing using pymoo
   Wraps the simulation runner to evaluate actual simulations

   Initialize the manufacturing optimization problem

   :param simulation_runner: SimulationRunner instance for evaluations
   :param objectives: List of optimization objectives
   :param constraints: Optional parameter constraints
   :param use_simulation: If True, run actual simulations; if False, use approximations


   .. py:attribute:: runner
      :type:  twin.simulation_runner.SimulationRunner


   .. py:attribute:: objectives
      :type:  List[Objective]


   .. py:attribute:: constraints
      :type:  Dict[str, Tuple[float, float]]


   .. py:attribute:: use_simulation
      :type:  bool
      :value: False



   .. py:attribute:: cached_evaluations
      :type:  Dict[str, Any]


   .. py:attribute:: config


   .. py:attribute:: param_names
      :type:  List[str]


   .. py:attribute:: param_objects
      :type:  List[Any]


.. py:class:: RecommendationEngine(simulation_runner: Optional[twin.simulation_runner.SimulationRunner] = None, state_manager: Optional[twin.twin_state.TwinStateManager] = None)

   Multi-objective optimization engine for virtual twin recommendations
   Uses pymoo's NSGA-II algorithm with proper constraint handling

   Initialize the RecommendationEngine.

   :param simulation_runner: Optional SimulationRunner instance. If None, creates a new one.
   :param state_manager: Optional TwinStateManager instance. If None, creates a new one.


   .. py:attribute:: runner
      :type:  twin.simulation_runner.SimulationRunner


   .. py:attribute:: state_manager
      :type:  twin.twin_state.TwinStateManager


   .. py:method:: optimize(objectives: List[Objective], constraints: Optional[Dict[str, Tuple[float, float]]] = None, population_size: Optional[int] = None, generations: Optional[int] = None, seed: Optional[int] = None, verbose: bool = True, use_simulation: bool = False) -> List[OptimizationResult]

      Run multi-objective optimization using pymoo's NSGA-II

      :param objectives: List of optimization objectives
      :param constraints: Optional parameter constraints
      :param population_size: Size of population for genetic algorithm
      :param generations: Number of generations to evolve
      :param seed: Random seed for reproducibility
      :param verbose: Print progress information
      :param use_simulation: If True, use actual simulations; if False, use approximations

      :returns: List of Pareto-optimal solutions



   .. py:method:: calculate_hypervolume(results: List[OptimizationResult], ref_point: Optional[numpy.ndarray] = None) -> float

      Calculate hypervolume indicator for the Pareto front

      :param results: List of optimization results
      :param ref_point: Reference point for hypervolume calculation

      :returns: Hypervolume value



   .. py:method:: visualize_pareto_front(results: List[OptimizationResult], objective_names: Optional[List[str]] = None, true_front: Optional[numpy.ndarray] = None)

      Visualize the Pareto front using pymoo's Scatter plot

      :param results: List of optimization results
      :param objective_names: Names of objectives for axis labels
      :param true_front: Optional true Pareto front for comparison



   .. py:method:: recommend_for_scenario(scenario: str, save_recommendation: bool = True, use_simulation: bool = False) -> Dict[str, Any]

      Generate recommendation for a specific scenario using pymoo

      :param scenario: Scenario description
      :param save_recommendation: Whether to save to database
      :param use_simulation: Whether to use actual simulations

      :returns: Recommendation dictionary



