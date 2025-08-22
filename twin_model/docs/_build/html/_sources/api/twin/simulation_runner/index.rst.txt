twin.simulation_runner
======================

.. py:module:: twin.simulation_runner

.. autoapi-nested-parse::

   Simulation Runner with Provenance Tracking and Monte Carlo Support
   Manages simulation runs with complete reproducibility, provenance, and uncertainty analysis



Classes
-------

.. autoapisummary::

   twin.simulation_runner.SimulationRun
   twin.simulation_runner.SimulationRunner


Module Contents
---------------

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



