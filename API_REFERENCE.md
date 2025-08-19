# API Reference

## Primitives

### BasePrimitive
Base class for all simulation primitives.

**Methods:**
- `start()`: Start the primitive's processes
- `emit_observable(event_type, details, severity)`: Emit observable event
- `stop()`: Stop the primitive

### Equipment
Production equipment with state management.

**States:**
- IDLE, RUNNING, STOPPED_FAILURE, STOPPED_MATERIAL, STARVED, BLOCKED, CHANGEOVER, MAINTENANCE

**Methods:**
- `process_unit()`: Process single unit
- `configure_for_product(product_id, order_id)`: Configure for product
- `perform_changeover(new_product)`: Execute changeover

### Buffer
Material storage primitive.

**Methods:**
- `put(quantity, product_id)`: Add items to buffer
- `get(quantity)`: Remove items from buffer
- `peek()`: Check next item without removing

## Transduction

### MESTransducer
Converts observables to MES format.

**Methods:**
- `process_observables(observables, manifests)`: Convert to MES DataFrame
- `save_to_csv(df, filepath)`: Save MES data
- `generate_summary_statistics(df)`: Calculate summary stats

## Model Builder

### OntologyDrivenModelBuilder
Builds simulation models from ontology.

**Methods:**
- `build_model(env)`: Build complete simulation model
- `load_ontology()`: Load ontology definition
- `load_manifests()`: Load configuration manifests
