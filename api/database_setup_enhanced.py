#!/usr/bin/env python3
"""
Enhanced Database Setup with Granular Cleaning
Provides selective cleaning of specific data categories
"""

import os
import sys
import json
import sqlite3
import shutil
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.setup.twin_tables import TwinTablesManager
from api.setup.mes_historical import MESHistoricalDataGenerator


# Define table categories for selective cleaning
TABLE_CATEGORIES = {
    'historical': [
        'mes_data',
        'kpi_results'
    ],
    'simulation': [
        'simulation_data',
        'twin_runs',
        'twin_state',
        'parameter_history'
    ],
    'optimization': [
        'optimization_results',
        'recommendations'
    ],
    'monitoring': [
        'quality_data',
        'sensor_data',
        'alert_config'
    ],
    'metadata': [
        'equipment_metadata',
        'entity_sync_metadata',
        'provenance_records'
    ],
    'logs': [
        'sync_health_log',
        'confidence_tracking'
    ]
}


class EnhancedDatabaseManager:
    """Enhanced database manager with granular cleaning capabilities"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the manager with configuration"""
        
        # Set up logging first
        self._setup_logging()
        
        # Load configuration
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'setup', 'config.json')
        
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Initialize managers
        self.twin_tables_manager = TwinTablesManager(self.config)
        self.historical_generator = MESHistoricalDataGenerator(self.config)
        
        # Database configuration
        db_config = self.config.get('database', {})
        self.db_path = db_config.get('path', 'data/mes_database.db')
        if not os.path.isabs(self.db_path):
            self.db_path = os.path.join(project_root, self.db_path)
        
        self.backup_on_clean = db_config.get('backup_on_clean', True)
        self.timeout = db_config.get('timeout_seconds', 30)
    
    def _setup_logging(self):
        """Set up logging configuration"""
        log_dir = os.path.join(project_root, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'database_setup.log')),
                logging.StreamHandler()
            ]
        )
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load config from {config_path}: {e}")
            sys.exit(1)
    
    def _get_database_connection(self) -> sqlite3.Connection:
        """Get database connection with proper timeout"""
        try:
            db_dir = os.path.dirname(self.db_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                self.logger.info(f"Created database directory: {db_dir}")
            
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database {self.db_path}: {e}")
            raise
    
    def _backup_database(self) -> Optional[str]:
        """Create a backup of the current database"""
        if not os.path.exists(self.db_path):
            self.logger.info("No existing database to backup")
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.backup_{timestamp}"
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backed up to: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            return None
    
    def get_all_tables(self, conn: sqlite3.Connection) -> List[str]:
        """Get list of all tables in database"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def clean_specific_tables(self, conn: sqlite3.Connection, 
                             tables: List[str], 
                             preserve: List[str] = None) -> bool:
        """Clean specific tables while preserving others"""
        
        preserve = preserve or []
        all_tables = self.get_all_tables(conn)
        
        # Filter out preserved tables
        tables_to_clean = [t for t in tables if t in all_tables and t not in preserve]
        
        if not tables_to_clean:
            self.logger.info("No tables to clean after applying preservation rules")
            return True
        
        self.logger.info(f"Cleaning tables: {tables_to_clean}")
        
        try:
            cursor = conn.cursor()
            
            # Disable foreign keys temporarily for cleaning
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            for table in tables_to_clean:
                try:
                    # Get row count before cleaning
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    # Clean the table
                    cursor.execute(f"DELETE FROM {table}")
                    
                    # Reset auto-increment
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                    
                    self.logger.info(f"  ✓ Cleaned {table} ({count} records removed)")
                    
                except Exception as e:
                    self.logger.warning(f"  ✗ Failed to clean {table}: {e}")
            
            # Re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Vacuum to reclaim space
            if len(tables_to_clean) > 5:  # Only vacuum for significant cleanups
                self.logger.info("Running VACUUM to optimize database...")
                conn.execute("VACUUM")
            
            conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed during table cleaning: {e}")
            conn.rollback()
            return False
    
    def clean_by_category(self, conn: sqlite3.Connection, 
                         category: str, 
                         preserve: List[str] = None) -> bool:
        """Clean all tables in a specific category"""
        
        if category not in TABLE_CATEGORIES:
            self.logger.error(f"Unknown category: {category}")
            self.logger.info(f"Available categories: {list(TABLE_CATEGORIES.keys())}")
            return False
        
        tables = TABLE_CATEGORIES[category]
        self.logger.info(f"Cleaning category '{category}': {tables}")
        
        return self.clean_specific_tables(conn, tables, preserve)
    
    def clean_by_pattern(self, conn: sqlite3.Connection, 
                        pattern: str, 
                        preserve: List[str] = None) -> bool:
        """Clean tables matching a pattern"""
        
        all_tables = self.get_all_tables(conn)
        
        # Find matching tables
        import re
        regex = re.compile(pattern)
        matching_tables = [t for t in all_tables if regex.search(t)]
        
        if not matching_tables:
            self.logger.warning(f"No tables match pattern: {pattern}")
            return True
        
        self.logger.info(f"Tables matching pattern '{pattern}': {matching_tables}")
        
        return self.clean_specific_tables(conn, matching_tables, preserve)
    
    def clean_by_age(self, conn: sqlite3.Connection, 
                    days_to_keep: int,
                    preserve: List[str] = None) -> bool:
        """Clean data older than specified days (where applicable)"""
        
        preserve = preserve or []
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        self.logger.info(f"Cleaning data older than {days_to_keep} days (before {cutoff_date[:10]})")
        
        # Tables with timestamp columns
        time_based_tables = {
            'mes_data': 'timestamp',
            'simulation_data': 'timestamp',
            'quality_data': 'timestamp',
            'sensor_data': 'timestamp',
            'sync_health_log': 'timestamp',
            'twin_runs': 'started_at',
            'optimization_results': 'created_at',
            'recommendations': 'created_at',
            'provenance_records': 'started_at'
        }
        
        try:
            cursor = conn.cursor()
            total_removed = 0
            
            for table, time_column in time_based_tables.items():
                if table in preserve:
                    continue
                
                # Check if table exists
                cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table}'
                """)
                if not cursor.fetchone():
                    continue
                
                # Count records to remove
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table} 
                    WHERE {time_column} < ?
                """, (cutoff_date,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # Delete old records
                    cursor.execute(f"""
                        DELETE FROM {table} 
                        WHERE {time_column} < ?
                    """, (cutoff_date,))
                    
                    self.logger.info(f"  ✓ Removed {count} old records from {table}")
                    total_removed += count
            
            conn.commit()
            
            if total_removed > 0:
                self.logger.info(f"Total records removed: {total_removed}")
                self.logger.info("Running VACUUM to optimize database...")
                conn.execute("VACUUM")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed during age-based cleaning: {e}")
            conn.rollback()
            return False
    
    def show_database_stats(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Show current database statistics"""
        
        stats = {
            'total_tables': 0,
            'total_records': 0,
            'categories': {},
            'table_sizes': {}
        }
        
        try:
            cursor = conn.cursor()
            all_tables = self.get_all_tables(conn)
            
            stats['total_tables'] = len(all_tables)
            
            # Get stats for each table
            for table in all_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats['table_sizes'][table] = count
                stats['total_records'] += count
            
            # Group by categories
            for category, tables in TABLE_CATEGORIES.items():
                category_count = sum(
                    stats['table_sizes'].get(t, 0) 
                    for t in tables 
                    if t in stats['table_sizes']
                )
                if category_count > 0:
                    stats['categories'][category] = {
                        'tables': [t for t in tables if t in stats['table_sizes']],
                        'total_records': category_count
                    }
            
            # Database file size
            if os.path.exists(self.db_path):
                file_size = os.path.getsize(self.db_path)
                stats['file_size_mb'] = round(file_size / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return stats


def main():
    """Enhanced CLI interface for database management"""
    
    parser = argparse.ArgumentParser(
        description='Enhanced Database Management with Granular Cleaning',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show database statistics
  %(prog)s stats
  
  # Clean specific category
  %(prog)s clean --category historical
  %(prog)s clean --category simulation --preserve twin_runs
  
  # Clean specific tables
  %(prog)s clean --tables mes_data,simulation_data
  
  # Clean by pattern
  %(prog)s clean --pattern ".*_log$"  # Clean all log tables
  
  # Clean old data
  %(prog)s clean --older-than 30  # Remove data older than 30 days
  
  # Combine options
  %(prog)s clean --category logs --older-than 7
  
Available categories:
  - historical: Historical MES data tables
  - simulation: Simulation and twin run data
  - optimization: Optimization results and recommendations
  - monitoring: Quality, sensor, and alert data
  - metadata: Equipment and entity metadata
  - logs: System and health logs
        """
    )
    
    parser.add_argument('action', choices=['clean', 'stats', 'list'],
                       help='Action to perform')
    parser.add_argument('--config', default=None,
                       help='Path to configuration file')
    
    # Cleaning options
    clean_group = parser.add_argument_group('cleaning options')
    clean_group.add_argument('--category', type=str,
                            help='Clean specific category of tables')
    clean_group.add_argument('--tables', type=str,
                            help='Comma-separated list of specific tables to clean')
    clean_group.add_argument('--pattern', type=str,
                            help='Regex pattern to match table names')
    clean_group.add_argument('--older-than', type=int,
                            help='Remove data older than N days')
    clean_group.add_argument('--preserve', type=str,
                            help='Comma-separated list of tables to preserve')
    clean_group.add_argument('--no-backup', action='store_true',
                            help='Skip backup before cleaning')
    clean_group.add_argument('--drop-tables', action='store_true',
                            help='Drop tables instead of just cleaning data')
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = EnhancedDatabaseManager(args.config)
    
    if args.action == 'stats':
        # Show database statistics
        conn = manager._get_database_connection()
        stats = manager.show_database_stats(conn)
        
        print("\n" + "=" * 60)
        print(" DATABASE STATISTICS")
        print("=" * 60)
        print(f"\nDatabase: {manager.db_path}")
        print(f"File size: {stats.get('file_size_mb', 0)} MB")
        print(f"Total tables: {stats['total_tables']}")
        print(f"Total records: {stats['total_records']:,}")
        
        if stats['categories']:
            print("\nBy Category:")
            for category, info in stats['categories'].items():
                print(f"  {category}: {info['total_records']:,} records across {len(info['tables'])} tables")
        
        if stats['table_sizes']:
            print("\nTop 10 Tables by Record Count:")
            sorted_tables = sorted(stats['table_sizes'].items(), key=lambda x: x[1], reverse=True)[:10]
            for table, count in sorted_tables:
                print(f"  {table:30} {count:>10,} records")
        
        conn.close()
        
    elif args.action == 'list':
        # List all tables grouped by category
        conn = manager._get_database_connection()
        all_tables = set(manager.get_all_tables(conn))
        
        print("\n" + "=" * 60)
        print(" DATABASE TABLES BY CATEGORY")
        print("=" * 60)
        
        for category, tables in TABLE_CATEGORIES.items():
            existing = [t for t in tables if t in all_tables]
            if existing:
                print(f"\n{category.upper()}:")
                for table in existing:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {table:30} {count:>10,} records")
        
        # Show uncategorized tables
        categorized = set()
        for tables in TABLE_CATEGORIES.values():
            categorized.update(tables)
        
        uncategorized = all_tables - categorized
        if uncategorized:
            print("\nUNCATEGORIZED:")
            for table in sorted(uncategorized):
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table:30} {count:>10,} records")
        
        conn.close()
        
    elif args.action == 'clean':
        # Perform cleaning based on options
        
        # Backup unless disabled
        if not args.no_backup:
            backup_path = manager._backup_database()
            if backup_path:
                print(f"✓ Backup created: {backup_path}")
        
        conn = manager._get_database_connection()
        
        # Parse preserve list
        preserve_tables = []
        if args.preserve:
            preserve_tables = [t.strip() for t in args.preserve.split(',')]
            print(f"Preserving tables: {preserve_tables}")
        
        success = True
        
        # Apply cleaning based on options
        if args.category:
            success = manager.clean_by_category(conn, args.category, preserve_tables)
        
        elif args.tables:
            tables = [t.strip() for t in args.tables.split(',')]
            success = manager.clean_specific_tables(conn, tables, preserve_tables)
        
        elif args.pattern:
            success = manager.clean_by_pattern(conn, args.pattern, preserve_tables)
        
        elif args.older_than:
            success = manager.clean_by_age(conn, args.older_than, preserve_tables)
        
        else:
            print("ERROR: Must specify at least one cleaning option")
            print("Use --help for examples")
            success = False
        
        conn.close()
        
        if success:
            print("\n✅ Cleaning completed successfully!")
        else:
            print("\n❌ Cleaning failed. Check logs for details.")
            sys.exit(1)


if __name__ == "__main__":
    main()