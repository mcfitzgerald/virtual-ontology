#!/usr/bin/env python3
"""
Initialize Virtual Twin Database Tables
Sets up all required tables for the Virtual Twin system while preserving existing data
"""

import sqlite3
import json
from datetime import datetime, timedelta
import random
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_twin_tables(conn):
    """Create all required twin tables if they don't exist"""
    
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
    
    print("✅ Created/verified all twin tables")
    conn.commit()


def populate_equipment_metadata(conn):
    """Populate equipment metadata if not exists"""
    
    cursor = conn.cursor()
    
    # Check if already populated
    cursor.execute("SELECT COUNT(*) FROM equipment_metadata")
    if cursor.fetchone()[0] > 0:
        print("ℹ️  Equipment metadata already populated")
        return
    
    equipment_data = []
    
    # Generate equipment for 3 lines
    for line_num in range(1, 4):
        line = f"LINE{line_num}"
        
        # Filler
        equipment_data.append({
            'equipment_id': f'{line}-FIL',
            'equipment_type': 'Filler',
            'line': line,
            'manufacturer': 'TechFill Inc',
            'model': 'TF-3000',
            'installation_date': '2021-01-15' if line_num == 2 else '2018-06-20',
            'last_maintenance': '2024-12-01',
            'capacity_per_hour': 1200,
            'energy_rating': 85.5,
            'attributes': {'sensors': 12, 'precision': 'high'}
        })
        
        # Packer
        equipment_data.append({
            'equipment_id': f'{line}-PCK',
            'equipment_type': 'Packer',
            'line': line,
            'manufacturer': 'PackMaster',
            'model': 'PM-500X',
            'installation_date': '2021-01-15' if line_num == 2 else '2018-06-20',
            'last_maintenance': '2024-11-15',
            'capacity_per_hour': 1000,
            'energy_rating': 78.2,
            'attributes': {'seal_type': 'heat', 'formats': 3}
        })
        
        # Palletizer
        equipment_data.append({
            'equipment_id': f'{line}-PAL',
            'equipment_type': 'Palletizer',
            'line': line,
            'manufacturer': 'RoboPal',
            'model': 'RP-200',
            'installation_date': '2021-01-15' if line_num == 2 else '2018-06-20',
            'last_maintenance': '2024-10-30',
            'capacity_per_hour': 800,
            'energy_rating': 92.1,
            'attributes': {'max_height': 2.5, 'pattern_types': 5}
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
    
    print(f"✅ Populated {len(equipment_data)} equipment records")
    conn.commit()


def populate_sample_quality_data(conn):
    """Add sample quality data for testing"""
    
    cursor = conn.cursor()
    
    # Check if already populated
    cursor.execute("SELECT COUNT(*) FROM quality_data")
    if cursor.fetchone()[0] > 100:
        print("ℹ️  Quality data already populated")
        return
    
    # Generate quality data for last 30 days
    base_date = datetime.now() - timedelta(days=30)
    
    quality_records = []
    batch_counter = 1000
    
    for day in range(30):
        current_date = base_date + timedelta(days=day)
        
        for hour in range(24):
            timestamp = current_date.replace(hour=hour, minute=0, second=0)
            
            for line_num in range(1, 4):
                for equip_type in ['FIL', 'PCK', 'PAL']:
                    equipment_id = f"LINE{line_num}-{equip_type}"
                    
                    # Generate realistic quality scores
                    base_quality = 0.95 if line_num == 2 else 0.93  # LINE2 performs better
                    
                    # Add some variation
                    if hour >= 8 and hour <= 10 and day == 7:  # Tuesday quality drop
                        quality_score = base_quality - 0.08 if equip_type == 'PCK' else base_quality
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
    
    print(f"✅ Populated {len(quality_records)} quality records")
    conn.commit()


def populate_sample_sensor_data(conn):
    """Add sample sensor data for real-time monitoring"""
    
    cursor = conn.cursor()
    
    # Check if already populated
    cursor.execute("SELECT COUNT(*) FROM sensor_data")
    if cursor.fetchone()[0] > 100:
        print("ℹ️  Sensor data already populated")
        return
    
    # Generate recent sensor data (last 24 hours)
    base_time = datetime.now() - timedelta(hours=24)
    
    sensor_records = []
    sensor_id_counter = 1
    
    for hour in range(24):
        for minute in range(0, 60, 5):  # Every 5 minutes
            timestamp = base_time + timedelta(hours=hour, minutes=minute)
            
            for line_num in range(1, 4):
                for equip_type in ['FIL', 'PCK', 'PAL']:
                    equipment_id = f"LINE{line_num}-{equip_type}"
                    
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
    
    print(f"✅ Populated {len(sensor_records)} sensor records")
    conn.commit()


def populate_alert_config(conn):
    """Set up default alert configurations"""
    
    cursor = conn.cursor()
    
    # Check if already populated
    cursor.execute("SELECT COUNT(*) FROM alert_config")
    if cursor.fetchone()[0] > 0:
        print("ℹ️  Alert configurations already set")
        return
    
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
    
    print(f"✅ Created {len(alerts)} alert configurations")
    conn.commit()


def create_indexes(conn):
    """Create indexes for performance"""
    
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
    
    print("✅ Created performance indexes")
    conn.commit()


def verify_database_setup(conn):
    """Verify all tables and data are properly set up"""
    
    cursor = conn.cursor()
    
    print("\n📊 Database Verification:")
    print("-" * 50)
    
    # Check all tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = cursor.fetchall()
    
    print(f"Tables ({len(tables)}):")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]:<30} {count:>10} records")
    
    print("\n✅ Database setup complete and verified!")


def main():
    """Main setup function"""
    
    print("=" * 60)
    print(" VIRTUAL TWIN DATABASE INITIALIZATION")
    print("=" * 60)
    
    # Connect to database
    db_path = "data/mes_database.db"
    
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created data directory")
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Create tables
        create_twin_tables(conn)
        
        # Populate data
        populate_equipment_metadata(conn)
        populate_sample_quality_data(conn)
        populate_sample_sensor_data(conn)
        populate_alert_config(conn)
        
        # Create indexes
        create_indexes(conn)
        
        # Verify setup
        verify_database_setup(conn)
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    print("\n🚀 Database ready for Virtual Twin operations!")
    print("   Run twin demos or use via Claude Code natural language interface")


if __name__ == "__main__":
    main()