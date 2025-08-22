database
========

.. py:module:: database

.. autoapi-nested-parse::

   Database package for ontology-driven virtual twin system

   This package provides database support for:
   - Historical MES data storage
   - Twin simulation tracking
   - Experiment management
   - Pattern discovery storage
   - Configuration management from YAML manifests



Submodules
----------

.. toctree::
   :maxdepth: 1

   /api/database/app/index
   /api/database/cli/index
   /api/database/dependencies/index
   /api/database/integration/index
   /api/database/integration_optimized/index
   /api/database/main/index
   /api/database/manager/index
   /api/database/models/index
   /api/database/repositories/index
   /api/database/routers/index
   /api/database/schemas/index


Classes
-------

.. autoapisummary::

   database.TwinDatabaseManager
   database.TwinDatabaseIntegration


Package Contents
----------------

.. py:class:: TwinDatabaseManager(db_path: database.models.Optional[pathlib.Path] = None, ontology_path: database.models.Optional[pathlib.Path] = None, manifest_dir: database.models.Optional[pathlib.Path] = None)

   Manage twin database with YAML ontologies


   .. py:attribute:: db_path


   .. py:attribute:: db_url
      :value: 'sqlite:///Instance of pathlib.Path'



   .. py:attribute:: engine
      :value: None



   .. py:attribute:: ontology_path


   .. py:attribute:: manifest_dir


   .. py:method:: create_all_tables()

      Create all database tables



   .. py:method:: load_ontology() -> database.models.Dict[str, database.models.Any]

      Load ontology from YAML file (cached)



   .. py:method:: load_manifest(manifest_name: str) -> database.models.Dict[str, database.models.Any]

      Load manifest from YAML file (cached)



   .. py:method:: import_historical_data(csv_path: pathlib.Path)

      Import historical MES data from CSV



   .. py:method:: sync_configurations_from_manifests()

      Sync equipment and product configs from manifest YAMLs



   .. py:method:: get_ontology_version() -> str

      Get version of current ontology



   .. py:method:: get_manifest_version() -> str

      Get combined version hash of manifests



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



