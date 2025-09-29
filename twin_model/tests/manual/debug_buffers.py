"""Debug script to check buffer connections."""

import logging
from pathlib import Path

import simpy

from twin_model.ontology_model_builder import OntologyModelBuilder

logging.basicConfig(level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s")


def debug_buffers():
    """Debug buffer connections and levels."""
    env = simpy.Environment()

    # Define paths
    project_root = Path(__file__).parent
    ontology_path = project_root / "ontology" / "filling_line_ontology.yaml"
    manifest_path = project_root / "manifests" / "equipment_instances.yaml"
    config_path = project_root / "config" / "tunable_parameters.yaml"

    # Build model
    builder = OntologyModelBuilder(
        env=env, ontology_path=ontology_path, manifest_path=manifest_path, config_path=config_path
    )

    model = builder.build_model()
    primitives = model["primitives"]

    print("\n" + "=" * 60)
    print("BUFFER CONNECTIONS BEFORE SIMULATION")
    print("=" * 60)

    for eq_id in ["LINE1-SOURCE", "LINE1-FIL", "LINE1-PCK", "LINE1-PAL", "LINE1-SINK"]:
        equipment = primitives[eq_id]
        print(f"\n{eq_id}:")

        if hasattr(equipment, "input_buffer") and equipment.input_buffer is not None:
            print(f"  Input buffer: {id(equipment.input_buffer)}")
            print(f"    Capacity: {equipment.input_buffer.capacity}")
            print(f"    Level: {equipment.input_buffer.level}")
        else:
            print("  No input buffer")

        if hasattr(equipment, "output_buffer") and equipment.output_buffer is not None:
            print(f"  Output buffer: {id(equipment.output_buffer)}")
            print(f"    Capacity: {equipment.output_buffer.capacity}")
            print(f"    Level: {equipment.output_buffer.level}")
        else:
            print("  No output buffer")

    # Check if buffers are actually shared
    print("\n" + "=" * 60)
    print("BUFFER SHARING CHECK")
    print("=" * 60)

    source = primitives["LINE1-SOURCE"]
    filler = primitives["LINE1-FIL"]

    if hasattr(source, "output_buffer") and hasattr(filler, "input_buffer"):
        if id(source.output_buffer) == id(filler.input_buffer):
            print("✅ Source output and Filler input share same buffer")
        else:
            print("❌ Source output and Filler input are DIFFERENT buffers!")
            print(f"   Source output: {id(source.output_buffer)}")
            print(f"   Filler input: {id(filler.input_buffer)}")

    # Run for a tiny bit
    print("\n" + "=" * 60)
    print("RUNNING FOR 0.5 MINUTES")
    print("=" * 60)

    env.run(until=0.5)

    print("\n" + "=" * 60)
    print("BUFFER LEVELS AFTER 0.5 MINUTES")
    print("=" * 60)

    for eq_id in ["LINE1-SOURCE", "LINE1-FIL"]:
        equipment = primitives[eq_id]
        print(f"\n{eq_id}:")
        print(f"  State: {equipment.current_state}")

        if hasattr(equipment, "input_buffer") and equipment.input_buffer is not None:
            print(f"  Input buffer level: {equipment.input_buffer.level:.2f}")

        if hasattr(equipment, "output_buffer") and equipment.output_buffer is not None:
            print(f"  Output buffer level: {equipment.output_buffer.level:.2f}")


if __name__ == "__main__":
    debug_buffers()
