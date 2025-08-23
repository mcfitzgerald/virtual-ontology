Configuration
=============

The database module uses YAML-based configuration with support for environment variables and runtime overrides.

Configuration Files
-------------------

Primary Configuration
~~~~~~~~~~~~~~~~~~~~~

The main database configuration is stored in ``config/database.yaml``:

.. code-block:: yaml

   # config/database.yaml
   database:
     # Connection settings
     connection:
       type: "sqlite"  # or "postgresql", "mysql"
       path: "data/twin_database.db"  # For SQLite
       # url: "postgresql://user:pass@localhost/dbname"  # For PostgreSQL
       check_same_thread: false  # SQLite specific
     
     # Connection pool settings
     pool:
       size: 5
       max_overflow: 10
       timeout: 30
       recycle: 3600  # Recycle connections after 1 hour
     
     # Query settings
     query:
       default_limit: 1000
       max_limit: 10000
       timeout: 60
     
     # Logging
     logging:
       echo: false  # Log SQL statements
       echo_pool: false  # Log connection pool events
       level: "INFO"
   
   # Ontology configuration
   ontology:
     twin_ontology: "ontology/twin_ontology.yaml"
     mes_ontology: "ontology/mes_ontology.yaml"
   
   # Manifest configuration
   manifests:
     directory: "manifests/"
     equipment: "equipment_manifest.yaml"
     production: "production_manifest.yaml"
   
   # Cache settings
   cache:
     enabled: true
     ttl: 300  # 5 minutes
     max_size: 1000

Environment Variables
---------------------

Override configuration using environment variables:

.. code-block:: bash

   # Database connection
   export DB_TYPE=postgresql
   export DB_URL=postgresql://user:pass@localhost/twin_db
   
   # Pool settings
   export DB_POOL_SIZE=10
   export DB_POOL_TIMEOUT=60
   
   # Logging
   export DB_ECHO=true
   export DB_LOG_LEVEL=DEBUG

Loading Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import os
   from database.config import DatabaseConfig
   
   # Load with environment overrides
   config = DatabaseConfig()
   config.load_from_env()
   
   # Or load from custom file
   config = DatabaseConfig.from_file("custom_config.yaml")

Database Connection Strings
---------------------------

SQLite
~~~~~~

.. code-block:: yaml

   database:
     connection:
       type: "sqlite"
       path: "data/twin_database.db"
       # In-memory database for testing
       # path: ":memory:"

PostgreSQL
~~~~~~~~~~

.. code-block:: yaml

   database:
     connection:
       type: "postgresql"
       host: "localhost"
       port: 5432
       database: "twin_db"
       username: "twin_user"
       password: "secure_password"
       # Or use connection URL
       url: "postgresql://twin_user:secure_password@localhost:5432/twin_db"

MySQL
~~~~~

.. code-block:: yaml

   database:
     connection:
       type: "mysql"
       host: "localhost"
       port: 3306
       database: "twin_db"
       username: "twin_user"
       password: "secure_password"
       # Connection URL format
       url: "mysql+pymysql://twin_user:secure_password@localhost:3306/twin_db"

Model Configuration
-------------------

Table Naming
~~~~~~~~~~~~

.. code-block:: python

   # database/models.py
   from sqlmodel import SQLModel, Field
   
   class HistoricalMESData(SQLModel, table=True):
       __tablename__ = "historical_mes_data"  # Explicit table name
       
       id: int = Field(default=None, primary_key=True)
       # ... other fields

Index Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sqlmodel import SQLModel, Field, Index
   
   class HistoricalMESData(SQLModel, table=True):
       __tablename__ = "historical_mes_data"
       
       id: int = Field(default=None, primary_key=True)
       timestamp: datetime = Field(index=True)
       equipment_id: str = Field(index=True)
       oee_score: float
       
       # Composite index
       __table_args__ = (
           Index("idx_equipment_timestamp", "equipment_id", "timestamp"),
       )

Relationship Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sqlmodel import SQLModel, Field, Relationship
   from typing import Optional, List
   
   class Equipment(SQLModel, table=True):
       id: int = Field(default=None, primary_key=True)
       name: str
       
       # One-to-many relationship
       production_records: List["ProductionRecord"] = Relationship(
           back_populates="equipment"
       )
   
   class ProductionRecord(SQLModel, table=True):
       id: int = Field(default=None, primary_key=True)
       equipment_id: int = Field(foreign_key="equipment.id")
       
       # Many-to-one relationship
       equipment: Optional[Equipment] = Relationship(
           back_populates="production_records"
       )

API Configuration
-----------------

FastAPI Settings
~~~~~~~~~~~~~~~~

.. code-block:: python

   # database/app.py
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   
   app = FastAPI(
       title="Virtual Ontology Database API",
       description="Database API for Virtual Twin System",
       version="2.0.0",
       docs_url="/docs",
       redoc_url="/redoc",
       openapi_url="/openapi.json"
   )
   
   # CORS configuration
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

Router Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # database/routers/config.py
   from fastapi import APIRouter
   
   router = APIRouter(
       prefix="/api/v1",
       tags=["database"],
       responses={
           404: {"description": "Not found"},
           500: {"description": "Internal server error"}
       }
   )

Performance Tuning
------------------

Connection Pool
~~~~~~~~~~~~~~~

.. code-block:: yaml

   database:
     pool:
       size: 20  # Base pool size
       max_overflow: 40  # Additional connections when needed
       timeout: 30  # Connection timeout in seconds
       recycle: 3600  # Recycle connections after 1 hour
       pre_ping: true  # Test connections before use

Query Optimization
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   database:
     query:
       # Pagination defaults
       default_page_size: 100
       max_page_size: 1000
       
       # Query timeout
       statement_timeout: 60  # seconds
       
       # Cache settings
       enable_query_cache: true
       cache_size: 10000
       cache_ttl: 300

Batch Operations
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   database:
     batch:
       insert_size: 1000  # Records per batch insert
       update_size: 500   # Records per batch update
       use_bulk: true     # Use bulk operations when available

Security Configuration
----------------------

Authentication
~~~~~~~~~~~~~~

.. code-block:: yaml

   security:
     # Database credentials
     credentials:
       username: "${DB_USERNAME}"  # From environment
       password: "${DB_PASSWORD}"  # From environment
     
     # SSL/TLS settings
     ssl:
       enabled: true
       ca_cert: "/path/to/ca-cert.pem"
       client_cert: "/path/to/client-cert.pem"
       client_key: "/path/to/client-key.pem"

Encryption
~~~~~~~~~~

.. code-block:: yaml

   security:
     encryption:
       # Encrypt sensitive fields
       fields:
         - "password"
         - "api_key"
         - "secret"
       
       # Encryption settings
       algorithm: "AES256"
       key_file: "/secure/path/encryption.key"

Logging Configuration
---------------------

.. code-block:: yaml

   logging:
     # Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
     level: "INFO"
     
     # Log outputs
     handlers:
       console:
         enabled: true
         format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
       
       file:
         enabled: true
         path: "logs/database.log"
         max_bytes: 10485760  # 10MB
         backup_count: 5
         format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
     
     # SQL logging
     sql:
       echo: false  # Log SQL statements
       echo_pool: false  # Log pool events
       format: "pretty"  # pretty or compact

Migration Configuration
-----------------------

Alembic Setup
~~~~~~~~~~~~~

.. code-block:: ini

   # alembic.ini
   [alembic]
   script_location = database/migrations
   sqlalchemy.url = sqlite:///data/twin_database.db
   
   [loggers]
   keys = root,sqlalchemy,alembic
   
   [handlers]
   keys = console
   
   [formatters]
   keys = generic

Migration Commands
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Initialize migrations
   alembic init database/migrations
   
   # Create a migration
   alembic revision --autogenerate -m "Add new column"
   
   # Apply migrations
   alembic upgrade head
   
   # Rollback
   alembic downgrade -1

Testing Configuration
---------------------

Test Database
~~~~~~~~~~~~~

.. code-block:: yaml

   # config/test_database.yaml
   test:
     database:
       connection:
         type: "sqlite"
         path: ":memory:"  # In-memory for tests
       
       pool:
         size: 1  # Single connection for tests
       
       logging:
         echo: true  # Verbose logging for debugging

Fixtures
~~~~~~~~

.. code-block:: python

   # tests/conftest.py
   import pytest
   from sqlmodel import Session, create_engine
   from database.models import SQLModel
   
   @pytest.fixture
   def test_engine():
       engine = create_engine("sqlite:///:memory:")
       SQLModel.metadata.create_all(engine)
       return engine
   
   @pytest.fixture
   def test_session(test_engine):
       with Session(test_engine) as session:
           yield session