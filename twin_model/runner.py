"""
Simulation runner for the SimPy twin model.

Manages simulation execution, MES data logging, and results aggregation.
"""

import simpy
import random
from typing import List, Dict, Any, Optional, Generator, Union
from dataclasses import dataclass

from .production_line import ProductionLine
from .config import SimulationConfig, ActionableParameters


@dataclass
class SimulationResults:
    """Results from a simulation run.

    Attributes:
        duration_minutes: Total simulation duration in minutes
        mes_data: MES snapshots collected during simulation
        line_summaries: Summary statistics for each line
        kpi_summary: Aggregated KPIs across all lines
    """

    duration_minutes: float
    mes_data: List[Dict[str, Any]]
    line_summaries: Dict[str, Dict[str, Any]]
    kpi_summary: Dict[str, float]


class MESLogger:
    """Logs MES data at regular intervals."""

    def __init__(
        self,
        env: simpy.Environment,
        lines: List[ProductionLine],
        interval_minutes: float,
    ):
        """Initialize MES logger.

        Args:
            env: SimPy environment
            lines: Production lines to monitor
            interval_minutes: Logging interval in minutes
        """
        self.env = env
        self.lines = lines
        self.interval = interval_minutes
        self.data: List[Dict[str, Any]] = []

        # Start logging process
        self.process = env.process(self._logging_loop())

    def _logging_loop(self) -> Generator[simpy.Event, None, None]:
        """Main logging loop."""
        while True:
            # Wait for next logging interval
            yield self.env.timeout(self.interval)

            # Capture snapshots from all lines
            for line in self.lines:
                snapshot = line.capture_mes_snapshot()
                self.data.append(snapshot)

    def get_data(self) -> List[Dict[str, Any]]:
        """Get collected MES data.

        Returns:
            List of MES snapshots
        """
        return self.data


class SimulationRunner:
    """Runs SimPy simulations with configuration."""

    def __init__(self, config: Optional[SimulationConfig] = None):
        """Initialize simulation runner.

        Args:
            config: Simulation configuration (uses default if None)
        """
        self.config = config or SimulationConfig.create_default_config()

    def run_simulation(
        self,
        parameters: Optional[ActionableParameters] = None,
        duration_days: Optional[Union[int, float]] = None,
        seed: Optional[int] = None,
    ) -> SimulationResults:
        """Run a simulation with given parameters.

        Args:
            parameters: Actionable parameters (uses config default if None)
            duration_days: Simulation duration in days (uses config default if None)
            seed: Random seed (uses config default if None)

        Returns:
            SimulationResults with all data and metrics
        """
        # Use provided values or defaults from config
        parameters = parameters or self.config.parameters
        duration_days = duration_days or self.config.duration_days
        seed = seed if seed is not None else self.config.random_seed

        # Set random seed for reproducibility
        if seed is not None:
            random.seed(seed)

        # Create SimPy environment
        env = simpy.Environment()

        # Create production lines
        lines = []
        for line_config in self.config.line_configs:
            line = ProductionLine(env, line_config, parameters)
            lines.append(line)

        # Create MES logger
        mes_logger = MESLogger(
            env=env, lines=lines, interval_minutes=self.config.mes_logging_interval
        )

        # Run simulation
        duration_minutes = duration_days * 24 * 60
        env.run(until=duration_minutes)

        # Collect results
        results = self._compile_results(
            lines=lines,
            mes_data=mes_logger.get_data(),
            duration_minutes=duration_minutes,
        )

        return results

    def _compile_results(
        self,
        lines: List[ProductionLine],
        mes_data: List[Dict[str, Any]],
        duration_minutes: float,
    ) -> SimulationResults:
        """Compile simulation results.

        Args:
            lines: Production lines
            mes_data: MES snapshots
            duration_minutes: Simulation duration

        Returns:
            Compiled SimulationResults
        """
        # Get line summaries
        line_summaries = {}
        for line in lines:
            line_summaries[line.line_id] = line.get_stats_summary()

        # Calculate aggregated KPIs
        kpi_summary = self._calculate_kpis(line_summaries, mes_data)

        return SimulationResults(
            duration_minutes=duration_minutes,
            mes_data=mes_data,
            line_summaries=line_summaries,
            kpi_summary=kpi_summary,
        )

    def _calculate_kpis(
        self, line_summaries: Dict[str, Dict[str, Any]], mes_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate aggregated KPIs.

        Args:
            line_summaries: Summary statistics for each line
            mes_data: MES snapshots

        Returns:
            Dictionary of KPIs
        """
        # Aggregate across all lines
        total_input = 0
        total_output = 0
        total_scrap = 0
        oee_values = []
        availability_values = []
        performance_values = []
        quality_values = []

        for line_id, summary in line_summaries.items():
            total_input += summary["total_input"]
            total_output += summary["total_output"]
            total_scrap += summary["total_scrap"]

            line_oee = summary["line_oee"]
            oee_values.append(line_oee["oee"])
            availability_values.append(line_oee["availability"])
            performance_values.append(line_oee["performance"])
            quality_values.append(line_oee["quality"])

        # Calculate averages
        num_lines = len(line_summaries)

        kpis = {
            "total_units_produced": total_output,
            "total_units_scrapped": total_scrap,
            "total_good_units": total_output,
            "mean_oee": sum(oee_values) / num_lines if num_lines > 0 else 0.0,
            "mean_availability": sum(availability_values) / num_lines
            if num_lines > 0
            else 0.0,
            "mean_performance": sum(performance_values) / num_lines
            if num_lines > 0
            else 0.0,
            "mean_quality": sum(quality_values) / num_lines if num_lines > 0 else 0.0,
            "overall_efficiency": (total_output / total_input * 100)
            if total_input > 0
            else 0.0,
        }

        # Add per-line OEE for tracking
        for line_id, summary in line_summaries.items():
            kpis[f"{line_id}_oee"] = summary["line_oee"]["oee"]

        return kpis

    def run_parameter_sweep(
        self,
        parameter_ranges: Dict[str, List[float]],
        duration_days: int = 1,
        replications: int = 3,
    ) -> List[Dict[str, Any]]:
        """Run parameter sweep for sensitivity analysis.

        Args:
            parameter_ranges: Dictionary of parameter names to value lists
            duration_days: Duration for each simulation
            replications: Number of replications per parameter set

        Returns:
            List of results for each parameter combination
        """
        results = []

        # Generate all parameter combinations
        import itertools

        param_names = list(parameter_ranges.keys())
        param_values = [parameter_ranges[name] for name in param_names]

        for values in itertools.product(*param_values):
            # Create parameter set
            params = ActionableParameters()
            for name, value in zip(param_names, values):
                setattr(params, name, value)

            # Run replications
            for rep in range(replications):
                seed = rep * 1000  # Different seed for each replication
                sim_results = self.run_simulation(
                    parameters=params, duration_days=duration_days, seed=seed
                )

                # Store results with parameter values
                result = {
                    "parameters": {
                        name: value for name, value in zip(param_names, values)
                    },
                    "replication": rep,
                    "kpis": sim_results.kpi_summary,
                }
                results.append(result)

        return results
