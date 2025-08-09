"""
Test Phase 1: Twin Ontology and Virtual Sensors
Validates SOSA/QUDT compliance and sensor definitions
"""

import yaml
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_twin_ontology():
    """Test twin ontology specification"""
    print("=" * 60)
    print("TESTING PHASE 1: TWIN ONTOLOGY")
    print("=" * 60)
    
    # Load twin ontology
    with open('ontology/twin_ontology_spec.yaml', 'r') as f:
        twin_ontology = yaml.safe_load(f)
    
    print("\n1. ONTOLOGY METADATA CHECK")
    print("-" * 40)
    
    # Check required metadata
    assert 'ontology' in twin_ontology, "Missing ontology metadata"
    metadata = twin_ontology['ontology']
    
    required_fields = ['name', 'version', 'namespace', 'description', 'standards']
    for field in required_fields:
        assert field in metadata, f"Missing required field: {field}"
        print(f"✓ {field}: {metadata[field] if not isinstance(metadata[field], list) else f'{len(metadata[field])} items'}")
    
    # Check standards compliance
    print("\n2. STANDARDS COMPLIANCE CHECK")
    print("-" * 40)
    standards = metadata.get('standards', [])
    assert len(standards) > 0, "No standards defined"
    
    for standard in standards:
        print(f"✓ {standard['name']}: {standard['compliance']}")
    
    # Check imports
    print("\n3. ONTOLOGY IMPORTS CHECK")
    print("-" * 40)
    imports = metadata.get('imports', [])
    assert len(imports) > 0, "No imports defined"
    
    required_imports = ['sosa', 'ssn', 'qudt']
    for imp in imports:
        for req in required_imports:
            if req in imp.lower():
                print(f"✓ Found {req.upper()} import: {imp}")
    
    # Check virtual sensors
    print("\n4. VIRTUAL SENSORS CHECK")
    print("-" * 40)
    assert 'virtual_sensors' in twin_ontology, "Missing virtual_sensors section"
    sensors = twin_ontology['virtual_sensors']
    
    # Check Equipment sensors
    assert 'Equipment' in sensors, "Missing Equipment sensors"
    equipment_sensors = sensors['Equipment']['embeds']
    
    required_sensors = [
        'ThroughputSensor',
        'QualityInspector',
        'PowerMeter',
        'PerformanceSensor',
        'MaterialFlowSensor',
        'VibrationSensor',
        'TemperatureSensor',
        'AvailabilitySensor'
    ]
    
    sensor_count = 0
    for sensor_list in equipment_sensors:
        for sensor_name in sensor_list.keys():
            if sensor_name in required_sensors:
                sensor_count += 1
                sensor_def = sensor_list[sensor_name]
                
                # Check SOSA compliance
                assert 'type' in sensor_def, f"{sensor_name} missing type"
                assert 'sosa:Sensor' in sensor_def['type'], f"{sensor_name} not SOSA compliant"
                
                # Check QUDT units
                assert 'observes' in sensor_def, f"{sensor_name} missing observes"
                observes = sensor_def['observes']
                if isinstance(observes, dict):
                    assert 'unit' in observes, f"{sensor_name} missing unit"
                    assert 'qudt.org' in observes['unit'], f"{sensor_name} not using QUDT units"
                
                print(f"✓ {sensor_name}: SOSA compliant, QUDT units")
    
    print(f"\nTotal sensors defined: {sensor_count}/{len(required_sensors)}")
    
    # Check synchronization metadata
    print("\n5. SYNCHRONIZATION METADATA CHECK")
    print("-" * 40)
    assert 'synchronization' in twin_ontology, "Missing synchronization section"
    sync = twin_ontology['synchronization']
    
    assert 'Equipment' in sync, "Missing Equipment synchronization"
    eq_sync = sync['Equipment']
    
    required_sync_fields = ['interval', 'source_type', 'health_thresholds']
    for field in required_sync_fields:
        assert field in eq_sync, f"Missing sync field: {field}"
        print(f"✓ {field}: {eq_sync[field] if not isinstance(eq_sync[field], dict) else 'defined'}")
    
    # Check ISO 8601 duration format
    interval = eq_sync['interval']
    assert interval.startswith('PT'), "Interval not in ISO 8601 format"
    print(f"✓ ISO 8601 duration format: {interval}")
    
    # Check observation classes
    print("\n6. OBSERVATION CLASSES CHECK")
    print("-" * 40)
    assert 'observation_classes' in twin_ontology, "Missing observation_classes"
    obs_classes = twin_ontology['observation_classes']
    
    required_obs = ['ThroughputObservation', 'QualityObservation', 'BufferLevelObservation']
    for obs in required_obs:
        assert obs in obs_classes, f"Missing observation class: {obs}"
        obs_def = obs_classes[obs]
        assert obs_def['type'] == 'sosa:Observation', f"{obs} not SOSA Observation"
        print(f"✓ {obs}: SOSA Observation compliant")
    
    print("\n✅ PHASE 1 ONTOLOGY TEST PASSED!")
    return True


def test_sync_health():
    """Test synchronization health monitoring"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 1: SYNC HEALTH MONITORING")
    print("=" * 60)
    
    from twin.sync_health import SyncHealthMonitor, SyncHealthStatus
    import time
    from datetime import datetime, timedelta
    
    # Create monitor
    monitor = SyncHealthMonitor()
    print("\n✓ SyncHealthMonitor initialized")
    
    # Test 1: Update sync metadata
    print("\n1. TESTING SYNC METADATA UPDATE")
    print("-" * 40)
    
    test_equipment = [
        ("LINE1-FIL", "Equipment"),
        ("LINE1-PCK", "Equipment"),
        ("LINE2-FIL", "Equipment")
    ]
    
    for eq_id, eq_type in test_equipment:
        metadata = monitor.update_sync_metadata(
            entity_id=eq_id,
            entity_type=eq_type,
            data={"test": "data"},
            source_run_id="test-run-001",
            sync_interval_minutes=5
        )
        assert metadata.health_status == SyncHealthStatus.HEALTHY
        print(f"✓ {eq_id}: Updated with HEALTHY status")
    
    # Test 2: Get sync health
    print("\n2. TESTING SYNC HEALTH RETRIEVAL")
    print("-" * 40)
    
    health_list = monitor.get_sync_health()
    assert len(health_list) >= len(test_equipment), "Not all equipment in health list"
    print(f"✓ Retrieved health for {len(health_list)} entities")
    
    # Test 3: Health summary
    print("\n3. TESTING HEALTH SUMMARY")
    print("-" * 40)
    
    summary = monitor.get_health_summary()
    assert 'HEALTHY' in summary
    assert 'DELAYED' in summary
    assert 'STALE' in summary
    print(f"✓ Summary: HEALTHY={summary['HEALTHY']}, DELAYED={summary['DELAYED']}, STALE={summary['STALE']}")
    
    # Test 4: Specific entity health
    print("\n4. TESTING SPECIFIC ENTITY HEALTH")
    print("-" * 40)
    
    specific_health = monitor.get_sync_health("LINE1-FIL")
    assert len(specific_health) > 0, "No health data for specific entity"
    assert specific_health[0].entity_id == "LINE1-FIL"
    print(f"✓ Retrieved health for LINE1-FIL: {specific_health[0].health_status.value}")
    
    # Test 5: Alert checking
    print("\n5. TESTING ALERT SYSTEM")
    print("-" * 40)
    
    # Force some entities to be stale by updating timestamp directly
    import sqlite3
    with sqlite3.connect(monitor.db_path) as conn:
        old_time = (datetime.now() - timedelta(hours=1)).isoformat()
        conn.execute(
            "UPDATE entity_sync_metadata SET last_update = ? WHERE entity_id = ?",
            (old_time, "LINE1-FIL")
        )
        conn.commit()
    
    alerts = monitor.check_and_alert(alert_threshold="STALE")
    print(f"✓ Alert system detected {len(alerts)} stale entities")
    
    # Test 6: Visualization
    print("\n6. TESTING VISUALIZATION")
    print("-" * 40)
    
    viz = monitor.visualize_health()
    assert "SYNCHRONIZATION HEALTH DASHBOARD" in viz
    assert "HEALTHY" in viz or "DELAYED" in viz or "STALE" in viz
    print("✓ Visualization generated successfully")
    
    print("\n✅ PHASE 1 SYNC HEALTH TEST PASSED!")
    return True


if __name__ == "__main__":
    try:
        # Test ontology
        test_twin_ontology()
        
        # Test sync health
        test_sync_health()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASE 1 TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)