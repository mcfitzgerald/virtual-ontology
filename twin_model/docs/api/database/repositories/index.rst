database.repositories
=====================

.. py:module:: database.repositories

.. autoapi-nested-parse::

   Repository pattern for database operations



Classes
-------

.. autoapisummary::

   database.repositories.TwinRunRepository
   database.repositories.SimulationDataRepository
   database.repositories.ExperimentRepository
   database.repositories.PatternRepository
   database.repositories.RecommendationRepository
   database.repositories.KPIRepository


Module Contents
---------------

.. py:class:: TwinRunRepository(session: sqlmodel.Session)

   Repository for twin run operations


   .. py:attribute:: session


   .. py:method:: create_run(run_type: str, ontology_version: str, manifest_version: str, parameters: database.models.Dict[str, database.models.Any], parent_run_id: database.models.Optional[str] = None) -> database.models.TwinRun

      Create a new twin run



   .. py:method:: update_run_status(run_id: str, status: str, kpi_summary: database.models.Optional[database.models.Dict[str, database.models.Any]] = None)

      Update run status and results



   .. py:method:: get_baseline_run() -> database.models.Optional[database.models.TwinRun]

      Get the most recent baseline run



.. py:class:: SimulationDataRepository(session: sqlmodel.Session)

   Repository for simulation data operations


   .. py:attribute:: session


   .. py:method:: store_simulation_data(run_id: str, mes_data: pandas.DataFrame)

      Store simulation output in MES format



   .. py:method:: batch_insert_events(run_id: str, events: List[database.models.Dict[str, database.models.Any]], batch_size: int = 1000) -> int

      Batch insert simulation events for performance.

      Efficiently inserts large numbers of events in batches
      to minimize database round-trips and transaction overhead.

      :param run_id: Simulation run identifier
      :param events: List of event dictionaries to insert
      :param batch_size: Number of records per batch (default 1000)

      :returns: Number of events inserted



   .. py:method:: flush_cache_to_database(run_id: str, cache_path: str, batch_size: int = 5000) -> database.models.Dict[str, database.models.Any]

      Flush events from cache to database in batches.

      Reads events from the ObservableCache and efficiently
      inserts them into the database using batch operations.
      This enables persisting simulation data without keeping
      everything in memory.

      :param run_id: Simulation run identifier
      :param cache_path: Path to cache directory
      :param batch_size: Number of records per database batch

      :returns: Dictionary with flush statistics



   .. py:method:: calculate_kpi_snapshot(run_id: str) -> database.models.Dict[str, database.models.Any]

      Calculate KPI summary for a run



.. py:class:: ExperimentRepository(session: sqlmodel.Session)

   Repository for experiment tracking


   .. py:attribute:: session


   .. py:method:: create_experiment(name: str, hypothesis: str, baseline_run_id: str, parameter_changes: database.models.Dict[str, database.models.Any]) -> database.models.Experiment

      Create new experiment



   .. py:method:: add_test_run(experiment_id: str, run_id: str)

      Add a test run to an experiment



   .. py:method:: complete_experiment(experiment_id: str, results_summary: database.models.Dict[str, database.models.Any], conclusion: str)

      Mark experiment as completed with results



.. py:class:: PatternRepository(session: sqlmodel.Session)

   Repository for discovered patterns


   .. py:attribute:: session


   .. py:method:: create_pattern(pattern_type: str, pattern_name: str, description: str, evidence: database.models.Dict[str, database.models.Any], experiment_ids: List[str], confidence_score: float) -> database.models.DiscoveredPattern

      Create a new discovered pattern



   .. py:method:: validate_pattern(pattern_id: int, validation_run_ids: List[str])

      Mark a pattern as validated



.. py:class:: RecommendationRepository(session: sqlmodel.Session)

   Repository for parameter recommendations


   .. py:attribute:: session


   .. py:method:: create_recommendation(pattern_id: database.models.Optional[int], recommendation_type: str, parameter_adjustments: database.models.Dict[str, database.models.Any], expected_improvement: database.models.Dict[str, float], confidence: float) -> database.models.ParameterRecommendation

      Create a new parameter recommendation



   .. py:method:: apply_recommendation(recommendation_id: int, run_id: str, actual_improvement: database.models.Dict[str, float])

      Mark recommendation as applied with results



.. py:class:: KPIRepository(session: sqlmodel.Session)

   Repository for KPI snapshots and comparisons


   .. py:attribute:: session


   .. py:method:: create_kpi_snapshot(run_id: str, entity_type: str, entity_id: str, kpis: database.models.Dict[str, database.models.Any], period_start: database.models.datetime, period_end: database.models.datetime) -> database.models.KPISnapshot

      Create a KPI snapshot



   .. py:method:: create_comparison(baseline_run_id: str, comparison_run_id: str) -> database.models.ComparisonResult

      Create a comparison between two runs



