"""
SQLModel database models for virtual twin system

Keeps ontologies as YAML files, stores operational data in database
"""

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