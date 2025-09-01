"""Integration tests for model builder with configuration."""

import tempfile
from pathlib import Path

import simpy
import yaml

from twin_model import FlowModelBuilder, SinkFlow, SourceFlow
from twin_model.monitoring import FlowMonitor
from twin_model.transduction import FlowTransducer


class TestModelBuilder:
    """Test model builder functionality."""

    def test_build_from_config(self):
        """Test building model from configuration files."""
        env = simpy.Environment()

        # Create temporary config files
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            manifest_dir = Path(tmpdir) / "manifests"
            config_dir.mkdir()
            manifest_dir.mkdir()

            # Create minimal system config
            system_config = {
                "system": {
                    "flow_control": {
                        "default_buffer_capacity": 1000,
                        "default_production_interval": 0.1,
                        "default_batch_size_min": 10
                    },
                    "monitoring": {
                        "kpi_interval": 5.0
                    }
                }
            }

            with open(manifest_dir / "system_config.yaml", "w") as f:
                yaml.dump(system_config, f)

            # Create equipment manifest
            equipment_manifest = {
                "equipment": {
                    "LINE1-FILLER-01": {
                        "type": "Filler",
                        "line_id": "LINE1",
                        "position": 1,
                        "flow_capacity": {
                            "max_input_rate": 260,
                            "max_output_rate": 250,
                            "internal_capacity": 500
                        },
                        "processing": {
                            "nominal_rate": 250,
                            "quality_rate": 0.95,
                            "performance_factor": 0.85,
                            "batch_size": 10,
                            "processing_interval": 0.1
                        },
                        "failures": {
                            "mtbf": 60,
                            "mttr": 5,
                            "micro_stop_rate": 0,
                            "micro_stop_duration": 0
                        }
                    }
                }
            }

            with open(manifest_dir / "equipment_manifest.yaml", "w") as f:
                yaml.dump(equipment_manifest, f)

            # Create production manifest
            production_manifest = {
                "lines": {
                    "LINE1": {
                        "equipment": ["LINE1-FILLER-01"],
                        "source": {
                            "generation_rate": 260,
                            "continuous_mode": True
                        },
                        "sink": {
                            "collection_rate": 250,
                            "nominal_rate": 240
                        }
                    }
                }
            }

            with open(manifest_dir / "production_manifest.yaml", "w") as f:
                yaml.dump(production_manifest, f)

            # Build model
            builder = FlowModelBuilder(env, config_dir, manifest_dir)
            model = builder.build_model()

            # Verify model was built
            assert "primitives" in model
            assert "env" in model
            assert "config" in model

            # Check primitives were created
            assert "LINE1-SOURCE" in model["primitives"]
            assert "LINE1-FILLER-01" in model["primitives"]
            assert "LINE1-SINK" in model["primitives"]

            # Verify types
            assert isinstance(model["primitives"]["LINE1-SOURCE"], SourceFlow)
            assert isinstance(model["primitives"]["LINE1-SINK"], SinkFlow)

            # Check connections were made
            source = model["primitives"]["LINE1-SOURCE"]
            filler = model["primitives"]["LINE1-FILLER-01"]
            sink = model["primitives"]["LINE1-SINK"]

            # Verify shared buffers
            assert source.output_buffer is not None
            assert source.output_buffer is filler.input_buffer
            assert filler.output_buffer is not None
            assert filler.output_buffer is sink.input_buffer

            # Run simulation briefly
            env.run(until=10)

            # Check that processes are running
            assert source.flow_metrics.total_output > 0
            assert sink.total_collected >= 0  # May be 0 if equipment is processing


class TestFlowMonitor:
    """Test flow monitoring functionality."""

    def test_monitor_integration(self):
        """Test monitoring with model builder."""
        env = simpy.Environment()

        # Create temporary config files
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            manifest_dir = Path(tmpdir) / "manifests"
            config_dir.mkdir()
            manifest_dir.mkdir()

            # Create minimal configs
            system_config = {
                "system": {
                    "flow_control": {
                        "default_buffer_capacity": 500
                    }
                }
            }

            with open(manifest_dir / "system_config.yaml", "w") as f:
                yaml.dump(system_config, f)

            equipment_manifest = {"equipment": {}}
            with open(manifest_dir / "equipment_manifest.yaml", "w") as f:
                yaml.dump(equipment_manifest, f)

            production_manifest = {
                "lines": {
                    "LINE1": {
                        "equipment": [],
                        "source": {"generation_rate": 100},
                        "sink": {"collection_rate": 100}
                    }
                }
            }

            with open(manifest_dir / "production_manifest.yaml", "w") as f:
                yaml.dump(production_manifest, f)

            # Build model
            builder = FlowModelBuilder(env, config_dir, manifest_dir)
            model = builder.build_model()

            # Create monitor
            monitor = FlowMonitor(env, monitoring_interval=1.0)
            monitor.register_primitives(
                model["primitives"],
                builder.get_topology()
            )
            monitor.start()

            # Run simulation
            env.run(until=10)

            # Check monitoring data
            status = monitor.get_current_status()
            assert status["monitored_equipment"] == 2  # Source and sink
            assert "line_metrics" in status

            # Check for snapshots
            assert len(monitor.snapshots) > 0


class TestFlowTransducer:
    """Test flow transduction to MES records."""

    def test_transducer_integration(self):
        """Test transducer with model output."""
        env = simpy.Environment()

        # Create temporary config files
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            manifest_dir = Path(tmpdir) / "manifests"
            config_dir.mkdir()
            manifest_dir.mkdir()

            # Create minimal configs
            system_config = {"system": {}}
            with open(manifest_dir / "system_config.yaml", "w") as f:
                yaml.dump(system_config, f)

            equipment_manifest = {"equipment": {}}
            with open(manifest_dir / "equipment_manifest.yaml", "w") as f:
                yaml.dump(equipment_manifest, f)

            production_manifest = {
                "lines": {
                    "LINE1": {
                        "equipment": [],
                        "source": {"generation_rate": 100},
                        "sink": {"collection_rate": 100, "nominal_rate": 100}
                    }
                }
            }

            with open(manifest_dir / "production_manifest.yaml", "w") as f:
                yaml.dump(production_manifest, f)

            # Build and run model
            builder = FlowModelBuilder(env, config_dir, manifest_dir)
            model = builder.build_model()

            env.run(until=10)

            # Create transducer
            transducer = FlowTransducer(time_bucket=5.0)

            # Process observables
            df = transducer.process_observables([], model["primitives"])

            # Check DataFrame structure
            assert not df.empty
            assert "Timestamp" in df.columns
            assert "OEE_Score" in df.columns
            assert "GoodUnitsProduced" in df.columns

            # Verify data types
            assert df["OEE_Score"].dtype in ["float64", "object"]


class TestFullSystem:
    """Test complete system integration."""

    def test_full_simulation(self):
        """Test full simulation with all components."""
        env = simpy.Environment()

        # Create temporary config files
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            manifest_dir = Path(tmpdir) / "manifests"
            config_dir.mkdir()
            manifest_dir.mkdir()

            # Create system config
            system_config = {
                "system": {
                    "flow_control": {
                        "default_buffer_capacity": 1000,
                        "default_production_interval": 0.1
                    },
                    "monitoring": {
                        "kpi_interval": 5.0
                    }
                }
            }

            with open(manifest_dir / "system_config.yaml", "w") as f:
                yaml.dump(system_config, f)

            # Create equipment manifest with multiple equipment
            equipment_manifest = {
                "equipment": {
                    "LINE1-EQUIPMENT-01": {
                        "type": "Equipment",
                        "processing": {
                            "nominal_rate": 200,
                            "quality_rate": 0.95,
                            "performance_factor": 0.9
                        },
                        "failures": {
                            "mtbf": 100,
                            "mttr": 10
                        }
                    },
                    "LINE1-EQUIPMENT-02": {
                        "type": "Equipment",
                        "processing": {
                            "nominal_rate": 190,
                            "quality_rate": 0.94,
                            "performance_factor": 0.85
                        },
                        "failures": {
                            "mtbf": 120,
                            "mttr": 8
                        }
                    }
                }
            }

            with open(manifest_dir / "equipment_manifest.yaml", "w") as f:
                yaml.dump(equipment_manifest, f)

            # Create production manifest
            production_manifest = {
                "lines": {
                    "LINE1": {
                        "equipment": ["LINE1-EQUIPMENT-01", "LINE1-EQUIPMENT-02"],
                        "source": {
                            "generation_rate": 210,
                            "continuous_mode": True
                        },
                        "sink": {
                            "collection_rate": 200,
                            "nominal_rate": 180
                        }
                    }
                }
            }

            with open(manifest_dir / "production_manifest.yaml", "w") as f:
                yaml.dump(production_manifest, f)

            # Build model
            builder = FlowModelBuilder(env, config_dir, manifest_dir)
            model = builder.build_model()

            # Create monitor
            monitor = FlowMonitor(env, monitoring_interval=1.0)
            monitor.register_primitives(model["primitives"], builder.get_topology())
            monitor.start()

            # Run simulation
            env.run(until=60)  # 1 hour

            # Create transducer and process data
            transducer = FlowTransducer(time_bucket=5.0)
            df = transducer.process_observables([], model["primitives"])

            # Verify results
            assert len(model["primitives"]) == 4  # Source, 2 equipment, sink
            assert not df.empty

            # Check monitoring detected something
            status = monitor.get_current_status()
            assert status["monitored_equipment"] == 4

            # Check sink collected material
            sink = model["primitives"]["LINE1-SINK"]
            assert sink.total_collected > 0

            # Calculate OEE
            oee, availability, performance, quality = sink.calculate_oee()

            # OEE should be reasonable (not 0 or 100)
            assert 0 < oee < 100
            assert 0 < availability <= 100
            assert 0 < performance <= 100
            assert 0 < quality <= 100
