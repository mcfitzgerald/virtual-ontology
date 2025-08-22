twin
====

.. py:module:: twin

.. autoapi-nested-parse::

   Virtual Twin Module - Manufacturing Digital Twin Simulation & Optimization

   This module provides a comprehensive digital twin framework for manufacturing systems,
   enabling simulation, optimization, and intelligent recommendation capabilities.

   Enhanced with:
       - pymoo for robust multi-objective optimization (NSGA-II)
       - PyMC for Bayesian Monte Carlo analysis
       - Monte Carlo wrapper for uncertainty analysis

   Core Components:
       - SimulationRunner: Execute what-if scenarios with Monte Carlo support
       - ActionableParameters: Manage and validate simulation parameters
       - TwinStateManager: Track and synchronize virtual twin state
       - ConfigTransformer: Transform parameters into simulation configurations
       - ConfigurationManager: Store and retrieve configuration history

   Analysis Components:
       - OptimizationEngine: Single/weighted multi-objective optimization
       - RecommendationEngine: pymoo-based NSGA-II multi-objective optimization
       - CostImpactCalculator: PyMC-based Bayesian ROI analysis

   Support Components:
       - SyncHealthMonitor: Monitor synchronization health
       - LineCouplingModel: Model production line interactions

   Usage:
       from twin import SimulationRunner, ActionableParameters, RecommendationEngine

       # Run a Monte Carlo simulation
       runner = SimulationRunner()
       params = ActionableParameters()
       uncertainty = {"micro_stop_probability": (-0.1, 0.1)}  # ±10%
       mc_results = runner.run_monte_carlo_simulation(params, uncertainty, n_simulations=100)

       # Run pymoo optimization
       engine = RecommendationEngine()
       results = engine.optimize(objectives, population_size=50, generations=100)



Submodules
----------

.. toctree::
   :maxdepth: 1

   /api/twin/actionable_parameters/index
   /api/twin/config_loader/index
   /api/twin/config_manager/index
   /api/twin/config_transformer/index
   /api/twin/config_validator/index
   /api/twin/cost_impact_calculator/index
   /api/twin/generator/index
   /api/twin/line_coupling_model/index
   /api/twin/optimization_engine/index
   /api/twin/recommendation_engine/index
   /api/twin/schema_manager/index
   /api/twin/simulation_runner/index
   /api/twin/sync_health/index
   /api/twin/twin_state/index
   /api/twin/virtual_sensors/index
   /api/twin/visualization/index


Classes
-------

.. autoapisummary::

   twin.SimulationRunner
   twin.SimulationRun
   twin.ActionableParameters
   twin.ActionableParameter
   twin.TwinStateManager
   twin.ConfigTransformer
   twin.ConfigurationManager
   twin.OptimizationEngine
   twin.RecommendationEngine
   twin.Objective
   twin.OptimizationResult
   twin.ManufacturingProblem
   twin.CostImpactCalculator
   twin.CostParameters
   twin.SyncHealthMonitor
   twin.SyncHealthStatus
   twin.LineCoupling


Package Contents
----------------

.. py:class:: SimulationRunner(db_path: Optional[str] = None, generator_path: Optional[str] = None, generator_version: Optional[str] = None, verbose: bool = False)

   Manages virtual twin simulations with complete provenance tracking.
   Ensures reproducibility and traceability of all simulation runs.

   This class provides methods to:
   - Run what-if scenario simulations
   - Create baseline simulations
   - Run Monte Carlo uncertainty analysis
   - Compare simulation results
   - Track simulation lineage

   .. rubric:: Example

   >>> runner = SimulationRunner(verbose=False)
   >>> params = ActionableParameters()
   >>> params.set_value("micro_stop_probability", 0.05)
   >>> result = runner.run_simulation(params, duration_days=7)
   >>> print(f"OEE: {result.kpi_summary['mean_oee']:.1f}%")

   Initialize the SimulationRunner.
   Configuration is required - will raise error if not available.

   :param db_path: Path to the SQLite database file (uses config if None)
   :param generator_path: Path to the MES data generation script (uses config if None)
   :param generator_version: Version identifier for the generator (uses config if None)
   :param verbose: If True, print progress messages; if False, run quietly

   :raises RuntimeError: If configuration is not available
   :raises FileNotFoundError: If generator_path does not exist
   :raises sqlite3.Error: If database connection fails


   .. py:attribute:: config
      :value: None



   .. py:attribute:: db_path
      :type:  str
      :value: None



   .. py:attribute:: generator_path
      :type:  pathlib.Path


   .. py:attribute:: generator_version
      :type:  str
      :value: None



   .. py:attribute:: verbose
      :type:  bool
      :value: False



   .. py:attribute:: sync_monitor
      :type:  twin.sync_health.SyncHealthMonitor


   .. py:attribute:: config_manager
      :type:  twin.config_manager.ConfigurationManager


   .. py:method:: run_simulation(parameters: twin.actionable_parameters.ActionableParameters, parent_run_id: Optional[str] = None, seed: Optional[int] = None, duration_days: int = 7, notes: Optional[str] = None) -> SimulationRun

      Run a simulation with specific parameters.

      :param parameters: ActionableParameters instance with values to test
      :param parent_run_id: Optional parent run for lineage tracking
      :param seed: Random seed for reproducibility (uses parent seed + 1 if not provided)
      :param duration_days: Simulation duration in days (1-30)
      :param notes: Optional description or notes about this run

      :returns:

                - run_id: Unique identifier
                - kpi_summary: Dict with KPIs (mean_oee, availability, etc.) as percentages (0-100)
                - status: 'completed' or 'failed'
                - Other metadata fields
      :rtype: SimulationRun object containing

      :raises ValueError: If duration_days is outside valid range (1-30)
      :raises RuntimeError: If simulation execution fails

      .. rubric:: Example

      >>> runner = SimulationRunner()
      >>> params = ActionableParameters()
      >>> params.set_value("micro_stop_probability", 0.05)
      >>> result = runner.run_simulation(params, duration_days=7)
      >>> print(f"Mean OEE: {result.kpi_summary['mean_oee']:.1f}%")
      >>> print(f"Downtime: {result.kpi_summary['downtime_percentage']:.1f}%")



   .. py:method:: create_baseline(seed: int = 42, duration_days: int = 7, notes: Optional[str] = None) -> SimulationRun

      Create a baseline simulation with default parameters.

      :param seed: Random seed for reproducibility
      :param duration_days: Simulation duration in days (1-30)
      :param notes: Optional description

      :returns: SimulationRun object with baseline results

      .. rubric:: Example

      >>> runner = SimulationRunner()
      >>> baseline = runner.create_baseline(duration_days=14)
      >>> print(f"Baseline OEE: {baseline.kpi_summary['mean_oee']:.1f}%")



   .. py:method:: run_monte_carlo_simulation(parameters: twin.actionable_parameters.ActionableParameters, uncertainty_ranges: Dict[str, Tuple[float, float]], n_simulations: int = 100, duration_days: int = 7, parent_run_id: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]

      Run Monte Carlo simulation with parameter uncertainty.

      :param parameters: Base parameters
      :param uncertainty_ranges: Dict mapping parameter names to (min_delta, max_delta) tuples
      :param n_simulations: Number of Monte Carlo iterations
      :param duration_days: Duration for each simulation
      :param parent_run_id: Optional parent run for lineage
      :param notes: Optional description

      :returns:

                - 'results': List of SimulationRun objects
                - 'statistics': Summary statistics (mean, std, percentiles)
                - 'confidence_intervals': 95% CI for each KPI
      :rtype: Dictionary containing

      .. rubric:: Example

      >>> runner = SimulationRunner()
      >>> params = ActionableParameters()
      >>> uncertainty = {"micro_stop_probability": (-0.02, 0.02)}  # ±2%
      >>> mc_results = runner.run_monte_carlo_simulation(
      ...     params, uncertainty, n_simulations=50
      ... )
      >>> print(f"Mean OEE: {mc_results['statistics']['mean_oee']:.1f}%")
      >>> print(f"95% CI: {mc_results['confidence_intervals']['mean_oee']}")



   .. py:method:: compare_runs(run_ids: List[str]) -> Dict[str, Any]

      Compare multiple simulation runs.

      :param run_ids: List of run IDs to compare

      :returns:

                - 'runs': List of SimulationRun objects
                - 'kpi_comparison': DataFrame comparing KPIs
                - 'parameter_differences': Dict of parameter variations
      :rtype: Dictionary containing

      .. rubric:: Example

      >>> comparison = runner.compare_runs(["sim-001", "sim-002", "sim-003"])
      >>> print(comparison['kpi_comparison'])



   .. py:method:: get_run_lineage(run_id: str) -> List[SimulationRun]

      Get complete lineage (ancestors and descendants) of a run.

      :param run_id: Run ID to trace lineage for

      :returns: List of SimulationRun objects in chronological order

      .. rubric:: Example

      >>> lineage = runner.get_run_lineage("sim-20240101-120000-abc123")
      >>> for run in lineage:
      ...     print(f"{run.run_id}: {run.run_type}")



.. py:class:: SimulationRun

   Metadata for a simulation run with full provenance.

   .. attribute:: run_id

      Unique identifier for this simulation run

   .. attribute:: run_type

      Type of run (baseline, simulation, recommendation, optimization)

   .. attribute:: seed

      Random seed used for reproducibility

   .. attribute:: generator_version

      Version of the data generator used

   .. attribute:: parent_run_id

      Optional ID of the parent run for lineage tracking

   .. attribute:: started_at

      Timestamp when the simulation started

   .. attribute:: finished_at

      Timestamp when the simulation completed (None if still running)

   .. attribute:: config_delta

      Dictionary of parameter changes from baseline

   .. attribute:: data_hash

      Hash of the generated data for verification

   .. attribute:: output_path

      Path to the output data file

   .. attribute:: kpi_summary

      Summary of KPI results (OEE, availability, etc.)

   .. attribute:: notes

      Optional description or notes about the run

   .. attribute:: status

      Current status (pending, running, completed, failed)

   .. rubric:: Example

   >>> run = SimulationRun(
   ...     run_id="sim-20240101-120000-abc123",
   ...     run_type="simulation",
   ...     seed=42,
   ...     generator_version="1.0.0",
   ...     parent_run_id=None,
   ...     started_at=datetime.now(),
   ...     finished_at=None,
   ...     config_delta={"micro_stop_probability": 0.05},
   ...     data_hash=None,
   ...     output_path=None,
   ...     kpi_summary=None,
   ...     notes="Testing reduced micro-stops",
   ...     status="running"
   ... )


   .. py:attribute:: run_id
      :type:  str


   .. py:attribute:: run_type
      :type:  str


   .. py:attribute:: seed
      :type:  int


   .. py:attribute:: generator_version
      :type:  str


   .. py:attribute:: parent_run_id
      :type:  Optional[str]


   .. py:attribute:: started_at
      :type:  datetime.datetime


   .. py:attribute:: finished_at
      :type:  Optional[datetime.datetime]


   .. py:attribute:: config_delta
      :type:  Dict[str, Any]


   .. py:attribute:: data_hash
      :type:  Optional[str]


   .. py:attribute:: output_path
      :type:  Optional[str]


   .. py:attribute:: kpi_summary
      :type:  Optional[Dict[str, float]]


   .. py:attribute:: notes
      :type:  Optional[str]


   .. py:attribute:: status
      :type:  str


.. py:class:: ActionableParameters(config_path: Optional[str] = None)

   The 5 key parameters that control virtual twin behavior
   These serve as proxies for real-world operational improvements

   Configuration is REQUIRED - all parameter definitions must come from config

   Initialize actionable parameters from configuration.
   Configuration is required - will raise error if not available.

   :param config_path: Optional path to JSON config file for parameter definitions.
                       If not provided, will use ConfigLoader.


   .. py:attribute:: current_values
      :type:  Dict[str, float]


   .. py:method:: set_value(parameter_name: str, value: float) -> None

      Set the value of a parameter with validation

      :param parameter_name: Name of the parameter to set
      :param value: New value for the parameter

      :raises KeyError: If parameter_name is not recognized
      :raises ValueError: If value is outside valid bounds



   .. py:method:: get_value(parameter_name: str) -> float

      Get the current value of a parameter

      :param parameter_name: Name of the parameter

      :returns: Current value of the parameter

      :raises KeyError: If parameter_name is not recognized



   .. py:method:: get_all_values() -> Dict[str, float]

      Get all current parameter values



   .. py:method:: get_all() -> Dict[str, float]

      Alias for get_all_values() for backward compatibility



   .. py:method:: reset(parameter_name: Optional[str] = None) -> None

      Reset parameter(s) to default values

      :param parameter_name: Specific parameter to reset, or None to reset all



   .. py:method:: get_normalized_vector() -> numpy.typing.NDArray[numpy.float64]

      Get all parameters as a normalized vector [0, 1]

      :returns: Numpy array of normalized parameter values



   .. py:method:: set_from_normalized_vector(vector: numpy.typing.NDArray[numpy.float64]) -> None

      Set all parameters from a normalized vector

      :param vector: Numpy array of normalized values [0, 1]

      :raises ValueError: If vector length doesn't match number of parameters



   .. py:method:: get_bounds_for_optimization() -> Tuple[numpy.typing.NDArray[numpy.float64], numpy.typing.NDArray[numpy.float64]]

      Get parameter bounds as arrays for optimization algorithms

      :returns: Tuple of (lower_bounds, upper_bounds) as numpy arrays



   .. py:method:: describe() -> str

      Get human-readable description of all parameters and their current values

      :returns: Formatted string describing all parameters



   .. py:method:: to_dict() -> Dict[str, Any]

      Convert parameters to dictionary representation

      :returns: Dictionary containing parameter definitions and current values



   .. py:method:: to_config_overlay() -> Dict[str, Any]

      Convert current values to configuration overlay format

      :returns: Dictionary in format expected by ConfigTransformer



   .. py:method:: validate_all() -> Tuple[bool, List[str]]

      Validate all current parameter values

      :returns: Tuple of (is_valid, list_of_errors)



.. py:class:: ActionableParameter

   A tunable parameter that can be adjusted in simulation to model operational changes



   .. py:attribute:: name
      :type:  str


   .. py:attribute:: description
      :type:  str


   .. py:attribute:: bounds
      :type:  Tuple[float, float]


   .. py:attribute:: default_value
      :type:  float


   .. py:attribute:: unit
      :type:  str


   .. py:attribute:: parameter_type
      :type:  ParameterType


   .. py:attribute:: causal_effect
      :type:  str


   .. py:attribute:: invariants
      :type:  List[str]
      :value: []



   .. py:method:: validate(value: float) -> bool

      Check if value is within bounds



   .. py:method:: normalize(value: float) -> float

      Normalize value to [0, 1] range



   .. py:method:: denormalize(normalized: float) -> float

      Convert from [0, 1] back to parameter range



.. py:class:: TwinStateManager(db_path: Optional[str] = None)

   Manages virtual twin state and provides high-level operations
   for querying, comparing, and optimizing the twin

   Initialize the TwinStateManager.

   :param db_path: Path to SQLite database. If None, uses path from configuration.

   :raises KeyError: If database path not found in configuration.


   .. py:attribute:: loader


   .. py:attribute:: config


   .. py:attribute:: module_config


   .. py:attribute:: db_path
      :type:  str
      :value: None



   .. py:method:: get_current_state() -> Optional[TwinState]

      Get the current state of the virtual twin



   .. py:method:: update_state(run_id: str, baseline_run_id: Optional[str] = None, notes: Optional[str] = None) -> None

      Update the twin state based on a simulation run

      :param run_id: Run ID to set as current state
      :param baseline_run_id: Optional baseline for comparison
      :param notes: Optional notes about the state change



   .. py:method:: calculate_confidence(run_id: str, n_validation_runs: Optional[int] = None, confidence_level: Optional[float] = None) -> None

      Calculate confidence intervals for KPIs using validation runs

      :param run_id: Base run to validate
      :param n_validation_runs: Number of validation runs (uses config if None)
      :param confidence_level: Confidence level (uses config if None)



   .. py:method:: create_recommendation(parameters: Dict[str, float], expected_improvement: Dict[str, float], recommendation_type: str = 'optimization', confidence: float = 0.0, notes: Optional[str] = None) -> int

      Create a new recommendation

      :param parameters: Recommended parameter values
      :param expected_improvement: Expected KPI improvements
      :param recommendation_type: Type of recommendation
      :param confidence: Confidence in recommendation (0-1)
      :param notes: Optional notes

      :returns: Recommendation ID



   .. py:method:: accept_recommendation(recommendation_id: int) -> Dict[str, float]

      Accept a recommendation and return its parameters

      :param recommendation_id: ID of recommendation to accept

      :returns: Parameter values from the recommendation



   .. py:method:: get_improvement_trends(n_runs: int = 10) -> Dict[str, List[float]]

      Get KPI improvement trends over recent runs

      :param n_runs: Number of recent runs to analyze

      :returns: Dictionary of KPI trends



   .. py:method:: generate_state_report() -> str

      Generate a comprehensive state report



.. py:class:: ConfigTransformer(base_config_path: Optional[str] = None, db_path: Optional[str] = None)

   Transforms actionable parameters into configuration overlays
   for the MES data generator

   Initialize the ConfigTransformer.

   :param base_config_path: Path to base MES data config. If None, uses path from configuration.
   :param db_path: Path to SQLite database. If None, uses path from configuration.

   :raises KeyError: If required paths not found in configuration.


   .. py:attribute:: loader


   .. py:attribute:: config


   .. py:attribute:: base_config_path
      :type:  pathlib.Path


   .. py:attribute:: base_config
      :type:  Dict[str, Any]


   .. py:attribute:: config_manager
      :type:  twin.config_manager.ConfigurationManager


   .. py:attribute:: baseline_values
      :type:  Dict[str, Any]


   .. py:method:: apply_parameters(parameters: twin.actionable_parameters.ActionableParameters, save_path: Optional[str] = None) -> Dict[str, Any]

      Apply scaling parameters to create a new configuration.

      All parameters are treated as multipliers where 1.0 = baseline.

      :param parameters: ActionableParameters instance with scaling values
      :param save_path: Optional path to save the transformed config

      :returns: Transformed configuration dictionary with scaled values



   .. py:method:: create_scenario(scenario_name: str, parameter_changes: Dict[str, float]) -> Dict[str, Any]

      Create a specific scenario configuration.

      :param scenario_name: Name of the scenario
      :param parameter_changes: Dictionary of parameter names and their scaling values

      :returns: Scenario configuration with scaled values



   .. py:method:: create_optimization_scenarios() -> Dict[str, Dict[str, Any]]

      Create standard optimization scenarios for comparison

      :returns: Dictionary of scenario configurations



.. py:class:: ConfigurationManager(db_path: Optional[str] = None)

   Manages simulation configurations with database storage
   Provides efficient storage using deltas and on-demand generation

   Initialize the ConfigurationManager.

   :param db_path: Path to SQLite database. If None, uses path from configuration.

   :raises KeyError: If database path not found in configuration.


   .. py:attribute:: loader


   .. py:attribute:: config


   .. py:attribute:: db_path
      :type:  str
      :value: None



   .. py:method:: store_config(config: Dict[str, Any], run_id: Optional[str] = None, config_type: str = 'full', description: Optional[str] = None) -> str

      Store configuration in database

      :param config: Configuration dictionary
      :param run_id: Associated simulation run ID
      :param config_type: Type of config (full, delta, base)
      :param description: Optional description

      :returns: config_id of stored configuration



   .. py:method:: get_config(config_id: str) -> Optional[Dict[str, Any]]

      Retrieve configuration by ID



   .. py:method:: get_config_by_run(run_id: str) -> Optional[Dict[str, Any]]

      Retrieve configuration associated with a run



   .. py:method:: list_configs(config_type: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]

      List available configurations



   .. py:method:: archive_config(config_id: str) -> bool

      Archive a configuration (soft delete)



   .. py:method:: cleanup_old_configs(days_to_keep: Optional[int] = None) -> int

      Archive configs older than specified days



   .. py:method:: migrate_file_configs(config_dir: Optional[str] = None) -> int

      Migrate existing file-based configs to database

      :param config_dir: Directory containing config JSON files

      :returns: Number of configs migrated



   .. py:method:: export_config_to_file(config_id: str, output_dir: Optional[str] = None) -> Optional[str]

      Export configuration to file for archival

      :param config_id: Configuration ID to export
      :param output_dir: Directory to save file

      :returns: Path to exported file or None if failed



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


.. py:class:: SyncHealthMonitor(db_path: Optional[str] = None)

   Monitors synchronization health between virtual twin and data sources
   Compliant with ISO 23247 synchronization requirements

   Configuration is REQUIRED - all values must come from config

   Initialize the SyncHealthMonitor.
   Configuration is required - will raise error if not available.

   :param db_path: Path to the SQLite database (uses config if None)

   :raises RuntimeError: If configuration is not available
   :raises ValueError: If required config values are missing


   .. py:attribute:: config
      :value: None



   .. py:attribute:: db_path
      :type:  str
      :value: None



   .. py:attribute:: default_sync_interval
      :value: None



   .. py:attribute:: alert_threshold
      :value: None



   .. py:attribute:: status_thresholds
      :value: None



   .. py:attribute:: sync_log_retention_days
      :value: None



   .. py:attribute:: default_history_hours
      :value: None



   .. py:method:: init_sync_tables() -> None

      Initialize synchronization metadata tables



   .. py:method:: update_sync_metadata(entity_id: str, entity_type: str, data: Optional[Dict[str, Any]] = None, source_run_id: Optional[str] = None, sync_interval_minutes: Optional[int] = None) -> None

      Update synchronization metadata for an entity

      :param entity_id: Unique identifier for the entity
      :param entity_type: Type of entity (Equipment, Line, etc.)
      :param data: Optional data to hash for change detection
      :param source_run_id: Optional simulation run that generated this data
      :param sync_interval_minutes: Expected sync interval (uses config default if None)



   .. py:method:: get_sync_health(entity_id: Optional[str] = None) -> List[SyncMetadata]

      Get synchronization health for one or all entities

      :param entity_id: Optional specific entity ID, or None for all

      :returns: List of SyncMetadata objects



   .. py:method:: check_health_alerts(threshold_minutes: Optional[int] = None) -> List[Dict[str, Any]]

      Check for entities requiring health alerts

      :param threshold_minutes: Minutes before raising alert (uses config if None)

      :returns: List of entities requiring alerts



   .. py:method:: get_health_summary() -> Dict[str, Any]

      Get overall health summary statistics

      :returns: Dictionary with health statistics



   .. py:method:: get_sync_history(entity_id: str, hours: Optional[int] = None) -> List[Dict[str, Any]]

      Get synchronization history for an entity

      :param entity_id: Entity identifier
      :param hours: Hours of history to retrieve (uses config if None)

      :returns: List of sync history records



   .. py:method:: cleanup_old_logs(days_to_keep: Optional[int] = None) -> int

      Clean up old synchronization logs

      :param days_to_keep: Number of days of logs to retain (uses config if None)

      :returns: Number of records deleted



   .. py:method:: get_entity_types() -> List[str]

      Get list of all entity types being monitored

      :returns: List of unique entity types



   .. py:method:: export_health_report() -> Dict[str, Any]

      Export comprehensive health report

      :returns: Dictionary containing full health report



.. py:class:: SyncHealthStatus(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Synchronization health states per ISO 23247


   .. py:attribute:: HEALTHY
      :value: 'HEALTHY'



   .. py:attribute:: DELAYED
      :value: 'DELAYED'



   .. py:attribute:: STALE
      :value: 'STALE'



   .. py:attribute:: UNKNOWN
      :value: 'UNKNOWN'



.. py:class:: LineCoupling

   Explicit cascade model with buffers and stochastic variation
   Models how upstream stops affect downstream equipment

   Initialize line coupling model


   .. py:attribute:: loader


   .. py:attribute:: config


   .. py:attribute:: buffer_capacity


   .. py:attribute:: initial_buffer_level


   .. py:attribute:: depletion_rate


   .. py:attribute:: refill_rate


   .. py:attribute:: depletion_noise_std


   .. py:attribute:: refill_noise_std


   .. py:attribute:: use_probabilistic


   .. py:attribute:: cascade_sensitivity


   .. py:attribute:: cascade_delay_minutes


   .. py:attribute:: buffers
      :type:  Dict[str, Buffer]


   .. py:attribute:: equipment_status
      :type:  Dict[str, EquipmentStatus]


   .. py:attribute:: cascade_timers
      :type:  Dict[str, int]


   .. py:method:: initialize_line(equipment_ids: List[str]) -> None

      Initialize a production line with equipment and buffers

      :param equipment_ids: List of equipment IDs in order (upstream to downstream)



   .. py:method:: calculate_starvation(downstream_id: str, upstream_id: str, upstream_status: EquipmentStatus, time_interval_minutes: Optional[int] = None) -> Tuple[bool, float]

      Calculate if downstream equipment starves due to upstream stop

      :param downstream_id: ID of downstream equipment
      :param upstream_id: ID of upstream equipment
      :param upstream_status: Current status of upstream equipment
      :param time_interval_minutes: Time interval for calculation

      :returns: Tuple of (is_starved, probability_of_starvation)



   .. py:method:: calculate_blockage(upstream_id: str, downstream_id: str, downstream_status: EquipmentStatus, time_interval_minutes: Optional[int] = None) -> Tuple[bool, float]

      Calculate if upstream equipment blocks due to downstream stop

      :param upstream_id: ID of upstream equipment
      :param downstream_id: ID of downstream equipment
      :param downstream_status: Current status of downstream equipment
      :param time_interval_minutes: Time interval for calculation

      :returns: Tuple of (is_blocked, probability_of_blockage)



   .. py:method:: simulate_cascade(equipment_sequence: List[str], initial_failure: str, time_steps: Optional[int] = None) -> Dict[str, List[EquipmentStatus]]

      Simulate cascade effects over time

      :param equipment_sequence: Ordered list of equipment IDs
      :param initial_failure: Equipment ID that initially fails
      :param time_steps: Number of 5-minute intervals to simulate

      :returns: Dictionary of equipment ID to list of statuses over time



   .. py:method:: get_buffer_status() -> Dict[str, Dict[str, Any]]

      Get current status of all buffers



