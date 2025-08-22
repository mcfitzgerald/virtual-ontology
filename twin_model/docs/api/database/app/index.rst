database.app
============

.. py:module:: database.app

.. autoapi-nested-parse::

   FastAPI application for Virtual Twin Database System

   Provides REST API endpoints for:
   - Database management
   - Simulation execution
   - Experiment tracking
   - Pattern discovery
   - SQL queries



Attributes
----------

.. autoapisummary::

   database.app.app


Functions
---------

.. autoapisummary::

   database.app.lifespan
   database.app.root
   database.app.health_check


Module Contents
---------------

.. py:function:: lifespan(app: fastapi.FastAPI) -> AsyncGenerator
   :async:


   Manage application lifecycle

   Startup:
   - Initialize database tables
   - Sync configurations from manifests
   - Store manager in app state

   Shutdown:
   - Clean up resources


.. py:data:: app

.. py:function:: root()
   :async:


   API root endpoint with system information


.. py:function:: health_check()
   :async:


   Health check endpoint for monitoring


