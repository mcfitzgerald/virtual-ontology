"""
Recommendation Engine with Multi-Objective Optimization using pymoo
Uses NSGA-II algorithm for finding Pareto-optimal configurations
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
import sqlite3
from datetime import datetime
import sys
import os

# pymoo imports for multi-objective optimization
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.indicators.hv import HV
from pymoo.indicators.igd import IGD
from pymoo.util.ref_dirs import get_reference_directions
from pymoo.visualization.scatter import Scatter

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from actionable_parameters import ActionableParameters
from simulation_runner import SimulationRunner
from twin_state import TwinStateManager


@dataclass
class Objective:
    """Optimization objective definition"""
    name: str
    direction: str  # 'minimize' or 'maximize'
    kpi_name: str
    weight: float = 1.0
    constraint: Optional[Tuple[float, float]] = None  # (min, max)


@dataclass
class OptimizationResult:
    """Result from multi-objective optimization"""
    parameters: Dict[str, float]
    objectives: Dict[str, float]
    pareto_rank: int
    crowding_distance: float
    feasible: bool
    run_id: Optional[str] = None


class ManufacturingProblem(Problem):
    """
    Multi-objective optimization problem for manufacturing using pymoo
    Wraps the simulation runner to evaluate actual simulations
    """
    
    def __init__(
        self,
        simulation_runner: SimulationRunner,
        objectives: List[Objective],
        constraints: Optional[Dict[str, Tuple[float, float]]] = None,
        use_simulation: bool = False  # Toggle between simulation and approximation
    ):
        """
        Initialize the manufacturing optimization problem
        
        Args:
            simulation_runner: SimulationRunner instance for evaluations
            objectives: List of optimization objectives
            constraints: Optional parameter constraints
            use_simulation: If True, run actual simulations; if False, use approximations
        """
        self.runner = simulation_runner
        self.objectives = objectives
        self.constraints = constraints or {}
        self.use_simulation = use_simulation
        self.cached_evaluations = {}
        
        # Get parameter definitions
        params = ActionableParameters()
        self.param_names = list(params.parameters.keys())
        self.param_objects = list(params.parameters.values())
        
        # Set bounds from ActionableParameters
        xl = []
        xu = []
        for param_name, param_obj in zip(self.param_names, self.param_objects):
            if param_name in self.constraints:
                min_val, max_val = self.constraints[param_name]
            else:
                min_val, max_val = param_obj.bounds
            xl.append(min_val)
            xu.append(max_val)
        
        # Count constraints for pymoo
        n_ieq_constr = len([obj for obj in objectives if obj.constraint is not None])
        
        super().__init__(
            n_var=len(self.param_names),  # 5 actionable parameters
            n_obj=len(objectives),  # Number of objectives
            n_ieq_constr=n_ieq_constr,  # Inequality constraints
            xl=np.array(xl),  # Lower bounds
            xu=np.array(xu)   # Upper bounds
        )
    
    def _evaluate(self, x, out, *args, **kwargs):
        """
        Evaluate objectives and constraints for a batch of solutions
        
        Args:
            x: Array of decision variables (population x n_var)
            out: Dictionary to store objectives and constraints
        """
        n_pop = x.shape[0]
        objectives = np.zeros((n_pop, self.n_obj))
        constraints = []
        
        for i in range(n_pop):
            # Convert to parameter dictionary
            param_dict = {
                name: float(x[i, j]) 
                for j, name in enumerate(self.param_names)
            }
            
            # Check cache
            param_key = tuple(x[i])
            if param_key in self.cached_evaluations:
                kpis = self.cached_evaluations[param_key]
            else:
                # Get KPIs either from simulation or approximation
                if self.use_simulation:
                    kpis = self._run_simulation(param_dict)
                else:
                    kpis = self._approximate_kpis(param_dict)
                self.cached_evaluations[param_key] = kpis
            
            # Calculate objective values
            for j, obj in enumerate(self.objectives):
                value = kpis.get(obj.kpi_name, 0.0)
                
                # Apply direction and weight
                if obj.direction == 'minimize':
                    objectives[i, j] = value * obj.weight
                else:  # maximize
                    objectives[i, j] = -value * obj.weight  # Negate for minimization
                
                # Handle constraints if specified
                if obj.constraint is not None:
                    min_val, max_val = obj.constraint
                    if min_val is not None:
                        constraints.append(min_val - value)  # g(x) <= 0 form
                    if max_val is not None:
                        constraints.append(value - max_val)  # g(x) <= 0 form
        
        out["F"] = objectives
        if constraints:
            out["G"] = np.column_stack(constraints) if len(constraints) > 0 else None
    
    def _run_simulation(self, param_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Run actual simulation using SimulationRunner
        
        Args:
            param_dict: Dictionary of parameter values
            
        Returns:
            Dictionary of KPI values
        """
        # Create ActionableParameters instance
        params = ActionableParameters()
        for name, value in param_dict.items():
            params.set_value(name, value)
        
        # Run simulation
        run_id = self.runner.run_simulation(
            parameters=params,
            duration_days=7,
            notes="Optimization evaluation"
        )
        
        # Get KPIs from simulation
        kpis = self.runner.get_run_kpis(run_id)
        return kpis
    
    def _approximate_kpis(self, param_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Approximate KPIs based on parameters (faster than simulation)
        Uses simplified models for demonstration
        
        Args:
            param_dict: Dictionary of parameter values
            
        Returns:
            Dictionary of approximated KPI values
        """
        values = param_dict
        
        # Base values
        base_oee = 0.65
        base_availability = 0.80
        base_performance = 0.85
        base_quality = 0.95
        base_energy = 1000.0  # kWh per day
        base_scrap = 0.05
        
        # Calculate impacts
        micro_stop_impact = (0.20 - values['micro_stop_probability']) / 0.20
        perf_impact = (values['performance_factor'] - 0.85) / 0.85
        scrap_impact = (2.0 - values['scrap_multiplier']) / 2.0
        material_impact = (values['material_reliability'] - 0.85) / 0.85
        cascade_impact = (0.5 - values['cascade_sensitivity']) / 0.5
        
        # Calculate KPIs
        availability = base_availability * (1 + 0.3 * micro_stop_impact + 0.1 * material_impact)
        performance = base_performance * (1 + 0.4 * perf_impact)
        quality = base_quality * (1 + 0.2 * scrap_impact)
        
        oee = availability * performance * quality
        
        # Energy inversely related to performance
        energy_per_unit = base_energy * (1 - 0.2 * perf_impact)
        
        # Scrap rate
        scrap_rate = base_scrap * values['scrap_multiplier']
        
        # Downtime
        downtime_pct = (1 - availability) * 100
        
        return {
            'mean_oee': min(1.0, max(0.0, oee)),
            'mean_availability': min(1.0, max(0.0, availability)),
            'mean_performance': min(1.0, max(0.0, performance)),
            'mean_quality': min(1.0, max(0.0, quality)),
            'energy_per_unit': max(100, energy_per_unit),
            'scrap_rate': min(0.5, max(0.0, scrap_rate)),
            'downtime_percentage': min(100, max(0, downtime_pct)),
            'total_good_units': 10000 * oee,  # Approximate production
            'total_cost': 1000 + energy_per_unit * 0.15 + scrap_rate * 5000  # Simplified cost
        }


class RecommendationEngine:
    """
    Multi-objective optimization engine for virtual twin recommendations
    Uses pymoo's NSGA-II algorithm with proper constraint handling
    """
    
    def __init__(
        self,
        simulation_runner: Optional[SimulationRunner] = None,
        state_manager: Optional[TwinStateManager] = None
    ):
        self.runner = simulation_runner or SimulationRunner()
        self.state_manager = state_manager or TwinStateManager()
        
    def optimize(
        self,
        objectives: List[Objective],
        constraints: Optional[Dict[str, Tuple[float, float]]] = None,
        population_size: int = 50,
        generations: int = 100,
        seed: int = 42,
        verbose: bool = True,
        use_simulation: bool = False
    ) -> List[OptimizationResult]:
        """
        Run multi-objective optimization using pymoo's NSGA-II
        
        Args:
            objectives: List of optimization objectives
            constraints: Optional parameter constraints
            population_size: Size of population for genetic algorithm
            generations: Number of generations to evolve
            seed: Random seed for reproducibility
            verbose: Print progress information
            use_simulation: If True, use actual simulations; if False, use approximations
            
        Returns:
            List of Pareto-optimal solutions
        """
        # Create the optimization problem
        problem = ManufacturingProblem(
            simulation_runner=self.runner,
            objectives=objectives,
            constraints=constraints,
            use_simulation=use_simulation
        )
        
        # Configure NSGA-II algorithm
        algorithm = NSGA2(
            pop_size=population_size,
            sampling=FloatRandomSampling(),
            crossover=SBX(prob=0.9, eta=15),
            mutation=PM(eta=20),
            eliminate_duplicates=True
        )
        
        # Run optimization
        res = minimize(
            problem,
            algorithm,
            ('n_gen', generations),
            seed=seed,
            verbose=verbose,
            save_history=True
        )
        
        # Extract Pareto front solutions
        results = []
        if res.F is not None:
            for i in range(len(res.X)):
                # Convert solution to parameter dictionary
                param_dict = {
                    name: float(res.X[i, j])
                    for j, name in enumerate(problem.param_names)
                }
                
                # Create objective dictionary
                obj_dict = {
                    obj.name: float(res.F[i, j])
                    for j, obj in enumerate(objectives)
                }
                
                # Determine feasibility
                feasible = True
                if hasattr(res, 'G') and res.G is not None:
                    feasible = np.all(res.G[i] <= 0)
                
                results.append(OptimizationResult(
                    parameters=param_dict,
                    objectives=obj_dict,
                    pareto_rank=1,  # All solutions in res.X are Pareto-optimal
                    crowding_distance=0.0,  # Can be calculated if needed
                    feasible=feasible
                ))
        
        return results
    
    def calculate_hypervolume(
        self,
        results: List[OptimizationResult],
        ref_point: Optional[np.ndarray] = None
    ) -> float:
        """
        Calculate hypervolume indicator for the Pareto front
        
        Args:
            results: List of optimization results
            ref_point: Reference point for hypervolume calculation
            
        Returns:
            Hypervolume value
        """
        if not results:
            return 0.0
        
        # Extract objective values
        F = np.array([[v for v in r.objectives.values()] for r in results])
        
        # Use nadir point as reference if not provided
        if ref_point is None:
            ref_point = np.max(F, axis=0) * 1.1
        
        # Calculate hypervolume
        hv = HV(ref_point=ref_point)
        return hv(F)
    
    def visualize_pareto_front(
        self,
        results: List[OptimizationResult],
        objective_names: Optional[List[str]] = None,
        true_front: Optional[np.ndarray] = None
    ):
        """
        Visualize the Pareto front using pymoo's Scatter plot
        
        Args:
            results: List of optimization results
            objective_names: Names of objectives for axis labels
            true_front: Optional true Pareto front for comparison
        """
        if not results:
            print("No results to visualize")
            return
        
        # Extract objective values
        F = np.array([[v for v in r.objectives.values()] for r in results])
        
        # Create scatter plot
        plot = Scatter()
        
        # Add true Pareto front if available
        if true_front is not None:
            plot.add(true_front, plot_type="line", color="black", alpha=0.7, label="True Front")
        
        # Add obtained solutions
        plot.add(F, facecolor="none", edgecolor="red", label="NSGA-II")
        
        # Set labels if provided
        if objective_names:
            plot.set_labels(objective_names)
        
        plot.show()
    
    def recommend_for_scenario(
        self,
        scenario: str,
        save_recommendation: bool = True,
        use_simulation: bool = False
    ) -> Dict[str, Any]:
        """
        Generate recommendation for a specific scenario using pymoo
        
        Args:
            scenario: Scenario description
            save_recommendation: Whether to save to database
            use_simulation: Whether to use actual simulations
            
        Returns:
            Recommendation dictionary
        """
        # Map scenario to objectives
        objectives = self._map_scenario_to_objectives(scenario)
        
        # Run optimization with pymoo
        results = self.optimize(
            objectives=objectives,
            population_size=40,
            generations=50,
            verbose=False,
            use_simulation=use_simulation
        )
        
        if not results:
            return {"error": "No feasible solutions found"}
        
        # Select best compromise solution (can use different selection methods)
        # For now, select the one closest to the ideal point
        best = self._select_compromise_solution(results, objectives)
        
        # Calculate expected improvements
        params = ActionableParameters()
        problem = ManufacturingProblem(
            self.runner, objectives, use_simulation=use_simulation
        )
        baseline_kpis = problem._approximate_kpis(params.get_all_values())
        
        # Apply recommended parameters
        for name, value in best.parameters.items():
            params.set_value(name, value)
        
        improved_kpis = problem._approximate_kpis(best.parameters)
        
        improvements = {
            kpi: ((improved_kpis[kpi] - baseline_kpis[kpi]) / baseline_kpis[kpi] * 100)
            if baseline_kpis[kpi] != 0 else 0
            for kpi in baseline_kpis
        }
        
        # Save recommendation if requested
        rec_id = None
        if save_recommendation:
            rec_id = self.state_manager.create_recommendation(
                parameters=best.parameters,
                expected_improvement=improvements,
                recommendation_type=f"pymoo_optimization_{scenario}",
                confidence=0.85,  # Higher confidence with pymoo
                notes=f"Multi-objective optimization using pymoo NSGA-II for: {scenario}"
            )
        
        return {
            "scenario": scenario,
            "recommendation_id": rec_id,
            "parameters": best.parameters,
            "expected_improvements": improvements,
            "objectives_achieved": best.objectives,
            "feasible": best.feasible,
            "confidence": 0.85,
            "algorithm": "pymoo NSGA-II"
        }
    
    def _select_compromise_solution(
        self,
        results: List[OptimizationResult],
        objectives: List[Objective]
    ) -> OptimizationResult:
        """
        Select a compromise solution from Pareto front
        Uses distance to ideal point
        
        Args:
            results: List of Pareto-optimal solutions
            objectives: List of objectives for direction info
            
        Returns:
            Best compromise solution
        """
        if len(results) == 1:
            return results[0]
        
        # Extract objective values
        F = np.array([[v for v in r.objectives.values()] for r in results])
        
        # Find ideal point (best value for each objective)
        ideal = np.min(F, axis=0)
        
        # Calculate distance to ideal point for each solution
        distances = np.linalg.norm(F - ideal, axis=1)
        
        # Return solution with minimum distance
        best_idx = np.argmin(distances)
        return results[best_idx]
    
    def _map_scenario_to_objectives(self, scenario: str) -> List[Objective]:
        """Map scenario description to optimization objectives"""
        scenario_lower = scenario.lower()
        objectives = []
        
        # Energy efficiency
        if any(word in scenario_lower for word in ['energy', 'power', 'consumption']):
            objectives.append(Objective(
                name="energy_efficiency",
                direction="minimize",
                kpi_name="energy_per_unit",
                weight=1.0
            ))
        
        # Quality
        if any(word in scenario_lower for word in ['quality', 'scrap', 'defect']):
            objectives.append(Objective(
                name="quality",
                direction="minimize",
                kpi_name="scrap_rate",
                weight=1.0
            ))
        
        # Throughput
        if any(word in scenario_lower for word in ['throughput', 'production', 'output']):
            objectives.append(Objective(
                name="throughput",
                direction="maximize",
                kpi_name="total_good_units",
                weight=1.0
            ))
        
        # Maintenance
        if any(word in scenario_lower for word in ['maintenance', 'downtime', 'availability']):
            objectives.append(Objective(
                name="availability",
                direction="maximize",
                kpi_name="mean_availability",
                weight=1.0
            ))
        
        # Cost
        if any(word in scenario_lower for word in ['cost', 'savings', 'financial']):
            objectives.append(Objective(
                name="cost",
                direction="minimize",
                kpi_name="total_cost",
                weight=1.5
            ))
        
        # Default: optimize OEE
        if not objectives:
            objectives.append(Objective(
                name="oee",
                direction="maximize",
                kpi_name="mean_oee",
                weight=1.0
            ))
        
        return objectives


def demonstrate_recommendation_engine():
    """Demonstrate multi-objective optimization with pymoo"""
    print("RECOMMENDATION ENGINE DEMONSTRATION (pymoo)")
    print("=" * 60)
    
    engine = RecommendationEngine()
    
    # Test 1: Energy vs Throughput optimization
    print("\n1. MULTI-OBJECTIVE OPTIMIZATION: Energy vs Throughput")
    print("-" * 40)
    
    objectives = [
        Objective("energy", "minimize", "energy_per_unit"),
        Objective("throughput", "maximize", "total_good_units")
    ]
    
    results = engine.optimize(
        objectives=objectives,
        population_size=30,
        generations=40,
        verbose=False,
        use_simulation=False  # Use approximation for demo
    )
    
    print(f"Found {len(results)} Pareto-optimal solutions")
    
    # Calculate hypervolume
    hv = engine.calculate_hypervolume(results)
    print(f"Hypervolume indicator: {hv:.4f}")
    
    print("\nTop 3 solutions:")
    for i, result in enumerate(results[:3], 1):
        print(f"\nSolution {i}:")
        print(f"  Energy: {-result.objectives.get('energy', 0):.1f} kWh/unit")
        print(f"  Throughput: {-result.objectives.get('throughput', 0):.0f} units")
        print(f"  Feasible: {result.feasible}")
        print(f"  Key parameters:")
        for param, value in result.parameters.items():
            params = ActionableParameters()
            default = params.parameters[param].default
            if abs(value - default) > 0.05:  # Show only changed params
                print(f"    {param}: {value:.3f}")
    
    # Visualize Pareto front (if in interactive environment)
    try:
        engine.visualize_pareto_front(
            results,
            objective_names=["Energy (kWh/unit)", "Throughput (units)"]
        )
    except:
        print("(Visualization skipped - requires display)")
    
    # Test 2: Scenario-based recommendation
    print("\n2. SCENARIO-BASED RECOMMENDATION (pymoo)")
    print("-" * 40)
    
    scenarios = [
        "optimize for energy efficiency",
        "maximize throughput while maintaining quality",
        "reduce maintenance costs"
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: '{scenario}'")
        recommendation = engine.recommend_for_scenario(
            scenario,
            save_recommendation=False,
            use_simulation=False
        )
        
        if "error" not in recommendation:
            print(f"Algorithm: {recommendation.get('algorithm', 'N/A')}")
            print(f"Confidence: {recommendation.get('confidence', 0):.0%}")
            print("Recommended changes:")
            params = ActionableParameters()
            for param, value in recommendation["parameters"].items():
                default = params.parameters[param].default
                if abs(value - default) > 0.01:
                    change = ((value - default) / default * 100) if default != 0 else 0
                    print(f"  {param}: {value:.3f} ({change:+.1f}% from default)")
            
            print("Expected improvements:")
            for kpi, improvement in recommendation["expected_improvements"].items():
                if abs(improvement) > 1:
                    print(f"  {kpi}: {improvement:+.1f}%")
    
    print("\n✅ pymoo-based recommendation engine demonstrated!")


if __name__ == "__main__":
    demonstrate_recommendation_engine()