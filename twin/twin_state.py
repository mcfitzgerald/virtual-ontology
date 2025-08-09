"""
Twin State Management
Manages the current state of the virtual twin and run ledger
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class TwinState:
    """Current state of the virtual twin"""
    current_run_id: str
    baseline_run_id: str
    last_update: datetime
    current_parameters: Dict[str, float]
    current_kpis: Dict[str, float]
    sync_status: Dict[str, str]  # entity_id -> health status
    active_recommendations: List[Dict[str, Any]]
    confidence_intervals: Dict[str, Tuple[float, float]]


class TwinStateManager:
    """
    Manages virtual twin state and provides high-level operations
    for querying, comparing, and optimizing the twin
    """
    
    def __init__(self, db_path: str = "data/mes_database.db"):
        self.db_path = db_path
        self._init_state_tables()
        
    def _init_state_tables(self):
        """Initialize state management tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Twin state table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS twin_state (
                    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    current_run_id TEXT REFERENCES twin_runs(run_id),
                    baseline_run_id TEXT REFERENCES twin_runs(run_id),
                    parameters_json TEXT NOT NULL,
                    kpis_json TEXT NOT NULL,
                    sync_status_json TEXT,
                    notes TEXT
                )
            """)
            
            # Recommendations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    run_id TEXT REFERENCES twin_runs(run_id),
                    recommendation_type TEXT,
                    parameters_json TEXT NOT NULL,
                    expected_improvement_json TEXT,
                    confidence REAL,
                    status TEXT CHECK(status IN ('pending', 'accepted', 'rejected', 'implemented')),
                    notes TEXT
                )
            """)
            
            # Confidence tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS confidence_tracking (
                    tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT REFERENCES twin_runs(run_id),
                    kpi TEXT NOT NULL,
                    mean_value REAL NOT NULL,
                    std_dev REAL NOT NULL,
                    lower_bound REAL NOT NULL,
                    upper_bound REAL NOT NULL,
                    n_samples INTEGER NOT NULL,
                    confidence_level REAL DEFAULT 0.95
                )
            """)
            
            conn.commit()
    
    def get_current_state(self) -> Optional[TwinState]:
        """Get the current state of the virtual twin"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM twin_state 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Get confidence intervals
            conf_cursor = conn.execute("""
                SELECT kpi, lower_bound, upper_bound 
                FROM confidence_tracking 
                WHERE run_id = ?
            """, (row[2],))  # current_run_id
            
            confidence_intervals = {
                r[0]: (r[1], r[2]) for r in conf_cursor.fetchall()
            }
            
            return TwinState(
                current_run_id=row[2],
                baseline_run_id=row[3],
                last_update=datetime.fromisoformat(row[1]),
                current_parameters=json.loads(row[4]),
                current_kpis=json.loads(row[5]),
                sync_status=json.loads(row[6]) if row[6] else {},
                active_recommendations=self._get_active_recommendations(),
                confidence_intervals=confidence_intervals
            )
    
    def update_state(
        self,
        run_id: str,
        baseline_run_id: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """
        Update the twin state based on a simulation run
        
        Args:
            run_id: Run ID to set as current state
            baseline_run_id: Optional baseline for comparison
            notes: Optional notes about the state change
        """
        # Get run data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM twin_runs WHERE run_id = ?",
                (run_id,)
            )
            run = cursor.fetchone()
            
            if not run:
                raise ValueError(f"Run {run_id} not found")
            
            # Extract data
            parameters = json.loads(run[7])  # config_delta_json
            kpis = json.loads(run[10]) if run[10] else {}  # kpi_summary_json
            
            # Get sync status
            sync_cursor = conn.execute("""
                SELECT entity_id, health_status 
                FROM sync_health_dashboard
            """)
            sync_status = {row[0]: row[1] for row in sync_cursor.fetchall()}
            
            # Use existing baseline if not provided
            if not baseline_run_id:
                current_state = self.get_current_state()
                baseline_run_id = current_state.baseline_run_id if current_state else run_id
            
            # Insert new state
            conn.execute("""
                INSERT INTO twin_state 
                (current_run_id, baseline_run_id, parameters_json, 
                 kpis_json, sync_status_json, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                run_id, baseline_run_id,
                json.dumps(parameters), json.dumps(kpis),
                json.dumps(sync_status), notes
            ))
            
            conn.commit()
    
    def calculate_confidence(
        self,
        run_id: str,
        n_validation_runs: int = 10,
        confidence_level: float = 0.95
    ):
        """
        Calculate confidence intervals for KPIs using validation runs
        
        Args:
            run_id: Base run to validate
            n_validation_runs: Number of validation runs
            confidence_level: Confidence level (default 95%)
        """
        # This would normally run multiple simulations with different seeds
        # For demonstration, we'll simulate the results
        
        with sqlite3.connect(self.db_path) as conn:
            # Get base run KPIs
            cursor = conn.execute(
                "SELECT kpi_summary_json FROM twin_runs WHERE run_id = ?",
                (run_id,)
            )
            row = cursor.fetchone()
            if not row or not row[0]:
                return
            
            base_kpis = json.loads(row[0])
            
            # Simulate validation runs (in reality, would run actual simulations)
            for kpi, base_value in base_kpis.items():
                # Simulate variation
                std_dev = base_value * 0.05  # 5% standard deviation
                samples = np.random.normal(base_value, std_dev, n_validation_runs)
                
                # Calculate statistics
                mean_val = np.mean(samples)
                std_val = np.std(samples)
                
                # Calculate confidence interval
                from scipy import stats
                confidence_interval = stats.t.interval(
                    confidence_level,
                    n_validation_runs - 1,
                    loc=mean_val,
                    scale=std_val / np.sqrt(n_validation_runs)
                )
                
                # Store confidence data
                conn.execute("""
                    INSERT INTO confidence_tracking 
                    (run_id, kpi, mean_value, std_dev, lower_bound, 
                     upper_bound, n_samples, confidence_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id, kpi, mean_val, std_val,
                    confidence_interval[0], confidence_interval[1],
                    n_validation_runs, confidence_level
                ))
            
            conn.commit()
    
    def create_recommendation(
        self,
        parameters: Dict[str, float],
        expected_improvement: Dict[str, float],
        recommendation_type: str = "optimization",
        confidence: float = 0.0,
        notes: Optional[str] = None
    ) -> int:
        """
        Create a new recommendation
        
        Args:
            parameters: Recommended parameter values
            expected_improvement: Expected KPI improvements
            recommendation_type: Type of recommendation
            confidence: Confidence in recommendation (0-1)
            notes: Optional notes
            
        Returns:
            Recommendation ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO recommendations 
                (recommendation_type, parameters_json, expected_improvement_json,
                 confidence, status, notes)
                VALUES (?, ?, ?, ?, 'pending', ?)
            """, (
                recommendation_type,
                json.dumps(parameters),
                json.dumps(expected_improvement),
                confidence,
                notes
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def _get_active_recommendations(self) -> List[Dict[str, Any]]:
        """Get pending recommendations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT recommendation_id, recommendation_type, 
                       parameters_json, expected_improvement_json,
                       confidence, created_at
                FROM recommendations 
                WHERE status = 'pending'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            recommendations = []
            for row in cursor.fetchall():
                recommendations.append({
                    "id": row[0],
                    "type": row[1],
                    "parameters": json.loads(row[2]),
                    "expected_improvement": json.loads(row[3]),
                    "confidence": row[4],
                    "created_at": row[5]
                })
            
            return recommendations
    
    def accept_recommendation(self, recommendation_id: int) -> Dict[str, float]:
        """
        Accept a recommendation and return its parameters
        
        Args:
            recommendation_id: ID of recommendation to accept
            
        Returns:
            Parameter values from the recommendation
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get recommendation
            cursor = conn.execute(
                "SELECT parameters_json FROM recommendations WHERE recommendation_id = ?",
                (recommendation_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"Recommendation {recommendation_id} not found")
            
            parameters = json.loads(row[0])
            
            # Update status
            conn.execute(
                "UPDATE recommendations SET status = 'accepted' WHERE recommendation_id = ?",
                (recommendation_id,)
            )
            conn.commit()
            
            return parameters
    
    def get_improvement_trends(
        self,
        n_runs: int = 10
    ) -> Dict[str, List[float]]:
        """
        Get KPI improvement trends over recent runs
        
        Args:
            n_runs: Number of recent runs to analyze
            
        Returns:
            Dictionary of KPI trends
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT run_id, kpi_summary_json, started_at
                FROM twin_runs 
                WHERE status = 'completed' AND kpi_summary_json IS NOT NULL
                ORDER BY started_at DESC
                LIMIT ?
            """, (n_runs,))
            
            trends = {}
            for row in cursor.fetchall():
                kpis = json.loads(row[1])
                for kpi, value in kpis.items():
                    if kpi not in trends:
                        trends[kpi] = []
                    trends[kpi].append(value)
            
            # Reverse to get chronological order
            for kpi in trends:
                trends[kpi].reverse()
            
            return trends
    
    def generate_state_report(self) -> str:
        """Generate a comprehensive state report"""
        state = self.get_current_state()
        
        if not state:
            return "No twin state available"
        
        report = []
        report.append("=" * 60)
        report.append("VIRTUAL TWIN STATE REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Last Update: {state.last_update.isoformat()}")
        report.append("")
        
        # Current configuration
        report.append("CURRENT CONFIGURATION:")
        report.append("-" * 40)
        for param, value in state.current_parameters.items():
            report.append(f"  {param}: {value:.3f}")
        report.append("")
        
        # Current KPIs
        report.append("CURRENT KPIs:")
        report.append("-" * 40)
        for kpi, value in state.current_kpis.items():
            conf_interval = state.confidence_intervals.get(kpi, (None, None))
            if conf_interval[0] is not None:
                report.append(
                    f"  {kpi}: {value:.3f} "
                    f"(95% CI: [{conf_interval[0]:.3f}, {conf_interval[1]:.3f}])"
                )
            else:
                report.append(f"  {kpi}: {value:.3f}")
        report.append("")
        
        # Sync status summary
        report.append("SYNCHRONIZATION STATUS:")
        report.append("-" * 40)
        status_counts = {}
        for entity, status in state.sync_status.items():
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            report.append(f"  {status}: {count} entities")
        report.append("")
        
        # Active recommendations
        if state.active_recommendations:
            report.append("ACTIVE RECOMMENDATIONS:")
            report.append("-" * 40)
            for i, rec in enumerate(state.active_recommendations, 1):
                report.append(f"\n  Recommendation {i} ({rec['type']}):")
                report.append(f"    Confidence: {rec['confidence']:.1%}")
                report.append("    Expected Improvements:")
                for kpi, improvement in rec['expected_improvement'].items():
                    report.append(f"      {kpi}: {improvement:+.1f}%")
        else:
            report.append("No active recommendations")
        
        # Improvement trends
        trends = self.get_improvement_trends(5)
        if trends:
            report.append("")
            report.append("RECENT TRENDS (last 5 runs):")
            report.append("-" * 40)
            for kpi, values in trends.items():
                if len(values) > 1:
                    trend = "↑" if values[-1] > values[0] else "↓" if values[-1] < values[0] else "→"
                    change = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                    report.append(f"  {kpi}: {trend} {change:+.1f}%")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def demonstrate_twin_state():
    """Demonstrate twin state management"""
    print("TWIN STATE MANAGEMENT DEMONSTRATION")
    print("=" * 60)
    
    manager = TwinStateManager()
    
    # Create initial state
    print("\n1. SETTING INITIAL STATE")
    print("-" * 40)
    
    manager.update_state(
        run_id="baseline-demo-001",
        baseline_run_id="baseline-demo-001",
        notes="Initial twin state"
    )
    print("✓ Initial state set")
    
    # Calculate confidence
    print("\n2. CALCULATING CONFIDENCE INTERVALS")
    print("-" * 40)
    
    manager.calculate_confidence("baseline-demo-001", n_validation_runs=10)
    print("✓ Confidence intervals calculated")
    
    # Create recommendations
    print("\n3. CREATING RECOMMENDATIONS")
    print("-" * 40)
    
    rec_id = manager.create_recommendation(
        parameters={
            "micro_stop_probability": 0.10,
            "performance_factor": 0.90
        },
        expected_improvement={
            "mean_oee": 10.0,
            "mean_availability": 6.25
        },
        recommendation_type="maintenance_improvement",
        confidence=0.85,
        notes="Reduce micro-stops through better maintenance"
    )
    print(f"✓ Created recommendation ID: {rec_id}")
    
    # Update state with new run
    print("\n4. UPDATING STATE WITH NEW RUN")
    print("-" * 40)
    
    manager.update_state(
        run_id="sim-demo-001",
        notes="Applied maintenance improvements"
    )
    print("✓ State updated with simulation results")
    
    # Generate report
    print("\n5. GENERATING STATE REPORT")
    print("-" * 40)
    
    # Note: This will show limited data since we're using demo runs
    report = manager.generate_state_report()
    print(report)
    
    print("\n✅ Twin state management demonstrated!")


if __name__ == "__main__":
    demonstrate_twin_state()