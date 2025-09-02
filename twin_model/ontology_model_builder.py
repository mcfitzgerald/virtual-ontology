"""Ontology-driven model builder for twin simulation.

This module builds simulation models using:
- Ontology for structure and validation
- Manifests for equipment instances
- Config for tunable parameters
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

import simpy
import yaml

from .primitives import (
    EquipmentFlow,
    FailureParameters,
    FlowCapacity,
    ProcessingParameters,
    SinkFlow,
    SourceFlow,
)

logger = logging.getLogger(__name__)


class OntologyModelBuilder:
    """Builds simulation models from ontology, manifests, and config."""

    def __init__(self, env: simpy.Environment, ontology_path: Path, manifest_path: Path, config_path: Path) -> None:
        """Initialize the ontology-driven model builder.

        Args:
            env: SimPy environment
            ontology_path: Path to ontology YAML file
            manifest_path: Path to equipment manifest YAML file
            config_path: Path to config YAML file with tunable parameters
        """
        self.env = env

        # Load files
        self.ontology = self._load_yaml(ontology_path)
        self.manifest = self._load_yaml(manifest_path)
        self.config = self._load_yaml(config_path)

        # Storage for created primitives
        self.primitives: Dict[str, Any] = {}
        self.connections: List[Dict[str, str]] = []

        logger.info("Initialized OntologyModelBuilder")
        logger.info(f"  Ontology: {self.ontology['metadata']['name']}")
        logger.info(f"  Manifest: {self.manifest['metadata']['name']}")
        logger.info(f"  Config: {self.config['metadata']['name']}")

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load and parse YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Parsed YAML content
        """
        with open(path) as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ValueError(f"Expected YAML file to contain a dictionary, got {type(data)}")
            return data

    def build_model(self) -> Dict[str, Any]:
        """Build complete simulation model.

        Returns:
            Dictionary containing primitives and metadata
        """
        logger.info("Building model from ontology, manifest, and config")

        # 1. Validate manifest against ontology
        self._validate_manifest()

        # 2. Create equipment primitives
        equipment_dict = self.manifest.get("equipment", {})
        for equipment_id, equipment_data in equipment_dict.items():
            self._create_equipment(equipment_id, equipment_data)

        # 3. Wire connections
        self._wire_connections()

        # 4. Start all processes
        self._start_processes()

        logger.info(f"Model built successfully with {len(self.primitives)} primitives")

        return {
            "primitives": self.primitives,
            "env": self.env,
            "ontology": self.ontology["metadata"]["name"],
            "lines": self._get_lines(),
        }

    def _validate_manifest(self) -> None:
        """Validate manifest against ontology structure."""
        types_defined = self.ontology["tbox"]["types"]
        equipment_dict = self.manifest.get("equipment", {})

        errors = []

        for equipment_id, equipment_data in equipment_dict.items():
            eq_type = equipment_data.get("type")

            # Check if type exists in ontology
            if eq_type not in types_defined:
                errors.append(f"Equipment {equipment_id} has invalid type: {eq_type}")

            # Check required properties
            if eq_type in types_defined:
                # Note: We don't check for required properties here since they're in config

                # Check position and line_id (structural requirements)
                if "position" not in equipment_data:
                    errors.append(f"Equipment {equipment_id} missing position")
                if "line_id" not in equipment_data:
                    errors.append(f"Equipment {equipment_id} missing line_id")

        # Validate connections
        connections = self.manifest.get("connections", [])
        for conn in connections:
            from_id = conn.get("from")
            to_id = conn.get("to")

            if from_id not in equipment_dict:
                errors.append(f"Connection references unknown equipment: {from_id}")
            if to_id not in equipment_dict:
                errors.append(f"Connection references unknown equipment: {to_id}")

            # Validate connection is allowed by ontology
            if from_id in equipment_dict and to_id in equipment_dict:
                from_type = equipment_dict[from_id]["type"]
                to_type = equipment_dict[to_id]["type"]

                if not self._is_valid_connection(from_type, to_type):
                    errors.append(f"Invalid connection: {from_type} -> {to_type}")

        if errors:
            for error in errors:
                logger.error(error)
            raise ValueError(f"Manifest validation failed with {len(errors)} errors")

        logger.info("Manifest validated successfully")

    def _is_valid_connection(self, from_type: str, to_type: str) -> bool:
        """Check if connection is valid according to ontology.

        Args:
            from_type: Type of upstream equipment
            to_type: Type of downstream equipment

        Returns:
            True if connection is valid
        """
        types_def = self.ontology["tbox"]["types"]

        # Get the type definition
        if from_type not in types_def:
            return False

        type_info = types_def[from_type]

        # Check relationships
        can_connect = type_info.get("relationships", {}).get("can_connect_to", [])

        # Check if to_type is in allowed connections
        if to_type in can_connect:
            return True

        # Check if to_type inherits from an allowed type
        to_type_info = types_def.get(to_type, {})
        parent = to_type_info.get("extends")
        if parent and parent in can_connect:
            return True

        return False

    def _create_equipment(self, equipment_id: str, equipment_data: Dict[str, Any]) -> None:
        """Create equipment primitive based on type.

        Args:
            equipment_id: Equipment identifier
            equipment_data: Equipment manifest data
        """
        eq_type = equipment_data["type"]

        # Get framework primitive from ontology
        type_def = self.ontology["tbox"]["types"][eq_type]
        framework_primitive = type_def["maps_to"]["framework_primitive"]

        # Get parameters from config
        eq_params = self.config["equipment_parameters"].get(equipment_id, {})
        flow_params = self.config["flow_capacity"]["equipment"].get(equipment_id, {})
        flow_defaults = self.config["flow_capacity"]["defaults"]

        # Merge with defaults
        for key, value in self.config["defaults"]["equipment"].items():
            if key not in eq_params:
                eq_params[key] = value

        for key, value in flow_defaults.items():
            if key not in flow_params:
                flow_params[key] = value

        # Create the appropriate primitive
        if framework_primitive == "SourceFlow":
            self._create_source(equipment_id, eq_params, flow_params)
        elif framework_primitive == "SinkFlow":
            self._create_sink(equipment_id, eq_params, flow_params)
        elif framework_primitive == "EquipmentFlow":
            self._create_equipment_flow(equipment_id, eq_params, flow_params, eq_type)
        else:
            raise ValueError(f"Unknown framework primitive: {framework_primitive}")

    def _create_source(self, source_id: str, params: Dict[str, Any], flow_params: Dict[str, Any]) -> None:
        """Create source primitive.

        Args:
            source_id: Source identifier
            params: Source parameters
            flow_params: Flow capacity parameters
        """
        # Create flow capacity
        capacity = FlowCapacity(
            max_input_rate=flow_params.get("max_input_rate", 100.0),
            max_output_rate=flow_params.get("max_output_rate", 60.0),
            internal_capacity=flow_params.get("internal_capacity", 1000.0),
            initial_level=flow_params.get("initial_level", 0.0),
        )

        # Create config dict
        config = {
            "name": source_id,
            "continuous_mode": params.get("continuous_mode", True),
            "default_product": params.get("default_product", "SKU-1001"),
        }

        # Create source
        source = SourceFlow(
            env=self.env,
            config=config,
            flow_capacity=capacity,
            generation_rate=params.get("generation_rate", 60.0),
            generation_interval=params.get("generation_interval", 0.1),
        )

        # Create output buffer
        source.output_buffer = simpy.Container(self.env, capacity=capacity.internal_capacity, init=0)

        # Store metadata as dynamic attributes
        source.equipment_type = "MaterialSource"  # type: ignore[attr-defined]
        source.equipment_id = source_id  # type: ignore[attr-defined]

        self.primitives[source_id] = source
        logger.debug(f"Created source: {source_id}")

    def _create_sink(self, sink_id: str, params: Dict[str, Any], flow_params: Dict[str, Any]) -> None:
        """Create sink primitive.

        Args:
            sink_id: Sink identifier
            params: Sink parameters
            flow_params: Flow capacity parameters
        """
        # Create flow capacity
        capacity = FlowCapacity(
            max_input_rate=flow_params.get("max_input_rate", 60.0),
            max_output_rate=flow_params.get("max_output_rate", 60.0),
            internal_capacity=flow_params.get("internal_capacity", 10000.0),
            initial_level=flow_params.get("initial_level", 0.0),
        )

        # Create config dict
        config = {
            "name": sink_id,
            "nominal_rate": params.get("nominal_rate", 50.0),
            "window_duration": params.get("window_duration", 5.0),
        }

        # Create sink
        sink = SinkFlow(
            env=self.env,
            config=config,
            flow_capacity=capacity,
            collection_rate=params.get("collection_rate", 50.0),
            collection_interval=params.get("collection_interval", 0.1),
        )

        # Create input buffer
        sink.input_buffer = simpy.Container(self.env, capacity=capacity.internal_capacity, init=0)

        # Store metadata as dynamic attributes
        sink.equipment_type = "ProductCollection"  # type: ignore[attr-defined]
        sink.equipment_id = sink_id  # type: ignore[attr-defined]

        self.primitives[sink_id] = sink
        logger.debug(f"Created sink: {sink_id}")

    def _create_equipment_flow(
        self, equipment_id: str, params: Dict[str, Any], flow_params: Dict[str, Any], equipment_type: str
    ) -> None:
        """Create equipment flow primitive.

        Args:
            equipment_id: Equipment identifier
            params: Equipment parameters
            flow_params: Flow capacity parameters
            equipment_type: Type of equipment (Filler, Packer, etc.)
        """
        # Create processing parameters
        processing = ProcessingParameters(
            nominal_rate=params.get("nominal_rate", 50.0),
            quality_rate=params.get("quality_rate", 0.95),
            performance_factor=params.get("performance_factor", 0.85),
            batch_size=params.get("batch_size", 10.0),
            processing_interval=params.get("processing_interval", 0.1),
        )

        # Create failure parameters
        failures = FailureParameters(
            mtbf=params.get("mtbf", 60.0),
            mttr=params.get("mttr", 10.0),
            micro_stop_rate=params.get("micro_stop_rate", 0.0),
            micro_stop_duration=params.get("micro_stop_duration", 0.0),
        )

        # Create flow capacity
        capacity = FlowCapacity(
            max_input_rate=flow_params.get("max_input_rate", 60.0),
            max_output_rate=flow_params.get("max_output_rate", 50.0),
            internal_capacity=flow_params.get("internal_capacity", 500.0),
            initial_level=flow_params.get("initial_level", 0.0),
        )

        # Create config dict
        config = {"name": equipment_id, "equipment_type": equipment_type}

        # Add type-specific parameters
        if equipment_type == "FillingStation":
            config["fill_rate"] = params.get("fill_rate", 50.0)
        elif equipment_type == "PackingStation":
            config["pack_size"] = params.get("pack_size", 12)
        elif equipment_type == "PalletizingStation":
            config["pallet_size"] = params.get("pallet_size", 144)

        # Create equipment
        equipment = EquipmentFlow(
            env=self.env, config=config, flow_capacity=capacity, processing=processing, failures=failures
        )

        # Create buffers
        equipment.input_buffer = simpy.Container(self.env, capacity=capacity.internal_capacity, init=0)
        equipment.output_buffer = simpy.Container(self.env, capacity=capacity.internal_capacity, init=0)
        # Note: internal_buffer is created by EquipmentFlow.__init__

        # Store metadata as dynamic attributes
        equipment.equipment_type = equipment_type  # type: ignore[attr-defined]
        equipment.equipment_id = equipment_id  # type: ignore[attr-defined]

        self.primitives[equipment_id] = equipment
        logger.debug(f"Created equipment: {equipment_id} (type: {equipment_type})")

    def _wire_connections(self) -> None:
        """Wire equipment connections based on manifest."""
        connections = self.manifest.get("connections", [])

        logger.info(f"Wiring {len(connections)} connections")

        for conn in connections:
            from_id = conn["from"]
            to_id = conn["to"]

            if from_id not in self.primitives or to_id not in self.primitives:
                logger.warning(f"Cannot wire {from_id} -> {to_id}: equipment not found")
                continue

            upstream = self.primitives[from_id]
            downstream = self.primitives[to_id]

            # Share buffers - upstream's output becomes downstream's input
            if hasattr(upstream, "output_buffer") and hasattr(downstream, "input_buffer"):
                # Don't create a new buffer - share the existing one!
                # The downstream's input buffer becomes the upstream's output buffer
                downstream.input_buffer = upstream.output_buffer

                logger.info(f"Wired: {from_id} -> {to_id} (shared buffer)")
                self.connections.append({"from": from_id, "to": to_id})
            else:
                logger.warning(f"Cannot wire {from_id} -> {to_id}: missing buffers")

    def _start_processes(self) -> None:
        """Start all equipment processes."""
        for equipment_id, equipment in self.primitives.items():
            if hasattr(equipment, "start"):
                equipment.start()
                logger.debug(f"Started process: {equipment_id}")

    def _get_lines(self) -> Dict[str, List[str]]:
        """Get equipment organized by production lines.

        Returns:
            Dictionary mapping line IDs to equipment IDs
        """
        lines: Dict[str, List[str]] = {}
        equipment_dict = self.manifest.get("equipment", {})

        for equipment_id, equipment_data in equipment_dict.items():
            line_id = equipment_data.get("line_id")
            if line_id:
                if line_id not in lines:
                    lines[line_id] = []
                lines[line_id].append(equipment_id)

        # Sort by position
        for line_id in lines:
            lines[line_id].sort(key=lambda eq_id: equipment_dict[eq_id].get("position", 999))

        return lines

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics from all equipment.

        Returns:
            Dictionary of metrics by equipment
        """
        metrics = {}

        for equipment_id, equipment in self.primitives.items():
            if hasattr(equipment, "get_metrics"):
                metrics[equipment_id] = equipment.get_metrics()
            elif hasattr(equipment, "flow_metrics"):
                metrics[equipment_id] = {
                    "total_input": equipment.flow_metrics.total_input,
                    "total_output": equipment.flow_metrics.total_output,
                    "total_scrap": equipment.flow_metrics.total_scrap,
                    "state": str(equipment.current_state) if hasattr(equipment, "current_state") else "UNKNOWN",
                }

        return metrics
