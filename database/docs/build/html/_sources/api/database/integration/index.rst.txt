database.integration
====================

.. py:module:: database.integration

.. autoapi-nested-parse::

   Integration with twin model



Classes
-------

.. autoapisummary::

   database.integration.TwinDatabaseIntegration


Module Contents
---------------

.. py:class:: TwinDatabaseIntegration(db_manager = None)

   Integrate twin model with database


   .. py:attribute:: db_manager


   .. py:method:: run_simulation_to_db(run_type = 'experiment', parameters = None, days = 1, parent_run_id = None)

      Run simulation and store results in database



   .. py:method:: run_experiment(name, hypothesis, parameter_changes, days = 1, num_runs = 3)

      Run an experiment with parameter changes



   .. py:method:: discover_patterns(min_confidence = 0.7)

      Discover patterns from completed experiments



   .. py:method:: generate_recommendations()

      Generate recommendations from discovered patterns



