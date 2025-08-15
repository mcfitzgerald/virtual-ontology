"""Unified Schema Management for Virtual Twin System

This module provides a single source of truth for all database schema operations,
ensuring consistency between SQLModel and raw SQL table definitions.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class SchemaManager:
    """Central manager for all database schema operations.
    
    Ensures consistency between:
    - SQLModel table definitions (MES tables)
    - Raw SQL table definitions (Twin tables)
    - Ontology YAML specifications
    - Database indices and constraints
    """
    
    # Schema version for migration tracking
    SCHEMA_VERSION = "1.3.0"
    
    # Core MES tables (managed by SQLModel)
    SQLMODEL_TABLES = {
        'mes_data',
        'simulation_data',
        'twin_runs'
    }
    
    # Twin-specific tables (managed by raw SQL)
    TWIN_TABLES = {
        'optimization_results',
        'provenance_records',
        'equipment_metadata',
        'quality_data',
        'sensor_data',
        'alert_config',
        'parameter_history',
        'simulation_configs',
        'twin_state',
        'recommendations',
        'confidence_tracking',
        'kpi_results',
        'sync_health_log',
        'entity_sync_metadata'
    }
    
    # Note: simulation_data and twin_runs are in SQLMODEL_TABLES
    # but documented in twin_database_schema.yaml because they're
    # primarily used by the twin system
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the schema manager.
        
        Args:
            db_path: Path to the SQLite database. If None, uses default.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "mes_database.db"
        
        self.db_path = Path(db_path)
        
    def get_all_tables(self) -> Set[str]:
        """Get the complete set of all managed tables.
        
        Returns:
            Set of all table names managed by the system
        """
        return self.SQLMODEL_TABLES.union(self.TWIN_TABLES)
    
    def verify_schema(self) -> Dict[str, Any]:
        """Verify the database schema against expected definitions.
        
        Returns:
            Dictionary with verification results including:
            - missing_tables: Tables that should exist but don't
            - extra_tables: Tables that exist but aren't documented
            - schema_version: Current schema version
            - is_valid: Boolean indicating if schema is valid
        """
        results = {
            'missing_tables': [],
            'extra_tables': [],
            'schema_version': self.SCHEMA_VERSION,
            'is_valid': True,
            'table_counts': {}
        }
        
        expected_tables = self.get_all_tables()
        
        with sqlite3.connect(self.db_path) as conn:
            # Get actual tables
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            actual_tables = {row[0] for row in cursor.fetchall()}
            
            # Find discrepancies
            results['missing_tables'] = list(expected_tables - actual_tables)
            results['extra_tables'] = list(actual_tables - expected_tables)
            
            # Get row counts for existing tables
            for table in actual_tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                results['table_counts'][table] = cursor.fetchone()[0]
            
            # Check schema version (stored in a metadata table if it exists)
            try:
                cursor = conn.execute("""
                    SELECT value FROM schema_metadata 
                    WHERE key = 'version'
                """)
                row = cursor.fetchone()
                if row:
                    results['stored_version'] = row[0]
            except sqlite3.OperationalError:
                # schema_metadata table doesn't exist yet
                results['stored_version'] = None
        
        # Determine validity
        results['is_valid'] = (
            len(results['missing_tables']) == 0 and
            len(results['extra_tables']) == 0
        )
        
        return results
    
    def initialize_schema_tracking(self, conn: sqlite3.Connection) -> None:
        """Initialize schema version tracking table.
        
        Args:
            conn: Active database connection
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            INSERT OR REPLACE INTO schema_metadata (key, value, updated_at)
            VALUES ('version', ?, CURRENT_TIMESTAMP)
        """, (self.SCHEMA_VERSION,))
        
        conn.execute("""
            INSERT OR REPLACE INTO schema_metadata (key, value, updated_at)
            VALUES ('last_migration', ?, CURRENT_TIMESTAMP)
        """, (datetime.now().isoformat(),))
        
        conn.commit()
    
    def create_all_twin_tables(self, conn: sqlite3.Connection) -> bool:
        """Create all twin-specific tables using raw SQL.
        
        This delegates to the existing TwinTablesManager for now,
        but provides a unified interface.
        
        Args:
            conn: Active database connection
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from api.setup.twin_tables import TwinTablesManager
            from api.setup.config import load_config
            
            config = load_config()
            manager = TwinTablesManager(config)
            
            # Create tables
            if not manager.create_all_tables(conn):
                logger.error("Failed to create twin tables")
                return False
            
            # Create indexes
            if not manager.create_indexes(conn):
                logger.error("Failed to create indexes")
                return False
            
            # Initialize schema tracking
            self.initialize_schema_tracking(conn)
            
            logger.info("✅ All twin tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create twin tables: {e}")
            return False
    
    def create_all_sqlmodel_tables(self) -> bool:
        """Create all SQLModel-managed tables.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            import sys
            import os
            from pathlib import Path
            
            # Need to be in API directory for imports
            original_dir = os.getcwd()
            api_dir = Path(__file__).parent.parent / "api"
            os.chdir(api_dir)
            
            try:
                from database import create_db_and_tables
                create_db_and_tables()
                logger.info("✅ SQLModel tables created successfully")
                return True
            finally:
                os.chdir(original_dir)
                
        except Exception as e:
            logger.error(f"Failed to create SQLModel tables: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific table.
        
        Args:
            table_name: Name of the table to inspect
            
        Returns:
            Dictionary with table information or None if table doesn't exist
        """
        if table_name not in self.get_all_tables():
            return None
        
        info = {
            'name': table_name,
            'type': 'sqlmodel' if table_name in self.SQLMODEL_TABLES else 'twin',
            'columns': [],
            'indexes': [],
            'foreign_keys': [],
            'row_count': 0
        }
        
        with sqlite3.connect(self.db_path) as conn:
            # Get table info
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            for row in cursor:
                info['columns'].append({
                    'name': row[1],
                    'type': row[2],
                    'nullable': not row[3],
                    'default': row[4],
                    'primary_key': bool(row[5])
                })
            
            # Get indexes
            cursor = conn.execute(f"PRAGMA index_list({table_name})")
            for row in cursor:
                info['indexes'].append(row[1])
            
            # Get foreign keys
            cursor = conn.execute(f"PRAGMA foreign_key_list({table_name})")
            for row in cursor:
                info['foreign_keys'].append({
                    'column': row[3],
                    'references_table': row[2],
                    'references_column': row[4]
                })
            
            # Get row count
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            info['row_count'] = cursor.fetchone()[0]
        
        return info
    
    def validate_against_ontology(self) -> Dict[str, Any]:
        """Validate database schema against ontology YAML definitions.
        
        Returns:
            Validation results dictionary
        """
        import yaml
        
        results = {
            'mes_ontology_valid': False,
            'twin_ontology_valid': False,
            'discrepancies': []
        }
        
        # Load ontology YAMLs
        ontology_dir = Path(__file__).parent.parent / "ontology"
        
        try:
            # Load MES database schema
            with open(ontology_dir / "database_schema.yaml", 'r') as f:
                mes_schema = yaml.safe_load(f)
            
            # Load Twin database schema
            with open(ontology_dir / "twin_database_schema.yaml", 'r') as f:
                twin_schema = yaml.safe_load(f)
            
            # Validate MES tables
            mes_table = mes_schema.get('table', {}).get('name')
            if mes_table and mes_table in self.SQLMODEL_TABLES:
                results['mes_ontology_valid'] = True
            else:
                results['discrepancies'].append(
                    f"MES ontology references table '{mes_table}' not in SQLMODEL_TABLES"
                )
            
            # Validate Twin tables
            twin_tables = {t['name'] for t in twin_schema.get('tables', [])}
            # Account for tables that are in SQLMODEL_TABLES but documented in twin ontology
            all_managed_tables = self.TWIN_TABLES.union(self.SQLMODEL_TABLES)
            missing = twin_tables - all_managed_tables
            if not missing:
                results['twin_ontology_valid'] = True
            else:
                for table in missing:
                    results['discrepancies'].append(
                        f"Twin ontology references table '{table}' not managed by system"
                    )
            
        except Exception as e:
            results['error'] = str(e)
        
        return results


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Schema Management Utility')
    parser.add_argument('action', choices=['verify', 'info', 'validate'],
                       help='Action to perform')
    parser.add_argument('--table', help='Table name for info action')
    parser.add_argument('--db-path', help='Database path')
    
    args = parser.parse_args()
    
    manager = SchemaManager(args.db_path)
    
    if args.action == 'verify':
        results = manager.verify_schema()
        print(f"Schema Version: {results['schema_version']}")
        print(f"Valid: {results['is_valid']}")
        if results['missing_tables']:
            print(f"Missing tables: {results['missing_tables']}")
        if results['extra_tables']:
            print(f"Extra tables: {results['extra_tables']}")
        print(f"Table counts: {results['table_counts']}")
    
    elif args.action == 'info':
        if not args.table:
            print("Table name required for info action")
        else:
            info = manager.get_table_info(args.table)
            if info:
                print(f"Table: {info['name']} ({info['type']})")
                print(f"Columns: {len(info['columns'])}")
                print(f"Indexes: {info['indexes']}")
                print(f"Row count: {info['row_count']}")
            else:
                print(f"Table {args.table} not found")
    
    elif args.action == 'validate':
        results = manager.validate_against_ontology()
        print(f"MES Ontology Valid: {results['mes_ontology_valid']}")
        print(f"Twin Ontology Valid: {results['twin_ontology_valid']}")
        if results['discrepancies']:
            print("Discrepancies:")
            for d in results['discrepancies']:
                print(f"  - {d}")