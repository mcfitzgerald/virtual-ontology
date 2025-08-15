"""Recommendation Engine with Multi-Objective Optimization using pymoo
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

from .actionable_parameters import ActionableParameters
from .simulation_runner import SimulationRunner
from .twin_state import TwinStateManager
from .config_loader import ConfigLoader


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
    """Multi-objective optimization problem for manufacturing using pymoo
    Wraps the simulation runner to evaluate actual simulations
    """
    
    def __init__(
        self,
        simulation_runner: SimulationRunner,
        objectives: List[Objective],
        constraints: Optional[Dict[str, Tuple[float, float]]] = None,
        use_simulation: bool = False  # Toggle between simulation and approximation
    ) -> None:
        """Initialize the manufacturing optimization problem
        
        Args:
            simulation_runner: SimulationRunner instance for evaluations
            objectives: List of optimization objectives
            constraints: Optional parameter constraints
            use_simulation: If True, run actual simulations; if False, use approximations

        """
        self.runner: SimulationRunner = simulation_runner
        self.objectives: List[Objective] = objectives
        self.constraints: Dict[str, Tuple[float, float]] = constraints or {}
        self.use_simulation: bool = use_simulation
        self.cached_evaluations: Dict[str, Any] = {}
        
        # Load configuration
        loader = ConfigLoader()
        self.config = loader.get_module_config('recommendation_engine')
        
        # Get parameter definitions
        params: ActionableParameters = ActionableParameters()
        self.param_names: List[str] = list(params.parameters.keys())
        self.param_objects: List[Any] = list(params.parameters.values())
        
        # Set bounds from ActionableParameters
        xl: List[float] = []
        xu: List[float] = []
        for param_name, param_obj in zip(self.param_names, self.param_objects):
            if param_name in self.constraints:
                min_val, max_val = self.constraints[param_name]
            else:
                min_val, max_val = param_obj.bounds
            xl.append(min_val)
            xu.append(max_val)
        
        # Count constraints for pymoo
        n_ieq_constr: int = len([obj for obj in objectives if obj.constraint is not None])
        
        super().__init__(
            n_var=len(self.param_names),  # 5 actionable parameters
            n_obj=len(objectives),  # Number of objectives
            n_ieq_constr=n_ieq_constr,  # Inequality constraints
            xl=np.array(xl),  # Lower bounds
            xu=np.array(xu)   # Upper bounds
        )
    
    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluate objectives and constraints for a batch of solutions.
        
        Args:
            x: Array of decision variables (population x n_var).
            out: Dictionary to store objectives and constraints.
            *args: Additional positional arguments passed by pymoo framework.
            **kwargs: Additional keyword arguments passed by pymoo framework.

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
        """Run actual simulation using SimulationRunner
        
        Args:
            param_dict: Dictionary of parameter values
            
        Returns:
            Dictionary of KPI values

        """
        # Create ActionableParameters instance
        params: ActionableParameters = ActionableParameters()
        for name, value in param_dict.items():
            params.set_value(name, value)
        
        # Run simulation
        duration_days = self.config.get('simulation_duration_days', 7)
        run_id: str = self.runner.run_simulation(
            parameters=params,
            duration_days=duration_days,
            notes="Optimization evaluation"
        )
        
        # Get KPIs from simulation
        kpis: Dict[str, float] = self.runner.get_run_kpis(run_id)
        return kpis
    
    def _approximate_kpis(self, param_dict: Dict[str, float]) -> Dict[str, float]:
        """Approximate KPIs based on parameters (faster than simulation)
        Uses simplified models for demonstration
        
        Args:
            param_dict: Dictionary of parameter values
            
        Returns:
            Dictionary of approximated KPI values

        """
        values: Dict[str, float] = param_dict
        
        # Base values from config
        base_kpis = self.config.get('base_kpis', {})
        base_oee: float = base_kpis.get('oee', 0.65)
        base_availability: float = base_kpis.get('availability', 0.80)
        base_performance: float = base_kpis.get('performance', 0.85)
        base_quality: float = base_kpis.get('quality', 0.95)
        base_energy: float = base_kpis.get('energy_per_day', 1000.0)
        base_scrap: float = base_kpis.get('scrap_rate', 0.05)
        
        # Calculate impacts using config baselines
        # Get baseline values from generator config
        loader = ConfigLoader()
        gen_params = loader.get_generator_config().get('parameters', {})
        
        micro_stop_baseline = gen_params.get('micro_stop_probability', {}).get('default', 1.0)
        perf_baseline = gen_params.get('performance_factor', {}).get('default', 1.0)
        scrap_baseline = gen_params.get('scrap_multiplier', {}).get('default', 1.0)
        material_baseline = gen_params.get('material_reliability', {}).get('default', 1.0)
        cascade_baseline = gen_params.get('cascade_sensitivity', {}).get('default', 1.0)
        
        micro_stop_impact: float = (micro_stop_baseline - values['micro_stop_probability']) / micro_stop_baseline if micro_stop_baseline > 0 else 0
        perf_impact: float = (values['performance_factor'] - perf_baseline) / perf_baseline if perf_baseline > 0 else 0
        scrap_impact: float = (scrap_baseline - values['scrap_multiplier']) / scrap_baseline if scrap_baseline > 0 else 0
        material_impact: float = (values['material_reliability'] - material_baseline) / material_baseline if material_baseline > 0 else 0
        cascade_impact: float = (cascade_baseline - values['cascade_sensitivity']) / cascade_baseline if cascade_baseline > 0 else 0
        
        # Calculate KPIs with configurable impact weights
        # These would ideally be in config, but using reasonable defaults
        availability: float = base_availability * (1 + 0.3 * micro_stop_impact + 0.1 * material_impact)
        performance: float = base_performance * (1 + 0.4 * perf_impact)
        quality: float = base_quality * (1 + 0.2 * scrap_impact)
        
        oee: float = availability * performance * quality
        
        # Energy inversely related to performance
        energy_per_unit: float = base_energy * (1 - 0.2 * perf_impact)
        
        # Scrap rate
        scrap_rate: float = base_scrap * values['scrap_multiplier']
        
        # Downtime
        downtime_pct: float = (1 - availability) * 100
        
        return {
            'mean_oee': min(1.0, max(0.0, oee)),
            'mean_availability': min(1.0, max(0.0, availability)),
            'mean_performance': min(1.0, max(0.0, performance)),
            'mean_quality': min(1.0, max(0.0, quality)),
            'energy_per_unit': max(100, energy_per_unit),
            'scrap_rate': min(0.5, max(0.0, scrap_rate)),
            'downtime_percentage': min(100, max(0, downtime_pct)),
            'total_good_units': base_kpis.get('production_units', 10000) * oee,
            'total_cost': 1000 + energy_per_unit * 0.15 + scrap_rate * 5000
        }


class RecommendationEngine:
    """Multi-objective optimization engine for virtual twin recommendations
    Uses pymoo's NSGA-II algorithm with proper constraint handling
    """
    
    def __init__(
        self,
        simulation_runner: Optional[SimulationRunner] = None,
        state_manager: Optional[TwinStateManager] = None
    ) -> None:
        """Initialize the RecommendationEngine.
        
        Args:
            simulation_runner: Optional SimulationRunner instance. If None, creates a new one.
            state_manager: Optional TwinStateManager instance. If None, creates a new one.

        """
        self.runner: SimulationRunner = simulation_runner or SimulationRunner()
        self.state_manager: TwinStateManager = state_manager or TwinStateManager()
        
    def optimize(
        self,
        objectives: List[Objective],
        constraints: Optional[Dict[str, Tuple[float, float]]] = None,
        population_size: Optional[int] = None,
        generations: Optional[int] = None,
        seed: Optional[int] = None,
        verbose: bool = True,
        use_simulation: bool = False
    ) -> List[OptimizationResult]:
        """Run multi-objective optimization using pymoo's NSGA-II
        
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
        # Load config and use defaults if not provided
        loader = ConfigLoader()
        config = loader.get_module_config('recommendation_engine')
        
        if population_size is None:
            population_size = config.get('optimization', {}).get('population_size', 50)
        if generations is None:
            generations = config.get('optimization', {}).get('generations', 100)
        if seed is None:
            seed = config.get('optimization', {}).get('seed', 42)
            
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
            # Handle both 1D and 2D arrays from optimizer
            if len(res.X.shape) == 1:
                # Single solution - reshape to 2D
                X_array = res.X.reshape(1, -1)
            else:
                X_array = res.X
                
            for i in range(len(X_array)):
                # Convert solution to parameter dictionary
                param_dict = {
                    name: float(X_array[i, j])
                    for j, name in enumerate(problem.param_names)
                }
                
                # Create objective dictionary
                # Handle both 1D and 2D F arrays
                if len(res.F.shape) == 1:
                    F_array = res.F.reshape(1, -1)
                else:
                    F_array = res.F
                    
                # Un-negate maximized objectives when storing
                obj_dict = {}
                for j, obj in enumerate(objectives):
                    value = float(F_array[i, j])
                    # If objective was maximized, it was negated, so un-negate it
                    if obj.direction == 'maximize':
                        value = -value
                    obj_dict[obj.name] = value
                
                # Determine feasibility
                feasible = True
                if hasattr(res, 'G') and res.G is not None and len(res.G) > 0:
                    if len(res.G.shape) == 1:
                        feasible = np.all(res.G <= 0)
                    else:
                        feasible = np.all(res.G[i] <= 0) if i < len(res.G) else True
                
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
        """Calculate hypervolume indicator for the Pareto front
        
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
        """Visualize the Pareto front using pymoo's Scatter plot
        
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
            plot.axis_labels = objective_names
        
        plot.show()
    
    def recommend_for_scenario(
        self,
        scenario: str,
        save_recommendation: bool = True,
        use_simulation: bool = False
    ) -> Dict[str, Any]:
        """Generate recommendation for a specific scenario using pymoo
        
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
        """Select a compromise solution from Pareto front
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
        
        # For specific scenarios, always include OEE as primary objective
        # to prevent solutions that destroy overall performance
        
        if 'maximize_oee' in scenario_lower or 'oee' in scenario_lower:
            # Single objective: maximize OEE
            objectives.append(Objective(
                name="oee",
                direction="maximize",
                kpi_name="mean_oee",
                weight=1.0
            ))
        
        elif 'reduce_downtime' in scenario_lower or 'availability' in scenario_lower:
            # Primary: maximize availability, Secondary: maintain OEE
            objectives.append(Objective(
                name="availability",
                direction="maximize",
                kpi_name="mean_availability",
                weight=1.0
            ))
            # Add OEE as secondary to prevent degradation
            objectives.append(Objective(
                name="oee",
                direction="maximize",
                kpi_name="mean_oee",
                weight=0.5
            ))
        
        elif 'improve_quality' in scenario_lower or 'scrap' in scenario_lower:
            # Primary: minimize scrap, Secondary: maintain OEE
            objectives.append(Objective(
                name="quality",
                direction="minimize",
                kpi_name="scrap_rate",
                weight=1.0
            ))
            # Add OEE as secondary to prevent degradation
            objectives.append(Objective(
                name="oee",
                direction="maximize",
                kpi_name="mean_oee",
                weight=0.5
            ))
        
        elif any(word in scenario_lower for word in ['energy', 'power', 'consumption']):
            objectives.append(Objective(
                name="energy_efficiency",
                direction="minimize",
                kpi_name="energy_per_unit",
                weight=1.0
            ))
            # Add OEE as secondary
            objectives.append(Objective(
                name="oee",
                direction="maximize",
                kpi_name="mean_oee",
                weight=0.5
            ))
        
        elif any(word in scenario_lower for word in ['throughput', 'production', 'output']):
            objectives.append(Objective(
                name="throughput",
                direction="maximize",
                kpi_name="total_good_units",
                weight=1.0
            ))
        
        elif any(word in scenario_lower for word in ['cost', 'savings', 'financial']):
            objectives.append(Objective(
                name="cost",
                direction="minimize",
                kpi_name="total_cost",
                weight=1.0
            ))
            # Add OEE as secondary
            objectives.append(Objective(
                name="oee",
                direction="maximize",
                kpi_name="mean_oee",
                weight=0.5
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