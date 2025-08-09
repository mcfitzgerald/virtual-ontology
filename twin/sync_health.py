"""
Synchronization Health Monitoring for Virtual Twin
Monitors the health status of synchronization between virtual and physical systems
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
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
    """
    Monitors synchronization health between virtual twin and data sources
    Compliant with ISO 23247 synchronization requirements
    """
    
    def __init__(self, db_path: str = "data/mes_database.db"):
        self.db_path = db_path
        self.init_sync_tables()
        
    def init_sync_tables(self):
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
                    ROUND((julianday('now') - julianday(last_update)) * 24 * 60, 2) as minutes_since_update,
                    CASE 
                        WHEN (julianday('now') - julianday(last_update)) * 24 * 60 <= sync_interval_minutes 
                        THEN 'HEALTHY'
                        WHEN (julianday('now') - julianday(last_update)) * 24 * 60 <= sync_interval_minutes * 2
                        THEN 'DELAYED'
                        ELSE 'STALE'
                    END as health_status,
                    data_hash,
                    source_run_id
                FROM entity_sync_metadata
                ORDER BY 
                    CASE health_status
                        WHEN 'STALE' THEN 1
                        WHEN 'DELAYED' THEN 2
                        WHEN 'HEALTHY' THEN 3
                    END,
                    minutes_since_update DESC
            """)
            
            conn.commit()
    
    def update_sync_metadata(
        self,
        entity_id: str,
        entity_type: str,
        data: Optional[Dict] = None,
        source_run_id: Optional[str] = None,
        sync_interval_minutes: int = 5
    ) -> SyncMetadata:
        """
        Update synchronization metadata for an entity
        
        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity (Equipment, ProductionLine, etc.)
            data: Optional data to compute hash from
            source_run_id: ID of the simulation/data source run
            sync_interval_minutes: Expected sync interval
            
        Returns:
            Updated SyncMetadata object
        """
        now = datetime.now()
        data_hash = None
        
        if data:
            # Compute hash of data for integrity checking
            data_str = json.dumps(data, sort_keys=True)
            data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            # Get previous status for logging
            cursor = conn.execute(
                "SELECT health_status FROM entity_sync_metadata WHERE entity_id = ?",
                (entity_id,)
            )
            previous_status = cursor.fetchone()
            previous_status = previous_status[0] if previous_status else None
            
            # Update or insert sync metadata
            conn.execute("""
                INSERT OR REPLACE INTO entity_sync_metadata 
                (entity_id, entity_type, last_update, sync_interval_minutes, 
                 source_run_id, data_hash, health_status)
                VALUES (?, ?, ?, ?, ?, ?, 'HEALTHY')
            """, (entity_id, entity_type, now, sync_interval_minutes, 
                  source_run_id, data_hash))
            
            # Log status change
            if previous_status and previous_status != 'HEALTHY':
                conn.execute("""
                    INSERT INTO sync_health_log 
                    (entity_id, previous_status, new_status, delay_minutes)
                    VALUES (?, ?, 'HEALTHY', 0)
                """, (entity_id, previous_status))
            
            conn.commit()
        
        return SyncMetadata(
            entity_id=entity_id,
            entity_type=entity_type,
            last_update=now,
            sync_interval_minutes=sync_interval_minutes,
            source_run_id=source_run_id,
            data_hash=data_hash,
            health_status=SyncHealthStatus.HEALTHY
        )
    
    def get_sync_health(self, entity_id: Optional[str] = None) -> List[SyncMetadata]:
        """
        Get current synchronization health status
        
        Args:
            entity_id: Optional specific entity to check
            
        Returns:
            List of SyncMetadata objects with current health status
        """
        with sqlite3.connect(self.db_path) as conn:
            if entity_id:
                query = """
                    SELECT * FROM sync_health_dashboard 
                    WHERE entity_id = ?
                """
                cursor = conn.execute(query, (entity_id,))
            else:
                query = "SELECT * FROM sync_health_dashboard"
                cursor = conn.execute(query)
            
            results = []
            for row in cursor.fetchall():
                last_update = datetime.fromisoformat(row[2])
                health_status = SyncHealthStatus[row[5]]
                
                results.append(SyncMetadata(
                    entity_id=row[0],
                    entity_type=row[1],
                    last_update=last_update,
                    sync_interval_minutes=row[3],
                    source_run_id=row[7],
                    data_hash=row[6],
                    health_status=health_status
                ))
        
        return results
    
    def get_health_summary(self) -> Dict[str, int]:
        """
        Get summary count of entities by health status
        
        Returns:
            Dictionary with counts by status
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    health_status,
                    COUNT(*) as count
                FROM sync_health_dashboard
                GROUP BY health_status
            """)
            
            summary = {
                "HEALTHY": 0,
                "DELAYED": 0,
                "STALE": 0,
                "UNKNOWN": 0
            }
            
            for row in cursor.fetchall():
                summary[row[0]] = row[1]
        
        return summary
    
    def check_and_alert(self, alert_threshold: str = "STALE") -> List[Tuple[str, str]]:
        """
        Check for entities that need alerts
        
        Args:
            alert_threshold: Status level that triggers alert (STALE or DELAYED)
            
        Returns:
            List of (entity_id, status) tuples that need alerts
        """
        alerts = []
        threshold_priority = {
            "STALE": ["STALE"],
            "DELAYED": ["STALE", "DELAYED"]
        }
        
        statuses_to_alert = threshold_priority.get(alert_threshold, ["STALE"])
        
        with sqlite3.connect(self.db_path) as conn:
            for status in statuses_to_alert:
                cursor = conn.execute("""
                    SELECT entity_id 
                    FROM sync_health_dashboard
                    WHERE health_status = ?
                """, (status,))
                
                for row in cursor.fetchall():
                    alerts.append((row[0], status))
                    
                    # Log alert
                    conn.execute("""
                        INSERT INTO sync_health_log 
                        (entity_id, new_status, alert_raised)
                        VALUES (?, ?, TRUE)
                    """, (row[0], status))
            
            conn.commit()
        
        return alerts
    
    def visualize_health(self) -> str:
        """
        Generate a text-based visualization of sync health
        
        Returns:
            ASCII table showing sync health status
        """
        health_data = self.get_sync_health()
        summary = self.get_health_summary()
        
        # Build header
        output = []
        output.append("=" * 80)
        output.append("SYNCHRONIZATION HEALTH DASHBOARD")
        output.append("=" * 80)
        output.append(f"Timestamp: {datetime.now().isoformat()}")
        output.append("")
        
        # Summary
        output.append("SUMMARY:")
        output.append(f"  🟢 HEALTHY: {summary['HEALTHY']}")
        output.append(f"  🟡 DELAYED: {summary['DELAYED']}")
        output.append(f"  🔴 STALE:   {summary['STALE']}")
        output.append(f"  ⚫ UNKNOWN: {summary['UNKNOWN']}")
        output.append("")
        
        # Detailed status
        output.append("DETAILED STATUS:")
        output.append("-" * 80)
        output.append(f"{'Entity ID':<20} {'Type':<15} {'Status':<10} {'Last Update':<20} {'Delay (min)':<10}")
        output.append("-" * 80)
        
        for entity in sorted(health_data, key=lambda x: (
            0 if x.health_status == SyncHealthStatus.STALE else
            1 if x.health_status == SyncHealthStatus.DELAYED else
            2 if x.health_status == SyncHealthStatus.HEALTHY else 3
        )):
            delay = (datetime.now() - entity.last_update).total_seconds() / 60
            status_icon = {
                SyncHealthStatus.HEALTHY: "🟢",
                SyncHealthStatus.DELAYED: "🟡",
                SyncHealthStatus.STALE: "🔴",
                SyncHealthStatus.UNKNOWN: "⚫"
            }.get(entity.health_status, "")
            
            output.append(
                f"{entity.entity_id:<20} {entity.entity_type:<15} "
                f"{status_icon} {entity.health_status.value:<8} "
                f"{entity.last_update.strftime('%Y-%m-%d %H:%M'):<20} "
                f"{delay:>8.1f}"
            )
        
        output.append("=" * 80)
        
        return "\n".join(output)


def demonstrate_sync_health():
    """Demonstrate sync health monitoring"""
    monitor = SyncHealthMonitor()
    
    # Simulate some entity updates
    print("Simulating entity synchronization...")
    
    # Update equipment entities
    for line in range(1, 4):
        for equipment in ["FIL", "PCK", "PAL"]:
            entity_id = f"LINE{line}-{equipment}"
            monitor.update_sync_metadata(
                entity_id=entity_id,
                entity_type="Equipment",
                data={"status": "Running", "oee": 0.85},
                source_run_id="sim-2025-01-09-001"
            )
    
    # Simulate some delayed entities
    import time
    time.sleep(1)
    
    # Check health
    print("\n" + monitor.visualize_health())
    
    # Check for alerts
    alerts = monitor.check_and_alert(alert_threshold="DELAYED")
    if alerts:
        print(f"\n⚠️  ALERTS: {len(alerts)} entities need attention")
        for entity_id, status in alerts:
            print(f"   - {entity_id}: {status}")


if __name__ == "__main__":
    demonstrate_sync_health()