database.routers.experiment
===========================

.. py:module:: database.routers.experiment

.. autoapi-nested-parse::

   Experiment and discovery endpoints

   Provides API for running experiments, discovering patterns,
   and generating recommendations



Attributes
----------

.. autoapisummary::

   database.routers.experiment.router


Functions
---------

.. autoapisummary::

   database.routers.experiment.create_experiment
   database.routers.experiment.list_experiments
   database.routers.experiment.get_experiment
   database.routers.experiment.list_patterns
   database.routers.experiment.discover_patterns
   database.routers.experiment.validate_pattern
   database.routers.experiment.list_recommendations
   database.routers.experiment.generate_recommendations
   database.routers.experiment.apply_recommendation


Module Contents
---------------

.. py:data:: router

.. py:function:: create_experiment(request, manager)
   :async:


   Create and run a new experiment

   This will:
   1. Create or use a baseline run
   2. Run multiple test simulations with parameter changes
   3. Analyze results
   4. Generate conclusions


.. py:function:: list_experiments(session, status = None)
   :async:


   List all experiments with optional status filter


.. py:function:: get_experiment(experiment_id, session)
   :async:


   Get details of a specific experiment


.. py:function:: list_patterns(session, min_confidence = 0.0, validated_only = False)
   :async:


   List discovered patterns with optional filtering


.. py:function:: discover_patterns(manager, min_confidence = 0.7)
   :async:


   Discover new patterns from completed experiments


.. py:function:: validate_pattern(pattern_id, validation_run_ids, session)
   :async:


   Mark a pattern as validated with supporting runs


.. py:function:: list_recommendations(session, applied_only = False, min_confidence = 0.0)
   :async:


   List parameter recommendations


.. py:function:: generate_recommendations(manager)
   :async:


   Generate new recommendations from discovered patterns


.. py:function:: apply_recommendation(recommendation_id, session, manager)
   :async:


   Apply a recommendation by running a simulation with recommended parameters


