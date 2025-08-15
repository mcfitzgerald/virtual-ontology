twin.test_integration
=====================

.. py:module:: twin.test_integration

.. autoapi-nested-parse::

   Integration tests for Virtual Twin System

   Tests the complete integration between:
   - Twin module database operations
   - Ontology-driven analytics
   - API exposure via api.sh and query-log.sh
   - Configuration management



Attributes
----------

.. autoapisummary::

   twin.test_integration.api_check


Classes
-------

.. autoapisummary::

   twin.test_integration.TestDatabaseIntegration
   twin.test_integration.TestQueryLogIntegration


Functions
---------

.. autoapisummary::

   twin.test_integration.run_tests


Module Contents
---------------

.. py:class:: TestDatabaseIntegration(methodName='runTest')

   Bases: :py:obj:`unittest.TestCase`


   Test database integration across all layers.


   .. py:method:: setUpClass()
      :classmethod:


      Set up test environment.



   .. py:method:: test_01_pristine_reset()

      Test pristine database reset capability.



   .. py:method:: test_02_config_storage_in_database()

      Test that configs are stored in database, not files.



   .. py:method:: test_03_ontology_schema_alignment()

      Test that database schema aligns with ontology definitions.



   .. py:method:: test_04_api_twin_table_access()

      Test that API can query twin tables.



   .. py:method:: test_05_simulation_config_database_flow()

      Test that simulation configs flow through database correctly.



   .. py:method:: test_06_unified_schema_management()

      Test unified schema management.



   .. py:method:: test_07_configuration_consistency()

      Test that all modules use consistent configuration.



.. py:class:: TestQueryLogIntegration(methodName='runTest')

   Bases: :py:obj:`unittest.TestCase`


   Test query-log.sh integration with twin tables.


   .. py:method:: test_query_log_twin_tables()

      Test that query-log.sh can query twin tables.



.. py:function:: run_tests()

   Run all integration tests.


.. py:data:: api_check

