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

.. py:class:: ConfigurationManager(db_path = None)

   Manages simulation configurations with database storage
   Provides efficient storage using deltas and on-demand generation


   .. py:attribute:: loader


   .. py:attribute:: config


   .. py:attribute:: db_path
      :type:  str
      :value: None



   .. py:method:: store_config(config, run_id = None, config_type = 'full', description = None)

      Store configuration in database

      :param config: Configuration dictionary
      :param run_id: Associated simulation run ID
      :param config_type: Type of config (full, delta, base)
      :param description: Optional description

      :returns: config_id of stored configuration



   .. py:method:: get_config(config_id)

      Retrieve configuration by ID



   .. py:method:: get_config_by_run(run_id)

      Retrieve configuration associated with a run



   .. py:method:: list_configs(config_type = None, limit = None)

      List available configurations



   .. py:method:: archive_config(config_id)

      Archive a configuration (soft delete)



   .. py:method:: cleanup_old_configs(days_to_keep = None)

      Archive configs older than specified days



   .. py:method:: migrate_file_configs(config_dir = None)

      Migrate existing file-based configs to database

      :param config_dir: Directory containing config JSON files

      :returns: Number of configs migrated



   .. py:method:: export_config_to_file(config_id, output_dir = None)

      Export configuration to file for archival

      :param config_id: Configuration ID to export
      :param output_dir: Directory to save file

      :returns: Path to exported file or None if failed



