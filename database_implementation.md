# Database Architecture Plan - YAML Ontologies + SQLModel

## Project Context
This is part of an ontology-driven virtual twin system for manufacturing simulation. The system:
- Uses **SimPy** for discrete event simulation
- Has an **ontology** (YAML) that defines structure, not values
- Has **manifests** (YAML) that provide configuration values
- Generates **MES data** (Manufacturing Execution System) for analysis
- The twin model code exists in `twin_model/` directory
- Existing API code in `api/` uses SQLModel patterns we want to leverage

### Key Dependencies
- `sqlmodel` - SQL database ORM with Pydantic integration
- `simpy` - Discrete event simulation
- `pandas` - Data manipulation
- `click` - CLI interface
- `pyyaml` - YAML file parsing

### Existing Code Structure
```
virtual-ontology/
├── ontology/
│   └── twin_ontology.yaml     # Ontology structure (TBox, RBox)
├── manifests/
│   ├── equipment_manifest.yaml # Equipment configurations
│   ├── production_manifest.yaml # Products and schedules
│   └── schedule_manifest.yaml  # Production schedules
├── twin_model/
│   ├── primitives/            # SimPy primitive implementations
│   ├── model_builder.py       # Builds model from ontology
│   └── transduction/
│       └── mes_transducer.py  # Converts observables to MES format
├── api/
│   ├── models.py             # Existing SQLModel models
│   ├── database.py           # Database connection
│   └── setup/
│       └── twin_tables.py    # Existing table definitions
└── database/                 # NEW - To be implemented
    ├── models.py
    ├── manager.py
    ├── repositories.py
    ├── integration.py
    └── cli.py
```

## Overview
Database architecture that:
1. **Keeps ontologies as YAML files** (version controlled, not in DB)
2. **Stores historical MES data** for baseline/reference
3. **Supports twin operations** (simulation runs, experiments, discoveries)
4. **Uses SQLModel** following the existing `api/` patterns

## Core Design Principles
- Ontologies remain as YAML files in `ontology/` directory
- Database stores operational data, not structure definitions
- Clean separation between configuration (manifests) and runtime data
- Leverage existing SQLModel patterns from `api/`

## Database Schema

### 1. Enhanced Models (`database/models.py`)
```python
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel
import json

# ============= HISTORICAL DATA =============

class HistoricalMESData(SQLModel, table=True):
    """Historical MES data for baseline reference"""
    __tablename__ = "historical_mes_data"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    production_order_id: Optional[str] = Field(default=None, index=True)
    line_id: str = Field(index=True)
    equipment_id: str = Field(index=True)
    equipment_type: str
    product_id: Optional[str] = Field(default=None, index=True)
    product_name: Optional[str] = None
    machine_status: str
    downtime_reason: Optional[str] = None
    good_units_produced: int
    scrap_units_produced: int
    target_rate_units_per_5min: int
    standard_cost_per_unit: float
    sale_price_per_unit: float
    availability_score: float
    performance_score: float
    quality_score: float
    oee_score: float = Field(index=True)
    energy_consumption_kwh: Optional[float] = None
    
    # Metadata about data source
    source: str = Field(default="historical")  # historical, imported, synthetic
    import_date: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: Optional[float] = None


# ============= CONFIGURATION (From Manifests) =============

class EquipmentConfig(SQLModel, table=True):
    """Equipment configuration from manifests"""
    __tablename__ = "equipment_config"
    
    equipment_id: str = Field(primary_key=True)  # e.g., LINE1-FIL
    equipment_type: str = Field(index=True)
    line_id: str = Field(index=True)
    position: Optional[int] = None
    base_rate: float
    mtbf: float
    mttr: float
    energy_consumption_rate: float
    
    # Store failure patterns as JSON
    failure_patterns_json: str = Field(default='{}')
    performance_by_product_json: str = Field(default='{}')
    
    # Metadata
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def failure_patterns(self) -> Dict[str, Any]:
        return json.loads(self.failure_patterns_json)
    
    @property
    def performance_by_product(self) -> Dict[str, float]:
        return json.loads(self.performance_by_product_json)


class ProductConfig(SQLModel, table=True):
    """Product configuration from manifests"""
    __tablename__ = "product_config"
    
    product_id: str = Field(primary_key=True)  # e.g., SKU-1001
    product_name: str
    target_rate_units_per_5min: int
    standard_cost_per_unit: float
    sale_price_per_unit: float
    
    # Scrap rates by condition
    scrap_rate_normal: float
    scrap_rate_startup: float
    scrap_rate_quality_issue: Optional[float] = None
    
    # Additional properties as JSON
    properties_json: str = Field(default='{}')
    
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProductionSchedule(SQLModel, table=True):
    """Production schedule from manifests"""
    __tablename__ = "production_schedule"
    
    schedule_id: Optional[int] = Field(default=None, primary_key=True)
    order_id: str = Field(index=True)
    product_id: Optional[str] = Field(foreign_key="product_config.product_id")
    line_id: str = Field(index=True)
    scheduled_start: datetime
    scheduled_duration_minutes: int
    target_quantity: Optional[int] = None
    priority: int = Field(default=0)
    schedule_type: str = Field(default="production")  # production, changeover, maintenance
    
    # Link to simulation run if this is a simulated schedule
    simulation_run_id: Optional[str] = Field(default=None, foreign_key="twin_runs.run_id")


# ============= TWIN OPERATIONS =============

class TwinRun(SQLModel, table=True):
    """Twin simulation runs (keep existing structure)"""
    __tablename__ = "twin_runs"
    
    run_id: str = Field(primary_key=True)
    run_type: str  # baseline, experiment, optimization, recommendation
    
    # Configuration tracking
    ontology_version: str  # Version of YAML ontology used
    manifest_version: str  # Version of manifest files used
    parameter_set_json: str  # JSON of parameters used
    config_delta_json: str  # Changes from baseline
    
    # Run metadata
    seed: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    simulation_days: int
    status: str  # pending, running, completed, failed
    
    # Results
    kpi_summary_json: Optional[str] = None
    output_path: Optional[str] = None
    data_hash: Optional[str] = None
    
    # Lineage
    parent_run_id: Optional[str] = Field(default=None, foreign_key="twin_runs.run_id")
    notes: Optional[str] = None
    created_by: str = Field(default="system")


class SimulationData(SQLModel, table=True):
    """Simulation output data (MES format)"""
    __tablename__ = "simulation_data"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="twin_runs.run_id", index=True)
    
    # Same structure as HistoricalMESData for consistency
    timestamp: datetime = Field(index=True)
    production_order_id: Optional[str] = Field(default=None, index=True)
    line_id: str = Field(index=True)
    equipment_id: str = Field(index=True)
    equipment_type: str
    product_id: Optional[str] = Field(default=None, index=True)
    product_name: Optional[str] = None
    machine_status: str
    downtime_reason: Optional[str] = None
    good_units_produced: int
    scrap_units_produced: int
    target_rate_units_per_5min: int
    standard_cost_per_unit: float
    sale_price_per_unit: float
    availability_score: float
    performance_score: float
    quality_score: float
    oee_score: float = Field(index=True)
    energy_consumption_kwh: Optional[float] = None


class SimulationObservable(SQLModel, table=True):
    """Raw observables from simulation (optional detailed storage)"""
    __tablename__ = "simulation_observables"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="twin_runs.run_id", index=True)
    timestamp: float  # Simulation time
    primitive_id: str = Field(index=True)
    primitive_type: str
    event_type: str = Field(index=True)
    details_json: str  # JSON of event details
    severity: Optional[str] = None
    
    # Only store if detailed logging enabled
    store_raw: bool = Field(default=False)


# ============= EXPERIMENTS & DISCOVERY =============

class Experiment(SQLModel, table=True):
    """Experiments for parameter discovery"""
    __tablename__ = "experiments"
    
    experiment_id: str = Field(primary_key=True)
    experiment_name: str
    hypothesis: Optional[str] = None
    
    # Runs involved
    baseline_run_id: str = Field(foreign_key="twin_runs.run_id")
    test_runs_json: str  # JSON array of test run IDs
    
    # Configuration
    parameter_changes_json: str  # JSON of parameter modifications
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    status: str = Field(default="planned")  # planned, running, completed, failed
    
    # Results
    results_summary_json: Optional[str] = None
    conclusion: Optional[str] = None


class DiscoveredPattern(SQLModel, table=True):
    """Patterns discovered through experiments"""
    __tablename__ = "discovered_patterns"
    
    pattern_id: Optional[int] = Field(default=None, primary_key=True)
    pattern_type: str  # correlation, causation, threshold, anomaly
    pattern_name: str
    description: str
    
    # Evidence
    evidence_json: str  # JSON of supporting data
    experiment_ids_json: str  # JSON array of experiment IDs
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Discovery metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    discovered_by: str  # LLM model or method
    validated: bool = Field(default=False)
    validation_runs_json: Optional[str] = None  # JSON array of validation run IDs


class ParameterRecommendation(SQLModel, table=True):
    """Parameter recommendations from discoveries"""
    __tablename__ = "parameter_recommendations"
    
    recommendation_id: Optional[int] = Field(default=None, primary_key=True)
    pattern_id: Optional[int] = Field(foreign_key="discovered_patterns.pattern_id")
    
    # Recommendation details
    recommendation_type: str  # efficiency, quality, throughput
    parameter_adjustments_json: str  # JSON of parameter changes
    expected_improvement_json: str  # JSON of expected KPI improvements
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Application tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    applied: bool = Field(default=False)
    applied_run_id: Optional[str] = Field(foreign_key="twin_runs.run_id")
    actual_improvement_json: Optional[str] = None  # JSON of actual results


# ============= ANALYSIS & REPORTING =============

class KPISnapshot(SQLModel, table=True):
    """KPI snapshots for quick comparison"""
    __tablename__ = "kpi_snapshots"
    
    snapshot_id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="twin_runs.run_id", index=True)
    entity_type: str  # line, equipment, product, overall
    entity_id: str
    
    # Core KPIs
    mean_oee: float
    mean_availability: float
    mean_performance: float
    mean_quality: float
    
    # Production metrics
    total_good_units: int
    total_scrap_units: int
    total_downtime_minutes: float
    
    # Additional metrics as JSON
    additional_metrics_json: str = Field(default='{}')
    
    # Time window
    period_start: datetime
    period_end: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ComparisonResult(SQLModel, table=True):
    """Results of comparing runs"""
    __tablename__ = "comparison_results"
    
    comparison_id: Optional[int] = Field(default=None, primary_key=True)
    baseline_run_id: str = Field(foreign_key="twin_runs.run_id")
    comparison_run_id: str = Field(foreign_key="twin_runs.run_id")
    
    # Comparison metrics
    oee_delta: float
    availability_delta: float
    performance_delta: float
    quality_delta: float
    production_delta: int
    
    # Statistical significance
    statistical_test: Optional[str] = None
    p_value: Optional[float] = None
    is_significant: bool = Field(default=False)
    
    # Analysis
    analysis_json: str  # JSON of detailed comparison
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2. Database Manager (`database/manager.py`)
```python
"""Database manager using SQLModel with YAML ontologies"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from sqlmodel import create_engine, SQLModel, Session
import yaml
import json
import pandas as pd
from datetime import datetime

from database.models import *

class TwinDatabaseManager:
    """Manage twin database with YAML ontologies"""
    
    def __init__(self, 
                 db_path: Optional[Path] = None,
                 ontology_path: Optional[Path] = None,
                 manifest_dir: Optional[Path] = None):
        
        # Database setup
        self.db_path = db_path or Path("data/twin_database.db")
        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False}
        )
        
        # YAML file paths
        self.ontology_path = ontology_path or Path("ontology/twin_ontology.yaml")
        self.manifest_dir = manifest_dir or Path("manifests/")
        
        # Cache for YAML data
        self._ontology_cache = None
        self._manifest_cache = {}
        
    def create_all_tables(self):
        """Create all database tables"""
        SQLModel.metadata.create_all(self.engine)
        print(f"✓ Created tables in {self.db_path}")
        
    def load_ontology(self) -> Dict[str, Any]:
        """Load ontology from YAML file (cached)"""
        if self._ontology_cache is None:
            with open(self.ontology_path) as f:
                self._ontology_cache = yaml.safe_load(f)
        return self._ontology_cache
    
    def load_manifest(self, manifest_name: str) -> Dict[str, Any]:
        """Load manifest from YAML file (cached)"""
        if manifest_name not in self._manifest_cache:
            manifest_path = self.manifest_dir / f"{manifest_name}.yaml"
            with open(manifest_path) as f:
                self._manifest_cache[manifest_name] = yaml.safe_load(f)
        return self._manifest_cache[manifest_name]
    
    def import_historical_data(self, csv_path: Path):
        """Import historical MES data from CSV"""
        df = pd.read_csv(csv_path)
        
        with Session(self.engine) as session:
            # Check if already imported
            existing = session.query(HistoricalMESData).first()
            if existing:
                print("Historical data already imported")
                return
            
            # Import records
            for _, row in df.iterrows():
                record = HistoricalMESData(
                    timestamp=pd.to_datetime(row['Timestamp']),
                    production_order_id=row.get('ProductionOrderID'),
                    line_id=str(row['LineID']),
                    equipment_id=row['EquipmentID'],
                    equipment_type=row['EquipmentType'],
                    product_id=row.get('ProductID'),
                    product_name=row.get('ProductName'),
                    machine_status=row['MachineStatus'],
                    downtime_reason=row.get('DowntimeReason'),
                    good_units_produced=int(row['GoodUnitsProduced']),
                    scrap_units_produced=int(row['ScrapUnitsProduced']),
                    target_rate_units_per_5min=int(row['TargetRate_units_per_5min']),
                    standard_cost_per_unit=float(row['StandardCost_per_unit']),
                    sale_price_per_unit=float(row['SalePrice_per_unit']),
                    availability_score=float(row['Availability_Score']),
                    performance_score=float(row['Performance_Score']),
                    quality_score=float(row['Quality_Score']),
                    oee_score=float(row['OEE_Score']),
                    energy_consumption_kwh=row.get('Energy_Consumption_kWh'),
                    source="historical"
                )
                session.add(record)
            
            session.commit()
            print(f"✓ Imported {len(df)} historical records")
    
    def sync_configurations_from_manifests(self):
        """Sync equipment and product configs from manifest YAMLs"""
        
        with Session(self.engine) as session:
            # Load and sync equipment manifest
            equipment_manifest = self.load_manifest("equipment_manifest")
            
            for eq_id, eq_data in equipment_manifest.get('equipment', {}).items():
                # Check if exists
                existing = session.get(EquipmentConfig, eq_id)
                
                if existing:
                    # Update existing
                    for key, value in eq_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new
                    config = EquipmentConfig(
                        equipment_id=eq_id,
                        equipment_type=eq_data['type'],
                        line_id=eq_data.get('line', 'LINE1'),
                        position=eq_data.get('position'),
                        base_rate=eq_data['base_rate'],
                        mtbf=eq_data['mtbf'],
                        mttr=eq_data['mttr'],
                        energy_consumption_rate=eq_data.get('energy_consumption_rate', 5.0),
                        failure_patterns_json=json.dumps(
                            eq_data.get('failure_patterns', {})
                        ),
                        performance_by_product_json=json.dumps(
                            eq_data.get('performance_by_product', {})
                        )
                    )
                    session.add(config)
            
            # Load and sync production manifest
            production_manifest = self.load_manifest("production_manifest")
            
            for prod_id, prod_data in production_manifest.get('products', {}).items():
                existing = session.get(ProductConfig, prod_id)
                
                if not existing:
                    config = ProductConfig(
                        product_id=prod_id,
                        product_name=prod_data['name'],
                        target_rate_units_per_5min=prod_data['target_rate_units_per_5min'],
                        standard_cost_per_unit=prod_data['standard_cost_per_unit'],
                        sale_price_per_unit=prod_data['sale_price_per_unit'],
                        scrap_rate_normal=prod_data['scrap_rates']['normal'],
                        scrap_rate_startup=prod_data['scrap_rates']['startup'],
                        scrap_rate_quality_issue=prod_data['scrap_rates'].get('quality_issue'),
                        properties_json=json.dumps(prod_data.get('properties', {}))
                    )
                    session.add(config)
            
            session.commit()
            print("✓ Synced configurations from manifests")
    
    def get_ontology_version(self) -> str:
        """Get version of current ontology"""
        ontology = self.load_ontology()
        return ontology.get('metadata', {}).get('version', '1.0.0')
    
    def get_manifest_version(self) -> str:
        """Get combined version hash of manifests"""
        import hashlib
        combined = ""
        for manifest_file in sorted(self.manifest_dir.glob("*.yaml")):
            with open(manifest_file) as f:
                combined += f.read()
        return hashlib.md5(combined.encode()).hexdigest()[:8]
```

### 3. Repository Layer (`database/repositories.py`)
```python
"""Repository pattern for database operations"""

from sqlmodel import Session, select, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from database.models import *

class TwinRunRepository:
    """Repository for twin run operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_run(self,
                   run_type: str,
                   ontology_version: str,
                   manifest_version: str,
                   parameters: Dict[str, Any],
                   parent_run_id: Optional[str] = None) -> TwinRun:
        """Create a new twin run"""
        
        run_id = f"{run_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        run = TwinRun(
            run_id=run_id,
            run_type=run_type,
            ontology_version=ontology_version,
            manifest_version=manifest_version,
            parameter_set_json=json.dumps(parameters),
            config_delta_json=json.dumps({}),
            seed=parameters.get('seed', 42),
            started_at=datetime.utcnow(),
            simulation_days=parameters.get('simulation_days', 1),
            status="pending",
            parent_run_id=parent_run_id
        )
        
        self.session.add(run)
        self.session.commit()
        return run
    
    def update_run_status(self, 
                         run_id: str, 
                         status: str,
                         kpi_summary: Optional[Dict[str, Any]] = None):
        """Update run status and results"""
        run = self.session.get(TwinRun, run_id)
        if run:
            run.status = status
            if status == "completed":
                run.finished_at = datetime.utcnow()
            if kpi_summary:
                run.kpi_summary_json = json.dumps(kpi_summary)
            self.session.commit()
    
    def get_baseline_run(self) -> Optional[TwinRun]:
        """Get the most recent baseline run"""
        statement = select(TwinRun).where(
            TwinRun.run_type == "baseline",
            TwinRun.status == "completed"
        ).order_by(TwinRun.started_at.desc())
        
        return self.session.exec(statement).first()


class SimulationDataRepository:
    """Repository for simulation data operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def store_simulation_data(self,
                             run_id: str,
                             mes_data: pd.DataFrame):
        """Store simulation output in MES format"""
        
        for _, row in mes_data.iterrows():
            record = SimulationData(
                run_id=run_id,
                timestamp=row['Timestamp'],
                production_order_id=row.get('ProductionOrderID'),
                line_id=row['LineID'],
                equipment_id=row['EquipmentID'],
                equipment_type=row['EquipmentType'],
                product_id=row.get('ProductID'),
                product_name=row.get('ProductName'),
                machine_status=row['MachineStatus'],
                downtime_reason=row.get('DowntimeReason'),
                good_units_produced=row['GoodUnitsProduced'],
                scrap_units_produced=row['ScrapUnitsProduced'],
                target_rate_units_per_5min=row['TargetRate_units_per_5min'],
                standard_cost_per_unit=row['StandardCost_per_unit'],
                sale_price_per_unit=row['SalePrice_per_unit'],
                availability_score=row['Availability_Score'],
                performance_score=row['Performance_Score'],
                quality_score=row['Quality_Score'],
                oee_score=row['OEE_Score'],
                energy_consumption_kwh=row.get('Energy_Consumption_kWh')
            )
            self.session.add(record)
        
        self.session.commit()
    
    def calculate_kpi_snapshot(self, run_id: str) -> Dict[str, Any]:
        """Calculate KPI summary for a run"""
        
        # Query simulation data
        statement = select(SimulationData).where(
            SimulationData.run_id == run_id
        )
        data = self.session.exec(statement).all()
        
        if not data:
            return {}
        
        # Calculate aggregates
        total_good = sum(d.good_units_produced for d in data)
        total_scrap = sum(d.scrap_units_produced for d in data)
        
        oee_values = [d.oee_score for d in data if d.oee_score > 0]
        availability_values = [d.availability_score for d in data if d.availability_score > 0]
        performance_values = [d.performance_score for d in data if d.performance_score > 0]
        quality_values = [d.quality_score for d in data if d.quality_score > 0]
        
        return {
            'mean_oee': sum(oee_values) / len(oee_values) if oee_values else 0,
            'mean_availability': sum(availability_values) / len(availability_values) if availability_values else 0,
            'mean_performance': sum(performance_values) / len(performance_values) if performance_values else 0,
            'mean_quality': sum(quality_values) / len(quality_values) if quality_values else 0,
            'total_good_units': total_good,
            'total_scrap_units': total_scrap,
            'scrap_rate': total_scrap / (total_good + total_scrap) if (total_good + total_scrap) > 0 else 0
        }


class ExperimentRepository:
    """Repository for experiment tracking"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_experiment(self,
                         name: str,
                         hypothesis: str,
                         baseline_run_id: str,
                         parameter_changes: Dict[str, Any]) -> Experiment:
        """Create new experiment"""
        
        experiment_id = f"exp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        experiment = Experiment(
            experiment_id=experiment_id,
            experiment_name=name,
            hypothesis=hypothesis,
            baseline_run_id=baseline_run_id,
            test_runs_json=json.dumps([]),
            parameter_changes_json=json.dumps(parameter_changes),
            created_by="system",
            status="planned"
        )
        
        self.session.add(experiment)
        self.session.commit()
        return experiment
```

### 4. Integration Module (`database/integration.py`)
```python
"""Integration with twin model"""

from pathlib import Path
from typing import Dict, Any, Optional
import simpy
from sqlmodel import Session

from database.manager import TwinDatabaseManager
from database.repositories import *
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction import MESTransducer

class TwinDatabaseIntegration:
    """Integrate twin model with database"""
    
    def __init__(self, db_manager: Optional[TwinDatabaseManager] = None):
        self.db_manager = db_manager or TwinDatabaseManager()
        
    def run_simulation_to_db(self,
                            run_type: str = "experiment",
                            parameters: Dict[str, Any] = None,
                            days: int = 1) -> str:
        """Run simulation and store results in database"""
        
        parameters = parameters or {}
        
        # Get versions
        ontology_version = self.db_manager.get_ontology_version()
        manifest_version = self.db_manager.get_manifest_version()
        
        with Session(self.db_manager.engine) as session:
            # Create run record
            run_repo = TwinRunRepository(session)
            run = run_repo.create_run(
                run_type=run_type,
                ontology_version=ontology_version,
                manifest_version=manifest_version,
                parameters=parameters
            )
            
            try:
                # Update status to running
                run_repo.update_run_status(run.run_id, "running")
                
                # Build and run model
                builder = OntologyDrivenModelBuilder(
                    self.db_manager.ontology_path,
                    self.db_manager.manifest_dir
                )
                
                env = simpy.Environment()
                model = builder.build_model(env)
                env.run(until=days * 24 * 60)
                
                # Collect observables
                all_observables = []
                for primitive_id, observables in builder.get_observables().items():
                    for obs in observables:
                        obs['primitive_id'] = primitive_id
                        obs['primitive_type'] = type(builder.primitives[primitive_id]).__name__
                    all_observables.extend(observables)
                
                # Transduce to MES format
                transducer = MESTransducer()
                mes_df = transducer.process_observables(
                    all_observables,
                    builder.manifests
                )
                
                # Store simulation data
                sim_repo = SimulationDataRepository(session)
                sim_repo.store_simulation_data(run.run_id, mes_df)
                
                # Calculate KPIs
                kpi_summary = sim_repo.calculate_kpi_snapshot(run.run_id)
                
                # Update run as completed
                run_repo.update_run_status(
                    run.run_id, 
                    "completed",
                    kpi_summary
                )
                
                return run.run_id
                
            except Exception as e:
                run_repo.update_run_status(run.run_id, "failed")
                raise e
```

### 5. CLI Tool (`database/cli.py`)
```python
"""CLI for database operations"""

import click
from pathlib import Path
from database.manager import TwinDatabaseManager
from database.integration import TwinDatabaseIntegration

@click.group()
def cli():
    """Twin Database Management CLI"""
    pass

@cli.command()
def init():
    """Initialize database with all tables"""
    manager = TwinDatabaseManager()
    manager.create_all_tables()
    click.echo("✓ Database initialized")

@cli.command()
@click.argument('csv_path', type=click.Path(exists=True))
def import_historical(csv_path):
    """Import historical MES data from CSV"""
    manager = TwinDatabaseManager()
    manager.import_historical_data(Path(csv_path))

@cli.command()
def sync_manifests():
    """Sync configurations from manifest YAMLs"""
    manager = TwinDatabaseManager()
    manager.sync_configurations_from_manifests()

@cli.command()
@click.option('--days', default=1, help='Days to simulate')
@click.option('--type', default='experiment', help='Run type')
def run_simulation(days, type):
    """Run simulation and store in database"""
    integration = TwinDatabaseIntegration()
    run_id = integration.run_simulation_to_db(
        run_type=type,
        days=days
    )
    click.echo(f"✓ Simulation complete: {run_id}")

if __name__ == '__main__':
    cli()
```

## Key Design Points

1. **Ontologies Stay as YAML**
   - Not stored in database
   - Version tracked by hash/version string
   - Loaded and cached when needed

2. **Historical Data Table**
   - `HistoricalMESData` for baseline reference
   - Includes source tracking and quality scores

3. **Twin Support Tables**
   - Configuration sync from manifests
   - Simulation runs with lineage
   - Experiment tracking
   - Pattern discovery
   - KPI snapshots for comparison

4. **Clean Integration**
   - Repositories for data access
   - Integration module for twin model
   - CLI for operations

5. **Leverages Existing Work**
   - Uses SQLModel patterns
   - Compatible with existing API
   - Extends rather than replaces

## Implementation Steps

1. **Create database package structure**
   ```
   database/
   ├── __init__.py
   ├── models.py           # SQLModel table definitions
   ├── manager.py          # Database manager
   ├── repositories.py     # Repository pattern implementations
   ├── integration.py      # Twin model integration
   └── cli.py             # Command-line interface
   ```

2. **Initialize database**
   ```bash
   python -m database.cli init
   ```

3. **Import historical data**
   ```bash
   python -m database.cli import-historical archive/misc/data/mes_data_with_kpis.csv
   ```

4. **Sync manifests**
   ```bash
   python -m database.cli sync-manifests
   ```

5. **Run simulation**
   ```bash
   python -m database.cli run-simulation --days 3 --type baseline
   ```

This design keeps ontologies as YAML files while providing comprehensive database support for twin operations.