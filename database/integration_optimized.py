"""Optimized database integration with performance configuration.

This module provides enhanced database integration using the performance
optimization features developed in Phases 1-5.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import simpy
from sqlmodel import Session
import pandas as pd
from datetime import datetime
import tracemalloc
import time
import tempfile
import shutil

from database.manager import TwinDatabaseManager
from database.repositories import *
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction.mes_transducer import MESTransducer
from twin_model.config import PerformanceConfig, ConfigPreset
from twin_model.primitives.base import (
    SamplingConfig,
    SimulationMode,
    ConsoleProgressReporter,
    SimulationMonitor
)
from twin_model.storage.cache import ObservableCache
from twin_model.state_manager import SimulationRunner


class OptimizedTwinDatabaseIntegration:
    """Enhanced database integration with performance optimizations.
    
    This class integrates all performance optimizations from Phases 1-5:
    - Configurable performance settings
    - Memory-efficient event handling
    - Batched database operations
    - Progress reporting
    - State persistence
    - Automatic mode switching on memory pressure
    
    Attributes:
        db_manager: Database manager instance
        perf_config: Performance configuration
        cache_dir: Directory for event caching
        checkpoint_dir: Directory for state checkpoints
        monitor: Optional simulation monitor
    """
    
    def __init__(self,
                 db_manager: Optional[TwinDatabaseManager] = None,
                 perf_config: Optional[PerformanceConfig] = None):
        """Initialize optimized integration.
        
        Args:
            db_manager: Database manager (creates default if None)
            perf_config: Performance configuration (uses PRODUCTION preset if None)
        """
        self.db_manager = db_manager or TwinDatabaseManager()
        self.perf_config = perf_config or PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
        
        # Setup temporary directories
        self.cache_dir = Path(tempfile.mkdtemp(prefix="twin_cache_"))
        self.checkpoint_dir = Path(tempfile.mkdtemp(prefix="twin_checkpoint_"))
        self.monitor: Optional[SimulationMonitor] = None
        
    def __del__(self):
        """Cleanup temporary directories on deletion."""
        try:
            if hasattr(self, 'cache_dir') and self.cache_dir.exists():
                shutil.rmtree(self.cache_dir, ignore_errors=True)
            if hasattr(self, 'checkpoint_dir') and self.checkpoint_dir.exists():
                shutil.rmtree(self.checkpoint_dir, ignore_errors=True)
        except:
            pass
    
    def run_simulation_to_db(self,
                            run_type: str = "experiment",
                            parameters: Dict[str, Any] = None,
                            days: float = 1,
                            parent_run_id: Optional[str] = None,
                            perf_config: Optional[PerformanceConfig] = None,
                            show_progress: bool = True) -> str:
        """Run optimized simulation and store results in database.
        
        Uses all performance optimizations including:
        - Circular buffers for memory efficiency
        - Event sampling based on configuration
        - Batched database operations
        - Cache-based event storage
        - Progress reporting
        - Automatic checkpointing
        
        Args:
            run_type: Type of simulation run
            parameters: Simulation parameters
            days: Duration in days
            parent_run_id: Optional parent run ID
            perf_config: Override performance configuration
            show_progress: Show progress updates
            
        Returns:
            Run ID of completed simulation
            
        Raises:
            Exception: If simulation fails
        """
        parameters = parameters or {}
        config = perf_config or self.perf_config
        
        # Start memory tracking if monitoring enabled
        if config.enable_monitoring:
            tracemalloc.start()
        
        # Get versions
        ontology_version = self.db_manager.get_ontology_version()
        manifest_version = self.db_manager.get_manifest_version()
        
        with Session(self.db_manager.engine) as session:
            # Create run record
            run_repo = TwinRunRepository(session)
            run = run_repo.create_run(
                run_type=run_type,
                ontology_version=ontology_version,
                manifest_version=manifest_version,
                parameters=parameters,
                parent_run_id=parent_run_id
            )
            
            print(f"\n{'='*60}")
            print(f"OPTIMIZED SIMULATION: {run.run_id}")
            print(f"{'='*60}")
            print(f"Configuration: {config.name}")
            print(f"Duration: {days} days")
            print(f"Mode: {config.simulation_mode.value}")
            print(f"Sampling: 1/{config.sampling_rate} ({100/config.sampling_rate:.1f}%)")
            print(f"Memory limit: {config.max_memory_mb:.0f}MB")
            
            try:
                # Update status to running
                run_repo.update_run_status(run.run_id, "running")
                
                # Build model with optimized configuration
                builder = OntologyDrivenModelBuilder(
                    Path(self.db_manager.ontology_path),
                    Path(self.db_manager.manifest_dir)
                )
                
                env = simpy.Environment()
                
                # Setup monitoring if enabled
                if config.enable_monitoring:
                    self.monitor = SimulationMonitor(
                        env,
                        memory_threshold_mb=config.max_memory_mb,
                        event_rate_threshold=100.0,
                        check_interval=config.monitoring_interval
                    )
                
                # Build model with sampling configuration
                sampling = SamplingConfig(
                    mode=config.simulation_mode,
                    sampling_rate=config.sampling_rate,
                    buffer_size=config.observable_buffer_size,
                    aggregation_interval=config.aggregation_interval,
                    enable_global_observables=config.enable_global_observables
                )
                
                # Build primitives with optimized settings
                model = builder.build_model(env)
                
                # Apply sampling to all primitives
                for primitive_id, primitive in builder.primitives.items():
                    if hasattr(primitive, 'sampling_config'):
                        primitive.sampling_config = sampling
                    if hasattr(primitive, 'observable_buffer'):
                        primitive.observable_buffer.buffer_size = config.observable_buffer_size
                
                # Setup event cache
                cache = ObservableCache(
                    self.cache_dir,
                    max_size=config.cache_max_size,
                    dtype_size=512
                )
                
                # Create simulation runner
                runner = SimulationRunner(
                    env,
                    builder.primitives,
                    checkpoint_dir=str(self.checkpoint_dir),
                    enable_monitoring=config.enable_monitoring
                )
                runner.cache_path = str(self.cache_dir)
                
                # Setup progress reporting
                progress_callback = None
                if show_progress and config.enable_progress:
                    progress_callback = ConsoleProgressReporter(report_interval=5.0)
                
                # Run simulation with optimizations
                start_time = time.time()
                
                results = runner.run_chunked(
                    total_days=days,
                    chunk_size_days=config.chunk_size_days,
                    progress_callback=progress_callback,
                    checkpoint_interval=config.checkpoint_interval / 1440 if config.checkpoint_interval else None
                )
                
                elapsed = time.time() - start_time
                
                print(f"\n✓ Simulation completed in {elapsed:.2f}s")
                print(f"  Speed: {results['speed_factor']:.0f}x real-time")
                
                # Process events efficiently
                print("\nProcessing events...")
                
                # Collect observables with batching
                all_observables = []
                batch_size = config.batch_size
                
                for primitive_id, primitive in builder.primitives.items():
                    if hasattr(primitive, 'observable_buffer'):
                        # Get events from buffer
                        events = list(primitive.observable_buffer.buffer)
                        
                        for event in events:
                            event['primitive_id'] = primitive_id
                            event['primitive_type'] = type(primitive).__name__
                            all_observables.append(event)
                            
                            # Write to cache in batches
                            if len(all_observables) >= batch_size:
                                cache.write_batch(all_observables)
                                all_observables = []
                                
                                if self.monitor:
                                    self.monitor.metrics["events_total"] += batch_size
                
                # Write remaining events
                if all_observables:
                    cache.write_batch(all_observables)
                    if self.monitor:
                        self.monitor.metrics["events_total"] += len(all_observables)
                
                # Get cache statistics
                cache_stats = cache.get_stats()
                print(f"  Events cached: {cache_stats['total_events']:,}")
                print(f"  Cache size: {cache_stats['total_size_mb']:.2f}MB")
                
                # Check memory before database operations
                if config.enable_monitoring:
                    current_memory, peak_memory = tracemalloc.get_traced_memory()
                    memory_mb = peak_memory / (1024 * 1024)
                    
                    if memory_mb > config.max_memory_mb:
                        print(f"  ⚠️  Memory pressure detected: {memory_mb:.1f}MB")
                        print(f"  Switching to FAST mode for database operations")
                        # Switch to more aggressive settings
                        config.batch_size = min(10000, config.batch_size * 2)
                
                # Flush cache to database in batches
                print("\nFlushing to database...")
                
                sim_repo = SimulationDataRepository(session)
                flush_stats = sim_repo.flush_cache_to_database(
                    run_id=run.run_id,
                    cache_path=str(self.cache_dir),
                    batch_size=config.batch_size
                )
                
                print(f"  Events inserted: {flush_stats['events_inserted']:,}")
                print(f"  Rate: {flush_stats['events_per_second']:.0f} events/s")
                
                # Calculate KPIs
                print("\nCalculating KPIs...")
                kpi_summary = sim_repo.calculate_kpi_snapshot(run.run_id)
                
                # Create KPI snapshot
                kpi_repo = KPIRepository(session)
                kpi_repo.create_kpi_snapshot(
                    run_id=run.run_id,
                    entity_type="overall",
                    entity_id="LINE1",
                    kpis=kpi_summary,
                    period_start=datetime.utcnow(),
                    period_end=datetime.utcnow()
                )
                
                # Update run as completed
                run_repo.update_run_status(
                    run.run_id, 
                    "completed",
                    kpi_summary
                )
                
                # Final statistics
                if config.enable_monitoring and self.monitor:
                    monitor_metrics = self.monitor.get_metrics()
                    print(f"\nPerformance Metrics:")
                    print(f"  Peak memory: {monitor_metrics['memory_max_mb']:.1f}MB")
                    print(f"  Avg event rate: {monitor_metrics['avg_event_rate']:.0f}/s")
                    print(f"  Warnings: {len(monitor_metrics['warnings'])}")
                    
                    tracemalloc.stop()
                
                print(f"\n✓ Run complete: {run.run_id}")
                print(f"  Mean OEE: {kpi_summary.get('mean_oee', 0):.1f}%")
                print(f"  Total Good Units: {kpi_summary.get('total_good_units', 0):,}")
                
                return run.run_id
                
            except Exception as e:
                run_repo.update_run_status(run.run_id, "failed")
                print(f"\n❌ Simulation failed: {e}")
                raise e
            
            finally:
                # Cleanup cache
                cache.clear()
    
    def run_performance_benchmark(self,
                                  days: float = 1,
                                  num_primitives: Optional[int] = None) -> Dict[str, Any]:
        """Run performance benchmark with different configurations.
        
        Tests multiple performance configurations and compares results.
        
        Args:
            days: Simulation duration
            num_primitives: Number of primitives (uses default model if None)
            
        Returns:
            Dictionary with benchmark results
        """
        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARK")
        print("="*60)
        
        results = {}
        
        # Test different configurations
        configs_to_test = [
            ConfigPreset.FAST,
            ConfigPreset.PRODUCTION,
            ConfigPreset.MEMORY_OPTIMIZED
        ]
        
        for preset in configs_to_test:
            config = PerformanceConfig.from_preset(preset)
            
            print(f"\nTesting {preset.value} configuration...")
            
            start_time = time.time()
            
            try:
                run_id = self.run_simulation_to_db(
                    run_type="benchmark",
                    parameters={"config": preset.value},
                    days=days,
                    perf_config=config,
                    show_progress=False
                )
                
                elapsed = time.time() - start_time
                
                # Get KPIs
                with Session(self.db_manager.engine) as session:
                    kpi_repo = KPIRepository(session)
                    from sqlmodel import select
                    
                    statement = select(KPISnapshot).where(
                        KPISnapshot.run_id == run_id
                    )
                    kpi = session.exec(statement).first()
                    
                    results[preset.value] = {
                        "run_id": run_id,
                        "elapsed_seconds": elapsed,
                        "mean_oee": kpi.mean_oee if kpi else 0,
                        "total_units": kpi.total_good_units if kpi else 0,
                        "config": config.name,
                        "success": True
                    }
                    
            except Exception as e:
                results[preset.value] = {
                    "error": str(e),
                    "success": False
                }
        
        # Compare results
        print("\n" + "="*60)
        print("BENCHMARK RESULTS")
        print("="*60)
        
        for config_name, result in results.items():
            if result["success"]:
                print(f"\n{config_name}:")
                print(f"  Time: {result['elapsed_seconds']:.2f}s")
                print(f"  OEE: {result['mean_oee']:.1f}%")
                print(f"  Units: {result['total_units']:,}")
            else:
                print(f"\n{config_name}: FAILED - {result.get('error', 'Unknown error')}")
        
        return results
    
    def auto_optimize_configuration(self,
                                   days: float,
                                   target_memory_mb: float = 500.0) -> PerformanceConfig:
        """Automatically optimize configuration for simulation.
        
        Analyzes simulation requirements and recommends optimal configuration.
        
        Args:
            days: Simulation duration
            target_memory_mb: Target memory budget
            
        Returns:
            Optimized PerformanceConfig
        """
        # Count primitives in model
        builder = OntologyDrivenModelBuilder(
            Path(self.db_manager.ontology_path),
            Path(self.db_manager.manifest_dir)
        )
        
        env = simpy.Environment()
        model = builder.build_model(env)
        num_primitives = len(builder.primitives)
        
        print(f"\nAuto-optimizing for {num_primitives} primitives, {days} days, {target_memory_mb}MB memory")
        
        # Get recommendation
        config = PerformanceConfig().recommend_settings(
            num_primitives=num_primitives,
            simulation_days=days,
            available_memory_mb=target_memory_mb
        )
        
        # Estimate memory usage
        estimates = config.estimate_memory_usage(num_primitives, days)
        
        print(f"\nRecommended configuration: {config.name}")
        print(f"  Estimated memory: {estimates['total_mb']:.1f}MB")
        print(f"  Buffer size: {config.observable_buffer_size}")
        print(f"  Sampling rate: 1/{config.sampling_rate}")
        print(f"  Mode: {config.simulation_mode.value}")
        
        return config
    
    def monitor_memory_pressure(self) -> bool:
        """Check if system is under memory pressure.
        
        Returns:
            True if memory usage exceeds threshold
        """
        if not tracemalloc.is_tracing():
            return False
            
        current, peak = tracemalloc.get_traced_memory()
        memory_mb = current / (1024 * 1024)
        
        return memory_mb > self.perf_config.max_memory_mb * 0.9  # 90% threshold
    
    def adaptive_mode_switch(self) -> None:
        """Adaptively switch modes based on memory pressure."""
        if self.monitor_memory_pressure():
            print("  ⚠️  Memory pressure detected, switching to FAST mode")
            
            # Switch to more aggressive settings
            self.perf_config.simulation_mode = SimulationMode.FAST
            self.perf_config.sampling_rate = min(1000, self.perf_config.sampling_rate * 10)
            self.perf_config.batch_size = min(10000, self.perf_config.batch_size * 2)
            self.perf_config.observable_buffer_size = max(10, self.perf_config.observable_buffer_size // 2)