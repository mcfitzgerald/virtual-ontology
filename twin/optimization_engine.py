"""Twin Optimization Engine
Multi-objective optimization using scipy's differential evolution algorithm
Following VIRTUAL_TWIN_IMPLEMENTATION_PLAN_FINAL.md Phase 4 specifications
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from scipy.optimize import (
    differential_evolution,
    NonlinearConstraint,
    LinearConstraint,
    Bounds,
)
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

    def __init__(self, simulation_runner: Optional[Any] = None) -> None:
        """Initialize optimization engine

        Args:
            simulation_runner: Optional simulation runner for evaluating solutions

        """
        self.loader = ConfigLoader()
        self.config = self.loader.config

        # Dynamically build parameters from configuration
        self.PARAMETERS: Dict[str, ActionableParameter] = {}
        for param_name, param_config in self.config["parameters"].items():
            self.PARAMETERS[param_name] = ActionableParameter(
                name=param_name,
                bounds=(param_config["bounds"]["min"], param_config["bounds"]["max"]),
                unit=param_config["unit"],
                causal_effect=param_config["causal_effect"],
                invariants=param_config.get("invariants", []),
            )

        self.simulation_runner: Optional[Any] = simulation_runner
        self.evaluation_count: int = 0
        self.best_solution: Optional[OptimizationResult] = None
        self.pareto_front: List[OptimizationResult] = []

    def optimize(
        self,
        objectives: List[OptimizationObjective],
        constraints: Optional[Dict[str, Any]] = None,
        population_size: Optional[int] = None,
        generations: Optional[int] = None,
        seed: Optional[int] = None,
        strategy: str = "best1bin",
        mutation: Optional[Tuple[float, float]] = None,
        recombination: Optional[float] = None,
        workers: int = 1,
        callback: Optional[Callable] = None,
        verbose: bool = True,
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
        # Set defaults from configuration
        opt_config = self.config["optimization"]["algorithm"]
        if population_size is None:
            population_size = opt_config["population_size"]
        if generations is None:
            generations = opt_config["generations"]
        if seed is None:
            seed = opt_config["seed"]
        if mutation is None:
            mutation = (opt_config["mutation_min"], opt_config["mutation_max"])
        if recombination is None:
            recombination = opt_config["recombination"]

        if verbose:
            logger.info(f"Starting optimization with {len(objectives)} objectives")
            for obj in objectives:
                logger.info(
                    f"  - Objective: {obj.name}, Direction: {obj.direction}, Weight: {obj.weight}"
                )
            logger.info(f"Population: {population_size}, Generations: {generations}")

        # Callback for progress logging
        def progress_callback(intermediate_result):
            generation = intermediate_result.nit
            best_fitness = intermediate_result.fun
            logger.info(
                f"Optimization Generation: {generation + 1}/{generations}, Best Fitness: {best_fitness:.4f}"
            )

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
            params_dict: Dict[str, float] = {
                name: val for name, val in zip(param_names, x)
            }

            # Convert dict to ActionableParameters object
            from .actionable_parameters import ActionableParameters

            params = ActionableParameters()
            for name, value in params_dict.items():
                params.set_value(name, value)

            # Simulate with parameters (or use mock if no runner)
            if self.simulation_runner:
                sim_result = self.simulation_runner.run_simulation(params, seed=seed)
                results = sim_result.kpi_summary
            else:
                # Mock simulation for testing
                results = self._mock_simulation(params_dict)

            # Calculate objective values
            obj_values: List[float] = []
            for obj in objectives:
                value = self._calculate_objective(results, obj)
                # Negate if maximizing (differential_evolution minimizes)
                if obj.direction == "maximize":
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
            tol=self.config["optimization"]["algorithm"]["tolerance"],
            mutation=mutation,
            recombination=recombination,
            seed=seed,
            callback=progress_callback if verbose and not callback else callback,
            disp=False,  # Use our own callback for logging
            polish=True,
            init="latinhypercube",
            atol=0,
            updating="deferred" if workers != 1 else "immediate",
            workers=workers,
            constraints=scipy_constraints,
        )

        # Convert result to OptimizationResult
        opt_params: Dict[str, float] = {
            name: val for name, val in zip(param_names, result.x)
        }

        # Get final objective values
        if self.simulation_runner:
            from .actionable_parameters import ActionableParameters

            final_params = ActionableParameters()
            for name, value in opt_params.items():
                final_params.set_value(name, value)
            final_sim_result = self.simulation_runner.run_simulation(
                final_params, seed=seed
            )
            final_results = final_sim_result.kpi_summary
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
            run_id=f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )

        # For true multi-objective, would return Pareto front
        # For now, return single best solution
        return [solution]

    def optimize_multi_objective(
        self,
        objectives: List[OptimizationObjective],
        constraints: Optional[Dict[str, Any]] = None,
        population_size: Optional[int] = None,
        generations: Optional[int] = None,
        seed: Optional[int] = None,
        verbose: bool = True,
    ) -> List[OptimizationResult]:
        """True multi-objective optimization with Pareto front
        Uses multiple differential evolution runs with different weights

        This is a simplified version - full NSGA-II would be better
        but scipy doesn't have it built-in
        """
        # Set defaults from configuration
        mo_config = self.config["optimization"]["multi_objective"]
        if population_size is None:
            population_size = mo_config["population_size"]
        if generations is None:
            generations = mo_config["generations"]
        if seed is None:
            seed = mo_config["seed"]

        pareto_solutions = []

        # Generate weight combinations for scalarization
        n_weights = min(population_size, mo_config["n_weights_limit"])
        weights_set = self._generate_weights(len(objectives), n_weights)

        for i, weights in enumerate(weights_set):
            if verbose and i % 5 == 0:
                logger.info(f"Evaluating weight combination {i+1}/{len(weights_set)}")

            # Apply weights to objectives
            weighted_objectives = []
            for obj, w in zip(objectives, weights):
                weighted_obj = OptimizationObjective(
                    name=obj.name, direction=obj.direction, weight=w, target=obj.target
                )
                weighted_objectives.append(weighted_obj)

            # Run optimization with these weights
            solutions = self.optimize(
                weighted_objectives,
                constraints=constraints,
                population_size=mo_config["run_population_size"],
                generations=mo_config["run_generations"],
                seed=seed + i,
                verbose=False,
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
        n_simulations: Optional[int] = None,
        confidence_level: Optional[float] = None,
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
        # Set defaults from configuration
        mc_config = self.config["optimization"]["monte_carlo"]
        if n_simulations is None:
            n_simulations = mc_config["n_simulations"]
        if confidence_level is None:
            confidence_level = mc_config["confidence_level"]

        if not self.simulation_runner:
            # Mock validation
            solution.confidence_interval = (
                solution.objectives.get("oee", 0) * 0.95,
                solution.objectives.get("oee", 0) * 1.05,
            )
            return solution

        # Run multiple simulations with different seeds
        objective_samples: Dict[str, List[float]] = {
            obj_name: [] for obj_name in solution.objectives
        }

        for i in range(n_simulations):
            seed: int = np.random.randint(
                0, self.config["optimization"]["monte_carlo"]["seed_max"]
            )
            from .actionable_parameters import ActionableParameters

            params = ActionableParameters()
            for name, value in solution.parameters.items():
                params.set_value(name, value)
            sim_result = self.simulation_runner.run_simulation(params, seed=seed)
            results = sim_result.kpi_summary

            for obj_name in solution.objectives:
                value = self._calculate_objective_by_name(results, obj_name)
                objective_samples[obj_name].append(value)

        # Calculate confidence intervals
        alpha: float = 1 - confidence_level
        for obj_name, samples in objective_samples.items():
            lower: float = float(np.percentile(samples, alpha / 2 * 100))
            upper: float = float(np.percentile(samples, (1 - alpha / 2) * 100))
            mean: float = float(np.mean(samples))
            std: float = float(np.std(samples))

            # Update solution with statistics
            solution.objectives[obj_name] = mean
            if obj_name == "oee":  # Primary metric
                solution.confidence_interval = (lower, upper)

        return solution

    def _mock_simulation(self, params: Dict[str, float]) -> Dict[str, Any]:
        """Mock simulation for testing without actual simulator"""
        # Simple model for testing
        defaults = self.config["optimization"]["approximation_defaults"]
        micro_stop: float = params.get(
            "micro_stop_probability", defaults["micro_stop_probability"]
        )
        performance: float = params.get(
            "performance_factor", defaults["performance_factor"]
        )
        scrap: float = params.get("scrap_multiplier", defaults["scrap_multiplier"])
        material: float = params.get(
            "material_reliability", defaults["material_reliability"]
        )
        cascade: float = params.get(
            "cascade_sensitivity", defaults["cascade_sensitivity"]
        )

        # Mock KPIs based on parameters
        base_availability = self.config["optimization"]["approximation_defaults"][
            "base_availability"
        ]
        availability: float = max(0, min(100, base_availability - micro_stop * 100))
        quality: float = max(0, min(100, 100 / scrap))
        oee: float = (availability * performance * quality) / 100

        # Mock energy and throughput
        energy_base = self.config["optimization"]["approximation_defaults"][
            "energy_base"
        ]
        energy_cascade_factor = self.config["optimization"]["approximation_defaults"][
            "energy_cascade_factor"
        ]
        base_throughput = self.config["optimization"]["approximation_defaults"][
            "base_throughput"
        ]

        energy_per_unit: float = energy_base + cascade * energy_cascade_factor
        throughput: float = base_throughput * performance * material

        return {
            "oee": oee,
            "availability": availability,
            "performance": performance * 100,
            "quality": quality,
            "energy_per_unit": energy_per_unit,
            "throughput": throughput,
            "scrap_rate": (scrap - 1) * 0.05,
        }

    def _calculate_objective(
        self, results: Dict[str, Any], objective: OptimizationObjective
    ) -> float:
        """Calculate objective value from simulation results"""
        return self._calculate_objective_by_name(results, objective.name)

    def _calculate_objective_by_name(
        self, results: Dict[str, Any], objective_name: str
    ) -> float:
        """Calculate objective value by name"""
        # Map objective names to result keys
        objective_mapping = {
            "oee": "oee",
            "energy": "energy_per_unit",
            "throughput": "throughput",
            "quality": "quality",
            "availability": "availability",
            "performance": "performance",
            "cost": "energy_per_unit",  # Simplified
            "scrap": "scrap_rate",
        }

        key = objective_mapping.get(objective_name, objective_name)
        return results.get(key, 0.0)

    def _build_constraints(
        self, constraints: Dict[str, Any], param_names: List[str]
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
        if "min_quality" in constraints:
            min_qual = constraints["min_quality"]

            def quality_constraint(x):
                params = {name: val for name, val in zip(param_names, x)}
                results = self._mock_simulation(params)
                return results["quality"] - min_qual

            scipy_constraints.append(NonlinearConstraint(quality_constraint, 0, np.inf))

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
        objectives: List[OptimizationObjective],
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
                if obj.direction == "maximize":
                    value = -value
                obj_matrix[i, j] = value

        # Find non-dominated solutions
        pareto_indices = []
        for i in range(n_solutions):
            dominated = False
            for j in range(n_solutions):
                if i != j:
                    # Check if solution j dominates solution i
                    if np.all(obj_matrix[j] <= obj_matrix[i]) and np.any(
                        obj_matrix[j] < obj_matrix[i]
                    ):
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
        verbose: bool = True,
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

        # Set defaults from configuration
        rs_config = self.config["optimization"]["recommendation_scenario"]

        # Run optimization
        solutions = self.optimize(
            objectives,
            constraints=constraints,
            population_size=rs_config["population_size"],
            generations=rs_config["generations"],
            verbose=verbose,
        )

        if not solutions or not solutions[0].success:
            return {
                "error": "Optimization failed",
                "message": solutions[0].message if solutions else "No solutions found",
            }

        best = solutions[0]

        # Generate recommendation
        recommendation = {
            "scenario": scenario,
            "parameters": best.parameters,
            "expected_improvements": best.objectives,
            "confidence": "High" if best.evaluations > 100 else "Medium",
            "implementation_steps": self._generate_implementation_steps(
                best.parameters
            ),
            "risks": self._identify_risks(best.parameters),
            "run_id": best.run_id,
        }

        return recommendation

    def _parse_scenario_to_objectives(
        self, scenario: str
    ) -> List[OptimizationObjective]:
        """Parse natural language scenario to optimization objectives"""
        scenario_lower = scenario.lower()
        objectives = []
        rec_config = self.config["recommendation"]

        for obj_name, config in rec_config["scenario_keywords"].items():
            if any(keyword in scenario_lower for keyword in config["keywords"]):
                objectives.append(
                    OptimizationObjective(
                        name=config["objective"]["name"],
                        direction=config["objective"]["direction"],
                        weight=config["objective"]["weight"],
                    )
                )

        # Default to OEE if no objectives identified
        if not objectives:
            default_obj = rec_config["default_objective"]
            objectives.append(
                OptimizationObjective(
                    name=default_obj["name"],
                    direction=default_obj["direction"],
                    weight=default_obj["weight"],
                )
            )

        return objectives

    def _generate_implementation_steps(self, parameters: Dict[str, float]) -> List[str]:
        """Generate implementation steps for parameter changes"""
        steps = []
        rec_config = self.config["recommendation"]

        for param_name, checks in rec_config["implementation_steps"].items():
            param_value = parameters.get(
                param_name, self.config["parameters"][param_name]["default"]
            )
            for check in checks:
                if (check["operator"] == "<" and param_value < check["threshold"]) or (
                    check["operator"] == ">" and param_value > check["threshold"]
                ):
                    steps.extend(check["steps"])

        return steps if steps else rec_config["default_implementation_steps"]

    def _identify_risks(self, parameters: Dict[str, float]) -> List[str]:
        """Identify risks associated with parameter changes"""
        risks = []
        rec_config = self.config["recommendation"]

        for param_name, checks in rec_config["risks"].items():
            param_value = parameters.get(
                param_name, self.config["parameters"][param_name]["default"]
            )
            for check in checks:
                if (check["operator"] == "<" and param_value < check["threshold"]) or (
                    check["operator"] == ">" and param_value > check["threshold"]
                ):
                    risks.extend(check["risks"])

        return risks if risks else rec_config["default_risks"]


# Example usage and testing
