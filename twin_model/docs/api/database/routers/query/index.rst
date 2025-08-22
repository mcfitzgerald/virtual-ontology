database.routers.query
======================

.. py:module:: database.routers.query

.. autoapi-nested-parse::

   SQL query execution endpoints

   Provides direct SQL access to the database with safety measures



Attributes
----------

.. autoapisummary::

   database.routers.query.router
   database.routers.query.ALLOWED_TABLES


Functions
---------

.. autoapisummary::

   database.routers.query.execute_query
   database.routers.query.list_tables
   database.routers.query.get_table_schema
   database.routers.query.validate_query


Module Contents
---------------

.. py:data:: router

.. py:data:: ALLOWED_TABLES

.. py:function:: execute_query(request: database.schemas.SQLQueryRequest, session: database.dependencies.SessionDep) -> database.schemas.SQLQueryResponse
   :async:


   Execute a SQL query against the database

   Safety measures:
   - Read-only queries only (SELECT)
   - Limited result size
   - Query timeout


.. py:function:: list_tables(session: database.dependencies.SessionDep, include_samples: bool = False) -> List[database.schemas.TableInfo]
   :async:


   List all available tables with metadata

   Returns information about each table including:
   - Table name
   - Record count
   - Column names
   - Indexes
   - Sample data (optional)


.. py:function:: get_table_schema(table_name: str, session: database.dependencies.SessionDep) -> Dict[str, Any]
   :async:


   Get detailed schema information for a specific table

   Returns:
   - Column definitions with types
   - Primary keys
   - Foreign keys
   - Indexes
   - Constraints


.. py:function:: validate_query(request: database.schemas.SQLQueryRequest) -> Dict[str, Any]
   :async:


   Validate a SQL query without executing it

   Checks for:
   - Syntax errors
   - Forbidden operations
   - Table existence


