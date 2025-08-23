#!/usr/bin/env python3
"""Test script to verify logging implementation and OEE fixes."""

import sys
from pathlib import Path
import simpy
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from twin_model.logging_config import SimulationLogger, EventInspector, setup_default_logging
from twin_model.primitives import (
    PrimitiveConfig,
    EquipmentPrimitive,
    BufferPrimitive,
    SourcePrimitive,
    SinkPrimitive,
    SamplingConfig,
    SimulationMode
)
from twin_model.transduction.mes_transducer import MESTransducer


def test_basic_logging():
    """Test basic logging functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic Logging Setup")
    print("="*60)
    
    # Setup logging with debug level
    setup_default_logging(level="DEBUG", enable_file=True, json_format=False)
    
    # Get a logger
    logger = SimulationLogger.get_logger("test_module")
    
    # Test different log levels
    logger.debug("Debug message", extra={'extra_data': {'test': 'debug'}})
    logger.info("Info message", extra={'extra_data': {'test': 'info'}})
    logger.warning("Warning message", extra={'extra_data': {'test': 'warning'}})
    logger.error("Error message", extra={'extra_data': {'test': 'error'}})
    
    print("✓ Basic logging test completed")


def test_simulation_with_logging():
    """Test a simple simulation with logging enabled."""
    print("\n" + "="*60)
    print("TEST 2: Simulation with Logging")
    print("="*60)
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Create equipment configuration
    equipment_config = PrimitiveConfig(
        id="TEST-EQ-001",
        type="Equipment",
        properties={
            "base_rate": 60.0,  # units per minute
            "mtbf": 480.0,      # mean time between failures
            "mttr": 30.0,       # mean time to repair
        }
    )
    
    # Create sampling config for detailed logging
    sampling_config = SamplingConfig(
        mode=SimulationMode.DETAILED,
        sampling_rate=1,  # Keep all events
        buffer_size=1000
    )
    
    # Create equipment
    equipment = EquipmentPrimitive(
        env=env,
        config=equipment_config,
        sampling_config=sampling_config
    )
    
    # Start equipment
    equipment.start()
    
    # Run simulation for 60 minutes
    print("Running simulation for 60 minutes...")
    env.run(until=60)
    
    # Get observables
    observables = list(equipment.observables)
    print(f"Generated {len(observables)} observable events")
    
    # Analyze events
    inspector = EventInspector()
    analysis = inspector.analyze_event_distribution(observables)
    
    print(f"Event distribution:")
    for event_type, count in analysis['event_types'].items():
        print(f"  {event_type}: {count}")
    
    print("✓ Simulation logging test completed")


def test_mes_transduction_with_fixes():
    """Test MES transduction with runtime inference fixes."""
    print("\n" + "="*60)
    print("TEST 3: MES Transduction with OEE Fixes")
    print("="*60)
    
    # Create a more complex simulation
    env = simpy.Environment()
    
    # Create buffer
    buffer_config = PrimitiveConfig(
        id="BUFFER-001",
        type="Buffer",
        properties={"capacity": 100}
    )
    buffer = BufferPrimitive(env, buffer_config)
    
    # Create equipment with buffer connection
    equipment_config = PrimitiveConfig(
        id="LINE1-FILLER",
        type="Equipment",
        properties={"base_rate": 60.0}
    )
    
    equipment = EquipmentPrimitive(
        env=env,
        config=equipment_config,
        downstream=buffer
    )
    
    # Start components
    buffer.start()
    equipment.start()
    
    # Run simulation
    print("Running simulation for 30 minutes...")
    env.run(until=30)
    
    # Get observables
    observables = list(equipment.observables)
    
    # Process through MES transducer
    transducer = MESTransducer(time_bucket=5)
    
    # Create test manifests
    manifests = {
        "equipment_manifest": {
            "equipment": {
                "LINE1-FILLER": {
                    "base_rate": 60.0,
                    "equipment_type": "Filler"
                }
            }
        },
        "production_manifest": {
            "products": {
                "PRODUCT-001": {
                    "target_rate_units_per_5min": 300
                }
            }
        }
    }
    
    # Process observables to MES format
    mes_df = transducer.process_observables(observables, manifests)
    
    if not mes_df.empty:
        print(f"\nGenerated {len(mes_df)} MES records")
        
        # Check for OEE calculations
        oee_values = mes_df['OEE_Score'].dropna()
        if len(oee_values) > 0:
            print(f"OEE Statistics:")
            print(f"  Mean: {oee_values.mean():.1f}%")
            print(f"  Min: {oee_values.min():.1f}%")
            print(f"  Max: {oee_values.max():.1f}%")
            
            # Check for runtime inference
            runtime_records = mes_df[mes_df['GoodUnitsProduced'] > 0]
            if len(runtime_records) > 0:
                zero_runtime = runtime_records[runtime_records['Performance_Score'] == 0]
                if len(zero_runtime) == 0:
                    print("✓ No zero performance when units produced (runtime inference working)")
                else:
                    print(f"⚠ Found {len(zero_runtime)} records with zero performance despite production")
        else:
            print("⚠ No OEE values calculated")
    else:
        print("⚠ No MES records generated")
    
    print("✓ MES transduction test completed")


def test_event_anomaly_detection():
    """Test event anomaly detection."""
    print("\n" + "="*60)
    print("TEST 4: Event Anomaly Detection")
    print("="*60)
    
    # Create inspector
    inspector = EventInspector()
    
    # Create test events with some anomalies
    test_events = [
        # Normal event
        {
            'timestamp': 10.0,
            'event_type': 'unit_produced',
            'primitive_id': 'EQ-001',
            'runtime_minutes': 5.0
        },
        # Missing timestamp
        {
            'event_type': 'unit_produced',
            'primitive_id': 'EQ-002',
            'runtime_minutes': 5.0
        },
        # Production without runtime
        {
            'timestamp': 20.0,
            'event_type': 'unit_produced',
            'primitive_id': 'EQ-003',
            'runtime_minutes': 0
        },
        # Missing primitive_id
        {
            'timestamp': 30.0,
            'event_type': 'state_change',
            'runtime_minutes': 5.0
        }
    ]
    
    # Find anomalies
    anomalies = inspector.find_anomalies(test_events)
    
    print(f"Found {len(anomalies)} anomalous events:")
    for anomaly in anomalies:
        print(f"  Issues: {', '.join(anomaly['issues'])}")
    
    print("✓ Anomaly detection test completed")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TWIN MODEL LOGGING AND OEE FIX TESTS")
    print("="*60)
    
    # Run tests
    test_basic_logging()
    test_simulation_with_logging()
    test_mes_transduction_with_fixes()
    test_event_anomaly_detection()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
    
    # Check log files
    log_dir = Path("logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            print(f"\nLog files created in {log_dir}:")
            for log_file in log_files:
                size_kb = log_file.stat().st_size / 1024
                print(f"  {log_file.name}: {size_kb:.1f} KB")
    
    print("\n✓ Testing complete. Check logs/ directory for detailed output.")


if __name__ == "__main__":
    main()