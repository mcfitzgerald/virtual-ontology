database.manager
================

.. py:module:: database.manager

.. autoapi-nested-parse::

   Database manager using SQLModel with YAML ontologies



Classes
-------

.. autoapisummary::

   database.manager.TwinDatabaseManager


Module Contents
---------------

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



