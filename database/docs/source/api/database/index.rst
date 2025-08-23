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

.. py:class:: TwinDatabaseManager(db_path = None, ontology_path = None, manifest_dir = None)

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



   .. py:method:: load_ontology()

      Load ontology from YAML file (cached)



   .. py:method:: load_manifest(manifest_name)

      Load manifest from YAML file (cached)



   .. py:method:: import_historical_data(csv_path)

      Import historical MES data from CSV



   .. py:method:: sync_configurations_from_manifests()

      Sync equipment and product configs from manifest YAMLs



   .. py:method:: get_ontology_version()

      Get version of current ontology



   .. py:method:: get_manifest_version()

      Get combined version hash of manifests



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



