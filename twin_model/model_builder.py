"""Model builder for creating flow-based simulation models from configuration.

This module provides the FlowModelBuilder class that constructs complete
simulation models from YAML configuration files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import simpy
import yaml

from .primitives import (
    EquipmentFlow,
    FailureParameters,
    FlowCapacity,
    ProcessingParameters,
    ProductionOrder,
    SinkFlow,
    SourceFlow,
)

logger = logging.getLogger(__name__)


class FlowModelBuilder:
    """Builds flow-based simulation model from configuration."""

    def __init__(
        self,
        env: simpy.Environment,
        config_dir: Path,
        manifest_dir: Path
    ) -> None:
        """Initialize model builder.

        Args:
            env: SimPy environment
            config_dir: Directory containing configuration files
            manifest_dir: Directory containing manifest files
        """
        self.env = env
        self.config_dir = Path(config_dir)
        self.manifest_dir = Path(manifest_dir)

        # Load configurations
        self.config = self._load_config()
        self.manifests = self._load_manifests()

        # Primitive storage
        self.primitives: dict[str, Any] = {}
        self.connections: list[dict[str, str]] = []

    def _load_config(self) -> dict[str, Any]:
        """Load system configuration from YAML files.

        Returns:
            Merged configuration dictionary
        """
        config = {}

        # Load system config
        system_config_path = self.manifest_dir / "system_config.yaml"
        if system_config_path.exists():
            with open(system_config_path) as f:
                system_config = yaml.safe_load(f)
                if system_config:
                    config.update(system_config)

        # Load twin model config
        model_config_path = self.config_dir / "twin_model.yaml"
        if model_config_path.exists():
            with open(model_config_path) as f:
                model_config = yaml.safe_load(f)
                if model_config:
                    config.update(model_config)

        logger.info(f"Loaded configuration with {len(config)} sections")
        return config

    def _load_manifests(self) -> dict[str, Any]:
        """Load equipment and production manifests from YAML files.

        Returns:
            Dictionary of manifests
        """
        manifests = {}

        # Load equipment manifest
        equipment_path = self.manifest_dir / "equipment_manifest.yaml"
        if equipment_path.exists():
            with open(equipment_path) as f:
                equipment_manifest = yaml.safe_load(f)
                if equipment_manifest:
                    manifests["equipment"] = equipment_manifest.get("equipment", {})

        # Load production manifest
        production_path = self.manifest_dir / "production_manifest.yaml"
        if production_path.exists():
            with open(production_path) as f:
                production_manifest = yaml.safe_load(f)
                if production_manifest:
                    manifests["lines"] = production_manifest.get("lines", {})
                    manifests["orders"] = production_manifest.get("orders", {})

        logger.info(f"Loaded manifests: {list(manifests.keys())}")
        return manifests

    def build_model(self) -> dict[str, Any]:
        """Build complete simulation model.

        Returns:
            Dictionary containing primitives, environment, and configuration
        """
        logger.info("Building flow model from configuration")

        # Create primitives for each production line
        for line_id, line_config in self.manifests.get("lines", {}).items():
            logger.info(f"Building line: {line_id}")
            self._build_line(line_id, line_config)

        # Wire connections between primitives
        self._wire_connections()

        # Load production orders if any
        self._load_orders()

        # Start all processes
        self._start_processes()

        logger.info(f"Model built with {len(self.primitives)} primitives")

        return {
            "primitives": self.primitives,
            "env": self.env,
            "config": self.config,
            "connections": self.connections
        }

    def _build_line(self, line_id: str, line_config: dict[str, Any]) -> None:
        """Build a production line from configuration.

        Args:
            line_id: Line identifier
            line_config: Line configuration dictionary
        """
        # Create source
        source_id = f"{line_id}-SOURCE"
        self._create_source(source_id, line_id, line_config.get("source", {}))

        # Create equipment based on equipment list
        equipment_list = line_config.get("equipment", [])
        for equipment_id in equipment_list:
            if equipment_id in self.manifests.get("equipment", {}):
                equipment_config = self.manifests["equipment"][equipment_id]
                self._create_equipment(equipment_id, line_id, equipment_config)
            else:
                logger.warning(f"Equipment {equipment_id} not found in manifest")

        # Create sink
        sink_id = f"{line_id}-SINK"
        self._create_sink(sink_id, line_id, line_config.get("sink", {}))

        # Store connection topology
        self._store_line_connections(line_id, source_id, equipment_list, sink_id)

    def _create_source(self, source_id: str, line_id: str, config: dict[str, Any]) -> None:
        """Create a source primitive.

        Args:
            source_id: Source identifier
            line_id: Line identifier
            config: Source configuration
        """
        # Get defaults from system config
        defaults = self.config.get("system", {}).get("flow_control", {})

        # Create flow capacity
        flow_capacity = FlowCapacity(
            max_input_rate=config.get("max_input_rate", 1000),
            max_output_rate=config.get("max_output_rate", 250),
            internal_capacity=config.get("internal_capacity", 1000),
            initial_level=config.get("initial_level", 0)
        )

        # Create source
        source = SourceFlow(
            env=self.env,
            config={
                "id": source_id,
                "line_id": line_id,
                "continuous_mode": config.get("continuous_mode", True),
                "default_product": config.get("default_product", "default")
            },
            flow_capacity=flow_capacity,
            generation_rate=config.get("generation_rate", 200.0),
            generation_interval=config.get("generation_interval",
                                         defaults.get("default_production_interval", 0.1))
        )

        self.primitives[source_id] = source
        logger.debug(f"Created source: {source_id}")

    def _create_equipment(self, equipment_id: str, line_id: str, config: dict[str, Any]) -> None:
        """Create an equipment primitive.

        Args:
            equipment_id: Equipment identifier
            line_id: Line identifier
            config: Equipment configuration
        """
        # Get equipment type for defaults
        equipment_type = config.get("type", "Equipment")

        # Get defaults from system config
        defaults = self.config.get("system", {}).get("flow_control", {})

        # Create flow capacity
        flow_config = config.get("flow_capacity", {})
        flow_capacity = FlowCapacity(
            max_input_rate=flow_config.get("max_input_rate", 250),
            max_output_rate=flow_config.get("max_output_rate", 245),
            internal_capacity=flow_config.get("internal_capacity", 500),
            initial_level=flow_config.get("initial_level", 0)
        )

        # Create processing parameters
        proc_config = config.get("processing", {})
        processing = ProcessingParameters(
            nominal_rate=proc_config.get("nominal_rate", 200.0),
            quality_rate=proc_config.get("quality_rate", 0.95),
            performance_factor=proc_config.get("performance_factor", 0.85),
            batch_size=proc_config.get("batch_size",
                                      defaults.get("default_batch_size_min", 10.0)),
            processing_interval=proc_config.get("processing_interval",
                                              defaults.get("default_production_interval", 0.1))
        )

        # Create failure parameters
        fail_config = config.get("failures", {})
        failures = FailureParameters(
            mtbf=fail_config.get("mtbf", 120.0),
            mttr=fail_config.get("mttr", 10.0),
            micro_stop_rate=fail_config.get("micro_stop_rate", 0.0),
            micro_stop_duration=fail_config.get("micro_stop_duration", 0.0)
        )

        # Create equipment
        equipment = EquipmentFlow(
            env=self.env,
            config={
                "id": equipment_id,
                "line_id": line_id,
                "type": equipment_type,
                "position": config.get("position", 0)
            },
            flow_capacity=flow_capacity,
            processing=processing,
            failures=failures
        )

        self.primitives[equipment_id] = equipment
        logger.debug(f"Created equipment: {equipment_id} (type: {equipment_type})")

    def _create_sink(self, sink_id: str, line_id: str, config: dict[str, Any]) -> None:
        """Create a sink primitive.

        Args:
            sink_id: Sink identifier
            line_id: Line identifier
            config: Sink configuration
        """
        # Get defaults from system config
        defaults = self.config.get("system", {}).get("monitoring", {})

        # Create flow capacity
        flow_capacity = FlowCapacity(
            max_input_rate=config.get("max_input_rate", 250),
            max_output_rate=config.get("max_output_rate", 250),
            internal_capacity=config.get("internal_capacity", 10000),
            initial_level=config.get("initial_level", 0)
        )

        # Create sink
        sink = SinkFlow(
            env=self.env,
            config={
                "id": sink_id,
                "line_id": line_id,
                "nominal_rate": config.get("nominal_rate", 200.0),
                "window_duration": config.get("window_duration",
                                            defaults.get("kpi_interval", 5.0))
            },
            flow_capacity=flow_capacity,
            collection_rate=config.get("collection_rate", 250.0),
            collection_interval=config.get("collection_interval", 0.1)
        )

        self.primitives[sink_id] = sink
        logger.debug(f"Created sink: {sink_id}")

    def _store_line_connections(
        self,
        line_id: str,
        source_id: str,
        equipment_list: list[str],
        sink_id: str
    ) -> None:
        """Store connection topology for a line.

        Args:
            line_id: Line identifier
            source_id: Source identifier
            equipment_list: List of equipment IDs in order
            sink_id: Sink identifier
        """
        connections = []

        # Source to first equipment
        if equipment_list:
            connections.append({
                "from": source_id,
                "to": equipment_list[0],
                "line": line_id
            })

            # Equipment to equipment
            for i in range(len(equipment_list) - 1):
                connections.append({
                    "from": equipment_list[i],
                    "to": equipment_list[i + 1],
                    "line": line_id
                })

            # Last equipment to sink
            connections.append({
                "from": equipment_list[-1],
                "to": sink_id,
                "line": line_id
            })
        else:
            # Direct source to sink
            connections.append({
                "from": source_id,
                "to": sink_id,
                "line": line_id
            })

        self.connections.extend(connections)

    def _wire_connections(self) -> None:
        """Wire equipment with shared Container buffers."""
        logger.info(f"Wiring {len(self.connections)} connections")

        # Get buffer defaults
        defaults = self.config.get("system", {}).get("flow_control", {})
        default_capacity = defaults.get("default_buffer_capacity", 1000)

        for connection in self.connections:
            from_id = connection["from"]
            to_id = connection["to"]

            if from_id not in self.primitives or to_id not in self.primitives:
                logger.warning(f"Cannot wire {from_id} -> {to_id}: primitive not found")
                continue

            from_primitive = self.primitives[from_id]
            to_primitive = self.primitives[to_id]

            # Calculate buffer capacity
            capacity = min(
                getattr(from_primitive.flow_capacity, "max_output_rate", 250) * 10,
                getattr(to_primitive.flow_capacity, "max_input_rate", 250) * 10,
                default_capacity
            )

            # Create shared buffer
            shared_buffer = simpy.Container(
                self.env,
                capacity=capacity,
                init=0  # Start empty (can be configured for WIP)
            )

            # Connect primitives
            from_primitive.output_buffer = shared_buffer
            to_primitive.input_buffer = shared_buffer

            logger.debug(f"Wired: {from_id} -> {to_id} (buffer capacity: {capacity})")

    def _load_orders(self) -> None:
        """Load production orders into sources."""
        orders = self.manifests.get("orders", {})

        for order_id, order_config in orders.items():
            line_id = order_config.get("line_id")
            if not line_id:
                logger.warning(f"Order {order_id} has no line_id")
                continue

            source_id = f"{line_id}-SOURCE"
            if source_id not in self.primitives:
                logger.warning(f"Source {source_id} not found for order {order_id}")
                continue

            source = self.primitives[source_id]
            if not isinstance(source, SourceFlow):
                logger.warning(f"{source_id} is not a SourceFlow")
                continue

            # Create production order
            order = ProductionOrder(
                order_id=order_id,
                product_id=order_config.get("product_id", "default"),
                target_volume=order_config.get("target_volume", 1000),
                due_time=order_config.get("due_time", 480),
                priority=order_config.get("priority", 0)
            )

            source.add_order(order)
            logger.debug(f"Added order {order_id} to {source_id}")

    def _start_processes(self) -> None:
        """Start all flow processes."""
        for primitive_id, primitive in self.primitives.items():
            if hasattr(primitive, "start"):
                primitive.start()
                logger.debug(f"Started process: {primitive_id}")

    def get_primitive(self, primitive_id: str) -> Optional[Any]:
        """Get a primitive by ID.

        Args:
            primitive_id: Primitive identifier

        Returns:
            Primitive instance or None if not found
        """
        return self.primitives.get(primitive_id)

    def get_line_primitives(self, line_id: str) -> list[Any]:
        """Get all primitives for a production line.

        Args:
            line_id: Line identifier

        Returns:
            List of primitives belonging to the line
        """
        line_primitives = []
        for primitive_id, primitive in self.primitives.items():
            if hasattr(primitive, "config") and primitive.config.get("line_id") == line_id:
                line_primitives.append(primitive)
        return line_primitives

    def get_topology(self) -> dict[str, list[str]]:
        """Get connection topology.

        Returns:
            Dictionary mapping primitive IDs to their downstream connections
        """
        topology = {}
        for connection in self.connections:
            from_id = connection["from"]
            to_id = connection["to"]

            if from_id not in topology:
                topology[from_id] = []
            topology[from_id].append(to_id)

        return topology
