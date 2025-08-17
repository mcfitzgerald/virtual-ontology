# Virtual Twin System - Complete Implementation Plan

## Executive Summary

Building an ontology-driven virtual twin system that uses SimPy discrete event simulation to model manufacturing operations. The system analyzes MES data through a semantic layer, identifies issues via natural language queries, and simulates remedies through parameter optimization.

**Core Innovation**: The twin ontology serves as both a declarative model specification AND a control interface, enabling the SimPy model to be generated directly from the ontology definition.

## System Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Twin Model    │────▶│    MES Data     │────▶│   Analytics     │
│ (SimPy Generator)│     │   (Baseline)    │     │  (NL → SQL)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         │                       ▼                        ▼
         │              ┌─────────────────┐     ┌─────────────────┐
         │              │  MES Ontology   │     │     Issues      │
         │              │ (Semantic Layer)│     │   Identified    │
         │              └─────────────────┘     └─────────────────┘
         │                                                │
         ▼                                                ▼
┌─────────────────┐                             ┌─────────────────┐
│  Twin Ontology  │◀────────────────────────────│   Optimization  │
│  (Model Spec)   │                             │   (Remedies)    │
└─────────────────┘                             └─────────────────┘
         │                                                │
         ▼                                                ▼
┌─────────────────┐                             ┌─────────────────┐
│ Model Builder   │                             │ Recommendations │
│(Ontology→SimPy) │                             │   (Actions)     │
└─────────────────┘                             └─────────────────┘
```

## Core Components

### 1. Twin Ontology
- **Purpose**: Declarative specification of the SimPy model and control parameters
- **Location**: `ontology/twin_ontology_spec.yaml`
- **Innovation**: Model is GENERATED from ontology, not coded

### 2. MES Ontology  
- **Purpose**: Semantic layer for MES data analysis
- **Location**: `ontology/ontology_spec.yaml`
- **Role**: Enables natural language to SQL translation

### 3. SimPy Twin Model
- **Purpose**: Discrete event simulation of production lines
- **Location**: `twin_model/`
- **Status**: Already implemented, needs ontology integration

### 4. Model Builder
- **Purpose**: Generates SimPy models from twin ontology
- **Location**: `twin_model/model_builder.py`
- **New Component**: To be implemented

## Phase 1: Twin Ontology Specification

### Objective
Create a comprehensive twin ontology that defines the virtual twin model declaratively.

### 1.1 Create Twin Ontology (`ontology/twin_ontology_spec.yaml`)

#### Structure Requirements
- Follow standard template (classes, relationships, properties)
- Add twin-specific sections:
  - `model_definition`: Declarative model structure
  - `behavioral_rules`: Component behaviors  
  - `parameter_effects`: How parameters affect model
  - `failure_modes`: Stochastic failure patterns
  - `transduction_layer`: MES ↔ Model mapping

#### Key Entities

```yaml
classes:
  Equipment:
    description: "Production equipment in virtual twin"
    maps_to:
      mes: "Equipment"
    properties:
      - base_rate: float
      - mtbf: float
      - mttr: float
      
  Buffer:
    description: "Work-in-process storage"
    properties:
      - capacity: integer
      - current_level: integer
      
  ProductionLine:
    description: "Complete production line"
    properties:
      - line_speed_setting: float
      - pm_intensity: float
```

#### Control Parameters

Real-world adjustable parameters:
1. **line_speed_setting** (0.7-1.2): Equipment speed dial
2. **preventive_maintenance_intensity** (0.5-2.0): PM frequency
3. **quality_threshold** (0.8-1.2): QC strictness
4. **operator_effectiveness** (0.8-1.2): Skill/staffing level
5. **buffer_management_strategy**: Reaction to buffer levels

#### Parameter Effects

```yaml
parameter_effects:
  line_speed_setting:
    affects:
      - equipment.current_rate: "base_rate * line_speed_setting"
      - failure.jam_probability: "base_prob * speed^2"
      - quality.scrap_rate: "base_scrap * (1 + 0.1*(speed-1))"
```

### Deliverables
- [ ] Complete twin ontology YAML file
- [ ] Validation against template structure
- [ ] Documentation of all entities and parameters

## Phase 2: Model Builder Implementation

### Objective
Create ontology-driven model builder that generates SimPy models from the twin ontology.

### 2.1 Core Model Builder (`twin_model/model_builder.py`)

```python
class OntologyDrivenModelBuilder:
    """Builds SimPy model from twin ontology specification"""
    
    def __init__(self, ontology_path: str):
        self.ontology = load_yaml(ontology_path)
        
    def build_model(self) -> SimulationModel:
        # 1. Register primitive classes
        # 2. Build lines from definitions
        # 3. Apply behavioral rules
        # 4. Wire parameter effects
        
    def apply_parameters(self, params: ActionableParameters):
        # Apply parameter effects from ontology
```

### 2.2 Refactor Existing Components

Keep current architecture but add ontology integration:
- Maintain `config.py` for runtime configuration
- Add ontology loader to equipment/buffer classes
- Preserve existing test suite

### Deliverables
- [ ] Model builder implementation
- [ ] Integration with existing twin_model
- [ ] Unit tests for model generation

## Phase 3: Database Redesign

### Objective
Design unified database schema for MES data and simulation results.

### 3.1 New Schema (`database/schema_v2.sql`)

#### Core Tables

```sql
-- MES data (real and simulated)
CREATE TABLE mes_data (
    timestamp TIMESTAMP,
    run_id TEXT,
    line_id TEXT,
    equipment_id TEXT,
    machine_status TEXT,
    downtime_reason TEXT,
    good_units INTEGER,
    scrap_units INTEGER,
    oee_score REAL,
    product_id TEXT,
    operator_id TEXT,
    shift_id TEXT,
    data_source TEXT -- 'simulation' or 'actual'
);

-- Simulation runs
CREATE TABLE simulation_runs (
    run_id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    run_type TEXT, -- 'baseline', 'what-if', 'optimization'
    parameters JSONB,
    ontology_version TEXT,
    results_summary JSONB
);

-- Parameter calibration history
CREATE TABLE calibrated_parameters (
    calibration_id TEXT PRIMARY KEY,
    calibrated_at TIMESTAMP,
    mes_data_range TEXT,
    equipment_configs JSONB,
    confidence_scores JSONB
);

-- Optimization results
CREATE TABLE optimization_results (
    optimization_id TEXT PRIMARY KEY,
    run_at TIMESTAMP,
    objective TEXT,
    constraints JSONB,
    best_parameters JSONB,
    expected_improvement JSONB
);

-- Recommendations
CREATE TABLE recommendations (
    recommendation_id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    issue_description TEXT,
    recommended_actions JSONB,
    expected_impact JSONB,
    implementation_status TEXT
);
```

### Deliverables
- [ ] Complete schema definition
- [ ] Migration scripts from existing database
- [ ] Data access layer updates

## Phase 4: MES Ontology Updates

### Objective
Update base MES ontology to align with new data structure and support richer analytics.

### 4.1 Enhance MES Ontology (`ontology/ontology_spec.yaml`)

#### New Properties
- Product complexity factors
- Shift patterns
- Operator assignments
- Changeover tracking

#### Common Queries
```yaml
common_queries:
  - name: "identify_bottleneck"
    question: "Which equipment has the lowest OEE and causes upstream blocking?"
    sql_pattern: |
      WITH equipment_oee AS (...)
      SELECT equipment_id, oee_score
      WHERE ...
      
  - name: "quality_issues"
    question: "Which products have high scrap rates?"
    sql_pattern: |
      SELECT product_id, AVG(scrap_rate)...
```

### Deliverables
- [ ] Updated MES ontology
- [ ] New common query patterns
- [ ] Validation of shared concepts with twin ontology

## Phase 5: Integration Layer

### Objective
Build components to connect all system parts.

### 5.1 Ontology Loader (`twin_model/ontology_loader.py`)

```python
class OntologyLoader:
    def load_twin_ontology(path: str) -> TwinOntology
    def load_mes_ontology(path: str) -> MesOntology
    def validate_consistency() -> List[str]
    def get_shared_concepts() -> Dict
```

### 5.2 Calibrator (`twin_model/calibrator.py`)

```python
class ModelCalibrator:
    def calibrate_from_mes(mes_data: pd.DataFrame) -> CalibratedConfig
    def infer_equipment_rates() -> Dict
    def estimate_failure_patterns() -> Dict
    def derive_buffer_sizes() -> Dict
```

### 5.3 Enhanced Runner (`twin_model/runner.py`)

- Use ontology-driven model
- Support multiple run types (baseline, what-if, optimization)
- Generate MES-compatible output

### Deliverables
- [ ] Ontology loader with validation
- [ ] Calibration system
- [ ] Enhanced simulation runner

## Phase 6: Analytics & Optimization

### Objective
Connect natural language analysis to simulation and optimization.

### 6.1 Issue Detector (`analytics/issue_detector.py`)

```python
class IssueDetector:
    def analyze_mes_data(data: pd.DataFrame) -> List[Issue]
    def identify_bottlenecks() -> List[Equipment]
    def find_quality_problems() -> List[Product]
    def detect_patterns() -> List[Pattern]
```

### 6.2 Remedy Finder (`optimization/remedy_finder.py`)

```python
class RemedyFinder:
    def map_issue_to_parameters(issue: Issue) -> List[Parameter]
    def simulate_remedies(issue: Issue) -> List[Remedy]
    def optimize_parameters(objective: str) -> OptimalParameters
```

### Deliverables
- [ ] Issue detection system
- [ ] Remedy simulation engine
- [ ] Parameter optimization

## Phase 7: Testing & Validation

### Objective
Ensure system correctness and demonstrate capabilities.

### 7.1 Test Suite

#### Unit Tests
- Ontology parsing and validation
- Model generation from ontology
- Parameter effect calculations
- MES data generation

#### Integration Tests
- End-to-end workflow
- Calibration accuracy
- Optimization convergence

### 7.2 Demonstration Notebook

Complete workflow demonstration:
1. Generate baseline MES data
2. Identify issues via NL query
3. Calibrate model from data
4. Simulate remedies
5. Optimize parameters
6. Show expected improvements

### Deliverables
- [ ] Comprehensive test suite
- [ ] Demo notebook
- [ ] Performance benchmarks

## Implementation Timeline

### Week 1: Foundation (Days 1-7)
- **Day 1-2**: Complete twin ontology specification
- **Day 3-4**: Implement core model builder
- **Day 5-6**: Design and implement database schema
- **Day 7**: Integration testing of Phase 1

### Week 2: Integration (Days 8-14)
- **Day 8-9**: Build ontology loader with validation
- **Day 10-11**: Refactor existing model for ontology integration
- **Day 12-13**: Update MES ontology
- **Day 14**: Integration testing of Phase 2

### Week 3: Intelligence (Days 15-21)
- **Day 15-16**: Implement calibrator
- **Day 17-18**: Build issue detector
- **Day 19-20**: Create remedy finder
- **Day 21**: Integration testing of Phase 3

### Week 4: Polish (Days 22-28)
- **Day 22-23**: Complete test suite
- **Day 24-25**: Create demonstration notebook
- **Day 26-27**: Documentation and cleanup
- **Day 28**: Final validation and release

## Success Criteria

### Technical Requirements
- [ ] SimPy model fully generated from ontology specification
- [ ] All control parameters show >5% impact on OEE
- [ ] Model calibration achieves >90% accuracy vs MES data
- [ ] Optimization finds parameters improving OEE by >10%
- [ ] Complete workflow executable via natural language

### Business Requirements
- [ ] Issues identified match operator observations
- [ ] Recommendations are actionable and realistic
- [ ] Cost impact calculations are accurate
- [ ] System provides clear audit trail

### Performance Requirements
- [ ] 7-day simulation completes in <60 seconds
- [ ] Optimization converges in <100 iterations
- [ ] Database queries return in <1 second
- [ ] Ontology parsing in <100ms

## Risk Mitigation

### Technical Risks
1. **Ontology Complexity**: Keep initial version focused on core entities
2. **Performance**: Use caching and parallel simulation
3. **Calibration Accuracy**: Start with simple patterns, iterate

### Business Risks
1. **User Adoption**: Provide clear documentation and examples
2. **Trust in Recommendations**: Show confidence intervals
3. **Integration Challenges**: Maintain backward compatibility

## Next Steps

1. **Immediate**: Review and approve this implementation plan
2. **Day 1**: Begin twin ontology specification
3. **Week 1 Checkpoint**: Review ontology and model builder
4. **Week 2 Checkpoint**: Validate integration layer
5. **Week 3 Checkpoint**: Test analytics and optimization
6. **Week 4**: Final review and deployment preparation

## Appendix: Key Design Decisions

### Why Ontology-Driven?
- Single source of truth for model behavior
- Declarative specification easier to maintain
- Natural language accessible
- Version control friendly

### Why SimPy?
- Industry standard for discrete event simulation
- Natural representation of material flow
- Built-in support for resources and processes
- Python native for easy integration

### Why Separate MES and Twin Ontologies?
- MES ontology focuses on data semantics
- Twin ontology focuses on simulation dynamics
- Clear separation of concerns
- Allows independent evolution

## Document History
- v1.0 (2025-01-17): Initial implementation plan created