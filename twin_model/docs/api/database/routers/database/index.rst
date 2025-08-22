database.routers.database
=========================

.. py:module:: database.routers.database

.. autoapi-nested-parse::

   Database management endpoints

   Provides API for database maintenance, backups, and monitoring



Attributes
----------

.. autoapisummary::

   database.routers.database.router
   database.routers.database.TABLE_CATEGORIES


Functions
---------

.. autoapisummary::

   database.routers.database.database_status
   database.routers.database.database_statistics
   database.routers.database.sync_manifests
   database.routers.database.import_historical_data
   database.routers.database.create_backup
   database.routers.database.restore_backup
   database.routers.database.clean_database
   database.routers.database.reset_database


Module Contents
---------------

.. py:data:: router

.. py:data:: TABLE_CATEGORIES

.. py:function:: database_status(manager: database.dependencies.ManagerDep, session: database.dependencies.SessionDep) -> Dict[str, Any]
   :async:


   Get current database status

   Returns:
   - Connection status
   - Ontology version
   - Manifest version
   - Table counts


.. py:function:: database_statistics(manager: database.dependencies.ManagerDep, session: database.dependencies.SessionDep) -> database.schemas.DatabaseStats
   :async:


   Get comprehensive database statistics

   Returns detailed information about:
   - Database file size
   - Table record counts
   - Data categories
   - Versions


.. py:function:: sync_manifests(manager: database.dependencies.ManagerDep) -> database.schemas.OperationResponse
   :async:


   Sync configurations from YAML manifest files

   Updates equipment and product configurations
   from the manifest YAML files


.. py:function:: import_historical_data(manager: database.dependencies.ManagerDep, csv_file: fastapi.UploadFile = File(...)) -> database.schemas.OperationResponse
   :async:


   Import historical MES data from CSV file


.. py:function:: create_backup(request: database.schemas.BackupRequest, manager: database.dependencies.ManagerDep) -> database.schemas.BackupResponse
   :async:


   Create a database backup

   Creates a timestamped backup of the database file
   with optional compression


.. py:function:: restore_backup(manager: database.dependencies.ManagerDep, backup_file: fastapi.UploadFile = File(...)) -> database.schemas.OperationResponse
   :async:


   Restore database from a backup file

   WARNING: This will replace the current database


.. py:function:: clean_database(request: database.schemas.CleanupRequest, session: database.dependencies.SessionDep) -> database.schemas.OperationResponse
   :async:


   Clean database tables

   Options:
   - Clean by category
   - Clean specific tables
   - Clean data older than N days
   - Preserve specific tables


.. py:function:: reset_database(manager: database.dependencies.ManagerDep, keep_configurations: bool = True) -> database.schemas.OperationResponse
   :async:


   Reset database to initial state

   Options:
   - keep_configurations: Preserve equipment/product configs


