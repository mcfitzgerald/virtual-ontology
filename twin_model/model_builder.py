"""Ontology-driven model builder for SimPy simulations.

This module builds SimPy models from the twin ontology structure and manifests.
Key features:
- NO BUFFERS - only internal equipment queues
- Direct equipment-to-equipment connections
- Two-layer control system integration
- Proper ontology interpretation
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
import yaml
import simpy
import logging
from collections import defaultdict

from twin_model.primitives import (
    BasePrimitive,
    PrimitiveConfig,
    EquipmentPrimitive,
    SourcePrimitive,
    SinkPrimitive,
    SchedulerPrimitive,
    MonitorPrimitive,
)
from twin_model.primitives.scheduler import ProductionOrder, Product, ProductCategory
from twin_model.control import ControlManager

logger = logging.getLogger(__name__)


@dataclass
class EntityDefinition:
    """Definition of an entity from ontology."""

    entity_id: str
    entity_class: str
    properties: Dict[str, Any]
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    primitive_type: Optional[str] = None


@dataclass
class LineConfiguration:
    """Configuration for a production line."""

    line_id: str
    source: Optional[EntityDefinition] = None
    equipment: List[EntityDefinition] = field(default_factory=list)
    sink: Optional[EntityDefinition] = None

    def get_equipment_sequence(self) -> List[EntityDefinition]:
        """Get equipment sorted by position."""
        return sorted(self.equipment, key=lambda e: e.properties.get("position", 0))


class OntologyDrivenModelBuilder:
    """Builds SimPy models from ontology structure and manifests.

    This builder:
    1. Interprets the twin ontology to understand structure
    2. Loads configuration from manifests
    3. Creates primitives with internal queues only
    4. Wires direct equipment connections
    5. Integrates two-layer control system
    """

    # Primitive class mapping
    PRIMITIVE_CLASSES = {
        "EquipmentPrimitive": EquipmentPrimitive,
        "SourcePrimitive": SourcePrimitive,
        "SinkPrimitive": SinkPrimitive,
        "SchedulerPrimitive": SchedulerPrimitive,
        "MonitorPrimitive": MonitorPrimitive,
    }

    def __init__(
        self,
        env: simpy.Environment,
        ontology_path: Path,
        manifest_dir: Path,
        control_manager: Optional[ControlManager] = None,
        config_path: Optional[Path] = None,
    ) -> None:
        """Initialize model builder.

        Args:
            env: SimPy environment
            ontology_path: Path to twin_ontology.yaml
            manifest_dir: Directory containing manifest files
            control_manager: Optional control manager for two-layer system
            config_path: Optional path to twin_model.yaml config file

        """
        self.env = env
        self.ontology_path = ontology_path
        self.manifest_dir = manifest_dir
        self.control_manager = control_manager
        self.config_path = config_path or Path("config/twin_model.yaml")

        # Load ontology
        self.ontology = self._load_yaml(ontology_path)

        # Load technical configuration
        if self.config_path.exists():
            self.technical_config = self._load_yaml(self.config_path)
        else:
            self.technical_config = {}
            logger.warning(f"Technical config not found at {self.config_path}")

        # Load manifests (including system_config.yaml)
        self.manifests = self._load_manifests(manifest_dir)
        
        # Extract system config if present
        self.system_config = self.manifests.get("system_config", {})

        # Parse ontology structure
        self.classes = self._parse_classes()
        self.relationships = self._parse_relationships()
        self.mappings = self._parse_mappings()

        # Storage for created entities
        self.entities: Dict[str, EntityDefinition] = {}
        self.primitives: Dict[str, BasePrimitive] = {}
        self.lines: Dict[str, LineConfiguration] = {}

        # Build flags
        self.built = False

        logger.info(f"Model builder initialized with ontology from {ontology_path}")

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file."""
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _load_manifests(self, manifest_dir: Path) -> Dict[str, Any]:
        """Load all manifest files from directory."""
        manifests = {}

        for file_path in manifest_dir.glob("*.yaml"):
            manifest_name = file_path.stem
            manifests[manifest_name] = self._load_yaml(file_path)
            logger.debug(f"Loaded manifest: {manifest_name}")

        return manifests

    def _parse_classes(self) -> Dict[str, Any]:
        """Parse class definitions from TBox."""
        tbox = self.ontology.get("tbox", {})
        return tbox.get("classes", {})
    
    def _get_ontology_defaults(self, class_name: str) -> Dict[str, Any]:
        """Get default property values from ontology class definition.
        
        Args:
            class_name: Name of the class to get defaults for
            
        Returns:
            Dictionary of property defaults
        """
        defaults = {}
        class_def = self.classes.get(class_name, {})
        properties = class_def.get("properties", {})
        
        for prop_name, prop_def in properties.items():
            if "default" in prop_def:
                defaults[prop_name] = prop_def["default"]
        
        # Also check parent class
        parent = class_def.get("parent")
        if parent and parent in self.classes:
            parent_defaults = self._get_ontology_defaults(parent)
            # Parent defaults are overridden by child defaults
            defaults = {**parent_defaults, **defaults}
        
        return defaults

    def _parse_relationships(self) -> Dict[str, Any]:
        """Parse relationships from RBox."""
        rbox = self.ontology.get("rbox", {})
        return rbox.get("relationships", {})

    def _parse_mappings(self) -> Dict[str, str]:
        """Parse primitive mappings."""
        mappings = self.ontology.get("mappings", {})
        return mappings.get("primitives", {})

    def build_model(self) -> Dict[str, Any]:
        """Build complete simulation model from ontology and manifests.

        Returns:
            Dictionary containing model components

        """
        if self.built:
            logger.warning("Model already built, rebuilding...")

        # Step 1: Load entities from manifests
        self._load_entities()

        # Step 2: Organize by production lines
        self._organize_lines()

        # Step 3: Create primitives
        self._create_primitives()

        # Step 4: Wire connections (internal queues only!)
        self._wire_connections()

        # Step 5: Create scheduler if orders exist
        scheduler = self._create_scheduler()

        # Step 6: Create monitors
        monitors = self._create_monitors()

        # Step 7: Apply control parameters
        if self.control_manager:
            self._apply_control_parameters()

        self.built = True

        return {
            "entities": self.entities,
            "primitives": self.primitives,
            "lines": self.lines,
            "scheduler": scheduler,
            "monitors": monitors,
        }

    def _load_entities(self) -> None:
        """Load entity definitions from manifests."""
        # Load equipment from equipment manifest
        equipment_manifest = self.manifests.get("equipment_manifest", {})
        equipment_data = equipment_manifest.get("equipment", {})

        for entity_id, properties in equipment_data.items():
            entity_type = properties.get("type", "Equipment")

            # Determine primitive type from ontology mapping
            primitive_type = self.mappings.get(entity_type)

            # Create entity definition
            entity = EntityDefinition(
                entity_id=entity_id, entity_class=entity_type, properties=properties, primitive_type=primitive_type
            )

            self.entities[entity_id] = entity

        # Load scheduler from scheduler manifest if it exists
        scheduler_manifest = self.manifests.get("scheduler_manifest", {})
        for entity_id, value in scheduler_manifest.items():
            if entity_id != "metadata" and isinstance(value, dict):
                entity_type = value.get("type", "scheduler")

                # Create entity definition for scheduler
                entity = EntityDefinition(
                    entity_id=entity_id,
                    entity_class=entity_type,
                    properties=value.get("properties", {}),
                    primitive_type="Scheduler",
                )
                entity.name = value.get("name", "Scheduler")

                self.entities[entity_id] = entity

        logger.info(f"Loaded {len(self.entities)} entities from manifests")

    def _organize_lines(self) -> None:
        """Organize entities into production lines."""
        # Group by line_id
        lines_dict: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"equipment": [], "source": None, "sink": None})

        for entity_id, entity in self.entities.items():
            line_id = entity.properties.get("line_id")
            if not line_id:
                continue

            entity_class = entity.entity_class

            if entity_class == "Source":
                lines_dict[line_id]["source"] = entity
            elif entity_class == "Sink":
                lines_dict[line_id]["sink"] = entity
            elif entity_class in ["Filler", "Packer", "Palletizer", "Equipment"]:
                lines_dict[line_id]["equipment"].append(entity)

        # Create line configurations
        for line_id, components in lines_dict.items():
            line_config = LineConfiguration(
                line_id=line_id, source=components["source"], equipment=components["equipment"], sink=components["sink"]
            )
            self.lines[line_id] = line_config

        logger.info(f"Organized {len(self.lines)} production lines")

    def _create_primitives(self) -> None:
        """Create SimPy primitives from entity definitions."""
        for entity_id, entity in self.entities.items():
            primitive_type = entity.primitive_type

            if not primitive_type:
                logger.debug(f"No primitive mapping for {entity_id}")
                continue

            # Get primitive class
            primitive_class = self.PRIMITIVE_CLASSES.get(primitive_type)
            if not primitive_class:
                logger.warning(f"Unknown primitive type: {primitive_type}")
                continue

            # Get ontology defaults for this class
            ontology_defaults = self._get_ontology_defaults(entity.entity_class)
            
            # Merge properties: ontology defaults < manifest properties
            merged_properties = {**ontology_defaults, **entity.properties}
            
            # Add references to system configurations
            merged_properties["_system_config"] = self.system_config
            merged_properties["_technical_config"] = self.technical_config
            
            # Create configuration
            config = PrimitiveConfig(
                id=entity_id,
                type=entity.entity_class,
                properties=merged_properties,
                metadata={"name": entity.properties.get("name", entity_id)},
            )

            # Create primitive based on type
            if primitive_type == "EquipmentPrimitive":
                # Equipment with internal queues only!
                primitive = primitive_class(env=self.env, config=config)
                # Equipment always uses internal queues

            elif primitive_type == "SourcePrimitive":
                primitive = primitive_class(
                    env=self.env,
                    config=config,
                    downstream=None,  # Will be wired to equipment input queue
                )

            elif primitive_type == "SinkPrimitive":
                primitive = primitive_class(
                    env=self.env,
                    config=config,
                    upstream=None,  # Will be wired to equipment output queue
                )

            else:
                # Generic primitive creation
                primitive = primitive_class(env=self.env, config=config)

            self.primitives[entity_id] = primitive

        logger.info(f"Created {len(self.primitives)} primitives")

    def _wire_connections(self) -> None:
        """Wire direct equipment-to-equipment connections using internal queues.

        This is the key architecture:
        - NO separate buffer entities
        - Direct equipment connections via internal queues
        - Source feeds first equipment's input queue
        - Sink collects from last equipment's output queue
        """
        for line_id, line_config in self.lines.items():
            # Get equipment in sequence
            equipment_sequence = line_config.get_equipment_sequence()

            if not equipment_sequence:
                logger.warning(f"No equipment in line {line_id}")
                continue

            # Get primitives
            equipment_primitives = []
            for entity in equipment_sequence:
                primitive = self.primitives.get(entity.entity_id)
                if primitive:
                    equipment_primitives.append(primitive)

            if not equipment_primitives:
                logger.warning(f"No equipment primitives for line {line_id}")
                continue

            # Wire source to first equipment
            if line_config.source:
                source_primitive = self.primitives.get(line_config.source.entity_id)
                if source_primitive and equipment_primitives:
                    first_equipment = equipment_primitives[0]
                    if hasattr(first_equipment, "input_queue"):
                        source_primitive.downstream = first_equipment.input_queue
                        logger.debug(
                            f"Connected {line_config.source.entity_id} to {first_equipment.config.id}.input_queue"
                        )
                    else:
                        logger.error(f"Equipment {first_equipment.config.id} has no input_queue!")

            # Wire equipment to equipment
            for i in range(len(equipment_primitives) - 1):
                current = equipment_primitives[i]
                next_eq = equipment_primitives[i + 1]

                if hasattr(current, "connect_to"):
                    current.connect_to(next_eq)
                    logger.debug(f"Connected {current.config.id} to {next_eq.config.id}")
                else:
                    # Manual connection if connect_to not available
                    if hasattr(current, "output_queue") and hasattr(next_eq, "input_queue"):
                        current.downstream_equipment = next_eq
                        next_eq.upstream_equipment = current
                        logger.debug(f"Manually connected {current.config.id} to {next_eq.config.id}")

            # Wire last equipment to sink
            if line_config.sink and equipment_primitives:
                sink_primitive = self.primitives.get(line_config.sink.entity_id)
                last_equipment = equipment_primitives[-1]
                if sink_primitive and hasattr(last_equipment, "output_queue"):
                    sink_primitive.upstream = last_equipment.output_queue
                    last_equipment.downstream = sink_primitive
                    logger.debug(f"Connected {last_equipment.config.id}.output_queue to {line_config.sink.entity_id}")

        logger.info("Wiring complete - internal queues only, no buffers!")

    def _create_scheduler(self) -> Optional[SchedulerPrimitive]:
        """Create scheduler with order management."""
        # Check for scheduler in manifests
        scheduler_entity = None
        scheduler_id = None
        for entity_id, entity_def in self.entities.items():
            # Check both entity_class and type property for scheduler
            is_scheduler = (
                entity_def.entity_class.lower() == "scheduler"
                or entity_def.properties.get("type", "").lower() == "scheduler"
            )
            if is_scheduler:
                scheduler_entity = entity_def
                scheduler_id = entity_id
                break

        if not scheduler_entity:
            logger.info("No scheduler entity found in manifests")
            return None

        # Create scheduler
        scheduler_config = PrimitiveConfig(
            id=scheduler_id or "SCHEDULER",
            type="Scheduler",
            properties=scheduler_entity.properties,
            metadata={"name": scheduler_entity.properties.get("name", "Production Scheduler")},
        )
        scheduler = SchedulerPrimitive(env=self.env, config=scheduler_config)

        # Register sources with scheduler
        for line_id, line_config in self.lines.items():
            if line_config.source:
                source_primitive = self.primitives.get(line_config.source.entity_id)
                if source_primitive:
                    scheduler.register_source(line_id, source_primitive)
                    logger.debug(f"Registered source {line_config.source.entity_id} for {line_id}")

        # Store scheduler in primitives
        self.primitives["SCHEDULER"] = scheduler

        # Start scheduler process
        self.env.process(scheduler.run())

        logger.info("Created scheduler with order management")
        return scheduler

    def _create_scheduler(self) -> Optional[SchedulerPrimitive]:
        """Create scheduler and load production orders."""
        # Check if production manifest exists
        production_manifest = self.manifests.get("production_manifest", {})
        if not production_manifest:
            logger.info("No production manifest found")
            return None

        orders_data = production_manifest.get("production_orders", [])
        if not orders_data:
            logger.info("No production orders found")
            return None

        # Create scheduler
        scheduler_config = PrimitiveConfig(
            id="SCHEDULER",
            type="Scheduler",
            properties={"schedule_horizon": 7},
            metadata={"name": "Production Scheduler"},
        )
        scheduler = SchedulerPrimitive(env=self.env, config=scheduler_config)

        # Register sources with scheduler
        for line_id, line_config in self.lines.items():
            if line_config.source:
                source_primitive = self.primitives.get(line_config.source.entity_id)
                if source_primitive:
                    scheduler.register_source(line_id, source_primitive)

        # Load production orders
        products = production_manifest.get("products", {})
        for order_data in orders_data:
            # Create production order
            product_id = order_data.get("product_id")
            product_info = products.get(product_id, {})

            # Create Product object
            product = Product(
                product_id=product_id,
                category=ProductCategory[product_info.get("category", "B")],
                family=product_info.get("family", "default"),
                volume_rank=product_info.get("volume_rank", 1),
                margin=product_info.get("margin", 0.1),
                complexity=product_info.get("complexity", 0.5),
                typical_batch_size=product_info.get("typical_batch_size", 100),
                min_batch_size=product_info.get("min_batch_size", 50),
                max_batch_size=product_info.get("max_batch_size", 200),
            )
            
            # Create ProductionOrder object
            order = ProductionOrder(
                order_id=order_data.get("order_id"),
                product=product,
                quantity=order_data.get("target_quantity"),
                due_date=order_data.get("due_date", float("inf")),
                priority=order_data.get("priority", 1),
                line_id=order_data.get("line_id", "LINE1"),  # Add line assignment
                release_date=order_data.get("start_time", 0),
            )

            scheduler.add_order(order)

        logger.info(f"Created scheduler with {len(orders_data)} orders")
        return scheduler

    def _create_monitors(self) -> List[MonitorPrimitive]:
        """Create monitors for KPI tracking."""
        monitors = []

        # Create a monitor for each line
        for line_id, line_config in self.lines.items():
            monitor_config = PrimitiveConfig(
                id=f"MONITOR-{line_id}",
                type="Monitor",
                properties={"monitoring_interval": 5.0},
                metadata={"name": f"Monitor for {line_id}"},
            )
            monitor = MonitorPrimitive(env=self.env, config=monitor_config)

            # Register equipment with monitor
            # Note: Monitor interface for equipment registration
            # for entity in line_config.equipment:
            #     primitive = self.primitives.get(entity.entity_id)
            #     if primitive:
            #         monitor.register_equipment(primitive)

            monitors.append(monitor)

        logger.info(f"Created {len(monitors)} monitors")
        return monitors

    def _apply_control_parameters(self) -> None:
        """Apply control system parameters to primitives."""
        if not self.control_manager:
            return

        # Get current parameters
        params = self.control_manager.get_all_parameters()

        # Apply to equipment
        for entity_id, primitive in self.primitives.items():
            if hasattr(primitive, "performance_factor"):  # Check if it's equipment
                # Apply performance parameters
                if "performance_factor" in params:
                    primitive.performance_factor = params["performance_factor"]

                # Apply failure parameters
                if "micro_stop_probability" in params:
                    primitive.micro_stop_probability = params["micro_stop_probability"]
                    primitive.config.properties["micro_stop_probability"] = params["micro_stop_probability"]

                # Apply quality parameters
                if "scrap_rate" in params:
                    primitive.scrap_rate = params["scrap_rate"]
                    primitive.config.properties["scrap_rate"] = params["scrap_rate"]

        logger.info("Applied control parameters to primitives")

    def start_processes(self) -> None:
        """Start all simulation processes."""
        if not self.built:
            raise RuntimeError("Model must be built before starting processes")

        # Start equipment processes
        for entity_id, primitive in self.primitives.items():
            if hasattr(primitive, "run"):
                self.env.process(primitive.run())
                logger.debug(f"Started process for {entity_id}")

        logger.info("All simulation processes started")

    def get_line_status(self, line_id: str) -> Dict[str, Any]:
        """Get current status of a production line.

        Args:
            line_id: Line identifier

        Returns:
            Status dictionary

        """
        if line_id not in self.lines:
            return {"error": f"Unknown line: {line_id}"}

        line_config = self.lines[line_id]
        status = {"line_id": line_id, "equipment": []}

        for entity in line_config.get_equipment_sequence():
            primitive = self.primitives.get(entity.entity_id)
            if primitive and isinstance(primitive, EquipmentPrimitive):
                eq_status = {
                    "id": entity.entity_id,
                    "state": primitive.state.value if hasattr(primitive, "state") else "UNKNOWN",
                    "units_produced": getattr(primitive, "units_produced", 0),
                    "units_scrapped": getattr(primitive, "units_scrapped", 0),
                }

                # Add queue levels if using internal queues
                if hasattr(primitive, "input_queue"):
                    eq_status["input_queue_level"] = len(primitive.input_queue.items)
                if hasattr(primitive, "output_queue"):
                    eq_status["output_queue_level"] = len(primitive.output_queue.items)

                status["equipment"].append(eq_status)

        return status

    def describe_model(self) -> str:
        """Get human-readable description of the model.

        Returns:
            Description string

        """
        desc = "=== Twin Model ===\n"
        desc += f"Lines: {len(self.lines)}\n"
        desc += f"Entities: {len(self.entities)}\n"
        desc += f"Primitives: {len(self.primitives)}\n\n"

        for line_id, line_config in self.lines.items():
            desc += f"Line {line_id}:\n"

            if line_config.source:
                desc += f"  Source: {line_config.source.entity_id}\n"

            desc += "  Equipment chain:\n"
            for entity in line_config.get_equipment_sequence():
                desc += f"    {entity.entity_id} (pos {entity.properties.get('position', 0)})\n"

            if line_config.sink:
                desc += f"  Sink: {line_config.sink.entity_id}\n"

            desc += "\n"

        desc += "Material flow: Source → Equipment.input_queue → Process → Equipment.output_queue → Next\n"
        desc += "NO BUFFERS - Internal queues only!\n"

        return desc
