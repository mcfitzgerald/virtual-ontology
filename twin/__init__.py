"""Virtual Twin Module - Manufacturing Digital Twin Simulation & Optimization

This module provides a comprehensive digital twin framework for manufacturing systems,
enabling simulation, optimization, and intelligent recommendation capabilities.

Enhanced with:
    - pymoo for robust multi-objective optimization (NSGA-II)
    - PyMC for Bayesian Monte Carlo analysis
    - Monte Carlo wrapper for uncertainty analysis

Core Components:
    - SimulationRunner: Execute what-if scenarios with Monte Carlo support
    - ActionableParameters: Manage and validate simulation parameters
    - TwinStateManager: Track and synchronize virtual twin state
    - ConfigTransformer: Transform parameters into simulation configurations
    - ConfigurationManager: Store and retrieve configuration history

Analysis Components:
    - OptimizationEngine: Single/weighted multi-objective optimization
    - RecommendationEngine: pymoo-based NSGA-II multi-objective optimization
    - CostImpactCalculator: PyMC-based Bayesian ROI analysis

Support Components:
    - SyncHealthMonitor: Monitor synchronization health
    - LineCouplingModel: Model production line interactions

Usage:
    from twin import SimulationRunner, ActionableParameters, RecommendationEngine
    
    # Run a Monte Carlo simulation
    runner = SimulationRunner()
    params = ActionableParameters()
    uncertainty = {"micro_stop_probability": (-0.1, 0.1)}  # ±10%
    mc_results = runner.run_monte_carlo_simulation(params, uncertainty, n_simulations=100)
    
    # Run pymoo optimization
    engine = RecommendationEngine()
    results = engine.optimize(objectives, population_size=50, generations=100)
"""

# Core Components - Main simulation and state management
from .simulation_runner import SimulationRunner, SimulationRun
from .actionable_parameters import ActionableParameters, ActionableParameter
from .twin_state import TwinStateManager
from .config_transformer import ConfigTransformer
from .config_manager import ConfigurationManager

# Analysis Components - Optimization and recommendations
from .optimization_engine import OptimizationEngine
from .recommendation_engine import RecommendationEngine, Objective, OptimizationResult, ManufacturingProblem
from .cost_impact_calculator import CostImpactCalculator, CostParameters

# Support Components - Helpers and utilities
from .sync_health import SyncHealthMonitor, SyncHealthStatus
from .line_coupling_model import LineCoupling

# Version - Updated for pymoo/PyMC enhancements
__version__ = "1.1.0"

# Public API
__all__ = [
    # Core
    "SimulationRunner",
    "SimulationRun",
    "ActionableParameters", 
    "ActionableParameter",
    "TwinStateManager",
    "ConfigTransformer",
    "ConfigurationManager",
    # Analysis
    "OptimizationEngine",
    "RecommendationEngine",
    "Objective",
    "OptimizationResult",
    "ManufacturingProblem",
    "CostImpactCalculator",
    "CostParameters",
    # Support
    "SyncHealthMonitor",
    "SyncHealthStatus",
    "LineCoupling",
]