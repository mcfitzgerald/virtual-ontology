Quick Start Guide
=================

This guide will help you get started with the Virtual Ontology Database module.

Installation
------------

The database module is part of the Virtual Ontology system. Ensure you have the required dependencies:

.. code-block:: bash

   pip install sqlmodel fastapi uvicorn pandas pyyaml

Basic Setup
-----------

1. Initialize the Database Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from database import TwinDatabaseManager
   
   # Create database manager with default settings
   db_manager = TwinDatabaseManager()
   
   # Or specify custom paths
   db_manager = TwinDatabaseManager(
       db_path=Path("custom/path/database.db"),
       ontology_path=Path("ontology/twin_ontology.yaml"),
       manifest_dir=Path("manifests/")
   )

2. Create Database Tables
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create all required tables
   db_manager.create_all_tables()
   print("Database tables created successfully")

3. Import Historical Data
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Import MES data from CSV
   csv_path = Path("data/mes_data.csv")
   db_manager.import_historical_data(csv_path)
   print(f"Imported data from {csv_path}")

4. Sync Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Load configurations from YAML manifests
   db_manager.sync_configurations_from_manifests()
   print("Configuration synchronized")

Using the API
-------------

Starting the API Server
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # database/app.py
   from fastapi import FastAPI
   from database.routers import database, simulation, query
   
   app = FastAPI(title="Virtual Ontology Database API")
   
   # Include routers
   app.include_router(database.router, prefix="/database")
   app.include_router(simulation.router, prefix="/simulations")
   app.include_router(query.router, prefix="/query")
   
   # Run with: uvicorn database.app:app --reload

Making API Requests
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import requests
   
   # Check database status
   response = requests.get("http://localhost:8000/database/status")
   print(response.json())
   
   # Query historical data
   query_params = {
       "start_date": "2024-01-01",
       "end_date": "2024-12-31",
       "equipment_id": "Line1_Equipment1"
   }
   response = requests.post(
       "http://localhost:8000/query/historical",
       json=query_params
   )
   data = response.json()

Database Integration with Twin Model
-------------------------------------

Basic Integration
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from database import TwinDatabaseIntegration
   from twin_model import OntologyDrivenModelBuilder
   
   # Initialize integration
   db_integration = TwinDatabaseIntegration()
   
   # Store simulation results
   simulation_result = {
       "timestamp": "2024-01-15T10:00:00",
       "kpi_metrics": {
           "oee": 85.5,
           "availability": 92.0,
           "performance": 95.0,
           "quality": 98.0
       },
       "production_output": 1500
   }
   
   run_id = db_integration.store_simulation_run(
       experiment_name="Baseline Analysis",
       parameters={"speed": 100, "batch_size": 50},
       results=simulation_result
   )
   print(f"Stored simulation run: {run_id}")

Querying Simulation Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get all runs for an experiment
   runs = db_integration.get_experiment_runs("Baseline Analysis")
   
   for run in runs:
       print(f"Run {run.id}: OEE = {run.results['kpi_metrics']['oee']}")
   
   # Query patterns
   patterns = db_integration.query_patterns(
       min_confidence=0.8,
       pattern_type="bottleneck"
   )

Working with Sessions
---------------------

Direct Database Access
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sqlmodel import Session, select
   from database.models import HistoricalMESData
   
   # Create a session
   with Session(db_manager.engine) as session:
       # Query historical data
       statement = select(HistoricalMESData).where(
           HistoricalMESData.equipment_id == "Line1_Equipment1"
       ).limit(10)
       
       results = session.exec(statement)
       for record in results:
           print(f"{record.timestamp}: OEE = {record.oee_score}")

Batch Operations
~~~~~~~~~~~~~~~~

.. code-block:: python

   from sqlmodel import Session
   from database.models import HistoricalMESData
   
   # Batch insert
   with Session(db_manager.engine) as session:
       records = []
       for i in range(100):
           record = HistoricalMESData(
               timestamp=f"2024-01-01T{i:02d}:00:00",
               equipment_id=f"Equipment_{i}",
               # ... other fields
           )
           records.append(record)
       
       session.add_all(records)
       session.commit()
       print(f"Inserted {len(records)} records")

Configuration Examples
----------------------

Database Configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # config/database.yaml
   database:
     connection:
       type: "sqlite"
       path: "data/twin_database.db"
       check_same_thread: false
     
     pool:
       size: 10
       max_overflow: 20
       timeout: 30
     
     logging:
       echo: false
       echo_pool: false

Using with Docker
-----------------

.. code-block:: dockerfile

   # Dockerfile
   FROM python:3.12-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   # Create data directory
   RUN mkdir -p data
   
   # Run API server
   CMD ["uvicorn", "database.app:app", "--host", "0.0.0.0", "--port", "8000"]

.. code-block:: yaml

   # docker-compose.yaml
   version: '3.8'
   
   services:
     database-api:
       build: .
       ports:
         - "8000:8000"
       volumes:
         - ./data:/app/data
         - ./config:/app/config
         - ./ontology:/app/ontology
         - ./manifests:/app/manifests
       environment:
         - DATABASE_PATH=/app/data/twin_database.db

Common Patterns
---------------

Repository Pattern
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from database.repositories import BaseRepository
   from database.models import HistoricalMESData
   
   class MESDataRepository(BaseRepository[HistoricalMESData]):
       def get_by_equipment(self, equipment_id: str):
           return self.query().filter(
               HistoricalMESData.equipment_id == equipment_id
           ).all()
       
       def get_high_oee_records(self, threshold: float = 85.0):
           return self.query().filter(
               HistoricalMESData.oee_score >= threshold
           ).all()

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from database.manager import TwinDatabaseManager
   from sqlmodel import Session
   import logging
   
   logger = logging.getLogger(__name__)
   
   try:
       db_manager = TwinDatabaseManager()
       db_manager.create_all_tables()
   except Exception as e:
       logger.error(f"Database initialization failed: {e}")
       # Fallback to in-memory database
       db_manager = TwinDatabaseManager(db_path=":memory:")

Next Steps
----------

* Explore the :doc:`api/index` for detailed API documentation
* Review :doc:`configuration` for advanced configuration options
* See :doc:`usage` for real-world usage examples