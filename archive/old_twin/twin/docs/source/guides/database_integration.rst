.. _database_integration:

====================
Database Integration
====================

.. note::
   This guide covers database integration features introduced in v1.3.0.

Overview
--------

The Virtual Twin system provides tight integration between the twin module, database layer, 
and API services. This guide covers database management features, configuration storage, 
and integration patterns.

Database Reset & Management
---------------------------

Pristine Reset Capability
^^^^^^^^^^^^^^^^^^^^^^^^^^

The system provides a complete "nuke and rebuild" capability for resetting the database 
to a pristine state::

    # Reset to pristine state (with backup)
    python api/database_setup.py reset

    # Reset without backup (useful for CI/CD)
    python api/database_setup.py reset --no-backup

What Reset Does
^^^^^^^^^^^^^^^

1. **Creates backup** (unless ``--no-backup`` specified)
2. **Drops all tables** - Complete database cleanup
3. **Recreates schema** - Fresh table structure
4. **Initializes metadata** - Equipment and alert configurations
5. **Clears file configs** - Removes all ``twin/configs/sim-*.json`` files
6. **Resets query logs** - Clears ``learning_history/query_logs.json``

Other Database Commands
^^^^^^^^^^^^^^^^^^^^^^^

::

    # Initialize fresh database with sample data
    python api/database_setup.py init

    # Clean data but preserve structure
    python api/database_setup.py clean

    # Verify database integrity
    python api/database_setup.py verify

    # Detailed verification
    python api/database_setup.py verify --detailed

Configuration Storage
---------------------

Database-Only Storage
^^^^^^^^^^^^^^^^^^^^^

Simulation configurations are now stored exclusively in the database, eliminating file clutter:

.. code-block:: python

    from twin.config_manager import ConfigurationManager

    # Configs are automatically stored in database
    config_manager = ConfigurationManager()
    config_id = config_manager.store_config(
        run_id="sim-20250815-123456",
        config=config_dict,
        config_type="generator",  # or "full", "delta", "base"
        description="Simulation with adjusted parameters"
    )

    # Retrieve config
    config = config_manager.get_config(config_id)

Key Benefits
^^^^^^^^^^^^

* **No file pollution** - No more ``twin/configs/*.json`` files
* **Deduplication** - Configs are hashed, identical configs share storage
* **Full traceability** - Every config linked to its simulation run
* **Database backup** - Configs included in database backups

Migration from File-Based Configs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have existing file-based configs:

.. code-block:: python

    from twin.config_manager import ConfigurationManager

    manager = ConfigurationManager()
    # Migrate all configs from twin/configs/ to database
    migrated_count = manager.migrate_file_configs("twin/configs")
    print(f"Migrated {migrated_count} configs to database")

Schema Management
-----------------

Unified Schema Manager
^^^^^^^^^^^^^^^^^^^^^^

The ``SchemaManager`` provides a single source of truth for all database operations:

.. code-block:: python

    from twin.schema_manager import SchemaManager

    manager = SchemaManager()

    # Verify schema integrity
    results = manager.verify_schema()
    print(f"Schema valid: {results['is_valid']}")
    print(f"Missing tables: {results['missing_tables']}")

    # Get table information
    info = manager.get_table_info("mes_data")
    print(f"Table type: {info['type']}")  # 'sqlmodel' or 'twin'
    print(f"Columns: {len(info['columns'])}")
    print(f"Row count: {info['row_count']}")

    # Validate against ontology
    validation = manager.validate_against_ontology()
    print(f"Ontology valid: {validation['mes_ontology_valid']}")

Table Categories
^^^^^^^^^^^^^^^^

The system manages two categories of tables:

**SQLModel Tables** (ORM-managed):

* ``mes_data`` - Main production data
* ``simulation_data`` - Simulation results
* ``twin_runs`` - Simulation metadata

**Twin Tables** (SQL-managed):

* ``equipment_metadata`` - Equipment definitions
* ``quality_data`` - Quality metrics
* ``sensor_data`` - Sensor readings
* ``alert_config`` - Alert thresholds
* ``optimization_results`` - Optimization outcomes
* ``recommendations`` - Generated recommendations
* ``parameter_history`` - Parameter changes
* ``simulation_configs`` - Configuration storage
* ``twin_state`` - Virtual twin state
* ``confidence_tracking`` - Statistical validation
* ``kpi_results`` - KPI calculations
* ``sync_health_log`` - Synchronization logs
* ``entity_sync_metadata`` - Entity sync status
* ``provenance_records`` - PROV-O compliant tracking

API Integration
---------------

Querying Twin Tables
^^^^^^^^^^^^^^^^^^^^

All twin tables are accessible via the API's SQL endpoint::

    # Query equipment metadata
    echo '{"sql": "SELECT * FROM equipment_metadata"}' | \
    curl -X POST http://localhost:8000/query \
      -H "Content-Type: application/json" -d @-

    # Query via query-log.sh (for logging)
    echo '{"sql": "SELECT * FROM alert_config WHERE active = 1"}' > query.json
    ./query-log.sh POST /query -d @query.json

API Status
^^^^^^^^^^

The ``api.sh status`` command shows comprehensive database statistics::

    ./api.sh status

    # Output includes:
    # - Database size
    # - Table counts for both MES and twin tables
    # - Data freshness metrics
    # - Empty tables summary

.. important::
   **Separation of Concerns**
   
   * **API Layer**: Handles SQL queries only (no natural language processing)
   * **Claude Code**: Handles all natural language to SQL translation
   * **Twin Module**: Direct database access for read-write operations
   * **query-log.sh**: Logs all queries for learning and audit

Testing Integration
-------------------

Running Integration Tests
^^^^^^^^^^^^^^^^^^^^^^^^^

The system includes comprehensive integration tests::

    # Run all integration tests
    python twin/test_integration.py

Test Coverage
^^^^^^^^^^^^^

1. **Database Reset** - Verifies complete reset to pristine state
2. **Config Storage** - Ensures configs stored in DB, not files
3. **Schema Validation** - Checks ontology alignment
4. **API Access** - Tests twin table queries
5. **Configuration Flow** - Validates config management
6. **Unified Schema** - Tests schema management
7. **Consistency** - Verifies all modules use same config

Configuration
-------------

Database Path Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

All modules use the same configuration source (``twin/config/system.yaml``):

.. code-block:: yaml

    database:
      path: "data/mes_database.db"
      api_interface: "api.sh"
      api_port: 8000

Module Configuration Access
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from twin.config_loader import ConfigLoader

    # All modules use same config
    config = ConfigLoader()
    db_path = config.get("database.path")

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**Stale Metadata After Reset**::

    # Solution: Run pristine reset
    python api/database_setup.py reset

**Config Files Still Being Created**::

    # Check simulation_runner is using latest version
    # Should use ConfigurationManager, not file writes

**Table Not Found Errors**::

    # Verify schema and recreate if needed
    python twin/schema_manager.py verify
    python api/database_setup.py reset

**API Can't Query Twin Tables**::

    # Ensure API is running
    ./api.sh restart

    # Test with curl
    curl -X POST http://localhost:8000/query \
      -H "Content-Type: application/json" \
      -d '{"sql": "SELECT COUNT(*) FROM equipment_metadata"}'

Best Practices
--------------

1. **Regular Resets**: Use pristine reset for clean testing environments
2. **No File Configs**: Always use ConfigurationManager for config storage
3. **Schema Validation**: Run schema verification before deployments
4. **Query Logging**: Use query-log.sh for audited queries
5. **Integration Testing**: Run tests after schema changes

Migration Notes
---------------

From v1.2.x to v1.3.0
^^^^^^^^^^^^^^^^^^^^^

1. **Config Storage Change**
   
   * Old: Configs stored in ``twin/configs/*.json``
   * New: Configs stored in ``simulation_configs`` table
   * Migration: Use ``ConfigurationManager.migrate_file_configs()``

2. **Schema Management**
   
   * Old: Scattered table creation
   * New: Unified ``SchemaManager``
   * Migration: Use ``python api/database_setup.py reset``

3. **Database Reset**
   
   * Old: Manual table drops
   * New: ``python api/database_setup.py reset``
   * Migration: Update scripts to use new command

Related Documentation
---------------------

* :doc:`configuration` - Configuration system guide
* :doc:`migration` - Migration from hardcoded values
* `System Architecture <https://github.com/your-org/virtual-ontology/blob/main/SYSTEM_ARCHITECTURE.md>`_
* `Database Schema <https://github.com/your-org/virtual-ontology/blob/main/DATABASE_AND_API.md>`_