# Ontology Guide

## Overview

The Virtual Twin Model uses an ontology-driven approach to define the structure, relationships, and constraints of the production system. This guide explains the ontology structure, how it drives model building, and how to extend it for new requirements.

## Ontology Structure (TBox/RBox)

### TBox (Terminological Box)
Defines the vocabulary - classes, properties, and their hierarchies.

### RBox (Role Box)  
Defines relationships and constraints between entities.

## File Organization

```
ontology/
├── twin_ontology.yaml      # Main ontology definition
├── control_mappings.yaml   # Control-to-parameter mappings
└── templates/
    └── twin_ontology_template.yaml  # Template for new ontologies

manifests/
├── system_config.yaml      # System-wide configuration
├── production_manifest.yaml # Production line definitions
├── equipment_manifest.yaml  # Equipment specifications
├── scheduler_manifest.yaml  # Scheduler and products
└── control_settings.yaml   # Control initial values
```

## Twin Ontology Structure

### 1. Metadata Section
```yaml
metadata:
  name: "Virtual Twin Ontology"
  version: "2.0.0"
  description: "Production system digital twin"
  created: "2024-12-19"
  author: "System Architect"
```

### 2. TBox - Class Definitions

#### Entity Classes
```yaml
tbox:
  classes:
    Entity:
      description: "Base class for all system entities"
      properties:
        - id: "Unique identifier"
        - name: "Human-readable name"
        - type: "Entity type"
    
    Equipment:
      parent: "Entity"
      description: "Processing equipment"
      properties:
        - line_id: "Production line assignment"
        - mtbf: "Mean time between failures"
        - mttr: "Mean time to repair"
        - performance_rate: "Nominal speed"
    
    Source:
      parent: "Entity"
      description: "Material generation point"
      properties:
        - arrival_rate: "Units per minute"
        - order_mode: "Order-driven or continuous"
    
    Sink:
      parent: "Entity"
      description: "Material collection point"
      properties:
        - line_id: "Associated production line"
```

#### Property Types
```yaml
property_types:
  mtbf:
    type: "float"
    unit: "minutes"
    range: [60, 10000]
  
  performance_rate:
    type: "float"
    unit: "units/minute"
    range: [0.1, 1000]
```

### 3. RBox - Relationships and Rules

#### Relationships
```yaml
rbox:
  relationships:
    feeds_into:
      domain: ["Source", "Equipment"]
      range: ["Equipment", "Sink"]
      cardinality: "1:1"
      description: "Material flow connection"
    
    belongs_to_line:
      domain: ["Equipment", "Source", "Sink"]
      range: ["ProductionLine"]
      cardinality: "N:1"
      description: "Line assignment"
```

#### Rules and Constraints
```yaml
rules:
  - id: "unique_equipment_id"
    description: "Equipment IDs must be unique"
    type: "uniqueness"
    applies_to: "Equipment.id"
  
  - id: "valid_line_assignment"
    description: "Equipment must belong to defined line"
    type: "reference_integrity"
    condition: "Equipment.line_id IN ProductionLine.id"
  
  - id: "mtbf_greater_than_mttr"
    description: "MTBF must exceed MTTR"
    type: "value_constraint"
    condition: "Equipment.mtbf > Equipment.mttr"
```

## Manifest System

### 1. Production Manifest
Defines production lines and their structure:

```yaml
# manifests/production_manifest.yaml
entities:
  LINE1:
    entity_class: "ProductionLine"
    name: "High-Speed Line 1"
    properties:
      capacity: 120  # units/min
      products: ["Beverages", "Juices"]
      shift_pattern: "3-shift"
    
    equipment_sequence:
      - LINE1-SRC   # Source
      - LINE1-FIL   # Filler
      - LINE1-PCK   # Packer
      - LINE1-PAL   # Palletizer
      - LINE1-SINK  # Sink
```

### 2. Equipment Manifest
Detailed equipment specifications:

```yaml
# manifests/equipment_manifest.yaml
entities:
  LINE1-FIL:
    entity_class: "Equipment"
    name: "Line 1 Filler"
    properties:
      equipment_type: "FILLER"
      line_id: "LINE1"
      
      # Performance parameters
      processing_time_base: 0.5  # seconds
      performance_rate: 85  # units/min
      queue_capacity: 20
      
      # Reliability parameters
      mtbf_base: 240  # minutes
      mttr_base: 15   # minutes
      micro_stop_frequency_base: 0.02
      micro_stop_duration: 0.5
      
      # Quality parameters
      scrap_rate_base: 0.02
      rework_rate: 0.01
```

### 3. Scheduler Manifest
Product definitions and scheduling configuration:

```yaml
# manifests/scheduler_manifest.yaml
SCHEDULER-1:
  type: "scheduler"
  name: "Production Scheduler"
  properties:
    sequencing_strategy: "changeover_optimized"
    campaign_size: 100
    lookahead_horizon: 480
    
    products:
      SKU-1001:
        family: "Beverages"
        category: "A"  # High volume
        volume_rank: 1
        margin: 0.35
        complexity: 0.3
        typical_batch: 100
        min_batch: 50
        max_batch: 200
```

## Model Building Process

### 1. Ontology Loading
```python
# Model builder loads ontology
ontology = load_yaml('ontology/twin_ontology.yaml')
validate_ontology(ontology)
```

### 2. Manifest Processing
```python
# Load all manifests
manifests = load_manifests('manifests/')
entities = merge_entities(manifests)
```

### 3. Entity Instantiation
```python
# Create primitives based on entity class
for entity_id, entity_def in entities.items():
    if entity_def.entity_class == 'Equipment':
        primitive = create_equipment(entity_def)
    elif entity_def.entity_class == 'Source':
        primitive = create_source(entity_def)
    # ...
```

### 4. Relationship Wiring
```python
# Connect equipment based on relationships
for line in production_lines:
    sequence = line.equipment_sequence
    for i in range(len(sequence)-1):
        wire_connection(sequence[i], sequence[i+1])
```

## Extending the Ontology

### 1. Adding New Entity Classes

To add a new type of equipment (e.g., Inspector):

```yaml
# In twin_ontology.yaml TBox
Inspector:
  parent: "Equipment"
  description: "Quality inspection station"
  properties:
    - inspection_time: "Time per unit"
    - rejection_rate: "Quality threshold"
    - sampling_rate: "Fraction inspected"
```

### 2. Adding New Relationships

To add supplier relationships:

```yaml
# In twin_ontology.yaml RBox
supplies_material:
  domain: ["Supplier"]
  range: ["Source"]
  cardinality: "N:N"
  description: "Material supply relationship"
```

### 3. Adding New Rules

To enforce minimum buffer sizes:

```yaml
# In twin_ontology.yaml rules
- id: "minimum_buffer_size"
  description: "Buffers must have minimum capacity"
  type: "value_constraint"
  condition: "Equipment.queue_capacity >= 5"
```

## Best Practices

### 1. Entity Naming Conventions
- **Lines**: `LINE1`, `LINE2`, `LINE3`
- **Equipment**: `{LINE}-{TYPE}` (e.g., `LINE1-FIL`)
- **Sources/Sinks**: `{LINE}-SRC`, `{LINE}-SINK`
- **Products**: `SKU-{NUMBER}` (e.g., `SKU-1001`)

### 2. Property Value Ranges
Always specify reasonable ranges:
```yaml
mtbf_base:
  default: 240
  min: 60      # At least 1 hour
  max: 10000   # About 1 week
```

### 3. Relationship Cardinality
Be explicit about cardinality:
- `1:1` - One-to-one (e.g., equipment to downstream)
- `N:1` - Many-to-one (e.g., equipment to line)
- `N:N` - Many-to-many (e.g., products to lines)

### 4. Rule Validation
Ensure rules are:
- **Checkable**: Can be validated programmatically
- **Meaningful**: Prevent real configuration errors
- **Documented**: Clear description of why rule exists

## Common Patterns

### 1. Line Definition Pattern
```yaml
LINE{N}:
  entity_class: "ProductionLine"
  equipment_sequence: [source, equipment1, ..., sink]
  properties:
    capacity: {value}
    products: [list]
```

### 2. Equipment Chain Pattern
```yaml
equipment_sequence:
  - SOURCE
  - EQUIPMENT_1
  - EQUIPMENT_2
  - ...
  - SINK
```

### 3. Product Family Pattern
```yaml
products:
  SKU-1xxx:  # Beverages family
    family: "Beverages"
  SKU-2xxx:  # Juices family
    family: "Juices"
```

## Validation

### 1. Ontology Validation
The system validates:
- Class hierarchy consistency
- Property type compliance
- Relationship domain/range
- Rule satisfaction

### 2. Manifest Validation
Checks for:
- Required properties present
- Value within specified ranges
- Reference integrity
- Unique identifiers

### 3. Runtime Validation
During model building:
- Equipment sequence connectivity
- Line assignment consistency
- Control parameter bounds
- Schedule feasibility

## Troubleshooting Ontology Issues

### Common Issues

1. **Missing Property**
   ```
   Error: Required property 'line_id' missing
   Solution: Add property to entity definition
   ```

2. **Invalid Reference**
   ```
   Error: Reference to undefined line 'LINE4'
   Solution: Ensure all referenced entities exist
   ```

3. **Rule Violation**
   ```
   Error: MTBF (50) less than MTTR (60)
   Solution: Adjust values to satisfy constraint
   ```

### Debugging Tools

1. **Ontology Validator**
   ```python
   python validate_ontology.py ontology/twin_ontology.yaml
   ```

2. **Manifest Checker**
   ```python
   python check_manifests.py manifests/
   ```

3. **Relationship Graph**
   ```python
   python visualize_ontology.py --output graph.png
   ```

## Summary

The ontology-driven approach provides:
- **Flexibility**: Configure without code changes
- **Consistency**: Enforced relationships and rules
- **Extensibility**: Easy to add new entity types
- **Validation**: Built-in constraint checking
- **Documentation**: Self-describing system structure

This architecture enables domain experts to configure production systems without programming knowledge while maintaining system integrity through validation rules.