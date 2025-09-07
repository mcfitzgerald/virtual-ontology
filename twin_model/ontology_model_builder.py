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

        # Create the appropriate primitive
        # Pass the equipment_id and type, let each method handle parameter resolution
        if framework_primitive == "SourceFlow":
            self._create_source(equipment_id)
        elif framework_primitive == "SinkFlow":
            self._create_sink(equipment_id)
        elif framework_primitive == "EquipmentFlow":
            self._create_equipment_flow(equipment_id, eq_type)
        else:
            raise ValueError(f"Unknown framework primitive: {framework_primitive}")

    def _create_source(self, source_id: str) -> None:
        """Create source primitive with proper parameter resolution.

        Args:
            source_id: Source identifier
        """
        # Get parameters directly from config sections
        eq_params = self.config.get("equipment_parameters", {}).get(source_id, {})
        eq_flow_params = self.config.get("flow_capacity", {}).get("equipment", {}).get(source_id, {})
        source_defaults = self.config.get("defaults", {}).get("source", {})
        flow_defaults = self.config.get("flow_capacity", {}).get("defaults", {})
        
        # Parameter resolution order: equipment-specific -> type-specific defaults -> general defaults -> fallback
        generation_rate = (
            eq_params.get("generation_rate") or
            source_defaults.get("generation_rate", 300.0)  # Last resort fallback
        )
        generation_interval = (
            eq_params.get("generation_interval") or
            source_defaults.get("generation_interval", 0.1)
        )
        
        # Log what we're using
        logger.info(f"Creating {source_id}:")
        logger.info(f"  generation_rate: {generation_rate} (from: {self._get_param_source('generation_rate', eq_params, source_defaults)})")
        logger.info(f"  generation_interval: {generation_interval} (from: {self._get_param_source('generation_interval', eq_params, source_defaults)})")
        
        # Create flow capacity with proper resolution: equipment-specific -> source defaults -> flow defaults
        max_input_rate = (
            eq_flow_params.get("max_input_rate") or
            source_defaults.get("max_input_rate") or
            flow_defaults.get("max_input_rate", 350.0)
        )
        max_output_rate = (
            eq_flow_params.get("max_output_rate") or
            source_defaults.get("max_output_rate") or
            flow_defaults.get("max_output_rate", 350.0)
        )
        internal_capacity = (
            eq_flow_params.get("internal_capacity") or
            source_defaults.get("internal_capacity") or
            flow_defaults.get("internal_capacity", 2000.0)
        )
        initial_level = eq_flow_params.get("initial_level", 0.0)
        
        logger.info(f"  max_input_rate: {max_input_rate} (from: {self._get_param_source('max_input_rate', eq_flow_params, source_defaults, flow_defaults)})")
        logger.info(f"  max_output_rate: {max_output_rate} (from: {self._get_param_source('max_output_rate', eq_flow_params, source_defaults, flow_defaults)})")
        logger.info(f"  internal_capacity: {internal_capacity} (from: {self._get_param_source('internal_capacity', eq_flow_params, source_defaults, flow_defaults)})")
        
        capacity = FlowCapacity(
            max_input_rate=max_input_rate,
            max_output_rate=max_output_rate,
            internal_capacity=internal_capacity,
            initial_level=initial_level,
        )

        # Create config dict
        config = {
            "name": source_id,
            "continuous_mode": eq_params.get("continuous_mode") or source_defaults.get("continuous_mode", True),
            "default_product": eq_params.get("default_product") or source_defaults.get("default_product", "SKU-1001"),
        }

        # Create source
        source = SourceFlow(
            env=self.env,
            config=config,
            flow_capacity=capacity,
            generation_rate=generation_rate,
            generation_interval=generation_interval,
        )

        # Create output buffer
        source.output_buffer = simpy.Container(self.env, capacity=capacity.internal_capacity, init=0)

        # Store metadata as dynamic attributes
        source.equipment_type = "MaterialSource"  # type: ignore[attr-defined]
        source.equipment_id = source_id  # type: ignore[attr-defined]

        self.primitives[source_id] = source
        logger.debug(f"Created source: {source_id}")

    def _create_sink(self, sink_id: str) -> None:
        """Create sink primitive with proper parameter resolution.

        Args:
            sink_id: Sink identifier
        """
        # Get parameters directly from config sections
        eq_params = self.config.get("equipment_parameters", {}).get(sink_id, {})
        eq_flow_params = self.config.get("flow_capacity", {}).get("equipment", {}).get(sink_id, {})
        sink_defaults = self.config.get("defaults", {}).get("sink", {})
        flow_defaults = self.config.get("flow_capacity", {}).get("defaults", {})
        
        # Collection rate resolution: equipment flow params -> equipment params -> sink defaults
        collection_rate = (
            eq_flow_params.get("collection_rate") or
            eq_params.get("collection_rate") or
            sink_defaults.get("collection_rate", 300.0)  # Last resort fallback
        )
        collection_interval = (
            eq_flow_params.get("collection_interval") or
            eq_params.get("collection_interval") or
            sink_defaults.get("collection_interval", 0.1)
        )
        
        # Log what we're using
        logger.info(f"Creating {sink_id}:")
        logger.info(f"  collection_rate: {collection_rate} (from: {self._get_param_source('collection_rate', eq_flow_params, eq_params, sink_defaults)})")
        logger.info(f"  collection_interval: {collection_interval} (from: {self._get_param_source('collection_interval', eq_flow_params, eq_params, sink_defaults)})")
        
        # Create flow capacity with proper resolution: equipment-specific -> sink defaults -> flow defaults
        max_input_rate = (
            eq_flow_params.get("max_input_rate") or
            sink_defaults.get("max_input_rate") or
            flow_defaults.get("max_input_rate", 350.0)
        )
        max_output_rate = (
            eq_flow_params.get("max_output_rate") or
            sink_defaults.get("max_output_rate") or
            flow_defaults.get("max_output_rate", 350.0)
        )
        internal_capacity = (
            eq_flow_params.get("internal_capacity") or
            sink_defaults.get("internal_capacity") or
            flow_defaults.get("internal_capacity", 10000.0)
        )
        initial_level = eq_flow_params.get("initial_level", 0.0)
        
        logger.info(f"  max_input_rate: {max_input_rate} (from: {self._get_param_source('max_input_rate', eq_flow_params, sink_defaults, flow_defaults)})")
        logger.info(f"  max_output_rate: {max_output_rate} (from: {self._get_param_source('max_output_rate', eq_flow_params, sink_defaults, flow_defaults)})")
        logger.info(f"  internal_capacity: {internal_capacity} (from: {self._get_param_source('internal_capacity', eq_flow_params, sink_defaults, flow_defaults)})")
        
        capacity = FlowCapacity(
            max_input_rate=max_input_rate,
            max_output_rate=max_output_rate,
            internal_capacity=internal_capacity,
            initial_level=initial_level,
        )

        # Create config dict with proper resolution
        nominal_rate = eq_params.get("nominal_rate") or sink_defaults.get("nominal_rate", 300.0)
        window_duration = eq_params.get("window_duration") or sink_defaults.get("window_duration", 5.0)
        
        config = {
            "name": sink_id,
            "nominal_rate": nominal_rate,
            "window_duration": window_duration,
        }

        # Create sink
        sink = SinkFlow(
            env=self.env,
            config=config,
            flow_capacity=capacity,
            collection_rate=collection_rate,
            collection_interval=collection_interval,
        )

        # Create input buffer
        sink.input_buffer = simpy.Container(self.env, capacity=capacity.internal_capacity, init=0)

        # Store metadata as dynamic attributes
        sink.equipment_type = "ProductCollection"  # type: ignore[attr-defined]
        sink.equipment_id = sink_id  # type: ignore[attr-defined]

        self.primitives[sink_id] = sink
        logger.debug(f"Created sink: {sink_id}")

    def _create_equipment_flow(
        self, equipment_id: str, equipment_type: str
    ) -> None:
        """Create equipment flow primitive with proper parameter resolution.

        Args:
            equipment_id: Equipment identifier
            equipment_type: Type of equipment (FillingStation, PackingStation, etc.)
        """
        # Get parameters directly from config sections
        eq_params = self.config.get("equipment_parameters", {}).get(equipment_id, {})
        eq_flow_params = self.config.get("flow_capacity", {}).get("equipment", {}).get(equipment_id, {})
        equipment_defaults = self.config.get("defaults", {}).get("equipment", {})
        flow_defaults = self.config.get("flow_capacity", {}).get("defaults", {})
        
        # Log what we're creating
        logger.info(f"Creating {equipment_id} (type: {equipment_type}):")
        
        # Create processing parameters with proper resolution
        nominal_rate = eq_params.get("nominal_rate") or equipment_defaults.get("nominal_rate", 90.0)
        quality_rate = eq_params.get("quality_rate") or equipment_defaults.get("quality_rate", 0.95)
        performance_factor = eq_params.get("performance_factor") or equipment_defaults.get("performance_factor", 0.55)
        batch_size = eq_params.get("batch_size") or equipment_defaults.get("batch_size", 10.0)
        processing_interval = eq_params.get("processing_interval") or equipment_defaults.get("processing_interval", 0.1)
        
        logger.info(f"  nominal_rate: {nominal_rate} (from: {self._get_param_source('nominal_rate', eq_params, equipment_defaults)})")
        logger.info(f"  quality_rate: {quality_rate} (from: {self._get_param_source('quality_rate', eq_params, equipment_defaults)})")
        logger.info(f"  performance_factor: {performance_factor} (from: {self._get_param_source('performance_factor', eq_params, equipment_defaults)})")
        logger.info(f"  batch_size: {batch_size} (from: {self._get_param_source('batch_size', eq_params, equipment_defaults)})")
        
        processing = ProcessingParameters(
            nominal_rate=nominal_rate,
            quality_rate=quality_rate,
            performance_factor=performance_factor,
            batch_size=batch_size,
            processing_interval=processing_interval,
        )

        # Create failure parameters with proper resolution
        mtbf = eq_params.get("mtbf") or equipment_defaults.get("mtbf", 60.0)
        mttr = eq_params.get("mttr") or equipment_defaults.get("mttr", 30.0)
        micro_stop_rate = eq_params.get("micro_stop_rate") or equipment_defaults.get("micro_stop_rate", 0.0)
        micro_stop_duration = eq_params.get("micro_stop_duration") or equipment_defaults.get("micro_stop_duration", 0.0)
        
        logger.info(f"  mtbf: {mtbf} (from: {self._get_param_source('mtbf', eq_params, equipment_defaults)})")
        logger.info(f"  mttr: {mttr} (from: {self._get_param_source('mttr', eq_params, equipment_defaults)})")
        
        failures = FailureParameters(
            mtbf=mtbf,
            mttr=mttr,
            micro_stop_rate=micro_stop_rate,
            micro_stop_duration=micro_stop_duration,
        )

        # Create flow capacity with proper resolution: equipment-specific -> equipment defaults -> flow defaults
        max_input_rate = (
            eq_flow_params.get("max_input_rate") or
            equipment_defaults.get("max_input_rate") or
            flow_defaults.get("max_input_rate", 100.0)
        )
        max_output_rate = (
            eq_flow_params.get("max_output_rate") or
            equipment_defaults.get("max_output_rate") or
            flow_defaults.get("max_output_rate", 90.0)
        )
        internal_capacity = (
            eq_flow_params.get("internal_capacity") or
            equipment_defaults.get("internal_capacity") or
            flow_defaults.get("internal_capacity", 500.0)
        )
        initial_level = eq_flow_params.get("initial_level", 0.0)
        
        logger.info(f"  max_input_rate: {max_input_rate} (from: {self._get_param_source('max_input_rate', eq_flow_params, equipment_defaults, flow_defaults)})")
        logger.info(f"  max_output_rate: {max_output_rate} (from: {self._get_param_source('max_output_rate', eq_flow_params, equipment_defaults, flow_defaults)})")
        logger.info(f"  internal_capacity: {internal_capacity} (from: {self._get_param_source('internal_capacity', eq_flow_params, equipment_defaults, flow_defaults)})")
        
        capacity = FlowCapacity(
            max_input_rate=max_input_rate,
            max_output_rate=max_output_rate,
            internal_capacity=internal_capacity,
            initial_level=initial_level,
        )

        # Create config dict
        config = {"name": equipment_id, "equipment_type": equipment_type}

        # Add type-specific parameters with proper resolution
        if equipment_type == "FillingStation":
            fill_rate = eq_params.get("fill_rate") or equipment_defaults.get("fill_rate", 90.0)
            config["fill_rate"] = fill_rate
            logger.info(f"  fill_rate: {fill_rate} (from: {self._get_param_source('fill_rate', eq_params, equipment_defaults)})")
        elif equipment_type == "PackingStation":
            pack_size = eq_params.get("pack_size") or equipment_defaults.get("pack_size", 12)
            config["pack_size"] = pack_size
            logger.info(f"  pack_size: {pack_size} (from: {self._get_param_source('pack_size', eq_params, equipment_defaults)})")
        elif equipment_type == "PalletizingStation":
            pallet_size = eq_params.get("pallet_size") or equipment_defaults.get("pallet_size", 144)
            config["pallet_size"] = pallet_size
            logger.info(f"  pallet_size: {pallet_size} (from: {self._get_param_source('pallet_size', eq_params, equipment_defaults)})")

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
    
    def _get_param_source(self, param_name: str, *param_dicts: Dict) -> str:
        """Helper to identify parameter source for logging.
        
        Args:
            param_name: Name of the parameter to look for
            *param_dicts: Variable number of parameter dictionaries to check in order
            
        Returns:
            String describing the source of the parameter
        """
        source_names = ["equipment_parameters", "flow_capacity", "defaults"]
        
        for i, param_dict in enumerate(param_dicts):
            if param_name in param_dict and param_dict[param_name] is not None:
                if i < len(source_names):
                    return source_names[i]
                else:
                    return f"dict_{i}"
        
        return "hardcoded_fallback"
