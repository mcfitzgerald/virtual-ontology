#!/usr/bin/env python
"""Run MES Baseline Simulation with Sub-Optimal Configuration.

This script runs a 14-day simulation using sub-optimal configuration
to generate baseline MES data with naturally emerging 45-55% OEE.
"""

import logging
import simpy
import yaml
from datetime import datetime
from pathlib import Path
import argparse
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from twin_model.ontology_model_builder import OntologyModelBuilder
from twin_model.transduction.mes_collector import MESDataCollector
from twin_model.scheduling.schedule_generator import (
    SubOptimalScheduleGenerator,
    ScheduleGeneratorConfig
)
from twin_model.scheduling.production_scheduler import ProductionScheduler
from twin_model.control import VCurveController, VCurveMode, VCurveParameters
from twin_model.primitives import ChangeoverMatrix, AccumulationBuffer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_suboptimal_config(config_path: Path) -> dict:
    """Load sub-optimal configuration from YAML.
    
    Args:
        config_path: Path to baseline_suboptimal.yaml
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded sub-optimal configuration from {config_path}")
    logger.info(f"Target OEE: {config['metadata']['target_oee']}")
    
    return config


def apply_suboptimal_parameters(primitives: dict, config: dict):
    """Apply sub-optimal parameters to equipment.
    
    Args:
        primitives: Dictionary of simulation primitives
        config: Sub-optimal configuration
    """
    equipment_config = config.get('equipment_performance', {})
    
    # Apply performance factors
    performance_factors = equipment_config.get('performance_factors', {})
    for equip_id, factor in performance_factors.items():
        if equip_id in primitives:
            equipment = primitives[equip_id]
            if hasattr(equipment, 'processing'):
                # Store original rate
                original_rate = equipment.processing.nominal_rate
                # Apply sub-optimal factor
                equipment.processing.performance_factor = factor
                logger.info(f"Applied performance factor {factor} to {equip_id}")
    
    # Apply quality rates
    quality_rates = equipment_config.get('quality_rates', {})
    for equip_id, rate in quality_rates.items():
        if equip_id in primitives:
            equipment = primitives[equip_id]
            if hasattr(equipment, 'processing'):
                equipment.processing.quality_rate = rate
                logger.info(f"Applied quality rate {rate} to {equip_id}")
    
    # Apply failure multipliers
    failure_mult = equipment_config.get('failure_multipliers', {})
    for equip_id in primitives:
        if hasattr(primitives[equip_id], 'failures'):
            equipment = primitives[equip_id]
            # Adjust MTBF (more failures)
            equipment.failures.mtbf *= failure_mult.get('mtbf_multiplier', 1.0)
            # Adjust MTTR (longer repairs)
            equipment.failures.mttr *= failure_mult.get('mttr_multiplier', 1.0)
            # Adjust micro-stops
            equipment.failures.micro_stop_rate *= failure_mult.get('micro_stop_rate_multiplier', 1.0)
            equipment.failures.micro_stop_duration *= failure_mult.get('micro_stop_duration_multiplier', 1.0)


def setup_vcurve_controller(env: simpy.Environment, primitives: dict, config: dict) -> VCurveController:
    """Set up V-curve controller with sub-optimal parameters.
    
    Args:
        env: SimPy environment
        primitives: Dictionary of simulation primitives
        config: Sub-optimal configuration
        
    Returns:
        Configured V-curve controller
    """
    vcurve_config = config.get('vcurve_configuration', {})
    
    # Get equipment for V-curve control
    equipment = {}
    for equip_id, primitive in primitives.items():
        if hasattr(primitive, 'processing') and 'SOURCE' not in equip_id and 'SINK' not in equip_id:
            equipment[equip_id] = primitive
    
    # Create V-curve parameters with sub-optimal settings
    vcurve_params = VCurveParameters(
        mode=VCurveMode.FIXED_CONSTRAINT,
        constraint_equipment="LINE1-FIL",  # Default constraint
        upstream_differential=vcurve_config.get('upstream_differential', 0.05),  # Sub-optimal
        downstream_differential=vcurve_config.get('downstream_differential', 0.05),  # Sub-optimal
        update_interval=vcurve_config.get('update_interval', 5.0),
        max_speed_multiplier=vcurve_config.get('max_speed_multiplier', 1.1),
        min_speed_multiplier=vcurve_config.get('min_speed_multiplier', 0.95)
    )
    
    controller = VCurveController(env, equipment, vcurve_params)
    controller.start()
    
    logger.info(f"V-curve controller started with sub-optimal settings")
    logger.info(f"  Upstream differential: {vcurve_params.upstream_differential}")
    logger.info(f"  Downstream differential: {vcurve_params.downstream_differential}")
    
    return controller


def setup_changeover_matrices(primitives: dict, config: dict):
    """Set up changeover matrices with sub-optimal timing.
    
    Args:
        primitives: Dictionary of simulation primitives
        config: Sub-optimal configuration
    """
    changeover_config = config.get('changeover_strategy', {})
    time_multipliers = changeover_config.get('changeover_time_multipliers', {})
    
    # Load changeover matrix configuration
    matrix_path = Path("config/changeover_matrix.yaml")
    if matrix_path.exists():
        with open(matrix_path, 'r') as f:
            matrix_config = yaml.safe_load(f)
        
        matrices = matrix_config.get('changeover_matrices', {})
        
        # Apply to equipment with multipliers
        for equip_id, primitive in primitives.items():
            if hasattr(primitive, 'changeover_matrix'):
                # Determine equipment type
                if 'FIL' in equip_id:
                    base_matrix = matrices.get('filler_matrix', {})
                elif 'PCK' in equip_id:
                    base_matrix = matrices.get('packer_matrix', {})
                elif 'PAL' in equip_id:
                    base_matrix = matrices.get('palletizer_matrix', {})
                else:
                    continue
                
                # Apply time multipliers to make changeovers longer
                modified_matrix = {}
                for from_prod, to_prods in base_matrix.get('matrix', {}).items():
                    modified_matrix[from_prod] = {}
                    for to_prod, time in to_prods.items():
                        # Apply multiplier based on type
                        if from_prod == to_prod:
                            multiplier = 1.0
                        else:
                            # Determine if same family or different
                            multiplier = time_multipliers.get('different_family', 1.5)
                        
                        modified_matrix[from_prod][to_prod] = time * multiplier
                
                # Create changeover matrix
                primitive.changeover_matrix = ChangeoverMatrix(
                    matrix=modified_matrix,
                    default_time=base_matrix.get('default_time', 30) * 1.5,
                    min_changeover_time=base_matrix.get('min_changeover_time', 5)
                )
                
                logger.info(f"Applied changeover matrix to {equip_id}")


def run_baseline_simulation(
    duration_days: int = 14,
    output_file: str = "mes_baseline_output.csv",
    config_path: str = "config/baseline_suboptimal.yaml"
):
    """Run baseline MES simulation with sub-optimal configuration.
    
    Args:
        duration_days: Number of days to simulate
        output_file: Output CSV file path
        config_path: Path to sub-optimal configuration
    """
    logger.info("=" * 80)
    logger.info("STARTING MES BASELINE SIMULATION")
    logger.info(f"Duration: {duration_days} days")
    logger.info(f"Configuration: {config_path}")
    logger.info("=" * 80)
    
    # Load sub-optimal configuration
    suboptimal_config = load_suboptimal_config(Path(config_path))
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Build base model
    logger.info("\nBuilding simulation model...")
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=Path("ontology/filling_line_ontology.yaml"),
        manifest_path=Path("manifests/equipment_manifest.yaml"),
        config_path=Path("config/calibrated_parameters.yaml")  # Start with calibrated
    )
    
    model = builder.build_model()
    primitives = model['primitives']
    
    logger.info(f"Model built with {len(primitives)} primitives")
    
    # Apply sub-optimal parameters
    logger.info("\nApplying sub-optimal parameters...")
    apply_suboptimal_parameters(primitives, suboptimal_config)
    
    # Set up V-curve controller with poor settings
    logger.info("\nSetting up sub-optimal V-curve control...")
    vcurve_controller = setup_vcurve_controller(env, primitives, suboptimal_config)
    
    # Set up changeover matrices with penalties
    logger.info("\nSetting up changeover matrices...")
    setup_changeover_matrices(primitives, suboptimal_config)
    
    # Create MES data collector
    logger.info("\nInitializing MES data collector...")
    start_date = datetime(2025, 6, 1, 0, 0, 0)  # Match ORIGINAL_2WEEK.csv
    
    mes_collector = MESDataCollector(
        env=env,
        interval_minutes=5.0,  # 5-minute intervals
        start_date=start_date,
        product_manifest_path=Path("config/product_manifest.yaml")
    )
    
    # Register equipment with MES collector
    for equip_id, primitive in primitives.items():
        if 'SOURCE' not in equip_id and 'SINK' not in equip_id:
            # Determine equipment type
            if 'FIL' in equip_id:
                equip_type = "Filler"
            elif 'PCK' in equip_id:
                equip_type = "Packer"
            elif 'PAL' in equip_id:
                equip_type = "Palletizer"
            else:
                continue
            
            # Extract line ID
            line_id = equip_id.split('-')[0].replace('LINE', '')
            
            mes_collector.register_equipment(
                equipment_id=equip_id,
                equipment=primitive,
                equipment_type=equip_type,
                line_id=line_id
            )
    
    # Generate sub-optimal production schedule
    logger.info("\nGenerating sub-optimal production schedule...")
    schedule_config = ScheduleGeneratorConfig(
        sequence_mode="random",  # Random sequencing causes excess changeovers
        batch_sizing="fixed",  # Fixed small batches
        min_batch_hours=2.0,  # Too short
        max_batch_hours=6.0,  # Still short
        changeover_frequency_target=0.15  # Target 15% changeover time
    )
    
    schedule_generator = SubOptimalScheduleGenerator(
        config=schedule_config,
        product_manifest_path=Path("config/product_manifest.yaml"),
        random_seed=42  # For reproducibility
    )
    
    orders = schedule_generator.generate_schedule(
        duration_days=duration_days,
        start_date=start_date
    )
    
    logger.info(f"Generated {len(orders)} production orders")
    
    # Create production scheduler (skip for now - we already have orders)
    # scheduler = ProductionScheduler(env=env)
    
    # Load orders into scheduler (skipped - using orders directly)
    # for order in orders:
    #     scheduler.schedule_order(order)
    
    # Process to execute orders
    def execute_orders():
        """Execute production orders and update MES collector."""
        for order in orders:
            # Wait until scheduled start
            yield env.timeout(max(0, order.scheduled_start - env.now))
            
            # For now, just log that we would process this order
            # Sources will run in continuous mode to generate material
            source_id = f"LINE{order.line_id}-SOURCE"
            if source_id in primitives:
                logger.info(f"Order {order.order_id} scheduled for {source_id}: {order.target_volume} units of {order.product_id}")
                # Note: Sources remain in continuous mode for now to ensure material flow
            else:
                logger.warning(f"Source {source_id} not found for order {order.order_id}")
            
            # Update MES collector with current order
            line_equipment = [
                eid for eid in primitives.keys()
                if f"LINE{order.line_id}" in eid and 'SOURCE' not in eid and 'SINK' not in eid
            ]
            
            for equip_id in line_equipment:
                mes_collector.update_production_order(
                    equipment_id=equip_id,
                    order_id=order.order_id,
                    product_id=order.product_id
                )
                
                # Request product change if equipment supports it
                if hasattr(primitives[equip_id], 'request_product_change'):
                    primitives[equip_id].request_product_change(order.product_id)
            
            logger.info(f"Started {order.order_id}: {order.product_id} on LINE{order.line_id}")
    
    # Start processes
    env.process(execute_orders())
    env.process(mes_collector.collect_data())
    
    # Run simulation
    simulation_minutes = duration_days * 24 * 60
    logger.info(f"\nRunning simulation for {simulation_minutes} minutes...")
    
    # Run with progress updates
    checkpoint_interval = 24 * 60  # Daily checkpoints
    for day in range(duration_days):
        env.run(until=(day + 1) * checkpoint_interval)
        logger.info(f"Day {day + 1}/{duration_days} complete (simulation time: {env.now:.0f} min)")
    
    # Collect final metrics
    logger.info("\n" + "=" * 80)
    logger.info("SIMULATION COMPLETE")
    logger.info("=" * 80)
    
    # Get V-curve metrics
    vcurve_metrics = vcurve_controller.get_metrics()
    logger.info(f"\nV-Curve Metrics:")
    logger.info(f"  Constraint: {vcurve_metrics['constraint_id']}")
    logger.info(f"  Constraint changes: {vcurve_metrics['constraint_changes']}")
    logger.info(f"  Starvation rate: {vcurve_metrics['constraint_starvation_rate']*100:.1f}%")
    logger.info(f"  Blocking rate: {vcurve_metrics['constraint_blocking_rate']*100:.1f}%")
    
    # Calculate overall OEE
    df = mes_collector.to_dataframe()
    
    if not df.empty:
        overall_availability = df['Availability_Score'].mean()
        overall_performance = df['Performance_Score'].mean()
        overall_quality = df['Quality_Score'].mean()
        overall_oee = df['OEE_Score'].mean()
        
        logger.info(f"\nOverall Metrics:")
        logger.info(f"  Availability: {overall_availability:.1f}%")
        logger.info(f"  Performance: {overall_performance:.1f}%")
        logger.info(f"  Quality: {overall_quality:.1f}%")
        logger.info(f"  OEE: {overall_oee:.1f}%")
        
        # Check if we hit target
        target_range = suboptimal_config['expected_metrics']['overall_oee']
        if target_range['min'] <= overall_oee/100 <= target_range['max']:
            logger.info(f"\n✅ SUCCESS: OEE {overall_oee:.1f}% is within target range [{target_range['min']*100:.0f}%-{target_range['max']*100:.0f}%]")
        else:
            logger.warning(f"\n⚠️ WARNING: OEE {overall_oee:.1f}% is outside target range [{target_range['min']*100:.0f}%-{target_range['max']*100:.0f}%]")
        
        # Save to CSV
        output_path = Path(output_file)
        mes_collector.save_to_csv(output_path)
        logger.info(f"\nMES data saved to: {output_path}")
        logger.info(f"Total records: {len(df)}")
    else:
        logger.error("No MES data collected!")
    
    return mes_collector, vcurve_controller


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run MES baseline simulation with sub-optimal configuration"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Number of days to simulate (default: 14)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="mes_baseline_output.csv",
        help="Output CSV file (default: mes_baseline_output.csv)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/baseline_suboptimal.yaml",
        help="Sub-optimal configuration file (default: config/baseline_suboptimal.yaml)"
    )
    
    args = parser.parse_args()
    
    try:
        mes_collector, vcurve_controller = run_baseline_simulation(
            duration_days=args.days,
            output_file=args.output,
            config_path=args.config
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("MES BASELINE SIMULATION COMPLETE")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()