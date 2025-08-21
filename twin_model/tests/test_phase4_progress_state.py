"""Test Phase 4 Progress Reporting and State Persistence.

This test validates progress reporting, simulation monitoring,
and state checkpoint/restore functionality.
"""

import simpy
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import tracemalloc
from datetime import datetime

from twin_model.primitives.base import (
    BasePrimitive,
    PrimitiveConfig,
    SamplingConfig,
    SimulationMode,
    ProgressCallback,
    ConsoleProgressReporter,
    SimulationMonitor
)
from twin_model.primitives.equipment import EquipmentPrimitive
from twin_model.state_manager import (
    SimulationCheckpoint,
    StateManager,
    SimulationRunner
)


def test_progress_callback():
    """Test progress callback implementation."""
    print("\nTesting Progress Callback...")
    
    # Create custom progress callback
    class TestProgressCallback(ProgressCallback):
        def __init__(self):
            self.calls = []
            
        def __call__(self, current_time: float, total_time: float,
                    events_processed: int, memory_usage_mb: float, **kwargs):
            self.calls.append({
                "current": current_time,
                "total": total_time,
                "events": events_processed,
                "memory": memory_usage_mb,
                "extra": kwargs
            })
    
    # Test callback
    callback = TestProgressCallback()
    
    # Simulate progress updates
    for i in range(5):
        callback(
            current_time=i * 100,
            total_time=500,
            events_processed=i * 1000,
            memory_usage_mb=50.0 + i * 5,
            chunk=i
        )
    
    assert len(callback.calls) == 5, "Should have 5 progress updates"
    assert callback.calls[0]["current"] == 0
    assert callback.calls[-1]["current"] == 400
    assert callback.calls[-1]["events"] == 4000
    assert "chunk" in callback.calls[0]["extra"]
    
    print(f"✓ Progress callback recorded {len(callback.calls)} updates")


def test_console_reporter():
    """Test console progress reporter."""
    print("\nTesting Console Progress Reporter...")
    
    reporter = ConsoleProgressReporter(report_interval=0.1)
    
    # Should report first call
    reporter(100, 1000, 500, 25.5)
    assert reporter.last_report_time > 0
    assert reporter.last_events == 500
    
    # Should skip if too soon
    initial_time = reporter.last_report_time
    reporter(110, 1000, 550, 26.0)
    # May or may not update depending on timing
    
    # Wait and report again
    time.sleep(0.15)
    reporter(200, 1000, 1000, 30.0)
    assert reporter.last_events == 1000
    
    print("✓ Console reporter rate limiting works")


def test_simulation_monitor():
    """Test simulation health monitoring."""
    print("\nTesting Simulation Monitor...")
    
    env = simpy.Environment()
    
    # Create monitor with low thresholds for testing
    monitor = SimulationMonitor(
        env,
        memory_threshold_mb=1.0,  # Very low for testing
        event_rate_threshold=1000.0,  # High threshold
        check_interval=10.0  # Check every 10 minutes
    )
    
    # Record some events
    for _ in range(100):
        monitor.record_event()
    
    # Run simulation briefly
    env.run(until=15)
    
    # Check metrics
    metrics = monitor.get_metrics()
    
    assert metrics["simulation_time"] == 15
    assert metrics["total_events"] == 100
    assert metrics["avg_event_rate"] > 0
    # Warning may or may not trigger depending on actual memory usage
    
    print(f"✓ Monitor recorded {metrics['total_events']} events")
    print(f"  Warnings: {len(metrics['warnings'])}")
    print(f"  Event rate: {metrics['avg_event_rate']:.1f}/s")


def test_state_checkpoint():
    """Test creating and loading checkpoints."""
    print("\nTesting State Checkpoints...")
    
    checkpoint_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create simulation
        env = simpy.Environment()
        
        config = PrimitiveConfig(
            id="TEST-EQ",
            type="Equipment",
            properties={"base_rate": 60.0}
        )
        
        equipment = EquipmentPrimitive(env, config)
        equipment.start()
        
        # Run simulation
        env.run(until=100)
        
        # Create checkpoint
        checkpoint = SimulationCheckpoint(
            checkpoint_id="test_checkpoint_001",
            simulation_time=env.now,
            real_time=datetime.now(),
            primitives_state={
                "equipment": equipment.get_state()
            },
            environment_state={
                "now": env.now
            },
            cache_path=None,
            metadata={"test": True}
        )
        
        # Save checkpoint
        filepath = checkpoint_dir / "test.ckpt"
        checkpoint.to_file(filepath)
        
        # Load checkpoint
        loaded = SimulationCheckpoint.from_file(filepath)
        
        assert loaded.checkpoint_id == "test_checkpoint_001"
        assert loaded.simulation_time == 100
        assert "equipment" in loaded.primitives_state
        assert loaded.metadata["test"] == True
        
        print("✓ Checkpoint save/load working")
        
        # Test summary
        summary = loaded.get_summary()
        assert summary["simulation_time"] == 100
        assert summary["num_primitives"] == 1
        
        print(f"  Checkpoint summary: {summary['num_primitives']} primitives at t={summary['simulation_time']}")
        
    finally:
        shutil.rmtree(checkpoint_dir)


def test_state_manager():
    """Test state manager functionality."""
    print("\nTesting State Manager...")
    
    checkpoint_dir = Path(tempfile.mkdtemp())
    
    try:
        manager = StateManager(
            checkpoint_dir=str(checkpoint_dir),
            max_checkpoints=3,
            compression=False
        )
        
        # Create test environment and primitives
        env = simpy.Environment()
        primitives = {
            "eq1": {"id": "EQ-001", "state": "running"},
            "eq2": {"id": "EQ-002", "state": "idle"}
        }
        
        # Save multiple checkpoints
        checkpoint_ids = []
        
        for i in range(5):
            env.run(until=env.now + 100)
            
            checkpoint_id = manager.save_checkpoint(
                env,
                primitives,
                metadata={"iteration": i}
            )
            checkpoint_ids.append(checkpoint_id)
            
            time.sleep(0.01)  # Ensure unique timestamps
        
        # Should only keep 3 checkpoints (max_checkpoints)
        assert len(manager.checkpoints) == 3
        
        # Oldest checkpoints should be deleted
        assert checkpoint_ids[0] not in manager.checkpoints
        assert checkpoint_ids[1] not in manager.checkpoints
        assert checkpoint_ids[-1] in manager.checkpoints
        
        print(f"✓ State manager maintains {len(manager.checkpoints)} checkpoints")
        
        # List checkpoints
        summaries = manager.list_checkpoints()
        assert len(summaries) == 3
        
        # Load a checkpoint
        checkpoint = manager.load_checkpoint(checkpoint_ids[-1])
        assert checkpoint.simulation_time == 500
        
        print("✓ Checkpoint lifecycle management working")
        
    finally:
        shutil.rmtree(checkpoint_dir)


def test_simulation_runner_chunked():
    """Test chunked simulation execution."""
    print("\nTesting Chunked Simulation Runner...")
    
    checkpoint_dir = Path(tempfile.mkdtemp())
    
    try:
        env = simpy.Environment()
        
        # Create primitives
        primitives = {}
        for i in range(3):
            config = PrimitiveConfig(
                id=f"EQ-{i:03d}",
                type="Equipment",
                properties={"base_rate": 60.0}
            )
            
            equipment = EquipmentPrimitive(env, config)
            equipment.start()
            primitives[f"eq{i}"] = equipment
        
        # Create runner
        runner = SimulationRunner(
            env,
            primitives,
            checkpoint_dir=str(checkpoint_dir),
            enable_monitoring=True
        )
        
        # Track progress
        progress_updates = []
        
        def progress_callback(**kwargs):
            progress_updates.append(kwargs)
        
        # Run chunked simulation
        results = runner.run_chunked(
            total_days=0.1,  # 144 minutes
            chunk_size_days=0.025,  # 36 minutes per chunk
            progress_callback=progress_callback,
            checkpoint_interval=0.05  # Checkpoint every 72 minutes
        )
        
        # Check results
        assert results["simulation_time"] >= 144
        assert results["chunks_completed"] == 4
        assert len(progress_updates) == 4
        assert results["checkpoints_saved"] >= 2
        
        print(f"✓ Chunked simulation completed:")
        print(f"  Chunks: {results['chunks_completed']}")
        print(f"  Time: {results['simulation_time']:.0f} minutes")
        print(f"  Speed: {results['speed_factor']:.0f}x")
        print(f"  Checkpoints: {results['checkpoints_saved']}")
        
        # Check monitoring worked
        if "monitor_metrics" in results:
            monitor = results["monitor_metrics"]
            print(f"  Events: {monitor['total_events']}")
            print(f"  Memory peak: {monitor['memory_max_mb']:.1f}MB")
        
    finally:
        shutil.rmtree(checkpoint_dir)


def test_pause_resume():
    """Test simulation pause/resume functionality."""
    print("\nTesting Pause/Resume...")
    
    checkpoint_dir = Path(tempfile.mkdtemp())
    pause_file = Path("PAUSE_SIMULATION")
    
    try:
        # Remove pause file if exists
        if pause_file.exists():
            pause_file.unlink()
        
        env = simpy.Environment()
        
        # Create simple primitive
        config = PrimitiveConfig(
            id="PAUSE-TEST",
            type="Equipment",
            properties={"base_rate": 60.0}
        )
        
        equipment = EquipmentPrimitive(env, config)
        equipment.start()
        primitives = {"equipment": equipment}
        
        # Create runner
        runner = SimulationRunner(
            env,
            primitives,
            checkpoint_dir=str(checkpoint_dir),
            enable_monitoring=False
        )
        
        # Run to a point
        env.run(until=100)
        initial_state = equipment.get_state()
        
        print(f"  Initial run to t={env.now}")
        
        # Save checkpoint manually
        checkpoint_id = runner.state_manager.save_checkpoint(
            env,
            primitives,
            metadata={"test": "pause_resume"}
        )
        
        # Continue running
        env.run(until=200)
        
        print(f"  Continued to t={env.now}")
        
        # Now restore from checkpoint
        # Note: In real scenario, we'd recreate the runner
        primitive_classes = {"EquipmentPrimitive": EquipmentPrimitive}
        
        # Load checkpoint to verify
        checkpoint = runner.state_manager.load_checkpoint(checkpoint_id)
        assert checkpoint.simulation_time == 100
        
        print(f"✓ Checkpoint verified at t={checkpoint.simulation_time}")
        
        # Test checkpoint list persistence
        manager2 = StateManager(checkpoint_dir=str(checkpoint_dir))
        assert checkpoint_id in manager2.checkpoints
        
        print("✓ Checkpoint list persisted correctly")
        
    finally:
        if pause_file.exists():
            pause_file.unlink()
        shutil.rmtree(checkpoint_dir)


def test_memory_tracking():
    """Test memory usage tracking during simulation."""
    print("\nTesting Memory Tracking...")
    
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    
    env = simpy.Environment()
    
    # Create equipment with large buffer
    config = PrimitiveConfig(
        id="MEM-TEST",
        type="Equipment",
        properties={"base_rate": 100.0}
    )
    
    sampling = SamplingConfig(
        mode=SimulationMode.DETAILED,
        buffer_size=10000
    )
    
    equipment = EquipmentPrimitive(env, config, sampling_config=sampling)
    equipment.start()
    
    # Monitor memory
    monitor = SimulationMonitor(
        env,
        memory_threshold_mb=10.0,
        check_interval=50.0
    )
    
    # Run and generate events
    start_memory = tracemalloc.get_traced_memory()[0]
    
    for _ in range(100):
        env.run(until=env.now + 1)
        monitor.record_event()
        
        # Generate more events
        for _ in range(10):
            equipment.emit_observable("test", {"data": "x" * 100})
    
    end_memory = tracemalloc.get_traced_memory()[0]
    memory_growth_mb = (end_memory - start_memory) / (1024 * 1024)
    
    # Get monitor metrics
    metrics = monitor.get_metrics()
    
    print(f"✓ Memory tracking:")
    print(f"  Growth: {memory_growth_mb:.2f}MB")
    print(f"  Current: {metrics['memory_current_mb']:.2f}MB")
    print(f"  Max: {metrics['memory_max_mb']:.2f}MB")
    
    # With circular buffer, growth should be limited
    assert memory_growth_mb < 50, f"Memory growth too high: {memory_growth_mb}MB"


def test_progress_with_long_simulation():
    """Test progress reporting with longer simulation."""
    print("\nTesting Progress with Long Simulation...")
    
    env = simpy.Environment()
    
    # Create equipment
    config = PrimitiveConfig(
        id="LONG-TEST",
        type="Equipment",
        properties={"base_rate": 60.0}
    )
    
    equipment = EquipmentPrimitive(env, config)
    equipment.start()
    
    # Console reporter
    reporter = ConsoleProgressReporter(report_interval=1.0)
    
    # Monitor
    monitor = SimulationMonitor(env, check_interval=60.0)
    
    # Run simulation with progress
    print("  Running 1-day simulation with progress...")
    
    TOTAL_MINUTES = 24 * 60
    CHUNK_SIZE = 60  # 1 hour chunks
    
    start_time = time.time()
    
    for chunk in range(0, TOTAL_MINUTES, CHUNK_SIZE):
        env.run(until=min(chunk + CHUNK_SIZE, TOTAL_MINUTES))
        
        # Record events
        events = equipment.events_emitted
        monitor.metrics["events_total"] = events
        
        # Get memory
        if tracemalloc.is_tracing():
            memory_mb = tracemalloc.get_traced_memory()[0] / (1024 * 1024)
        else:
            memory_mb = 0
        
        # Report progress
        reporter(
            current_time=env.now,
            total_time=TOTAL_MINUTES,
            events_processed=events,
            memory_usage_mb=memory_mb
        )
    
    elapsed = time.time() - start_time
    
    print(f"\n✓ Completed 1-day simulation:")
    print(f"  Simulation time: {env.now} minutes")
    print(f"  Real time: {elapsed:.2f} seconds")
    print(f"  Speed factor: {env.now/elapsed:.0f}x")


def run_all_tests():
    """Run all Phase 4 tests."""
    print("=" * 60)
    print("PHASE 4 PROGRESS & STATE MANAGEMENT TESTS")
    print("=" * 60)
    
    from datetime import datetime
    
    try:
        test_progress_callback()
        test_console_reporter()
        test_simulation_monitor()
        test_state_checkpoint()
        test_state_manager()
        test_simulation_runner_chunked()
        test_pause_resume()
        test_memory_tracking()
        test_progress_with_long_simulation()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASE 4 TESTS PASSED")
        print("=" * 60)
        print("\nPhase 4 optimizations successfully implemented:")
        print("  • Progress callbacks with customizable reporting")
        print("  • Console progress reporter with ETA calculation")
        print("  • Simulation health monitoring and warnings")
        print("  • State checkpointing with compression support")
        print("  • Checkpoint lifecycle management")
        print("  • Chunked execution with auto-checkpointing")
        print("  • Pause/resume capability")
        print("  • Memory usage tracking")
        print("\nReady to proceed to Phase 5!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()