#!/usr/bin/env python3
"""Run Twin Model simulation with production orders and MES data collection.

This script orchestrates a complete production simulation using:
- Ontology-driven equipment definitions
- Equipment manifest for instances and connections
- Tunable parameters for operational settings
- Product manifest for product specifications
- Production orders for scheduling

Time units: All durations are in MINUTES (Twin Model native unit)
"""

import argparse
import logging
import simpy
import sys
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from twin_model import OntologyModelBuilder
from twin_model.scheduling import ProductionScheduler
from twin_model.scheduling.product_manifest import ProductManifest
from twin_model.transduction import MESDataCollector
# Use the ProductionOrder from source_flow which is what sources expect
from twin_model.primitives.source_flow import ProductionOrder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_yaml_file(filepath: Path) -> Dict:
    """Load and parse a YAML file.
    
    Args:
        filepath: Path to YAML file
        
    Returns:
        Parsed YAML content
        
    Raises:
        SystemExit: If file cannot be loaded
    """
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        sys.exit(1)
    
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        sys.exit(1)


def load_production_orders(orders_path: Path) -> Dict[str, List[ProductionOrder]]:
    """Load production orders from YAML file.
    
    Args:
        orders_path: Path to production orders YAML
        
    Returns:
        Dictionary mapping line IDs to lists of ProductionOrder objects
    """
    data = load_yaml_file(orders_path)
    orders_by_line = {}
    
    # Check if orders are directly defined
    if 'orders' in data:
        current_time = 0.0  # Start time in minutes
        
        for i, order_data in enumerate(data['orders']):
            # Calculate duration based on target volume if not specified
            # Assume nominal rate of 50 units/minute as default
            if 'scheduled_duration' in order_data:
                duration = order_data['scheduled_duration']
            else:
                # Estimate duration from volume (assume 50 units/min rate)
                nominal_rate = 50.0
                duration = (order_data['target_volume'] / nominal_rate) * 1.2  # Add 20% buffer
            
            # Use specified start time or calculate sequentially
            if 'scheduled_start' in order_data:
                start_time = order_data['scheduled_start']
            else:
                start_time = current_time
                # Add changeover time between orders (30 minutes default)
                if i > 0:
                    start_time += 30
            
            # Calculate due_time from start_time + duration
            due_time = start_time + duration
            
            # Create order using source_flow.ProductionOrder structure
            order = ProductionOrder(
                order_id=order_data['order_id'],
                product_id=order_data['product_id'],
                target_volume=order_data['target_volume'],
                due_time=due_time,  # source_flow expects due_time
                priority=order_data.get('priority', 5)
            )
            
            # Group by line_id for later dispatch
            line_id = order_data['line_id']
            if line_id not in orders_by_line:
                orders_by_line[line_id] = []
            orders_by_line[line_id].append(order)
            
            # Update current time for next order on same line
            current_time = start_time + duration
    
    return orders_by_line


def connect_scheduler_to_sources(
    scheduler: ProductionScheduler,
    model: Dict,
    orders_by_line: Dict[str, List[ProductionOrder]]
) -> None:
    """Connect scheduler to source equipment for order dispatch.
    
    Args:
        scheduler: Production scheduler instance
        model: Model dictionary from OntologyModelBuilder
        orders_by_line: Dictionary mapping line IDs to lists of ProductionOrder objects
    """
    primitives = model['primitives']
    
    # Process orders for each line
    for line_id, line_orders in orders_by_line.items():
        # Normalize line_id
        normalized_line_id = f"LINE{line_id}" if not line_id.startswith("LINE") else line_id
        
        # Find source for this line
        source_id = None
        for eq_id, equipment in primitives.items():
            if normalized_line_id in eq_id and 'SOURCE' in eq_id:
                source_id = eq_id
                break
        
        if source_id:
            source = primitives[source_id]
            # Switch to order mode from continuous mode
            source.continuous_mode = False
            # Add all orders for this line
            for order in line_orders:
                source.add_order(order)
                logger.info(f"Added order {order.order_id} to {source_id}")
        else:
            logger.warning(f"No source found for line {normalized_line_id}")


def print_progress(env: simpy.Environment, model: Dict, metrics: Dict) -> None:
    """Print simulation progress report.
    
    Args:
        env: SimPy environment
        model: Model dictionary
        metrics: Current metrics from builder
    """
    print("\n" + "=" * 80)
    print(f"SIMULATION TIME: {env.now:.1f} minutes ({env.now/60:.1f} hours)")
    print("=" * 80)
    
    primitives = model['primitives']
    lines = model.get('lines', {})
    
    # Summary by line
    for line_id, equipment_ids in lines.items():
        print(f"\n{line_id}:")
        
        # Find sink for total production
        sink_id = None
        for eq_id in equipment_ids:
            if 'SINK' in eq_id:
                sink_id = eq_id
                break
        
        if sink_id and sink_id in metrics:
            sink_metrics = metrics[sink_id]
            # Sink reports total_input not total_consumed
            total = sink_metrics.get('total_input', 0)
            rate = total / env.now if env.now > 0 else 0
            print(f"  Total Production: {total:.0f} units")
            print(f"  Production Rate: {rate:.1f} units/min")
            
            # OEE if available
            oee = sink_metrics.get('oee', 0)
            if oee > 0:
                print(f"  Line OEE: {oee:.1f}%")  # Already in percentage
        
        # Equipment states
        states = []
        for eq_id in equipment_ids:
            if eq_id in primitives:
                equipment = primitives[eq_id]
                state = str(equipment.current_state).split('.')[-1]
                states.append(f"{eq_id.split('-')[-1]}:{state}")
        
        if states:
            print(f"  States: {' -> '.join(states)}")


def print_final_summary(env: simpy.Environment, model: Dict, metrics: Dict) -> None:
    """Print final simulation summary.
    
    Args:
        env: SimPy environment
        model: Model dictionary
        metrics: Final metrics from builder
    """
    print("\n" + "=" * 80)
    print("FINAL SIMULATION SUMMARY")
    print("=" * 80)
    print(f"Total Simulation Time: {env.now:.1f} minutes ({env.now/60:.1f} hours)")
    
    # Overall production
    total_production = 0
    for eq_id, eq_metrics in metrics.items():
        if 'SINK' in eq_id:
            # Sink reports total_input not total_consumed
            total_production += eq_metrics.get('total_input', 0)
    
    print(f"Total Production: {total_production:.0f} units")
    print(f"Average Rate: {total_production/env.now:.1f} units/min")
    
    # Per-line summary
    lines = model.get('lines', {})
    print("\nPer-Line Performance:")
    for line_id in sorted(lines.keys()):
        equipment_ids = lines[line_id]
        
        # Find key equipment
        for eq_id in equipment_ids:
            if 'SINK' in eq_id and eq_id in metrics:
                sink_metrics = metrics[eq_id]
                # Sink reports total_input not total_consumed
                production = sink_metrics.get('total_input', 0)
                oee = sink_metrics.get('oee', 0)
                
                print(f"\n{line_id}:")
                print(f"  Production: {production:.0f} units")
                print(f"  OEE: {oee:.1f}%")  # Already in percentage
                
                # Breakdown if available
                availability = sink_metrics.get('availability', 0)
                performance = sink_metrics.get('performance', 0)
                quality = sink_metrics.get('quality', 0)
                
                if availability > 0:
                    print(f"  - Availability: {availability:.1f}%")  # Already in percentage
                    print(f"  - Performance: {performance:.1f}%")  # Already in percentage
                    print(f"  - Quality: {quality:.1f}%")  # Already in percentage
                break
    
    # Equipment-level OEE
    print("\nEquipment OEE:")
    equipment_found = False
    for eq_id in sorted(metrics.keys()):
        if any(x in eq_id for x in ['FIL', 'PCK', 'PAL']):
            eq_metrics = metrics[eq_id]
            oee = eq_metrics.get('oee', 0)
            if oee > 0:
                equipment_found = True
                print(f"  {eq_id}: {oee:.1f}%")  # Already in percentage
                # Show breakdown if available
                if 'availability' in eq_metrics and 'performance' in eq_metrics and 'quality' in eq_metrics:
                    print(f"    A:{eq_metrics['availability']:.1f}% P:{eq_metrics['performance']:.1f}% Q:{eq_metrics['quality']:.1f}%")
    
    if not equipment_found:
        print("  (No equipment OEE data available)")


def main():
    """Main simulation runner."""
    parser = argparse.ArgumentParser(
        description="Run Twin Model simulation with production orders"
    )
    
    # Required arguments
    parser.add_argument(
        '--ontology', 
        type=Path, 
        required=True,
        help='Path to ontology YAML file'
    )
    parser.add_argument(
        '--manifest', 
        type=Path, 
        required=True,
        help='Path to equipment manifest YAML file'
    )
    parser.add_argument(
        '--config', 
        type=Path, 
        required=True,
        help='Path to configuration/parameters YAML file'
    )
    parser.add_argument(
        '--product-manifest', 
        type=Path, 
        required=True,
        help='Path to product manifest YAML file'
    )
    parser.add_argument(
        '--production-orders', 
        type=Path, 
        required=True,
        help='Path to production orders YAML file'
    )
    
    # Optional arguments
    parser.add_argument(
        '--duration', 
        type=float, 
        default=480.0,
        help='Simulation duration in minutes (default: 480 = 8 hours)'
    )
    parser.add_argument(
        '--mes-output', 
        type=Path,
        help='Path for MES output CSV file'
    )
    parser.add_argument(
        '--report-interval', 
        type=float,
        default=60.0,
        help='Progress report interval in minutes (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Validate all required files exist
    for filepath, name in [
        (args.ontology, 'Ontology'),
        (args.manifest, 'Manifest'),
        (args.config, 'Config'),
        (args.product_manifest, 'Product Manifest'),
        (args.production_orders, 'Production Orders')
    ]:
        if not filepath.exists():
            logger.error(f"{name} file not found: {filepath}")
            sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("TWIN MODEL SIMULATION RUNNER")
    logger.info("=" * 80)
    logger.info(f"Ontology: {args.ontology}")
    logger.info(f"Manifest: {args.manifest}")
    logger.info(f"Config: {args.config}")
    logger.info(f"Product Manifest: {args.product_manifest}")
    logger.info(f"Production Orders: {args.production_orders}")
    logger.info(f"Duration: {args.duration} minutes ({args.duration/60:.1f} hours)")
    logger.info("=" * 80)
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Build model
    logger.info("\nBuilding simulation model...")
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=args.ontology,
        manifest_path=args.manifest,
        config_path=args.config
    )
    
    model = builder.build_model()
    primitives = model['primitives']
    lines = model.get('lines', {})
    
    logger.info(f"Model built with {len(primitives)} equipment pieces")
    logger.info(f"Production lines: {list(lines.keys())}")
    
    # Load product manifest
    logger.info("\nLoading product manifest...")
    product_manifest = ProductManifest(args.product_manifest)
    logger.info(f"Loaded {len(product_manifest.products)} products")
    
    # Load production orders
    logger.info("\nLoading production orders...")
    orders_by_line = load_production_orders(args.production_orders)
    total_orders = sum(len(orders) for orders in orders_by_line.values())
    logger.info(f"Loaded {total_orders} production orders across {len(orders_by_line)} lines")
    
    # Create scheduler (sequential, no optimization)
    logger.info("\nSetting up production scheduler...")
    scheduler = ProductionScheduler(
        env=env,
        catalog_path=args.product_manifest
    )
    
    # Connect orders to sources
    logger.info("\nConnecting orders to equipment...")
    connect_scheduler_to_sources(scheduler, model, orders_by_line)
    
    # Setup MES collection if requested
    mes_collector = None
    if args.mes_output:
        logger.info("\nSetting up MES data collection...")
        mes_collector = MESDataCollector(
            env=env,
            product_manifest_path=args.product_manifest
        )
        
        # Register only core production equipment with MES collector
        # (FIL, PCK, PAL - not sources, sinks, or buffers)
        for eq_id, equipment in primitives.items():
            # Skip buffers, sources, and sinks
            if 'BUF' in eq_id or 'SOURCE' in eq_id or 'SINK' in eq_id:
                continue
            
            # Only register core production equipment (FIL, PCK, PAL)
            if any(equip_type in eq_id for equip_type in ['-FIL', '-PCK', '-PAL']):
                # Extract line_id from equipment ID (e.g., LINE1-FIL -> LINE1)
                line_id = eq_id.split('-')[0] if '-' in eq_id else 'UNKNOWN'
                # Get equipment type from class name
                equipment_type = equipment.__class__.__name__
                
                # Register equipment for monitoring
                mes_collector.register_equipment(
                    equipment_id=eq_id,
                    equipment=equipment,
                    equipment_type=equipment_type,
                    line_id=line_id
                )
                logger.debug(f"Registered {eq_id} with MES collector")
        
        # Start the data collection process
        env.process(mes_collector.collect_data())
        logger.info("Started MES data collection process")
    
    # Run simulation with periodic reporting
    logger.info("\n" + "=" * 80)
    logger.info("STARTING SIMULATION")
    logger.info("=" * 80)
    
    # Initial state
    metrics = builder.get_metrics()
    print_progress(env, model, metrics)
    
    # Run with periodic reports
    next_report = args.report_interval
    while env.now < args.duration:
        # Run until next report or end
        run_until = min(next_report, args.duration)
        env.run(until=run_until)
        
        # Get current metrics
        metrics = builder.get_metrics()
        print_progress(env, model, metrics)
        
        next_report += args.report_interval
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("SIMULATION COMPLETE")
    logger.info("=" * 80)
    
    final_metrics = builder.get_metrics()
    print_final_summary(env, model, final_metrics)
    
    # Export MES data if requested
    if mes_collector and args.mes_output:
        # Force final data collection at simulation end (t=60)
        logger.info("Collecting final MES data point...")
        mes_collector.collect_current_data()
        
        logger.info(f"\nExporting MES data to {args.mes_output}...")
        mes_collector.save_to_csv(args.mes_output)
        logger.info("MES data export complete")
    
    logger.info("\n✅ Simulation completed successfully!")


if __name__ == "__main__":
    main()