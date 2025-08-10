#!/usr/bin/env python3
"""
Virtual Twin - Natural Language REPL Interface
Main entry point for LLM to orchestrate twin operations
Following the virtual ontology pattern
"""

import sys
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse

# Add twin module path
sys.path.append(os.path.join(os.path.dirname(__file__), 'twin'))

from simulation_runner import SimulationRunner
from optimization_engine import OptimizationEngine
from cost_impact_calculator import CostImpactCalculator
from financial_roi_demo import FinancialROIAnalyzer
from disambiguation import DisambiguationHelper
from actionable_parameters import ActionableParameters


class VirtualTwin:
    """
    Main orchestrator for Virtual Twin operations
    Designed to be called by the Natural Language REPL (Claude Code)
    """
    
    def __init__(self, db_path: str = "data/mes_database.db"):
        self.db_path = db_path
        self.runner = SimulationRunner(db_path=db_path)
        self.engine = OptimizationEngine(simulation_runner=self.runner)
        self.calculator = CostImpactCalculator(db_path=db_path)
        self.analyzer = FinancialROIAnalyzer(db_path=db_path)
        self.helper = DisambiguationHelper()
        
        # Query result store (following virtual ontology pattern)
        self.operation_log = "twin_operations.jsonl"
        
    def get_baseline(self) -> Dict[str, Any]:
        """Get current baseline metrics from database"""
        with sqlite3.connect(self.db_path) as conn:
            # Get date range
            date_query = "SELECT MIN(timestamp), MAX(timestamp) FROM mes_data"
            date_result = conn.execute(date_query).fetchone()
            
            # Get KPIs for last week of data
            kpi_query = """
                SELECT 
                    AVG(oee_score) as avg_oee,
                    AVG(availability_score) as avg_availability,
                    AVG(performance_score) as avg_performance,
                    AVG(quality_score) as avg_quality,
                    SUM(CASE WHEN machine_status = 'Stopped' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as downtime_pct,
                    SUM(energy_consumption_kwh) as total_energy_kwh,
                    SUM(good_units_produced) as total_good_units,
                    SUM(scrap_units_produced) as total_scrap_units
                FROM mes_data
                WHERE timestamp >= datetime(?, '-6 days')
            """
            
            max_date = date_result[1] if date_result else '2025-06-14'
            result = conn.execute(kpi_query, (max_date,)).fetchone()
            
            return {
                'date_range': (date_result[0], date_result[1]) if date_result else None,
                'avg_oee': result[0] if result else 0,
                'avg_availability': result[1] if result else 0,
                'avg_performance': result[2] if result else 0,
                'avg_quality': result[3] if result else 0,
                'downtime_percentage': result[4] if result else 0,
                'weekly_energy_kwh': result[5] if result else 0,
                'total_good_units': int(result[6]) if result else 0,
                'total_scrap_units': int(result[7]) if result else 0
            }
    
    def simulate(self, 
                 changes: Dict[str, float],
                 duration_days: int = 14,
                 seed: int = 42) -> Dict[str, Any]:
        """
        Run simulation with parameter changes
        
        Args:
            changes: Dict of parameter changes, e.g., {'micro_stop_probability': -0.30}
            duration_days: Simulation duration
            seed: Random seed for reproducibility
        """
        baseline = self.get_baseline()
        
        # Create parameters with changes
        params = ActionableParameters()
        
        # Apply changes
        if 'micro_stop_probability' in changes:
            # Baseline is around 0.30, apply relative change
            params.micro_stop_probability = max(0.05, min(0.50, 0.30 * (1 + changes['micro_stop_probability'])))
        
        if 'performance_factor' in changes:
            params.performance_factor = max(0.50, min(1.00, 0.85 * (1 + changes['performance_factor'])))
        
        if 'scrap_multiplier' in changes:
            params.scrap_multiplier = max(1.0, min(5.0, 2.0 * (1 + changes['scrap_multiplier'])))
        
        # Run simulation
        results = self.runner.run_simulation(
            parameters=params,
            duration_days=duration_days,
            seed=seed
        )
        
        # Log operation
        self._log_operation('simulation', changes, results)
        
        return {
            'baseline': baseline,
            'parameters': params.to_dict(),
            'results': results,
            'changes': changes
        }
    
    def optimize(self,
                 objectives: List[str] = ['oee'],
                 constraints: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Run multi-objective optimization
        
        Args:
            objectives: List of objectives to optimize ['oee', 'energy', 'quality']
            constraints: Dict of constraints, e.g., {'quality_min': 0.95}
        """
        baseline = self.get_baseline()
        
        if constraints is None:
            constraints = {'quality_min': 0.95}
        
        # Run optimization
        results = self.engine.optimize_multi_objective(
            objectives=objectives,
            constraints=constraints,
            n_generations=50
        )
        
        # Log operation
        self._log_operation('optimization', 
                          {'objectives': objectives, 'constraints': constraints},
                          results)
        
        return {
            'baseline': baseline,
            'optimization_config': {
                'objectives': objectives,
                'constraints': constraints
            },
            'results': results
        }
    
    def calculate_roi(self,
                     scenario: str,
                     changes: Dict[str, float],
                     n_simulations: int = 1000) -> Dict[str, Any]:
        """
        Calculate ROI with Monte Carlo uncertainty
        
        Args:
            scenario: Scenario description
            changes: Parameter changes
            n_simulations: Number of Monte Carlo simulations
        """
        baseline = self.get_baseline()
        
        # Convert baseline to KPI format
        baseline_kpis = {
            'mean_oee': baseline['avg_oee'] / 100.0,
            'mean_availability': baseline['avg_availability'] / 100.0,
            'mean_performance': baseline['avg_performance'] / 100.0,
            'mean_quality': baseline['avg_quality'] / 100.0,
            'downtime_percentage': baseline['downtime_percentage'],
            'scrap_rate': baseline['total_scrap_units'] / (baseline['total_good_units'] + baseline['total_scrap_units']) if baseline['total_good_units'] > 0 else 0.05,
            'weekly_energy_kwh': baseline['weekly_energy_kwh']
        }
        
        # Calculate impact
        impact = self.calculator.calculate_scenario_impact(
            scenario,
            baseline_kpis,
            changes,
            n_simulations
        )
        
        # Log operation
        self._log_operation('financial', {'scenario': scenario, 'changes': changes}, impact)
        
        return impact
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze natural language query to determine intent
        
        Args:
            query: Natural language query from user
        """
        context = self.helper.get_query_context(query)
        
        # Determine operation type
        operation_type = 'unknown'
        if any(word in query.lower() for word in ['what if', 'simulate', 'would happen']):
            operation_type = 'simulation'
        elif any(word in query.lower() for word in ['optimize', 'best', 'maximize', 'minimize']):
            operation_type = 'optimization'
        elif any(word in query.lower() for word in ['roi', 'cost', 'financial', 'save', 'benefit']):
            operation_type = 'financial'
        elif any(word in query.lower() for word in ['why', 'cause', 'reason']):
            operation_type = 'root_cause'
        
        return {
            'query': query,
            'context': context,
            'suggested_operation': operation_type,
            'entities': context.get('entities', []),
            'metrics': context.get('metrics', []),
            'time_range': context.get('time_range', 'last_week')
        }
    
    def get_financial_report(self) -> str:
        """Generate comprehensive financial report"""
        return self.analyzer.generate_financial_report()
    
    def _log_operation(self, operation_type: str, inputs: Dict, results: Dict):
        """Log operation to result store (following virtual ontology pattern)"""
        import numpy as np
        
        def convert_to_serializable(obj):
            """Convert numpy types to Python types for JSON serialization"""
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            return obj
        
        operation = {
            'timestamp': datetime.now().isoformat(),
            'operation_type': operation_type,
            'inputs': convert_to_serializable(inputs),
            'results': convert_to_serializable(results)
        }
        
        with open(self.operation_log, 'a') as f:
            f.write(json.dumps(operation, default=str) + '\n')


def main():
    """CLI interface for Virtual Twin"""
    parser = argparse.ArgumentParser(description='Virtual Twin Operations')
    parser.add_argument('operation', choices=['baseline', 'simulate', 'optimize', 'roi', 'analyze', 'report'],
                       help='Operation to perform')
    parser.add_argument('--query', type=str, help='Natural language query')
    parser.add_argument('--changes', type=str, help='JSON string of parameter changes')
    parser.add_argument('--objectives', type=str, help='Comma-separated objectives')
    parser.add_argument('--scenario', type=str, help='Scenario description')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    twin = VirtualTwin()
    
    if args.operation == 'baseline':
        result = twin.get_baseline()
        print(json.dumps(result, indent=2))
        
    elif args.operation == 'simulate':
        changes = json.loads(args.changes) if args.changes else {'micro_stop_probability': -0.30}
        result = twin.simulate(changes, seed=args.seed)
        print(json.dumps(result, indent=2, default=str))
        
    elif args.operation == 'optimize':
        objectives = args.objectives.split(',') if args.objectives else ['oee']
        result = twin.optimize(objectives=objectives)
        print(json.dumps(result, indent=2, default=str))
        
    elif args.operation == 'roi':
        changes = json.loads(args.changes) if args.changes else {'micro_stop_probability': -0.30}
        scenario = args.scenario or "parameter_change"
        result = twin.calculate_roi(scenario, changes)
        print(json.dumps(result, indent=2, default=str))
        
    elif args.operation == 'analyze':
        if not args.query:
            print("Error: --query required for analyze operation")
            sys.exit(1)
        result = twin.analyze_query(args.query)
        print(json.dumps(result, indent=2))
        
    elif args.operation == 'report':
        report = twin.get_financial_report()
        print(report)


if __name__ == "__main__":
    main()