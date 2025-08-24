"""Verify production line connections are properly wired."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import simpy
import random
import numpy as np
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.primitives.equipment import EquipmentPrimitive
from twin_model.primitives.buffer import BufferPrimitive
from twin_model.primitives.source import SourcePrimitive
from twin_model.primitives.sink import SinkPrimitive


def verify_line_connections(builder: OntologyDrivenModelBuilder) -> bool:
    """Verify all equipment and buffers have proper connections.
    
    Args:
        builder: The model builder with primitives
        
    Returns:
        True if all connections are valid
    """
    print("\n" + "="*60)
    print("PRODUCTION LINE CONNECTION VERIFICATION")
    print("="*60)
    
    issues = []
    connection_summary = []
    
    # Check each primitive
    for prim_id, primitive in builder.primitives.items():
        if isinstance(primitive, EquipmentPrimitive):
            # Equipment should have upstream and downstream
            upstream_id = primitive.upstream.config.id if primitive.upstream else "None"
            downstream_id = primitive.downstream.config.id if primitive.downstream else "None"
            
            connection_summary.append(
                f"Equipment {prim_id}: {upstream_id} → [{prim_id}] → {downstream_id}"
            )
            
            if not primitive.upstream:
                issues.append(f"{prim_id}: Missing upstream connection")
            if not primitive.downstream:
                issues.append(f"{prim_id}: Missing downstream connection")
                
        elif isinstance(primitive, BufferPrimitive):
            # Buffers should be connected in the flow
            connection_summary.append(f"Buffer {prim_id}: capacity={primitive.capacity}")
            
        elif isinstance(primitive, SourcePrimitive):
            # Sources should feed into something
            connection_summary.append(f"Source {prim_id}: arrival_rate={primitive.arrival_rate}")
            
        elif isinstance(primitive, SinkPrimitive):
            # Sinks should receive from something
            connection_summary.append(f"Sink {prim_id}: target={primitive.target_throughput}")
    
    # Print connection summary
    print("\nConnection Summary:")
    print("-" * 40)
    
    # Group by line
    lines = {}
    for summary in sorted(connection_summary):
        line_id = "DEFAULT"
        if "LINE1" in summary:
            line_id = "LINE1"
        elif "LINE2" in summary:
            line_id = "LINE2"
        elif "LINE3" in summary:
            line_id = "LINE3"
        
        if line_id not in lines:
            lines[line_id] = []
        lines[line_id].append(summary)
    
    for line_id, summaries in sorted(lines.items()):
        print(f"\n{line_id}:")
        for summary in summaries:
            print(f"  {summary}")
    
    # Report issues
    if issues:
        print("\n⚠ CONNECTION ISSUES FOUND:")
        print("-" * 40)
        for issue in issues:
            print(f"  - {issue}")
        print(f"\nTotal issues: {len(issues)}")
        return False
    else:
        print("\n✓ All equipment properly connected!")
        return True


def test_production_flow(builder: OntologyDrivenModelBuilder, env: simpy.Environment) -> None:
    """Test actual production flow through a line.
    
    Args:
        builder: The model builder with primitives
        env: SimPy environment
    """
    print("\n" + "="*60)
    print("PRODUCTION FLOW TEST (5 minute simulation)")
    print("="*60)
    
    # Find a filler to monitor
    filler = None
    filler_id = None
    
    for prim_id, primitive in builder.primitives.items():
        if isinstance(primitive, EquipmentPrimitive) and 'FIL' in prim_id:
            filler = primitive
            filler_id = prim_id
            break
    
    if filler:
        print(f"\nMonitoring {filler_id}:")
        print(f"  Base rate: {filler.base_rate} units/min")
        print(f"  Expected in 5 min: {filler.base_rate * 5} units")
        print(f"  Upstream: {filler.upstream.config.id if filler.upstream else 'None'}")
        print(f"  Downstream: {filler.downstream.config.id if filler.downstream else 'None'}")
        
        # Run for 5 minutes
        env.run(until=5)
        
        print(f"\nAfter 5 minutes:")
        print(f"  Units produced: {filler.units_produced}")
        print(f"  Units scrapped: {filler.units_scrapped}")
        print(f"  Total processed: {filler.units_produced + filler.units_scrapped}")
        
        efficiency = ((filler.units_produced + filler.units_scrapped) / (filler.base_rate * 5)) * 100
        print(f"  Production efficiency: {efficiency:.1f}%")
        
        if efficiency < 80:
            print(f"\n⚠ WARNING: Low efficiency detected ({efficiency:.1f}%)")
            print("  Possible causes:")
            print("  - Connections not properly functioning")
            print("  - Upstream starvation")
            print("  - Downstream blocking")
        else:
            print(f"\n✓ Good production efficiency: {efficiency:.1f}%")
    else:
        print("⚠ No filler equipment found to monitor")


def main():
    """Main verification routine."""
    print("Starting connection verification...")
    
    # Set seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    # Build model
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    builder = OntologyDrivenModelBuilder(
        ontology_path=ontology_path,
        manifest_dir=manifest_dir
    )
    
    # Create environment and build model
    env = simpy.Environment()
    model = builder.build_model(env)
    
    # Verify connections
    connections_valid = verify_line_connections(builder)
    
    if connections_valid:
        # Test production flow
        test_production_flow(builder, env)
    else:
        print("\n⚠ Skipping production flow test due to connection issues")
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    
    return connections_valid


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)