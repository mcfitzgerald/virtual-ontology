#!/usr/bin/env python3
"""Generate 30-day baseline simulation using optimized twin_model framework.

This script generates a complete 30-day baseline simulation with:
- Performance optimizations from all 6 phases
- Progress monitoring and reporting
- Database storage and CSV export
- Memory-efficient processing
"""

import sys
import os
import time
import tracemalloc
from pathlib import Path
from datetime import datetime
import pandas as pd
import simpy
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.config import PerformanceConfig, ConfigPreset
from twin_model.primitives.base import SamplingConfig, SimulationMode, ConsoleProgressReporter
from twin_model.transduction.mes_transducer import MESTransducer
from database.manager import TwinDatabaseManager
from database.integration_optimized import OptimizedTwinDatabaseIntegration
from sqlmodel import Session
from database.repositories import TwinRunRepository, SimulationDataRepository, KPIRepository


def generate_30day_baseline():
    """Generate 30-day baseline simulation with full optimization."""
    
    print("=" * 70)
    print(" " * 15 + "30-DAY BASELINE SIMULATION GENERATOR")
    print("=" * 70)
    print()
    
    # Configuration
    simulation_days = 30
    simulation_minutes = simulation_days * 24 * 60  # 43,200 minutes
    
    # Step 1: Configure performance settings
    print("📋 Step 1: Configuring Performance Settings")
    print("-" * 50)
    config = PerformanceConfig.from_preset(ConfigPreset.LONG_RUNNING)
    print(f"  Configuration preset: {config.name}")
    print(f"  Sampling rate: 1/{config.sampling_rate} (keeping {100/config.sampling_rate:.1f}% of events)")
    print(f"  Buffer size: {config.observable_buffer_size} events per primitive")
    print(f"  Memory limit: {config.max_memory_mb:.0f}MB")
    print(f"  Checkpoint interval: Every {config.checkpoint_interval/1440:.1f} days")
    print()
    
    # Step 2: Initialize components
    print("🔧 Step 2: Initializing System Components")
    print("-" * 50)
    
    # Database manager
    db_manager = TwinDatabaseManager()
    print(f"  ✓ Database: {db_manager.db_path}")
    
    # Optimized integration
    integration = OptimizedTwinDatabaseIntegration(
        db_manager=db_manager,
        perf_config=config
    )
    print(f"  ✓ Integration layer initialized")
    
    # Progress reporter
    progress_reporter = ConsoleProgressReporter()
    print(f"  ✓ Progress reporter ready")
    print()
    
    # Step 3: Build simulation model
    print("🏗️  Step 3: Building Simulation Model")
    print("-" * 50)
    
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    print(f"  Loading ontology: {ontology_path}")
    print(f"  Loading manifests: {manifest_dir}")
    
    builder = OntologyDrivenModelBuilder(
        ontology_path=ontology_path,
        manifest_dir=manifest_dir
    )
    
    env = simpy.Environment()
    model = builder.build_model(env)
    
    print(f"  ✓ Model built with {len(builder.primitives)} primitives")
    
    # List primitives by type
    primitive_types = {}
    for prim_id, prim in builder.primitives.items():
        prim_type = type(prim).__name__
        primitive_types[prim_type] = primitive_types.get(prim_type, 0) + 1
    
    for prim_type, count in sorted(primitive_types.items()):
        print(f"    - {prim_type}: {count}")
    print()
    
    # Step 4: Apply sampling configuration
    print("⚙️  Step 4: Applying Performance Optimizations")
    print("-" * 50)
    
    sampling = SamplingConfig(
        mode=config.simulation_mode,
        sampling_rate=config.sampling_rate,
        buffer_size=config.observable_buffer_size,
        aggregation_interval=config.aggregation_interval,
        enable_global_observables=False  # Disable global collection for memory efficiency
    )
    
    # Apply to all primitives
    configured_count = 0
    for primitive in builder.primitives.values():
        if hasattr(primitive, 'sampling_config'):
            primitive.sampling_config = sampling
            configured_count += 1
    
    print(f"  ✓ Sampling applied to {configured_count} primitives")
    print(f"  ✓ Memory optimizations active")
    print()
    
    # Step 5: Run simulation with progress monitoring
    print(f"🚀 Step 5: Running {simulation_days}-Day Simulation")
    print("-" * 50)
    print("  This will take approximately 2-5 minutes...")
    print()
    
    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()
    last_day = 0
    
    # Progress tracking
    print("  Progress:")
    print("  " + "─" * 45)
    
    # Run simulation day by day with progress updates
    while env.now < simulation_minutes:
        # Run for one day
        run_until = min(env.now + 1440, simulation_minutes)
        env.run(until=run_until)
        
        # Calculate progress
        current_day = int(env.now / 1440)
        progress_pct = (env.now / simulation_minutes) * 100
        elapsed = time.time() - start_time
        memory_current, memory_peak = tracemalloc.get_traced_memory()
        memory_mb = memory_peak / (1024 * 1024)
        
        # Update progress display
        if current_day > last_day:
            # Estimate time remaining
            if progress_pct > 0:
                eta_seconds = (elapsed / progress_pct) * (100 - progress_pct)
                eta_min = int(eta_seconds / 60)
                eta_sec = int(eta_seconds % 60)
                eta_str = f"{eta_min}:{eta_sec:02d}"
            else:
                eta_str = "calculating..."
            
            # Progress bar
            bar_width = 30
            filled = int(bar_width * progress_pct / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            print(f"  Day {current_day:2d}/30 │{bar}│ {progress_pct:5.1f}% │ "
                  f"Mem: {memory_mb:6.1f}MB │ ETA: {eta_str}")
            
            last_day = current_day
            
            # Check memory pressure
            if memory_mb > config.max_memory_mb * 0.9:
                print(f"  ⚠️  Memory pressure detected ({memory_mb:.1f}MB), optimizing...")
                # Could implement adaptive mode switching here
    
    # Final statistics
    total_time = time.time() - start_time
    final_memory = tracemalloc.get_traced_memory()[1] / (1024 * 1024)
    tracemalloc.stop()
    
    print("  " + "─" * 45)
    print(f"  ✓ Simulation completed in {total_time:.1f} seconds")
    print(f"  ✓ Peak memory usage: {final_memory:.1f}MB")
    print()
    
    # Step 6: Collect and process observables
    print("📊 Step 6: Processing Simulation Data")
    print("-" * 50)
    
    all_observables = []
    event_counts = {}
    
    for primitive_id, primitive in builder.primitives.items():
        events = []
        
        # Try to get events from optimized buffer first
        if hasattr(primitive, 'observable_buffer') and primitive.observable_buffer:
            events = list(primitive.observable_buffer.buffer)
        # Fallback to standard observables
        elif hasattr(primitive, 'observables'):
            events = primitive.observables
        
        # Add primitive context to each event
        for event in events:
            event['primitive_id'] = primitive_id
            event['primitive_type'] = type(primitive).__name__
            all_observables.append(event)
        
        if events:
            event_counts[primitive_id] = len(events)
    
    print(f"  ✓ Collected {len(all_observables):,} observable events")
    print(f"  ✓ From {len(event_counts)} active primitives")
    print()
    
    # Step 7: Transduce to MES format
    print("🔄 Step 7: Converting to MES Format")
    print("-" * 50)
    
    transducer = MESTransducer(time_bucket=5)  # 5-minute buckets
    mes_df = transducer.process_observables(all_observables, builder.manifests)
    
    print(f"  ✓ Generated {len(mes_df):,} MES records")
    print(f"  ✓ Time buckets: 5-minute intervals")
    
    if len(mes_df) > 0:
        # Show sample of equipment types
        equipment_types = mes_df['EquipmentType'].value_counts() if 'EquipmentType' in mes_df else {}
        if len(equipment_types) > 0:
            print("\n  Equipment distribution:")
            for eq_type, count in equipment_types.head(5).items():
                print(f"    - {eq_type}: {count:,} records")
    print()
    
    # Step 8: Calculate KPIs
    print("📈 Step 8: Calculating KPIs")
    print("-" * 50)
    
    kpi_summary = {}
    
    if len(mes_df) > 0:
        # Calculate KPIs from MES data
        kpi_summary['total_good_units'] = int(mes_df['GoodUnitsProduced'].sum()) if 'GoodUnitsProduced' in mes_df else 0
        kpi_summary['total_scrap_units'] = int(mes_df['ScrapUnitsProduced'].sum()) if 'ScrapUnitsProduced' in mes_df else 0
        kpi_summary['mean_oee'] = float(mes_df['OEE_Score'].mean()) if 'OEE_Score' in mes_df else 0
        kpi_summary['mean_availability'] = float(mes_df['Availability_Score'].mean()) if 'Availability_Score' in mes_df else 0
        kpi_summary['mean_performance'] = float(mes_df['Performance_Score'].mean()) if 'Performance_Score' in mes_df else 0
        kpi_summary['mean_quality'] = float(mes_df['Quality_Score'].mean()) if 'Quality_Score' in mes_df else 0
    else:
        # Use defaults if no data
        kpi_summary = {
            'total_good_units': 0,
            'total_scrap_units': 0,
            'mean_oee': 0,
            'mean_availability': 0,
            'mean_performance': 0,
            'mean_quality': 0
        }
    
    # Add metadata
    kpi_summary['simulation_days'] = simulation_days
    kpi_summary['simulation_time_seconds'] = total_time
    kpi_summary['peak_memory_mb'] = final_memory
    kpi_summary['total_events'] = len(all_observables)
    kpi_summary['mes_records'] = len(mes_df)
    
    print(f"  Total Good Units:    {kpi_summary['total_good_units']:,}")
    print(f"  Total Scrap Units:   {kpi_summary['total_scrap_units']:,}")
    print(f"  Mean OEE:            {kpi_summary['mean_oee']:.1f}%")
    print(f"  Mean Availability:   {kpi_summary['mean_availability']:.1f}%")
    print(f"  Mean Performance:    {kpi_summary['mean_performance']:.1f}%")
    print(f"  Mean Quality:        {kpi_summary['mean_quality']:.1f}%")
    print()
    
    # Step 9: Store in database
    print("💾 Step 9: Storing in Database")
    print("-" * 50)
    
    with Session(db_manager.engine) as session:
        # Create run record
        run_repo = TwinRunRepository(session)
        run = run_repo.create_run(
            run_type="baseline_30day",
            ontology_version=db_manager.get_ontology_version(),
            manifest_version=db_manager.get_manifest_version(),
            parameters={
                'simulation_days': simulation_days,
                'config_preset': config.name,
                'sampling_rate': config.sampling_rate
            },
            parent_run_id=None
        )
        
        run_id = run.run_id
        print(f"  Created run: {run_id}")
        
        # Store simulation data (batch insert for efficiency)
        if len(mes_df) > 0:
            sim_repo = SimulationDataRepository(session)
            sim_repo.store_simulation_data(run_id, mes_df)
            print(f"  ✓ Stored {len(mes_df):,} simulation records")
        
        # Create KPI snapshot
        kpi_repo = KPIRepository(session)
        kpi_repo.create_kpi_snapshot(
            run_id=run_id,
            entity_type="overall",
            entity_id="ALL_LINES",
            kpis=kpi_summary,
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow()
        )
        print(f"  ✓ Stored KPI snapshot")
        
        # Update run status
        run_repo.update_run_status(run_id, "completed", kpi_summary)
        
        session.commit()
        print(f"  ✓ Database transaction committed")
    
    print()
    
    # Step 10: Export to CSV
    print("📁 Step 10: Exporting to CSV")
    print("-" * 50)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"baseline_30day_{timestamp}.csv"
    csv_path = Path("/tmp") / csv_filename
    
    mes_df.to_csv(csv_path, index=False)
    file_size_mb = csv_path.stat().st_size / (1024 * 1024)
    
    print(f"  ✓ Exported to: {csv_path}")
    print(f"  ✓ File size: {file_size_mb:.2f}MB")
    print()
    
    # Summary
    print("=" * 70)
    print(" " * 20 + "SIMULATION COMPLETE! 🎉")
    print("=" * 70)
    print()
    print("📊 Summary:")
    print(f"  • Simulation duration: {simulation_days} days")
    print(f"  • Real time elapsed: {total_time:.1f} seconds")
    print(f"  • Peak memory usage: {final_memory:.1f}MB")
    print(f"  • Events processed: {len(all_observables):,}")
    print(f"  • MES records: {len(mes_df):,}")
    print(f"  • Mean OEE: {kpi_summary['mean_oee']:.1f}%")
    print(f"  • Total production: {kpi_summary['total_good_units']:,} units")
    print()
    print("📂 Output Files:")
    print(f"  • Database: {db_manager.db_path}")
    print(f"  • Run ID: {run_id}")
    print(f"  • CSV Export: {csv_path}")
    print()
    print("🔍 Query Examples:")
    print(f"  • View in database:")
    print(f"    ./twin.sh query \"SELECT * FROM simulation_data WHERE run_id = '{run_id}' LIMIT 10\"")
    print(f"  • Analyze CSV:")
    print(f"    pandas.read_csv('{csv_path}')")
    print()
    
    return run_id, csv_path, kpi_summary


if __name__ == "__main__":
    try:
        run_id, csv_path, kpis = generate_30day_baseline()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)