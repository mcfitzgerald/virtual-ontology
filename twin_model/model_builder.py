"""Ontology-driven model builder for SimPy simulations.

This module builds SimPy models from the twin ontology structure and manifests.
It interprets the ontology to instantiate primitives, wire relationships,
and configure values from manifests.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import simpy
from dataclasses import dataclass

from .primitives import (
    BasePrimitive,
    PrimitiveConfig,
    EquipmentPrimitive,
    BufferPrimitive,
    SourcePrimitive,
    SinkPrimitive,
    SchedulerPrimitive,
    MonitorPrimitive,
)


@dataclass
class ModelEntity:
    """Represents an entity to be instantiated in the model.

    Attributes:
        id: Unique identifier
        ontology_class: Class name from ontology
        primitive_type: Primitive class to instantiate
        properties: Configuration properties
        relationships: Entity relationships
    """

    id: str
    ontology_class: str
    primitive_type: str
    properties: Dict[str, Any]
    relationships: Dict[str, List[str]]


class OntologyDrivenModelBuilder:
    """Builds SimPy models from ontology structure and manifests.

    This builder interprets the twin ontology to construct a simulation model,
    then configures it with values from manifests. It maintains separation
    between structure (ontology) and configuration (manifests).
    """

    # Primitive class mapping
    PRIMITIVE_CLASSES = {
        "EquipmentPrimitive": EquipmentPrimitive,
        "BufferPrimitive": BufferPrimitive,
        "SourcePrimitive": SourcePrimitive,
        "SinkPrimitive": SinkPrimitive,
        "SchedulerPrimitive": SchedulerPrimitive,
        "MonitorPrimitive": MonitorPrimitive,
    }

    def __init__(
        self, ontology_path: Path, manifest_dir: Optional[Path] = None
    ) -> None:
        """Initialize builder with ontology and manifest directory.

        Args:
            ontology_path: Path to twin_ontology.yaml
            manifest_dir: Directory containing manifest files (optional)
        """
        self.ontology_path = ontology_path
        self.manifest_dir = manifest_dir

        # Load ontology
        self.ontology = self._load_ontology(ontology_path)

        # Load manifests if provided
        self.manifests = {}
        if manifest_dir and manifest_dir.exists():
            self.manifests = self._load_manifests(manifest_dir)

        # Model storage
        self.entities: Dict[str, ModelEntity] = {}
        self.primitives: Dict[str, BasePrimitive] = {}
        self.production_lines: Dict[str, Dict[str, Any]] = {}

    def _load_ontology(self, path: Path) -> Dict[str, Any]:
        """Load ontology from YAML file.

        Args:
            path: Path to ontology file

        Returns:
            Parsed ontology dictionary
        """
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _load_manifests(self, manifest_dir: Path) -> Dict[str, Any]:
        """Load all manifests from directory.

        Args:
            manifest_dir: Directory containing manifest files

        Returns:
            Dictionary of manifest name to content
        """
        manifests = {}

        for manifest_file in manifest_dir.glob("*.yaml"):
            manifest_name = manifest_file.stem
            with open(manifest_file, "r") as f:
                manifests[manifest_name] = yaml.safe_load(f)

        return manifests

    def build_model(self, env: simpy.Environment) -> Dict[str, Any]:
        """Build complete simulation model from ontology.

        Args:
            env: SimPy environment for the model

        Returns:
            Dictionary containing:
                - primitives: Instantiated primitive objects
                - lines: Production line configurations
                - scheduler: Scheduler primitive if created
                - monitor: Monitor primitive if created
        """
        # Add global observables to environment
        env.global_observables = []  # type: ignore[attr-defined]

        # Parse entities from manifests or use defaults
        self._parse_entities()

        # Instantiate primitives
        self._instantiate_primitives(env)

        # Wire relationships
        self._wire_relationships()

        # Create production lines
        self._create_production_lines()

        # Setup scheduler if configured
        scheduler = self._setup_scheduler(env)

        # Setup monitor if configured
        monitor = self._setup_monitor(env)

        # Start all primitives
        self._start_all_primitives()

        return {
            "primitives": self.primitives,
            "lines": self.production_lines,
            "scheduler": scheduler,
            "monitor": monitor,
            "entities": self.entities,
        }

    def _parse_entities(self) -> None:
        """Parse entities from manifests and ontology."""
        # Get equipment manifest if available
        equipment_manifest = self.manifests.get("equipment_manifest", {})
        equipment_config = equipment_manifest.get("equipment", {})

        # Get production manifest if available (may be used in future)
        # production_manifest = self.manifests.get('production_manifest', {})

        # Parse equipment entities
        for eq_id, eq_data in equipment_config.items():
            entity = ModelEntity(
                id=eq_id,
                ontology_class=eq_data.get("type", "Equipment"),
                primitive_type=self._get_primitive_type(
                    eq_data.get("type", "Equipment")
                ),
                properties=eq_data,
                relationships={},
            )
            self.entities[eq_id] = entity

        # Parse buffer entities from manifests
        buffer_config = equipment_manifest.get("buffers", {})
        for buf_id, buf_data in buffer_config.items():
            entity = ModelEntity(
                id=buf_id,
                ontology_class="Buffer",
                primitive_type="BufferPrimitive",
                properties=buf_data,
                relationships={},
            )
            self.entities[buf_id] = entity

        # If no manifests, create default entities from ontology patterns
        if not self.entities:
            self._create_default_entities()

    def _get_primitive_type(self, ontology_class: str) -> str:
        """Get primitive type for an ontology class.

        Args:
            ontology_class: Class name from ontology

        Returns:
            Primitive type name
        """
        # Check TBox for class definition
        tbox = self.ontology.get("tbox", {})
        classes = tbox.get("classes", {})

        # Look up class and its primitive mapping
        if ontology_class in classes:
            class_def = classes[ontology_class]
            primitive = class_def.get("primitive")
            if primitive:
                return primitive

            # Check parent class
            parent = class_def.get("parent")
            if parent and parent != "SimulationEntity":
                return self._get_primitive_type(parent)

        # Check primitive mapping rules
        mappings = self.ontology.get("primitive_mapping", {}).get(
            "default_mappings", {}
        )

        # Handle specialized equipment types
        if ontology_class in ["Filler", "Packer", "Palletizer"]:
            return "EquipmentPrimitive"

        return mappings.get(ontology_class, "EquipmentPrimitive")

    def _create_default_entities(self) -> None:
        """Create default entities for testing."""
        # Create a default production line
        default_line = [
            ModelEntity(
                id="SRC-DEFAULT",
                ontology_class="Source",
                primitive_type="SourcePrimitive",
                properties={
                    "arrival_rate": 65.0,
                    "arrival_pattern": "EXPONENTIAL",
                    "quality_rate": 0.98,
                },
                relationships={"feeds_into": ["BUF-IN"]},
            ),
            ModelEntity(
                id="BUF-IN",
                ontology_class="Buffer",
                primitive_type="BufferPrimitive",
                properties={"capacity": 100, "buffer_type": "FIFO"},
                relationships={"feeds_into": ["EQ-DEFAULT"]},
            ),
            ModelEntity(
                id="EQ-DEFAULT",
                ontology_class="Equipment",
                primitive_type="EquipmentPrimitive",
                properties={
                    "base_rate": 60.0,
                    "mtbf": 480.0,
                    "mttr": 30.0,
                    "energy_consumption_rate": 5.0,
                },
                relationships={"draws_from": ["BUF-IN"], "feeds_into": ["BUF-OUT"]},
            ),
            ModelEntity(
                id="BUF-OUT",
                ontology_class="Buffer",
                primitive_type="BufferPrimitive",
                properties={"capacity": 50, "buffer_type": "FIFO"},
                relationships={
                    "draws_from": ["EQ-DEFAULT"],
                    "feeds_into": ["SINK-DEFAULT"],
                },
            ),
            ModelEntity(
                id="SINK-DEFAULT",
                ontology_class="Sink",
                primitive_type="SinkPrimitive",
                properties={"collection_rate": 55.0, "target_throughput": 50.0},
                relationships={"draws_from": ["BUF-OUT"]},
            ),
        ]

        for entity in default_line:
            self.entities[entity.id] = entity

    def _instantiate_primitives(self, env: simpy.Environment) -> None:
        """Instantiate primitive objects from entities.

        Args:
            env: SimPy environment
        """
        for entity_id, entity in self.entities.items():
            # Get primitive class
            primitive_class = self.PRIMITIVE_CLASSES.get(entity.primitive_type)

            if not primitive_class:
                print(f"Warning: Unknown primitive type {entity.primitive_type}")
                continue

            # Create configuration
            config = PrimitiveConfig(
                id=entity_id,
                type=entity.ontology_class,
                properties=entity.properties,
                relationships=entity.relationships,
            )

            # Add default product based on line for equipment
            if entity.primitive_type == "EquipmentPrimitive":
                if "LINE1" in entity_id:
                    config.properties["default_product"] = "SKU-1001"
                    config.properties["default_order"] = "ORD-1000"
                elif "LINE2" in entity_id:
                    config.properties["default_product"] = "SKU-1002"
                    config.properties["default_order"] = "ORD-1001"
                elif "LINE3" in entity_id:
                    config.properties["default_product"] = "SKU-3001"
                    config.properties["default_order"] = "ORD-1009"

            # Special handling for equipment with buffers
            if entity.primitive_type == "EquipmentPrimitive":
                # Will wire buffers in relationship phase
                primitive = primitive_class(env, config)
            else:
                # Create primitive
                primitive = primitive_class(env, config)

            self.primitives[entity_id] = primitive

    def _wire_relationships(self) -> None:
        """Wire relationships between primitives."""
        for entity_id, entity in self.entities.items():
            primitive = self.primitives.get(entity_id)

            if not primitive:
                continue

            # Process each relationship type
            for rel_type, target_ids in entity.relationships.items():
                for target_id in target_ids:
                    target = self.primitives.get(target_id)

                    if not target:
                        continue

                    # Wire based on relationship type
                    if rel_type == "feeds_into":
                        # Set downstream connection
                        if hasattr(primitive, "downstream"):
                            primitive.downstream = target

                        # For equipment, also set buffer connections
                        if isinstance(primitive, EquipmentPrimitive):
                            if isinstance(target, BufferPrimitive):
                                primitive.downstream = target

                    elif rel_type == "draws_from":
                        # Set upstream connection
                        if hasattr(primitive, "upstream"):
                            primitive.upstream = target

                        # For equipment, also set buffer connections
                        if isinstance(primitive, EquipmentPrimitive):
                            if isinstance(target, BufferPrimitive):
                                primitive.upstream = target

                    # Track relationship in primitive
                    primitive.connect_to(target, rel_type)

    def _create_production_lines(self) -> None:
        """Create production line structures."""
        # Group entities by line
        lines: Dict[str, Dict[str, Any]] = {}

        for entity_id, entity in self.entities.items():
            # Get line ID from properties or relationships
            line_id = entity.properties.get("line_id", "DEFAULT")

            if line_id not in lines:
                lines[line_id] = {
                    "equipment": [],
                    "buffers": [],
                    "source": None,
                    "sink": None,
                }

            # Categorize by type
            if entity.ontology_class == "Source":
                lines[line_id]["source"] = self.primitives[entity_id]
            elif entity.ontology_class == "Sink":
                lines[line_id]["sink"] = self.primitives[entity_id]
            elif entity.ontology_class == "Buffer":
                lines[line_id]["buffers"].append(self.primitives[entity_id])
            elif entity.ontology_class in [
                "Equipment",
                "Filler",
                "Packer",
                "Palletizer",
            ]:
                lines[line_id]["equipment"].append(self.primitives[entity_id])

        self.production_lines = lines

    def _setup_scheduler(self, env: simpy.Environment) -> Optional[SchedulerPrimitive]:
        """Setup scheduler if configured.

        Args:
            env: SimPy environment

        Returns:
            Scheduler primitive or None
        """
        # Check for scheduler in manifests
        scheduler_config = self.manifests.get("schedule_manifest", {})

        if not scheduler_config and "SCHEDULER" not in self.primitives:
            # Create default scheduler
            config = PrimitiveConfig(
                id="SCHEDULER-DEFAULT",
                type="Scheduler",
                properties={
                    "schedule_horizon": 10080,  # 1 week
                    "optimization_mode": "FIFO",
                },
            )

            scheduler = SchedulerPrimitive(env, config)
            self.primitives["SCHEDULER-DEFAULT"] = scheduler

            # Register equipment with scheduler
            for entity_id, primitive in self.primitives.items():
                if isinstance(primitive, EquipmentPrimitive):
                    scheduler.register_equipment(entity_id, primitive)

            return scheduler

        # Return existing scheduler if present
        for primitive in self.primitives.values():
            if isinstance(primitive, SchedulerPrimitive):
                return primitive

        return None

    def _setup_monitor(self, env: simpy.Environment) -> Optional[MonitorPrimitive]:
        """Setup monitor if configured.

        Args:
            env: SimPy environment

        Returns:
            Monitor primitive or None
        """
        # Check for monitor in manifests
        monitor_config = self.manifests.get("monitor_manifest", {})

        if not monitor_config and "MONITOR" not in self.primitives:
            # Create default monitor
            config = PrimitiveConfig(
                id="MONITOR-DEFAULT",
                type="Monitor",
                properties={
                    "update_interval": 5.0,
                    "aggregation_window": 60.0,
                    "kpi_definitions": {
                        "overall_oee": {"type": "OEE", "target": 65.0, "unit": "%"},
                        "throughput": {
                            "type": "THROUGHPUT",
                            "target": 50.0,
                            "unit": "units/min",
                        },
                        "availability": {
                            "type": "AVAILABILITY",
                            "target": 90.0,
                            "unit": "%",
                        },
                        "quality": {"type": "QUALITY", "target": 98.0, "unit": "%"},
                    },
                },
            )

            monitor = MonitorPrimitive(env, config)
            self.primitives["MONITOR-DEFAULT"] = monitor

            # Register all primitives with monitor
            for entity_id, primitive in self.primitives.items():
                if entity_id not in ["MONITOR-DEFAULT", "SCHEDULER-DEFAULT"]:
                    monitor.register_primitive(entity_id, primitive)

            return monitor

        # Return existing monitor if present
        for primitive in self.primitives.values():
            if isinstance(primitive, MonitorPrimitive):
                return primitive

        return None

    def _start_all_primitives(self) -> None:
        """Start all instantiated primitives."""
        # Start in order: Buffers, Sources, Equipment, Sinks, Scheduler, Monitor
        start_order = [
            BufferPrimitive,
            SourcePrimitive,
            EquipmentPrimitive,
            SinkPrimitive,
            SchedulerPrimitive,
            MonitorPrimitive,
        ]

        for primitive_class in start_order:
            for primitive in self.primitives.values():
                if isinstance(primitive, primitive_class) and not primitive.is_running:
                    primitive.start()

    def get_controllable_parameters(self) -> Dict[str, Any]:
        """Get controllable parameters from ontology.

        Returns:
            Dictionary of parameter names to definitions
        """
        return self.ontology.get("controllables", {})

    def apply_parameter_changes(self, parameters: Dict[str, float]) -> None:
        """Apply parameter changes to running model.

        Args:
            parameters: Dictionary of parameter name to value
        """
        # This would be implemented to apply parameters to primitives
        # For now, parameters would be read from manifests
        pass

    def get_observables(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all observables from primitives.

        Returns:
            Dictionary of primitive ID to observable list
        """
        observables = {}

        for entity_id, primitive in self.primitives.items():
            if hasattr(primitive, "observables"):
                observables[entity_id] = primitive.observables

        return observables

    def get_model_structure(self) -> Dict[str, Any]:
        """Get model structure for analysis.

        Returns:
            Dictionary describing model structure
        """
        return {
            "entities": {
                entity_id: {
                    "class": entity.ontology_class,
                    "primitive": entity.primitive_type,
                    "relationships": entity.relationships,
                }
                for entity_id, entity in self.entities.items()
            },
            "lines": {
                line_id: {
                    "equipment_count": len(line["equipment"]),
                    "buffer_count": len(line["buffers"]),
                    "has_source": line["source"] is not None,
                    "has_sink": line["sink"] is not None,
                }
                for line_id, line in self.production_lines.items()
            },
            "controllables": list(self.get_controllable_parameters().keys()),
            "observable_types": list(self.ontology.get("observables", {}).keys()),
        }
