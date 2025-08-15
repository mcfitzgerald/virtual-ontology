# Virtual Twin Architecture Refactoring Plan

## Project Context & Vision

### The Broader Goal
This Virtual Twin Manufacturing Intelligence Platform is designed to address a common real-world challenge: manufacturing facilities often have excellent MES (Manufacturing Execution System) data but lack comprehensive IoT sensor infrastructure. The project demonstrates how to create a "virtual twin" layer that bridges this gap by deriving sensor-like observations from existing production data.

### Core Value Proposition
1. **Insight Discovery**: Use ontology-driven analysis to find patterns and opportunities in baseline production data
2. **What-If Analysis**: Adjust actionable parameters (maintenance effectiveness, operational excellence, quality control, supply chain reliability, line coupling) to simulate operational improvements
3. **Optimization**: Use the virtual twin to test scenarios and find optimal configurations before implementing real-world changes
4. **ROI Justification**: Quantify the potential impact of investments (better maintenance, quality systems, etc.) before committing resources

### Why Virtual Sensors Matter
Traditional digital twins often assume rich sensor data exists. Our approach acknowledges that many facilities operate with limited sensor infrastructure but still generate valuable production data. By creating "virtual sensors" that observe and derive metrics from this production data, we can:
- Estimate energy consumption without power meters
- Detect quality issues without inline inspection systems  
- Identify bottlenecks without detailed equipment monitoring
- Predict cascade failures without equipment-to-equipment sensors

This virtual sensor layer becomes the interface between raw production facts and actionable insights, enabling sophisticated analytics without requiring massive IoT investments.

## Executive Summary

This plan outlines a comprehensive refactoring of the Virtual Twin system to properly implement the virtual sensor layer as an abstraction that derives insights from MES production data, rather than generating synthetic sensor readings. The key insight is that we don't have physical IoT sensors, but we can derive meaningful observations from the production data we do have.

## Core Architectural Principles

### 1. Three-Layer Data Architecture
```
Raw Layer (Facts)     →  Virtual Layer (Observations)  →  Analytics Layer (Insights)
mes_data/simulation   →  sensor_data/quality_data      →  KPIs/Recommendations
```

### 2. Virtual Sensors as Observers
- Virtual sensors **observe and derive** metrics from production data
- They do NOT generate independent synthetic data
- Energy consumption, quality trends, bottlenecks are all **derived observations**

### 3. Clear Separation of Concerns
- **Twin Module**: All data generation and virtual observations
- **API Module**: Pure data access layer (no data generation)
- **Ontology**: Defines relationships and derivation logic

## Current Issues to Fix

### Database Schema Misalignment
- [ ] `energy_consumption_kwh` calculated by generator but missing from SQLModel schema
- [ ] Sample data generation in API layer violates architecture
- [ ] Inconsistent schema definitions across YAML files and SQLModel

### Conceptual Misalignment
- [ ] Physical sensors (temperature, vibration) defined but not derivable
- [ ] Energy treated as raw data instead of derived observation
- [ ] Unclear distinction between facts and observations

## Implementation Tasks

### Phase 1: Database Schema Alignment

#### Task 1.1: Audit All Schema Definitions
**Files to check:**
- `/api/models.py` - SQLModel definitions
- `/ontology/database_schema.yaml` - MES schema
- `/ontology/twin_database_schema.yaml` - Twin schema
- `/DATABASE_AND_API.md` - Documentation
- `/twin/schema_manager.py` - Schema validation

**Actions:**
1. Remove `energy_consumption_kwh` from any raw data table definitions
2. Ensure `sensor_data` table is properly defined for observations
3. Ensure `quality_data` table is properly defined for quality events
4. Add migration script for existing databases

#### Task 1.2: Update SQLModel Definitions
```python
# api/models.py - REMOVE energy field
class MESData(SQLModel, table=True):
    # ... existing fields ...
    # REMOVE: energy_consumption_kwh: float
    
class SimulationData(SQLModel, table=True):
    # ... existing fields ...
    # REMOVE: energy_consumption_kwh: float
```

### Phase 2: Generator Cleanup

#### Task 2.1: Remove Energy Column from Output
**File:** `/twin/generator.py`

**Actions:**
1. Keep `calculate_energy_consumption()` function for later use
2. Remove energy from DataFrame columns
3. Remove energy from database column mapping
4. Add CSV output option with `--output-csv` flag

#### Task 2.2: Add CSV Export Capability
```python
def generate_mes_data(start_date, end_date, config, output_format='db'):
    # ... existing generation logic ...
    
    if output_format == 'csv':
        df.to_csv(f'mes_data_{timestamp}.csv', index=False)
    elif output_format == 'both':
        df.to_csv(f'mes_data_{timestamp}.csv', index=False)
        save_to_database(df, 'mes_data')
    else:
        save_to_database(df, 'mes_data')
```

### Phase 3: API Layer Cleanup

#### Task 3.1: Remove Sample Data Generation
**File:** `/api/setup/twin_tables.py`

**Actions:**
1. Delete `populate_sample_quality_data()` method
2. Delete `populate_sample_sensor_data()` method
3. Keep table creation methods only

#### Task 3.2: Update Configuration
**File:** `/api/setup/config.json`

**Actions:**
1. Remove `populate_sample_data` flags
2. Keep table definitions only

### Phase 4: Virtual Sensor Layer Implementation

#### Task 4.1: Create Virtual Sensor Module
**New File:** `/twin/virtual_sensors.py`

```python
"""Virtual Sensor Layer - Derives observations from production data"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, DataFrame
import pandas as pd
import numpy as np

@dataclass
class SensorObservation:
    sensor_id: str
    equipment_id: str
    timestamp: datetime
    observable_property: str
    value: float
    unit: str
    confidence: float = 1.0

class VirtualSensor(ABC):
    """Base class for virtual sensors that observe production data"""
    
    @abstractmethod
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        """Derive observations from production data"""
        pass

class PowerMeterSensor(VirtualSensor):
    """Virtual power meter that derives energy consumption"""
    
    def __init__(self, config: Dict):
        self.config = config
        
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        """Calculate energy consumption from production patterns"""
        observations = []
        
        for _, row in production_data.iterrows():
            # Use existing calculate_energy_consumption logic
            energy_kwh = self._calculate_energy(
                status=row['machine_status'],
                equipment_type=row['equipment_type'],
                performance=row['performance_score'],
                product_id=row['product_id']
            )
            
            observations.append(SensorObservation(
                sensor_id=f"PWR-{row['equipment_id']}",
                equipment_id=row['equipment_id'],
                timestamp=row['timestamp'],
                observable_property='power_consumption',
                value=energy_kwh,
                unit='kWh',
                confidence=0.95  # We're estimating, not measuring
            ))
            
        return observations

class ThroughputSensor(VirtualSensor):
    """Observes production rate vs target"""
    
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        observations = []
        
        for _, row in production_data.iterrows():
            if row['machine_status'] == 'Running':
                throughput_ratio = row['good_units_produced'] / row['target_rate_units_per_5min']
                
                observations.append(SensorObservation(
                    sensor_id=f"THR-{row['equipment_id']}",
                    equipment_id=row['equipment_id'],
                    timestamp=row['timestamp'],
                    observable_property='throughput_efficiency',
                    value=throughput_ratio,
                    unit='ratio',
                    confidence=1.0
                ))
                
        return observations

class DefectRateSensor(VirtualSensor):
    """Observes quality through scrap patterns"""
    
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        observations = []
        
        for _, row in production_data.iterrows():
            total_units = row['good_units_produced'] + row['scrap_units_produced']
            if total_units > 0:
                defect_rate = row['scrap_units_produced'] / total_units
                
                observations.append(SensorObservation(
                    sensor_id=f"QUA-{row['equipment_id']}",
                    equipment_id=row['equipment_id'],
                    timestamp=row['timestamp'],
                    observable_property='defect_rate',
                    value=defect_rate,
                    unit='ratio',
                    confidence=1.0
                ))
                
        return observations

class BottleneckDetector(VirtualSensor):
    """Identifies production bottlenecks from OEE patterns"""
    
    def observe(self, production_data: pd.DataFrame) -> List[SensorObservation]:
        # Aggregate by equipment to find bottlenecks
        equipment_oee = production_data.groupby('equipment_id')['oee_score'].mean()
        min_oee_equipment = equipment_oee.idxmin()
        
        observations = []
        for equipment_id in equipment_oee.index:
            is_bottleneck = 1.0 if equipment_id == min_oee_equipment else 0.0
            
            observations.append(SensorObservation(
                sensor_id=f"BTN-{equipment_id}",
                equipment_id=equipment_id,
                timestamp=production_data['timestamp'].max(),
                observable_property='bottleneck_indicator',
                value=is_bottleneck,
                unit='boolean',
                confidence=0.8
            ))
            
        return observations

class VirtualSensorObserver:
    """Orchestrates all virtual sensors"""
    
    def __init__(self, config: Dict):
        self.sensors = [
            PowerMeterSensor(config),
            ThroughputSensor(config),
            DefectRateSensor(config),
            BottleneckDetector(config)
        ]
        
    def observe_production(self, production_data: pd.DataFrame) -> pd.DataFrame:
        """Run all virtual sensors and collect observations"""
        all_observations = []
        
        for sensor in self.sensors:
            observations = sensor.observe(production_data)
            all_observations.extend(observations)
            
        # Convert to DataFrame for storage
        return pd.DataFrame([obs.__dict__ for obs in all_observations])
```

#### Task 4.2: Integrate with SimulationRunner
**File:** `/twin/simulation_runner.py`

**Updates:**
```python
def run_simulation(self, parameters, duration_days, seed):
    # ... existing simulation logic ...
    
    # After generating simulation data
    sim_data = self._run_generator(config_dict, duration_days, seed)
    
    # NEW: Run virtual sensors
    observer = VirtualSensorObserver(self.config)
    sensor_observations = observer.observe_production(sim_data)
    
    # Store sensor observations
    self._store_sensor_data(run_id, sensor_observations)
    
    # ... rest of method ...
```

### Phase 5: Ontology Revision

#### Task 5.1: Update Twin Ontology
**File:** `/ontology/twin_ontology_spec.yaml`

**Changes:**
1. Remove physical sensor types (temperature, vibration, speed)
2. Add meaningful virtual sensors:
   - PowerMeterSensor (derives energy from production)
   - ThroughputSensor (observes production efficiency)
   - DefectRateSensor (derives quality from scrap)
   - BottleneckDetector (identifies constraints)
   - LineCouplingMonitor (observes cascade effects)
   - DowntimePatternSensor (analyzes downtime trends)

3. Update properties to reflect derivation:
```yaml
properties:
  power_consumption:
    class: "PowerMeterSensor"
    type: "float"
    description: "Energy consumption derived from equipment status and performance"
    derives_from: "machine_status, performance_score, equipment_type, product_id"
    unit: "kWh"
    
  throughput_efficiency:
    class: "ThroughputSensor"
    type: "float"
    description: "Actual vs target production rate"
    derives_from: "good_units_produced / target_rate_units_per_5min"
    unit: "ratio"
```

#### Task 5.2: Update Database Schema YAMLs
**Files:**
- `/ontology/database_schema.yaml`
- `/ontology/twin_database_schema.yaml`

**Actions:**
1. Ensure mes_data has no energy column
2. Define sensor_data structure properly
3. Define quality_data structure properly

### Phase 6: Testing & Validation

#### Task 6.1: Create Test Script
**New File:** `/twin/test_virtual_sensors.py`

```python
"""Test virtual sensor observations"""

def test_complete_flow():
    # 1. Generate baseline data
    runner = SimulationRunner()
    baseline = runner.create_baseline(duration_days=1)
    
    # 2. Check mes_data has no energy column
    assert 'energy_consumption_kwh' not in baseline.data.columns
    
    # 3. Check sensor_data has energy observations
    sensor_data = get_sensor_data(baseline.run_id)
    power_readings = sensor_data[sensor_data['observable_property'] == 'power_consumption']
    assert len(power_readings) > 0
    
    # 4. Verify CSV export
    runner.export_to_csv(baseline.run_id, 'test_baseline.csv')
    assert os.path.exists('test_baseline.csv')
```

#### Task 6.2: Migration Script
**New File:** `/migration/fix_energy_column.py`

```python
"""Migrate existing databases to new schema"""

def migrate_database():
    # 1. Extract energy data from mes_data if it exists
    # 2. Create sensor observations from energy data
    # 3. Store in sensor_data table
    # 4. Drop energy column from mes_data
    pass
```

## Implementation Sequence

### Week 1: Foundation
1. [ ] Create this plan document
2. [ ] Audit all schema definitions
3. [ ] Create test data backup

### Week 2: Schema Updates
4. [ ] Update SQLModel definitions
5. [ ] Update YAML schemas
6. [ ] Create migration script

### Week 3: Code Cleanup
7. [ ] Clean up generator.py
8. [ ] Remove API sample data generation
9. [ ] Add CSV export option

### Week 4: Virtual Sensor Layer
10. [ ] Implement virtual_sensors.py
11. [ ] Integrate with SimulationRunner
12. [ ] Test sensor observations

### Week 5: Ontology & Documentation
13. [ ] Revise twin_ontology_spec.yaml
14. [ ] Update all documentation
15. [ ] Create examples

### Week 6: Testing & Validation
16. [ ] Run complete test suite
17. [ ] Validate all data flows
18. [ ] Performance testing

## Success Criteria

1. **Clean Architecture**: Clear separation between facts (mes_data) and observations (sensor_data)
2. **No Energy in Raw Data**: Energy only exists as virtual sensor observations
3. **CSV Export Works**: Can inspect generated data easily
4. **Virtual Sensors Function**: All defined sensors produce meaningful observations
5. **Ontology Alignment**: YAML specs match actual implementation
6. **Tests Pass**: Complete flow from generation to observation works

## Risk Mitigation

1. **Data Loss**: Backup database before migration
2. **Breaking Changes**: Run parallel systems during transition
3. **Performance**: Monitor query performance with new structure
4. **Validation**: Extensive testing at each phase

## Next Session Starting Point

Begin with Phase 1, Task 1.1: Audit all schema definitions to understand current state fully before making changes.

## Quick Reference Guide

### Key File Locations

#### Database & Schema Files
- **SQLModel Definitions**: `/api/models.py` (MESData, SimulationData classes)
- **MES Ontology**: `/ontology/ontology_spec.yaml` (base MES concepts)
- **Twin Ontology**: `/ontology/twin_ontology_spec.yaml` (virtual twin layer)
- **Database Schemas**: 
  - `/ontology/database_schema.yaml` (MES tables)
  - `/ontology/twin_database_schema.yaml` (Twin tables)
- **Schema Manager**: `/twin/schema_manager.py` (validation & migration)

#### Core Modules
- **Data Generator**: `/twin/generator.py` (creates MES/simulation data)
- **Simulation Runner**: `/twin/simulation_runner.py` (orchestrates simulations)
- **Actionable Parameters**: `/twin/actionable_parameters.py` (the 5 tunable knobs)
- **Configuration**: 
  - `/twin/config/generator.yaml` (generation parameters)
  - `/twin/config/system.yaml` (system settings)

#### API Layer
- **API Models**: `/api/models.py` (SQLModel definitions)
- **Database Setup**: `/api/database_setup.py` (initialization & reset)
- **Twin Tables**: `/api/setup/twin_tables.py` (table creation - needs cleanup)
- **MES Historical**: `/api/setup/mes_historical.py` (baseline data generation)

### Database Access Commands

#### Via API (recommended)
```bash
# Start API if not running
./api.sh start

# Check database status
./api.sh status

# Query data (with enhanced logging)
echo '{"sql": "SELECT * FROM mes_data LIMIT 5"}' | ./query-log.sh POST /query -d @- --nl "Sample MES records"

# Direct query (without logging)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) FROM mes_data"}'
```

#### Database Reset & Generation
```bash
# Complete reset to pristine state
python api/database_setup.py reset

# Initialize with historical data
python api/database_setup.py init --historical

# Run verification
python api/database_setup.py verify --detailed
```

#### Direct SQLite Access (for debugging)
```bash
sqlite3 data/mes_database.db
.tables
.schema mes_data
```

### Twin Module Usage

```python
# Basic simulation
from twin import SimulationRunner, ActionableParameters

runner = SimulationRunner(verbose=False)
params = ActionableParameters()

# Adjust parameters (multipliers where 1.0 = baseline)
params.micro_stop_probability = 0.8  # 20% improvement
params.performance_factor = 1.1       # 10% improvement

# Run simulation
result = runner.run_simulation(params, duration_days=7)
print(f"OEE: {result.kpi_summary['mean_oee']:.1f}%")
```

### Documentation
- **Twin README**: `/twin/README.md` (comprehensive twin module guide)
- **Database & API**: `/DATABASE_AND_API.md` (API endpoints & schemas)
- **Query Logging**: `/QUERY_LOGGING.md` (enhanced query logging system)
- **System Architecture**: `/SYSTEM_ARCHITECTURE.md` (overall design)

### Current Database State (as of last session)
- **mes_data**: 36,288 records (June 1-14, 2025)
- **sensor_data**: 7,776 records (should be removed - synthetic)
- **quality_data**: 6,480 records (should be removed - synthetic)
- **twin_runs**: Empty (awaiting simulations)
- **simulation_data**: Empty (awaiting simulations)

## Notes from Discussion

- User has good MES data but no physical IoT sensors
- Virtual twin layer provides the abstraction for "what-if" analysis
- Energy as derived observation is more instructive than raw data
- Goal is to find insights in baseline, adjust parameters, generate new data, compare
- This is part of a broader real-world application concept

---
*Created: 2025-08-15*
*Last Updated: 2025-08-15*