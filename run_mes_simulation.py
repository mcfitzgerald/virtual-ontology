"""Run full MES simulation with scheduling and data collection."""

import simpy
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import yaml
import random
from typing import Dict, List, Any, Tuple

from twin_model.scheduling.scheduler_integration import SchedulerSimulationBridge
from twin_model.scheduling.product_manifest import ProductManifest
from twin_model.scheduling.base_scheduler import SchedulerConfig, SchedulingConstraints
from twin_model.scheduling.production_scheduler import ProductionOrder
from twin_model.transduction.mes_collector import MESDataCollector
from twin_model.primitives.source_flow import SourceFlow
from twin_model.primitives.equipment_flow import EquipmentFlow
from twin_model.primitives.sink_flow import SinkFlow

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_configurations() -> Tuple[ProductManifest, SchedulerConfig, SchedulingConstraints]:
    """Load all configuration files."""
    logger.info("Loading configurations...")
    
    # Load product manifest
    manifest = ProductManifest()
    manifest.load_from_yaml(Path("config/product_manifest.yaml"))
    logger.info(f"Loaded {len(manifest.products)} products from manifest")
    
    # Load scheduler config
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
    
    logger.info("Configurations loaded successfully")
    return manifest, config, constraints


def create_production_lines(env: simpy.Environment, manifest: ProductManifest) -> Dict[str, Dict[str, Any]]:
    """Create three production lines with equipment."""
    logger.info("Creating production lines...")
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
        processor = EquipmentFlow(
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
        logger.info(f"Created production line: {line_id}")
    
    return lines


def setup_mes_collection(env: simpy.Environment, lines: Dict[str, Dict[str, Any]]) -> MESDataCollector:
    """Setup MES data collection."""
    logger.info("Setting up MES data collection...")
    
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
        logger.info(f"Registered {line_id} for MES monitoring")
    
    return collector


def generate_production_schedule(
    env: simpy.Environment,
    manifest: ProductManifest,
    config: SchedulerConfig,
    constraints: SchedulingConstraints,
    duration_days: int = 14
) -> Tuple[SchedulerSimulationBridge, Dict[str, List[ProductionOrder]]]:
    """Generate and schedule production orders for simulation period."""
    logger.info(f"Generating production schedule for {duration_days} days...")
    
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
    logger.info(f"Generating {total_orders} orders...")
    
    # Generate orders with realistic distribution
    orders = scheduler_bridge.generate_orders(
        num_orders=total_orders,
        horizon_hours=duration_days * 24
    )
    
    # Schedule orders with optimization
    logger.info("Scheduling orders with campaign optimization...")
    schedule = scheduler_bridge.schedule_orders(
        orders=orders,
        horizon_hours=duration_days * 24,
        optimize=True
    )
    
    # Log schedule summary
    total_scheduled = sum(len(line_orders) for line_orders in schedule.values())
    logger.info(f"Scheduled {total_scheduled} orders across {len(schedule)} lines")
    
    return scheduler_bridge, schedule


def simulate_disruptions(
    env: simpy.Environment,
    scheduler_bridge: SchedulerSimulationBridge,
    lines: Dict[str, Dict[str, Any]],
    duration_days: int
):
    """Simulate random disruptions."""
    logger.info("Starting disruption simulation process...")
    
    disruption_types = [
        ('equipment_failure', 60, ['Line1', 'Line2', 'Line3']),
        ('material_shortage', 120, ['Line1', 'Line2']),
        ('quality_issue', 30, ['Line2', 'Line3'])
    ]
    
    # Schedule 2-3 disruptions per week
    disruptions_per_week = random.randint(2, 3)
    total_disruptions = disruptions_per_week * (duration_days // 7)
    
    # Generate disruption times
    disruption_times = sorted([
        random.uniform(24 * 60, (duration_days * 24 - 24) * 60)
        for _ in range(total_disruptions)
    ])
    
    for disruption_time in disruption_times:
        # Wait until disruption time
        yield env.timeout(disruption_time - env.now)
        
        # Select random disruption
        disruption_type, duration, affected_lines = random.choice(disruption_types)
        affected = random.sample(affected_lines, k=random.randint(1, len(affected_lines)))
        
        logger.warning(
            f"Disruption {disruption_type} at {env.now/60:.1f} hours "
            f"affecting {affected} for {duration} minutes"
        )
        
        # Simulate disruption by stopping affected lines
        for line_id in affected:
            if line_id in lines:
                # Stop the processor temporarily
                processor = lines[line_id]['processor']
                # Mark processor as down (this would need to be implemented in ProcessorFlow)
                # For now, we just log it
                logger.info(f"Line {line_id} affected by {disruption_type}")


def run_simulation_process(
    env: simpy.Environment,
    scheduler_bridge: SchedulerSimulationBridge,
    lines: Dict[str, Dict[str, Any]],
    collector: MESDataCollector,
    duration_days: int = 14
):
    """Main simulation process."""
    logger.info("Starting main simulation process...")
    
    # Start MES data collection
    env.process(collector.collect_data())
    
    # Register line sources with scheduler
    for line_id, line_equipment in lines.items():
        scheduler_bridge.register_line_source(line_id, line_equipment['source'])
    
    # Dispatch the schedule
    scheduler_bridge.dispatch_schedule(scheduler_bridge.line_schedules)
    
    # Run scheduled production
    env.process(scheduler_bridge.run_scheduled_production(duration_days * 24))
    
    # Add disruptions for realism
    env.process(simulate_disruptions(env, scheduler_bridge, lines, duration_days))
    
    # Run simulation
    simulation_hours = duration_days * 24
    simulation_minutes = simulation_hours * 60
    logger.info(f"Running simulation for {simulation_hours} hours ({simulation_minutes} minutes)...")
    env.run(until=simulation_minutes)
    logger.info("Simulation completed")


def analyze_results(
    collector: MESDataCollector,
    scheduler_bridge: SchedulerSimulationBridge,
    target_file: str = "data/target/ORIGINAL_2WEEK.csv"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Analyze simulation results against targets."""
    logger.info("Analyzing simulation results...")
    
    # Get collected MES data
    mes_data = collector.get_dataframe()
    
    if mes_data.empty:
        logger.warning("No MES data collected!")
        return pd.DataFrame(), pd.DataFrame()
    
    # Calculate actual metrics
    actual_oee = mes_data['OEE'].mean() if 'OEE' in mes_data else 0
    actual_availability = mes_data['Availability'].mean() if 'Availability' in mes_data else 0
    actual_performance = mes_data['Performance'].mean() if 'Performance' in mes_data else 0
    actual_quality = mes_data['Quality'].mean() if 'Quality' in mes_data else 0
    
    # Calculate downtime and scrap
    if 'State' in mes_data:
        actual_downtime = (mes_data['State'] == 'Down').mean() * 100
    else:
        actual_downtime = 0
    
    if 'Bad_Count' in mes_data and 'Good_Count' in mes_data:
        total_good = mes_data['Good_Count'].sum()
        total_bad = mes_data['Bad_Count'].sum()
        if total_good > 0:
            actual_scrap = (total_bad / total_good) * 100
        else:
            actual_scrap = 0
    else:
        actual_scrap = 0
    
    # Try to load target data
    target_oee = 46.0  # Default target
    target_downtime = 33.0
    target_scrap = 6.79
    
    if Path(target_file).exists():
        try:
            target_df = pd.read_csv(target_file)
            if not target_df.empty:
                target_oee = target_df['OEE'].mean() if 'OEE' in target_df else target_oee
                if 'State' in target_df:
                    target_downtime = (target_df['State'] == 'Down').mean() * 100
                if 'Bad_Count' in target_df and 'Good_Count' in target_df:
                    total_good = target_df['Good_Count'].sum()
                    total_bad = target_df['Bad_Count'].sum()
                    if total_good > 0:
                        target_scrap = (total_bad / total_good) * 100
        except Exception as e:
            logger.warning(f"Could not load target data: {e}")
    
    # Compare results
    results = {
        'Metric': ['OEE', 'Availability', 'Performance', 'Quality', 'Downtime %', 'Scrap %'],
        'Target': [target_oee, 75.0, 85.0, 95.0, target_downtime, target_scrap],
        'Actual': [actual_oee, actual_availability, actual_performance, actual_quality, actual_downtime, actual_scrap],
        'Difference': [
            actual_oee - target_oee,
            actual_availability - 75.0,
            actual_performance - 85.0,
            actual_quality - 95.0,
            actual_downtime - target_downtime,
            actual_scrap - target_scrap
        ]
    }
    
    results_df = pd.DataFrame(results)
    print("\n" + "=" * 60)
    print("SIMULATION RESULTS")
    print("=" * 60)
    print(results_df.to_string(index=False))
    
    # Get scheduling metrics
    schedule_metrics = scheduler_bridge.get_schedule_metrics()
    print("\n" + "=" * 60)
    print("SCHEDULING METRICS")
    print("=" * 60)
    for key, value in schedule_metrics.items():
        print(f"{key}: {value}")
    
    return results_df, mes_data


def export_results(
    mes_data: pd.DataFrame,
    schedule: Dict[str, List[ProductionOrder]],
    results_df: pd.DataFrame
):
    """Export simulation results."""
    logger.info("Exporting results...")
    
    # Create output directory
    output_dir = Path("output/simulation_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export MES data
    if not mes_data.empty:
        mes_data.to_csv(output_dir / "mes_data.csv", index=False)
        logger.info(f"Exported MES data: {len(mes_data)} records")
    
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
    
    if schedule_df:
        pd.DataFrame(schedule_df).to_csv(output_dir / "production_schedule.csv", index=False)
        logger.info(f"Exported production schedule: {len(schedule_df)} orders")
    
    # Export KPI comparison
    results_df.to_csv(output_dir / "kpi_comparison.csv", index=False)
    logger.info("Exported KPI comparison")
    
    print(f"\nResults exported to {output_dir}")


def main():
    """Main simulation execution."""
    print("=" * 60)
    print("MES SIMULATION WITH INTEGRATED SCHEDULING")
    print("=" * 60)
    print()
    
    try:
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
        
        # Store schedule for the bridge
        scheduler_bridge.line_schedules = schedule
        
        # Run simulation
        run_simulation_process(env, scheduler_bridge, lines, collector, duration_days=14)
        
        # Analyze results
        results_df, mes_data = analyze_results(collector, scheduler_bridge)
        
        # Export results
        export_results(mes_data, schedule, results_df)
        
        print("\n" + "=" * 60)
        print("SIMULATION COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()