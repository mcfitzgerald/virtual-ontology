# Ontology-Driven Virtual Twin Architecture & Implementation Plan

## Executive Summary

Building a discovery-based virtual twin system where:
- **Ontology defines structure** (entities, relationships, properties)
- **Manifests provide configuration** (values, schedules, parameters)
- **Primitives are generic building blocks** (Equipment, Buffer, Source, Sink)
- **Model Builder interprets ontology** to instantiate SimPy models
- **LLM discovers relationships** through observation and experimentation (not prescription)

The system generates MES data that an LLM can analyze to identify issues, propose parameter changes, run simulations, and validate improvements - all through ontology-driven understanding.

## Core Architecture

```
┌─────────────────────┐
│   Twin Ontology     │  ← Defines: Equipment, Line, Order, Product (structure only)
│  (Structure Only)   │  ← Relationships: feeds_into, processes, scheduled_on
└─────────────────────┘
         ↓
┌─────────────────────┐
│  SimPy Primitives   │  ← Generic: EquipmentPrimitive, BufferPrimitive, etc.
│ (Building Blocks)   │  ← Extensible: Can express many behaviors
└─────────────────────┘
         ↓
┌─────────────────────┐
│   Model Builder     │  ← Reads ontology structure
│(Ontology→Primitives)│  ← Instantiates primitives per ontology specification
└─────────────────────┘
         ↓
┌─────────────────────┐
│     Manifests       │  ← Products: SKUs, rates, costs, scrap rates
│  (Configuration)    │  ← Equipment: Specific instances, failure patterns
└─────────────────────┘  ← Schedule: Production orders, changeovers
         ↓
┌─────────────────────┐
│  Running Simulation │  ← SimPy executes configured model
│ (Rich Observables)  │  ← Emits comprehensive event stream
└─────────────────────┘
         ↓
┌─────────────────────┐
│    Transduction     │  ← Extracts MES-observable subset
│  (SimPy → MES)      │  ← Formats as tabular records
└─────────────────────┘
         ↓
┌─────────────────────┐
│     MES Data        │  ← What LLM analyzes (matching mes_data_with_kpis.csv)
│   (CSVs/Tables)     │  ← Contains patterns for discovery
└─────────────────────┘
```

## Key Design Principles

### 1. Ontology as Structure (Not Configuration)
```yaml
# GOOD - Ontology defines what exists
Equipment:
  properties:
    - base_rate: float
    - mtbf: float

# BAD - Ontology contains values
Equipment:
  base_rate: 60.0  # ← This belongs in manifest
```

### 2. Discovery Over Prescription
- **No prescribed mappings**: "if downtime > X then adjust Y"
- **Rich observables**: Equipment emits detailed event streams
- **LLM learns**: Discovers relationships through experimentation
- **Actionable parameters**: Exposed knobs without prescribed effects

### 3. Primitive-Based Architecture
- **Generic primitives**: Not specialized per equipment type (for now)
- **Behavior through composition**: Combine primitives to create complex systems
- **Event-driven**: Primitives emit events that become observables

## Implementation Plan

## Phase 1: SimPy Primitives Framework

### 1.1 Create Base Primitive (`twin_model/primitives/base.py`)
```python
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import simpy

@dataclass
class PrimitiveConfig:
    """Configuration for a primitive instance.
    
    Attributes:
        id: Unique identifier for this primitive
        type: Type of primitive (Equipment, Buffer, etc.)
        properties: Type-checked properties from manifest
    """
    id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)

class BasePrimitive(ABC):
    """Base class for all SimPy primitives.
    
    All primitives must emit observables for discovery-based learning.
    """
    
    def __init__(self, 
                 env: simpy.Environment, 
                 config: PrimitiveConfig) -> None:
        """Initialize primitive with configuration.
        
        Args:
            env: SimPy environment
            config: Primitive configuration from manifest
        """
        self.env = env
        self.config = config
        self.observables: List[Dict[str, Any]] = []
        
    @abstractmethod
    def start(self) -> None:
        """Start the primitive's processes."""
        pass
        
    def emit_observable(self, 
                       event_type: str, 
                       details: Dict[str, Any]) -> None:
        """Emit an observable event for learning.
        
        Args:
            event_type: Type of event (state_change, production, failure)
            details: Event-specific details
        """
        self.observables.append({
            'timestamp': self.env.now,
            'primitive_id': self.config.id,
            'event_type': event_type,
            **details
        })
```

**Requirements**:
- Use context7 to fetch SimPy documentation for Process, Store, Resource patterns
- Implement with strict type hints
- Comprehensive docstrings for auto-documentation

### 1.2 Create Equipment Primitive (`twin_model/primitives/equipment.py`)
```python
from typing import Optional, Generator, Dict, Any
from enum import Enum
import random
import simpy

from .base import BasePrimitive, PrimitiveConfig
from .buffer import BufferPrimitive

class EquipmentState(str, Enum):
    """Possible equipment states."""
    RUNNING = "RUNNING"
    STOPPED_FAILURE = "STOPPED_FAILURE" 
    STOPPED_MAINTENANCE = "STOPPED_MAINTENANCE"
    STARVED = "STARVED"
    BLOCKED = "BLOCKED"
    IDLE = "IDLE"
    CHANGEOVER = "CHANGEOVER"

class EquipmentPrimitive(BasePrimitive):
    """Generic equipment that processes materials.
    
    Emits rich observables for pattern discovery including:
    - State transitions with context
    - Production events with quality metrics
    - Failure events with contributing factors
    - Performance variations by shift/product
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 config: PrimitiveConfig,
                 upstream: Optional[BufferPrimitive] = None,
                 downstream: Optional[BufferPrimitive] = None) -> None:
        """Initialize equipment with buffers.
        
        Args:
            env: SimPy environment
            config: Equipment configuration
            upstream: Input buffer (None for source equipment)
            downstream: Output buffer (None for sink equipment)
        """
        # Implementation with rich state tracking
```

**Features to implement**:
- Multiple failure modes (micro-stops, major failures, quality issues)
- Shift-based performance variations
- Product-specific behavior
- Energy consumption tracking
- Rich context in observables (runtime, product, shift, buffer levels)

### 1.3 Create Other Primitives
- `BufferPrimitive`: Store with capacity, tracks levels
- `SourcePrimitive`: Material generator with stochastic arrivals
- `SinkPrimitive`: Product collector, tracks throughput
- `SchedulerPrimitive`: Manages production orders and changeovers
- `MonitorPrimitive`: Captures KPIs and aggregates metrics

## Phase 2: Ontology-Driven Model Builder

### 2.1 Update Twin Ontology (`ontology/twin_ontology.yaml`)
```yaml
# Following proper ontology structure (TBox, RBox)
metadata:
  name: "Manufacturing Twin Ontology"
  version: "2.0.0"
  description: "Structure for discovery-based virtual twin"

# TBox - Class definitions
tbox:
  classes:
    Equipment:
      description: "Production equipment that processes materials"
      parent: "SimulationEntity"
      primitive: "EquipmentPrimitive"  # Maps to primitive type
      
    Filler:
      description: "Equipment that fills containers"
      parent: "Equipment"
      isa: "Equipment"  # Ontologically correct inheritance
      
    ProductionLine:
      description: "Collection of equipment in sequence"
      parent: "SimulationEntity"
      
    ProductionOrder:
      description: "Scheduled production run"
      parent: "SimulationEntity"
      
    Product:
      description: "Item being produced"
      parent: "SimulationEntity"

# RBox - Relationships
rbox:
  relationships:
    feeds_into:
      domain: "Equipment"
      range: "Equipment"
      transitivity: true
      description: "Material flow relationship"
      
    processes_product:
      domain: "ProductionOrder"
      range: "Product"
      cardinality: "1:1"
      
    scheduled_on:
      domain: "ProductionOrder"
      range: "ProductionLine"
      cardinality: "N:1"

# Observable properties (what can be measured)
observables:
  equipment_state:
    source: "Equipment.state"
    type: "categorical"
    
  production_count:
    source: "Equipment.units_produced"
    type: "numeric"
    aggregation: "sum"
    
  downtime_events:
    source: "Equipment.failure_events"
    type: "event_stream"

# Controllable parameters (knobs to turn)
controllables:
  micro_stop_probability:
    description: "Affects equipment reliability"
    bounds: [0.3, 1.5]
    default: 1.0
    
  performance_factor:
    description: "Affects production speed"
    bounds: [0.7, 1.3]
    default: 1.0
```

### 2.2 Create Model Builder (`twin_model/model_builder.py`)
```python
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import simpy

from .primitives import (
    EquipmentPrimitive, 
    BufferPrimitive,
    SourcePrimitive,
    SinkPrimitive,
    SchedulerPrimitive
)

class OntologyDrivenModelBuilder:
    """Builds SimPy models from ontology structure and manifests.
    
    Interprets the twin ontology to construct a simulation model,
    then configures it with values from manifests.
    """
    
    def __init__(self, 
                 ontology_path: Path,
                 manifest_dir: Path) -> None:
        """Initialize builder with ontology and manifest directory.
        
        Args:
            ontology_path: Path to twin_ontology.yaml
            manifest_dir: Directory containing manifest files
        """
        self.ontology = self._load_ontology(ontology_path)
        self.manifests = self._load_manifests(manifest_dir)
        
    def build_model(self, env: simpy.Environment) -> Dict[str, Any]:
        """Build complete simulation model from ontology.
        
        Args:
            env: SimPy environment for the model
            
        Returns:
            Dictionary of instantiated primitives keyed by ID
        """
        # Parse ontology classes and relationships
        # Instantiate appropriate primitives
        # Wire relationships
        # Configure from manifests
```

**Requirements**:
- Use context7 for SimPy Environment documentation
- Parse ontology using standard structure (TBox, RBox)
- Support extension (Filler isa Equipment)
- Type-safe primitive instantiation

## Phase 3: Configuration Layer (Manifests)

### 3.1 Create Production Manifest (`manifests/production_manifest.yaml`)
```yaml
# Products from original generator.yaml
products:
  SKU-1001:
    name: "12oz Sparkling Water"
    target_rate_units_per_5min: 500
    standard_cost_per_unit: 0.15
    sale_price_per_unit: 0.50
    scrap_rates:
      normal: 0.02
      startup: 0.05
      
  SKU-1002:
    name: "32oz Premium Juice"
    target_rate_units_per_5min: 350
    standard_cost_per_unit: 0.45
    sale_price_per_unit: 1.50
    scrap_rates:
      normal: 0.025
      quality_issue: 0.08
      startup: 0.06
      
  # ... other 4 products

# Production schedule
production_orders:
  - order_id: "ORD-1000"
    product_id: "SKU-2002"
    line_id: "LINE1"
    start_time: 0  # minutes from simulation start
    duration: 480  # 8 hours
    
  - order_id: "CHANGEOVER"
    product_id: null  # Changeover has no product
    line_id: "LINE1"
    start_time: 480
    duration: 45
    downtime_reason: "PLN-CO"
    
  - order_id: "ORD-1001"
    product_id: "SKU-1001"
    line_id: "LINE1"
    start_time: 525
    duration: 600
```

### 3.2 Create Equipment Manifest (`manifests/equipment_manifest.yaml`)
```yaml
# Equipment instances
equipment:
  LINE1-FIL:
    type: "Filler"
    line: "LINE1"
    position: 1
    base_rate: 60.0  # units/minute
    mtbf: 480.0  # 8 hours
    mttr: 30.0
    
  LINE1-PCK:
    type: "Packer"
    line: "LINE1"
    position: 2
    base_rate: 55.0
    mtbf: 600.0
    mttr: 20.0
    
  # ... LINE2, LINE3 equipment

# Equipment-specific failure patterns
failure_patterns:
  Filler:
    micro_stops:
      probability_per_5min: 0.08
      duration_range: [1, 3]
      downtime_reason: "UNP-SENS"  # Sensor issues common on fillers
      
    major_failures:
      probability_per_5min: 0.025
      duration_range: [15, 45]
      downtime_reason: "UNP-MECH"
      
  Packer:
    quality_issues:
      probability_per_5min: 0.05
      duration_range: [2, 5]
      downtime_reason: "UNP-QC"
      
  Palletizer:
    electrical_issues:
      probability_per_5min: 0.015
      duration_range: [20, 60]
      downtime_reason: "UNP-ELEC"

# Shift performance
shifts:
  shift1:  # 6am-2pm
    start_hour: 6
    performance_range: [0.95, 1.05]
    
  shift2:  # 2pm-10pm  
    start_hour: 14
    performance_range: [0.90, 1.00]
    
  shift3:  # 10pm-6am
    start_hour: 22
    performance_range: [0.85, 0.95]

# Actionable parameters (controllable knobs)
parameters:
  micro_stop_probability: 1.0
  performance_factor: 1.0
  scrap_multiplier: 1.0
  material_reliability: 1.0
  cascade_sensitivity: 1.0
```

## Phase 4: Enhanced Transduction Layer

### 4.1 Update Transduction (`twin_model/transduction.py`)
```python
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd

@dataclass
class MESTransducer:
    """Converts rich SimPy observables to MES format.
    
    Extracts MES-relevant subset from comprehensive event stream,
    formats as tabular records matching mes_data_with_kpis.csv.
    """
    
    def transduce_observables(self, 
                             observables: List[Dict[str, Any]],
                             manifest: Dict[str, Any]) -> pd.DataFrame:
        """Convert observable stream to MES records.
        
        Args:
            observables: Complete event stream from simulation
            manifest: Configuration for context (products, orders)
            
        Returns:
            DataFrame matching MES schema with all required fields
        """
        # Group observables by timestamp and equipment
        # Extract state at each 5-minute mark
        # Calculate KPIs (OEE, availability, performance, quality)
        # Handle changeovers (NULL product/order)
        # Add energy consumption
```

**Output schema** (matching mes_data_with_kpis.csv):
- Timestamp, ProductionOrderID, LineID, EquipmentID, EquipmentType
- ProductID, ProductName, MachineStatus, DowntimeReason
- GoodUnitsProduced, ScrapUnitsProduced, TargetRate_units_per_5min
- StandardCost_per_unit, SalePrice_per_unit
- Availability_Score, Performance_Score, Quality_Score, OEE_Score
- Energy_Consumption_kWh

## Phase 5: Integration and Testing

### 5.1 Create Integration Test (`tests/test_mes_generation.py`)
```python
from typing import Dict, Any
import pandas as pd
from pathlib import Path

def test_full_mes_generation() -> None:
    """Test complete pipeline from ontology to MES data.
    
    Validates:
    - 3 production lines with correct equipment
    - 6 products with proper rotation
    - 8 downtime codes with equipment-specific patterns
    - Changeovers with NULL fields
    - Realistic OEE around 65%
    - Energy consumption tracking
    """
    # Load ontology and manifests
    # Build model
    # Run 3-day simulation
    # Transduce to MES format
    # Validate against expected patterns
```

### 5.2 Create Baseline Generator (`scripts/generate_baseline.py`)
```python
def generate_baseline_data(days: int = 14) -> pd.DataFrame:
    """Generate baseline MES data with realistic patterns.
    
    Includes:
    - Intentional inefficiencies for discovery (65% OEE)
    - Equipment-specific failure patterns
    - Product-specific performance variations
    - Shift performance differences
    - Cascade failures
    - Material shortages
    
    Args:
        days: Number of days to simulate
        
    Returns:
        DataFrame of MES records with discoverable patterns
    """
```

## Phase 6: Validation and Documentation

### 6.1 Statistical Validation (`tests/validate_distribution.py`)
Compare generated data against original mes_data_with_kpis.csv:
- Downtime frequency by type and equipment
- OEE distribution (mean ~65%, std dev ~15%)
- Product mix percentages
- Scrap rate patterns
- Energy consumption profiles

### 6.2 Documentation
- README with architecture overview
- Ontology specification guide
- Manifest schema documentation
- Primitive extension guide
- Example: Adding new equipment type

## Implementation Guidelines

### Code Quality Standards
1. **Type Hints**: Complete annotations on ALL functions/methods
2. **Docstrings**: Google-style with Args, Returns, Raises, Examples
3. **Context7 Usage**: Fetch SimPy docs for new patterns
4. **Testing**: Unit tests for each primitive, integration tests for pipeline
5. **Comments**: Inline documentation for complex logic

### Success Criteria
✅ Generated MES data format matches mes_data_with_kpis.csv exactly  
✅ Statistical properties align (OEE ~65%, proper downtime distribution)  
✅ All 6 products scheduled with changeovers  
✅ Equipment-specific failure patterns evident  
✅ Rich observables support pattern discovery  
✅ Model built from ontology + manifests (not hardcoded)  
✅ LLM can discover relationships without prescriptive mappings  

## Next Steps After Implementation

1. **Pattern Injection**: Add specific inefficiencies for LLM to discover
2. **Experiment Framework**: Support for parameter sweeps and scenario comparison
3. **Learning Loop**: Track what LLM discovers and validates
4. **Ontology Evolution**: Extend with more specialized equipment types
5. **Scale Testing**: Validate with 7-day, 30-day simulations

## Key Innovation

The system enables **discovery-based optimization** where:
- The ontology provides structure without prescriptive rules
- The manifests configure without constraining
- The primitives emit rich observables
- The LLM discovers relationships through experimentation
- Improvements are validated through simulation

This creates a powerful feedback loop for continuous improvement without requiring explicit programming of cause-effect relationships.