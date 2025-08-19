"""Repository pattern for database operations"""

from sqlmodel import Session, select, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import pandas as pd

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
    
    def add_test_run(self, experiment_id: str, run_id: str):
        """Add a test run to an experiment"""
        experiment = self.session.get(Experiment, experiment_id)
        if experiment:
            test_runs = json.loads(experiment.test_runs_json)
            test_runs.append(run_id)
            experiment.test_runs_json = json.dumps(test_runs)
            self.session.commit()
    
    def complete_experiment(self, 
                           experiment_id: str,
                           results_summary: Dict[str, Any],
                           conclusion: str):
        """Mark experiment as completed with results"""
        experiment = self.session.get(Experiment, experiment_id)
        if experiment:
            experiment.status = "completed"
            experiment.results_summary_json = json.dumps(results_summary)
            experiment.conclusion = conclusion
            self.session.commit()


class PatternRepository:
    """Repository for discovered patterns"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_pattern(self,
                      pattern_type: str,
                      pattern_name: str,
                      description: str,
                      evidence: Dict[str, Any],
                      experiment_ids: List[str],
                      confidence_score: float) -> DiscoveredPattern:
        """Create a new discovered pattern"""
        
        pattern = DiscoveredPattern(
            pattern_type=pattern_type,
            pattern_name=pattern_name,
            description=description,
            evidence_json=json.dumps(evidence),
            experiment_ids_json=json.dumps(experiment_ids),
            confidence_score=confidence_score,
            discovered_by="system",
            validated=False
        )
        
        self.session.add(pattern)
        self.session.commit()
        return pattern
    
    def validate_pattern(self, 
                        pattern_id: int,
                        validation_run_ids: List[str]):
        """Mark a pattern as validated"""
        pattern = self.session.get(DiscoveredPattern, pattern_id)
        if pattern:
            pattern.validated = True
            pattern.validation_runs_json = json.dumps(validation_run_ids)
            self.session.commit()


class RecommendationRepository:
    """Repository for parameter recommendations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_recommendation(self,
                            pattern_id: Optional[int],
                            recommendation_type: str,
                            parameter_adjustments: Dict[str, Any],
                            expected_improvement: Dict[str, float],
                            confidence: float) -> ParameterRecommendation:
        """Create a new parameter recommendation"""
        
        recommendation = ParameterRecommendation(
            pattern_id=pattern_id,
            recommendation_type=recommendation_type,
            parameter_adjustments_json=json.dumps(parameter_adjustments),
            expected_improvement_json=json.dumps(expected_improvement),
            confidence=confidence,
            applied=False
        )
        
        self.session.add(recommendation)
        self.session.commit()
        return recommendation
    
    def apply_recommendation(self,
                            recommendation_id: int,
                            run_id: str,
                            actual_improvement: Dict[str, float]):
        """Mark recommendation as applied with results"""
        recommendation = self.session.get(ParameterRecommendation, recommendation_id)
        if recommendation:
            recommendation.applied = True
            recommendation.applied_run_id = run_id
            recommendation.actual_improvement_json = json.dumps(actual_improvement)
            self.session.commit()


class KPIRepository:
    """Repository for KPI snapshots and comparisons"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_kpi_snapshot(self,
                          run_id: str,
                          entity_type: str,
                          entity_id: str,
                          kpis: Dict[str, Any],
                          period_start: datetime,
                          period_end: datetime) -> KPISnapshot:
        """Create a KPI snapshot"""
        
        snapshot = KPISnapshot(
            run_id=run_id,
            entity_type=entity_type,
            entity_id=entity_id,
            mean_oee=kpis['mean_oee'],
            mean_availability=kpis['mean_availability'],
            mean_performance=kpis['mean_performance'],
            mean_quality=kpis['mean_quality'],
            total_good_units=kpis['total_good_units'],
            total_scrap_units=kpis['total_scrap_units'],
            total_downtime_minutes=kpis.get('total_downtime_minutes', 0),
            additional_metrics_json=json.dumps(kpis.get('additional', {})),
            period_start=period_start,
            period_end=period_end
        )
        
        self.session.add(snapshot)
        self.session.commit()
        return snapshot
    
    def create_comparison(self,
                         baseline_run_id: str,
                         comparison_run_id: str) -> ComparisonResult:
        """Create a comparison between two runs"""
        
        # Get KPI snapshots for both runs
        baseline_statement = select(KPISnapshot).where(
            KPISnapshot.run_id == baseline_run_id,
            KPISnapshot.entity_type == "overall"
        )
        comparison_statement = select(KPISnapshot).where(
            KPISnapshot.run_id == comparison_run_id,
            KPISnapshot.entity_type == "overall"
        )
        
        baseline = self.session.exec(baseline_statement).first()
        comparison = self.session.exec(comparison_statement).first()
        
        if not baseline or not comparison:
            raise ValueError("Missing KPI snapshots for comparison")
        
        # Calculate deltas
        comparison_result = ComparisonResult(
            baseline_run_id=baseline_run_id,
            comparison_run_id=comparison_run_id,
            oee_delta=comparison.mean_oee - baseline.mean_oee,
            availability_delta=comparison.mean_availability - baseline.mean_availability,
            performance_delta=comparison.mean_performance - baseline.mean_performance,
            quality_delta=comparison.mean_quality - baseline.mean_quality,
            production_delta=comparison.total_good_units - baseline.total_good_units,
            analysis_json=json.dumps({
                'baseline_kpis': {
                    'oee': baseline.mean_oee,
                    'availability': baseline.mean_availability,
                    'performance': baseline.mean_performance,
                    'quality': baseline.mean_quality,
                    'production': baseline.total_good_units
                },
                'comparison_kpis': {
                    'oee': comparison.mean_oee,
                    'availability': comparison.mean_availability,
                    'performance': comparison.mean_performance,
                    'quality': comparison.mean_quality,
                    'production': comparison.total_good_units
                }
            })
        )
        
        self.session.add(comparison_result)
        self.session.commit()
        return comparison_result