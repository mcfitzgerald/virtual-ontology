Overview
========

The Virtual Ontology Database module provides a comprehensive data persistence layer for the virtual twin simulation system. It manages both historical manufacturing data and real-time simulation results.

Core Components
---------------

Database Manager
~~~~~~~~~~~~~~~~

The :class:`database.manager.TwinDatabaseManager` is the primary interface for database operations:

* Manages SQLite database connections
* Handles YAML ontology and manifest loading
* Provides high-level data import/export operations
* Manages configuration synchronization

Database Integration
~~~~~~~~~~~~~~~~~~~~

The :class:`database.integration.TwinDatabaseIntegration` provides seamless integration with the twin model:

* Stores simulation results
* Tracks experiments and runs
* Manages pattern discovery
* Provides query interfaces for analysis

Data Models
-----------

Historical MES Data
~~~~~~~~~~~~~~~~~~~

The :class:`database.models.HistoricalMESData` model stores manufacturing execution system data:

* Production metrics (OEE, availability, performance, quality)
* Equipment status and downtime reasons
* Product information and costs
* Energy consumption data

Configuration Models
~~~~~~~~~~~~~~~~~~~~

Equipment and product configurations are managed through:

* :class:`database.models.EquipmentConfig`: Equipment parameters and settings
* :class:`database.models.ProductConfig`: Product specifications and requirements

Simulation Tracking
~~~~~~~~~~~~~~~~~~~

Simulation data is tracked through:

* :class:`database.models.SimulationRun`: Individual simulation executions
* :class:`database.models.ExperimentRun`: Grouped experimental runs
* :class:`database.models.DiscoveredPattern`: Patterns identified during analysis

API Endpoints
-------------

The module provides RESTful API endpoints through FastAPI routers:

Database Router
~~~~~~~~~~~~~~~

* ``GET /database/status``: Check database connection status
* ``POST /database/init``: Initialize database tables
* ``POST /database/import``: Import historical data

Simulation Router
~~~~~~~~~~~~~~~~~

* ``GET /simulations``: List all simulation runs
* ``GET /simulations/{id}``: Get specific simulation details
* ``POST /simulations``: Create new simulation run

Query Router
~~~~~~~~~~~~

* ``POST /query/historical``: Query historical MES data
* ``POST /query/patterns``: Search discovered patterns
* ``GET /query/experiments``: List experiment runs

Configuration
-------------

The database module uses YAML-based configuration:

.. code-block:: yaml

   # config/database.yaml
   database:
     path: "data/twin_database.db"
     pool_size: 5
     echo: false
   
   ontology:
     path: "ontology/twin_ontology.yaml"
     manifest_dir: "manifests/"

Data Flow
---------

1. **Historical Data Import**: CSV files → Database tables
2. **Configuration Sync**: YAML manifests → Configuration tables
3. **Simulation Storage**: Twin model results → Simulation tables
4. **Pattern Discovery**: Analysis results → Pattern tables
5. **Query & Retrieval**: Database → API responses → Client applications

Integration Points
------------------

With Twin Model
~~~~~~~~~~~~~~~

The database integrates with the twin model through:

* Storing simulation parameters and results
* Providing historical data for model calibration
* Tracking KPI metrics over time

With Configuration System
~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration integration includes:

* Loading ontology definitions
* Syncing manifest specifications
* Managing runtime parameters

With API Layer
~~~~~~~~~~~~~~

The API layer provides:

* RESTful endpoints for all operations
* WebSocket support for real-time updates
* Batch operations for performance

Performance Considerations
--------------------------

* **Connection Pooling**: Managed connection pool for concurrent access
* **Batch Operations**: Bulk insert/update capabilities
* **Index Optimization**: Strategic indexing on frequently queried columns
* **Query Caching**: In-memory caching for repeated queries
* **Async Operations**: Non-blocking database operations

Error Handling
--------------

The module implements comprehensive error handling:

* Database connection failures
* Data validation errors
* Transaction rollback on failures
* Detailed error logging
* Graceful degradation strategies