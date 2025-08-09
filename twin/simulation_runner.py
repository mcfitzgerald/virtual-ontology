"""
Simulation Runner with Provenance Tracking
Manages simulation runs with complete reproducibility and provenance
"""

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import subprocess
import tempfile
import numpy as np
import sys
import os

# Add twin directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from actionable_parameters import ActionableParameters
from config_transformer import ConfigTransformer
from sync_health import SyncHealthMonitor


@dataclass
class SimulationRun:
    """Metadata for a simulation run with full provenance"""
    run_id: str
    run_type: str  # baseline, simulation, recommendation
    seed: int
    generator_version: str
    parent_run_id: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    config_delta: Dict[str, Any]
    data_hash: Optional[str]
    output_path: Optional[str]
    kpi_summary: Optional[Dict[str, float]]
    notes: Optional[str]
    status: str  # pending, running, completed, failed


class SimulationRunner:
    """
    Manages virtual twin simulations with complete provenance tracking
    Ensures reproducibility and traceability of all simulation runs
    """
    
    def __init__(
        self,
        db_path: str = "data/mes_database.db",
        generator_path: str = "synthetic_data_generator/mes_data_generation.py",
        generator_version: str = "1.0.0"
    ):
        self.db_path = db_path
        self.generator_path = Path(generator_path)
        self.generator_version = generator_version
        self.sync_monitor = SyncHealthMonitor(db_path)
        
        # Initialize provenance database
        self._init_provenance_db()
        
    def _init_provenance_db(self):
        """Initialize provenance tracking tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Twin runs table for complete provenance
            conn.execute("""
                CREATE TABLE IF NOT EXISTS twin_runs (
                    run_id TEXT PRIMARY KEY,
                    run_type TEXT CHECK(run_type IN ('baseline', 'simulation', 'recommendation', 'optimization')),
                    seed INTEGER NOT NULL,
                    generator_version TEXT NOT NULL,
                    parent_run_id TEXT REFERENCES twin_runs(run_id),
                    started_at TIMESTAMP NOT NULL,
                    finished_at TIMESTAMP,
                    config_delta_json TEXT NOT NULL,
                    data_hash TEXT,
                    output_path TEXT,
                    kpi_summary_json TEXT,
                    notes TEXT,
                    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed'))
                )
            """)
            
            # KPI results table with evaluation windows
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kpi_results (
                    run_id TEXT REFERENCES twin_runs(run_id),
                    entity_id TEXT NOT NULL,
                    kpi TEXT NOT NULL,
                    value REAL NOT NULL,
                    window_start TIMESTAMP NOT NULL,
                    window_end TIMESTAMP NOT NULL,
                    aggregation_method TEXT,
                    PRIMARY KEY (run_id, entity_id, kpi, window_start)
                )
            """)
            
            # Parameter history for tracking changes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS parameter_history (
                    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT REFERENCES twin_runs(run_id),
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    parameter_name TEXT NOT NULL,
                    old_value REAL,
                    new_value REAL NOT NULL,
                    change_reason TEXT
                )
            """)
            
            conn.commit()
    
    def create_baseline(
        self,
        seed: int = 42,
        duration_days: int = 7,
        notes: Optional[str] = None
    ) -> SimulationRun:
        """
        Create a baseline simulation run with default parameters
        
        Args:
            seed: Random seed for reproducibility
            duration_days: Simulation duration in days
            notes: Optional notes about the run
            
        Returns:
            SimulationRun object with run metadata
        """
        run_id = f"baseline-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # Use default parameters
        params = ActionableParameters()
        transformer = ConfigTransformer()
        
        # Create baseline config
        config = transformer.apply_parameters(params)
        
        # Save config to temp file
        config_path = Path(f"twin/configs/{run_id}.json")
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create run metadata
        run = SimulationRun(
            run_id=run_id,
            run_type="baseline",
            seed=seed,
            generator_version=self.generator_version,
            parent_run_id=None,
            started_at=datetime.now(),
            finished_at=None,
            config_delta=params.get_all_values(),
            data_hash=None,
            output_path=None,
            kpi_summary=None,
            notes=notes or "Baseline run with default parameters",
            status="pending"
        )
        
        # Store in database
        self._store_run_metadata(run)
        
        # Execute simulation
        output_path = self._execute_simulation(run, config_path, duration_days)
        
        # Calculate data hash
        data_hash = self._calculate_data_hash(output_path)
        
        # Calculate KPIs
        kpi_summary = self._calculate_kpis(output_path)
        
        # Update run metadata
        run.finished_at = datetime.now()
        run.output_path = str(output_path)
        run.data_hash = data_hash
        run.kpi_summary = kpi_summary
        run.status = "completed"
        
        # Update database
        self._update_run_metadata(run)
        
        # Update sync health
        self._update_sync_health(run)
        
        return run
    
    def run_simulation(
        self,
        parameters: ActionableParameters,
        parent_run_id: Optional[str] = None,
        seed: Optional[int] = None,
        duration_days: int = 7,
        notes: Optional[str] = None
    ) -> SimulationRun:
        """
        Run a simulation with specific parameters
        
        Args:
            parameters: ActionableParameters instance with values to test
            parent_run_id: Optional parent run for lineage tracking
            seed: Random seed (uses parent seed + 1 if not provided)
            duration_days: Simulation duration
            notes: Optional notes
            
        Returns:
            SimulationRun object with results
        """
        # Generate run ID
        run_id = f"sim-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # Determine seed
        if seed is None and parent_run_id:
            parent = self._get_run_metadata(parent_run_id)
            seed = parent.seed + 1
        elif seed is None:
            seed = np.random.randint(0, 10000)
        
        # Transform parameters to config
        transformer = ConfigTransformer()
        config = transformer.apply_parameters(parameters)
        
        # Save config
        config_path = Path(f"twin/configs/{run_id}.json")
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create run metadata
        run = SimulationRun(
            run_id=run_id,
            run_type="simulation",
            seed=seed,
            generator_version=self.generator_version,
            parent_run_id=parent_run_id,
            started_at=datetime.now(),
            finished_at=None,
            config_delta=parameters.get_all_values(),
            data_hash=None,
            output_path=None,
            kpi_summary=None,
            notes=notes,
            status="running"
        )
        
        # Store metadata
        self._store_run_metadata(run)
        
        # Track parameter changes
        if parent_run_id:
            self._track_parameter_changes(run_id, parent_run_id, parameters)
        
        # Execute simulation
        output_path = self._execute_simulation(run, config_path, duration_days)
        
        # Calculate results
        data_hash = self._calculate_data_hash(output_path)
        kpi_summary = self._calculate_kpis(output_path)
        
        # Update metadata
        run.finished_at = datetime.now()
        run.output_path = str(output_path)
        run.data_hash = data_hash
        run.kpi_summary = kpi_summary
        run.status = "completed"
        
        self._update_run_metadata(run)
        self._update_sync_health(run)
        
        return run
    
    def _execute_simulation(
        self,
        run: SimulationRun,
        config_path: Path,
        duration_days: int
    ) -> Path:
        """
        Execute the actual simulation using the data generator
        
        Args:
            run: SimulationRun metadata
            config_path: Path to configuration file
            duration_days: Duration in days
            
        Returns:
            Path to output data file
        """
        # Create output path
        output_dir = Path(f"twin/simulation_outputs")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{run.run_id}.csv"
        
        # Build command
        cmd = [
            "python",
            str(self.generator_path),
            "--config", str(config_path),
            "--output", str(output_path),
            "--seed", str(run.seed),
            "--days", str(duration_days)
        ]
        
        # Execute generator
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Log output if verbose
            if result.stdout:
                print(f"Generator output: {result.stdout}")
                
        except subprocess.CalledProcessError as e:
            print(f"Simulation failed: {e.stderr}")
            run.status = "failed"
            run.notes = f"{run.notes}\nError: {e.stderr}" if run.notes else f"Error: {e.stderr}"
            self._update_run_metadata(run)
            raise
        
        return output_path
    
    def _calculate_data_hash(self, data_path: Path) -> str:
        """Calculate SHA256 hash of output data for integrity"""
        sha256_hash = hashlib.sha256()
        with open(data_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _calculate_kpis(self, data_path: Path) -> Dict[str, float]:
        """
        Calculate KPI summary from simulation output
        
        Args:
            data_path: Path to simulation output CSV
            
        Returns:
            Dictionary of KPI values
        """
        import pandas as pd
        
        # Load simulation data
        df = pd.read_csv(data_path)
        
        # Calculate aggregate KPIs
        kpis = {}
        
        # OEE metrics
        if 'oee_score' in df.columns:
            kpis['mean_oee'] = df['oee_score'].mean()
            kpis['p95_oee'] = df['oee_score'].quantile(0.95)
            kpis['min_oee'] = df['oee_score'].min()
        
        # Availability
        if 'availability_score' in df.columns:
            kpis['mean_availability'] = df['availability_score'].mean()
        
        # Performance
        if 'performance_score' in df.columns:
            kpis['mean_performance'] = df['performance_score'].mean()
        
        # Quality
        if 'quality_score' in df.columns:
            kpis['mean_quality'] = df['quality_score'].mean()
            
        # Production metrics
        if 'good_units_produced' in df.columns:
            kpis['total_good_units'] = df['good_units_produced'].sum()
            
        if 'scrap_units_produced' in df.columns:
            kpis['total_scrap_units'] = df['scrap_units_produced'].sum()
            kpis['scrap_rate'] = (
                kpis['total_scrap_units'] / 
                (kpis.get('total_good_units', 0) + kpis['total_scrap_units'])
                if (kpis.get('total_good_units', 0) + kpis['total_scrap_units']) > 0
                else 0
            )
        
        # Downtime analysis
        if 'machine_status' in df.columns:
            downtime_pct = (df['machine_status'] == 'Stopped').mean() * 100
            kpis['downtime_percentage'] = downtime_pct
        
        return kpis
    
    def _store_run_metadata(self, run: SimulationRun):
        """Store run metadata in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO twin_runs 
                (run_id, run_type, seed, generator_version, parent_run_id,
                 started_at, finished_at, config_delta_json, data_hash,
                 output_path, kpi_summary_json, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.run_id, run.run_type, run.seed, run.generator_version,
                run.parent_run_id, run.started_at, run.finished_at,
                json.dumps(run.config_delta), run.data_hash,
                run.output_path, json.dumps(run.kpi_summary) if run.kpi_summary else None,
                run.notes, run.status
            ))
            conn.commit()
    
    def _update_run_metadata(self, run: SimulationRun):
        """Update run metadata in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE twin_runs 
                SET finished_at = ?, data_hash = ?, output_path = ?,
                    kpi_summary_json = ?, notes = ?, status = ?
                WHERE run_id = ?
            """, (
                run.finished_at, run.data_hash, run.output_path,
                json.dumps(run.kpi_summary) if run.kpi_summary else None,
                run.notes, run.status, run.run_id
            ))
            conn.commit()
    
    def _get_run_metadata(self, run_id: str) -> SimulationRun:
        """Retrieve run metadata from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM twin_runs WHERE run_id = ?",
                (run_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"Run {run_id} not found")
            
            return SimulationRun(
                run_id=row[0],
                run_type=row[1],
                seed=row[2],
                generator_version=row[3],
                parent_run_id=row[4],
                started_at=datetime.fromisoformat(row[5]),
                finished_at=datetime.fromisoformat(row[6]) if row[6] else None,
                config_delta=json.loads(row[7]),
                data_hash=row[8],
                output_path=row[9],
                kpi_summary=json.loads(row[10]) if row[10] else None,
                notes=row[11],
                status=row[12]
            )
    
    def _track_parameter_changes(
        self,
        run_id: str,
        parent_run_id: str,
        parameters: ActionableParameters
    ):
        """Track parameter changes between runs"""
        parent = self._get_run_metadata(parent_run_id)
        parent_params = parent.config_delta
        current_params = parameters.get_all_values()
        
        with sqlite3.connect(self.db_path) as conn:
            for param_name, new_value in current_params.items():
                old_value = parent_params.get(param_name)
                if old_value != new_value:
                    conn.execute("""
                        INSERT INTO parameter_history 
                        (run_id, parameter_name, old_value, new_value, change_reason)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        run_id, param_name, old_value, new_value,
                        f"Changed from parent run {parent_run_id}"
                    ))
            conn.commit()
    
    def _update_sync_health(self, run: SimulationRun):
        """Update synchronization health for all entities"""
        # Update sync metadata for equipment
        for line in range(1, 4):
            for equipment in ["FIL", "PCK", "PAL"]:
                entity_id = f"LINE{line}-{equipment}"
                self.sync_monitor.update_sync_metadata(
                    entity_id=entity_id,
                    entity_type="Equipment",
                    data={"run_id": run.run_id, "kpis": run.kpi_summary},
                    source_run_id=run.run_id,
                    sync_interval_minutes=5
                )
    
    def get_run_lineage(self, run_id: str) -> List[SimulationRun]:
        """
        Get complete lineage of a run (ancestors and descendants)
        
        Args:
            run_id: Run ID to trace
            
        Returns:
            List of related runs in chronological order
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get ancestors (recursive CTE)
            ancestors = conn.execute("""
                WITH RECURSIVE lineage AS (
                    SELECT * FROM twin_runs WHERE run_id = ?
                    UNION ALL
                    SELECT t.* FROM twin_runs t
                    JOIN lineage l ON t.run_id = l.parent_run_id
                )
                SELECT * FROM lineage ORDER BY started_at
            """, (run_id,)).fetchall()
            
            # Get descendants
            descendants = conn.execute("""
                WITH RECURSIVE lineage AS (
                    SELECT * FROM twin_runs WHERE run_id = ?
                    UNION ALL
                    SELECT t.* FROM twin_runs t
                    JOIN lineage l ON t.parent_run_id = l.run_id
                )
                SELECT * FROM lineage WHERE run_id != ? ORDER BY started_at
            """, (run_id, run_id)).fetchall()
            
            # Convert to SimulationRun objects
            all_runs = []
            for row in ancestors + descendants:
                all_runs.append(SimulationRun(
                    run_id=row[0],
                    run_type=row[1],
                    seed=row[2],
                    generator_version=row[3],
                    parent_run_id=row[4],
                    started_at=datetime.fromisoformat(row[5]),
                    finished_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    config_delta=json.loads(row[7]),
                    data_hash=row[8],
                    output_path=row[9],
                    kpi_summary=json.loads(row[10]) if row[10] else None,
                    notes=row[11],
                    status=row[12]
                ))
            
            return all_runs
    
    def compare_runs(
        self,
        run_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple simulation runs
        
        Args:
            run_ids: List of run IDs to compare
            
        Returns:
            Comparison dictionary with KPIs and parameters
        """
        comparison = {
            "runs": {},
            "kpi_comparison": {},
            "parameter_comparison": {},
            "improvements": {}
        }
        
        baseline_kpis = None
        baseline_params = None
        
        for run_id in run_ids:
            run = self._get_run_metadata(run_id)
            comparison["runs"][run_id] = {
                "type": run.run_type,
                "seed": run.seed,
                "status": run.status,
                "kpis": run.kpi_summary,
                "parameters": run.config_delta
            }
            
            # Track first run as baseline
            if baseline_kpis is None:
                baseline_kpis = run.kpi_summary or {}
                baseline_params = run.config_delta
                baseline_id = run_id
            else:
                # Calculate improvements
                if run.kpi_summary:
                    for kpi, value in run.kpi_summary.items():
                        if kpi in baseline_kpis:
                            baseline_val = baseline_kpis[kpi]
                            if baseline_val != 0:
                                improvement = ((value - baseline_val) / baseline_val) * 100
                                comparison["improvements"][f"{run_id}_vs_{baseline_id}_{kpi}"] = improvement
        
        # Aggregate KPI comparison
        for run_id, run_data in comparison["runs"].items():
            if run_data["kpis"]:
                for kpi, value in run_data["kpis"].items():
                    if kpi not in comparison["kpi_comparison"]:
                        comparison["kpi_comparison"][kpi] = {}
                    comparison["kpi_comparison"][kpi][run_id] = value
        
        # Parameter differences
        for run_id, run_data in comparison["runs"].items():
            for param, value in run_data["parameters"].items():
                if param not in comparison["parameter_comparison"]:
                    comparison["parameter_comparison"][param] = {}
                comparison["parameter_comparison"][param][run_id] = value
        
        return comparison


def demonstrate_simulation_runner():
    """Demonstrate simulation runner with provenance"""
    print("SIMULATION RUNNER DEMONSTRATION")
    print("=" * 60)
    
    runner = SimulationRunner()
    
    # Note: This is a demonstration - actual execution would require
    # the mes_data_generation.py script to accept these parameters
    
    print("\n1. CREATING BASELINE RUN")
    print("-" * 40)
    
    # Create baseline (would execute if generator was set up)
    baseline = SimulationRun(
        run_id="baseline-demo-001",
        run_type="baseline",
        seed=42,
        generator_version="1.0.0",
        parent_run_id=None,
        started_at=datetime.now(),
        finished_at=datetime.now(),
        config_delta=ActionableParameters().get_all_values(),
        data_hash="abc123def456",
        output_path="twin/simulation_outputs/baseline-demo-001.csv",
        kpi_summary={
            "mean_oee": 0.65,
            "mean_availability": 0.80,
            "mean_performance": 0.85,
            "mean_quality": 0.95
        },
        notes="Demo baseline run",
        status="completed"
    )
    
    runner._store_run_metadata(baseline)
    print(f"✓ Created baseline run: {baseline.run_id}")
    print(f"  OEE: {baseline.kpi_summary['mean_oee']:.2%}")
    
    print("\n2. RUNNING IMPROVED MAINTENANCE SIMULATION")
    print("-" * 40)
    
    # Create improved parameters
    params = ActionableParameters()
    params.set_value("micro_stop_probability", 0.10)
    params.set_value("performance_factor", 0.90)
    
    # Create simulation run
    sim_run = SimulationRun(
        run_id="sim-demo-001",
        run_type="simulation",
        seed=43,
        generator_version="1.0.0",
        parent_run_id="baseline-demo-001",
        started_at=datetime.now(),
        finished_at=datetime.now(),
        config_delta=params.get_all_values(),
        data_hash="def789ghi012",
        output_path="twin/simulation_outputs/sim-demo-001.csv",
        kpi_summary={
            "mean_oee": 0.72,
            "mean_availability": 0.85,
            "mean_performance": 0.90,
            "mean_quality": 0.95
        },
        notes="Improved maintenance scenario",
        status="completed"
    )
    
    runner._store_run_metadata(sim_run)
    runner._track_parameter_changes(sim_run.run_id, baseline.run_id, params)
    
    print(f"✓ Created simulation run: {sim_run.run_id}")
    print(f"  OEE: {sim_run.kpi_summary['mean_oee']:.2%}")
    print(f"  Improvement: +{(sim_run.kpi_summary['mean_oee'] - baseline.kpi_summary['mean_oee'])*100:.1f}%")
    
    print("\n3. COMPARING RUNS")
    print("-" * 40)
    
    comparison = runner.compare_runs([baseline.run_id, sim_run.run_id])
    
    print("KPI Comparison:")
    for kpi, values in comparison["kpi_comparison"].items():
        print(f"  {kpi}:")
        for run_id, value in values.items():
            print(f"    {run_id}: {value:.3f}")
    
    print("\nParameter Changes:")
    for param, values in comparison["parameter_comparison"].items():
        unique_values = set(values.values())
        if len(unique_values) > 1:
            print(f"  {param}: {dict(values)}")
    
    print("\n4. PROVENANCE TRACKING")
    print("-" * 40)
    
    # Show lineage
    lineage = runner.get_run_lineage(sim_run.run_id)
    print(f"Run lineage for {sim_run.run_id}:")
    for run in lineage:
        print(f"  → {run.run_id} (type: {run.run_type}, parent: {run.parent_run_id})")
    
    print("\n✅ Simulation runner with full provenance demonstrated!")


if __name__ == "__main__":
    demonstrate_simulation_runner()