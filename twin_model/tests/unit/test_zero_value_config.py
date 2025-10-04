"""Test that zero values in config properly override defaults.

This test verifies the fix for the zero-value bug where explicit config
values of 0 were treated as falsy and would fall through to default values.
"""

import tempfile
from pathlib import Path

import pytest
import simpy
import yaml

from twin_model import OntologyModelBuilder


@pytest.fixture
def temp_config_files():
    """Create temporary configuration files for testing."""
    # Minimal ontology matching actual structure
    ontology = {
        "metadata": {"name": "Test Ontology", "version": "1.0.0"},
        "tbox": {
            "types": {
                "FillingStation": {
                    "description": "Test filler",
                    "maps_to": {
                        "framework_primitive": "EquipmentFlow",
                    },
                }
            }
        },
    }

    # Minimal manifest
    manifest = {
        "metadata": {"name": "Test Manifest", "version": "1.0.0"},
        "equipment": {
            "TEST-FIL": {
                "type": "FillingStation",
                "position": 1,
                "line_id": "LINE1",
            },
        },
    }

    # Config with ZERO values (this is what we're testing!)
    config = {
        "metadata": {"name": "Test Config", "version": "1.0.0"},
        "defaults": {
            "equipment": {
                "nominal_rate": 100.0,  # Default
                "quality_rate": 0.95,  # Default
                "performance_factor": 0.85,  # Default
                "mtbf": 120.0,  # Default
                "mttr": 30.0,  # Default
            },
            "flow_capacity": {
                "equipment": {
                    "max_input_rate": 150.0,
                    "max_output_rate": 150.0,
                    "internal_capacity": 1000.0,
                }
            },
        },
        "equipment_parameters": {
            "TEST-FIL": {
                "nominal_rate": 0.01,  # Very small value - should NOT fall through to default!
                "quality_rate": 0.01,  # Very small value - should NOT fall through!
                "performance_factor": 0.01,  # Very small value - should NOT fall through!
                "mtbf": 0.01,  # Small MTBF value
                "mttr": 0.01,  # Small MTTR value
            }
        },
    }

    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        ont_path = Path(tmpdir) / "ontology.yaml"
        man_path = Path(tmpdir) / "manifest.yaml"
        cfg_path = Path(tmpdir) / "config.yaml"

        with open(ont_path, "w") as f:
            yaml.dump(ontology, f)
        with open(man_path, "w") as f:
            yaml.dump(manifest, f)
        with open(cfg_path, "w") as f:
            yaml.dump(config, f)

        yield {"ontology": ont_path, "manifest": man_path, "config": cfg_path}


def test_zero_nominal_rate(temp_config_files):
    """Test that nominal_rate=0.01 is honored, not overridden by default."""
    env = simpy.Environment()
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=temp_config_files["ontology"],
        manifest_path=temp_config_files["manifest"],
        config_path=temp_config_files["config"],
    )

    model = builder.build_model()
    equipment = model["primitives"]["TEST-FIL"]

    # The bug would cause this to be 100.0 (the default)
    # With the fix, it should be 0.01 (the explicit config value)
    assert (
        equipment.processing.nominal_rate == 0.01
    ), f"Expected 0.01, got {equipment.processing.nominal_rate}. Small value was not honored!"


def test_zero_quality_rate(temp_config_files):
    """Test that quality_rate=0.01 is honored (very low quality for testing)."""
    env = simpy.Environment()
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=temp_config_files["ontology"],
        manifest_path=temp_config_files["manifest"],
        config_path=temp_config_files["config"],
    )

    model = builder.build_model()
    equipment = model["primitives"]["TEST-FIL"]

    assert (
        equipment.processing.quality_rate == 0.01
    ), f"Expected 0.01, got {equipment.processing.quality_rate}. Small value was not honored!"


def test_zero_performance_factor(temp_config_files):
    """Test that performance_factor=0.01 is honored (very low performance)."""
    env = simpy.Environment()
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=temp_config_files["ontology"],
        manifest_path=temp_config_files["manifest"],
        config_path=temp_config_files["config"],
    )

    model = builder.build_model()
    equipment = model["primitives"]["TEST-FIL"]

    assert (
        equipment.processing.performance_factor == 0.01
    ), f"Expected 0.01, got {equipment.processing.performance_factor}. Small value was not honored!"


def test_zero_mtbf(temp_config_files):
    """Test that mtbf=0.01 is honored (very frequent failures)."""
    env = simpy.Environment()
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=temp_config_files["ontology"],
        manifest_path=temp_config_files["manifest"],
        config_path=temp_config_files["config"],
    )

    model = builder.build_model()
    equipment = model["primitives"]["TEST-FIL"]

    assert equipment.failures.mtbf == 0.01, f"Expected 0.01, got {equipment.failures.mtbf}. Small value was not honored!"


def test_zero_mttr(temp_config_files):
    """Test that mttr=0.01 is honored (very fast repair)."""
    env = simpy.Environment()
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=temp_config_files["ontology"],
        manifest_path=temp_config_files["manifest"],
        config_path=temp_config_files["config"],
    )

    model = builder.build_model()
    equipment = model["primitives"]["TEST-FIL"]

    assert equipment.failures.mttr == 0.01, f"Expected 0.01, got {equipment.failures.mttr}. Small value was not honored!"


def test_positive_values_still_work(temp_config_files):
    """Verify that positive values continue to work as expected."""
    # Modify config to have positive values
    with open(temp_config_files["config"]) as f:
        config = yaml.safe_load(f)

    config["equipment_parameters"]["TEST-FIL"] = {
        "nominal_rate": 50.0,
        "quality_rate": 0.98,
        "performance_factor": 0.92,
    }

    with open(temp_config_files["config"], "w") as f:
        yaml.dump(config, f)

    env = simpy.Environment()
    builder = OntologyModelBuilder(
        env=env,
        ontology_path=temp_config_files["ontology"],
        manifest_path=temp_config_files["manifest"],
        config_path=temp_config_files["config"],
    )

    model = builder.build_model()
    equipment = model["primitives"]["TEST-FIL"]

    assert equipment.processing.nominal_rate == 50.0
    assert equipment.processing.quality_rate == 0.98
    assert equipment.processing.performance_factor == 0.92
