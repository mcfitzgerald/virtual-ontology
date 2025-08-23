Ontology-Driven Architecture
=============================

The twin model uses ontologies to define system structure, behavior, and semantics, enabling flexible and maintainable simulation models.

Ontology Structure
------------------

Twin Ontology Components
~~~~~~~~~~~~~~~~~~~~~~~~

The twin ontology (``ontology/twin_ontology.yaml``) defines:

.. code-block:: yaml

   twin_model:
     metadata:
       name: "Manufacturing Twin Model"
       version: "2.0.0"
       description: "Ontology for virtual twin simulation"
     
     # Primitive definitions
     primitives:
       Equipment:
         class: "EquipmentPrimitive"
         properties:
           processing_time:
             type: float
             unit: "minutes"
             description: "Time to process one item"
           failure_rate:
             type: float
             range: [0.0, 1.0]
             description: "Probability of failure"
         relationships:
           feeds_to:
             target: ["Buffer", "Sink"]
             cardinality: "1:N"
           receives_from:
             target: ["Buffer", "Source"]
             cardinality: "N:1"
     
     # Pattern definitions
     patterns:
       bottleneck:
         detection:
           trigger: "buffer_full"
           condition: "duration > threshold"
         impact:
           upstream: "blocking"
           downstream: "starvation"
     
     # System configurations
     configurations:
       production_lines:
         structure: "sequential"
         scheduling: "push"
         monitoring: "real-time"

MES Ontology Integration
~~~~~~~~~~~~~~~~~~~~~~~~

The MES ontology (``ontology/mes_ontology.yaml``) defines data semantics:

.. code-block:: yaml

   mes_data:
     entities:
       ProductionOrder:
         attributes:
           - id: string
           - product_type: string
           - quantity: integer
           - due_date: datetime
         relationships:
           - requires: Equipment
           - produces: Product
       
       MachineStatus:
         values:
           - Running
           - Idle
           - Maintenance
           - Failed
         transitions:
           Running -> Idle: "completion"
           Idle -> Running: "start"
           Running -> Failed: "failure"
           Failed -> Maintenance: "repair_start"

Model Builder Architecture
--------------------------

OntologyDrivenModelBuilder
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`twin_model.model_builder.OntologyDrivenModelBuilder` interprets ontologies:

.. code-block:: python

   from twin_model import OntologyDrivenModelBuilder
   from pathlib import Path
   
   class OntologyDrivenModelBuilder:
       def __init__(self, ontology_path: Path, manifest_dir: Path):
           # Load ontology
           self.ontology = self._load_ontology(ontology_path)
           
           # Load manifests
           self.manifests = self._load_manifests(manifest_dir)
           
           # Parse structure
           self.entities = self._parse_entities()
           self.relationships = self._parse_relationships()
           self.patterns = self._parse_patterns()
       
       def build_model(self, env: simpy.Environment):
           """Build simulation model from ontology"""
           # Create primitives
           primitives = self._instantiate_primitives(env)
           
           # Wire relationships
           self._connect_primitives(primitives)
           
           # Configure from manifests
           self._apply_configurations(primitives)
           
           # Setup monitors
           self._setup_monitoring(primitives)
           
           return Model(env, primitives)

Entity Parsing
~~~~~~~~~~~~~~

.. code-block:: python

   def _parse_entities(self) -> Dict[str, ModelEntity]:
       """Parse entities from ontology"""
       entities = {}
       
       for name, definition in self.ontology['primitives'].items():
           entity = ModelEntity(
               id=name,
               ontology_class=definition['class'],
               primitive_type=self._resolve_primitive_type(definition['class']),
               properties=definition.get('properties', {}),
               relationships=definition.get('relationships', {})
           )
           entities[name] = entity
       
       return entities
   
   def _resolve_primitive_type(self, class_name: str):
       """Map ontology class to primitive implementation"""
       mapping = {
           'EquipmentPrimitive': EquipmentPrimitive,
           'BufferPrimitive': BufferPrimitive,
           'SourcePrimitive': SourcePrimitive,
           'SinkPrimitive': SinkPrimitive,
           'SchedulerPrimitive': SchedulerPrimitive,
           'MonitorPrimitive': MonitorPrimitive
       }
       return mapping.get(class_name)

Relationship Wiring
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def _parse_relationships(self) -> List[Relationship]:
       """Parse relationships between entities"""
       relationships = []
       
       for line_name, line_def in self.ontology['production_lines'].items():
           for flow in line_def.get('flow', []):
               relationship = Relationship(
                   from_entity=flow['from'],
                   to_entity=flow['to'],
                   type=flow.get('type', 'material_flow'),
                   properties=flow.get('properties', {})
               )
               relationships.append(relationship)
       
       return relationships
   
   def _connect_primitives(self, primitives: Dict[str, BasePrimitive]):
       """Wire primitives based on relationships"""
       for rel in self.relationships:
           from_primitive = primitives[rel.from_entity]
           to_primitive = primitives[rel.to_entity]
           
           if rel.type == 'material_flow':
               from_primitive.set_output(to_primitive)
           elif rel.type == 'information_flow':
               from_primitive.add_observer(to_primitive)
           elif rel.type == 'control_flow':
               from_primitive.set_controller(to_primitive)

Manifest Integration
--------------------

Configuration Loading
~~~~~~~~~~~~~~~~~~~~~

Manifests provide concrete values for ontology-defined properties:

.. code-block:: yaml

   # manifests/equipment_manifest.yaml
   equipment:
     Line1_Equipment1:
       type: "Assembly"
       processing_time: 5.0
       failure_rate: 0.01
       mttr: 30.0
       mtbf: 1000.0
       capacity_per_hour: 100
       energy_consumption: 50.0
       
       # Custom properties
       custom:
         operator_required: true
         setup_time: 10.0
         changeover_matrix:
           ProductA_to_ProductB: 15.0
           ProductB_to_ProductA: 20.0

.. code-block:: python

   def _apply_configurations(self, primitives: Dict[str, BasePrimitive]):
       """Apply manifest configurations to primitives"""
       for name, primitive in primitives.items():
           # Find matching manifest entry
           manifest_config = self._find_manifest_config(name)
           
           if manifest_config:
               # Apply properties
               for prop, value in manifest_config.items():
                   if hasattr(primitive, prop):
                       setattr(primitive, prop, value)
                   else:
                       # Store as metadata
                       primitive.metadata[prop] = value
               
               # Validate against ontology
               self._validate_configuration(primitive, manifest_config)

Dynamic Model Construction
--------------------------

Production Line Builder
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ProductionLineBuilder:
       """Build production lines from ontology definitions"""
       
       def build_line(self, env: simpy.Environment, 
                     ontology: dict, 
                     line_name: str) -> ProductionLine:
           """Build a specific production line"""
           
           line_def = ontology['production_lines'][line_name]
           
           # Create components
           components = {}
           for comp in line_def['components']:
               primitive_class = self._get_primitive_class(comp['type'])
               config = self._get_component_config(comp['id'])
               
               component = primitive_class(
                   env=env,
                   name=comp['id'],
                   **config
               )
               components[comp['id']] = component
           
           # Establish flow
           for flow in line_def['flow']:
               from_comp = components[flow['from']]
               to_comp = components[flow['to']]
               
               # Create connection based on flow type
               if flow.get('buffer'):
                   # Insert buffer between components
                   buffer = BufferPrimitive(
                       env, f"Buffer_{flow['from']}_{flow['to']}",
                       capacity=flow['buffer']['capacity']
                   )
                   from_comp.set_output(buffer)
                   buffer.set_output(to_comp)
               else:
                   # Direct connection
                   from_comp.set_output(to_comp)
           
           return ProductionLine(env, line_name, components)

Pattern-Driven Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class PatternConfigurator:
       """Configure model based on pattern definitions"""
       
       def apply_patterns(self, model: Model, patterns: dict):
           """Apply pattern configurations to model"""
           
           for pattern_name, pattern_def in patterns.items():
               if pattern_name == "bottleneck":
                   self._configure_bottleneck_detection(model, pattern_def)
               elif pattern_name == "cascade_failure":
                   self._configure_cascade_detection(model, pattern_def)
               elif pattern_name == "quality_degradation":
                   self._configure_quality_monitoring(model, pattern_def)
       
       def _configure_bottleneck_detection(self, model, pattern_def):
           """Setup bottleneck detection"""
           
           # Configure buffer monitoring
           for buffer in model.get_buffers():
               buffer.set_threshold(
                   pattern_def['detection']['buffer_threshold']
               )
               buffer.on_threshold_exceeded = lambda b: 
                   self._detect_bottleneck(b, model)
           
           # Configure equipment monitoring
           for equipment in model.get_equipment():
               equipment.track_utilization = True
               equipment.utilization_window = pattern_def['detection']['window']

Runtime Ontology Updates
------------------------

Dynamic Reconfiguration
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class DynamicOntologyManager:
       """Manage runtime ontology updates"""
       
       def __init__(self, model: Model):
           self.model = model
           self.ontology = model.ontology
           self.version_history = []
       
       def update_ontology(self, updates: dict):
           """Apply ontology updates at runtime"""
           
           # Version the current ontology
           self.version_history.append(self.ontology.copy())
           
           # Apply updates
           for path, value in updates.items():
               self._update_path(path, value)
           
           # Reconfigure model
           self._reconfigure_model()
       
       def _update_path(self, path: str, value):
           """Update specific ontology path"""
           # Parse path (e.g., "primitives.Equipment.properties.processing_time")
           parts = path.split('.')
           target = self.ontology
           
           for part in parts[:-1]:
               target = target[part]
           
           target[parts[-1]] = value
       
       def _reconfigure_model(self):
           """Reconfigure model based on updated ontology"""
           
           # Update primitive configurations
           for primitive in self.model.primitives:
               config = self._get_updated_config(primitive.name)
               primitive.reconfigure(config)
           
           # Update relationships if changed
           self._update_relationships()
           
           # Notify observers
           self.model.notify_ontology_update()

Ontology Validation
-------------------

Schema Validation
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from jsonschema import validate
   
   class OntologyValidator:
       """Validate ontology against schema"""
       
       def __init__(self, schema_path: Path):
           self.schema = self._load_schema(schema_path)
       
       def validate(self, ontology: dict) -> List[str]:
           """Validate ontology and return errors"""
           errors = []
           
           try:
               validate(instance=ontology, schema=self.schema)
           except ValidationError as e:
               errors.append(str(e))
           
           # Custom validation rules
           errors.extend(self._validate_relationships(ontology))
           errors.extend(self._validate_patterns(ontology))
           
           return errors
       
       def _validate_relationships(self, ontology: dict) -> List[str]:
           """Validate relationship consistency"""
           errors = []
           
           # Check that all relationship targets exist
           for primitive, definition in ontology['primitives'].items():
               for rel_name, rel_def in definition.get('relationships', {}).items():
                   targets = rel_def.get('target', [])
                   for target in targets:
                       if target not in ontology['primitives']:
                           errors.append(
                               f"Invalid relationship target: {primitive}.{rel_name} -> {target}"
                           )
           
           return errors

Semantic Consistency
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class SemanticValidator:
       """Validate semantic consistency"""
       
       def validate_semantics(self, ontology: dict, manifests: dict) -> List[str]:
           """Check semantic consistency between ontology and manifests"""
           errors = []
           
           # Check property types
           for entity, manifest in manifests.items():
               ontology_def = self._find_ontology_definition(entity, ontology)
               
               if ontology_def:
                   for prop, value in manifest.items():
                       expected_type = ontology_def['properties'].get(prop, {}).get('type')
                       
                       if expected_type and not self._check_type(value, expected_type):
                           errors.append(
                               f"Type mismatch: {entity}.{prop} expected {expected_type}, got {type(value)}"
                           )
           
           # Check value ranges
           errors.extend(self._validate_ranges(ontology, manifests))
           
           # Check cardinality constraints
           errors.extend(self._validate_cardinality(ontology, manifests))
           
           return errors

Best Practices
--------------

Ontology Design
~~~~~~~~~~~~~~~

1. **Separation of Concerns**: Keep structure (ontology) separate from configuration (manifests)
2. **Versioning**: Version ontologies for backward compatibility
3. **Modularity**: Use modular ontology components that can be composed
4. **Documentation**: Document all properties and relationships
5. **Validation**: Define schemas and validation rules

Example Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

   ontology/
   ├── twin_ontology.yaml          # Main twin model ontology
   ├── mes_ontology.yaml           # MES data semantics
   ├── patterns/
   │   ├── bottleneck.yaml         # Bottleneck pattern definition
   │   ├── cascade.yaml            # Cascade failure pattern
   │   └── quality.yaml            # Quality degradation pattern
   └── schemas/
       ├── twin_schema.json        # JSON schema for validation
       └── mes_schema.json         # MES data schema
   
   manifests/
   ├── equipment_manifest.yaml     # Equipment configurations
   ├── production_manifest.yaml    # Production parameters
   └── scenarios/
       ├── baseline.yaml           # Baseline scenario
       ├── optimized.yaml          # Optimized parameters
       └── stressed.yaml           # Stress test scenario