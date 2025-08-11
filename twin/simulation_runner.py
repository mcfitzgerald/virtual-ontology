"""
Simulation Runner with Provenance Tracking and Monte Carlo Support
Manages simulation runs with complete reproducibility, provenance, and uncertainty analysis
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
import pandas as pd
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add twin directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from actionable_parameters import ActionableParameters
from config_transformer import ConfigTransformer
from sync_health import SyncHealthMonitor
from config_manager import ConfigurationManager


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
        self.config_manager = ConfigurationManager(db_path)
        
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
        
        # Save config - use absolute path
        config_dir = Path(__file__).parent / "configs"
        config_dir.mkdir(exist_ok=True)
        config_path = config_dir / f"{run_id}.json"
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
    ) -> str:
        """
        Execute the actual simulation using the data generator
        
        Args:
            run: SimulationRun metadata
            config_path: Path to configuration file
            duration_days: Duration in days
            
        Returns:
            Database table reference (simulation_data with run_id)
        """
        # Calculate end date
        from datetime import timedelta
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=duration_days)
        
        # Build command to write to database
        cmd = [
            "python",
            str(self.generator_path),
            "--config", str(config_path),  # Pass the custom config
            "--seed", str(run.seed),  # Pass the seed for reproducibility
            "--output", "db",
            "--table", "simulation_data",
            "--run-id", run.run_id,
            "--start-date", start_date.strftime("%Y-%m-%d"),
            "--end-date", end_date.strftime("%Y-%m-%d")
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
        
        return f"simulation_data:{run.run_id}"
    
    def _calculate_data_hash(self, data_ref: str) -> str:
        """Calculate SHA256 hash of output data for integrity"""
        if ":" in data_ref:
            table, run_id = data_ref.split(":")
            # Hash database records
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM simulation_data WHERE run_id = ? ORDER BY timestamp, equipment_id",
                    (run_id,)
                )
                sha256_hash = hashlib.sha256()
                for row in cursor:
                    row_str = str(row).encode()
                    sha256_hash.update(row_str)
                return sha256_hash.hexdigest()
        else:
            # Legacy path support
            sha256_hash = hashlib.sha256()
            with open(data_ref, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
    
    def _calculate_kpis(self, data_ref: str) -> Dict[str, float]:
        """
        Calculate KPI summary from simulation output
        
        Args:
            data_ref: Reference to data (database table:run_id or file path)
            
        Returns:
            Dictionary of KPI values
        """
        import pandas as pd
        from sqlalchemy import create_engine
        
        if ":" in data_ref:
            # Load from database
            table, run_id = data_ref.split(":")
            engine = create_engine(f"sqlite:///{self.db_path}")
            df = pd.read_sql_query(
                f"SELECT * FROM {table} WHERE run_id = '{run_id}'",
                engine
            )
        else:
            # Load from CSV (legacy)
            df = pd.read_csv(data_ref)
        
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
        
        # Convert numpy types to Python native types for JSON serialization
        import numpy as np
        for key, value in kpis.items():
            if isinstance(value, (np.integer, np.floating)):
                kpis[key] = value.item()  # Use .item() for proper conversion
        
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
    
    def run_monte_carlo_simulation(
        self,
        base_parameters: ActionableParameters,
        uncertainty_ranges: Dict[str, Tuple[float, float]],
        n_simulations: int = 100,
        duration_days: int = 7,
        parallel: bool = True,
        max_workers: int = 4,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulations with parameter uncertainty
        
        Args:
            base_parameters: Base parameter configuration
            uncertainty_ranges: Dict of parameter names to (min_pct, max_pct) variation
                               e.g., {"micro_stop_probability": (-0.1, 0.1)} for ±10%
            n_simulations: Number of Monte Carlo simulations to run
            duration_days: Duration of each simulation in days
            parallel: Whether to run simulations in parallel
            max_workers: Maximum number of parallel workers
            notes: Optional notes for the batch
            
        Returns:
            Dictionary with aggregated results and statistics
        """
        mc_batch_id = f"mc-batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # Generate parameter sets with uncertainty
        parameter_sets = self._generate_mc_parameter_sets(
            base_parameters,
            uncertainty_ranges,
            n_simulations
        )
        
        # Run simulations
        if parallel:
            results = self._run_parallel_simulations(
                parameter_sets,
                duration_days,
                mc_batch_id,
                max_workers
            )
        else:
            results = self._run_sequential_simulations(
                parameter_sets,
                duration_days,
                mc_batch_id
            )
        
        # Aggregate results
        mc_summary = self._aggregate_mc_results(results, mc_batch_id)
        
        # Store batch metadata
        self._store_mc_batch_metadata(
            mc_batch_id,
            base_parameters,
            uncertainty_ranges,
            n_simulations,
            mc_summary,
            notes
        )
        
        return mc_summary
    
    def _generate_mc_parameter_sets(
        self,
        base_parameters: ActionableParameters,
        uncertainty_ranges: Dict[str, Tuple[float, float]],
        n_simulations: int
    ) -> List[ActionableParameters]:
        """
        Generate parameter sets with uncertainty for Monte Carlo simulation
        
        Args:
            base_parameters: Base parameter configuration
            uncertainty_ranges: Uncertainty ranges for each parameter
            n_simulations: Number of parameter sets to generate
            
        Returns:
            List of ActionableParameters with varied values
        """
        np.random.seed(seed)  # Use provided seed for reproducibility
        parameter_sets = []
        
        for i in range(n_simulations):
            # Create copy of base parameters
            params = ActionableParameters()
            base_values = base_parameters.get_all_values()
            
            # Apply uncertainty to each parameter
            for param_name, base_value in base_values.items():
                if param_name in uncertainty_ranges:
                    min_pct, max_pct = uncertainty_ranges[param_name]
                    # Generate random variation within range
                    variation = np.random.uniform(min_pct, max_pct)
                    new_value = base_value * (1 + variation)
                    
                    # Ensure within parameter bounds
                    param_obj = params.parameters[param_name]
                    min_bound, max_bound = param_obj.bounds
                    new_value = np.clip(new_value, min_bound, max_bound)
                    
                    params.set_value(param_name, new_value)
                else:
                    params.set_value(param_name, base_value)
            
            parameter_sets.append(params)
        
        return parameter_sets
    
    def _run_parallel_simulations(
        self,
        parameter_sets: List[ActionableParameters],
        duration_days: int,
        batch_id: str,
        max_workers: int
    ) -> List[Dict[str, Any]]:
        """
        Run simulations in parallel using ThreadPoolExecutor
        
        Args:
            parameter_sets: List of parameter configurations
            duration_days: Duration of each simulation
            batch_id: Batch identifier
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of simulation results
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all simulations
            future_to_params = {
                executor.submit(
                    self.run_simulation,
                    parameters=params,
                    duration_days=duration_days,
                    notes=f"MC batch {batch_id}, simulation {i+1}/{len(parameter_sets)}"
                ): (i, params)
                for i, params in enumerate(parameter_sets)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_params):
                sim_index, params = future_to_params[future]
                try:
                    run_id = future.result()
                    run = self._get_run_metadata(run_id)
                    
                    results.append({
                        "simulation_index": sim_index,
                        "run_id": run_id,
                        "parameters": params.get_all_values(),
                        "kpis": run.kpi_summary,
                        "status": run.status
                    })
                except Exception as e:
                    print(f"Simulation {sim_index} failed: {e}")
                    results.append({
                        "simulation_index": sim_index,
                        "run_id": None,
                        "parameters": params.get_all_values(),
                        "kpis": None,
                        "status": "failed",
                        "error": str(e)
                    })
        
        return results
    
    def _run_sequential_simulations(
        self,
        parameter_sets: List[ActionableParameters],
        duration_days: int,
        batch_id: str
    ) -> List[Dict[str, Any]]:
        """
        Run simulations sequentially
        
        Args:
            parameter_sets: List of parameter configurations
            duration_days: Duration of each simulation
            batch_id: Batch identifier
            
        Returns:
            List of simulation results
        """
        results = []
        
        for i, params in enumerate(parameter_sets):
            try:
                run_id = self.run_simulation(
                    parameters=params,
                    duration_days=duration_days,
                    notes=f"MC batch {batch_id}, simulation {i+1}/{len(parameter_sets)}"
                )
                run = self._get_run_metadata(run_id)
                
                results.append({
                    "simulation_index": i,
                    "run_id": run_id,
                    "parameters": params.get_all_values(),
                    "kpis": run.kpi_summary,
                    "status": run.status
                })
            except Exception as e:
                print(f"Simulation {i} failed: {e}")
                results.append({
                    "simulation_index": i,
                    "run_id": None,
                    "parameters": params.get_all_values(),
                    "kpis": None,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def _aggregate_mc_results(
        self,
        results: List[Dict[str, Any]],
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Aggregate Monte Carlo simulation results
        
        Args:
            results: List of individual simulation results
            batch_id: Batch identifier
            
        Returns:
            Aggregated statistics and distributions
        """
        # Filter successful simulations
        successful_results = [r for r in results if r["status"] == "completed" and r["kpis"]]
        
        if not successful_results:
            return {
                "batch_id": batch_id,
                "n_simulations": len(results),
                "n_successful": 0,
                "error": "No successful simulations"
            }
        
        # Extract KPI data
        kpi_data = {}
        for result in successful_results:
            for kpi, value in result["kpis"].items():
                if kpi not in kpi_data:
                    kpi_data[kpi] = []
                kpi_data[kpi].append(value)
        
        # Calculate statistics for each KPI
        kpi_statistics = {}
        for kpi, values in kpi_data.items():
            values_array = np.array(values)
            kpi_statistics[kpi] = {
                "mean": float(np.mean(values_array)),
                "std": float(np.std(values_array)),
                "median": float(np.median(values_array)),
                "min": float(np.min(values_array)),
                "max": float(np.max(values_array)),
                "percentiles": {
                    "p5": float(np.percentile(values_array, 5)),
                    "p25": float(np.percentile(values_array, 25)),
                    "p50": float(np.percentile(values_array, 50)),
                    "p75": float(np.percentile(values_array, 75)),
                    "p95": float(np.percentile(values_array, 95))
                },
                "confidence_interval_95": (
                    float(np.percentile(values_array, 2.5)),
                    float(np.percentile(values_array, 97.5))
                ),
                "coefficient_of_variation": float(np.std(values_array) / np.mean(values_array)) if np.mean(values_array) != 0 else 0
            }
        
        # Parameter sensitivity analysis (simplified)
        parameter_sensitivity = self._calculate_parameter_sensitivity(successful_results)
        
        return {
            "batch_id": batch_id,
            "n_simulations": len(results),
            "n_successful": len(successful_results),
            "success_rate": len(successful_results) / len(results),
            "kpi_statistics": kpi_statistics,
            "parameter_sensitivity": parameter_sensitivity,
            "run_ids": [r["run_id"] for r in successful_results],
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_parameter_sensitivity(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate simplified parameter sensitivity using correlation
        
        Args:
            results: List of simulation results
            
        Returns:
            Parameter sensitivity metrics
        """
        if len(results) < 3:
            return {}
        
        # Create DataFrame for analysis
        param_data = pd.DataFrame([r["parameters"] for r in results])
        kpi_data = pd.DataFrame([r["kpis"] for r in results])
        
        sensitivity = {}
        
        # Calculate correlation between each parameter and KPI
        for param in param_data.columns:
            sensitivity[param] = {}
            for kpi in kpi_data.columns:
                try:
                    correlation = param_data[param].corr(kpi_data[kpi])
                    sensitivity[param][kpi] = float(correlation) if not pd.isna(correlation) else 0.0
                except:
                    sensitivity[param][kpi] = 0.0
        
        return sensitivity
    
    def _store_mc_batch_metadata(
        self,
        batch_id: str,
        base_parameters: ActionableParameters,
        uncertainty_ranges: Dict[str, Tuple[float, float]],
        n_simulations: int,
        summary: Dict[str, Any],
        notes: Optional[str]
    ):
        """
        Store Monte Carlo batch metadata in database
        
        Args:
            batch_id: Batch identifier
            base_parameters: Base parameter configuration
            uncertainty_ranges: Uncertainty ranges used
            n_simulations: Number of simulations
            summary: Aggregated results summary
            notes: Optional notes
        """
        with sqlite3.connect(self.db_path) as conn:
            # Create MC batch table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mc_batches (
                    batch_id TEXT PRIMARY KEY,
                    base_parameters_json TEXT NOT NULL,
                    uncertainty_ranges_json TEXT NOT NULL,
                    n_simulations INTEGER NOT NULL,
                    summary_json TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert batch metadata
            conn.execute("""
                INSERT INTO mc_batches (
                    batch_id, base_parameters_json, uncertainty_ranges_json,
                    n_simulations, summary_json, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                batch_id,
                json.dumps(base_parameters.get_all_values()),
                json.dumps(uncertainty_ranges),
                n_simulations,
                json.dumps(summary),
                notes
            ))
            
            conn.commit()


