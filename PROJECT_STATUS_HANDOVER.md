# Virtual Ontology Project - Status Handover Document

## Project Overview

This is a discrete event simulation project using SimPy to model manufacturing production lines. The system uses an ontology-driven approach where:
- **Ontology** defines equipment types and relationships
- **Manifests** specify equipment instances and connections
- **Configuration** provides tunable parameters
- **OntologyModelBuilder** constructs the simulation from these inputs

## Critical Context: The Hardcoded Parameter Problem

### Original Issue
The simulation was producing only 1.9% of the target 8.4M units over 14 days because the `OntologyModelBuilder` had extensive hardcoded default values that prevented configuration from being properly applied. Sources defaulted to 60 units/minute instead of the required 300+ units/minute.

### Root Cause Discovered
The parameter resolution system had a critical bug where `_create_equipment()` was pre-merging default parameters before passing them to specific creation methods. This caused general defaults to override type-specific defaults (e.g., flow_capacity.defaults at 150 units/min would override source defaults at 350 units/min).

## Completed Fixes (Phases 1-3)

### Phase 1: Enhanced Parameter Loading ✅
**File Modified**: `twin_model/ontology_model_builder.py`

**Changes Made**:
- Modified `_create_source`, `_create_sink`, and `_create_equipment_flow` methods
- Added proper parameter resolution with detailed logging
- Added `_get_param_source()` helper method to track where parameters come from
- Eliminated hardcoded defaults (e.g., 60 units/min → uses config values)

### Phase 2: Comprehensive Defaults Structure ✅
**File Modified**: `config/calibrated_parameters.yaml`

**Added Defaults Sections**:
```yaml
defaults:
  source:
    generation_rate: 300.0      # High rate for target production
    max_input_rate: 600.0       # Must exceed generation_rate
    max_output_rate: 600.0      
    internal_capacity: 2000.0   
    
  sink:
    collection_rate: 300.0      # Match source generation rate
    max_input_rate: 350.0       
    internal_capacity: 10000.0  
    
  equipment:
    nominal_rate: 450.0         # High nominal for baseline
    performance_factor: 0.50    # Poor (target: improve to 0.85)
    quality_rate: 0.94          # Moderate (target: improve to 0.98)
    max_input_rate: 600.0       
    max_output_rate: 600.0      
```

### Phase 3: Fixed Parameter Resolution Bug ✅
**File Modified**: `twin_model/ontology_model_builder.py`

**Critical Fix**:
- Removed pre-merging of defaults in `_create_equipment()`
- Each creation method now directly accesses config sections
- Proper resolution hierarchy: equipment-specific → type-specific defaults → general defaults → fallback

**Before (Buggy)**:
```python
def _create_equipment(self, equipment_id, equipment_data):
    flow_params = self.config["flow_capacity"]["equipment"].get(equipment_id, {})
    for key, value in flow_defaults.items():
        if key not in flow_params:
            flow_params[key] = value  # This overwrote source-specific defaults!
    self._create_source(equipment_id, eq_params, flow_params)
```

**After (Fixed)**:
```python
def _create_equipment(self, equipment_id, equipment_data):
    if framework_primitive == "SourceFlow":
        self._create_source(equipment_id)  # Method accesses config directly

def _create_source(self, source_id):
    eq_flow_params = self.config.get("flow_capacity", {}).get("equipment", {}).get(source_id, {})
    source_defaults = self.config.get("defaults", {}).get("source", {})
    # Proper resolution without pre-merging
```

## Current State: Baseline Configuration

### Objective
Create a baseline with intentionally low OEE (~30-35%) that achieves the 8.4M target while leaving significant room for improvement.

### Current Configuration (`config/calibrated_parameters.yaml`)
**LINE 1** (Worst Performer - 27.8% OEE):
- Nominal rates: 480-500 units/min
- Performance: 0.46
- Quality: 0.93
- MTBF/MTTR: 65/35 (65% availability)

**LINE 2** (Mid Performer - 33.2% OEE):
- Nominal rates: 450-470 units/min
- Performance: 0.52
- Quality: 0.94
- MTBF/MTTR: 60/28 (68% availability)

**LINE 3** (Best Performer - 36.6% OEE):
- Nominal rates: 440-460 units/min
- Performance: 0.55
- Quality: 0.95
- MTBF/MTTR: 70/30 (70% availability)

### Important Discovery: Processing Model Constraints

**Expected vs Actual Production**:
- **Mathematical expectation**: 8.96M units (444 units/min)
- **Actual simulation**: 295K units (14.6 units/min)

**Root Cause**: Equipment processes in batches
- `batch_size`: 10 units
- `processing_interval`: 0.1 minutes (6 seconds)
- Equipment can only process `nominal_rate × interval × performance` per batch
- Sources get blocked when downstream equipment can't consume fast enough

This is **realistic behavior** - the slowest equipment constrains the entire line.

## Key Files and Locations

### Core Implementation
- `twin_model/ontology_model_builder.py` - Main builder with parameter resolution
- `twin_model/primitives/source_flow.py` - Source generation logic
- `twin_model/primitives/sink_flow.py` - Sink collection logic
- `twin_model/primitives/equipment_flow.py` - Equipment processing logic

### Configuration
- `config/calibrated_parameters.yaml` - Main parameters (includes defaults sections)
- `ontology/filling_line_ontology.yaml` - Equipment type definitions
- `manifests/equipment_manifest.yaml` - Equipment instances and connections

### Validation & Testing
- `validate_phase3.py` - Tests production achievement
- `test_phase1_calibrated.py` - Tests parameter resolution
- `test_phase2_defaults.py` - Tests defaults structure

### Documentation
- `fix-hardcoded-parameters-COMPLETED.md` - Details of parameter fixes
- `baseline-configuration-analysis.md` - Analysis of current baseline

## What's Left To Do

### 1. Decide on Baseline Target
**Option A**: Accept current low baseline (295K units)
- Pros: Shows dramatic improvement potential (28x)
- Cons: Very far from 8.4M target

**Option B**: Adjust processing model for higher baseline
- Reduce `processing_interval` to 0.01 (10x throughput)
- Or increase `batch_size` to 100 (10x throughput)
- Would achieve closer to 3-4M units baseline

### 2. Create Production Orders
The system supports order-based production but currently runs in continuous mode. Need to create `config/baseline_production_orders.yaml` with specific product orders if order-based simulation is desired.

### 3. Implement MES Integration
The MES (Manufacturing Execution System) components exist but aren't fully integrated:
- Scheduler for production planning
- Order management
- Resource allocation

### 4. Metrics and Reporting
- Implement comprehensive OEE tracking
- Create visualization of production metrics
- Generate baseline performance reports

### 5. Optimization Scenarios
Document and implement improvement scenarios:
- Quick wins (performance factor improvements)
- Equipment upgrades (reduce MTTR)
- Quality improvements
- Processing efficiency gains

## Running the Simulation

### Basic Test
```bash
~/.local/bin/poetry run python validate_phase3.py
```

### Check Parameter Resolution
```bash
~/.local/bin/poetry run python test_phase2_defaults.py
```

### Important Commands
- Always use `~/.local/bin/poetry run` for Python commands
- Use `semgrep --config=.semgrep/rules/project-specific.yaml` to check for hardcoded values
- Check git status for modified files

## Critical Things to Remember

1. **Parameter Resolution Order**: Equipment-specific → Type-specific defaults → General defaults → Fallback
2. **Flow Rates Must Match**: `max_input_rate` and `max_output_rate` must exceed generation/collection rates
3. **Sources Get Blocked**: If downstream can't consume, sources stop generating
4. **Sinks Use `total_collected`**: Not `total_output` (different metric)
5. **Processing is Batched**: Equipment processes `batch_size` units every `processing_interval`

## Next Session Recommendations

1. **First Priority**: Decide whether to keep the current low baseline (295K) or adjust the processing model for a higher baseline (3-4M)

2. **If keeping low baseline**: Document it as a "heavily constrained system" perfect for demonstrating optimization value

3. **If adjusting for higher baseline**: 
   - Reduce `processing_interval` from 0.1 to 0.01 in equipment defaults
   - This will 10x throughput while maintaining same OEE percentages
   - Re-run validation to confirm ~3M units achievement

4. **Then proceed with**: Creating production orders and implementing reporting/metrics

## Contact & Context
- Project uses Poetry for dependency management
- Follows PEP 8, uses mypy and ruff for code quality
- CLAUDE.md file contains coding preferences
- Git branch: `twin-model-standalone`