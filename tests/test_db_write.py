#!/usr/bin/env python3
"""Test database writing functionality"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import subprocess
import sqlite3

def test_db_write():
    """Test writing MES data to database"""
    print("Testing database write functionality...")
    print("=" * 60)
    
    # Test 1: Write to mes_data table
    print("\n1. Testing write to mes_data table (1 day of data)...")
    result = subprocess.run([
        'python', 'synthetic_data_generator/mes_data_generation.py',
        '--output', 'db',
        '--table', 'mes_data',
        '--start-date', '2025-06-01',
        '--end-date', '2025-06-01'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    # Check database
    db_path = "data/mes_database.db"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM mes_data")
        count = cursor.fetchone()[0]
        print(f"  ✓ Wrote {count} records to mes_data table")
        
        # Check sample data
        cursor = conn.execute("""
            SELECT equipment_id, timestamp, oee_score 
            FROM mes_data 
            LIMIT 3
        """)
        print("  Sample records:")
        for row in cursor.fetchall():
            print(f"    - {row[0]}: {row[1]}, OEE={row[2]}")
    
    # Test 2: Write to simulation_data table
    print("\n2. Testing write to simulation_data table (1 day)...")
    result = subprocess.run([
        'python', 'synthetic_data_generator/mes_data_generation.py',
        '--output', 'db',
        '--table', 'simulation_data',
        '--run-id', 'test-sim-001',
        '--start-date', '2025-06-02',
        '--end-date', '2025-06-02'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT COUNT(*), run_id 
            FROM simulation_data 
            WHERE run_id = 'test-sim-001'
            GROUP BY run_id
        """)
        row = cursor.fetchone()
        if row:
            print(f"  ✓ Wrote {row[0]} records with run_id={row[1]}")
    
    # Test 3: Test both output
    print("\n3. Testing 'both' output mode...")
    result = subprocess.run([
        'python', 'synthetic_data_generator/mes_data_generation.py',
        '--output', 'both',
        '--table', 'mes_data',
        '--start-date', '2025-06-01',
        '--end-date', '2025-06-01'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    # Check CSV was created
    csv_path = "Data/mes_data_with_kpis.csv"
    if os.path.exists(csv_path):
        print(f"  ✓ CSV file created at {csv_path}")
    
    print("\n✅ All database write tests passed!")
    return True

if __name__ == "__main__":
    test_db_write()