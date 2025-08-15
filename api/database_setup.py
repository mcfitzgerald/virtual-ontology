#!/usr/bin/env python3
"""
Database Initialization System - Main Orchestrator
Provides comprehensive database initialization, cleaning, and verification functionality
"""

import os
import sys
import json
import sqlite3
import shutil
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.setup.twin_tables import TwinTablesManager
from api.setup.mes_historical import MESHistoricalDataGenerator


class DatabaseSetupOrchestrator:
    """Main orchestrator for database initialization and management"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the orchestrator with configuration"""
        
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
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(project_root, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'database_setup.log')),
                logging.StreamHandler()  # Console output
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
            # Ensure data directory exists
            db_dir = os.path.dirname(self.db_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                self.logger.info(f"Created database directory: {db_dir}")
            
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
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
    
    def initialize_fresh_database(self, populate_sample_data: bool = True, 
                                  generate_historical: bool = False,
                                  historical_start_date: Optional[str] = None,
                                  historical_end_date: Optional[str] = None) -> bool:
        """Initialize a fresh database with all tables and optional sample data"""
        
        self.logger.info("=" * 60)
        self.logger.info(" INITIALIZING FRESH DATABASE")
        self.logger.info("=" * 60)
        
        try:
            conn = self._get_database_connection()
            
            # Create all tables
            if not self.twin_tables_manager.create_all_tables(conn):
                self.logger.error("Failed to create tables")
                return False
            
            # Create indexes
            if not self.twin_tables_manager.create_indexes(conn):
                self.logger.error("Failed to create indexes")
                return False
            
            # Populate equipment metadata (always needed)
            if not self.twin_tables_manager.populate_equipment_metadata(conn):
                self.logger.error("Failed to populate equipment metadata")
                return False
            
            # Populate alert configurations
            if not self.twin_tables_manager.populate_alert_config(conn):
                self.logger.error("Failed to populate alert configurations")
                return False
            
            # Populate sample data if requested
            if populate_sample_data:
                twin_config = self.config.get('twin_tables', {})
                
                if twin_config.get('quality_data', {}).get('populate_sample_data', False):
                    sample_days = twin_config.get('quality_data', {}).get('sample_days', 30)
                    if not self.twin_tables_manager.populate_sample_quality_data(conn, sample_days):
                        self.logger.error("Failed to populate sample quality data")
                        return False
                
                if twin_config.get('sensor_data', {}).get('populate_sample_data', False):
                    sample_hours = twin_config.get('sensor_data', {}).get('sample_hours', 24)
                    if not self.twin_tables_manager.populate_sample_sensor_data(conn, sample_hours):
                        self.logger.error("Failed to populate sample sensor data")
                        return False
            
            # Generate historical MES data if requested
            if generate_historical:
                if not self._generate_historical_data(conn, historical_start_date, historical_end_date):
                    self.logger.error("Failed to generate historical data")
                    return False
            
            # Verify database setup
            table_counts = self.twin_tables_manager.verify_database_setup(conn)
            
            conn.close()
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info(" DATABASE INITIALIZATION COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 60)
            self.logger.info(f"Database location: {self.db_path}")
            self.logger.info(f"Total tables: {len(table_counts)}")
            for table_name, count in table_counts.items():
                self.logger.info(f"  - {table_name}: {count:,} records")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            return False
    
    def clean_database(self, preserve_structure: bool = True) -> bool:
        """Clean/flush existing database data"""
        
        self.logger.info("=" * 60)
        self.logger.info(" CLEANING DATABASE")
        self.logger.info("=" * 60)
        
        try:
            # Create backup if requested
            if self.backup_on_clean:
                backup_path = self._backup_database()
                if backup_path:
                    self.logger.info(f"Backup created: {backup_path}")
            
            conn = self._get_database_connection()
            
            # Clean all twin tables
            if not self.twin_tables_manager.clean_all_data(conn, preserve_structure):
                self.logger.error("Failed to clean database")
                return False
            
            # If not preserving structure, recreate tables
            if not preserve_structure:
                if not self.twin_tables_manager.create_all_tables(conn):
                    self.logger.error("Failed to recreate tables after cleanup")
                    return False
                
                if not self.twin_tables_manager.create_indexes(conn):
                    self.logger.error("Failed to recreate indexes after cleanup")
                    return False
            
            conn.close()
            
            self.logger.info("✅ Database cleaning completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clean database: {e}")
            return False
    
    def reset_to_pristine(self, no_backup: bool = False) -> bool:
        """Reset database to pristine state - complete nuke and rebuild
        
        This performs:
        1. Backup current database (unless no_backup is True)
        2. Drop all tables
        3. Recreate all tables with fresh schema
        4. Initialize essential metadata
        5. Clear all file-based configs
        6. Reset query logs
        
        Args:
            no_backup: If True, skip backup creation (useful for CI/CD)
            
        Returns:
            True if reset successful, False otherwise
        """
        self.logger.info("=" * 60)
        self.logger.info(" RESETTING DATABASE TO PRISTINE STATE")
        self.logger.info("=" * 60)
        
        try:
            # Step 1: Backup if requested
            if not no_backup and self.backup_on_clean:
                backup_path = self._backup_database()
                if backup_path:
                    self.logger.info(f"Backup created: {backup_path}")
            
            # Step 2: Clear file-based configs
            config_dir = os.path.join(project_root, 'twin', 'configs')
            if os.path.exists(config_dir):
                import shutil
                # Keep only the base config files
                for file in os.listdir(config_dir):
                    if file.startswith('sim-') and file.endswith('.json'):
                        os.remove(os.path.join(config_dir, file))
                self.logger.info(f"Cleared simulation configs from {config_dir}")
            
            # Step 3: Reset query logs
            query_log_path = os.path.join(project_root, 'learning_history', 'query_logs.json')
            if os.path.exists(query_log_path):
                with open(query_log_path, 'w') as f:
                    f.write('[]')
                self.logger.info("Reset query logs")
            
            # Step 4: Drop and recreate database
            conn = self._get_database_connection()
            
            # Drop all tables
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            for table in tables:
                if not table[0].startswith('sqlite_'):
                    cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
            conn.commit()
            self.logger.info(f"Dropped {len(tables)} tables")
            
            # Recreate all tables
            if not self.twin_tables_manager.create_all_tables(conn):
                self.logger.error("Failed to recreate tables")
                return False
            
            if not self.twin_tables_manager.create_indexes(conn):
                self.logger.error("Failed to create indexes")
                return False
            
            # Initialize essential metadata
            if not self.twin_tables_manager.populate_equipment_metadata(conn):
                self.logger.error("Failed to populate equipment metadata")
                return False
            
            if not self.twin_tables_manager.populate_alert_config(conn):
                self.logger.error("Failed to populate alert config")
                return False
            
            conn.close()
            
            # Step 5: Create fresh MES tables via SQLModel
            # Need to ensure we're in the right directory context
            import sys
            from pathlib import Path
            
            # Save current directory and change to API dir for relative imports
            original_dir = os.getcwd()
            api_dir = os.path.join(project_root, 'api')
            os.chdir(api_dir)
            
            try:
                from database import create_db_and_tables
                create_db_and_tables()
            finally:
                # Restore original directory
                os.chdir(original_dir)
            
            self.logger.info("✅ Database reset to pristine state successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset database: {e}")
            return False
    
    def verify_database(self, detailed: bool = False) -> bool:
        """Verify database state and integrity"""
        
        self.logger.info("=" * 60)
        self.logger.info(" VERIFYING DATABASE")
        self.logger.info("=" * 60)
        
        try:
            if not os.path.exists(self.db_path):
                self.logger.error(f"Database file does not exist: {self.db_path}")
                return False
            
            conn = self._get_database_connection()
            
            # Get database info
            file_size = os.path.getsize(self.db_path)
            self.logger.info(f"Database file: {self.db_path}")
            self.logger.info(f"File size: {file_size:,} bytes ({file_size/(1024*1024):.1f} MB)")
            
            # Verify tables and data
            table_counts = self.twin_tables_manager.verify_database_setup(conn)
            
            if detailed:
                self.logger.info("\nDetailed verification:")
                self._perform_detailed_verification(conn)
            
            conn.close()
            
            # Summary
            total_records = sum(table_counts.values())
            self.logger.info(f"\nSummary:")
            self.logger.info(f"  - Tables: {len(table_counts)}")
            self.logger.info(f"  - Total records: {total_records:,}")
            
            # Check for potential issues
            issues = []
            if total_records == 0:
                issues.append("Database appears to be empty")
            
            if 'equipment_metadata' in table_counts and table_counts['equipment_metadata'] == 0:
                issues.append("No equipment metadata found")
            
            if issues:
                self.logger.warning("Potential issues found:")
                for issue in issues:
                    self.logger.warning(f"  - {issue}")
            else:
                self.logger.info("✅ Database verification completed - no issues found")
            
            return len(issues) == 0
            
        except Exception as e:
            self.logger.error(f"Failed to verify database: {e}")
            return False
    
    def _perform_detailed_verification(self, conn: sqlite3.Connection):
        """Perform detailed database verification"""
        cursor = conn.cursor()
        
        try:
            # Check foreign key integrity
            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
            if fk_violations:
                self.logger.warning(f"Foreign key violations found: {len(fk_violations)}")
                for violation in fk_violations[:5]:  # Show first 5
                    self.logger.warning(f"  - {violation}")
            else:
                self.logger.info("✅ No foreign key violations found")
            
            # Check for recent data
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('quality_data', 'sensor_data')
            """)
            time_tables = [row[0] for row in cursor.fetchall()]
            
            for table in time_tables:
                cursor.execute(f"""
                    SELECT MAX(timestamp) as latest, MIN(timestamp) as earliest, COUNT(*) as count
                    FROM {table}
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    self.logger.info(f"  - {table}: {result[2]} records from {result[1]} to {result[0]}")
            
            # Check equipment metadata completeness
            cursor.execute("SELECT COUNT(*) FROM equipment_metadata")
            equip_count = cursor.fetchone()[0]
            if equip_count > 0:
                cursor.execute("SELECT COUNT(*) FROM equipment_metadata WHERE manufacturer IS NULL")
                null_manufacturer = cursor.fetchone()[0]
                if null_manufacturer > 0:
                    self.logger.warning(f"  - {null_manufacturer} equipment records missing manufacturer")
            
        except Exception as e:
            self.logger.warning(f"Error during detailed verification: {e}")
    
    def _generate_historical_data(self, conn: sqlite3.Connection, start_date: Optional[str] = None, 
                                  end_date: Optional[str] = None) -> bool:
        """Generate historical MES data"""
        try:
            # Parse dates
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                default_range = self.config.get('historical_data_generation', {}).get('default_date_range', {})
                start_dt = datetime.strptime(default_range.get('start', '2025-06-01'), '%Y-%m-%d')
            
            if end_date:
                end_dt = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            else:
                default_range = self.config.get('historical_data_generation', {}).get('default_date_range', {})
                end_dt = datetime.strptime(default_range.get('end', '2025-06-14') + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            
            self.logger.info(f"Generating historical data from {start_dt} to {end_dt}")
            
            # Generate data
            mes_data = self.historical_generator.generate_mes_data(start_dt, end_dt)
            
            # Save to database
            if not self.historical_generator.save_to_database(mes_data, 'mes_data'):
                self.logger.error("Failed to save historical data to database")
                return False
            
            # Generate and log summary statistics
            summary = self.historical_generator.generate_summary_statistics(mes_data)
            self.logger.info(f"Historical data summary: {summary}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate historical data: {e}")
            return False
    
    def generate_sample_data_only(self, output_format: str = 'csv', 
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> bool:
        """Generate sample MES data without affecting database structure"""
        
        self.logger.info("=" * 60)
        self.logger.info(" GENERATING SAMPLE DATA")
        self.logger.info("=" * 60)
        
        try:
            # Parse dates
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                default_range = self.config.get('historical_data_generation', {}).get('default_date_range', {})
                start_dt = datetime.strptime(default_range.get('start', '2025-06-01'), '%Y-%m-%d')
            
            if end_date:
                end_dt = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            else:
                default_range = self.config.get('historical_data_generation', {}).get('default_date_range', {})
                end_dt = datetime.strptime(default_range.get('end', '2025-06-14') + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            
            self.logger.info(f"Generating sample data from {start_dt} to {end_dt}")
            
            # Generate data
            mes_data = self.historical_generator.generate_mes_data(start_dt, end_dt)
            
            # Save based on format
            if output_format in ['csv', 'both']:
                output_file = os.path.join(project_root, 'data', 'mes_data_with_kpis.csv')
                if not self.historical_generator.save_to_csv(mes_data, output_file):
                    return False
            
            if output_format in ['db', 'both']:
                if not self.historical_generator.save_to_database(mes_data, 'mes_data'):
                    return False
            
            # Generate and display summary
            summary = self.historical_generator.generate_summary_statistics(mes_data)
            self.logger.info("Sample data generation completed successfully")
            self.logger.info(f"Summary: {json.dumps(summary, indent=2)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate sample data: {e}")
            return False


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Database Initialization System for Virtual Twin',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s init                     # Initialize fresh database with sample data
  %(prog)s clean                    # Clean database (preserve structure)  
  %(prog)s clean --drop-tables      # Clean database (drop all tables)
  %(prog)s reset                    # Reset to pristine state (complete rebuild)
  %(prog)s reset --no-backup        # Reset without backup (CI/CD)
  %(prog)s verify                   # Verify database state
  %(prog)s verify --detailed        # Verify with detailed checks
  %(prog)s generate --format csv    # Generate sample data to CSV
  %(prog)s init --historical        # Initialize with historical MES data
        """
    )
    
    parser.add_argument('action', choices=['init', 'clean', 'verify', 'generate', 'reset'],
                       help='Action to perform')
    parser.add_argument('--config', type=str, 
                       help='Path to configuration file')
    parser.add_argument('--no-sample-data', action='store_true',
                       help='Skip sample data population during init')
    parser.add_argument('--historical', action='store_true',
                       help='Generate historical MES data during init')
    parser.add_argument('--start-date', type=str,
                       help='Start date for historical data (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                       help='End date for historical data (YYYY-MM-DD)')
    parser.add_argument('--drop-tables', action='store_true',
                       help='Drop all tables during clean (default: preserve structure)')
    parser.add_argument('--detailed', action='store_true',
                       help='Perform detailed verification')
    parser.add_argument('--format', choices=['csv', 'db', 'both'], default='csv',
                       help='Output format for generate action')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup during reset (useful for CI/CD)')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = DatabaseSetupOrchestrator(args.config)
    
    success = False
    
    try:
        if args.action == 'init':
            success = orchestrator.initialize_fresh_database(
                populate_sample_data=not args.no_sample_data,
                generate_historical=args.historical,
                historical_start_date=args.start_date,
                historical_end_date=args.end_date
            )
        
        elif args.action == 'clean':
            success = orchestrator.clean_database(
                preserve_structure=not args.drop_tables
            )
        
        elif args.action == 'verify':
            success = orchestrator.verify_database(detailed=args.detailed)
        
        elif args.action == 'generate':
            success = orchestrator.generate_sample_data_only(
                output_format=args.format,
                start_date=args.start_date,
                end_date=args.end_date
            )
        
        elif args.action == 'reset':
            success = orchestrator.reset_to_pristine(
                no_backup=args.no_backup
            )
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
    
    if success:
        print("\n🚀 Operation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Operation failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()