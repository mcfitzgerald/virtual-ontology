"""Database Cleanup Utility for Virtual Twin System
Provides comprehensive cleanup capabilities for simulation and optimization data.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class DatabaseCleaner:
    """Manages database cleanup operations for the virtual twin system.
    
    Provides methods to clean simulation data, optimization results,
    and related metadata while preserving base MES data.
    """
    
    # Tables that should never be deleted (core MES data)
    PROTECTED_TABLES: Set[str] = {
        'mes_data',
        'equipment_metadata', 
        'product_master',
        'downtime_reasons'
    }
    
    # Tables that can be safely cleaned
    CLEANABLE_TABLES: Dict[str, str] = {
        'simulation_data': 'Simulation results data',
        'twin_runs': 'Simulation run metadata',
        'parameter_history': 'Parameter change tracking',
        'optimization_results': 'Optimization outcomes',
        'confidence_tracking': 'Confidence interval tracking',
        'sync_health_log': 'Synchronization health logs',
        'twin_state': 'Virtual twin state snapshots',
        'recommendations': 'Generated recommendations',
        'simulation_configs': 'Stored simulation configurations'
    }
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize the database cleaner.
        
        Args:
            db_path: Path to the SQLite database. If None, uses default path.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "mes_database.db"
        
        self.db_path: Path = Path(db_path)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")
    
    def get_table_stats(self) -> Dict[str, int]:
        """Get record counts for all tables.
        
        Returns:
            Dictionary mapping table names to record counts.
        """
        stats: Dict[str, int] = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = cursor.fetchall()
            
            for table_name in tables:
                table_name = table_name[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                stats[table_name] = count
        
        return stats
    
    def clean_simulation_data(
        self,
        keep_baseline: bool = True,
        older_than_days: Optional[int] = None,
        run_ids_to_keep: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Clean simulation data and related tables.
        
        Args:
            keep_baseline: If True, preserves baseline runs.
            older_than_days: Remove data older than this many days.
            run_ids_to_keep: Specific run IDs to preserve.
            
        Returns:
            Cleanup statistics including tables and records cleaned.
        """
        cleaned_stats: Dict[str, Any] = {
            'tables_cleaned': [],
            'total_removed': 0,
            'details': {}
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Build WHERE clause for filtering
            conditions = []
            params = []
            
            if keep_baseline:
                conditions.append("run_type != 'baseline'")
            
            if older_than_days:
                cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat()
                conditions.append("started_at < ?")
                params.append(cutoff)
            
            if run_ids_to_keep:
                placeholders = ','.join(['?' for _ in run_ids_to_keep])
                conditions.append(f"run_id NOT IN ({placeholders})")
                params.extend(run_ids_to_keep)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get run_ids to delete
            query = f"SELECT run_id FROM twin_runs{where_clause}"
            cursor.execute(query, params)
            run_ids_to_delete = [row[0] for row in cursor.fetchall()]
            
            if not run_ids_to_delete:
                logger.info("No simulation runs to clean")
                return cleaned_stats
            
            # Clean simulation_data
            placeholders = ','.join(['?' for _ in run_ids_to_delete])
            
            # Count records before deletion
            cursor.execute(
                f"SELECT COUNT(*) FROM simulation_data WHERE run_id IN ({placeholders})",
                run_ids_to_delete
            )
            sim_count = cursor.fetchone()[0]
            
            # Delete simulation data
            cursor.execute(
                f"DELETE FROM simulation_data WHERE run_id IN ({placeholders})",
                run_ids_to_delete
            )
            cleaned_stats['details']['simulation_data'] = sim_count
            cleaned_stats['total_removed'] += sim_count
            
            # Clean parameter_history
            cursor.execute(
                f"SELECT COUNT(*) FROM parameter_history WHERE run_id IN ({placeholders})",
                run_ids_to_delete
            )
            param_count = cursor.fetchone()[0]
            
            cursor.execute(
                f"DELETE FROM parameter_history WHERE run_id IN ({placeholders})",
                run_ids_to_delete
            )
            cleaned_stats['details']['parameter_history'] = param_count
            cleaned_stats['total_removed'] += param_count
            
            # Clean twin_runs
            cursor.execute(
                f"DELETE FROM twin_runs{where_clause}",
                params
            )
            runs_deleted = cursor.rowcount
            cleaned_stats['details']['twin_runs'] = runs_deleted
            cleaned_stats['total_removed'] += runs_deleted
            
            cleaned_stats['tables_cleaned'] = list(cleaned_stats['details'].keys())
            
            conn.commit()
            
            # Vacuum to reclaim space
            if cleaned_stats['total_removed'] > 1000:
                conn.execute("VACUUM")
                logger.info("Database vacuumed")
        
        logger.info(f"Cleaned {cleaned_stats['total_removed']} records from {len(cleaned_stats['tables_cleaned'])} tables")
        return cleaned_stats
    
    def clean_optimization_results(
        self,
        older_than_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Clean optimization results.
        
        Args:
            older_than_days: Remove results older than this many days.
            
        Returns:
            Cleanup statistics.
        """
        cleaned_stats: Dict[str, Any] = {
            'tables_cleaned': ['optimization_results'],
            'total_removed': 0
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if older_than_days:
                cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat()
                cursor.execute(
                    "DELETE FROM optimization_results WHERE created_at < ?",
                    (cutoff,)
                )
            else:
                cursor.execute("DELETE FROM optimization_results")
            
            cleaned_stats['total_removed'] = cursor.rowcount
            conn.commit()
        
        logger.info(f"Cleaned {cleaned_stats['total_removed']} optimization results")
        return cleaned_stats
    
    def clean_all_twin_data(
        self,
        preserve_mes_data: bool = True,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """Clean all twin-related data, optionally preserving MES data.
        
        Args:
            preserve_mes_data: If True, preserves core MES data tables.
            confirm: Must be True to execute this operation.
            
        Returns:
            Comprehensive cleanup statistics.
        """
        if not confirm:
            raise ValueError("Must set confirm=True to clean all twin data")
        
        cleaned_stats: Dict[str, Any] = {
            'tables_cleaned': [],
            'total_removed': 0,
            'details': {},
            'preserved_tables': []
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for table_name in self.CLEANABLE_TABLES:
                # Check if table exists
                cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """)
                if not cursor.fetchone():
                    continue
                
                # Get count before cleaning
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                before_count = cursor.fetchone()[0]
                
                if before_count > 0:
                    # Clean the table
                    cursor.execute(f"DELETE FROM {table_name}")
                    cleaned_stats['details'][table_name] = before_count
                    cleaned_stats['total_removed'] += before_count
                    cleaned_stats['tables_cleaned'].append(table_name)
                    logger.info(f"Cleaned {before_count} records from {table_name}")
            
            if preserve_mes_data:
                cleaned_stats['preserved_tables'] = list(self.PROTECTED_TABLES)
            
            conn.commit()
            
            # Vacuum to reclaim space
            if cleaned_stats['total_removed'] > 1000:
                conn.execute("VACUUM")
                logger.info("Database vacuumed")
        
        return cleaned_stats
    
    def reset_to_baseline(self) -> Dict[str, Any]:
        """Reset database to contain only MES data and baseline runs.
        
        Removes all simulation and optimization data except baseline runs.
        
        Returns:
            Cleanup statistics.
        """
        logger.info("Resetting database to baseline state")
        
        # Clean simulations but keep baseline
        stats = self.clean_simulation_data(keep_baseline=True)
        
        # Clean optimization results completely
        opt_stats = self.clean_optimization_results()
        stats['total_removed'] += opt_stats['total_removed']
        stats['tables_cleaned'].extend(opt_stats['tables_cleaned'])
        
        # Clean other twin tables
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for table in ['confidence_tracking', 'sync_health_log', 'recommendations']:
                cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table}'
                """)
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        cursor.execute(f"DELETE FROM {table}")
                        stats['total_removed'] += count
                        stats['tables_cleaned'].append(table)
                        logger.info(f"Cleaned {count} records from {table}")
            
            conn.commit()
        
        logger.info(f"Reset complete: cleaned {stats['total_removed']} records")
        return stats
    
    def get_database_size(self) -> Dict[str, Any]:
        """Get database file size and statistics.
        
        Returns:
            Dictionary with size information.
        """
        size_bytes = self.db_path.stat().st_size
        
        return {
            'path': str(self.db_path),
            'size_bytes': size_bytes,
            'size_mb': round(size_bytes / (1024 * 1024), 2),
            'size_gb': round(size_bytes / (1024 * 1024 * 1024), 3)
        }


def main():
    """Command-line interface for database cleanup."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean Virtual Twin database')
    parser.add_argument(
        '--action',
        choices=['stats', 'clean-sim', 'clean-opt', 'clean-all', 'reset'],
        default='stats',
        help='Cleanup action to perform'
    )
    parser.add_argument(
        '--older-than-days',
        type=int,
        help='Remove data older than N days'
    )
    parser.add_argument(
        '--keep-baseline',
        action='store_true',
        default=True,
        help='Preserve baseline runs'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm destructive operations'
    )
    parser.add_argument(
        '--db-path',
        help='Path to database file'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    cleaner = DatabaseCleaner(args.db_path)
    
    if args.action == 'stats':
        stats = cleaner.get_table_stats()
        size_info = cleaner.get_database_size()
        
        print(f"\nDatabase: {size_info['path']}")
        print(f"Size: {size_info['size_mb']} MB")
        print("\nTable Statistics:")
        print("-" * 50)
        
        total = 0
        for table, count in sorted(stats.items()):
            status = "🔒" if table in DatabaseCleaner.PROTECTED_TABLES else "✓"
            print(f"{status} {table:30} {count:10,} records")
            total += count
        
        print("-" * 50)
        print(f"{'Total':30} {total:10,} records")
    
    elif args.action == 'clean-sim':
        if not args.confirm:
            print("Add --confirm to execute cleanup")
            return
        
        stats = cleaner.clean_simulation_data(
            keep_baseline=args.keep_baseline,
            older_than_days=args.older_than_days
        )
        print(f"Cleaned {stats['total_removed']} records from simulation tables")
        for table, count in stats['details'].items():
            print(f"  - {table}: {count} records")
    
    elif args.action == 'clean-opt':
        if not args.confirm:
            print("Add --confirm to execute cleanup")
            return
        
        stats = cleaner.clean_optimization_results(
            older_than_days=args.older_than_days
        )
        print(f"Cleaned {stats['total_removed']} optimization results")
    
    elif args.action == 'clean-all':
        if not args.confirm:
            print("WARNING: This will delete all twin data!")
            print("Add --confirm to execute cleanup")
            return
        
        stats = cleaner.clean_all_twin_data(confirm=True)
        print(f"Cleaned {stats['total_removed']} records from {len(stats['tables_cleaned'])} tables")
        if stats['preserved_tables']:
            print(f"Preserved tables: {', '.join(stats['preserved_tables'])}")
    
    elif args.action == 'reset':
        if not args.confirm:
            print("This will reset to baseline state")
            print("Add --confirm to execute")
            return
        
        stats = cleaner.reset_to_baseline()
        print(f"Reset complete: cleaned {stats['total_removed']} records")


if __name__ == "__main__":
    main()