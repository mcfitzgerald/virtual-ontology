"""Simulation Runner with Provenance Tracking and Monte Carlo Support
Manages simulation runs with complete reproducibility, provenance, and uncertainty analysis
"""

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
import subprocess
import tempfile
import numpy as np
import pandas as pd
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import from same package
from .actionable_parameters import ActionableParameters
from .config_transformer import ConfigTransformer
from .sync_health import SyncHealthMonitor
from .config_manager import ConfigurationManager


@dataclass
class SimulationRun:
    """Metadata for a simulation run with full provenance.
    
    Attributes:
        run_id: Unique identifier for this simulation run
        run_type: Type of run (baseline, simulation, recommendation, optimization)
        seed: Random seed used for reproducibility
        generator_version: Version of the data generator used
        parent_run_id: Optional ID of the parent run for lineage tracking
        started_at: Timestamp when the simulation started
        finished_at: Timestamp when the simulation completed (None if still running)
        config_delta: Dictionary of parameter changes from baseline
        data_hash: Hash of the generated data for verification
        output_path: Path to the output data file
        kpi_summary: Summary of KPI results (OEE, availability, etc.)
        notes: Optional description or notes about the run
        status: Current status (pending, running, completed, failed)
    
    Example:
        >>> run = SimulationRun(
        ...     run_id="sim-20240101-120000-abc123",
        ...     run_type="simulation",
        ...     seed=42,
        ...     generator_version="1.0.0",
        ...     parent_run_id=None,
        ...     started_at=datetime.now(),
        ...     finished_at=None,
        ...     config_delta={"micro_stop_probability": 0.05},
        ...     data_hash=None,
        ...     output_path=None,
        ...     kpi_summary=None,
        ...     notes="Testing reduced micro-stops",
        ...     status="running"
        ... )

    """

    run_id: str
    run_type: str  # baseline, simulation, recommendation, optimization
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
    """Manages virtual twin simulations with complete provenance tracking.
    Ensures reproducibility and traceability of all simulation runs.
    
    This class provides methods to:
    - Run what-if scenario simulations
    - Create baseline simulations
    - Run Monte Carlo uncertainty analysis
    - Compare simulation results
    - Track simulation lineage
    
    Example:
        >>> runner = SimulationRunner(verbose=False)
        >>> params = ActionableParameters()
        >>> params.set_value("micro_stop_probability", 0.05)
        >>> result = runner.run_simulation(params, duration_days=7)
        >>> print(f"OEE: {result.kpi_summary['mean_oee']:.1f}%")

    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        generator_path: Optional[str] = None,
        generator_version: Optional[str] = None,
        verbose: bool = False
    ) -> None:
        """Initialize the SimulationRunner.
        Configuration is required - will raise error if not available.
        
        Args:
            db_path: Path to the SQLite database file (uses config if None)
            generator_path: Path to the MES data generation script (uses config if None)
            generator_version: Version identifier for the generator (uses config if None)
            verbose: If True, print progress messages; if False, run quietly
        
        Raises:
            RuntimeError: If configuration is not available
            FileNotFoundError: If generator_path does not exist
            sqlite3.Error: If database connection fails

        """
        # Always load from config - no fallbacks
        from .config_loader import get_config
        self.config = get_config()  # Will raise error if config not available
        
        # Get required values from config
        self.db_path: str = db_path if db_path is not None else self.config.get("database.path")
        # Generator is now internal to twin module
        self.generator_path: Path = Path(__file__).parent / "generator.py"
        self.generator_version: str = generator_version if generator_version is not None else self.config.get("simulation.generator_version")
        
        # Validate required config values exist
        if not self.db_path:
            raise ValueError("Database path not provided and not found in configuration")
        if not self.generator_path:
            raise ValueError("Generator path not provided and not found in configuration")
        if not self.generator_version:
            raise ValueError("Generator version not provided and not found in configuration")
            
        self.verbose: bool = verbose
        self.sync_monitor: SyncHealthMonitor = SyncHealthMonitor(self.db_path)
        self.config_manager: ConfigurationManager = ConfigurationManager(self.db_path)
        
        # Initialize provenance database
        self._init_provenance_db()
        
    def _init_provenance_db(self) -> None:
        """Initialize provenance tracking tables in the database.
        
        Creates tables for:
        - twin_runs: Simulation run metadata
        - kpi_results: KPI calculation results
        - simulation_data: Time-series simulation data
        """
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
                    confidence REAL,
                    PRIMARY KEY (run_id, entity_id, kpi, window_start)
                )
            """)
            
            # Simulation data table for generated records
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simulation_data (
                    run_id TEXT REFERENCES twin_runs(run_id),
                    timestamp TIMESTAMP NOT NULL,
                    line_id TEXT NOT NULL,
                    equipment_id TEXT NOT NULL,
                    equipment_type TEXT NOT NULL,
                    product_id TEXT,
                    machine_status TEXT NOT NULL,
                    downtime_reason TEXT,
                    good_units_produced INTEGER,
                    scrap_units_produced INTEGER,
                    target_rate_units_per_5min INTEGER,
                    availability_score REAL,
                    performance_score REAL,
                    quality_score REAL,
                    oee_score REAL,
                    energy_consumption_kwh REAL,
                    PRIMARY KEY (run_id, timestamp, equipment_id)
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_twin_runs_status ON twin_runs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_twin_runs_parent ON twin_runs(parent_run_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_kpi_results_run ON kpi_results(run_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_simulation_data_run ON simulation_data(run_id)")
            
    def run_simulation(
        self,
        parameters: ActionableParameters,
        parent_run_id: Optional[str] = None,
        seed: Optional[int] = None,
        duration_days: int = 7,
        notes: Optional[str] = None
    ) -> SimulationRun:
        """Run a simulation with specific parameters.
        
        Args:
            parameters: ActionableParameters instance with values to test
            parent_run_id: Optional parent run for lineage tracking
            seed: Random seed for reproducibility (uses parent seed + 1 if not provided)
            duration_days: Simulation duration in days (1-30)
            notes: Optional description or notes about this run
            
        Returns:
            SimulationRun object containing:
            - run_id: Unique identifier
            - kpi_summary: Dict with KPIs (mean_oee, availability, etc.) as percentages (0-100)
            - status: 'completed' or 'failed'
            - Other metadata fields
            
        Raises:
            ValueError: If duration_days is outside valid range (1-30)
            RuntimeError: If simulation execution fails
            
        Example:
            >>> runner = SimulationRunner()
            >>> params = ActionableParameters()
            >>> params.set_value("micro_stop_probability", 0.05)
            >>> result = runner.run_simulation(params, duration_days=7)
            >>> print(f"Mean OEE: {result.kpi_summary['mean_oee']:.1f}%")
            >>> print(f"Downtime: {result.kpi_summary['downtime_percentage']:.1f}%")

        """
        # Validate duration
        min_days = self.config.get("simulation.duration_limits.min")
        max_days = self.config.get("simulation.duration_limits.max")
        if not min_days <= duration_days <= max_days:
            raise ValueError(f"duration_days must be between {min_days} and {max_days}, got {duration_days}")
            
        # Generate run ID
        run_id = f"sim-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # Determine seed
        if seed is None and parent_run_id:
            parent = self._get_run_metadata(parent_run_id)
            seed = parent.seed + 1
        elif seed is None:
            seed_min = self.config.get("simulation.seed_range.min")
            seed_max = self.config.get("simulation.seed_range.max")
            seed = np.random.randint(seed_min, seed_max)
        
        # Transform parameters to config
        transformer = ConfigTransformer()
        config = transformer.apply_parameters(parameters)
        
        # Store config in database instead of file
        # The config_manager will handle deduplication via hashing
        config_id = self.config_manager.store_config(
            run_id=run_id,
            config=config,
            config_type="generator",
            description=f"Simulation config with parameters: {parameters.get_all_values()}"
        )
        
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
        if self.verbose:
            print(f"Starting simulation {run_id} with seed {seed}")
            
        try:
            result = self._execute_simulation(
                run_id=run_id,
                config_id=config_id,
                seed=seed,
                duration_days=duration_days
            )
            
            # Parse results
            kpi_summary = self._calculate_kpis(result['data'])
            
            # Update run with results
            run.finished_at = datetime.now()
            run.kpi_summary = kpi_summary
            run.data_hash = result['hash']
            run.output_path = result.get('output_path')
            run.status = "completed"
            
            # Store results
            self._update_run_metadata(run)
            # Data is already stored in database by the generator script
            # self._store_simulation_data(run_id, result['data'])
            
            if self.verbose:
                print(f"Simulation completed: OEE={kpi_summary['mean_oee']:.1f}%")
                
        except Exception as e:
            # Mark as failed
            run.finished_at = datetime.now()
            run.status = "failed"
            run.notes = f"{run.notes}\nError: {str(e)}" if run.notes else f"Error: {str(e)}"
            self._update_run_metadata(run)
            raise RuntimeError(f"Simulation failed: {str(e)}")
            
        return run
        
    def create_baseline(
        self,
        seed: int = 42,
        duration_days: int = 7,
        notes: Optional[str] = None
    ) -> SimulationRun:
        """Create a baseline simulation with default parameters.
        
        Args:
            seed: Random seed for reproducibility
            duration_days: Simulation duration in days (1-30)
            notes: Optional description
            
        Returns:
            SimulationRun object with baseline results
            
        Example:
            >>> runner = SimulationRunner()
            >>> baseline = runner.create_baseline(duration_days=14)
            >>> print(f"Baseline OEE: {baseline.kpi_summary['mean_oee']:.1f}%")

        """
        params = ActionableParameters()  # Use defaults
        run = self.run_simulation(
            parameters=params,
            seed=seed,
            duration_days=duration_days,
            notes=notes or "Baseline simulation with default parameters"
        )
        run.run_type = "baseline"
        self._update_run_metadata(run)
        return run
        
    def run_monte_carlo_simulation(
        self,
        parameters: ActionableParameters,
        uncertainty_ranges: Dict[str, Tuple[float, float]],
        n_simulations: int = 100,
        duration_days: int = 7,
        parent_run_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation with parameter uncertainty.
        
        Args:
            parameters: Base parameters
            uncertainty_ranges: Dict mapping parameter names to (min_delta, max_delta) tuples
            n_simulations: Number of Monte Carlo iterations
            duration_days: Duration for each simulation
            parent_run_id: Optional parent run for lineage
            notes: Optional description
            
        Returns:
            Dictionary containing:
            - 'results': List of SimulationRun objects
            - 'statistics': Summary statistics (mean, std, percentiles)
            - 'confidence_intervals': 95% CI for each KPI
            
        Example:
            >>> runner = SimulationRunner()
            >>> params = ActionableParameters()
            >>> uncertainty = {"micro_stop_probability": (-0.02, 0.02)}  # ±2%
            >>> mc_results = runner.run_monte_carlo_simulation(
            ...     params, uncertainty, n_simulations=50
            ... )
            >>> print(f"Mean OEE: {mc_results['statistics']['mean_oee']:.1f}%")
            >>> print(f"95% CI: {mc_results['confidence_intervals']['mean_oee']}")

        """
        results: List[SimulationRun] = []
        
        max_workers = self.config.get("simulation.max_workers")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            for i in range(n_simulations):
                # Sample parameters with uncertainty
                sampled_params = self._sample_parameters(parameters, uncertainty_ranges)
                
                # Submit simulation
                future = executor.submit(
                    self.run_simulation,
                    sampled_params,
                    parent_run_id,
                    None,  # Random seed
                    duration_days,
                    f"MC iteration {i+1}/{n_simulations}"
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    if self.verbose:
                        print(f"MC iteration failed: {e}")
        
        # Calculate statistics
        statistics = self._calculate_mc_statistics(results)
        confidence_intervals = self._calculate_confidence_intervals(results)
        
        return {
            'results': results,
            'statistics': statistics,
            'confidence_intervals': confidence_intervals,
            'n_successful': len(results),
            'n_failed': n_simulations - len(results)
        }
        
    def compare_runs(
        self,
        run_ids: List[str]
    ) -> Dict[str, Any]:
        """Compare multiple simulation runs.
        
        Args:
            run_ids: List of run IDs to compare
            
        Returns:
            Dictionary containing:
            - 'runs': List of SimulationRun objects
            - 'kpi_comparison': DataFrame comparing KPIs
            - 'parameter_differences': Dict of parameter variations
            
        Example:
            >>> comparison = runner.compare_runs(["sim-001", "sim-002", "sim-003"])
            >>> print(comparison['kpi_comparison'])

        """
        runs = [self._get_run_metadata(run_id) for run_id in run_ids]
        
        # Create KPI comparison DataFrame
        kpi_data = []
        for run in runs:
            if run.kpi_summary:
                kpi_data.append({
                    'run_id': run.run_id,
                    'run_type': run.run_type,
                    **run.kpi_summary
                })
        
        kpi_comparison = pd.DataFrame(kpi_data) if kpi_data else pd.DataFrame()
        
        # Find parameter differences
        param_differences = self._find_parameter_differences(runs)
        
        return {
            'runs': runs,
            'kpi_comparison': kpi_comparison,
            'parameter_differences': param_differences
        }
        
    def get_run_lineage(
        self,
        run_id: str
    ) -> List[SimulationRun]:
        """Get complete lineage (ancestors and descendants) of a run.
        
        Args:
            run_id: Run ID to trace lineage for
            
        Returns:
            List of SimulationRun objects in chronological order
            
        Example:
            >>> lineage = runner.get_run_lineage("sim-20240101-120000-abc123")
            >>> for run in lineage:
            ...     print(f"{run.run_id}: {run.run_type}")

        """
        lineage = []
        
        # Get ancestors
        current_id = run_id
        while current_id:
            run = self._get_run_metadata(current_id)
            lineage.insert(0, run)  # Add to beginning
            current_id = run.parent_run_id
        
        # Get descendants
        descendants = self._get_descendants(run_id)
        lineage.extend(descendants)
        
        return lineage
        
    # Private helper methods
    def _execute_simulation(
        self,
        run_id: str,
        config_id: str,
        seed: int,
        duration_days: int
    ) -> Dict[str, Any]:
        """Execute the simulation subprocess and return results."""
        try:
            # Retrieve config from database
            config = self.config_manager.get_config(config_id)
            if not config:
                raise ValueError(f"Config {config_id} not found in database")
            
            # Write config to a temporary file for the generator
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(config, f, indent=2)
                temp_config_path = f.name
            
            # Build command to write directly to database
            cmd = [
                sys.executable,
                str(self.generator_path),
                '--config', temp_config_path,
                '--output', 'db',
                '--table', 'simulation_data',
                '--run-id', run_id,
                '--start-date', self.config.get("simulation.default_start_date"),
                '--end-date', f'2025-06-{duration_days:02d}',
                '--seed', str(seed)
            ]
            
            # Execute
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
            finally:
                # Clean up temporary config file
                import os
                if 'temp_config_path' in locals():
                    try:
                        os.remove(temp_config_path)
                    except:
                        pass  # Ignore cleanup errors
            
            # Load generated data from database
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(
                    f"SELECT * FROM simulation_data WHERE run_id = '{run_id}'",
                    conn
                )
            
            # Calculate hash
            data_hash = hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()
            
            return {
                'data': df,
                'hash': data_hash,
                'output_path': None  # No file path since we're using database
            }
            
        except subprocess.CalledProcessError as e:
            # Clean up temp file on error
            if 'temp_config_path' in locals():
                try:
                    os.remove(temp_config_path)
                except:
                    pass
            raise RuntimeError(f"Simulation subprocess failed: {e.stderr}")
                
    def _calculate_kpis(
        self,
        data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate KPI summary from simulation data.
        
        Returns KPIs as percentages (0-100), not fractions.
        """
        running_data = data[data['machine_status'] == 'Running']
        
        if running_data.empty:
            return {
                'mean_oee': 0.0,
                'p95_oee': 0.0,
                'min_oee': 0.0,
                'mean_availability': 0.0,
                'mean_performance': 0.0,
                'mean_quality': 0.0,
                'total_good_units': 0,
                'total_scrap_units': 0,
                'scrap_rate': 0.0,
                'downtime_percentage': 100.0
            }
        
        # Calculate KPIs (already in percentage form in data)
        kpis = {
            'mean_oee': float(running_data['oee_score'].mean()),
            'p95_oee': float(running_data['oee_score'].quantile(0.95)),
            'min_oee': float(running_data['oee_score'].min()),
            'mean_availability': float(running_data['availability_score'].mean()),
            'mean_performance': float(running_data['performance_score'].mean()),
            'mean_quality': float(running_data['quality_score'].mean()),
            'total_good_units': int(data['good_units_produced'].sum()),
            'total_scrap_units': int(data['scrap_units_produced'].sum()),
            'scrap_rate': float(data['scrap_units_produced'].sum() / 
                               (data['good_units_produced'].sum() + data['scrap_units_produced'].sum())
                               if (data['good_units_produced'].sum() + data['scrap_units_produced'].sum()) > 0 else 0),
            'downtime_percentage': float((len(data[data['machine_status'] == 'Stopped']) / len(data)) * 100)
        }
        
        return kpis
        
    def _store_run_metadata(
        self,
        run: SimulationRun
    ) -> None:
        """Store simulation run metadata to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO twin_runs (
                    run_id, run_type, seed, generator_version, parent_run_id,
                    started_at, finished_at, config_delta_json, data_hash,
                    output_path, kpi_summary_json, notes, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.run_id, run.run_type, run.seed, run.generator_version,
                run.parent_run_id, run.started_at, run.finished_at,
                json.dumps(run.config_delta), run.data_hash, run.output_path,
                json.dumps(run.kpi_summary) if run.kpi_summary else None,
                run.notes, run.status
            ))
            
    def _update_run_metadata(
        self,
        run: SimulationRun
    ) -> None:
        """Update existing run metadata in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE twin_runs SET
                    run_type = ?, finished_at = ?, data_hash = ?,
                    output_path = ?, kpi_summary_json = ?, notes = ?, status = ?
                WHERE run_id = ?
            """, (
                run.run_type, run.finished_at, run.data_hash, run.output_path,
                json.dumps(run.kpi_summary) if run.kpi_summary else None,
                run.notes, run.status, run.run_id
            ))
            
    def _get_run_metadata(
        self,
        run_id: str
    ) -> SimulationRun:
        """Retrieve run metadata from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM twin_runs WHERE run_id = ?
            """, (run_id,))
            
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Run {run_id} not found")
            
            # Convert row to dict
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            
            # Parse JSON fields
            return SimulationRun(
                run_id=data['run_id'],
                run_type=data['run_type'],
                seed=data['seed'],
                generator_version=data['generator_version'],
                parent_run_id=data['parent_run_id'],
                started_at=datetime.fromisoformat(data['started_at']),
                finished_at=datetime.fromisoformat(data['finished_at']) if data['finished_at'] else None,
                config_delta=json.loads(data['config_delta_json']),
                data_hash=data['data_hash'],
                output_path=data['output_path'],
                kpi_summary=json.loads(data['kpi_summary_json']) if data['kpi_summary_json'] else None,
                notes=data['notes'],
                status=data['status']
            )
            
    def _store_simulation_data(
        self,
        run_id: str,
        data: pd.DataFrame
    ) -> None:
        """Store simulation data to database."""
        # Add run_id column
        data['run_id'] = run_id
        
        # Store to database
        with sqlite3.connect(self.db_path) as conn:
            data.to_sql('simulation_data', conn, if_exists='append', index=False)
            
    def _track_parameter_changes(
        self,
        run_id: str,
        parent_run_id: str,
        parameters: ActionableParameters
    ) -> None:
        """Track parameter changes between runs."""
        # This would store parameter history for tracking changes
        pass
        
    def _sample_parameters(
        self,
        base_params: ActionableParameters,
        uncertainty_ranges: Dict[str, Tuple[float, float]]
    ) -> ActionableParameters:
        """Sample parameters with uncertainty for Monte Carlo."""
        sampled = ActionableParameters()
        
        for param_name in base_params.parameters:
            base_value = base_params.get_value(param_name)
            
            if param_name in uncertainty_ranges:
                min_delta, max_delta = uncertainty_ranges[param_name]
                delta = np.random.uniform(min_delta, max_delta)
                new_value = base_value + delta
                
                # Ensure within bounds
                param = base_params.parameters[param_name]
                new_value = max(param.bounds[0], min(param.bounds[1], new_value))
                sampled.set_value(param_name, new_value)
            else:
                sampled.set_value(param_name, base_value)
                
        return sampled
        
    def _calculate_mc_statistics(
        self,
        results: List[SimulationRun]
    ) -> Dict[str, float]:
        """Calculate statistics from Monte Carlo results."""
        kpi_values = {}
        
        for result in results:
            if result.kpi_summary:
                for kpi, value in result.kpi_summary.items():
                    if kpi not in kpi_values:
                        kpi_values[kpi] = []
                    kpi_values[kpi].append(value)
        
        statistics = {}
        for kpi, values in kpi_values.items():
            arr = np.array(values)
            statistics[f'{kpi}_mean'] = float(np.mean(arr))
            statistics[f'{kpi}_std'] = float(np.std(arr))
            statistics[f'{kpi}_min'] = float(np.min(arr))
            statistics[f'{kpi}_max'] = float(np.max(arr))
            statistics[f'{kpi}_p25'] = float(np.percentile(arr, 25))
            statistics[f'{kpi}_p50'] = float(np.percentile(arr, 50))
            statistics[f'{kpi}_p75'] = float(np.percentile(arr, 75))
            
        return statistics
        
    def _calculate_confidence_intervals(
        self,
        results: List[SimulationRun],
        confidence: float = 0.95
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for KPIs."""
        kpi_values = {}
        
        for result in results:
            if result.kpi_summary:
                for kpi, value in result.kpi_summary.items():
                    if kpi not in kpi_values:
                        kpi_values[kpi] = []
                    kpi_values[kpi].append(value)
        
        intervals = {}
        alpha = 1 - confidence
        for kpi, values in kpi_values.items():
            arr = np.array(values)
            lower = float(np.percentile(arr, alpha/2 * 100))
            upper = float(np.percentile(arr, (1 - alpha/2) * 100))
            intervals[kpi] = (lower, upper)
            
        return intervals
        
    def _find_parameter_differences(
        self,
        runs: List[SimulationRun]
    ) -> Dict[str, List[float]]:
        """Find parameter variations across runs."""
        param_values = {}
        
        for run in runs:
            for param, value in run.config_delta.items():
                if param not in param_values:
                    param_values[param] = []
                param_values[param].append(value)
                
        return param_values
        
    def _get_descendants(
        self,
        run_id: str
    ) -> List[SimulationRun]:
        """Get all descendant runs."""
        descendants = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT run_id FROM twin_runs WHERE parent_run_id = ?
            """, (run_id,))
            
            child_ids = [row[0] for row in cursor.fetchall()]
            
        for child_id in child_ids:
            child = self._get_run_metadata(child_id)
            descendants.append(child)
            # Recursively get descendants
            descendants.extend(self._get_descendants(child_id))
            
        return descendants