"""
Recommendation Engine with Multi-Objective Optimization
Uses NSGA-II algorithm for finding Pareto-optimal configurations
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass
import json
import sqlite3
from datetime import datetime
import sys
import os

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


class RecommendationEngine:
    """
    Multi-objective optimization engine for virtual twin recommendations
    Implements NSGA-II algorithm with constraints
    """
    
    def __init__(
        self,
        simulation_runner: Optional[SimulationRunner] = None,
        state_manager: Optional[TwinStateManager] = None
    ):
        self.runner = simulation_runner or SimulationRunner()
        self.state_manager = state_manager or TwinStateManager()
        self.cached_evaluations = {}
        
    def optimize(
        self,
        objectives: List[Objective],
        constraints: Optional[Dict[str, Tuple[float, float]]] = None,
        population_size: int = 50,
        generations: int = 100,
        seed: int = 42,
        verbose: bool = True
    ) -> List[OptimizationResult]:
        """
        Run multi-objective optimization using NSGA-II
        
        Args:
            objectives: List of optimization objectives
            constraints: Optional parameter constraints
            population_size: Size of population for genetic algorithm
            generations: Number of generations to evolve
            seed: Random seed for reproducibility
            verbose: Print progress information
            
        Returns:
            List of Pareto-optimal solutions
        """
        np.random.seed(seed)
        
        # Initialize population
        population = self._initialize_population(population_size, constraints)
        
        # Evolution loop
        for gen in range(generations):
            if verbose and gen % 10 == 0:
                print(f"Generation {gen}/{generations}")
            
            # Evaluate fitness
            fitness_values = [
                self._evaluate_objectives(ind, objectives)
                for ind in population
            ]
            
            # Non-dominated sorting
            fronts = self._non_dominated_sort(population, fitness_values)
            
            # Calculate crowding distance
            for front in fronts:
                self._calculate_crowding_distance(front, fitness_values)
            
            # Selection and reproduction
            population = self._create_next_generation(
                population, fitness_values, fronts, population_size
            )
        
        # Final evaluation
        final_fitness = [
            self._evaluate_objectives(ind, objectives)
            for ind in population
        ]
        
        # Get Pareto front
        pareto_front = self._get_pareto_front(population, final_fitness)
        
        # Create results
        results = []
        for solution in pareto_front:
            params = self._decode_individual(solution['individual'])
            results.append(OptimizationResult(
                parameters=params,
                objectives=solution['objectives'],
                pareto_rank=solution['rank'],
                crowding_distance=solution['crowding_distance'],
                feasible=self._check_feasibility(params, constraints)
            ))
        
        return sorted(results, key=lambda x: x.crowding_distance, reverse=True)
    
    def _initialize_population(
        self,
        size: int,
        constraints: Optional[Dict[str, Tuple[float, float]]]
    ) -> List[np.ndarray]:
        """Initialize random population within constraints"""
        population = []
        params = ActionableParameters()
        
        for _ in range(size):
            individual = []
            for param_name in params.parameters:
                param = params.parameters[param_name]
                if constraints and param_name in constraints:
                    min_val, max_val = constraints[param_name]
                else:
                    min_val, max_val = param.bounds
                
                # Random value within bounds
                value = np.random.uniform(min_val, max_val)
                individual.append(value)
            
            population.append(np.array(individual))
        
        return population
    
    def _decode_individual(self, individual: np.ndarray) -> Dict[str, float]:
        """Decode individual to parameter dictionary"""
        params = ActionableParameters()
        param_names = list(params.parameters.keys())
        param_list = list(params.parameters.values())
        
        # Ensure values are within bounds
        result = {}
        for i in range(len(individual)):
            min_val, max_val = param_list[i].bounds
            value = float(individual[i])
            # Clip to bounds
            value = np.clip(value, min_val, max_val)
            result[param_names[i]] = value
        
        return result
    
    def _evaluate_objectives(
        self,
        individual: np.ndarray,
        objectives: List[Objective]
    ) -> Dict[str, float]:
        """Evaluate objectives for an individual"""
        # Check cache
        ind_key = tuple(individual)
        if ind_key in self.cached_evaluations:
            return self.cached_evaluations[ind_key]
        
        # Decode to parameters
        param_dict = self._decode_individual(individual)
        
        # Create parameters instance
        params = ActionableParameters()
        for name, value in param_dict.items():
            params.set_value(name, value)
        
        # Simulate (in production, would actually run simulation)
        # For demonstration, use approximation formulas
        kpis = self._approximate_kpis(params)
        
        # Calculate objective values
        obj_values = {}
        for obj in objectives:
            value = kpis.get(obj.kpi_name, 0.0)
            
            # Apply direction
            if obj.direction == 'minimize':
                obj_values[obj.name] = value * obj.weight
            else:  # maximize
                obj_values[obj.name] = -value * obj.weight  # Negate for minimization
        
        # Cache result
        self.cached_evaluations[ind_key] = obj_values
        
        return obj_values
    
    def _approximate_kpis(self, params: ActionableParameters) -> Dict[str, float]:
        """
        Approximate KPIs based on parameters
        Uses simplified models for demonstration
        """
        values = params.get_all_values()
        
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
    
    def _non_dominated_sort(
        self,
        population: List[np.ndarray],
        fitness_values: List[Dict[str, float]]
    ) -> List[List[int]]:
        """Perform non-dominated sorting (NSGA-II)"""
        n = len(population)
        fronts = [[]]
        
        # Initialize dominance counts and dominated solutions
        domination_count = [0] * n
        dominated_solutions = [[] for _ in range(n)]
        
        # Compare all pairs
        for i in range(n):
            for j in range(i + 1, n):
                if self._dominates(fitness_values[i], fitness_values[j]):
                    dominated_solutions[i].append(j)
                    domination_count[j] += 1
                elif self._dominates(fitness_values[j], fitness_values[i]):
                    dominated_solutions[j].append(i)
                    domination_count[i] += 1
        
        # Find first front
        for i in range(n):
            if domination_count[i] == 0:
                fronts[0].append(i)
        
        # Find remaining fronts
        current_front = 0
        while current_front < len(fronts) and fronts[current_front]:
            next_front = []
            for i in fronts[current_front]:
                for j in dominated_solutions[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        next_front.append(j)
            
            if next_front:
                fronts.append(next_front)
            current_front += 1
        
        # Remove empty fronts
        return [f for f in fronts if f]
    
    def _dominates(self, fitness1: Dict[str, float], fitness2: Dict[str, float]) -> bool:
        """Check if fitness1 dominates fitness2"""
        better_in_any = False
        for key in fitness1:
            # Skip non-objective keys
            if key == 'crowding_distance':
                continue
            if fitness1[key] > fitness2[key]:  # All objectives minimized
                return False
            elif fitness1[key] < fitness2[key]:
                better_in_any = True
        return better_in_any
    
    def _calculate_crowding_distance(
        self,
        front: List[int],
        fitness_values: List[Dict[str, float]]
    ):
        """Calculate crowding distance for solutions in a front"""
        if len(front) <= 2:
            for idx in front:
                fitness_values[idx]['crowding_distance'] = float('inf')
            return
        
        # Initialize distances
        for idx in front:
            fitness_values[idx]['crowding_distance'] = 0
        
        # Calculate for each objective
        objectives = list(fitness_values[0].keys())
        objectives = [o for o in objectives if o != 'crowding_distance']
        
        for obj in objectives:
            # Sort by objective
            sorted_indices = sorted(front, key=lambda x: fitness_values[x][obj])
            
            # Boundary points get infinite distance
            fitness_values[sorted_indices[0]]['crowding_distance'] = float('inf')
            fitness_values[sorted_indices[-1]]['crowding_distance'] = float('inf')
            
            # Calculate range
            obj_range = (
                fitness_values[sorted_indices[-1]][obj] -
                fitness_values[sorted_indices[0]][obj]
            )
            
            if obj_range == 0:
                continue
            
            # Calculate distances
            for i in range(1, len(sorted_indices) - 1):
                idx = sorted_indices[i]
                distance = (
                    fitness_values[sorted_indices[i + 1]][obj] -
                    fitness_values[sorted_indices[i - 1]][obj]
                ) / obj_range
                
                fitness_values[idx]['crowding_distance'] += distance
    
    def _create_next_generation(
        self,
        population: List[np.ndarray],
        fitness_values: List[Dict[str, float]],
        fronts: List[List[int]],
        pop_size: int
    ) -> List[np.ndarray]:
        """Create next generation using tournament selection and crossover"""
        next_population = []
        
        # Add fronts until population is filled
        for front in fronts:
            if len(next_population) + len(front) <= pop_size:
                for idx in front:
                    next_population.append(population[idx])
            else:
                # Sort by crowding distance and add best
                sorted_front = sorted(
                    front,
                    key=lambda x: fitness_values[x].get('crowding_distance', 0),
                    reverse=True
                )
                for idx in sorted_front[:pop_size - len(next_population)]:
                    next_population.append(population[idx])
                break
        
        # Apply genetic operators
        offspring = []
        while len(offspring) < pop_size:
            # Tournament selection
            parent1 = self._tournament_selection(next_population)
            parent2 = self._tournament_selection(next_population)
            
            # Crossover
            child1, child2 = self._crossover(parent1, parent2)
            
            # Mutation
            child1 = self._mutate(child1)
            child2 = self._mutate(child2)
            
            offspring.extend([child1, child2])
        
        return offspring[:pop_size]
    
    def _tournament_selection(
        self,
        population: List[np.ndarray],
        tournament_size: int = 3
    ) -> np.ndarray:
        """Select individual using tournament selection"""
        indices = np.random.choice(len(population), tournament_size, replace=False)
        tournament = [population[i] for i in indices]
        return tournament[np.random.randint(len(tournament))]
    
    def _crossover(
        self,
        parent1: np.ndarray,
        parent2: np.ndarray,
        crossover_rate: float = 0.9
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Simulated binary crossover (SBX)"""
        if np.random.random() > crossover_rate:
            return parent1.copy(), parent2.copy()
        
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        # SBX crossover
        eta = 20  # Distribution index
        for i in range(len(parent1)):
            if np.random.random() < 0.5:
                if abs(parent1[i] - parent2[i]) > 1e-10:
                    beta = self._calculate_beta(eta)
                    child1[i] = 0.5 * ((1 + beta) * parent1[i] + (1 - beta) * parent2[i])
                    child2[i] = 0.5 * ((1 - beta) * parent1[i] + (1 + beta) * parent2[i])
        
        return child1, child2
    
    def _calculate_beta(self, eta: float) -> float:
        """Calculate beta for SBX crossover"""
        u = np.random.random()
        if u <= 0.5:
            return (2 * u) ** (1 / (eta + 1))
        else:
            return (1 / (2 * (1 - u))) ** (1 / (eta + 1))
    
    def _mutate(
        self,
        individual: np.ndarray,
        mutation_rate: float = 0.1
    ) -> np.ndarray:
        """Polynomial mutation"""
        mutated = individual.copy()
        eta = 20  # Distribution index
        
        params = ActionableParameters()
        param_list = list(params.parameters.values())
        
        for i in range(len(mutated)):
            if np.random.random() < mutation_rate:
                # Get bounds
                min_val, max_val = param_list[i].bounds
                
                # Polynomial mutation
                delta = self._calculate_delta(eta)
                mutated[i] = mutated[i] + delta * (max_val - min_val)
                
                # Ensure within bounds
                mutated[i] = np.clip(mutated[i], min_val, max_val)
        
        return mutated
    
    def _calculate_delta(self, eta: float) -> float:
        """Calculate delta for polynomial mutation"""
        u = np.random.random()
        if u < 0.5:
            return (2 * u) ** (1 / (eta + 1)) - 1
        else:
            return 1 - (2 * (1 - u)) ** (1 / (eta + 1))
    
    def _check_feasibility(
        self,
        parameters: Dict[str, float],
        constraints: Optional[Dict[str, Tuple[float, float]]]
    ) -> bool:
        """Check if parameters satisfy constraints"""
        if not constraints:
            return True
        
        for param, (min_val, max_val) in constraints.items():
            if param in parameters:
                if parameters[param] < min_val or parameters[param] > max_val:
                    return False
        return True
    
    def _get_pareto_front(
        self,
        population: List[np.ndarray],
        fitness_values: List[Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """Extract Pareto front solutions"""
        fronts = self._non_dominated_sort(population, fitness_values)
        
        if not fronts:
            return []
        
        # Calculate crowding distance for first front
        self._calculate_crowding_distance(fronts[0], fitness_values)
        
        # Build result
        pareto_solutions = []
        for idx in fronts[0]:
            pareto_solutions.append({
                'individual': population[idx],
                'objectives': {
                    k: v for k, v in fitness_values[idx].items()
                    if k != 'crowding_distance'
                },
                'rank': 1,
                'crowding_distance': fitness_values[idx].get('crowding_distance', 0)
            })
        
        return pareto_solutions
    
    def recommend_for_scenario(
        self,
        scenario: str,
        save_recommendation: bool = True
    ) -> Dict[str, Any]:
        """
        Generate recommendation for a specific scenario
        
        Args:
            scenario: Scenario description
            save_recommendation: Whether to save to database
            
        Returns:
            Recommendation dictionary
        """
        # Map scenario to objectives
        objectives = self._map_scenario_to_objectives(scenario)
        
        # Run optimization
        results = self.optimize(
            objectives=objectives,
            population_size=30,
            generations=50,
            verbose=False
        )
        
        if not results:
            return {"error": "No feasible solutions found"}
        
        # Select best compromise solution
        best = results[0]  # Highest crowding distance
        
        # Calculate expected improvements
        params = ActionableParameters()
        baseline_kpis = self._approximate_kpis(params)
        
        # Apply recommended parameters
        for name, value in best.parameters.items():
            params.set_value(name, value)
        
        improved_kpis = self._approximate_kpis(params)
        
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
                recommendation_type=f"optimization_{scenario}",
                confidence=0.75,
                notes=f"Multi-objective optimization for: {scenario}"
            )
        
        return {
            "scenario": scenario,
            "recommendation_id": rec_id,
            "parameters": best.parameters,
            "expected_improvements": improvements,
            "objectives_achieved": best.objectives,
            "feasible": best.feasible,
            "confidence": 0.75
        }
    
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
    """Demonstrate multi-objective optimization"""
    print("RECOMMENDATION ENGINE DEMONSTRATION")
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
        population_size=20,
        generations=30,
        verbose=False
    )
    
    print(f"Found {len(results)} Pareto-optimal solutions")
    print("\nTop 3 solutions:")
    for i, result in enumerate(results[:3], 1):
        print(f"\nSolution {i}:")
        print(f"  Energy: {-result.objectives['energy']:.1f} kWh/unit")
        print(f"  Throughput: {-result.objectives['throughput']:.0f} units")
        print(f"  Key parameters:")
        for param, value in result.parameters.items():
            if abs(value - 0.85) > 0.05:  # Show only changed params
                print(f"    {param}: {value:.3f}")
    
    # Test 2: Scenario-based recommendation
    print("\n2. SCENARIO-BASED RECOMMENDATION")
    print("-" * 40)
    
    scenarios = [
        "optimize for energy efficiency",
        "maximize throughput while maintaining quality",
        "reduce maintenance costs"
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: '{scenario}'")
        recommendation = engine.recommend_for_scenario(scenario, save_recommendation=False)
        
        if "error" not in recommendation:
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
    
    print("\n✅ Recommendation engine demonstrated!")


if __name__ == "__main__":
    demonstrate_recommendation_engine()