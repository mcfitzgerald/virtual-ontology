database.main
=============

.. py:module:: database.main

.. autoapi-nested-parse::

   Main entry point for Virtual Twin Database API server

   Run with:
       python -m database.main

   Or use the management script:
       ./twin.sh start



Attributes
----------

.. autoapisummary::

   database.main.db_config


Functions
---------

.. autoapisummary::

   database.main.main


Module Contents
---------------

.. py:data:: db_config

.. py:function:: main()

   Start the FastAPI server with Uvicorn

   Configuration options can be set via environment variables:
   - TWIN_API_HOST: Host to bind to (default: 0.0.0.0)
   - TWIN_API_PORT: Port to bind to (default: 8000)
   - TWIN_API_RELOAD: Enable auto-reload (default: True in dev)
   - TWIN_API_LOG_LEVEL: Log level (default: info)


