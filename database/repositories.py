"""Repository pattern for database operations"""

from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import (
    TwinRun,
    SimulationData,
    Experiment,
    DiscoveredPattern,
    ParameterRecommendation,
    KPISnapshot,
    ComparisonResult,
)
from config.config_loader import ConfigLoader, ConfigurationError

# Load database configuration
try:
    _db_config = ConfigLoader.load_config("database")
except ConfigurationError:
    # Use defaults if config not available (for testing)
    _db_config = {"processing": {"batch_size": 5000, "chunk_size": 10000, "progress_report_interval": 50000}}


class TwinRunRepository:
    """Repository for twin run operations"""

    def __init__(self, session: Session):
        self.session = session

    def create_run(
        self,
        run_type: str,
        ontology_version: str,
        manifest_version: str,
        parameters: Dict[str, Any],
        parent_run_id: Optional[str] = None,
    ) -> TwinRun:
        """Create a new twin run"""

        run_id = f"{run_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        run = TwinRun(
            run_id=run_id,
            run_type=run_type,
            ontology_version=ontology_version,
            manifest_version=manifest_version,
            parameter_set_json=json.dumps(parameters),
            config_delta_json=json.dumps({}),
            seed=parameters.get("seed", 42),
            started_at=datetime.utcnow(),
            simulation_days=parameters.get("simulation_days", 1),
            status="pending",
            parent_run_id=parent_run_id,
        )

        self.session.add(run)
        self.session.commit()
        return run

    def update_run_status(self, run_id: str, status: str, kpi_summary: Optional[Dict[str, Any]] = None):
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
        statement = (
            select(TwinRun)
            .where(TwinRun.run_type == "baseline", TwinRun.status == "completed")
            .order_by(TwinRun.started_at.desc())  # type: ignore[attr-defined]
        )

        return self.session.exec(statement).first()


class SimulationDataRepository:
    """Repository for simulation data operations"""

    def __init__(self, session: Session):
        self.session = session

    def store_simulation_data(self, run_id: str, mes_data: pd.DataFrame):
        """Store simulation output in MES format"""
        from datetime import datetime

        for _, row in mes_data.iterrows():
            # Convert timestamp string to datetime if needed
            timestamp = row["Timestamp"]
            if isinstance(timestamp, str):
                timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

            record = SimulationData(
                run_id=run_id,
                timestamp=timestamp,
                production_order_id=row.get("ProductionOrderID"),
                line_id=row["LineID"],
                equipment_id=row["EquipmentID"],
                equipment_type=row["EquipmentType"],
                product_id=row.get("ProductID"),
                product_name=row.get("ProductName"),
                machine_status=row["MachineStatus"],
                downtime_reason=row.get("DowntimeReason"),
                good_units_produced=row["GoodUnitsProduced"],
                scrap_units_produced=row["ScrapUnitsProduced"],
                target_rate_units_per_5min=row["TargetRate_units_per_5min"],
                standard_cost_per_unit=row["StandardCost_per_unit"],
                sale_price_per_unit=row["SalePrice_per_unit"],
                availability_score=row["Availability_Score"],
                performance_score=row["Performance_Score"],
                quality_score=row["Quality_Score"],
                oee_score=row["OEE_Score"],
                energy_consumption_kwh=row.get("Energy_Consumption_kWh"),
            )
            self.session.add(record)

        self.session.commit()

    def batch_insert_events(self, run_id: str, events: List[Dict[str, Any]], batch_size: int = 1000) -> int:
        """Batch insert simulation events for performance.

        Efficiently inserts large numbers of events in batches
        to minimize database round-trips and transaction overhead.

        Args:
            run_id: Simulation run identifier
            events: List of event dictionaries to insert
            batch_size: Number of records per batch (default 1000)

        Returns:
            Number of events inserted
        """
        from datetime import datetime

        total_inserted = 0
        batch_records = []

        for event in events:
            # Convert event to SimulationData format
            # Handle different event structures flexibly
            timestamp = event.get("timestamp", 0)
            if isinstance(timestamp, (int, float)):
                # Convert simulation time to datetime
                base_time = datetime.utcnow()
                timestamp = base_time + timedelta(minutes=timestamp)
            elif isinstance(timestamp, str):
                timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

            # Map event fields to database columns
            record = SimulationData(
                run_id=run_id,
                timestamp=timestamp,
                production_order_id=event.get("production_order_id"),
                line_id=event.get("line_id", "LINE-001"),
                equipment_id=event.get("primitive_id", event.get("equipment_id", "UNKNOWN")),
                equipment_type=event.get("equipment_type", event.get("event_type", "Equipment")),
                product_id=event.get("product_id"),
                product_name=event.get("product_name"),
                machine_status=event.get("state", event.get("machine_status", "UNKNOWN")),
                downtime_reason=event.get("downtime_reason"),
                good_units_produced=event.get("good_units", event.get("good_units_produced", 0)),
                scrap_units_produced=event.get("scrap_units", event.get("scrap_units_produced", 0)),
                target_rate_units_per_5min=event.get("target_rate", 0),
                standard_cost_per_unit=event.get("standard_cost", 0),
                sale_price_per_unit=event.get("sale_price", 0),
                availability_score=event.get("availability", 0),
                performance_score=event.get("performance", 0),
                quality_score=event.get("quality", 0),
                oee_score=event.get("oee", 0),
                energy_consumption_kwh=event.get("energy_consumption", 0),
            )

            batch_records.append(record)

            # Flush batch when it reaches the size limit
            if len(batch_records) >= batch_size:
                self.session.bulk_save_objects(batch_records)
                self.session.commit()
                total_inserted += len(batch_records)
                batch_records = []

        # Insert remaining records
        if batch_records:
            self.session.bulk_save_objects(batch_records)
            self.session.commit()
            total_inserted += len(batch_records)

        return total_inserted

    def flush_cache_to_database(self, run_id: str, cache_path: str, batch_size: int = None) -> Dict[str, Any]:  # type: ignore[assignment]
        """Flush events from cache to database in batches.

        Reads events from the ObservableCache and efficiently
        inserts them into the database using batch operations.
        This enables persisting simulation data without keeping
        everything in memory.

        Args:
            run_id: Simulation run identifier
            cache_path: Path to cache directory
            batch_size: Number of records per database batch

        Returns:
            Dictionary with flush statistics
        """
        from pathlib import Path
        import time
        import json
        import numpy as np

        # Use config value if not provided
        if batch_size is None:
            batch_size = _db_config["processing"]["batch_size"]

        start_time = time.time()

        # Load cache metadata to find files
        cache_dir = Path(cache_path)
        metadata_file = cache_dir / "metadata.json"

        if not metadata_file.exists():
            return {
                "events_in_cache": 0,
                "events_processed": 0,
                "events_inserted": 0,
                "flush_time_seconds": 0,
                "events_per_second": 0,
                "cache_size_mb": 0,
            }

        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        total_events = metadata.get("total_events", 0)

        # Calculate total size
        total_size_mb = 0
        for file_info in metadata.get("files", []):
            file_path = cache_dir / file_info["filename"]
            if file_path.exists():
                total_size_mb += file_path.stat().st_size / (1024 * 1024)

        # Process events in chunks
        events_processed = 0
        events_inserted = 0
        chunk_size = _db_config["processing"]["chunk_size"]  # Read chunks from cache

        print(f"  Flushing {total_events:,} events to database...")

        # Read events from cache files directly
        all_events = []

        for file_info in metadata.get("files", []):
            file_path = cache_dir / file_info["filename"]
            if not file_path.exists():
                continue

            # Open memory-mapped file for reading
            # Reconstruct dtype from first file
            dtype = np.dtype(
                [
                    ("timestamp", np.float64),
                    ("event_type", "U32"),
                    ("primitive_id", "U32"),
                    ("data", np.uint8, (1024,)),  # Default size
                ]
            )

            mmap = np.memmap(file_path, dtype=dtype, mode="r", shape=(file_info["max_events"],))

            # Read only populated entries
            num_events = file_info["current_events"]
            data = mmap[:num_events]

            # Convert to events
            for row in data:
                # Reconstruct event
                json_bytes = row["data"].tobytes()
                json_str = json_bytes.rstrip(b"\0").decode("utf-8")

                event = json.loads(json_str) if json_str else {}
                event["timestamp"] = float(row["timestamp"])
                event["event_type"] = str(row["event_type"])
                event["primitive_id"] = str(row["primitive_id"])

                all_events.append(event)

                # Process in batches
                if len(all_events) >= chunk_size:
                    inserted = self.batch_insert_events(run_id, all_events[:chunk_size], batch_size)
                    events_inserted += inserted
                    events_processed += len(all_events[:chunk_size])
                    all_events = all_events[chunk_size:]

                    # Progress update
                    progress_interval = _db_config["processing"]["progress_report_interval"]
                    if events_processed % progress_interval == 0:
                        print(f"    Processed {events_processed:,}/{total_events:,} events...")

            del mmap  # Close memory map

        # Insert remaining events
        if all_events:
            inserted = self.batch_insert_events(run_id, all_events, batch_size)
            events_inserted += inserted
            events_processed += len(all_events)

        elapsed_time = time.time() - start_time

        return {
            "events_in_cache": total_events,
            "events_processed": events_processed,
            "events_inserted": events_inserted,
            "flush_time_seconds": elapsed_time,
            "events_per_second": events_inserted / elapsed_time if elapsed_time > 0 else 0,
            "cache_size_mb": total_size_mb,
        }

    def calculate_kpi_snapshot(self, run_id: str) -> Dict[str, Any]:
        """Calculate KPI summary for a run"""

        # Query simulation data
        statement = select(SimulationData).where(SimulationData.run_id == run_id)
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
            "mean_oee": sum(oee_values) / len(oee_values) if oee_values else 0,
            "mean_availability": sum(availability_values) / len(availability_values) if availability_values else 0,
            "mean_performance": sum(performance_values) / len(performance_values) if performance_values else 0,
            "mean_quality": sum(quality_values) / len(quality_values) if quality_values else 0,
            "total_good_units": total_good,
            "total_scrap_units": total_scrap,
            "scrap_rate": total_scrap / (total_good + total_scrap) if (total_good + total_scrap) > 0 else 0,
        }


class ExperimentRepository:
    """Repository for experiment tracking"""

    def __init__(self, session: Session):
        self.session = session

    def create_experiment(
        self, name: str, hypothesis: str, baseline_run_id: str, parameter_changes: Dict[str, Any]
    ) -> Experiment:
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
            status="planned",
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

    def complete_experiment(self, experiment_id: str, results_summary: Dict[str, Any], conclusion: str):
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

    def create_pattern(
        self,
        pattern_type: str,
        pattern_name: str,
        description: str,
        evidence: Dict[str, Any],
        experiment_ids: List[str],
        confidence_score: float,
    ) -> DiscoveredPattern:
        """Create a new discovered pattern"""

        pattern = DiscoveredPattern(
            pattern_type=pattern_type,
            pattern_name=pattern_name,
            description=description,
            evidence_json=json.dumps(evidence),
            experiment_ids_json=json.dumps(experiment_ids),
            confidence_score=confidence_score,
            discovered_by="system",
            validated=False,
        )

        self.session.add(pattern)
        self.session.commit()
        return pattern

    def validate_pattern(self, pattern_id: int, validation_run_ids: List[str]):
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

    def create_recommendation(
        self,
        pattern_id: Optional[int],
        recommendation_type: str,
        parameter_adjustments: Dict[str, Any],
        expected_improvement: Dict[str, float],
        confidence: float,
    ) -> ParameterRecommendation:
        """Create a new parameter recommendation"""

        recommendation = ParameterRecommendation(
            pattern_id=pattern_id,
            recommendation_type=recommendation_type,
            parameter_adjustments_json=json.dumps(parameter_adjustments),
            expected_improvement_json=json.dumps(expected_improvement),
            confidence=confidence,
            applied=False,
        )

        self.session.add(recommendation)
        self.session.commit()
        return recommendation

    def apply_recommendation(self, recommendation_id: int, run_id: str, actual_improvement: Dict[str, float]):
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

    def create_kpi_snapshot(
        self,
        run_id: str,
        entity_type: str,
        entity_id: str,
        kpis: Dict[str, Any],
        period_start: datetime,
        period_end: datetime,
    ) -> KPISnapshot:
        """Create a KPI snapshot"""

        snapshot = KPISnapshot(
            run_id=run_id,
            entity_type=entity_type,
            entity_id=entity_id,
            mean_oee=kpis["mean_oee"],
            mean_availability=kpis["mean_availability"],
            mean_performance=kpis["mean_performance"],
            mean_quality=kpis["mean_quality"],
            total_good_units=kpis["total_good_units"],
            total_scrap_units=kpis["total_scrap_units"],
            total_downtime_minutes=kpis.get("total_downtime_minutes", 0),
            additional_metrics_json=json.dumps(kpis.get("additional", {})),
            period_start=period_start,
            period_end=period_end,
        )

        self.session.add(snapshot)
        self.session.commit()
        return snapshot

    def create_comparison(self, baseline_run_id: str, comparison_run_id: str) -> ComparisonResult:
        """Create a comparison between two runs"""

        # Get KPI snapshots for both runs
        baseline_statement = select(KPISnapshot).where(
            KPISnapshot.run_id == baseline_run_id, KPISnapshot.entity_type == "overall"
        )
        comparison_statement = select(KPISnapshot).where(
            KPISnapshot.run_id == comparison_run_id, KPISnapshot.entity_type == "overall"
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
            analysis_json=json.dumps(
                {
                    "baseline_kpis": {
                        "oee": baseline.mean_oee,
                        "availability": baseline.mean_availability,
                        "performance": baseline.mean_performance,
                        "quality": baseline.mean_quality,
                        "production": baseline.total_good_units,
                    },
                    "comparison_kpis": {
                        "oee": comparison.mean_oee,
                        "availability": comparison.mean_availability,
                        "performance": comparison.mean_performance,
                        "quality": comparison.mean_quality,
                        "production": comparison.total_good_units,
                    },
                }
            ),
        )

        self.session.add(comparison_result)
        self.session.commit()
        return comparison_result
