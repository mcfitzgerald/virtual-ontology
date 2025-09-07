# Fix Hardcoded Parameters in Twin Model

## Problem Summary

The OntologyModelBuilder has extensive hardcoded default values that prevent proper configuration from being applied. This caused the simulation to produce only 1.9% of the target 8.4M units because sources defaulted to 60 units/minute instead of the required 300+ units/minute.

## Identified Hardcoded Values

### In `twin_model/ontology_model_builder.py`:

```python
# Line 250: Sources
generation_rate=params.get("generation_rate", 60.0)  # Should be ~300 for our target

# Line 292: Sinks  
collection_rate=params.get("collection_rate", 50.0)  # Should be ~300 for our target

# Line 319: Equipment
nominal_rate=params.get("nominal_rate", 50.0)  # Should be 90+ for our equipment

# Other hardcodes:
- max_input_rate: 60.0, 100.0 (varies)
- max_output_rate: 50.0, 60.0 (varies)  
- internal_capacity: 500.0, 1000.0, 10000.0 (varies)
- quality_rate: 0.95
- performance_factor: 0.85
- batch_size: 10.0
- processing_interval: 0.1
- mtbf: 60.0
- mttr: 10.0
- fill_rate: 50.0
- pack_size: 12
- pallet_size: 144
```

## Configuration Structure Issues

### Current Parameter Loading Flow:

1. **OntologyModelBuilder._create_equipment()** loads parameters:
   ```python
   eq_params = self.config["equipment_parameters"].get(equipment_id, {})
   flow_params = self.config["flow_capacity"]["equipment"].get(equipment_id, {})
   ```

2. **Parameter Merging Issue**:
   - `eq_params` gets merged with `config["defaults"]["equipment"]`
   - `flow_params` gets merged with `config["flow_capacity"]["defaults"]`
   - BUT: Special parameters like `collection_rate` for sinks are looked for in `eq_params` but we put them in `flow_params`

3. **Configuration Confusion**:
   - Sink `collection_rate` is in `flow_capacity.equipment.LINE1-SINK`
   - But code expects it in `equipment_parameters.LINE1-SINK`
   - Same issue may affect other equipment-specific parameters

## Recommended Long-Term Fix Implementation

### Phase 1: Enhance Parameter Loading in OntologyModelBuilder

The core issue is that parameters can come from multiple configuration sections, and the code needs to check all of them in a logical order. Here's the comprehensive fix:

```python
# In twin_model/ontology_model_builder.py

def _create_source(self, source_id: str, params: Dict[str, Any], flow_params: Dict[str, Any]) -> None:
    """Create source primitive with proper parameter resolution."""
    
    # Get defaults from config, not hardcoded
    source_defaults = self.config.get("defaults", {}).get("source", {})
    
    # Parameter resolution order: equipment_params -> flow_params -> defaults
    generation_rate = (
        params.get("generation_rate") or 
        flow_params.get("generation_rate") or
        source_defaults.get("generation_rate", 300.0)  # Last resort fallback
    )
    generation_interval = (
        params.get("generation_interval") or
        flow_params.get("generation_interval") or
        source_defaults.get("generation_interval", 0.1)
    )
    
    # Log what we're using
    logger.info(f"Creating {source_id}:")
    logger.info(f"  generation_rate: {generation_rate} (from: {self._get_param_source('generation_rate', params, flow_params, source_defaults)})")
    
    # Create flow capacity with same pattern
    capacity = FlowCapacity(
        max_input_rate=flow_params.get("max_input_rate") or source_defaults.get("max_input_rate", 350.0),
        max_output_rate=flow_params.get("max_output_rate") or source_defaults.get("max_output_rate", 350.0),
        internal_capacity=flow_params.get("internal_capacity") or source_defaults.get("internal_capacity", 1000.0),
        initial_level=flow_params.get("initial_level", 0.0)
    )
    
    # Continue with source creation...

def _create_sink(self, sink_id: str, params: Dict[str, Any], flow_params: Dict[str, Any]) -> None:
    """Create sink primitive with proper parameter resolution."""
    
    sink_defaults = self.config.get("defaults", {}).get("sink", {})
    
    # Collection rate logically belongs in flow_params, but check both
    collection_rate = (
        flow_params.get("collection_rate") or
        params.get("collection_rate") or
        sink_defaults.get("collection_rate", 300.0)
    )
    
    logger.info(f"Creating {sink_id}: collection_rate={collection_rate}")
    # Continue with sink creation...

def _get_param_source(self, param_name: str, params: Dict, flow_params: Dict, defaults: Dict) -> str:
    """Helper to identify parameter source for logging."""
    if param_name in params:
        return "equipment_parameters"
    elif param_name in flow_params:
        return "flow_capacity"
    elif param_name in defaults:
        return "defaults"
    else:
        return "hardcoded_fallback"
```

### Phase 2: Update Configuration Structure

Add a comprehensive defaults section while keeping parameters in logical sections:

```yaml
# config/calibrated_parameters.yaml

# NEW: Defaults section for all primitive types
defaults:
  source:
    generation_rate: 300.0      # High rate for target production
    generation_interval: 0.1
    max_input_rate: 350.0
    max_output_rate: 350.0
    internal_capacity: 2000.0
    
  sink:
    collection_rate: 300.0      # Match source generation rate
    collection_interval: 0.1
    nominal_rate: 300.0
    max_input_rate: 350.0
    internal_capacity: 10000.0  # Large buffer for sink
    
  equipment:
    nominal_rate: 90.0          # Base processing rate
    quality_rate: 0.95
    performance_factor: 0.55    # For 46% OEE target
    batch_size: 10.0
    processing_interval: 0.1
    mtbf: 60.0
    mttr: 30.0

# Equipment-specific overrides (keep existing structure)
equipment_parameters:
  LINE1-SOURCE:
    generation_rate: 310.0
    generation_interval: 0.1
  # ... other equipment keeps their current settings

# Flow capacity (keep sink rates here - it's logical)
flow_capacity:
  equipment:
    LINE1-SINK:
      collection_rate: 300.0
      collection_interval: 0.1
    # ... other sinks
```

### Phase 3: Add Parameter Validation and Tracking

```python
# In twin_model/ontology_model_builder.py

class ParameterTracker:
    """Track parameter usage and validate values."""
    
    def __init__(self):
        self.parameters_used = {}
        self.defaults_used = []
        self.warnings = []
        
    def record_param(self, equipment_id: str, param_name: str, value: Any, source: str):
        """Record parameter usage."""
        key = f"{equipment_id}.{param_name}"
        self.parameters_used[key] = {"value": value, "source": source}
        if source in ["defaults", "hardcoded_fallback"]:
            self.defaults_used.append(key)
            
    def validate_source(self, source_id: str, generation_rate: float):
        """Validate source parameters."""
        if generation_rate < 100:
            self.warnings.append(f"{source_id}: Low generation_rate {generation_rate} will limit production")
        elif generation_rate > 1000:
            self.warnings.append(f"{source_id}: Very high generation_rate {generation_rate}")
            
    def report(self):
        """Generate parameter usage report."""
        logger.info("=== Parameter Usage Report ===")
        if self.defaults_used:
            logger.warning(f"Using {len(self.defaults_used)} default values:")
            for param in self.defaults_used[:5]:  # Show first 5
                logger.warning(f"  - {param}")
        if self.warnings:
            logger.warning("Validation warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
```

### Phase 4: Remove Hardcoded Values Systematically

Replace ALL hardcoded defaults with config-driven defaults:

```python
# List of all parameters to fix:
PARAMETERS_TO_FIX = [
    ("_create_source", "generation_rate", 60.0),
    ("_create_source", "generation_interval", 0.1),
    ("_create_sink", "collection_rate", 50.0),
    ("_create_sink", "collection_interval", 0.1),
    ("_create_equipment_flow", "nominal_rate", 50.0),
    ("_create_equipment_flow", "quality_rate", 0.95),
    ("_create_equipment_flow", "performance_factor", 0.85),
    ("_create_equipment_flow", "batch_size", 10.0),
    ("_create_equipment_flow", "mtbf", 60.0),
    ("_create_equipment_flow", "mttr", 10.0),
    # Flow capacity parameters
    ("FlowCapacity", "max_input_rate", 60.0),
    ("FlowCapacity", "max_output_rate", 50.0),
    ("FlowCapacity", "internal_capacity", 500.0),
]

# Pattern to follow for each:
# OLD: param = params.get("param_name", HARDCODED_VALUE)
# NEW: param = params.get("param_name") or defaults.get("param_name", SENSIBLE_FALLBACK)
```

## Deep Sweep for Additional Hardcodes

### Search Commands to Run:
```bash
# Find all numeric defaults in Python files
grep -r "get(.*,\s*[0-9]" twin_model/ --include="*.py"

# Find all direct numeric assignments
grep -r "=\s*[0-9]+\.[0-9]" twin_model/ --include="*.py"

# Use semgrep with pattern
semgrep --pattern='$X.get($Y, $LITERAL)' twin_model/
```

### Files to Check:
- `twin_model/ontology_model_builder.py` ✅ (found many)
- `twin_model/primitives/source_flow.py` 
- `twin_model/primitives/sink_flow.py`
- `twin_model/primitives/equipment_flow.py`
- `twin_model/scheduling/*.py`
- `run_baseline_twin_simulation.py`
- `run_calibrated_mes_simulation.py`

## Robust Logging Implementation

### 1. Log Parameter Values at Creation
```python
# In OntologyModelBuilder._create_source()
logger.info(f"Creating {source_id}:")
logger.info(f"  generation_rate: {generation_rate} (from: {'config' if 'generation_rate' in params else 'default'})")
logger.info(f"  generation_interval: {generation_interval}")
logger.info(f"  max_input_rate: {capacity.max_input_rate}")
logger.info(f"  max_output_rate: {capacity.max_output_rate}")
```

### 2. Add Parameter Validation
```python
# Create a validator
def validate_parameters(equipment_id: str, params: Dict[str, Any]) -> None:
    if 'generation_rate' in params:
        rate = params['generation_rate']
        if rate < 100:
            logger.warning(f"{equipment_id}: Low generation_rate {rate} may limit production")
        if rate > 1000:
            logger.warning(f"{equipment_id}: Very high generation_rate {rate} may cause bottlenecks")
```

### 3. Track Default Usage
```python
# Add tracking of when defaults are used
class DefaultTracker:
    def __init__(self):
        self.defaults_used = {}
        
    def get_param(self, params, key, default, equipment_id):
        if key not in params:
            self.defaults_used[f"{equipment_id}.{key}"] = default
            logger.debug(f"{equipment_id}: Using default {key}={default}")
        return params.get(key, default)
        
    def report(self):
        if self.defaults_used:
            logger.warning(f"Used {len(self.defaults_used)} default values:")
            for key, value in self.defaults_used.items():
                logger.warning(f"  {key}: {value}")
```

## Testing Strategy

### 1. Unit Test Parameter Loading
```python
def test_source_uses_configured_generation_rate():
    config = {
        "equipment_parameters": {
            "LINE1-SOURCE": {"generation_rate": 500.0}
        }
    }
    # Verify source gets 500, not default 60
```

### 2. Integration Test Full Pipeline
```python
def test_production_achieves_target():
    # Run 1 hour simulation
    # Verify production rate > 400 units/minute total
    # Verify no equipment using default rates
```

### 3. Create Parameter Validation Script
```python
# validate_parameters.py
def validate_config(config_path):
    """Check config has all required parameters."""
    required = {
        "LINE1-SOURCE": ["generation_rate"],
        "LINE1-SINK": ["collection_rate"],
        # etc...
    }
    # Report missing parameters
```

## Implementation Order

Follow these steps in sequence for the complete fix:

1. **Add defaults section to config/calibrated_parameters.yaml**
   - Add the defaults section as shown in Phase 2
   - This provides proper defaults for all equipment types
   
2. **Update OntologyModelBuilder parameter loading**
   - Implement the enhanced parameter resolution in Phase 1
   - Check equipment_params -> flow_params -> defaults -> fallback
   - Add logging to show which source each parameter came from
   
3. **Fix all hardcoded values**
   - Replace all `params.get("x", HARDCODED)` with proper resolution
   - Use the pattern shown in Phase 4 for each parameter
   
4. **Add ParameterTracker class**
   - Implement validation and tracking as shown in Phase 3
   - Report warnings and default usage at startup
   
5. **Test the complete fix**
   - Run simulation and verify 8.4M unit target is achieved
   - Check logs to ensure configured values are being used
   - Verify no unexpected defaults are applied

## Questions to Resolve

1. **Config Loader**: Is there an existing ConfigLoader class that should handle parameter merging?
2. **Parameter Hierarchy**: Should flow_capacity parameters override equipment_parameters or vice versa?
3. **Defaults Location**: Should defaults be in config files or a separate defaults.yaml?
4. **Validation**: Should we fail fast on bad parameters or use defaults with warnings?

## Next Session Tasks

1. Run the deep sweep for all hardcoded values
2. Implement the parameter loading fixes
3. Add comprehensive logging
4. Test with the calibrated parameters
5. Verify 8.4M unit target is achieved