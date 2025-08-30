"""Simple test to verify material flow."""

import simpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from twin_model.primitives.source import SourcePrimitive
from twin_model.primitives.equipment import EquipmentPrimitive
from twin_model.primitives.sink import SinkPrimitive
from twin_model.primitives.base import PrimitiveConfig


def test_simple_flow():
    """Test a simple source -> equipment -> sink flow."""
    env = simpy.Environment()

    # Create simple configs
    source_config = PrimitiveConfig(
        id="SOURCE",
        type="SourcePrimitive",
        properties={
            "order_mode": False,  # Continuous
            "arrival_rate": 60.0,  # 60/min = 1/sec
            "quality_rate": 1.0,  # No quality issues
            "disruption_probability": 0.0,  # No disruptions
        },
    )

    equipment_config = PrimitiveConfig(
        id="EQUIPMENT",
        type="EquipmentPrimitive",
        properties={
            "base_rate": 60.0,
            "internal_queue_size": 10,
            "performance_factor": 1.0,
            "scrap_rate": 0.0,
            "micro_stop_probability": 0.0,
            "warmup_period": 0.0,
        },
    )

    sink_config = PrimitiveConfig(id="SINK", type="SinkPrimitive", properties={})

    # Create primitives
    source = SourcePrimitive(env, source_config)
    equipment = EquipmentPrimitive(env, equipment_config)
    sink = SinkPrimitive(env, sink_config)

    # Connect them
    source.set_downstream(equipment.input_queue)
    equipment.downstream_equipment = sink
    sink.set_upstream(equipment.output_queue)

    # Start processes
    source.start()
    equipment.start()
    sink.start()

    # Run for 5 minutes
    env.run(until=5)

    print(f"Time: {env.now}")
    print(f"Source generated: {source.units_generated}")
    print(f"Equipment produced: {equipment.units_produced}")
    print(f"Equipment scrapped: {equipment.units_scrapped}")
    print(f"Sink collected: {sink.total_units_collected}")

    # Check material flow
    assert source.units_generated > 0, "Source should generate units"
    assert equipment.units_produced > 0, "Equipment should produce units"
    assert sink.total_units_collected > 0, "Sink should collect units"

    print("\n✓ Simple flow test passed!")


if __name__ == "__main__":
    test_simple_flow()
