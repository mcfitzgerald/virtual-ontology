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

.. py:class:: TwinDatabaseIntegration(db_manager: database.repositories.Optional[database.manager.TwinDatabaseManager] = None)

   Integrate twin model with database


   .. py:attribute:: db_manager


   .. py:method:: run_simulation_to_db(run_type: str = 'experiment', parameters: database.repositories.Dict[str, database.repositories.Any] = None, days: int = 1, parent_run_id: database.repositories.Optional[str] = None) -> str

      Run simulation and store results in database



   .. py:method:: run_experiment(name: str, hypothesis: str, parameter_changes: database.repositories.Dict[str, database.repositories.Any], days: int = 1, num_runs: int = 3) -> str

      Run an experiment with parameter changes



   .. py:method:: discover_patterns(min_confidence: float = 0.7) -> database.repositories.List[database.repositories.DiscoveredPattern]

      Discover patterns from completed experiments



   .. py:method:: generate_recommendations() -> database.repositories.List[database.repositories.ParameterRecommendation]

      Generate recommendations from discovered patterns



