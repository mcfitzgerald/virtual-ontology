# Ontology-Driven Virtual Twin System

## Overview
This system implements an ontology-driven virtual twin that generates synthetic MES (Manufacturing Execution System) data matching real production patterns.

## Architecture

### 1. Ontology Layer (`ontology/twin_ontology.yaml`)
- Defines system structure using TBox (terminology) and RBox (relationships)
- No hardcoded values - pure structural definition
- Key entities: Equipment, Buffer, Source, Sink, Product, ProductionOrder

### 2. Primitives Layer (`twin_model/primitives/`)
- **BasePrimitive**: Foundation class with observable emission
- **Equipment**: Production equipment with states, failures, OEE tracking
- **Buffer**: Material storage with FIFO/LIFO support
- **Source**: Material generation with various patterns
- **Sink**: Material consumption and disposal
- **Scheduler**: Production order management
- **Monitor**: System monitoring and alerting

### 3. Model Builder (`twin_model/model_builder.py`)
- Interprets ontology to build SimPy simulation models
- Wires relationships between primitives
- Creates production lines from equipment chains

### 4. Manifests (`manifests/`)
- **production_manifest.yaml**: Products, orders, schedules
- **equipment_manifest.yaml**: Equipment configurations, failure patterns

### 5. Transduction Layer (`twin_model/transduction/`)
- Converts rich SimPy observables to MES format
- Extracts MES-visible subset of events
- Calculates KPIs (OEE, Availability, Performance, Quality)

## Key Features

### Discovery-Based Learning
- No prescriptive cause-effect mappings
- LLM discovers relationships through observation
- Rich observables enable pattern discovery

### Separation of Concerns
- Structure (ontology) vs Configuration (manifests)
- Generic primitives as building blocks
- Controllable parameters without prescribed effects

### Realistic Production Patterns
- 6 product SKUs across 3 families
- 3 production lines with 9 equipment
- 8 downtime reason codes
- Shift-based performance variations
- Product-specific changeover times

## Usage

### Basic Simulation
```python
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction.mes_transducer import MESTransducer

# Build model
builder = OntologyDrivenModelBuilder('ontology/twin_ontology.yaml', 'manifests/')
model = builder.build_model(env)

# Run simulation
env.run(until=480)  # 8 hours

# Generate MES data
transducer = MESTransducer()
mes_df = transducer.process_observables(observables, manifests)
```

### Testing
- `test_phase1_*.py`: Primitive validation
- `test_phase2_*.py`: Model builder validation  
- `test_phase3_*.py`: Manifest validation
- `test_phase4_*.py`: Transduction validation
- `test_phase5_*.py`: Integration testing
- `test_phase6_*.py`: Statistical validation

## Output Format
Generates CSV matching `mes_data_with_kpis.csv`:
- Timestamp, ProductionOrderID, LineID, EquipmentID
- ProductID, ProductName, MachineStatus, DowntimeReason
- GoodUnitsProduced, ScrapUnitsProduced
- OEE_Score, Availability_Score, Performance_Score, Quality_Score
- Energy_Consumption_kWh

## Performance Metrics
- Target OEE: 65% (85% Availability × 85% Performance × 90% Quality)
- Scrap Rate: 1-3% typical
- Downtime: 15% of production time
- Changeover: 15-45 minutes depending on product family

## Future Enhancements
1. Multi-line coordination
2. Predictive maintenance patterns
3. Supply chain integration
4. Energy optimization
5. Real-time adaptation

## References
- SimPy Documentation: https://simpy.readthedocs.io/
- OEE Standards: https://www.oee.com/
- ISA-95 MES Standards
