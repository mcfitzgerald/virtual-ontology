twin.schema_manager
===================

.. py:module:: twin.schema_manager

.. autoapi-nested-parse::

   Unified Schema Management for Virtual Twin System

   This module provides a single source of truth for all database schema operations,
   ensuring consistency between SQLModel and raw SQL table definitions.



Attributes
----------

.. autoapisummary::

   twin.schema_manager.logger
   twin.schema_manager.parser


Classes
-------

.. autoapisummary::

   twin.schema_manager.SchemaManager


Module Contents
---------------

.. py:data:: logger

.. py:class:: SchemaManager(db_path: Optional[str] = None)

   Central manager for all database schema operations.

   Ensures consistency between:
   - SQLModel table definitions (MES tables)
   - Raw SQL table definitions (Twin tables)
   - Ontology YAML specifications
   - Database indices and constraints

   Initialize the schema manager.

   :param db_path: Path to the SQLite database. If None, uses default.


   .. py:attribute:: SCHEMA_VERSION
      :value: '1.3.0'



   .. py:attribute:: SQLMODEL_TABLES


   .. py:attribute:: TWIN_TABLES


   .. py:attribute:: db_path


   .. py:method:: get_all_tables() -> Set[str]

      Get the complete set of all managed tables.

      :returns: Set of all table names managed by the system



   .. py:method:: verify_schema() -> Dict[str, Any]

      Verify the database schema against expected definitions.

      :returns:

                - missing_tables: Tables that should exist but don't
                - extra_tables: Tables that exist but aren't documented
                - schema_version: Current schema version
                - is_valid: Boolean indicating if schema is valid
      :rtype: Dictionary with verification results including



   .. py:method:: initialize_schema_tracking(conn: sqlite3.Connection) -> None

      Initialize schema version tracking table.

      :param conn: Active database connection



   .. py:method:: create_all_twin_tables(conn: sqlite3.Connection) -> bool

      Create all twin-specific tables using raw SQL.

      This delegates to the existing TwinTablesManager for now,
      but provides a unified interface.

      :param conn: Active database connection

      :returns: True if successful, False otherwise



   .. py:method:: create_all_sqlmodel_tables() -> bool

      Create all SQLModel-managed tables.

      :returns: True if successful, False otherwise



   .. py:method:: get_table_info(table_name: str) -> Optional[Dict[str, Any]]

      Get detailed information about a specific table.

      :param table_name: Name of the table to inspect

      :returns: Dictionary with table information or None if table doesn't exist



   .. py:method:: validate_against_ontology() -> Dict[str, Any]

      Validate database schema against ontology YAML definitions.

      :returns: Validation results dictionary



.. py:data:: parser

