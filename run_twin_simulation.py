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
import sys
from pathlib import Path
from typing import Dict, Generator, List

import simpy
import yaml

from twin_model import OntologyModelBuilder

# Use the ProductionOrder from source_flow which is what sources expect
from twin_model.primitives.source_flow import ProductionOrder
from twin_model.scheduling import ProductionScheduler
from twin_model.scheduling.product_manifest import ProductManifest
from twin_model.transduction import MESDataCollector

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
        with open(filepath) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        sys.exit(1)


def load_production_orders(
    orders_path: Path, simulation_duration: float = 0.0, cycle_orders: bool = True
) -> Dict[str, List[ProductionOrder]]:
    """Load production orders from YAML file, optionally cycling them to fill duration.

    Args:
        orders_path: Path to production orders YAML
        simulation_duration: Simulation duration in minutes (0 = no cycling)
        cycle_orders: Whether to automatically cycle orders to fill duration

    Returns:
        Dictionary mapping line IDs to lists of ProductionOrder objects
    """
    data = load_yaml_file(orders_path)
    orders_by_line = {}

    # Check if orders are directly defined
    if "orders" in data:
        # Track current time PER LINE, not globally
        current_time_by_line = {}

        for order_data in data["orders"]:
            line_id = order_data["line_id"]

            # Initialize line's timeline if first order
            if line_id not in current_time_by_line:
                current_time_by_line[line_id] = 0.0
                orders_by_line[line_id] = []

            # Calculate order duration based on target volume if not specified
            # Derive nominal rate from product manifest when possible; fallback to 50 u/min
            if "scheduled_duration" in order_data:
                order_duration = order_data["scheduled_duration"]
            else:
                # Try to read product manifest target rate (units per 5 minutes)
                product_id = order_data.get("product_id")
                nominal_rate = 50.0
                try:
                    # Load product manifest once per call (outside loop would be better, but keep function pure)
                    # Note: This function doesn't have product manifest path; use default location
                    product_manifest_path = Path("manifests/product_manifest.yaml")
                    if product_manifest_path.exists() and product_id:
                        with open(product_manifest_path) as pf:
                            pm_data = yaml.safe_load(pf) or {}
                        prod = (pm_data.get("products", {}) or {}).get(product_id, {})
                        target_rate_5min = prod.get("production", {}).get("target_rate_5min")
                        nominal_rate_per_min = None
                        if target_rate_5min:
                            nominal_rate_per_min = float(target_rate_5min) / 5.0
                        else:
                            nominal_rate_per_min = prod.get("production", {}).get("nominal_rate_per_min")

                        if nominal_rate_per_min and float(nominal_rate_per_min) > 0:
                            nominal_rate = float(nominal_rate_per_min)
                except Exception:
                    # Fall back silently to default
                    pass

                order_duration = (order_data["target_volume"] / nominal_rate) * 1.2  # Add 20% buffer

            # Use specified start time or calculate sequentially FOR THIS LINE
            if "scheduled_start" in order_data:
                start_time = order_data["scheduled_start"]
            else:
                start_time = current_time_by_line[line_id]
                # Add changeover time between orders on same line (30 minutes default)
                if len(orders_by_line[line_id]) > 0:
                    start_time += 30

            # Calculate due_time from start_time + order_duration
            due_time = start_time + order_duration

            # Create order using source_flow.ProductionOrder structure
            order = ProductionOrder(
                order_id=order_data["order_id"],
                product_id=order_data["product_id"],
                target_volume=order_data["target_volume"],
                due_time=due_time,  # source_flow expects due_time
                priority=order_data.get("priority", 5),
            )

            # Add to line's order list
            orders_by_line[line_id].append(order)

            # Update current time for THIS LINE
            current_time_by_line[line_id] = start_time + order_duration

    if cycle_orders and simulation_duration > 0 and orders_by_line:
        logger.info(f"Cycling orders to fill {simulation_duration:.0f} minute simulation...")

        for line_id, orders in orders_by_line.items():
            if not orders:
                continue

            last_due_time = max(o.due_time for o in orders)
            logger.debug(
                f"{line_id}: last_due_time={last_due_time:.1f}, simulation_duration={simulation_duration:.1f}, will_cycle={last_due_time < simulation_duration}"
            )

            if last_due_time < simulation_duration:
                original_orders = orders.copy()
                cycle = 1

                # Calculate the cycle duration (time for all orders in one cycle)
                cycle_duration = max(o.due_time for o in original_orders)

                while last_due_time < simulation_duration:
                    # Add ALL orders for this cycle before moving to next cycle
                    cycle_orders = []
                    for original_order in original_orders:
                        new_order = ProductionOrder(
                            order_id=f"{original_order.order_id}-C{cycle}",
                            product_id=original_order.product_id,
                            target_volume=original_order.target_volume,
                            due_time=original_order.due_time + (cycle * cycle_duration),
                            priority=original_order.priority,
                        )
                        cycle_orders.append(new_order)
                        last_due_time = new_order.due_time

                    # Check if the entire cycle fits within simulation duration
                    if cycle_orders and cycle_orders[-1].due_time <= simulation_duration:
                        # Append entire cycle at once
                        orders.extend(cycle_orders)
                    else:
                        # Don't add partial cycles
                        break

                    cycle += 1

                    if cycle > 100:
                        logger.warning(f"Order cycling limit reached for {line_id}")
                        break

                logger.info(f"{line_id}: Cycled to {len(orders)} orders (from {len(original_orders)} original)")

    return orders_by_line


def update_mes_from_sources(env: simpy.Environment, mes_collector, model: Dict, primitives: Dict) -> Generator:
    """Background process to sync MES collector with current production orders from sources.

    Args:
        env: SimPy environment
        mes_collector: MES data collector instance
        model: Model dictionary with equipment info
        primitives: Dictionary of all primitives
    """
    lines = model.get("lines", {})
    source_by_line = {}

    for line_id, equipment_ids in lines.items():
        for eq_id in equipment_ids:
            if "SOURCE" in eq_id and eq_id in primitives:
                source_by_line[line_id] = primitives[eq_id]
                break

    last_order_by_line = {}

    while True:
        yield env.timeout(1.0)

        for line_id, source in source_by_line.items():
            if source.current_order:
                order_id = source.current_order.order_id
                product_id = source.current_order.product_id

                if last_order_by_line.get(line_id) != order_id:
                    for eq_id in lines[line_id]:
                        if "SOURCE" not in eq_id and "SINK" not in eq_id and "BUF" not in eq_id:
                            mes_collector.update_production_order(eq_id, order_id, product_id)

                    logger.debug(f"{line_id}: MES updated to order {order_id}, product {product_id}")
                    last_order_by_line[line_id] = order_id


def connect_scheduler_to_sources(
    scheduler: ProductionScheduler, model: Dict, orders_by_line: Dict[str, List[ProductionOrder]]
) -> None:
    """Connect scheduler to source equipment for order dispatch.

    Args:
        scheduler: Production scheduler instance
        model: Model dictionary from OntologyModelBuilder
        orders_by_line: Dictionary mapping line IDs to lists of ProductionOrder objects
    """
    primitives = model["primitives"]

    # Process orders for each line
    for line_id, line_orders in orders_by_line.items():
        # Normalize line_id
        normalized_line_id = f"LINE{line_id}" if not line_id.startswith("LINE") else line_id

        # Find source for this line
        source_id = None
        for eq_id, _equipment in primitives.items():
            if normalized_line_id in eq_id and "SOURCE" in eq_id:
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

    primitives = model["primitives"]
    lines = model.get("lines", {})

    # Summary by line
    for line_id, equipment_ids in lines.items():
        print(f"\n{line_id}:")

        # Find sink for total production
        sink_id = None
        for eq_id in equipment_ids:
            if "SINK" in eq_id:
                sink_id = eq_id
                break

        if sink_id and sink_id in metrics:
            sink_metrics = metrics[sink_id]
            # Sink reports total_input not total_consumed
            total = sink_metrics.get("total_input", 0)
            rate = total / env.now if env.now > 0 else 0
            print(f"  Total Production: {total:.0f} units")
            print(f"  Production Rate: {rate:.1f} units/min")

            # OEE if available
            oee = sink_metrics.get("oee", 0)
            if oee > 0:
                print(f"  Line OEE: {oee:.1f}%")  # Already in percentage

        # Equipment states
        states = []
        for eq_id in equipment_ids:
            if eq_id in primitives:
                equipment = primitives[eq_id]
                state = str(equipment.current_state).split(".")[-1]
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
        if "SINK" in eq_id:
            # Sink reports total_input not total_consumed
            total_production += eq_metrics.get("total_input", 0)

    print(f"Total Production: {total_production:.0f} units")
    print(f"Average Rate: {total_production/env.now:.1f} units/min")

    # Per-line summary
    lines = model.get("lines", {})
    print("\nPer-Line Performance:")
    for line_id in sorted(lines.keys()):
        equipment_ids = lines[line_id]

        # Find key equipment
        for eq_id in equipment_ids:
            if "SINK" in eq_id and eq_id in metrics:
                sink_metrics = metrics[eq_id]
                # Sink reports total_input not total_consumed
                production = sink_metrics.get("total_input", 0)
                oee = sink_metrics.get("oee", 0)

                print(f"\n{line_id}:")
                print(f"  Production: {production:.0f} units")
                print(f"  OEE: {oee:.1f}%")  # Already in percentage

                # Breakdown if available
                availability = sink_metrics.get("availability", 0)
                performance = sink_metrics.get("performance", 0)
                quality = sink_metrics.get("quality", 0)

                if availability > 0:
                    print(f"  - Availability: {availability:.1f}%")  # Already in percentage
                    print(f"  - Performance: {performance:.1f}%")  # Already in percentage
                    print(f"  - Quality: {quality:.1f}%")  # Already in percentage
                break

    # Equipment-level OEE
    print("\nEquipment OEE:")
    equipment_found = False
    for eq_id in sorted(metrics.keys()):
        if any(x in eq_id for x in ["FIL", "PCK", "PAL"]):
            eq_metrics = metrics[eq_id]
            oee = eq_metrics.get("oee", 0)
            if oee > 0:
                equipment_found = True
                print(f"  {eq_id}: {oee:.1f}%")  # Already in percentage
                # Show breakdown if available
                if "availability" in eq_metrics and "performance" in eq_metrics and "quality" in eq_metrics:
                    print(
                        f"    A:{eq_metrics['availability']:.1f}% P:{eq_metrics['performance']:.1f}% Q:{eq_metrics['quality']:.1f}%"
                    )

    if not equipment_found:
        print("  (No equipment OEE data available)")


def main():
    """Main simulation runner."""
    parser = argparse.ArgumentParser(description="Run Twin Model simulation with production orders")

    # Configuration file arguments with defaults
    parser.add_argument(
        "--ontology",
        type=Path,
        default=Path("ontology/filling_line_ontology.yaml"),
        help="Path to ontology YAML file (default: ontology/filling_line_ontology.yaml)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("manifests/equipment_manifest.yaml"),
        help="Path to equipment manifest YAML file (default: manifests/equipment_manifest.yaml)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/tunable_parameters.yaml"),
        help="Path to configuration/parameters YAML file (default: config/tunable_parameters.yaml)",
    )
    parser.add_argument(
        "--product-manifest",
        type=Path,
        default=Path("manifests/product_manifest.yaml"),
        help="Path to product manifest YAML file (default: manifests/product_manifest.yaml)",
    )
    parser.add_argument(
        "--production-orders",
        type=Path,
        default=Path("manifests/production_orders_manifest.yaml"),
        help="Path to production orders YAML file (default: manifests/production_orders_manifest.yaml)",
    )

    # Duration arguments
    parser.add_argument("--duration", type=float, help="Simulation duration in minutes (use --days for convenience)")
    parser.add_argument("--days", type=float, help="Simulation duration in days (converted to minutes)")

    # Output and reporting
    parser.add_argument("--mes-output", type=Path, help="Path for MES output CSV file")
    parser.add_argument(
        "--report-interval", type=float, default=60.0, help="Progress report interval in minutes (default: 60)"
    )

    # Logging
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--no-cycle-orders", action="store_true", help="Disable automatic order cycling to fill simulation duration"
    )

    args = parser.parse_args()

    # Handle duration conversion
    if args.days and args.duration:
        logger.error("Cannot specify both --days and --duration")
        sys.exit(1)
    elif args.days:
        args.duration = args.days * 1440  # Convert days to minutes
    elif not args.duration:
        args.duration = 480.0  # Default: 8 hours

    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Validate all required files exist
    for filepath, name in [
        (args.ontology, "Ontology"),
        (args.manifest, "Manifest"),
        (args.config, "Config"),
        (args.product_manifest, "Product Manifest"),
        (args.production_orders, "Production Orders"),
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
        env=env, ontology_path=args.ontology, manifest_path=args.manifest, config_path=args.config
    )

    model = builder.build_model()
    primitives = model["primitives"]
    lines = model.get("lines", {})

    logger.info(f"Model built with {len(primitives)} equipment pieces")
    logger.info(f"Production lines: {list(lines.keys())}")

    # Load product manifest
    logger.info("\nLoading product manifest...")
    product_manifest = ProductManifest(args.product_manifest)
    logger.info(f"Loaded {len(product_manifest.products)} products")

    # Load production orders
    logger.info("\nLoading production orders...")
    orders_by_line = load_production_orders(
        args.production_orders, simulation_duration=args.duration, cycle_orders=not args.no_cycle_orders
    )
    total_orders = sum(len(orders) for orders in orders_by_line.values())
    logger.info(f"Loaded {total_orders} production orders across {len(orders_by_line)} lines")

    # Create scheduler (sequential, no optimization)
    logger.info("\nSetting up production scheduler...")
    scheduler = ProductionScheduler(env=env, catalog_path=args.product_manifest)

    # Setup MES collection if requested
    mes_collector = None
    if args.mes_output:
        logger.info("\nSetting up MES data collection...")
        mes_collector = MESDataCollector(env=env, product_manifest_path=args.product_manifest)

        # Register only core production equipment with MES collector
        # (FIL, PCK, PAL - not sources, sinks, or buffers)
        for eq_id, equipment in primitives.items():
            # Skip buffers, sources, and sinks
            if "BUF" in eq_id or "SOURCE" in eq_id or "SINK" in eq_id:
                continue

            # Only register core production equipment (FIL, PCK, PAL)
            if any(equip_type in eq_id for equip_type in ["-FIL", "-PCK", "-PAL"]):
                # Extract line_id from equipment ID (e.g., LINE1-FIL -> LINE1)
                line_id = eq_id.split("-")[0] if "-" in eq_id else "UNKNOWN"
                # Get equipment type from class name
                equipment_type = equipment.__class__.__name__

                # Register equipment for monitoring
                mes_collector.register_equipment(
                    equipment_id=eq_id, equipment=equipment, equipment_type=equipment_type, line_id=line_id
                )
                logger.debug(f"Registered {eq_id} with MES collector")

        # Start the data collection process
        env.process(mes_collector.collect_data())
        logger.info("Started MES data collection process")

    # Connect orders to sources
    logger.info("\nConnecting orders to equipment...")
    connect_scheduler_to_sources(scheduler, model, orders_by_line)

    # Start MES sync process if MES collector exists
    if mes_collector:
        env.process(update_mes_from_sources(env, mes_collector, model, primitives))
        logger.info("Started MES order sync process")

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
