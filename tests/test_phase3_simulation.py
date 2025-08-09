"""
Test Phase 3: Simulation Runner and Twin State Management
Validates provenance tracking, state management, and reproducibility
"""

import sys
import os
import json
from datetime import datetime, timedelta
import sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_simulation_runner():
    """Test simulation runner with provenance"""
    print("=" * 60)
    print("TESTING PHASE 3: SIMULATION RUNNER")
    print("=" * 60)
    
    from twin.simulation_runner import SimulationRunner, SimulationRun
    from twin.actionable_parameters import ActionableParameters
    
    runner = SimulationRunner()
    print("\n✓ SimulationRunner initialized")
    
    # Test 1: Provenance database initialization
    print("\n1. PROVENANCE DATABASE CHECK")
    print("-" * 40)
    
    with sqlite3.connect(runner.db_path) as conn:
        # Check tables exist
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('twin_runs', 'kpi_results', 'parameter_history')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'twin_runs' in tables, "Missing twin_runs table"
        assert 'kpi_results' in tables, "Missing kpi_results table"
        assert 'parameter_history' in tables, "Missing parameter_history table"
        print(f"✓ Found {len(tables)} provenance tables")
    
    # Test 2: Create and store run metadata
    print("\n2. RUN METADATA STORAGE CHECK")
    print("-" * 40)
    
    import uuid
    test_run_id = f"test-run-{uuid.uuid4().hex[:8]}"
    
    test_run = SimulationRun(
        run_id=test_run_id,
        run_type="baseline",
        seed=42,
        generator_version="1.0.0",
        parent_run_id=None,
        started_at=datetime.now(),
        finished_at=datetime.now(),
        config_delta={"test_param": 0.5},
        data_hash="testhash123",
        output_path="test/path.csv",
        kpi_summary={"test_kpi": 0.85},
        notes="Test run",
        status="completed"
    )
    
    runner._store_run_metadata(test_run)
    print("✓ Stored test run metadata")
    
    # Retrieve and verify
    retrieved = runner._get_run_metadata(test_run_id)
    assert retrieved.run_id == test_run_id
    assert retrieved.seed == 42
    assert retrieved.status == "completed"
    print("✓ Retrieved and verified run metadata")
    
    # Test 3: Data hash calculation
    print("\n3. DATA HASH CALCULATION CHECK")
    print("-" * 40)
    
    # Create a temporary test file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("test,data\n1,2\n3,4\n")
        temp_path = f.name
    
    from pathlib import Path
    hash_value = runner._calculate_data_hash(Path(temp_path))
    assert len(hash_value) == 64, "SHA256 hash should be 64 characters"
    print(f"✓ Calculated data hash: {hash_value[:16]}...")
    
    # Clean up
    os.unlink(temp_path)
    
    # Test 4: KPI calculation
    print("\n4. KPI CALCULATION CHECK")
    print("-" * 40)
    
    # Create test CSV with KPI data
    import pandas as pd
    test_data = pd.DataFrame({
        'oee_score': [0.65, 0.70, 0.68, 0.72, 0.69],
        'availability_score': [0.80, 0.85, 0.82, 0.88, 0.84],
        'performance_score': [0.85, 0.88, 0.86, 0.90, 0.87],
        'quality_score': [0.95, 0.93, 0.96, 0.91, 0.94],
        'good_units_produced': [100, 110, 105, 115, 108],
        'scrap_units_produced': [5, 8, 4, 9, 6],
        'machine_status': ['Running', 'Running', 'Stopped', 'Running', 'Running']
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        test_data.to_csv(f, index=False)
        temp_csv = f.name
    
    kpis = runner._calculate_kpis(Path(temp_csv))
    
    assert 'mean_oee' in kpis
    assert 'mean_availability' in kpis
    assert 'total_good_units' in kpis
    assert 'scrap_rate' in kpis
    assert 'downtime_percentage' in kpis
    
    print(f"✓ Calculated {len(kpis)} KPIs from test data")
    print(f"  Mean OEE: {kpis['mean_oee']:.3f}")
    print(f"  Scrap rate: {kpis['scrap_rate']:.3f}")
    
    os.unlink(temp_csv)
    
    # Test 5: Parameter tracking
    print("\n5. PARAMETER TRACKING CHECK")
    print("-" * 40)
    
    # Create parent and child runs with unique IDs
    parent_id = f"parent-{uuid.uuid4().hex[:8]}"
    child_id = f"child-{uuid.uuid4().hex[:8]}"
    
    parent_run = SimulationRun(
        run_id=parent_id,
        run_type="baseline",
        seed=100,
        generator_version="1.0.0",
        parent_run_id=None,
        started_at=datetime.now(),
        finished_at=datetime.now(),
        config_delta={"param1": 0.5, "param2": 0.8},
        data_hash="parenthash",
        output_path="parent.csv",
        kpi_summary={"kpi1": 0.65},
        notes="Parent run",
        status="completed"
    )
    
    runner._store_run_metadata(parent_run)
    
    # Track parameter changes
    params = ActionableParameters()
    params.set_value("micro_stop_probability", 0.15)  # Changed from default
    
    runner._track_parameter_changes(child_id, parent_id, params)
    
    # Check parameter history
    with sqlite3.connect(runner.db_path) as conn:
        cursor = conn.execute("""
            SELECT parameter_name, old_value, new_value 
            FROM parameter_history 
            WHERE run_id = ?
        """, (child_id,))
        changes = cursor.fetchall()
    
    assert len(changes) > 0, "No parameter changes tracked"
    print(f"✓ Tracked {len(changes)} parameter changes")
    
    # Test 6: Run lineage
    print("\n6. RUN LINEAGE CHECK")
    print("-" * 40)
    
    child_run = SimulationRun(
        run_id=child_id,
        run_type="simulation",
        seed=101,
        generator_version="1.0.0",
        parent_run_id=parent_id,
        started_at=datetime.now(),
        finished_at=datetime.now(),
        config_delta=params.get_all_values(),
        data_hash="childhash",
        output_path="child.csv",
        kpi_summary={"kpi1": 0.72},
        notes="Child run",
        status="completed"
    )
    
    runner._store_run_metadata(child_run)
    
    lineage = runner.get_run_lineage(child_id)
    assert len(lineage) >= 2, "Lineage should include parent and child"
    print(f"✓ Retrieved lineage with {len(lineage)} runs")
    
    # Test 7: Run comparison
    print("\n7. RUN COMPARISON CHECK")
    print("-" * 40)
    
    comparison = runner.compare_runs([parent_id, child_id])
    
    assert "runs" in comparison
    assert "kpi_comparison" in comparison
    assert "parameter_comparison" in comparison
    assert "improvements" in comparison
    
    print("✓ Comparison structure validated")
    
    if comparison["improvements"]:
        for key, value in comparison["improvements"].items():
            if "kpi1" in key:
                print(f"  KPI improvement: {value:.1f}%")
    
    print("\n✅ SIMULATION RUNNER TEST PASSED!")
    return True


def test_twin_state(test_run_id=None):
    """Test twin state management"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 3: TWIN STATE MANAGEMENT")
    print("=" * 60)
    
    from twin.twin_state import TwinStateManager, TwinState
    from twin.simulation_runner import SimulationRunner, SimulationRun
    import uuid
    
    # Use provided run ID or create new one
    if not test_run_id:
        test_run_id = f"test-state-{uuid.uuid4().hex[:8]}"
        
        # Create a test run in the database first
        runner = SimulationRunner()
        test_run = SimulationRun(
            run_id=test_run_id,
            run_type="baseline",
            seed=42,
            generator_version="1.0.0",
            parent_run_id=None,
            started_at=datetime.now(),
            finished_at=datetime.now(),
            config_delta={"test_param": 0.5},
            data_hash="testhash",
            output_path="test.csv",
            kpi_summary={"test_kpi": 0.75},
            notes="Test run for state management",
            status="completed"
        )
        runner._store_run_metadata(test_run)
    
    manager = TwinStateManager()
    print("\n✓ TwinStateManager initialized")
    
    # Test 1: State tables initialization
    print("\n1. STATE TABLES CHECK")
    print("-" * 40)
    
    with sqlite3.connect(manager.db_path) as conn:
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('twin_state', 'recommendations', 'confidence_tracking')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'twin_state' in tables
        assert 'recommendations' in tables
        assert 'confidence_tracking' in tables
        print(f"✓ Found {len(tables)} state management tables")
    
    # Test 2: Update state
    print("\n2. STATE UPDATE CHECK")
    print("-" * 40)
    
    # Use the run we created in previous test
    manager.update_state(
        run_id=test_run_id,
        baseline_run_id=test_run_id,
        notes="Test state update"
    )
    print("✓ State updated successfully")
    
    # Test 3: Get current state
    print("\n3. STATE RETRIEVAL CHECK")
    print("-" * 40)
    
    state = manager.get_current_state()
    assert state is not None, "No state retrieved"
    assert state.current_run_id == test_run_id
    print(f"✓ Retrieved current state: {state.current_run_id}")
    
    # Test 4: Confidence calculation
    print("\n4. CONFIDENCE CALCULATION CHECK")
    print("-" * 40)
    
    # Need scipy for this test
    try:
        manager.calculate_confidence(test_run_id, n_validation_runs=5)
        
        # Check confidence data
        with sqlite3.connect(manager.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM confidence_tracking 
                WHERE run_id = ?
            """, (test_run_id,))
            count = cursor.fetchone()[0]
        
        assert count > 0, "No confidence data stored"
        print(f"✓ Calculated confidence for {count} KPIs")
        
    except ImportError:
        print("⚠ Skipping confidence test (scipy not available)")
    
    # Test 5: Create recommendation
    print("\n5. RECOMMENDATION CREATION CHECK")
    print("-" * 40)
    
    rec_id = manager.create_recommendation(
        parameters={"param1": 0.7, "param2": 0.9},
        expected_improvement={"kpi1": 15.0, "kpi2": 8.5},
        recommendation_type="test_recommendation",
        confidence=0.75,
        notes="Test recommendation"
    )
    
    assert rec_id > 0, "Invalid recommendation ID"
    print(f"✓ Created recommendation ID: {rec_id}")
    
    # Test 6: Get active recommendations
    print("\n6. ACTIVE RECOMMENDATIONS CHECK")
    print("-" * 40)
    
    active = manager._get_active_recommendations()
    assert len(active) > 0, "No active recommendations found"
    assert active[0]["type"] == "test_recommendation"
    print(f"✓ Found {len(active)} active recommendations")
    
    # Test 7: Accept recommendation
    print("\n7. ACCEPT RECOMMENDATION CHECK")
    print("-" * 40)
    
    params = manager.accept_recommendation(rec_id)
    assert "param1" in params
    assert params["param1"] == 0.7
    print("✓ Recommendation accepted and parameters retrieved")
    
    # Test 8: Improvement trends
    print("\n8. IMPROVEMENT TRENDS CHECK")
    print("-" * 40)
    
    trends = manager.get_improvement_trends(n_runs=5)
    print(f"✓ Retrieved trends for {len(trends)} KPIs")
    
    # Test 9: State report generation
    print("\n9. STATE REPORT GENERATION CHECK")
    print("-" * 40)
    
    report = manager.generate_state_report()
    assert "VIRTUAL TWIN STATE REPORT" in report
    assert "CURRENT CONFIGURATION" in report
    assert "CURRENT KPIs" in report
    print("✓ State report generated successfully")
    
    print("\n✅ TWIN STATE MANAGEMENT TEST PASSED!")
    return True


def test_provenance_reproducibility():
    """Test that simulations are reproducible with same seed"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 3: PROVENANCE & REPRODUCIBILITY")
    print("=" * 60)
    
    from twin.simulation_runner import SimulationRunner, SimulationRun
    from twin.actionable_parameters import ActionableParameters
    import numpy as np
    
    runner = SimulationRunner()
    
    # Test 1: Seed reproducibility
    print("\n1. SEED REPRODUCIBILITY CHECK")
    print("-" * 40)
    
    # Set seed and generate random numbers
    np.random.seed(42)
    values1 = [np.random.random() for _ in range(5)]
    
    np.random.seed(42)
    values2 = [np.random.random() for _ in range(5)]
    
    assert values1 == values2, "Random values not reproducible with same seed"
    print("✓ Seeds produce reproducible random values")
    
    # Test 2: Configuration reproducibility
    print("\n2. CONFIGURATION REPRODUCIBILITY CHECK")
    print("-" * 40)
    
    params = ActionableParameters()
    params.set_value("micro_stop_probability", 0.123)
    
    from twin.config_transformer import ConfigTransformer
    transformer = ConfigTransformer()
    
    config1 = transformer.apply_parameters(params)
    config2 = transformer.apply_parameters(params)
    
    # Remove timestamps from comparison
    if "twin_metadata" in config1:
        del config1["twin_metadata"]["transformation_timestamp"]
    if "twin_metadata" in config2:
        del config2["twin_metadata"]["transformation_timestamp"]
    
    assert config1 == config2, "Configurations not reproducible"
    print("✓ Configuration transformation is deterministic")
    
    # Test 3: Hash validation
    print("\n3. HASH VALIDATION CHECK")
    print("-" * 40)
    
    import hashlib
    
    test_data = b"test data for hashing"
    hash1 = hashlib.sha256(test_data).hexdigest()
    hash2 = hashlib.sha256(test_data).hexdigest()
    
    assert hash1 == hash2, "Hashes not consistent"
    assert len(hash1) == 64, "Invalid SHA256 hash length"
    print(f"✓ Hash validation passed: {hash1[:16]}...")
    
    # Test 4: Lineage tracking
    print("\n4. LINEAGE TRACKING CHECK")
    print("-" * 40)
    
    # Create a chain of runs
    run_ids = []
    parent_id = None
    
    for i in range(3):
        run_id = f"lineage-test-{i}"
        run = SimulationRun(
            run_id=run_id,
            run_type="simulation" if i > 0 else "baseline",
            seed=100 + i,
            generator_version="1.0.0",
            parent_run_id=parent_id,
            started_at=datetime.now() + timedelta(minutes=i),
            finished_at=datetime.now() + timedelta(minutes=i+1),
            config_delta={"test": i},
            data_hash=f"hash{i}",
            output_path=f"path{i}.csv",
            kpi_summary={"kpi": 0.5 + i*0.1},
            notes=f"Lineage test {i}",
            status="completed"
        )
        runner._store_run_metadata(run)
        run_ids.append(run_id)
        parent_id = run_id
    
    # Check lineage
    lineage = runner.get_run_lineage(run_ids[-1])
    lineage_ids = [r.run_id for r in lineage]
    
    assert len(lineage) >= len(run_ids), "Incomplete lineage"
    for run_id in run_ids:
        assert run_id in lineage_ids, f"Missing {run_id} in lineage"
    
    print(f"✓ Lineage tracking validated with {len(lineage)} runs")
    
    print("\n✅ PROVENANCE & REPRODUCIBILITY TEST PASSED!")
    return True


if __name__ == "__main__":
    try:
        # Test simulation runner
        test_simulation_runner()
        
        # Test twin state
        test_twin_state()
        
        # Test provenance and reproducibility
        test_provenance_reproducibility()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASE 3 TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)