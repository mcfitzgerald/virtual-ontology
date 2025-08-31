#!/usr/bin/env python3
"""Run simulation and generate MES-format output.

This script orchestrates the twin_model components to run a production simulation
and output results in MES-compatible CSV format.
"""

import sys
from pathlib import Path
import simpy
import yaml
import logging
from datetime import datetime
import argparse

# Add current directory to path if needed
sys.path.insert(0, str(Path.cwd()))

from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.control.control_manager import ControlManager
from twin_model.transduction.mes_transducer import MESTransducer
from twin_model.logging_config import SimulationLogger

# Configure logging
logger = SimulationLogger.get_logger(__name__)


def load_manifests(manifest_dir: Path) -> dict:
    """Load all manifest files."""
    manifests = {}
    
    # Load equipment manifest
    equipment_path = manifest_dir / "equipment_manifest.yaml"
    if equipment_path.exists():
        with open(equipment_path, "r") as f:
            manifests["equipment_manifest"] = yaml.safe_load(f)
            logger.info(f"Loaded equipment manifest with {len(manifests['equipment_manifest'].get('equipment', {}))} equipment")
    
    # Load production manifest
    production_path = manifest_dir / "production_manifest.yaml"
    if production_path.exists():
        with open(production_path, "r") as f:
            manifests["production_manifest"] = yaml.safe_load(f)
            logger.info(f"Loaded production manifest with {len(manifests['production_manifest'].get('products', {}))} products")
    
    # Load control settings
    control_path = manifest_dir / "control_settings.yaml"
    if control_path.exists():
        with open(control_path, "r") as f:
            manifests["control_settings"] = yaml.safe_load(f)
            logger.info("Loaded control settings")
    
    return manifests


def run_mes_simulation(
    duration_minutes: int = 60,
    output_file: str = "mes_simulation_output.csv",
    set_baseline_parameters: bool = True
):
    """Run simulation and generate MES-format output.
    
    Args:
        duration_minutes: Simulation duration in minutes (default 60)
        output_file: Output CSV filename (default mes_simulation_output.csv)
        set_baseline_parameters: Whether to set realistic OEE parameters (default True)
    
    Returns:
        DataFrame with MES-format results
    """
    print("\n" + "=" * 80)
    print(f"MES SIMULATION - {duration_minutes} minutes")
    print("=" * 80)
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Set up paths
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    # Initialize control manager
    logger.info("Initializing control manager...")
    control_mgr = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml"
    )
    
    # Load manifests
    logger.info("Loading manifests...")
    manifests = load_manifests(manifest_dir)
    
    # Create model builder
    logger.info("Creating model builder...")
    builder = OntologyDrivenModelBuilder(
        env=env,
        ontology_path=ontology_path,
        manifest_dir=manifest_dir,
        control_manager=control_mgr
    )
    
    # Build the model
    logger.info("Building model from ontology and manifests...")
    model = builder.build_model()
    
    # All parameters come from manifests - no overrides needed
    if set_baseline_parameters:
        logger.info("Using baseline parameters from manifests...")
    
    # Configure sources for continuous generation (if not using production orders)
    logger.info("Configuring sources...")
    for primitive in model["primitives"].values():
        if hasattr(primitive, "order_mode"):
            # Keep order mode as configured in manifests
            # But ensure reasonable arrival rate
            if not primitive.order_mode:
                primitive.arrival_rate = 100  # 100 units/min for continuous mode
            logger.info(f"Source {primitive.config.id}: order_mode={primitive.order_mode}, rate={primitive.arrival_rate}")
    
    # Start all processes
    logger.info("Starting all processes...")
    for primitive in model["primitives"].values():
        if hasattr(primitive, "start"):
            primitive.start()
    
    # Start scheduler if present
    if "scheduler" in model and model["scheduler"]:
        logger.info("Starting scheduler...")
        model["scheduler"].start()
    
    # Run simulation
    logger.info(f"\nRunning simulation for {duration_minutes} minutes...")
    env.run(until=duration_minutes)
    
    # Finalize state durations for all equipment
    logger.info("Finalizing state durations...")
    for primitive in model["primitives"].values():
        if hasattr(primitive, "state_durations") and hasattr(primitive, "state"):
            # Add remaining time to current state
            if hasattr(primitive, "state_start_time"):
                remaining_duration = env.now - primitive.state_start_time
                primitive.state_durations[primitive.state] += remaining_duration
    
    # Collect observables from all primitives
    logger.info("Collecting observables...")
    all_observables = []
    
    for prim_id, primitive in model["primitives"].items():
        if hasattr(primitive, "get_observables"):
            obs_list = primitive.get_observables()
            
            # Ensure primitive_id is set for each observable
            for obs in obs_list:
                obs["primitive_id"] = prim_id
                all_observables.append(obs)
    
    logger.info(f"Collected {len(all_observables)} observable events")
    
    # Process observables through MES transducer
    logger.info("Processing observables through MES transducer...")
    transducer = MESTransducer(time_bucket=5)  # 5-minute buckets
    mes_df = transducer.process_observables(all_observables, manifests)
    
    logger.info(f"Generated {len(mes_df)} MES records")
    
    # Save to CSV
    if not mes_df.empty:
        mes_df.to_csv(output_file, index=False)
        print(f"\n✅ MES data saved to {output_file}")
        
        # Print summary statistics
        print("\n" + "=" * 80)
        print("SIMULATION SUMMARY")
        print("=" * 80)
        
        summary = transducer.generate_summary_statistics(mes_df)
        
        print("\nOverall Metrics:")
        print(f"  OEE:          {summary['overall_metrics']['oee']:.1f}%")
        print(f"  Availability: {summary['overall_metrics']['availability']:.1f}%")
        print(f"  Performance:  {summary['overall_metrics']['performance']:.1f}%")
        print(f"  Quality:      {summary['overall_metrics']['quality']:.1f}%")
        
        print("\nProduction:")
        print(f"  Good Units:   {summary['production']['total_good_units']:,}")
        print(f"  Scrap Units:  {summary['production']['total_scrap_units']:,}")
        print(f"  Scrap Rate:   {summary['production']['scrap_rate']:.2f}%")
        
        if summary['downtime']['total_stops'] > 0:
            print("\nDowntime:")
            print(f"  Total Stops:  {summary['downtime']['total_stops']}")
            if summary['downtime']['reasons']:
                print("  Reasons:")
                for reason, count in summary['downtime']['reasons'].items():
                    print(f"    {reason}: {count}")
        
        if summary['line_performance']:
            print("\nLine Performance (OEE):")
            for line, oee in summary['line_performance'].items():
                print(f"  Line {line}: {oee:.1f}%")
    else:
        print("\n⚠️  No MES records generated - check simulation configuration")
    
    return mes_df


def main():
    """Main entry point with CLI arguments."""
    parser = argparse.ArgumentParser(description="Run twin model simulation with MES output")
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Simulation duration in minutes (default: 60)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="mes_simulation_output.csv",
        help="Output CSV filename (default: mes_simulation_output.csv)"
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="Don't set baseline OEE parameters (use manifest values)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Run simulation
    mes_df = run_mes_simulation(
        duration_minutes=args.duration,
        output_file=args.output,
        set_baseline_parameters=not args.no_baseline
    )
    
    return 0 if not mes_df.empty else 1


if __name__ == "__main__":
    sys.exit(main())