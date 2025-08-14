"""Twin Optimization Engine
Multi-objective optimization using scipy's differential evolution algorithm
Following VIRTUAL_TWIN_IMPLEMENTATION_PLAN_FINAL.md Phase 4 specifications
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from scipy.optimize import differential_evolution, NonlinearConstraint, LinearConstraint, Bounds
import logging
from datetime import datetime
import json
from .config_loader import ConfigLoader

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ActionableParameter:
    """Actionable parameter that can be tuned in the simulation
    Ref: VIRTUAL_TWIN_IMPLEMENTATION_PLAN_FINAL.md lines 114-122
    """

    name: str
    bounds: Tuple[float, float]
    unit: str  # QUDT URI
    causal_effect: str
    invariants: List[str]
    current_value: Optional[float] = None


@dataclass
class OptimizationObjective:
    """Single optimization objective"""

    name: str
    direction: str  # 'minimize' or 'maximize'
    weight: float = 1.0
    target: Optional[float] = None


@dataclass
class OptimizationResult:
    """Result from optimization run"""

    parameters: Dict[str, float]
    objectives: Dict[str, float]
    success: bool
    message: str
    iterations: int
    evaluations: int
    pareto_rank: Optional[int] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    run_id: Optional[str] = None


class OptimizationEngine:
    """Multi-objective optimization engine using differential evolution
    Implements NSGA-II concepts for Pareto optimization
    """
    
    # The 5 Actionable Parameters (lines 124-147)
    PARAMETERS = {
        'micro_stop_probability': ActionableParameter(
            name='micro_stop_probability',
            bounds=(0.05, 0.50),  # TODO: HARDCODED - parameter bounds
            unit='http://qudt.org/vocab/unit/PERCENT',
            causal_effect='Reduces availability score',
            invariants=['value >= 0', 'value <= 1']
        ),
        'performance_factor': ActionableParameter(
            name='performance_factor',
            bounds=(0.50, 1.00),  # TODO: HARDCODED - parameter bounds
            unit='http://qudt.org/vocab/quantitykind/Dimensionless',
            causal_effect='Scales actual vs target throughput',
            invariants=['value > 0', 'value <= 1']
        ),
        'scrap_multiplier': ActionableParameter(
            name='scrap_multiplier',
            bounds=(1.0, 5.0),  # TODO: HARDCODED - parameter bounds
            unit='http://qudt.org/vocab/quantitykind/Dimensionless',
            causal_effect='Increases defect rate, reduces quality score',
            invariants=['value >= 1']
        ),
        'material_reliability': ActionableParameter(
            name='material_reliability',
            bounds=(0.50, 1.00),  # TODO: HARDCODED - parameter bounds
            unit='http://qudt.org/vocab/unit/PERCENT',
            causal_effect='Probability of good material batch',
            invariants=['value >= 0', 'value <= 1']
        ),
        'cascade_sensitivity': ActionableParameter(
            name='cascade_sensitivity',
            bounds=(0.0, 1.0),  # TODO: HARDCODED - parameter bounds
            unit='http://qudt.org/vocab/quantitykind/Dimensionless',
            causal_effect='Controls blockage/starvation propagation',
            invariants=['value >= 0', 'value <= 1']
        )
    }
    
    def __init__(self, simulation_runner: Optional[Any] = None) -> None:
        """Initialize optimization engine
        
        Args:
            simulation_runner: Optional simulation runner for evaluating solutions

        """
        self.loader = ConfigLoader()
        self.config = self.loader.config
        
        # Update parameter bounds from configuration
        for param_name, param_config in self.config["parameters"].items():
            if param_name in self.PARAMETERS:
                self.PARAMETERS[param_name].bounds = (
                    param_config["bounds"]["min"],
                    param_config["bounds"]["max"]
                )
        
        self.simulation_runner: Optional[Any] = simulation_runner
        self.evaluation_count: int = 0
        self.best_solution: Optional[OptimizationResult] = None
        self.pareto_front: List[OptimizationResult] = []
        
    def optimize(
        self,
        objectives: List[OptimizationObjective],
        constraints: Optional[Dict[str, Any]] = None,
        population_size: int = 40,  # TODO: HARDCODED - default population size
        generations: int = 100,  # TODO: HARDCODED - default generations
        seed: int = 42,  # TODO: HARDCODED - default seed
        strategy: str = 'best1bin',
        mutation: Tuple[float, float] = (0.5, 1.0),  # TODO: HARDCODED - mutation range
        recombination: float = 0.7,  # TODO: HARDCODED - recombination probability
        workers: int = 1,
        callback: Optional[Callable] = None,
        verbose: bool = True
    ) -> List[OptimizationResult]:
        """Run multi-objective optimization using differential evolution
        Following VIRTUAL_TWIN_IMPLEMENTATION_PLAN_FINAL.md lines 283-358
        
        Args:
            objectives: List of optimization objectives
            constraints: Optional constraints on parameters or objectives
            population_size: Size of population for differential evolution
            generations: Number of generations to evolve
            seed: Random seed for reproducibility
            strategy: Evolution strategy ('best1bin', 'rand1bin', etc.)
            mutation: Mutation factor range
            recombination: Crossover probability
            workers: Number of parallel workers (-1 for all cores)
            callback: Optional callback function
            verbose: Whether to print progress
            
        Returns:
            List of Pareto-optimal solutions

        """
        if verbose:
            logger.info(f"Starting optimization with {len(objectives)} objectives")
            logger.info(f"Population: {population_size}, Generations: {generations}")
        
        # Reset counters
        self.evaluation_count = 0
        self.pareto_front = []
        
        # Build bounds from parameters
        bounds: List[Tuple[float, float]] = []
        param_names: List[str] = []
        for param_name, param in self.PARAMETERS.items():
            bounds.append(param.bounds)
            param_names.append(param_name)
        
        # Create objective function
        def objective_function(x: np.ndarray) -> float:
            """Evaluate solution and return objective values"""
            self.evaluation_count += 1
            
            # Map array to parameter dict
            params: Dict[str, float] = {name: val for name, val in zip(param_names, x)}
            
            # Simulate with parameters (or use mock if no runner)
            if self.simulation_runner:
                results = self.simulation_runner.simulate(params, seed=seed)
            else:
                # Mock simulation for testing
                results = self._mock_simulation(params)
            
            # Calculate objective values
            obj_values: List[float] = []
            for obj in objectives:
                value = self._calculate_objective(results, obj)
                # Negate if maximizing (differential_evolution minimizes)
                if obj.direction == 'maximize':
                    value = -value
                obj_values.append(value * obj.weight)
            
            # For multi-objective, use weighted sum (simple approach)
            # More sophisticated would use NSGA-II ranking
            if len(obj_values) > 1:
                return sum(obj_values)
            else:
                return obj_values[0]
        
        # Build constraints if provided
        scipy_constraints: List[Any] = []
        if constraints:
            scipy_constraints = self._build_constraints(constraints, param_names)
        
        # Run differential evolution
        result = differential_evolution(
            objective_function,
            bounds,
            strategy=strategy,
            maxiter=generations,
            popsize=population_size,
            tol=0.01,  # TODO: HARDCODED - tolerance
            mutation=mutation,
            recombination=recombination,
            seed=seed,
            callback=callback,
            disp=verbose,
            polish=True,
            init='latinhypercube',
            atol=0,
            updating='deferred' if workers != 1 else 'immediate',
            workers=workers,
            constraints=scipy_constraints
        )
        
        # Convert result to OptimizationResult
        opt_params: Dict[str, float] = {name: val for name, val in zip(param_names, result.x)}
        
        # Get final objective values
        if self.simulation_runner:
            final_results = self.simulation_runner.simulate(opt_params, seed=seed)
        else:
            final_results = self._mock_simulation(opt_params)
        
        obj_values: Dict[str, float] = {}
        for obj in objectives:
            value = self._calculate_objective(final_results, obj)
            obj_values[obj.name] = value
        
        solution = OptimizationResult(
            parameters=opt_params,
            objectives=obj_values,
            success=result.success,
            message=result.message,
            iterations=result.nit,
            evaluations=result.nfev,
            run_id=f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # For true multi-objective, would return Pareto front
        # For now, return single best solution
        return [solution]
    
    def optimize_multi_objective(
        self,
        objectives: List[OptimizationObjective],
        constraints: Optional[Dict[str, Any]] = None,
        population_size: int = 100,
        generations: int = 200,
        seed: int = 42,
        verbose: bool = True
    ) -> List[OptimizationResult]:
        """True multi-objective optimization with Pareto front
        Uses multiple differential evolution runs with different weights
        
        This is a simplified version - full NSGA-II would be better
        but scipy doesn't have it built-in
        """
        pareto_solutions = []
        
        # Generate weight combinations for scalarization
        n_weights = min(population_size, 20)  # Limit for practicality
        weights_set = self._generate_weights(len(objectives), n_weights)
        
        for i, weights in enumerate(weights_set):
            if verbose and i % 5 == 0:
                logger.info(f"Evaluating weight combination {i+1}/{len(weights_set)}")
            
            # Apply weights to objectives
            weighted_objectives = []
            for obj, w in zip(objectives, weights):
                weighted_obj = OptimizationObjective(
                    name=obj.name,
                    direction=obj.direction,
                    weight=w,
                    target=obj.target
                )
                weighted_objectives.append(weighted_obj)
            
            # Run optimization with these weights
            solutions = self.optimize(
                weighted_objectives,
                constraints=constraints,
                population_size=20,  # Smaller for each run
                generations=50,  # Fewer generations per run
                seed=seed + i,
                verbose=False
            )
            
            if solutions[0].success:
                solutions[0].pareto_rank = None  # Will calculate later
                pareto_solutions.append(solutions[0])
        
        # Filter to get Pareto front
        pareto_front = self._extract_pareto_front(pareto_solutions, objectives)
        
        # Assign Pareto ranks
        for i, sol in enumerate(pareto_front):
            sol.pareto_rank = 1  # All in front have rank 1
        
        if verbose:
            logger.info(f"Found {len(pareto_front)} Pareto-optimal solutions")
        
        return pareto_front
    
    def validate_with_monte_carlo(
        self,
        solution: OptimizationResult,
        n_simulations: int = 1000,  # TODO: HARDCODED - default simulations
        confidence_level: float = 0.95  # TODO: HARDCODED - default confidence level
    ) -> OptimizationResult:
        """Validate solution with Monte Carlo simulation
        Following VIRTUAL_TWIN_IMPLEMENTATION_PLAN_FINAL.md lines 351-357
        
        Args:
            solution: Solution to validate
            n_simulations: Number of Monte Carlo runs
            confidence_level: Confidence level for interval
            
        Returns:
            Updated solution with confidence intervals

        """
        if not self.simulation_runner:
            # Mock validation
            solution.confidence_interval = (
                solution.objectives.get('oee', 0) * 0.95,
                solution.objectives.get('oee', 0) * 1.05
            )
            return solution
        
        # Run multiple simulations with different seeds
        objective_samples: Dict[str, List[float]] = {obj_name: [] for obj_name in solution.objectives}
        
        for i in range(n_simulations):
            seed: int = np.random.randint(0, 2**32)  # TODO: HARDCODED - seed range
            results = self.simulation_runner.simulate(solution.parameters, seed=seed)
            
            for obj_name in solution.objectives:
                value = self._calculate_objective_by_name(results, obj_name)
                objective_samples[obj_name].append(value)
        
        # Calculate confidence intervals
        alpha: float = 1 - confidence_level
        for obj_name, samples in objective_samples.items():
            lower: float = float(np.percentile(samples, alpha/2 * 100))
            upper: float = float(np.percentile(samples, (1 - alpha/2) * 100))
            mean: float = float(np.mean(samples))
            std: float = float(np.std(samples))
            
            # Update solution with statistics
            solution.objectives[obj_name] = mean
            if obj_name == 'oee':  # Primary metric
                solution.confidence_interval = (lower, upper)
        
        return solution
    
    def _mock_simulation(self, params: Dict[str, float]) -> Dict[str, Any]:
        """Mock simulation for testing without actual simulator"""
        # Simple model for testing
        micro_stop: float = params.get('micro_stop_probability', 0.15)  # TODO: HARDCODED - default value
        performance: float = params.get('performance_factor', 0.85)  # TODO: HARDCODED - default value
        scrap: float = params.get('scrap_multiplier', 2.0)  # TODO: HARDCODED - default value
        material: float = params.get('material_reliability', 0.85)  # TODO: HARDCODED - default value
        cascade: float = params.get('cascade_sensitivity', 0.5)  # TODO: HARDCODED - default value
        
        # Mock KPIs based on parameters
        availability: float = max(0, min(100, 95 - micro_stop * 100))  # TODO: HARDCODED - formula
        quality: float = max(0, min(100, 100 / scrap))
        oee: float = (availability * performance * quality) / 100
        
        # Mock energy and throughput
        energy_per_unit: float = 0.5 + cascade * 0.2  # TODO: HARDCODED - energy formula
        throughput: float = 1000 * performance * material  # TODO: HARDCODED - base throughput 1000
        
        return {
            'oee': oee,
            'availability': availability,
            'performance': performance * 100,
            'quality': quality,
            'energy_per_unit': energy_per_unit,
            'throughput': throughput,
            'scrap_rate': (scrap - 1) * 0.05
        }
    
    def _calculate_objective(
        self,
        results: Dict[str, Any],
        objective: OptimizationObjective
    ) -> float:
        """Calculate objective value from simulation results"""
        return self._calculate_objective_by_name(results, objective.name)
    
    def _calculate_objective_by_name(
        self,
        results: Dict[str, Any],
        objective_name: str
    ) -> float:
        """Calculate objective value by name"""
        # Map objective names to result keys
        objective_mapping = {
            'oee': 'oee',
            'energy': 'energy_per_unit',
            'throughput': 'throughput',
            'quality': 'quality',
            'availability': 'availability',
            'performance': 'performance',
            'cost': 'energy_per_unit',  # Simplified
            'scrap': 'scrap_rate'
        }
        
        key = objective_mapping.get(objective_name, objective_name)
        return results.get(key, 0.0)
    
    def _build_constraints(
        self,
        constraints: Dict[str, Any],
        param_names: List[str]
    ) -> List:
        """Build scipy constraints from constraint dict"""
        scipy_constraints = []
        
        # Parameter bounds constraints
        for param_name, bounds in constraints.items():
            if param_name in param_names:
                idx = param_names.index(param_name)
                if isinstance(bounds, tuple) and len(bounds) == 2:
                    # Already handled by bounds parameter
                    pass
        
        # Add any functional constraints here
        # Example: quality >= 95%
        if 'min_quality' in constraints:
            min_qual = constraints['min_quality']
            
            def quality_constraint(x):
                params = {name: val for name, val in zip(param_names, x)}
                results = self._mock_simulation(params)
                return results['quality'] - min_qual
            
            scipy_constraints.append(
                NonlinearConstraint(quality_constraint, 0, np.inf)
            )
        
        return scipy_constraints
    
    def _generate_weights(self, n_objectives: int, n_samples: int) -> List[List[float]]:
        """Generate diverse weight combinations for multi-objective optimization"""
        if n_objectives == 1:
            return [[1.0]]
        
        # Use uniform sampling on simplex
        weights_set = []
        for _ in range(n_samples):
            # Random weights that sum to 1
            weights = np.random.random(n_objectives)
            weights = weights / weights.sum()
            weights_set.append(weights.tolist())
        
        # Add corner cases (single objective focus)
        for i in range(n_objectives):
            weights = [0.0] * n_objectives
            weights[i] = 1.0
            weights_set.append(weights)
        
        # Add equal weights
        equal_weight = 1.0 / n_objectives
        weights_set.append([equal_weight] * n_objectives)
        
        return weights_set[:n_samples]
    
    def _extract_pareto_front(
        self,
        solutions: List[OptimizationResult],
        objectives: List[OptimizationObjective]
    ) -> List[OptimizationResult]:
        """Extract Pareto-optimal solutions from all solutions"""
        if not solutions:
            return []
        
        # Build objective matrix
        n_solutions = len(solutions)
        n_objectives = len(objectives)
        obj_matrix = np.zeros((n_solutions, n_objectives))
        
        for i, sol in enumerate(solutions):
            for j, obj in enumerate(objectives):
                value = sol.objectives.get(obj.name, 0)
                # Convert to minimization
                if obj.direction == 'maximize':
                    value = -value
                obj_matrix[i, j] = value
        
        # Find non-dominated solutions
        pareto_indices = []
        for i in range(n_solutions):
            dominated = False
            for j in range(n_solutions):
                if i != j:
                    # Check if solution j dominates solution i
                    if np.all(obj_matrix[j] <= obj_matrix[i]) and np.any(obj_matrix[j] < obj_matrix[i]):
                        dominated = True
                        break
            if not dominated:
                pareto_indices.append(i)
        
        # Return Pareto front
        return [solutions[i] for i in pareto_indices]
    
    def recommend_for_scenario(
        self,
        scenario: str,
        constraints: Optional[Dict[str, Any]] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Generate recommendation for a specific scenario using natural language
        
        Args:
            scenario: Natural language description of optimization goal
            constraints: Optional constraints
            verbose: Whether to print progress
            
        Returns:
            Recommendation with parameters and expected improvements

        """
        # Parse scenario to objectives (simplified)
        objectives = self._parse_scenario_to_objectives(scenario)
        
        # Run optimization
        solutions = self.optimize(
            objectives,
            constraints=constraints,
            population_size=20,
            generations=50,
            verbose=verbose
        )
        
        if not solutions or not solutions[0].success:
            return {
                'error': 'Optimization failed',
                'message': solutions[0].message if solutions else 'No solutions found'
            }
        
        best = solutions[0]
        
        # Generate recommendation
        recommendation = {
            'scenario': scenario,
            'parameters': best.parameters,
            'expected_improvements': best.objectives,
            'confidence': 'High' if best.evaluations > 100 else 'Medium',
            'implementation_steps': self._generate_implementation_steps(best.parameters),
            'risks': self._identify_risks(best.parameters),
            'run_id': best.run_id
        }
        
        return recommendation
    
    def _parse_scenario_to_objectives(self, scenario: str) -> List[OptimizationObjective]:
        """Parse natural language scenario to optimization objectives"""
        scenario_lower = scenario.lower()
        objectives = []
        
        # Simple keyword matching (would use NLP in production)
        if 'energy' in scenario_lower or 'power' in scenario_lower:
            objectives.append(OptimizationObjective('energy', 'minimize', 1.0))
        
        if 'throughput' in scenario_lower or 'production' in scenario_lower:
            objectives.append(OptimizationObjective('throughput', 'maximize', 1.0))
        
        if 'quality' in scenario_lower or 'defect' in scenario_lower:
            objectives.append(OptimizationObjective('quality', 'maximize', 1.0))
        
        if 'oee' in scenario_lower or 'efficiency' in scenario_lower:
            objectives.append(OptimizationObjective('oee', 'maximize', 1.0))
        
        if 'cost' in scenario_lower or 'save' in scenario_lower:
            objectives.append(OptimizationObjective('cost', 'minimize', 1.0))
        
        # Default to OEE if no objectives identified
        if not objectives:
            objectives.append(OptimizationObjective('oee', 'maximize', 1.0))
        
        return objectives
    
    def _generate_implementation_steps(self, parameters: Dict[str, float]) -> List[str]:
        """Generate implementation steps for parameter changes"""
        steps = []
        
        if parameters.get('micro_stop_probability', self.config["parameters"]["micro_stop_probability"]["default"]) < 0.10:
            steps.append("Implement preventive maintenance schedule")
            steps.append("Train operators on micro-stop prevention")
        
        if parameters.get('performance_factor', self.config["parameters"]["performance_factor"]["default"]) > 0.90:
            steps.append("Optimize equipment speed settings")
            steps.append("Review and adjust production targets")
        
        if parameters.get('scrap_multiplier', self.config["parameters"]["scrap_multiplier"]["default"]) < 1.5:
            steps.append("Enhance quality control procedures")
            steps.append("Implement inline inspection systems")
        
        if parameters.get('material_reliability', self.config["parameters"]["material_reliability"]["default"]) > 0.95:
            steps.append("Work with suppliers on material quality")
            steps.append("Implement incoming material inspection")
        
        if parameters.get('cascade_sensitivity', self.config["parameters"]["cascade_sensitivity"]["default"]) < 0.3:
            steps.append("Increase buffer capacity between equipment")
            steps.append("Implement decoupling strategies")
        
        return steps if steps else ["Review and implement parameter adjustments"]
    
    def _identify_risks(self, parameters: Dict[str, float]) -> List[str]:
        """Identify risks associated with parameter changes"""
        risks = []
        
        if parameters.get('performance_factor', self.config["parameters"]["performance_factor"]["default"]) > 0.95:
            risks.append("Equipment wear may increase at higher speeds")
        
        if parameters.get('scrap_multiplier', self.config["parameters"]["scrap_multiplier"]["default"]) < 1.2:
            risks.append("Quality improvements may require capital investment")
        
        if parameters.get('cascade_sensitivity', self.config["parameters"]["cascade_sensitivity"]["default"]) < 0.2:
            risks.append("Increased buffer inventory costs")
        
        return risks if risks else ["No significant risks identified"]


# Example usage and testing
