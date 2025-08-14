"""Synchronization Health Monitoring for Virtual Twin
Monitors the health status of synchronization between virtual and physical systems
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import hashlib
import json


class SyncHealthStatus(Enum):
    """Synchronization health states per ISO 23247"""

    HEALTHY = "HEALTHY"  # Within sync interval
    DELAYED = "DELAYED"  # Within 2x sync interval
    STALE = "STALE"      # Beyond 2x sync interval
    UNKNOWN = "UNKNOWN"  # No sync data available


@dataclass
class SyncMetadata:
    """Metadata for entity synchronization"""

    entity_id: str
    entity_type: str  # Equipment, ProductionLine, etc.
    last_update: datetime
    sync_interval_minutes: int
    source_run_id: Optional[str] = None
    data_hash: Optional[str] = None
    health_status: SyncHealthStatus = SyncHealthStatus.UNKNOWN


class SyncHealthMonitor:
    """Monitors synchronization health between virtual twin and data sources
    Compliant with ISO 23247 synchronization requirements
    
    Configuration is REQUIRED - all values must come from config
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize the SyncHealthMonitor.
        Configuration is required - will raise error if not available.
        
        Args:
            db_path: Path to the SQLite database (uses config if None)
            
        Raises:
            RuntimeError: If configuration is not available
            ValueError: If required config values are missing

        """
        from .config_loader import get_config
        self.config = get_config()  # Will raise error if config not available
        
        # Get required values from config
        self.db_path: str = db_path if db_path is not None else self.config.get("database.path")
        if not self.db_path:
            raise ValueError("Database path not provided and not found in configuration")
            
        # Load sync health configuration
        self.default_sync_interval = self.config.get("sync_health.default_sync_interval")
        self.alert_threshold = self.config.get("sync_health.alert_threshold")
        self.status_thresholds = self.config.get("sync_health.status_thresholds")
        self.sync_log_retention_days = self.config.get("retention.sync_log_days")
        self.default_history_hours = self.config.get("retention.default_history_hours")
        
        # Validate required config values
        if self.default_sync_interval is None:
            raise ValueError("sync_health.default_sync_interval not found in configuration")
        if self.alert_threshold is None:
            raise ValueError("sync_health.alert_threshold not found in configuration")
        if self.status_thresholds is None:
            raise ValueError("sync_health.status_thresholds not found in configuration")
            
        self.init_sync_tables()
        
    def init_sync_tables(self) -> None:
        """Initialize synchronization metadata tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entity_sync_metadata (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    last_update TIMESTAMP NOT NULL,
                    sync_interval_minutes INTEGER NOT NULL DEFAULT 5,
                    source_run_id TEXT,
                    data_hash TEXT,
                    health_status TEXT,
                    CHECK(health_status IN ('HEALTHY', 'DELAYED', 'STALE', 'UNKNOWN'))
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_health_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    entity_id TEXT NOT NULL,
                    previous_status TEXT,
                    new_status TEXT NOT NULL,
                    delay_minutes REAL,
                    alert_raised BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (entity_id) REFERENCES entity_sync_metadata(entity_id)
                )
            """)
            
            # Create view for current sync health
            conn.execute("""
                CREATE VIEW IF NOT EXISTS sync_health_dashboard AS
                SELECT 
                    entity_id,
                    entity_type,
                    last_update,
                    sync_interval_minutes,
                    health_status,
                    CAST((julianday('now') - julianday(last_update)) * 24 * 60 AS REAL) as minutes_since_update,
                    CASE 
                        WHEN CAST((julianday('now') - julianday(last_update)) * 24 * 60 AS REAL) <= sync_interval_minutes THEN 'HEALTHY'
                        WHEN CAST((julianday('now') - julianday(last_update)) * 24 * 60 AS REAL) <= sync_interval_minutes * 2 THEN 'DELAYED'
                        ELSE 'STALE'
                    END as calculated_status
                FROM entity_sync_metadata
            """)
            
            # Index for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_health_log_timestamp 
                ON sync_health_log(timestamp DESC)
            """)
            
    def update_sync_metadata(
        self, 
        entity_id: str,
        entity_type: str,
        data: Optional[Dict[str, Any]] = None,
        source_run_id: Optional[str] = None,
        sync_interval_minutes: Optional[int] = None
    ) -> None:
        """Update synchronization metadata for an entity
        
        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity (Equipment, Line, etc.)
            data: Optional data to hash for change detection
            source_run_id: Optional simulation run that generated this data
            sync_interval_minutes: Expected sync interval (uses config default if None)

        """
        if sync_interval_minutes is None:
            sync_interval_minutes = self.config.get("sync_health.default_sync_interval")
        current_time = datetime.now()
        data_hash: Optional[str] = None
        
        if data:
            # Create hash of data for change detection
            data_str = json.dumps(data, sort_keys=True)
            data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        # Get previous status for logging
        previous_status: Optional[str] = self._get_entity_status(entity_id)
        
        # Determine new health status
        health_status = SyncHealthStatus.HEALTHY
        
        with sqlite3.connect(self.db_path) as conn:
            # Upsert sync metadata
            conn.execute("""
                INSERT OR REPLACE INTO entity_sync_metadata
                (entity_id, entity_type, last_update, sync_interval_minutes, 
                 source_run_id, data_hash, health_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id, entity_type, current_time, sync_interval_minutes,
                source_run_id, data_hash, health_status.value
            ))
            
            # Log status change if different
            if previous_status != health_status.value:
                conn.execute("""
                    INSERT INTO sync_health_log
                    (entity_id, previous_status, new_status, delay_minutes, alert_raised)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    entity_id, previous_status, health_status.value, 0.0, False
                ))
                
    def get_sync_health(
        self, 
        entity_id: Optional[str] = None
    ) -> List[SyncMetadata]:
        """Get synchronization health for one or all entities
        
        Args:
            entity_id: Optional specific entity ID, or None for all
            
        Returns:
            List of SyncMetadata objects

        """
        with sqlite3.connect(self.db_path) as conn:
            if entity_id:
                cursor = conn.execute("""
                    SELECT entity_id, entity_type, last_update, sync_interval_minutes,
                           source_run_id, data_hash, calculated_status
                    FROM sync_health_dashboard
                    WHERE entity_id = ?
                """, (entity_id,))
            else:
                cursor = conn.execute("""
                    SELECT entity_id, entity_type, last_update, sync_interval_minutes,
                           source_run_id, data_hash, calculated_status
                    FROM sync_health_dashboard
                    ORDER BY calculated_status DESC, minutes_since_update DESC
                """)
            
            results: List[SyncMetadata] = []
            for row in cursor.fetchall():
                results.append(SyncMetadata(
                    entity_id=row[0],
                    entity_type=row[1],
                    last_update=datetime.fromisoformat(row[2]),
                    sync_interval_minutes=row[3],
                    source_run_id=row[4],
                    data_hash=row[5],
                    health_status=SyncHealthStatus(row[6])
                ))
                
        return results
        
    def check_health_alerts(
        self, 
        threshold_minutes: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Check for entities requiring health alerts
        
        Args:
            threshold_minutes: Minutes before raising alert (uses config if None)
            
        Returns:
            List of entities requiring alerts

        """
        if threshold_minutes is None:
            threshold_minutes = self.alert_threshold
        alerts: List[Dict[str, Any]] = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT entity_id, entity_type, minutes_since_update, calculated_status
                FROM sync_health_dashboard
                WHERE minutes_since_update > ?
                  AND calculated_status IN ('STALE', 'DELAYED')
            """, (threshold_minutes,))
            
            for row in cursor.fetchall():
                alerts.append({
                    'entity_id': row[0],
                    'entity_type': row[1],
                    'minutes_since_update': row[2],
                    'status': row[3],
                    'severity': 'HIGH' if row[3] == 'STALE' else 'MEDIUM'
                })
                
        return alerts
        
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary statistics
        
        Returns:
            Dictionary with health statistics

        """
        with sqlite3.connect(self.db_path) as conn:
            # Count by status
            cursor = conn.execute("""
                SELECT calculated_status, COUNT(*) 
                FROM sync_health_dashboard
                GROUP BY calculated_status
            """)
            
            status_counts: Dict[str, int] = {}
            for row in cursor.fetchall():
                status_counts[row[0]] = row[1]
            
            # Average delay
            cursor = conn.execute("""
                SELECT AVG(minutes_since_update)
                FROM sync_health_dashboard
            """)
            avg_delay: float = cursor.fetchone()[0] or 0.0
            
            # Entities with longest delay
            cursor = conn.execute("""
                SELECT entity_id, entity_type, minutes_since_update
                FROM sync_health_dashboard
                ORDER BY minutes_since_update DESC
                LIMIT 5
            """)
            
            longest_delays: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                longest_delays.append({
                    'entity_id': row[0],
                    'entity_type': row[1],
                    'delay_minutes': row[2]
                })
            
        total_entities = sum(status_counts.values())
        health_percentage = (
            (status_counts.get('HEALTHY', 0) / total_entities * 100) 
            if total_entities > 0 else 0
        )
        
        return {
            'total_entities': total_entities,
            'status_counts': status_counts,
            'health_percentage': health_percentage,
            'average_delay_minutes': avg_delay,
            'longest_delays': longest_delays,
            'timestamp': datetime.now().isoformat()
        }
        
    def _get_entity_status(self, entity_id: str) -> Optional[str]:
        """Get current status for an entity
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Current status string or None if not found

        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT health_status
                FROM entity_sync_metadata
                WHERE entity_id = ?
            """, (entity_id,))
            
            result = cursor.fetchone()
            return result[0] if result else None
            
    def get_sync_history(
        self, 
        entity_id: str,
        hours: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get synchronization history for an entity
        
        Args:
            entity_id: Entity identifier
            hours: Hours of history to retrieve (uses config if None)
            
        Returns:
            List of sync history records

        """
        if hours is None:
            hours = self.default_history_hours
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, previous_status, new_status, 
                       delay_minutes, alert_raised
                FROM sync_health_log
                WHERE entity_id = ?
                  AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (entity_id, cutoff_time))
            
            history: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                history.append({
                    'timestamp': row[0],
                    'previous_status': row[1],
                    'new_status': row[2],
                    'delay_minutes': row[3],
                    'alert_raised': bool(row[4])
                })
                
        return history
        
    def cleanup_old_logs(
        self, 
        days_to_keep: Optional[int] = None
    ) -> int:
        """Clean up old synchronization logs
        
        Args:
            days_to_keep: Number of days of logs to retain (uses config if None)
            
        Returns:
            Number of records deleted

        """
        if days_to_keep is None:
            days_to_keep = self.sync_log_retention_days
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM sync_health_log
                WHERE timestamp < ?
            """, (cutoff_time,))
            
            deleted_count = cursor.rowcount
            
        return deleted_count
        
    def get_entity_types(self) -> List[str]:
        """Get list of all entity types being monitored
        
        Returns:
            List of unique entity types

        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT entity_type
                FROM entity_sync_metadata
                ORDER BY entity_type
            """)
            
            return [row[0] for row in cursor.fetchall()]
            
    def export_health_report(self) -> Dict[str, Any]:
        """Export comprehensive health report
        
        Returns:
            Dictionary containing full health report

        """
        return {
            'summary': self.get_health_summary(),
            'entities': [
                {
                    'metadata': metadata.__dict__,
                    'history': self.get_sync_history(metadata.entity_id)
                }
                for metadata in self.get_sync_health()
            ],
            'alerts': self.check_health_alerts(),
            'entity_types': self.get_entity_types(),
            'report_generated': datetime.now().isoformat()
        }