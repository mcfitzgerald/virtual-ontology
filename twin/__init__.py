"""
Virtual Twin Module - Manufacturing Digital Twin Simulation & Optimization

This module provides a comprehensive digital twin framework for manufacturing systems,
enabling simulation, optimization, and intelligent recommendation capabilities.

Core Components:
    - SimulationRunner: Execute what-if scenarios and parameter simulations
    - ActionableParameters: Manage and validate simulation parameters
    - TwinStateManager: Track and synchronize virtual twin state
    - ConfigTransformer: Transform parameters into simulation configurations
    - ConfigurationManager: Store and retrieve configuration history

Analysis Components:
    - OptimizationEngine: Multi-objective optimization using NSGA-II
    - RecommendationEngine: Generate scenario-based recommendations
    - CostImpactCalculator: Financial impact and ROI analysis

Support Components:
    - DisambiguationHelper: Natural language query interpretation
    - SyncHealthMonitor: Monitor synchronization health
    - LineCouplingModel: Model production line interactions

Usage:
    from twin import SimulationRunner, ActionableParameters
    
    # Run a simulation
    runner = SimulationRunner()
    params = ActionableParameters()
    params.set_value("micro_stop_probability", 0.05)
    result = runner.run_simulation(params)
"""

# Core Components - Main simulation and state management
from .simulation_runner import SimulationRunner, SimulationRun
from .actionable_parameters import ActionableParameters, ActionableParameter
from .twin_state import TwinStateManager
from .config_transformer import ConfigTransformer
from .config_manager import ConfigurationManager

# Analysis Components - Optimization and recommendations
from .optimization_engine import OptimizationEngine
from .recommendation_engine import RecommendationEngine
from .cost_impact_calculator import CostImpactCalculator

# Support Components - Helpers and utilities
from .disambiguation import DisambiguationHelper
from .sync_health import SyncHealthMonitor, SyncHealthStatus
from .line_coupling_model import LineCoupling

# Version
__version__ = "1.0.0"

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
    "CostImpactCalculator",
    # Support
    "DisambiguationHelper",
    "SyncHealthMonitor",
    "SyncHealthStatus",
    "LineCoupling",
]