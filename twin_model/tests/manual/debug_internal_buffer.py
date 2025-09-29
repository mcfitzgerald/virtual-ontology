"""Debug internal buffer issue."""

import logging
from pathlib import Path

import simpy

from twin_model.ontology_model_builder import OntologyModelBuilder

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")


def debug_internal_buffer():
    """Debug internal buffer."""
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

    filler = primitives["LINE1-FIL"]

    print("\nLINE1-FIL attributes:")
    print(f"  Has input_buffer: {hasattr(filler, 'input_buffer')}")
    print(f"  Has output_buffer: {hasattr(filler, 'output_buffer')}")
    print(f"  Has internal_buffer: {hasattr(filler, 'internal_buffer')}")

    if hasattr(filler, "internal_buffer"):
        print(f"  Internal buffer capacity: {filler.internal_buffer.capacity}")
        print(f"  Internal buffer level: {filler.internal_buffer.level}")
    else:
        print("  ❌ NO INTERNAL BUFFER!")

    print("\n  Processing parameters:")
    print(f"    Batch size: {filler.processing.batch_size}")
    print(f"    Nominal rate: {filler.processing.nominal_rate}")
    print(f"    Processing interval: {filler.processing.processing_interval}")


if __name__ == "__main__":
    debug_internal_buffer()
