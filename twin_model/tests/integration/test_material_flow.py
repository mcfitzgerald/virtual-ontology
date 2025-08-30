"""Test material flow improvements in equipment.

This test validates that the fixed equipment properly handles:
1. Material flow without double-queuing
2. Proper blocking/starved state detection
3. Achieving target OEE of 40-65%
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

import simpy

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from twin_model.primitives.base import PrimitiveConfig
from twin_model.primitives.equipment import EquipmentPrimitive, EquipmentState
from twin_model.primitives.source import SourcePrimitive, ArrivalPattern
from twin_model.primitives.sink import SinkPrimitive

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_test_line(env: simpy.Environment) -> Dict[str, Any]:
    """Create a simple production line for testing.

    Args:
        env: SimPy environment

    Returns:
        Dictionary containing primitives

    """
    primitives = {}

    # Create source
    source_config = PrimitiveConfig(
        id="TEST-SRC",
        type="SOURCE",
        metadata={"name": "Test Source"},
        properties={
            "arrival_rate": 100.0,  # High rate to avoid starvation
            "arrival_pattern": ArrivalPattern.CONSTANT.value,
        },
    )
    source = SourcePrimitive(env=env, config=source_config, arrival_rate=100.0, arrival_pattern=ArrivalPattern.CONSTANT)
    primitives["source"] = source

    # Create equipment chain
    equipment_ids = ["TEST-EQ1", "TEST-EQ2", "TEST-EQ3"]
    equipment_list = []

    for i, eq_id in enumerate(equipment_ids):
        eq_config = PrimitiveConfig(
            id=eq_id,
            type="EQUIPMENT",
            metadata={"name": f"Equipment {i + 1}"},
            properties={
                "base_rate": 80.0,  # Units per minute
                "performance_factor": 0.85,
                "scrap_rate": 0.05,
                "internal_queue_size": 10,
                "micro_stop_probability": 0.10,  # Lower for testing
                "mtbf": 300,
                "mttr": 10,
            },
        )

        equipment = EquipmentPrimitive(
            env=env,
            config=eq_config,
            base_rate=80.0,
            performance_factor=0.85,
            scrap_rate=0.05,
            micro_stop_probability=0.10,
        )

        equipment_list.append(equipment)
        primitives[eq_id] = equipment

    # Create sink
    sink_config = PrimitiveConfig(
        id="TEST-SINK", type="SINK", metadata={"name": "Test Sink"}, properties={"collection_rate": 1000.0}
    )
    sink = SinkPrimitive(env=env, config=sink_config, collection_rate=1000.0)
    primitives["sink"] = sink

    # Connect equipment chain
    for i in range(len(equipment_list) - 1):
        equipment_list[i].connect_to(equipment_list[i + 1])
        logger.info(f"Connected {equipment_list[i].config.id} → {equipment_list[i + 1].config.id}")

    # Connect source to first equipment
    source.set_downstream(equipment_list[0])
    logger.info(f"Connected source → {equipment_list[0].config.id}")

    # Connect last equipment to sink (via sink pulling from output queue)
    sink.set_upstream(equipment_list[-1])
    logger.info(f"Connected {equipment_list[-1].config.id} → sink")

    return primitives


def test_material_flow():
    """Test the improved material flow."""
    print("\n" + "=" * 80)
    print("MATERIAL FLOW TEST")
    print("=" * 80)

    # Create environment
    env = simpy.Environment()

    # Create test line
    logger.info("Creating test production line...")
    primitives = create_test_line(env)

    # Start all processes
    logger.info("Starting all processes...")
    for name, primitive in primitives.items():
        if hasattr(primitive, "start"):
            primitive.start()
            logger.info(f"Started {name}")

    # Run for 60 minutes
    duration = 60
    logger.info(f"\nRunning simulation for {duration} minutes...")
    env.run(until=duration)

    # Finalize state durations
    logger.info("Finalizing state durations...")
    for name, primitive in primitives.items():
        if hasattr(primitive, "state_durations") and hasattr(primitive, "state"):
            if hasattr(primitive, "state_start_time"):
                remaining_duration = env.now - primitive.state_start_time
                primitive.state_durations[primitive.state] += remaining_duration

    # Collect and display results
    print("\n" + "=" * 80)
    print("SIMULATION RESULTS")
    print("=" * 80)

    # Source metrics
    source = primitives["source"]
    print("\nSource:")
    print(f"  Units generated: {source.units_generated}")

    # Equipment metrics
    for eq_id in ["TEST-EQ1", "TEST-EQ2", "TEST-EQ3"]:
        eq = primitives[eq_id]
        print(f"\n{eq_id}:")
        print(f"  Units produced: {eq.units_produced}")
        print(f"  Units scrapped: {eq.units_scrapped}")
        print(f"  Failures: {eq.failure_count} (micro: {eq.micro_stop_count})")

        # State durations
        total_time = duration
        for state, state_duration in eq.state_durations.items():
            if state_duration > 0:
                pct = (state_duration / total_time) * 100
                print(f"  {state.value}: {state_duration:.1f} min ({pct:.1f}%)")

        # Calculate OEE
        stats = eq.get_statistics()
        print(
            f"  OEE: {stats['oee']:.1%} (A:{stats['availability']:.1%} "
            f"P:{stats['performance']:.1%} Q:{stats['quality']:.1%})"
        )

    # Sink metrics
    sink = primitives["sink"]
    print("\nSink:")
    print(f"  Units collected: {sink.total_units_collected}")

    # Check if we achieved target OEE
    print("\n" + "=" * 80)
    print("OEE ANALYSIS")
    print("=" * 80)

    avg_oee = 0
    for eq_id in ["TEST-EQ1", "TEST-EQ2", "TEST-EQ3"]:
        stats = primitives[eq_id].get_statistics()
        avg_oee += stats["oee"]
    avg_oee /= 3

    print(f"\nAverage OEE across equipment: {avg_oee:.1%}")

    if 0.40 <= avg_oee <= 0.65:
        print("✅ Target OEE achieved (40-65%)")
    else:
        print(f"❌ OEE outside target range (got {avg_oee:.1%}, want 40-65%)")

    # Check material flow efficiency
    print("\n" + "=" * 80)
    print("MATERIAL FLOW ANALYSIS")
    print("=" * 80)

    total_starved_time = 0
    total_blocked_time = 0

    for eq_id in ["TEST-EQ1", "TEST-EQ2", "TEST-EQ3"]:
        eq = primitives[eq_id]
        starved = eq.state_durations.get(EquipmentState.STARVED, 0)
        blocked = eq.state_durations.get(EquipmentState.BLOCKED, 0)
        total_starved_time += starved
        total_blocked_time += blocked

    avg_starved = (total_starved_time / 3) / duration * 100
    avg_blocked = (total_blocked_time / 3) / duration * 100

    print(f"\nAverage time STARVED: {avg_starved:.1f}%")
    print(f"Average time BLOCKED: {avg_blocked:.1f}%")

    if avg_starved < 10 and avg_blocked < 10:
        print("✅ Material flow is efficient")
    else:
        print("⚠️ Material flow issues detected")

    return avg_oee


if __name__ == "__main__":
    oee = test_material_flow()

    # Exit with success if OEE is in target range
    if 0.40 <= oee <= 0.65:
        sys.exit(0)
    else:
        sys.exit(1)
