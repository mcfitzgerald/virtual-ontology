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

.. py:class:: TwinRunRepository(session)

   Repository for twin run operations


   .. py:attribute:: session


   .. py:method:: create_run(run_type, ontology_version, manifest_version, parameters, parent_run_id = None)

      Create a new twin run



   .. py:method:: update_run_status(run_id, status, kpi_summary = None)

      Update run status and results



   .. py:method:: get_baseline_run()

      Get the most recent baseline run



.. py:class:: SimulationDataRepository(session)

   Repository for simulation data operations


   .. py:attribute:: session


   .. py:method:: store_simulation_data(run_id, mes_data)

      Store simulation output in MES format



   .. py:method:: batch_insert_events(run_id, events, batch_size = 1000)

      Batch insert simulation events for performance.

      Efficiently inserts large numbers of events in batches
      to minimize database round-trips and transaction overhead.

      :param run_id: Simulation run identifier
      :param events: List of event dictionaries to insert
      :param batch_size: Number of records per batch (default 1000)

      :returns: Number of events inserted



   .. py:method:: flush_cache_to_database(run_id, cache_path, batch_size = None)

      Flush events from cache to database in batches.

      Reads events from the ObservableCache and efficiently
      inserts them into the database using batch operations.
      This enables persisting simulation data without keeping
      everything in memory.

      :param run_id: Simulation run identifier
      :param cache_path: Path to cache directory
      :param batch_size: Number of records per database batch

      :returns: Dictionary with flush statistics



   .. py:method:: calculate_kpi_snapshot(run_id)

      Calculate KPI summary for a run



.. py:class:: ExperimentRepository(session)

   Repository for experiment tracking


   .. py:attribute:: session


   .. py:method:: create_experiment(name, hypothesis, baseline_run_id, parameter_changes)

      Create new experiment



   .. py:method:: add_test_run(experiment_id, run_id)

      Add a test run to an experiment



   .. py:method:: complete_experiment(experiment_id, results_summary, conclusion)

      Mark experiment as completed with results



.. py:class:: PatternRepository(session)

   Repository for discovered patterns


   .. py:attribute:: session


   .. py:method:: create_pattern(pattern_type, pattern_name, description, evidence, experiment_ids, confidence_score)

      Create a new discovered pattern



   .. py:method:: validate_pattern(pattern_id, validation_run_ids)

      Mark a pattern as validated



.. py:class:: RecommendationRepository(session)

   Repository for parameter recommendations


   .. py:attribute:: session


   .. py:method:: create_recommendation(pattern_id, recommendation_type, parameter_adjustments, expected_improvement, confidence)

      Create a new parameter recommendation



   .. py:method:: apply_recommendation(recommendation_id, run_id, actual_improvement)

      Mark recommendation as applied with results



.. py:class:: KPIRepository(session)

   Repository for KPI snapshots and comparisons


   .. py:attribute:: session


   .. py:method:: create_kpi_snapshot(run_id, entity_type, entity_id, kpis, period_start, period_end)

      Create a KPI snapshot



   .. py:method:: create_comparison(baseline_run_id, comparison_run_id)

      Create a comparison between two runs



