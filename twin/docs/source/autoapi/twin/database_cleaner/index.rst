twin.database_cleaner
=====================

.. py:module:: twin.database_cleaner

.. autoapi-nested-parse::

   Database Cleanup Utility for Virtual Twin System
   Provides comprehensive cleanup capabilities for simulation and optimization data.



Attributes
----------

.. autoapisummary::

   twin.database_cleaner.logger


Classes
-------

.. autoapisummary::

   twin.database_cleaner.DatabaseCleaner


Functions
---------

.. autoapisummary::

   twin.database_cleaner.main


Module Contents
---------------

.. py:data:: logger

.. py:class:: DatabaseCleaner(db_path = None)

   Manages database cleanup operations for the virtual twin system.

   Provides methods to clean simulation data, optimization results,
   and related metadata while preserving base MES data.


   .. py:attribute:: PROTECTED_TABLES
      :type:  Set[str]


   .. py:attribute:: CLEANABLE_TABLES
      :type:  Dict[str, str]


   .. py:attribute:: db_path
      :type:  pathlib.Path


   .. py:method:: get_table_stats()

      Get record counts for all tables.

      :returns: Dictionary mapping table names to record counts.



   .. py:method:: clean_simulation_data(keep_baseline = True, older_than_days = None, run_ids_to_keep = None)

      Clean simulation data and related tables.

      :param keep_baseline: If True, preserves baseline runs.
      :param older_than_days: Remove data older than this many days.
      :param run_ids_to_keep: Specific run IDs to preserve.

      :returns: Cleanup statistics including tables and records cleaned.



   .. py:method:: clean_optimization_results(older_than_days = None)

      Clean optimization results.

      :param older_than_days: Remove results older than this many days.

      :returns: Cleanup statistics.



   .. py:method:: clean_all_twin_data(preserve_mes_data = True, confirm = False)

      Clean all twin-related data, optionally preserving MES data.

      :param preserve_mes_data: If True, preserves core MES data tables.
      :param confirm: Must be True to execute this operation.

      :returns: Comprehensive cleanup statistics.



   .. py:method:: reset_to_baseline()

      Reset database to contain only MES data and baseline runs.

      Removes all simulation and optimization data except baseline runs.

      :returns: Cleanup statistics.



   .. py:method:: get_database_size()

      Get database file size and statistics.

      :returns: Dictionary with size information.



.. py:function:: main()

   Command-line interface for database cleanup.


