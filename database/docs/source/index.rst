.. Virtual Ontology Database documentation master file

Virtual Ontology Database Documentation
========================================

Welcome to the Virtual Ontology Database module documentation. This module provides
comprehensive database support for the ontology-driven virtual twin system.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   quickstart
   api/index
   configuration
   usage

Overview
--------

The database module provides:

* **Historical MES Data Storage**: Persistent storage for manufacturing execution system data
* **Twin Simulation Tracking**: Track and manage virtual twin simulation runs
* **Experiment Management**: Organize and compare different experimental configurations
* **Pattern Discovery Storage**: Store discovered patterns and insights
* **Configuration Management**: YAML-based configuration from manifests

Key Features
------------

* **SQLModel ORM**: Type-safe database operations with Pydantic integration
* **FastAPI Integration**: RESTful API endpoints for all database operations
* **YAML Configuration**: Ontology and manifest-driven configuration
* **Async Support**: Asynchronous database operations for high performance
* **Migration Support**: Database schema versioning and migration tools

Architecture
------------

The database module follows a layered architecture:

1. **Models Layer** (:mod:`database.models`): SQLModel entities representing database tables
2. **Schemas Layer** (:mod:`database.schemas`): Pydantic schemas for API validation
3. **Repository Layer** (:mod:`database.repositories`): Data access patterns and queries
4. **Manager Layer** (:mod:`database.manager`): High-level database operations
5. **Integration Layer** (:mod:`database.integration`): Twin model integration
6. **API Layer** (:mod:`database.routers`): FastAPI endpoints

Dependencies
------------

This module depends on:

* **config/**: Configuration loader and YAML files
* **ontology/**: MES and twin ontology definitions
* **manifests/**: Equipment and production manifests

Quick Start
-----------

.. code-block:: python

   from database import TwinDatabaseManager
   
   # Initialize database manager
   db_manager = TwinDatabaseManager()
   
   # Create all tables
   db_manager.create_all_tables()
   
   # Import historical data
   db_manager.import_historical_data(Path("data/mes_data.csv"))
   
   # Sync configurations from manifests
   db_manager.sync_configurations_from_manifests()

API Reference
-------------

The complete API documentation is automatically generated from the source code:

.. toctree::
   :maxdepth: 2

   api/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`