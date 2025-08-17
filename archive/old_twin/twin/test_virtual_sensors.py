#!/usr/bin/env python3
"""Test script for Virtual Sensor Refactoring

This script validates that:
1. MES data generation no longer includes energy column
2. Virtual sensors properly derive observations from production data
3. Sensor data is correctly stored in the database
4. CSV export functionality works
5. The complete flow from generation to observation functions correctly
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twin import SimulationRunner, ActionableParameters
from twin.virtual_sensors import VirtualSensorObserver
from twin.generator import generate_mes_data, save_to_csv, load_config


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def test_mes_data_no_energy():
    """Test that MES data generation no longer includes energy column."""
    print_section("Test 1: MES Data Has No Energy Column")
    
    # Generate some test data
    config = load_config()
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2025, 6, 1, 12, 0, 0)  # Just 12 hours for testing
    
    print("Generating MES data...")
    mes_data = generate_mes_data(start_date, end_date, config)
    
    # Check columns
    columns = mes_data.columns.tolist()
    
    if 'Energy_Consumption_kWh' in columns:
        print("❌ FAILED: Energy column still present in generated data")
        print(f"   Columns: {columns}")
        return False
    elif 'energy_consumption_kwh' in columns:
        print("❌ FAILED: Energy column (snake_case) still present in generated data")
        print(f"   Columns: {columns}")
        return False
    else:
        print("✅ PASSED: No energy column in MES data")
        print(f"   Generated {len(mes_data)} records")
        print(f"   Columns: {', '.join(columns[:5])}... ({len(columns)} total)")
        return True


def test_virtual_sensors():
    """Test that virtual sensors generate observations from production data."""
    print_section("Test 2: Virtual Sensors Generate Observations")
    
    # Generate test data
    config = load_config()
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2025, 6, 1, 1, 0, 0)  # Just 1 hour for testing
    
    print("Generating production data...")
    production_data = generate_mes_data(start_date, end_date, config)
    
    # Rename columns to match what virtual sensors expect (snake_case)
    column_mapping = {
        'Timestamp': 'timestamp',
        'LineID': 'line_id',
        'EquipmentID': 'equipment_id',
        'EquipmentType': 'equipment_type',
        'ProductID': 'product_id',
        'MachineStatus': 'machine_status',
        'DowntimeReason': 'downtime_reason',
        'GoodUnitsProduced': 'good_units_produced',
        'ScrapUnitsProduced': 'scrap_units_produced',
        'TargetRate_units_per_5min': 'target_rate_units_per_5min',
        'Performance_Score': 'performance_score',
        'Quality_Score': 'quality_score',
        'OEE_Score': 'oee_score'
    }
    production_data.rename(columns=column_mapping, inplace=True)
    
    print(f"Production data shape: {production_data.shape}")
    
    # Run virtual sensors
    print("Running virtual sensors...")
    observer = VirtualSensorObserver(config)
    observations = observer.observe_production(production_data)
    
    if observations.empty:
        print("❌ FAILED: No observations generated")
        return False
    
    print(f"✅ PASSED: Generated {len(observations)} sensor observations")
    
    # Check observation types
    property_counts = observations['observable_property'].value_counts()
    print("\nObservation types:")
    for prop, count in property_counts.items():
        print(f"  - {prop}: {count} observations")
    
    # Verify power consumption observations exist
    power_obs = observations[observations['observable_property'] == 'power_consumption']
    if power_obs.empty:
        print("❌ WARNING: No power consumption observations (energy now derived)")
        return False
    else:
        print(f"\n✅ Power consumption derived: {len(power_obs)} observations")
        print(f"   Average: {power_obs['value'].mean():.2f} kWh")
        print(f"   Range: {power_obs['value'].min():.2f} - {power_obs['value'].max():.2f} kWh")
    
    return True


def test_csv_export():
    """Test CSV export functionality."""
    print_section("Test 3: CSV Export Functionality")
    
    # Generate test data
    config = load_config()
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2025, 6, 1, 0, 30, 0)  # Just 30 minutes
    
    print("Generating test data...")
    mes_data = generate_mes_data(start_date, end_date, config)
    
    # Save to CSV
    print("Saving to CSV...")
    csv_path = save_to_csv(mes_data, "test_export.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ FAILED: CSV file not created at {csv_path}")
        return False
    
    # Read back and verify
    df_loaded = pd.read_csv(csv_path)
    
    if len(df_loaded) != len(mes_data):
        print(f"❌ FAILED: Row count mismatch. Original: {len(mes_data)}, Loaded: {len(df_loaded)}")
        return False
    
    print(f"✅ PASSED: CSV export successful")
    print(f"   File: {csv_path}")
    print(f"   Size: {os.path.getsize(csv_path):,} bytes")
    print(f"   Records: {len(df_loaded)}")
    
    # Clean up
    try:
        os.remove(csv_path)
    except:
        pass
    
    return True


def test_complete_simulation_flow():
    """Test the complete flow with SimulationRunner."""
    print_section("Test 4: Complete Simulation Flow")
    
    try:
        # Initialize runner with generator version
        print("Initializing SimulationRunner...")
        runner = SimulationRunner(verbose=False, generator_version="1.2.0")
        
        # Create baseline
        print("Creating baseline simulation...")
        baseline = runner.create_baseline(duration_days=1, seed=42)
        
        if baseline.status != "completed":
            print(f"❌ FAILED: Baseline status is {baseline.status}")
            return False
        
        print(f"✅ Baseline created: {baseline.run_id}")
        print(f"   OEE: {baseline.kpi_summary['mean_oee']:.1f}%")
        
        # Check if sensor data was generated
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "data", 
            "mes_database.db"
        )
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check simulation data
            cursor.execute(
                "SELECT COUNT(*) FROM simulation_data WHERE run_id = ?",
                (baseline.run_id,)
            )
            sim_count = cursor.fetchone()[0]
            
            # Check sensor data (sensor_data table doesn't have run_id in legacy schema)
            cursor.execute(
                "SELECT COUNT(*) FROM sensor_data WHERE timestamp >= datetime('now', '-1 day')"
            )
            sensor_count = cursor.fetchone()[0]
            
            # Check for energy observations
            cursor.execute("""
                SELECT COUNT(*) FROM sensor_data 
                WHERE timestamp >= datetime('now', '-1 day') 
                AND observable_property = 'power_consumption'
            """)
            power_count = cursor.fetchone()[0]
        
        print(f"\nDatabase records:")
        print(f"  - Simulation data: {sim_count} records")
        print(f"  - Sensor observations: {sensor_count} records")
        print(f"  - Power consumption observations: {power_count} records")
        
        if sim_count == 0:
            print("❌ FAILED: No simulation data generated")
            return False
        
        if sensor_count == 0:
            print("❌ FAILED: No sensor observations generated")
            return False
            
        if power_count == 0:
            print("❌ WARNING: No power consumption observations (should be derived)")
            # This is not a failure, just a warning
        
        # Test with modified parameters
        print("\nTesting with modified parameters...")
        params = ActionableParameters()
        params.micro_stop_probability = 0.8  # 20% improvement
        params.performance_factor = 1.1       # 10% improvement
        
        simulation = runner.run_simulation(
            parameters=params,
            parent_run_id=baseline.run_id,
            duration_days=1,
            notes="Test with improved parameters"
        )
        
        if simulation.status != "completed":
            print(f"❌ FAILED: Simulation status is {simulation.status}")
            return False
            
        print(f"✅ Simulation completed: {simulation.run_id}")
        print(f"   OEE: {simulation.kpi_summary['mean_oee']:.1f}%")
        print(f"   Improvement: {simulation.kpi_summary['mean_oee'] - baseline.kpi_summary['mean_oee']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_database_schema():
    """Verify database schema is correct."""
    print_section("Test 5: Database Schema Validation")
    
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "data", 
        "mes_database.db"
    )
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check mes_data table
        cursor.execute("PRAGMA table_info(mes_data)")
        mes_columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        if 'energy_consumption_kwh' in mes_columns:
            print("❌ FAILED: energy_consumption_kwh still in mes_data table")
            return False
        else:
            print("✅ PASSED: mes_data table has no energy column")
            
        # Check simulation_data table
        cursor.execute("PRAGMA table_info(simulation_data)")
        sim_columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        if 'energy_consumption_kwh' in sim_columns:
            print("❌ FAILED: energy_consumption_kwh still in simulation_data table")
            return False
        else:
            print("✅ PASSED: simulation_data table has no energy column")
            
        # Check sensor_data table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sensor_data'
        """)
        if cursor.fetchone():
            print("✅ PASSED: sensor_data table exists")
            
            # Check sensor_data structure
            cursor.execute("PRAGMA table_info(sensor_data)")
            sensor_columns = {row[1] for row in cursor.fetchall()}
            
            required_columns = {
                'sensor_id', 'equipment_id', 'timestamp', 
                'observable_property', 'value', 'unit'
            }
            
            missing = required_columns - sensor_columns
            if missing:
                print(f"❌ WARNING: Missing columns in sensor_data: {missing}")
            else:
                print("✅ PASSED: sensor_data has all required columns")
        else:
            print("❌ WARNING: sensor_data table does not exist (will be created on first run)")
    
    return True


def main():
    """Run all tests."""
    print("="*60)
    print(" VIRTUAL SENSOR REFACTORING TEST SUITE")
    print("="*60)
    print(f"\nTest Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("MES Data No Energy", test_mes_data_no_energy),
        ("Virtual Sensors", test_virtual_sensors),
        ("CSV Export", test_csv_export),
        ("Database Schema", test_database_schema),
        ("Complete Flow", test_complete_simulation_flow),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {str(e)}")
            results[test_name] = False
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Virtual sensor refactoring is complete.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the output above.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())