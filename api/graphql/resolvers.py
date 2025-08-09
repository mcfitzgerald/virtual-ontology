"""
GraphQL Resolvers for Virtual Twin
Thin wrappers around existing twin functionality
"""

import strawberry
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .types import (
    TwinRun, SimulationDataPoint, ParameterUpdate, Recommendation,
    ComparisonResult, ROIResult, KPISummary, RunType, SimulationParameters,
    ROICalculationInput, SyncHealthReport, SyncHealthStatus
)
from twin.simulation_runner import SimulationRun
from twin.actionable_parameters import ActionableParameters


def convert_run_to_graphql(run: SimulationRun) -> TwinRun:
    """Convert database run to GraphQL type"""
    kpi_summary = None
    if run.kpi_summary:
        kpi_summary = KPISummary(
            mean_oee=run.kpi_summary.get("mean_oee", 0),
            mean_availability=run.kpi_summary.get("mean_availability", 0),
            mean_performance=run.kpi_summary.get("mean_performance", 0),
            mean_quality=run.kpi_summary.get("mean_quality", 0),
            downtime_percentage=run.kpi_summary.get("downtime_percentage", 0),
            scrap_rate=run.kpi_summary.get("scrap_rate", 0)
        )
    
    return TwinRun(
        run_id=run.run_id,
        run_type=RunType[run.run_type.upper()],
        seed=run.seed,
        generator_version=run.generator_version,
        parent_run_id=run.parent_run_id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        config_delta=run.config_delta,
        data_hash=run.data_hash,
        output_path=run.output_path,
        kpi_summary=kpi_summary,
        notes=run.notes,
        status=run.status
    )


@strawberry.type
class Query:
    @strawberry.field
    def get_run(self, run_id: str, info: strawberry.Info) -> Optional[TwinRun]:
        """Get a specific simulation run"""
        runner = info.context["simulation_runner"]
        
        with sqlite3.connect(info.context["db_path"]) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM twin_runs WHERE run_id = ?",
                (run_id,)
            )
            row = cursor.fetchone()
            
            if row:
                run = SimulationRun(
                    run_id=row["run_id"],
                    run_type=row["run_type"],
                    seed=row["seed"],
                    generator_version=row["generator_version"],
                    parent_run_id=row["parent_run_id"],
                    started_at=datetime.fromisoformat(row["started_at"]),
                    finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
                    config_delta=json.loads(row["config_delta_json"]),
                    data_hash=row["data_hash"],
                    output_path=row["output_path"],
                    kpi_summary=json.loads(row["kpi_summary_json"]) if row["kpi_summary_json"] else None,
                    notes=row["notes"],
                    status=row["status"]
                )
                return convert_run_to_graphql(run)
        return None
    
    @strawberry.field
    def get_runs(
        self, 
        info: strawberry.Info,
        limit: int = 10,
        run_type: Optional[str] = None
    ) -> List[TwinRun]:
        """Get list of simulation runs"""
        runs = []
        
        with sqlite3.connect(info.context["db_path"]) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM twin_runs"
            params = []
            
            if run_type:
                query += " WHERE run_type = ?"
                params.append(run_type)
            
            query += " ORDER BY started_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            
            for row in cursor.fetchall():
                run = SimulationRun(
                    run_id=row["run_id"],
                    run_type=row["run_type"],
                    seed=row["seed"],
                    generator_version=row["generator_version"],
                    parent_run_id=row["parent_run_id"],
                    started_at=datetime.fromisoformat(row["started_at"]),
                    finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
                    config_delta=json.loads(row["config_delta_json"]),
                    data_hash=row["data_hash"],
                    output_path=row["output_path"],
                    kpi_summary=json.loads(row["kpi_summary_json"]) if row["kpi_summary_json"] else None,
                    notes=row["notes"],
                    status=row["status"]
                )
                runs.append(convert_run_to_graphql(run))
        
        return runs
    
    @strawberry.field
    def get_recommendations(
        self,
        scenario: str,
        info: strawberry.Info
    ) -> List[Recommendation]:
        """Get recommendations for a scenario"""
        engine = info.context["recommendation_engine"]
        
        recommendations = engine.recommend_for_scenario(scenario)
        
        result = []
        for i, rec in enumerate(recommendations.get("parameters", {}).items()):
            param_name, value = rec
            result.append(Recommendation(
                recommendation_id=f"{scenario}_{i}",
                scenario=scenario,
                parameters={param_name: value},
                expected_oee=0.75,  # Mock value
                confidence_level=0.85,
                implementation_cost=5000,
                payback_weeks=3
            ))
        
        return result
    
    @strawberry.field
    def calculate_roi(
        self,
        input: ROICalculationInput,
        info: strawberry.Info
    ) -> ROIResult:
        """Calculate ROI between two runs"""
        calculator = info.context["cost_calculator"]
        
        roi_summary = calculator.calculate_roi(
            baseline_run_id=input.baseline_run_id,
            improved_run_id=input.improved_run_id,
            n_simulations=input.n_simulations,
            time_horizon_weeks=input.time_horizon_weeks,
            include_uncertainty=input.include_uncertainty
        )
        
        return ROIResult(
            implementation_cost=roi_summary["implementation_cost"],
            weekly_savings_mean=roi_summary["weekly_savings"]["mean"],
            weekly_savings_std=roi_summary["weekly_savings"]["std"],
            confidence_interval_lower=roi_summary["weekly_savings"]["confidence_interval"][0],
            confidence_interval_upper=roi_summary["weekly_savings"]["confidence_interval"][1],
            payback_weeks_mean=roi_summary["payback_weeks"]["mean"],
            npv_mean=roi_summary["npv"]["mean"],
            npv_probability_positive=roi_summary["npv"]["probability_positive"],
            annual_benefit_mean=roi_summary["annual_benefit"]["mean"]
        )
    
    @strawberry.field
    def get_sync_health(self, info: strawberry.Info) -> List[SyncHealthReport]:
        """Get synchronization health status"""
        monitor = info.context["sync_monitor"]
        
        health_data = monitor.get_all_sync_status()
        
        reports = []
        for entity_id, data in health_data.items():
            status_str = data.get("health_status", "STALE")
            try:
                status = SyncHealthStatus[status_str]
            except KeyError:
                status = SyncHealthStatus.STALE
                
            reports.append(SyncHealthReport(
                entity_id=entity_id,
                entity_type=data.get("entity_type", "Equipment"),
                health_status=status,
                last_update=datetime.fromisoformat(data.get("last_update", datetime.now().isoformat())),
                sync_interval_minutes=data.get("sync_interval_minutes", 5),
                data_freshness_seconds=data.get("data_freshness_seconds", 0)
            ))
        
        return reports


@strawberry.type
class Mutation:
    @strawberry.mutation
    def run_simulation(
        self,
        parameters: SimulationParameters,
        info: strawberry.Info
    ) -> TwinRun:
        """Run a new simulation with specified parameters"""
        runner = info.context["simulation_runner"]
        
        # Create parameter configuration
        config = {}
        if parameters.micro_stop_probability is not None:
            config["micro_stop_probability"] = parameters.micro_stop_probability
        if parameters.performance_factor is not None:
            config["performance_factor"] = parameters.performance_factor
        if parameters.scrap_multiplier is not None:
            config["scrap_multiplier"] = parameters.scrap_multiplier
        if parameters.material_reliability is not None:
            config["material_reliability"] = parameters.material_reliability
        if parameters.cascade_sensitivity is not None:
            config["cascade_sensitivity"] = parameters.cascade_sensitivity
        
        # Run simulation
        run = runner.run_simulation(
            config_delta=config,
            duration_days=parameters.duration_days,
            seed=parameters.seed
        )
        
        return convert_run_to_graphql(run)
    
    @strawberry.mutation
    def update_parameters(
        self,
        changes: Dict[str, float],
        info: strawberry.Info
    ) -> List[ParameterUpdate]:
        """Update actionable parameters"""
        params = ActionableParameters()
        
        updates = []
        for param_name, new_value in changes.items():
            old_value = params.get_value(param_name)
            params.set_value(param_name, new_value)
            
            updates.append(ParameterUpdate(
                parameter_name=param_name,
                old_value=old_value,
                new_value=new_value,
                impact_estimate=abs(new_value - old_value) * 0.1  # Simple estimate
            ))
        
        return updates