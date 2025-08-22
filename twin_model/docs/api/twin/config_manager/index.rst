twin.config_manager
===================

.. py:module:: twin.config_manager

.. autoapi-nested-parse::

   Configuration Manager for Virtual Twin Simulations
   Handles storage and retrieval of simulation configurations in database



Attributes
----------

.. autoapisummary::

   twin.config_manager.logger


Classes
-------

.. autoapisummary::

   twin.config_manager.ConfigurationManager


Module Contents
---------------

.. py:data:: logger

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



