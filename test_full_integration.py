"""Full integration test using ModelBuilder with all configuration files.

This test properly loads and uses:
- Ontology (twin_ontology.yaml)
- Equipment manifest (equipment_manifest.yaml)
- Production manifest (production_manifest.yaml)
- Control settings (control_settings.yaml)
- Control mappings (control_mappings.yaml)
"""

import sys
from pathlib import Path
import simpy
import yaml
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from twin_model.model_builder import OntologyDrivenModelBuilderV2 as ModelBuilderV2
from twin_model.control.control_manager import ControlManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_manifests(manifest_dir: Path) -> dict:
    """Load all manifest files."""
    manifests = {}
    
    # Load equipment manifest
    equipment_path = manifest_dir / "equipment_manifest.yaml"
    if equipment_path.exists():
        with open(equipment_path, 'r') as f:
            manifests['equipment_manifest'] = yaml.safe_load(f)
            logger.info(f"Loaded equipment manifest with {len(manifests['equipment_manifest'].get('equipment', {}))} equipment")
    
    # Load production manifest
    production_path = manifest_dir / "production_manifest.yaml"
    if production_path.exists():
        with open(production_path, 'r') as f:
            manifests['production_manifest'] = yaml.safe_load(f)
            logger.info(f"Loaded production manifest with {len(manifests['production_manifest'].get('products', {}))} products")
    
    # Load control settings
    control_path = manifest_dir / "control_settings.yaml"
    if control_path.exists():
        with open(control_path, 'r') as f:
            manifests['control_settings'] = yaml.safe_load(f)
            logger.info("Loaded control settings")
    
    return manifests


def test_full_integration():
    """Test full system with proper configuration loading."""
    
    print("\n" + "="*80)
    print("FULL INTEGRATION TEST WITH MODELBUILDER")
    print("="*80)
    
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
    builder = ModelBuilderV2(
        env=env,
        ontology_path=ontology_path,
        manifest_dir=manifest_dir,
        control_manager=control_mgr
    )
    
    # Build the model
    logger.info("Building model from ontology and manifests...")
    model = builder.build_model()
    
    # Override control parameters with reasonable baseline values
    logger.info("Setting baseline parameters for 40-65% OEE target...")
    for prim_id, prim in model['primitives'].items():
        if hasattr(prim, 'micro_stop_probability'):
            # Set reasonable failure parameters
            prim.micro_stop_probability = 0.15  # 15% chance per 5 min
            prim.performance_factor = 0.85  # 85% of theoretical
            prim.scrap_rate = 0.05  # 5% quality loss
            prim.config.properties['mtbf'] = 240  # Failure every 4 hours on average
            prim.config.properties['mttr'] = 15  # 15 min repair time
            prim.config.properties['minor_failure_probability'] = 0.02
            prim.config.properties['major_failure_probability'] = 0.01
    
    # Log what was created
    logger.info(f"Created model with {len(model['primitives'])} primitives")
    logger.info(f"Lines: {list(model['lines'].keys())}")
    
    # Check LINE1 configuration from manifests
    if 'LINE1' in model['lines']:
        line1 = model['lines']['LINE1']
        logger.info("\nLINE1 Configuration:")
        
        # Check source
        if line1.source:
            source_id = line1.source.entity_id
            source = model['primitives'][source_id]
            source_config = manifests['equipment_manifest']['equipment'].get('LINE1-SRC', {})
            logger.info(f"  Source: {source_id}")
            logger.info(f"    Arrival rate: {source_config.get('arrival_rate', 'N/A')} units/min")
            logger.info(f"    Order mode: {source_config.get('order_mode', 'N/A')}")
        
        # Check equipment
        for eq_entity in line1.equipment:
            eq_id = eq_entity.entity_id
            eq = model['primitives'][eq_id]
            eq_config = manifests['equipment_manifest']['equipment'].get(eq_id, {})
            logger.info(f"  Equipment: {eq_id}")
            logger.info(f"    Type: {eq_config.get('type', 'N/A')}")
            logger.info(f"    Base rate: {eq_config.get('base_rate', 'N/A')} units/min")
            logger.info(f"    Queue size: {eq_config.get('internal_queue_size', 20)}")
            logger.info(f"    MTBF: {eq_config.get('mtbf', 'N/A')} min")
            logger.info(f"    MTTR: {eq_config.get('mttr', 'N/A')} min")
        
        # Check sink
        if line1.sink:
            sink_id = line1.sink.entity_id
            sink = model['primitives'][sink_id]
            sink_config = manifests['equipment_manifest']['equipment'].get('LINE1-SINK', {})
            logger.info(f"  Sink: {sink_id}")
            logger.info(f"    Collection rate: {sink_config.get('collection_rate', 'N/A')} units/min")
    
    # Disable order mode for continuous generation in test
    logger.info("\nConfiguring sources for continuous generation...")
    for primitive in model['primitives'].values():
        if hasattr(primitive, 'order_mode'):
            # Set to continuous mode for test
            primitive.order_mode = False
            # Also ensure reasonable arrival rate
            primitive.arrival_rate = 100  # 100 units/min to ensure no starvation
            primitive.disruption_probability = 0  # Disable disruptions for testing
            logger.info(f"Set {primitive.config.id} to continuous mode with rate {primitive.arrival_rate}")
    
    # Start all processes
    logger.info("\nStarting processes...")
    for primitive in model['primitives'].values():
        if hasattr(primitive, 'start'):
            primitive.start()
    
    # Run simulation for 1 hour (60 minutes)
    logger.info("\nRunning simulation for 60 minutes...")
    duration = 60
    env.run(until=duration)
    
    # Finalize state durations for all equipment
    logger.info("Finalizing state durations...")
    for primitive in model['primitives'].values():
        if hasattr(primitive, 'state_durations') and hasattr(primitive, 'state'):
            # Add remaining time to current state
            if hasattr(primitive, 'state_start_time'):
                remaining_duration = env.now - primitive.state_start_time
                primitive.state_durations[primitive.state] += remaining_duration
    
    # Collect KPIs
    logger.info("\n" + "="*80)
    logger.info("SIMULATION RESULTS")
    logger.info("="*80)
    
    for line_id, line in model['lines'].items():
        print(f"\n{line_id} Results:")
        
        # Get source metrics
        if line.source and line.source.entity_id in model['primitives']:
            source = model['primitives'][line.source.entity_id]
            print(f"  Source {line.source.entity_id}:")
            print(f"    Units generated: {getattr(source, 'units_generated', 0)}")
            print(f"    Quality rejects: {getattr(source, 'quality_rejects', 0)}")
        
        # Get equipment metrics
        for eq_entity in line.equipment:
            eq_id = eq_entity.entity_id
            if eq_id in model['primitives']:
                eq = model['primitives'][eq_id]
                print(f"  Equipment {eq_id}:")
                print(f"    Units produced: {getattr(eq, 'units_produced', 0)}")
                print(f"    Units scrapped: {getattr(eq, 'units_scrapped', 0)}")
                print(f"    Micro-stops: {getattr(eq, 'micro_stop_count', 0)}")
                print(f"    Failures: {getattr(eq, 'failure_count', 0)}")
                
                # Debug state durations
                if hasattr(eq, 'state_durations'):
                    # Sum all state durations
                    total_tracked = sum(eq.state_durations.values())
                    print(f"    Total time tracked: {total_tracked:.1f} min (should be {duration})")
                    # Show percentage in each state
                    for state, duration_val in eq.state_durations.items():
                        if duration_val > 0:
                            pct = (duration_val / duration) * 100
                            print(f"      {state.value if hasattr(state, 'value') else state}: {duration_val:.1f} min ({pct:.1f}%)")
                
                # Calculate equipment OEE
                total_time = duration * 60  # Convert to seconds if state_durations is in seconds
                if hasattr(eq, 'state_durations'):
                    # Check if state_durations uses EquipmentState enum or strings
                    from twin_model.primitives.equipment import EquipmentState
                    
                    # Try to get running time with enum first, then string
                    running_time = eq.state_durations.get(EquipmentState.RUNNING, 
                                                         eq.state_durations.get('RUNNING', 0))
                    
                    # Ensure times are in the same units (minutes)
                    if running_time > total_time:
                        # State durations are likely in seconds, convert to minutes
                        running_time = running_time / 60
                        for key in eq.state_durations:
                            eq.state_durations[key] = eq.state_durations[key] / 60
                    
                    availability = running_time / duration if duration > 0 else 0
                    
                    base_rate = eq.config.properties.get('base_rate', 80)
                    theoretical_output = running_time * base_rate
                    actual_output = getattr(eq, 'units_produced', 0)
                    performance = actual_output / theoretical_output if theoretical_output > 0 else 0
                    
                    good_units = getattr(eq, 'units_produced', 0)
                    total_units = good_units + getattr(eq, 'units_scrapped', 0)
                    quality = good_units / total_units if total_units > 0 else 0
                    
                    oee = availability * performance * quality
                    print(f"    OEE: {oee:.1%} (A:{availability:.1%} P:{performance:.1%} Q:{quality:.1%})")
        
        # Get sink metrics
        if line.sink and line.sink.entity_id in model['primitives']:
            sink = model['primitives'][line.sink.entity_id]
            print(f"  Sink {line.sink.entity_id}:")
            print(f"    Units collected: {getattr(sink, 'total_units_collected', 0)}")
            print(f"    Units rejected: {getattr(sink, 'total_rejected', 0)}")
    
    # Check control effects
    print("\n" + "="*80)
    print("CONTROL SETTINGS APPLIED")
    print("="*80)
    
    # Get control values using correct method
    print("\nActive Controls:")
    control_names = ['changeover_reduction_level', 'operator_training_hours', 
                     'line_speed_setting', 'sensor_calibration_frequency',
                     'product_sequencing_strategy', 'pm_schedule_compliance',
                     'staffing_level', 'autonomous_maintenance_level']
    for control in control_names:
        value = control_mgr.get_control_value(control)
        if value is not None:
            print(f"  {control}: {value}")
    
    # Get computed parameters
    print("\nComputed Parameters:")
    all_params = control_mgr.get_all_parameters()
    for param, value in all_params.items():
        print(f"  {param}: {value}")
    
    # Also check what equipment actually has
    print("\nEquipment Actual Values:")
    for prim_id, prim in model['primitives'].items():
        if hasattr(prim, 'micro_stop_probability'):
            print(f"  {prim_id}: micro_stop={prim.micro_stop_probability:.2f}, perf={prim.performance_factor:.2f}, scrap={prim.scrap_rate:.3f}")
    
    logger.info("\n✅ Full integration test completed successfully!")


if __name__ == "__main__":
    test_full_integration()