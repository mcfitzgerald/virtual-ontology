# MES Simulation Execution Plan

## Overview
This document provides a comprehensive plan for running a full Manufacturing Execution System (MES) simulation using the twin_model framework with integrated scheduling and cost optimization.

## Current System State

### Completed Components
1. **Scheduling System**
   - `BaseScheduler` - Abstract scheduler interface
   - `SequentialScheduler` - FIFO scheduling algorithm
   - `CampaignOptimizer` - Campaign-based grouping for changeover minimization
   - `SchedulerSimulationBridge` - Integration between schedulers and SimPy

2. **Product Management**
   - `ProductManifest` - Comprehensive product specifications (850+ lines)
   - `ProductionCostCalculator` - Multi-factor cost calculation
   - Line efficiency mapping with format conversion ("Line1" ↔ "1")

3. **Configuration Files**
   - `config/product_manifest.yaml` - Full product specifications
   - `config/scheduler_config.yaml` - Scheduling parameters
   - `config/production_orders.yaml` - Order generation patterns
   - `config/mes_parameters.yaml` - MES collection settings

4. **MES Data Collection**
   - `MESDataCollector` - 5-minute interval data collection
   - 18 MES fields including OEE components
   - Target metrics: 46% OEE, 33% downtime, 6.79% scrap

## Simulation Execution Plan

### Phase 1: Environment Setup

#### 1.1 Create Main Simulation Script
Create `run_mes_simulation.py` in project root:

```python
"""Run full MES simulation with scheduling and data collection."""

import simpy
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging

from twin_model.scheduling.scheduler_integration import SchedulerSimulationBridge
from twin_model.scheduling.product_manifest import ProductManifest
from twin_model.scheduling.base_scheduler import SchedulerConfig, SchedulingConstraints
from twin_model.transduction.mes_collector import MESDataCollector
from twin_model.primitives.source_flow import SourceFlow
from twin_model.primitives.processor_flow import ProcessorFlow
from twin_model.primitives.sink_flow import SinkFlow

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

#### 1.2 Load Configurations
```python
def load_configurations():
    """Load all configuration files."""
    # Load product manifest
    manifest = ProductManifest()
    manifest.load_from_yaml(Path("config/product_manifest.yaml"))
    
    # Load scheduler config
    import yaml
    with open("config/scheduler_config.yaml", 'r') as f:
        scheduler_yaml = yaml.safe_load(f)
    
    config = SchedulerConfig(
        min_order_duration_hours=scheduler_yaml['scheduler_config']['min_order_duration_hours'],
        max_order_duration_hours=scheduler_yaml['scheduler_config']['max_order_duration_hours'],
        efficiency_factor=scheduler_yaml['scheduler_config']['efficiency_factor']
    )
    
    # Load constraints
    constraints = SchedulingConstraints(
        product_line_compatibility=scheduler_yaml['scheduling_constraints']['product_line_compatibility'],
        horizon_hours=scheduler_yaml['scheduling_constraints']['horizon_hours']
    )
    
    return manifest, config, constraints
```

### Phase 2: Production Line Setup

#### 2.1 Create Production Lines
```python
def create_production_lines(env, manifest):
    """Create three production lines with equipment."""
    lines = {}
    
    for line_id in ['Line1', 'Line2', 'Line3']:
        # Create source (order input)
        source = SourceFlow(
            env=env,
            name=f"{line_id}_Source",
            initial_level=0,
            capacity=100000
        )
        
        # Create processor (production)
        processor = ProcessorFlow(
            env=env,
            name=f"{line_id}_Processor",
            processing_time=lambda: 1.0,  # Will be overridden by product rates
            input_container=source.output_container,
            capacity=1000
        )
        
        # Create sink (finished goods)
        sink = SinkFlow(
            env=env,
            name=f"{line_id}_Sink",
            input_container=processor.output_container
        )
        
        lines[line_id] = {
            'source': source,
            'processor': processor,
            'sink': sink
        }
    
    return lines
```

#### 2.2 Configure MES Collection
```python
def setup_mes_collection(env, lines):
    """Setup MES data collection."""
    # Load MES parameters
    with open("config/mes_parameters.yaml", 'r') as f:
        mes_config = yaml.safe_load(f)
    
    # Create MES collector
    collector = MESDataCollector(
        env=env,
        collection_interval=mes_config['collection']['interval_minutes'] * 60,  # Convert to seconds
        output_dir=Path("output/mes_data")
    )
    
    # Register equipment for monitoring
    for line_id, equipment in lines.items():
        collector.register_equipment(
            equipment_id=line_id,
            equipment={
                'processor': equipment['processor'],
                'oee_target': mes_config['oee_thresholds']['target_oee']
            }
        )
    
    return collector
```

### Phase 3: Order Generation and Scheduling

#### 3.1 Generate Production Orders
```python
def generate_production_schedule(env, manifest, config, constraints, duration_days=14):
    """Generate and schedule production orders for simulation period."""
    
    # Create scheduler bridge (use campaign optimizer for better performance)
    scheduler_bridge = SchedulerSimulationBridge(
        env=env,
        scheduler_type="campaign",
        config=config,
        constraints=constraints,
        product_manifest=manifest
    )
    
    # Calculate number of orders needed
    # Assume average order duration of 4 hours
    orders_per_day = 24 / 4 * 3  # 3 lines
    total_orders = int(orders_per_day * duration_days)
    
    # Generate orders with realistic distribution
    orders = scheduler_bridge.generate_orders(
        num_orders=total_orders,
        horizon_hours=duration_days * 24
    )
    
    # Schedule orders with optimization
    schedule = scheduler_bridge.schedule_orders(
        orders=orders,
        horizon_hours=duration_days * 24,
        optimize=True
    )
    
    return scheduler_bridge, schedule
```

### Phase 4: Simulation Execution

#### 4.1 Main Simulation Process
```python
def run_simulation_process(env, scheduler_bridge, lines, collector, duration_days=14):
    """Main simulation process."""
    
    # Start MES data collection
    env.process(collector.collect_data())
    
    # Dispatch scheduled orders to lines
    for line_id, line_equipment in lines.items():
        if line_id in scheduler_bridge.line_sources:
            # Connect scheduler to line source
            scheduler_bridge.register_line_source(line_id, line_equipment['source'])
    
    # Dispatch the schedule
    scheduler_bridge.dispatch_schedule(scheduler_bridge.line_schedules)
    
    # Run scheduled production
    env.process(scheduler_bridge.run_scheduled_production(duration_days * 24))
    
    # Add disruptions for realism
    env.process(simulate_disruptions(env, scheduler_bridge, duration_days))
    
    # Run simulation
    simulation_hours = duration_days * 24
    simulation_minutes = simulation_hours * 60
    env.run(until=simulation_minutes)
```

#### 4.2 Disruption Simulation
```python
def simulate_disruptions(env, scheduler_bridge, duration_days):
    """Simulate random disruptions."""
    import random
    
    disruption_types = [
        ('equipment_failure', 60, ['Line1', 'Line2', 'Line3']),
        ('material_shortage', 120, ['Line1', 'Line2']),
        ('quality_issue', 30, ['Line2', 'Line3'])
    ]
    
    # Schedule 2-3 disruptions per week
    disruptions_per_week = random.randint(2, 3)
    total_disruptions = disruptions_per_week * (duration_days // 7)
    
    for i in range(total_disruptions):
        # Random time during simulation
        disruption_time = random.uniform(24, duration_days * 24 - 24) * 60
        
        # Wait until disruption time
        yield env.timeout(disruption_time - env.now)
        
        # Select random disruption
        disruption_type, duration, affected_lines = random.choice(disruption_types)
        affected = random.sample(affected_lines, k=random.randint(1, len(affected_lines)))
        
        # Handle disruption
        scheduler_bridge.handle_disruption(
            disruption_type=disruption_type,
            affected_lines=affected,
            duration_minutes=duration
        )
        
        logger.info(f"Disruption {disruption_type} at {env.now/60:.1f} hours affecting {affected}")
```

### Phase 5: Results Analysis

#### 5.1 Calculate KPIs
```python
def analyze_results(collector, scheduler_bridge, target_file="data/target/ORIGINAL_2WEEK.csv"):
    """Analyze simulation results against targets."""
    
    # Get collected MES data
    mes_data = collector.get_dataframe()
    
    # Calculate actual metrics
    actual_oee = mes_data['OEE'].mean()
    actual_availability = mes_data['Availability'].mean()
    actual_performance = mes_data['Performance'].mean()
    actual_quality = mes_data['Quality'].mean()
    actual_downtime = (mes_data['State'] == 'Down').mean() * 100
    actual_scrap = mes_data['Bad_Count'].sum() / mes_data['Good_Count'].sum() * 100
    
    # Load target data
    target_df = pd.read_csv(target_file)
    target_oee = target_df['OEE'].mean()
    target_downtime = (target_df['State'] == 'Down').mean() * 100
    target_scrap = target_df['Bad_Count'].sum() / target_df['Good_Count'].sum() * 100
    
    # Compare results
    results = {
        'Metric': ['OEE', 'Availability', 'Performance', 'Quality', 'Downtime %', 'Scrap %'],
        'Target': [target_oee, None, None, None, target_downtime, target_scrap],
        'Actual': [actual_oee, actual_availability, actual_performance, actual_quality, actual_downtime, actual_scrap],
        'Difference': [actual_oee - target_oee, None, None, None, actual_downtime - target_downtime, actual_scrap - target_scrap]
    }
    
    results_df = pd.DataFrame(results)
    print("\n=== SIMULATION RESULTS ===")
    print(results_df.to_string(index=False))
    
    # Get scheduling metrics
    schedule_metrics = scheduler_bridge.get_schedule_metrics()
    print("\n=== SCHEDULING METRICS ===")
    for key, value in schedule_metrics.items():
        print(f"{key}: {value}")
    
    return results_df, mes_data
```

#### 5.2 Export Results
```python
def export_results(mes_data, schedule, results_df):
    """Export simulation results."""
    # Create output directory
    output_dir = Path("output/simulation_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export MES data
    mes_data.to_csv(output_dir / "mes_data.csv", index=False)
    
    # Export schedule
    schedule_df = []
    for line_id, orders in schedule.items():
        for order in orders:
            schedule_df.append({
                'line_id': line_id,
                'order_id': order.order_id,
                'product_id': order.product_id,
                'start_time': order.scheduled_start,
                'duration': order.scheduled_duration,
                'volume': order.target_volume
            })
    pd.DataFrame(schedule_df).to_csv(output_dir / "production_schedule.csv", index=False)
    
    # Export KPI comparison
    results_df.to_csv(output_dir / "kpi_comparison.csv", index=False)
    
    print(f"\nResults exported to {output_dir}")
```

### Phase 6: Main Execution

```python
def main():
    """Main simulation execution."""
    print("=" * 60)
    print("MES SIMULATION WITH INTEGRATED SCHEDULING")
    print("=" * 60)
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Load configurations
    manifest, config, constraints = load_configurations()
    
    # Create production lines
    lines = create_production_lines(env, manifest)
    
    # Setup MES collection
    collector = setup_mes_collection(env, lines)
    
    # Generate and schedule orders
    scheduler_bridge, schedule = generate_production_schedule(
        env, manifest, config, constraints, duration_days=14
    )
    
    # Run simulation
    run_simulation_process(env, scheduler_bridge, lines, collector, duration_days=14)
    
    # Analyze results
    results_df, mes_data = analyze_results(collector, scheduler_bridge)
    
    # Export results
    export_results(mes_data, schedule, results_df)
    
    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

## Execution Instructions

### Step 1: Verify Prerequisites
```bash
# Check all required files exist
ls config/*.yaml
ls twin_model/scheduling/*.py
ls twin_model/transduction/mes_collector.py
```

### Step 2: Run Tests First
```bash
# Test product manifest
~/.local/bin/poetry run python tests/test_product_manifest_integration.py

# Test scheduler integration
~/.local/bin/poetry run python tests/test_scheduler_integration.py
```

### Step 3: Execute Simulation
```bash
# Run the full simulation
~/.local/bin/poetry run python run_mes_simulation.py
```

### Step 4: Verify Output
```bash
# Check output files
ls output/simulation_results/
cat output/simulation_results/kpi_comparison.csv
```

## Expected Outcomes

### Success Criteria
1. **OEE within 5% of target (46%)**
   - Actual OEE should be between 41-51%

2. **Downtime realistic (target 33%)**
   - Should see planned and unplanned downtime events

3. **Scrap rate appropriate (target 6.79%)**
   - Quality losses should be realistic

4. **Schedule optimization working**
   - Campaign optimizer should show fewer changeovers than sequential
   - Cost savings should be measurable

### Troubleshooting

#### Issue: Import errors
- Ensure poetry environment is activated
- Check PYTHONPATH includes project root

#### Issue: No MES data collected
- Verify MESDataCollector is properly initialized
- Check collection interval is appropriate (5 minutes)

#### Issue: Orders not being produced
- Verify scheduler_bridge.dispatch_schedule() is called
- Check line sources are properly registered

#### Issue: Unrealistic metrics
- Adjust disruption frequency
- Tune product rates in product_manifest.yaml
- Modify efficiency factors

## Next Steps After Successful Run

1. **Compare Schedulers**
   - Run with sequential scheduler
   - Run with campaign optimizer
   - Compare costs and OEE

2. **Optimization Experiments**
   - Vary campaign lengths
   - Test different changeover matrices
   - Measure impact of disruptions

3. **Visualization**
   - Create Gantt chart of schedule
   - Plot OEE trends over time
   - Generate cost breakdown charts

## Key Files Reference

- **Scheduler Integration**: `twin_model/scheduling/scheduler_integration.py`
- **Product Manifest**: `config/product_manifest.yaml`
- **MES Collector**: `twin_model/transduction/mes_collector.py`
- **Cost Calculator**: `twin_model/scheduling/cost_calculator.py`
- **Target Data**: `data/target/ORIGINAL_2WEEK.csv`

## Notes for Fresh Session

When starting fresh:
1. This plan assumes all components from previous sessions are implemented
2. The ProductManifest class handles line ID conversion ("Line1" ↔ "1")
3. OrderStatus enum is in base_scheduler.py
4. ProductionOrder validation requires scheduled_duration > 0
5. The system uses minutes as the base time unit in SimPy