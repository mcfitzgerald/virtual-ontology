#!/usr/bin/env python3
"""
Virtual Twin Database Tables Setup Module
Handles creation and initialization of all twin-specific database tables
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
import random
from typing import Dict, Any, Optional, List


logger = logging.getLogger(__name__)


class TwinTablesManager:
    """Manager for Virtual Twin database tables and data initialization"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.equipment_config = config.get('equipment_configuration', {})
        self.downtime_reasons = config.get('downtime_reason_mapping', {})
        self.twin_tables_config = config.get('twin_tables', {})
    
    def create_all_tables(self, conn: sqlite3.Connection) -> bool:
        """Create all required twin tables if they don't exist"""
        try:
            logger.info("Creating Virtual Twin database tables...")
            
            cursor = conn.cursor()
            
            # 1. Optimization Results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimization_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    solution_index INTEGER NOT NULL,
                    objectives_json TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    constraints_satisfied BOOLEAN DEFAULT 1,
                    is_pareto BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES twin_runs(run_id)
                )
            """)
            
            # 2. Provenance Records table (PROV-O compliant)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS provenance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    activity_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    inputs_json TEXT,
                    outputs_json TEXT,
                    attributes_json TEXT,
                    FOREIGN KEY (run_id) REFERENCES twin_runs(run_id)
                )
            """)
            
            # 3. Equipment Metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS equipment_metadata (
                    equipment_id TEXT PRIMARY KEY,
                    equipment_type TEXT NOT NULL,
                    line TEXT NOT NULL,
                    manufacturer TEXT,
                    model TEXT,
                    installation_date DATE,
                    last_maintenance DATE,
                    capacity_per_hour INTEGER,
                    energy_rating REAL,
                    attributes_json TEXT
                )
            """)
            
            # 4. Quality Data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    equipment_id TEXT NOT NULL,
                    batch_id TEXT,
                    quality_score REAL,
                    defect_type TEXT,
                    defect_count INTEGER,
                    scrap_weight REAL,
                    rework_needed BOOLEAN DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (equipment_id) REFERENCES equipment_metadata(equipment_id)
                )
            """)
            
            # 5. Real-time Sensor Data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id TEXT NOT NULL,
                    equipment_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    observable_property TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    quality REAL DEFAULT 1.0,
                    FOREIGN KEY (equipment_id) REFERENCES equipment_metadata(equipment_id)
                )
            """)
            
            # 6. Alert Configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_name TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    condition TEXT NOT NULL,
                    equipment_id TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_triggered TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("✅ Created/verified all twin tables")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create twin tables: {e}")
            conn.rollback()
            return False

    def create_indexes(self, conn: sqlite3.Connection) -> bool:
        """Create indexes for performance"""
        try:
            logger.info("Creating database indexes for performance...")
            
            cursor = conn.cursor()
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_optimization_run ON optimization_results(run_id)",
                "CREATE INDEX IF NOT EXISTS idx_optimization_pareto ON optimization_results(is_pareto)",
                "CREATE INDEX IF NOT EXISTS idx_provenance_run ON provenance_records(run_id)",
                "CREATE INDEX IF NOT EXISTS idx_quality_timestamp ON quality_data(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_quality_equipment ON quality_data(equipment_id)",
                "CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_data(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_sensor_equipment ON sensor_data(equipment_id)",
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            logger.info("✅ Created performance indexes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return False

    def populate_equipment_metadata(self, conn: sqlite3.Connection) -> bool:
        """Populate equipment metadata from configuration"""
        try:
            cursor = conn.cursor()
            
            # Check if already populated
            cursor.execute("SELECT COUNT(*) FROM equipment_metadata")
            if cursor.fetchone()[0] > 0:
                logger.info("ℹ️  Equipment metadata already populated")
                return True
            
            logger.info("Populating equipment metadata...")
            equipment_data = []
            
            # Generate equipment for each line from configuration
            for line_id, line_info in self.equipment_config.get('lines', {}).items():
                line = line_id
                
                for equip_info in line_info.get('equipment_sequence', []):
                    equipment_data.append({
                        'equipment_id': equip_info['id'],
                        'equipment_type': equip_info['type'],
                        'line': line,
                        'manufacturer': self._get_manufacturer_for_type(equip_info['type']),
                        'model': self._get_model_for_type(equip_info['type']),
                        'installation_date': '2021-01-15' if '2' in line else '2018-06-20',
                        'last_maintenance': '2024-12-01',
                        'capacity_per_hour': self._get_capacity_for_type(equip_info['type']),
                        'energy_rating': self._get_energy_rating_for_type(equip_info['type']),
                        'attributes': self._get_attributes_for_type(equip_info['type'])
                    })
            
            # Insert equipment data
            for equip in equipment_data:
                cursor.execute("""
                    INSERT INTO equipment_metadata 
                    (equipment_id, equipment_type, line, manufacturer, model, 
                     installation_date, last_maintenance, capacity_per_hour, 
                     energy_rating, attributes_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    equip['equipment_id'],
                    equip['equipment_type'],
                    equip['line'],
                    equip['manufacturer'],
                    equip['model'],
                    equip['installation_date'],
                    equip['last_maintenance'],
                    equip['capacity_per_hour'],
                    equip['energy_rating'],
                    json.dumps(equip['attributes'])
                ))
            
            conn.commit()
            logger.info(f"✅ Populated {len(equipment_data)} equipment records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to populate equipment metadata: {e}")
            return False

    def populate_sample_quality_data(self, conn: sqlite3.Connection, days: int = 30) -> bool:
        """Add sample quality data for testing"""
        try:
            cursor = conn.cursor()
            
            # Check if already populated
            cursor.execute("SELECT COUNT(*) FROM quality_data")
            if cursor.fetchone()[0] > 100:
                logger.info("ℹ️  Quality data already populated")
                return True
            
            logger.info(f"Generating {days} days of sample quality data...")
            
            # Generate quality data for specified period
            base_date = datetime.now() - timedelta(days=days)
            quality_records = []
            batch_counter = 1000
            
            for day in range(days):
                current_date = base_date + timedelta(days=day)
                
                for hour in range(24):
                    timestamp = current_date.replace(hour=hour, minute=0, second=0)
                    
                    # Get equipment from configuration
                    for line_id, line_info in self.equipment_config.get('lines', {}).items():
                        line_num = int(line_id.replace('LINE', ''))
                        
                        for equip_info in line_info.get('equipment_sequence', []):
                            equipment_id = equip_info['id']
                            equip_type = equip_info['type']
                            
                            # Generate realistic quality scores
                            base_quality = 0.95 if line_num == 2 else 0.93  # LINE2 performs better
                            
                            # Add some variation - Tuesday quality drop simulation
                            if hour >= 8 and hour <= 10 and day == 7:
                                quality_score = base_quality - 0.08 if equip_type == 'Packer' else base_quality
                            else:
                                quality_score = base_quality + random.uniform(-0.02, 0.02)
                            
                            quality_score = max(0.85, min(0.99, quality_score))
                            
                            # Defects based on quality
                            defect_count = int((1 - quality_score) * 100)
                            defect_type = random.choice(['seal', 'weight', 'label', 'damage', None])
                            
                            quality_records.append((
                                None,  # run_id
                                timestamp.isoformat(),
                                equipment_id,
                                f"BATCH-{batch_counter}",
                                quality_score,
                                defect_type,
                                defect_count if defect_type else 0,
                                defect_count * 0.5 if defect_type else 0,  # scrap_weight
                                1 if quality_score < 0.90 else 0,  # rework_needed
                                None  # notes
                            ))
                            
                            batch_counter += 1
            
            # Insert in batches
            cursor.executemany("""
                INSERT INTO quality_data 
                (run_id, timestamp, equipment_id, batch_id, quality_score,
                 defect_type, defect_count, scrap_weight, rework_needed, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, quality_records)
            
            conn.commit()
            logger.info(f"✅ Populated {len(quality_records)} quality records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to populate sample quality data: {e}")
            return False

    def populate_sample_sensor_data(self, conn: sqlite3.Connection, hours: int = 24) -> bool:
        """Add sample sensor data for real-time monitoring"""
        try:
            cursor = conn.cursor()
            
            # Check if already populated
            cursor.execute("SELECT COUNT(*) FROM sensor_data")
            if cursor.fetchone()[0] > 100:
                logger.info("ℹ️  Sensor data already populated")
                return True
            
            logger.info(f"Generating {hours} hours of sample sensor data...")
            
            # Generate recent sensor data
            base_time = datetime.now() - timedelta(hours=hours)
            sensor_records = []
            
            for hour in range(hours):
                for minute in range(0, 60, 5):  # Every 5 minutes
                    timestamp = base_time + timedelta(hours=hour, minutes=minute)
                    
                    # Get equipment from configuration
                    for line_id, line_info in self.equipment_config.get('lines', {}).items():
                        for equip_info in line_info.get('equipment_sequence', []):
                            equipment_id = equip_info['id']
                            
                            # Temperature sensor
                            sensor_records.append((
                                f"TEMP-{equipment_id}",
                                equipment_id,
                                timestamp.isoformat(),
                                'temperature',
                                22.0 + random.uniform(-2, 2),
                                'celsius',
                                1.0
                            ))
                            
                            # Vibration sensor
                            sensor_records.append((
                                f"VIB-{equipment_id}",
                                equipment_id,
                                timestamp.isoformat(),
                                'vibration',
                                0.5 + random.uniform(-0.2, 0.3),
                                'mm/s',
                                0.95
                            ))
                            
                            # Speed sensor
                            sensor_records.append((
                                f"SPEED-{equipment_id}",
                                equipment_id,
                                timestamp.isoformat(),
                                'speed',
                                100.0 + random.uniform(-10, 10),
                                'units/min',
                                0.98
                            ))
            
            # Insert sensor data
            cursor.executemany("""
                INSERT INTO sensor_data 
                (sensor_id, equipment_id, timestamp, observable_property, value, unit, quality)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, sensor_records)
            
            conn.commit()
            logger.info(f"✅ Populated {len(sensor_records)} sensor records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to populate sample sensor data: {e}")
            return False

    def populate_alert_config(self, conn: sqlite3.Connection) -> bool:
        """Set up default alert configurations"""
        try:
            cursor = conn.cursor()
            
            # Check if already populated
            cursor.execute("SELECT COUNT(*) FROM alert_config")
            if cursor.fetchone()[0] > 0:
                logger.info("ℹ️  Alert configurations already set")
                return True
            
            logger.info("Setting up default alert configurations...")
            
            alerts = [
                ('Low OEE Alert', 'oee', 0.60, 'below', None),
                ('High Energy Usage', 'energy_consumption', 1000, 'above', None),
                ('Quality Degradation', 'quality_score', 0.92, 'below', None),
                ('Excessive Downtime', 'downtime_minutes', 30, 'above', None),
                ('Vibration Warning', 'vibration', 1.0, 'above', None),
                ('Temperature Alert', 'temperature', 30, 'above', None),
            ]
            
            cursor.executemany("""
                INSERT INTO alert_config (alert_name, metric, threshold, condition, equipment_id)
                VALUES (?, ?, ?, ?, ?)
            """, alerts)
            
            conn.commit()
            logger.info(f"✅ Created {len(alerts)} alert configurations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to populate alert configurations: {e}")
            return False

    def verify_database_setup(self, conn: sqlite3.Connection) -> Dict[str, int]:
        """Verify all tables and data are properly set up"""
        try:
            cursor = conn.cursor()
            
            logger.info("Verifying database setup...")
            
            # Check all tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            tables = cursor.fetchall()
            
            table_counts = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                table_counts[table_name] = count
                logger.debug(f"  - {table_name:<30} {count:>10} records")
            
            logger.info(f"✅ Database verification complete - {len(tables)} tables found")
            return table_counts
            
        except Exception as e:
            logger.error(f"Failed to verify database setup: {e}")
            return {}

    def clean_all_data(self, conn: sqlite3.Connection, preserve_structure: bool = True) -> bool:
        """Clean all data from twin tables"""
        try:
            logger.info("Cleaning all data from twin tables...")
            cursor = conn.cursor()
            
            # Define tables in dependency order (child tables first)
            tables_to_clean = [
                'sensor_data',
                'quality_data', 
                'alert_config',
                'provenance_records',
                'optimization_results',
                'equipment_metadata'
            ]
            
            if preserve_structure:
                # Just delete data, keep structure
                for table in tables_to_clean:
                    try:
                        cursor.execute(f"DELETE FROM {table}")
                        logger.debug(f"Cleaned data from {table}")
                    except sqlite3.Error as e:
                        logger.warning(f"Could not clean {table}: {e}")
            else:
                # Drop tables entirely
                for table in tables_to_clean:
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {table}")
                        logger.debug(f"Dropped table {table}")
                    except sqlite3.Error as e:
                        logger.warning(f"Could not drop {table}: {e}")
            
            conn.commit()
            logger.info("✅ Database cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean database: {e}")
            conn.rollback()
            return False

    # Helper methods for equipment metadata
    def _get_manufacturer_for_type(self, equip_type: str) -> str:
        """Get manufacturer name for equipment type"""
        manufacturers = {
            'Filler': 'TechFill Inc',
            'Packer': 'PackMaster', 
            'Palletizer': 'RoboPal'
        }
        return manufacturers.get(equip_type, 'Generic Corp')
    
    def _get_model_for_type(self, equip_type: str) -> str:
        """Get model name for equipment type"""
        models = {
            'Filler': 'TF-3000',
            'Packer': 'PM-500X',
            'Palletizer': 'RP-200'
        }
        return models.get(equip_type, 'MODEL-X')
    
    def _get_capacity_for_type(self, equip_type: str) -> int:
        """Get capacity for equipment type"""
        capacities = {
            'Filler': 1200,
            'Packer': 1000,
            'Palletizer': 800
        }
        return capacities.get(equip_type, 1000)
    
    def _get_energy_rating_for_type(self, equip_type: str) -> float:
        """Get energy rating for equipment type"""
        ratings = {
            'Filler': 85.5,
            'Packer': 78.2,
            'Palletizer': 92.1
        }
        return ratings.get(equip_type, 80.0)
    
    def _get_attributes_for_type(self, equip_type: str) -> Dict[str, Any]:
        """Get attributes dictionary for equipment type"""
        attributes = {
            'Filler': {'sensors': 12, 'precision': 'high'},
            'Packer': {'seal_type': 'heat', 'formats': 3},
            'Palletizer': {'max_height': 2.5, 'pattern_types': 5}
        }
        return attributes.get(equip_type, {'type': equip_type})