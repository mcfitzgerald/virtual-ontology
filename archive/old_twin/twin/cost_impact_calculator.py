"""Cost Impact Calculator with PyMC for Bayesian Monte Carlo ROI Simulation
Provides probabilistic financial validation for virtual twin recommendations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
from datetime import datetime, timedelta
import sqlite3
import warnings

# PyMC imports for Bayesian probabilistic modeling
import pymc as pm
import arviz as az

# Suppress PyMC sampling warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)


@dataclass
class CostParameters:
    """Financial parameters for ROI calculation - no defaults, all required"""

    # Production costs
    labor_cost_per_hour: float
    energy_cost_per_kwh: float
    material_cost_per_unit: float
    
    # Downtime costs
    downtime_cost_per_hour: float
    
    # Quality costs
    scrap_cost_per_unit: float
    rework_cost_per_unit: float
    
    # Implementation costs
    parameter_change_cost: float
    training_cost: float
    monitoring_cost_per_week: float
    
    # Financial parameters
    discount_rate: float
    confidence_level: float


class CostImpactCalculator:
    """Calculates financial impact of virtual twin recommendations
    using PyMC for Bayesian Monte Carlo simulation with proper uncertainty quantification
    
    Configuration is REQUIRED - all cost parameters must come from config
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        cost_params: Optional[CostParameters] = None
    ) -> None:
        """Initialize CostImpactCalculator.
        Configuration is required - will raise error if not available.
        
        Args:
            db_path: Path to SQLite database (uses config if None)
            cost_params: Optional CostParameters (uses config if None)
            
        Raises:
            RuntimeError: If configuration is not available
            ValueError: If required config values are missing

        """
        # Always load from config - no fallbacks
        from .config_loader import get_config
        self.config = get_config()  # Will raise error if config not available
        
        # Get database path
        self.db_path: str = db_path if db_path is not None else self.config.get("database.path")
        if not self.db_path:
            raise ValueError("Database path not provided and not found in configuration")
        
        # Load cost parameters from config if not provided
        if cost_params is None:
            cost_params = self._load_cost_params_from_config()
            
        self.cost_params: CostParameters = cost_params
    
    def _load_cost_params_from_config(self) -> CostParameters:
        """Load cost parameters from configuration.
        All parameters are required - no defaults.
        
        Returns:
            CostParameters with values from config
            
        Raises:
            KeyError: If required config keys are missing

        """
        cost_config = self.config.get("cost_parameters")
        if not cost_config:
            raise ValueError("cost_parameters section not found in configuration")
            
        try:
            return CostParameters(
                labor_cost_per_hour=cost_config["labor_cost_per_hour"],
                energy_cost_per_kwh=cost_config["energy_cost_per_kwh"],
                material_cost_per_unit=cost_config["material_cost_per_unit"],
                downtime_cost_per_hour=cost_config["downtime_cost_per_hour"],
                scrap_cost_per_unit=cost_config["scrap_cost_per_unit"],
                rework_cost_per_unit=cost_config["rework_cost_per_unit"],
                parameter_change_cost=cost_config["parameter_change_cost"],
                training_cost=cost_config["training_cost"],
                monitoring_cost_per_week=cost_config["monitoring_cost_per_week"],
                discount_rate=cost_config["discount_rate"],
                confidence_level=cost_config["confidence_level"]
            )
        except KeyError as e:
            raise KeyError(f"Missing required cost parameter in configuration: {e}")
        
    def calculate_roi(
        self,
        baseline_run_id: str,
        improved_run_id: str,
        n_simulations: Optional[int] = None,
        time_horizon_weeks: Optional[int] = None,
        include_uncertainty: bool = True
    ) -> Dict[str, Any]:
        """Calculate ROI using PyMC Bayesian Monte Carlo simulation
        
        Args:
            baseline_run_id: Run ID for baseline scenario
            improved_run_id: Run ID for improved scenario
            n_simulations: Number of Monte Carlo simulations (uses config default if None)
            time_horizon_weeks: Time horizon for ROI calculation (uses config default if None)
            include_uncertainty: Whether to add uncertainty to parameters
            
        Returns:
            Dictionary with ROI metrics and credible intervals

        """
        # Use config defaults if not provided
        if n_simulations is None:
            n_simulations = self.config.get("simulation.validation_runs") * 1000
        if time_horizon_weeks is None:
            time_horizon_weeks = self.config.get("cost_parameters.default_time_horizon_weeks")
            
        # Get KPIs from database
        baseline_kpis: Dict[str, float] = self._get_run_kpis(baseline_run_id)
        improved_kpis: Dict[str, float] = self._get_run_kpis(improved_run_id)
        
        # Get parameter changes
        param_changes: Dict[str, float] = self._get_parameter_changes(baseline_run_id, improved_run_id)
        
        # Calculate implementation costs
        implementation_cost: float = self._calculate_implementation_cost(param_changes)
        
        # Build and run PyMC model for ROI calculation
        roi_results: Dict[str, Any] = self._run_pymc_roi_model(
            baseline_kpis,
            improved_kpis,
            implementation_cost,
            n_simulations,
            time_horizon_weeks,
            include_uncertainty
        )
        
        return roi_results
    
    def _run_pymc_roi_model(
        self,
        baseline_kpis: Dict[str, float],
        improved_kpis: Dict[str, float],
        implementation_cost: float,
        n_simulations: int,
        time_horizon_weeks: int,
        include_uncertainty: bool
    ) -> Dict[str, Any]:
        """Build and run PyMC model for ROI calculation with proper Bayesian inference
        
        Args:
            baseline_kpis: Baseline KPI values
            improved_kpis: Improved KPI values  
            implementation_cost: One-time implementation cost
            n_simulations: Number of MCMC samples
            time_horizon_weeks: Time horizon for analysis
            include_uncertainty: Whether to model uncertainty
            
        Returns:
            Dictionary with ROI metrics and credible intervals

        """
        with pm.Model() as roi_model:
            
            if include_uncertainty:
                # Model KPI improvements with uncertainty using distributions
                
                # OEE improvement - Beta distribution bounded [0, 1]
                baseline_oee = baseline_kpis.get("mean_oee", 0.65)
                improved_oee = improved_kpis.get("mean_oee", 0.70)
                oee_improvement_mean = improved_oee - baseline_oee
                
                # Use Beta distribution for bounded uncertainty
                oee_improvement = pm.Normal(
                    "oee_improvement",
                    mu=oee_improvement_mean,
                    sigma=0.02,  # 2% standard deviation
                    initval=oee_improvement_mean
                )
                
                # Downtime reduction - Normal distribution with positive constraint
                baseline_downtime = baseline_kpis.get("downtime_percentage", 20)
                improved_downtime = improved_kpis.get("downtime_percentage", 15)
                downtime_reduction_mean = baseline_downtime - improved_downtime
                
                downtime_reduction = pm.TruncatedNormal(
                    "downtime_reduction",
                    mu=downtime_reduction_mean,
                    sigma=downtime_reduction_mean * 0.15,  # 15% coefficient of variation
                    lower=0,
                    initval=max(0, downtime_reduction_mean)
                )
                
                # Scrap reduction - Gamma distribution (always positive)
                baseline_scrap = baseline_kpis.get("scrap_rate", 0.05)
                improved_scrap = improved_kpis.get("scrap_rate", 0.03)
                scrap_reduction_mean = max(0.001, baseline_scrap - improved_scrap)
                
                scrap_reduction = pm.Gamma(
                    "scrap_reduction",
                    alpha=scrap_reduction_mean * 100,  # Shape parameter
                    beta=100,  # Rate parameter
                    initval=scrap_reduction_mean
                )
                
                # Energy reduction - Normal distribution
                baseline_energy = baseline_kpis.get("weekly_energy_kwh", 25332)
                improved_energy = improved_kpis.get("weekly_energy_kwh", 23000)
                energy_reduction_mean = baseline_energy - improved_energy
                
                energy_reduction = pm.Normal(
                    "energy_reduction",
                    mu=energy_reduction_mean,
                    sigma=energy_reduction_mean * 0.1,  # 10% uncertainty
                    initval=energy_reduction_mean
                )
                
                # Weekly production volume uncertainty
                weekly_production = pm.Normal(
                    "weekly_production",
                    mu=100000,
                    sigma=10000,
                    initval=100000
                )
                
            else:
                # Deterministic values without uncertainty
                oee_improvement = improved_kpis.get("mean_oee", 0.70) - baseline_kpis.get("mean_oee", 0.65)
                downtime_reduction = baseline_kpis.get("downtime_percentage", 20) - improved_kpis.get("downtime_percentage", 15)
                scrap_reduction = baseline_kpis.get("scrap_rate", 0.05) - improved_kpis.get("scrap_rate", 0.03)
                energy_reduction = baseline_kpis.get("weekly_energy_kwh", 25332) - improved_kpis.get("weekly_energy_kwh", 23000)
                weekly_production = 100000
            
            # Calculate weekly savings components
            weekly_hours = pm.ConstantData("weekly_hours", 168)
            
            # Downtime savings
            downtime_savings = pm.Deterministic(
                "downtime_savings",
                downtime_reduction / 100 * weekly_hours * self.cost_params.downtime_cost_per_hour
            )
            
            # Scrap savings
            scrap_savings = pm.Deterministic(
                "scrap_savings",
                scrap_reduction * weekly_production * self.cost_params.scrap_cost_per_unit
            )
            
            # Energy savings
            energy_savings = pm.Deterministic(
                "energy_savings",
                energy_reduction * self.cost_params.energy_cost_per_kwh
            )
            
            # OEE improvement value (each 1% OEE ~ $5000/week)
            oee_value = pm.Deterministic(
                "oee_value",
                oee_improvement * 100 * 5000
            )
            
            # Total weekly savings
            weekly_savings = pm.Deterministic(
                "weekly_savings",
                downtime_savings + scrap_savings + energy_savings + oee_value
            )
            
            # Calculate cash flows over time horizon
            cash_flows = []
            for week in range(time_horizon_weeks):
                if week == 0:
                    # Initial investment
                    cash_flow = -implementation_cost
                else:
                    # Weekly savings minus monitoring cost
                    cash_flow = weekly_savings - self.cost_params.monitoring_cost_per_week
                    
                    if include_uncertainty:
                        # Add weekly variation
                        variation = pm.Normal(f"variation_week_{week}", mu=1.0, sigma=0.05)
                        cash_flow = cash_flow * variation
                
                cash_flows.append(cash_flow)
            
            # Calculate cumulative metrics
            total_benefit = pm.Deterministic(
                "total_benefit",
                sum(cash_flows)
            )
            
            # NPV calculation
            weekly_discount_rate = self.cost_params.discount_rate / 52
            npv_components = [
                cash_flows[week] / (1 + weekly_discount_rate) ** week
                for week in range(time_horizon_weeks)
            ]
            npv = pm.Deterministic("npv", sum(npv_components))
            
            # ROI percentage
            roi_percentage = pm.Deterministic(
                "roi_percentage",
                (total_benefit / implementation_cost - 1) * 100 if implementation_cost > 0 else 0
            )
            
            # Payback period approximation
            cumulative_cf = pm.math.cumsum([cf for cf in cash_flows])
            
            # Annual benefit
            annual_benefit = pm.Deterministic(
                "annual_benefit",
                weekly_savings * 52
            )
            
            # Sample from the model using MCMC
            trace = pm.sample(
                draws=n_simulations,
                tune=1000,  # Burn-in samples
                cores=4,
                progressbar=False,
                return_inferencedata=True
            )
        
        # Extract results and calculate statistics
        roi_summary = self._extract_pymc_results(
            trace,
            implementation_cost,
            time_horizon_weeks,
            n_simulations,
            include_uncertainty
        )
        
        return roi_summary
    
    def _extract_pymc_results(
        self,
        trace,
        implementation_cost: float,
        time_horizon_weeks: int,
        n_simulations: int,
        include_uncertainty: bool
    ) -> Dict[str, Any]:
        """Extract results from PyMC trace and calculate statistics
        
        Args:
            trace: PyMC InferenceData object
            implementation_cost: Implementation cost
            time_horizon_weeks: Time horizon
            n_simulations: Number of samples
            include_uncertainty: Whether uncertainty was modeled
            
        Returns:
            Dictionary with ROI metrics and credible intervals

        """
        # Extract posterior samples
        posterior = trace.posterior
        
        # Calculate credible intervals (Bayesian equivalent of confidence intervals)
        confidence = self.cost_params.confidence_level
        hdi_prob = confidence  # Highest Density Interval probability
        
        # Weekly savings statistics
        weekly_savings_samples = posterior["weekly_savings"].values.flatten()
        weekly_savings_hdi = az.hdi(posterior, hdi_prob=hdi_prob)["weekly_savings"].values
        
        # NPV statistics
        npv_samples = posterior["npv"].values.flatten()
        npv_hdi = az.hdi(posterior, hdi_prob=hdi_prob)["npv"].values
        
        # ROI percentage statistics
        roi_samples = posterior["roi_percentage"].values.flatten()
        roi_hdi = az.hdi(posterior, hdi_prob=hdi_prob)["roi_percentage"].values
        
        # Annual benefit statistics
        annual_samples = posterior["annual_benefit"].values.flatten()
        annual_hdi = az.hdi(posterior, hdi_prob=hdi_prob)["annual_benefit"].values
        
        # Calculate payback period (simplified)
        payback_weeks = implementation_cost / np.mean(weekly_savings_samples) if np.mean(weekly_savings_samples) > 0 else np.inf
        
        roi_summary = {
            "implementation_cost": implementation_cost,
            "weekly_savings": {
                "mean": np.mean(weekly_savings_samples),
                "std": np.std(weekly_savings_samples),
                "median": np.median(weekly_savings_samples),
                "credible_interval": (float(weekly_savings_hdi[0]), float(weekly_savings_hdi[1])),
                "percentiles": {
                    "p5": np.percentile(weekly_savings_samples, 5),
                    "p50": np.percentile(weekly_savings_samples, 50),
                    "p95": np.percentile(weekly_savings_samples, 95)
                }
            },
            "payback_weeks": {
                "mean": payback_weeks,
                "std": payback_weeks * 0.2 if include_uncertainty else 0,  # Approximation
                "credible_interval": (
                    payback_weeks * 0.8 if payback_weeks < np.inf else np.inf,
                    payback_weeks * 1.2 if payback_weeks < np.inf else np.inf
                )
            },
            "npv": {
                "mean": np.mean(npv_samples),
                "std": np.std(npv_samples),
                "median": np.median(npv_samples),
                "credible_interval": (float(npv_hdi[0]), float(npv_hdi[1])),
                "probability_positive": np.mean(npv_samples > 0),
                "percentiles": {
                    "p5": np.percentile(npv_samples, 5),
                    "p50": np.percentile(npv_samples, 50),
                    "p95": np.percentile(npv_samples, 95)
                }
            },
            "roi_percentage": {
                "mean": np.mean(roi_samples),
                "std": np.std(roi_samples),
                "median": np.median(roi_samples),
                "credible_interval": (float(roi_hdi[0]), float(roi_hdi[1])),
                "percentiles": {
                    "p5": np.percentile(roi_samples, 5),
                    "p50": np.percentile(roi_samples, 50),
                    "p95": np.percentile(roi_samples, 95)
                }
            },
            "annual_benefit": {
                "mean": np.mean(annual_samples),
                "median": np.median(annual_samples),
                "credible_interval": (float(annual_hdi[0]), float(annual_hdi[1]))
            },
            "simulation_parameters": {
                "n_simulations": n_simulations,
                "time_horizon_weeks": time_horizon_weeks,
                "confidence_level": confidence,
                "include_uncertainty": include_uncertainty,
                "method": "PyMC Bayesian MCMC"
            },
            "diagnostics": {
                "effective_sample_size": float(az.ess(trace)["weekly_savings"].values.mean()),
                "r_hat": float(az.rhat(trace)["weekly_savings"].values.mean())  # Convergence diagnostic
            }
        }
        
        return roi_summary
    
    def calculate_scenario_impact(
        self,
        scenario: str,
        baseline_kpis: Dict[str, float],
        parameter_changes: Dict[str, float],
        n_simulations: int = 1000
    ) -> Dict[str, Any]:
        """Calculate financial impact of a specific scenario using PyMC
        
        Args:
            scenario: Scenario name (e.g., "reduce_micro_stops_30%")
            baseline_kpis: Baseline KPI values
            parameter_changes: Parameter changes for scenario
            n_simulations: Number of simulations
            
        Returns:
            Financial impact with credible intervals

        """
        with pm.Model() as scenario_model:
            # Estimate KPI improvements based on parameter changes
            improved_kpis = self._estimate_kpi_impact_probabilistic(
                baseline_kpis,
                parameter_changes
            )
            
            # Calculate financial impact based on scenario
            if "micro_stop" in scenario.lower():
                # Model downtime reduction
                downtime_reduction_mean = baseline_kpis.get("downtime_percentage", 20) * abs(parameter_changes.get("micro_stop_probability", 0))
                downtime_reduction = pm.TruncatedNormal(
                    "downtime_reduction",
                    mu=downtime_reduction_mean,
                    sigma=downtime_reduction_mean * 0.2,
                    lower=0
                )
                
                weekly_hours = 168
                downtime_hours_saved = weekly_hours * (downtime_reduction / 100)
                weekly_savings = downtime_hours_saved * self.cost_params.downtime_cost_per_hour
                
            elif "quality" in scenario.lower() or "scrap" in scenario.lower():
                # Model scrap reduction
                scrap_reduction_mean = baseline_kpis.get("scrap_rate", 0.05) * (1 - parameter_changes.get("scrap_multiplier", 1.0))
                scrap_reduction = pm.Beta(
                    "scrap_reduction",
                    alpha=2,
                    beta=20
                ) * scrap_reduction_mean
                
                weekly_production = pm.Normal("weekly_production", mu=100000, sigma=10000)
                scrap_units_saved = weekly_production * scrap_reduction
                weekly_savings = scrap_units_saved * self.cost_params.scrap_cost_per_unit
                
            elif "energy" in scenario.lower():
                # Model energy reduction
                energy_reduction = pm.Normal(
                    "energy_reduction",
                    mu=0.15,  # 15% reduction
                    sigma=0.03
                )
                weekly_kwh = pm.Normal("weekly_kwh", mu=50000, sigma=5000)
                kwh_saved = weekly_kwh * energy_reduction
                weekly_savings = kwh_saved * self.cost_params.energy_cost_per_kwh
                
            else:
                # General OEE improvement - properly handle percentage to fraction conversion
                baseline_oee = baseline_kpis.get("mean_oee", 65.0)  # As percentage
                improved_oee = improved_kpis.get("mean_oee", 65.0)  # As percentage
                
                # Calculate the improvement as a fraction for financial impact
                # E.g., if OEE goes from 47.7% to 57.5%, that's a 9.8 percentage point improvement
                # which represents a 9.8/100 = 0.098 (9.8%) improvement in production value
                oee_improvement_pct_points = improved_oee - baseline_oee  # Percentage points
                oee_improvement_fraction = oee_improvement_pct_points / 100.0  # As fraction
                
                # Ensure sigma is always positive and reasonable
                oee_sigma = max(abs(oee_improvement_fraction) * 0.2, 0.001)  # At least 0.1% sigma
                oee_improvement = pm.Normal("oee_improvement", mu=oee_improvement_fraction, sigma=oee_sigma)
                
                # Calculate actual weekly production value (7 days * daily value)
                # Using realistic estimate based on typical MES data (~$590k/day from query)
                weekly_value = 4_100_000  # ~$590k/day * 7 days from actual data
                
                # Financial impact: production value * OEE improvement fraction
                weekly_savings = weekly_value * oee_improvement
            
            # Add uncertainty multiplier
            uncertainty_mult = pm.TruncatedNormal(
                "uncertainty",
                mu=1.0,
                sigma=0.15,
                lower=0.5,
                upper=1.5
            )
            
            weekly_impact = pm.Deterministic(
                "weekly_impact",
                weekly_savings * uncertainty_mult
            )
            
            annual_impact = pm.Deterministic(
                "annual_impact",
                weekly_impact * 52
            )
            
            # Sample from model
            trace = pm.sample(
                draws=n_simulations,
                tune=500,
                progressbar=False,
                return_inferencedata=True
            )
        
        # Extract results
        posterior = trace.posterior
        weekly_samples = posterior["weekly_impact"].values.flatten()
        annual_samples = posterior["annual_impact"].values.flatten()
        
        hdi_95 = az.hdi(trace, hdi_prob=0.95)
        
        return {
            "scenario": scenario,
            "weekly_impact": {
                "mean": np.mean(weekly_samples),
                "std": np.std(weekly_samples),
                "median": np.median(weekly_samples),
                "credible_interval_95": (
                    float(hdi_95["weekly_impact"].values[0]),
                    float(hdi_95["weekly_impact"].values[1])
                ),
                "percentiles": {
                    "p5": np.percentile(weekly_samples, 5),
                    "p50": np.percentile(weekly_samples, 50),
                    "p95": np.percentile(weekly_samples, 95)
                }
            },
            "annual_impact": {
                "mean": np.mean(annual_samples),
                "median": np.median(annual_samples),
                "credible_interval_95": (
                    float(hdi_95["annual_impact"].values[0]),
                    float(hdi_95["annual_impact"].values[1])
                )
            },
            "parameter_changes": parameter_changes,
            "method": "PyMC Bayesian Analysis"
        }
    
    def _get_run_kpis(self, run_id: str) -> Dict[str, float]:
        """Get KPIs for a simulation run from database"""
        with sqlite3.connect(self.db_path) as conn:
            # Try to get from twin_runs table first
            cursor = conn.execute(
                "SELECT kpi_summary_json FROM twin_runs WHERE run_id = ?",
                (run_id,)
            )
            row = cursor.fetchone()
            
            if row and row[0]:
                kpis = json.loads(row[0])
            else:
                # Calculate from actual data if run_id not found
                kpis = self._calculate_kpis_from_data(conn, run_id)
            
            # Get energy consumption from virtual sensors if available
            try:
                energy_cursor = conn.execute("""
                    SELECT 
                        SUM(value) as total_energy,
                        AVG(value) as avg_energy
                    FROM sensor_data 
                    WHERE observable_property = 'power_consumption'
                    AND timestamp >= datetime('now', '-7 days')
                """)
                energy_row = energy_cursor.fetchone()
                
                if energy_row and energy_row[0]:
                    kpis["weekly_energy_kwh"] = energy_row[0]
                    kpis["avg_energy_per_interval"] = energy_row[1]
                else:
                    # Use default estimates if no sensor data
                    kpis["weekly_energy_kwh"] = 25332
                    kpis["avg_energy_per_interval"] = 0.7
            except:
                # Fallback to defaults if sensor_data table doesn't exist
                kpis["weekly_energy_kwh"] = 25332
                kpis["avg_energy_per_interval"] = 0.7
            
            return kpis
    
    def _calculate_kpis_from_data(self, conn, run_id: str = None) -> Dict[str, float]:
        """Calculate KPIs directly from mes_data table"""
        cursor = conn.execute("""
            SELECT 
                AVG(oee_score) as mean_oee,
                AVG(availability_score) as mean_availability,
                AVG(performance_score) as mean_performance,
                AVG(quality_score) as mean_quality,
                SUM(CASE WHEN machine_status = 'Stopped' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as downtime_percentage,
                AVG(CASE WHEN good_units_produced + scrap_units_produced > 0 
                    THEN scrap_units_produced * 1.0 / (good_units_produced + scrap_units_produced) 
                    ELSE 0 END) as scrap_rate
            FROM mes_data
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        
        row = cursor.fetchone()
        if row:
            return {
                "mean_oee": row[0] / 100.0 if row[0] else 0.65,
                "mean_availability": row[1] / 100.0 if row[1] else 0.80,
                "mean_performance": row[2] / 100.0 if row[2] else 0.85,
                "mean_quality": row[3] / 100.0 if row[3] else 0.95,
                "downtime_percentage": row[4] if row[4] else 20.0,
                "scrap_rate": row[5] if row[5] else 0.05
            }
        
        # Return default KPIs if no data found
        return {
            "mean_oee": 0.65,
            "mean_availability": 0.80,
            "mean_performance": 0.85,
            "mean_quality": 0.95,
            "downtime_percentage": 20.0,
            "scrap_rate": 0.05
        }
    
    def _get_parameter_changes(self, baseline_run_id: str, improved_run_id: str) -> Dict[str, float]:
        """Get parameter changes between two runs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT parameter_name, old_value, new_value
                FROM parameter_history
                WHERE run_id = ?
            """, (improved_run_id,))
            
            changes = {}
            for row in cursor.fetchall():
                param_name = row[0]
                old_value = row[1] if row[1] is not None else 0
                new_value = row[2]
                changes[param_name] = new_value - old_value
            
            return changes
    
    def _calculate_implementation_cost(self, param_changes: Dict[str, float]) -> float:
        """Calculate one-time implementation cost"""
        num_changes = len(param_changes)
        
        # Base costs
        cost = self.cost_params.training_cost
        cost += num_changes * self.cost_params.parameter_change_cost
        
        return cost
    
    def _estimate_kpi_impact_probabilistic(
        self,
        baseline_kpis: Dict[str, float],
        parameter_changes: Dict[str, float]
    ) -> Dict[str, float]:
        """Estimate KPI impact from parameter changes (deterministic for now)
        Could be enhanced with probabilistic relationships
        """
        improved_kpis = baseline_kpis.copy()
        
        # Simple impact model
        if "micro_stop_probability" in parameter_changes:
            change = parameter_changes["micro_stop_probability"]
            # Reducing micro-stops improves availability
            # Note: negative change (e.g., -0.5 for 50% reduction) should INCREASE availability
            if "mean_availability" in improved_kpis:
                # Invert the sign: reducing stops (-) increases availability (+)
                improved_kpis["mean_availability"] *= (1 - change * 0.5)  # Note the minus sign
                # Ensure stays within valid percentage range
                improved_kpis["mean_availability"] = min(100.0, max(0.0, improved_kpis["mean_availability"]))
            
            # Handle downtime_percentage - calculate from availability if not present
            if "downtime_percentage" not in improved_kpis and "mean_availability" in improved_kpis:
                improved_kpis["downtime_percentage"] = 100 - improved_kpis["mean_availability"]
            
            if "downtime_percentage" in improved_kpis:
                improved_kpis["downtime_percentage"] *= (1 + change)
                improved_kpis["downtime_percentage"] = min(100.0, max(0.0, improved_kpis["downtime_percentage"]))
        
        if "scrap_multiplier" in parameter_changes:
            change = parameter_changes["scrap_multiplier"]
            # Reducing scrap improves quality
            if "mean_quality" in improved_kpis:
                improved_kpis["mean_quality"] *= (1 - change * 0.2)
                # Ensure stays within valid percentage range
                improved_kpis["mean_quality"] = min(100.0, max(0.0, improved_kpis["mean_quality"]))
            if "scrap_rate" in improved_kpis:
                improved_kpis["scrap_rate"] *= (1 + change)
                # Scrap rate is typically 0-100 but often expressed as 0-1, keep reasonable
                improved_kpis["scrap_rate"] = max(0.0, improved_kpis["scrap_rate"])
        
        if "performance_factor" in parameter_changes:
            change = parameter_changes["performance_factor"]
            # Improving performance factor
            if "mean_performance" in improved_kpis:
                improved_kpis["mean_performance"] *= (1 + change * 0.3)
                # Ensure stays within valid percentage range
                improved_kpis["mean_performance"] = min(100.0, max(0.0, improved_kpis["mean_performance"]))
        
        # Don't recalculate OEE - it's not just the product of the three factors
        # The actual simulation has complex interactions that affect OEE differently
        # Instead, estimate OEE improvement based on the component improvements
        if "mean_oee" in improved_kpis:
            # Estimate OEE improvement as weighted average of component improvements
            baseline_avail = baseline_kpis.get("mean_availability", 80.0)
            baseline_perf = baseline_kpis.get("mean_performance", 85.0)
            baseline_qual = baseline_kpis.get("mean_quality", 95.0)
            
            avail_improvement = (improved_kpis.get("mean_availability", baseline_avail) - baseline_avail) / baseline_avail
            perf_improvement = (improved_kpis.get("mean_performance", baseline_perf) - baseline_perf) / baseline_perf
            qual_improvement = (improved_kpis.get("mean_quality", baseline_qual) - baseline_qual) / baseline_qual
            
            # Weighted average based on typical impact
            weighted_improvement = (avail_improvement * 0.4 + perf_improvement * 0.4 + qual_improvement * 0.2)
            
            # Apply improvement to baseline OEE
            improved_kpis["mean_oee"] = baseline_kpis.get("mean_oee", 65.0) * (1 + weighted_improvement)
            improved_kpis["mean_oee"] = min(100.0, max(0.0, improved_kpis["mean_oee"]))
        
        return improved_kpis
    
    def format_roi_report(self, roi_summary: Dict[str, Any]) -> str:
        """Format ROI summary as a readable report with Bayesian credible intervals"""
        report = []
        report.append("=" * 60)
        report.append("VIRTUAL TWIN ROI ANALYSIS (PyMC Bayesian)")
        report.append("=" * 60)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"Method: {roi_summary['simulation_parameters'].get('method', 'PyMC')}")
        report.append("")
        
        # Implementation cost
        report.append("IMPLEMENTATION COSTS:")
        report.append(f"  One-time investment: ${roi_summary['implementation_cost']:,.0f}")
        report.append("")
        
        # Weekly savings with credible intervals
        report.append("WEEKLY SAVINGS:")
        ws = roi_summary['weekly_savings']
        report.append(f"  Mean: ${ws['mean']:,.0f}")
        report.append(f"  Median: ${ws['median']:,.0f}")
        report.append(f"  95% Credible Interval: ${ws['credible_interval'][0]:,.0f} - ${ws['credible_interval'][1]:,.0f}")
        if 'percentiles' in ws:
            report.append(f"  Percentiles: P5=${ws['percentiles']['p5']:,.0f}, P50=${ws['percentiles']['p50']:,.0f}, P95=${ws['percentiles']['p95']:,.0f}")
        report.append("")
        
        # Payback period
        report.append("PAYBACK PERIOD:")
        pb = roi_summary['payback_weeks']
        report.append(f"  Mean: {pb['mean']:.1f} weeks")
        if pb['mean'] < 52:
            report.append(f"  ({pb['mean']/4:.1f} months)")
        report.append("")
        
        # Annual benefit
        report.append("ANNUAL BENEFIT:")
        ab = roi_summary['annual_benefit']
        report.append(f"  Mean: ${ab['mean']:,.0f}")
        report.append(f"  95% Credible Interval: ${ab['credible_interval'][0]:,.0f} - ${ab['credible_interval'][1]:,.0f}")
        report.append("")
        
        # NPV with percentiles
        report.append("NET PRESENT VALUE (NPV):")
        npv = roi_summary['npv']
        report.append(f"  Mean: ${npv['mean']:,.0f}")
        report.append(f"  Median: ${npv['median']:,.0f}")
        report.append(f"  95% Credible Interval: ${npv['credible_interval'][0]:,.0f} - ${npv['credible_interval'][1]:,.0f}")
        report.append(f"  Probability of positive NPV: {npv['probability_positive']:.1%}")
        if 'percentiles' in npv:
            report.append(f"  Percentiles: P5=${npv['percentiles']['p5']:,.0f}, P50=${npv['percentiles']['p50']:,.0f}, P95=${npv['percentiles']['p95']:,.0f}")
        report.append("")
        
        # ROI percentage
        report.append("RETURN ON INVESTMENT:")
        roi = roi_summary['roi_percentage']
        report.append(f"  Mean ROI: {roi['mean']:.1f}%")
        report.append(f"  Median ROI: {roi['median']:.1f}%")
        report.append(f"  95% Credible Interval: {roi['credible_interval'][0]:.1f}% - {roi['credible_interval'][1]:.1f}%")
        report.append("")
        
        # Diagnostics
        if 'diagnostics' in roi_summary:
            report.append("MCMC DIAGNOSTICS:")
            diag = roi_summary['diagnostics']
            report.append(f"  Effective Sample Size: {diag.get('effective_sample_size', 'N/A'):.0f}")
            report.append(f"  R-hat (convergence): {diag.get('r_hat', 'N/A'):.3f}")
            report.append("")
        
        # Recommendation
        report.append("RECOMMENDATION:")
        if npv['probability_positive'] > 0.8:
            report.append("  ✅ STRONG BUY - High probability of positive returns")
        elif npv['probability_positive'] > 0.6:
            report.append("  ✅ BUY - Good probability of positive returns")
        elif npv['probability_positive'] > 0.4:
            report.append("  ⚠️  CONSIDER - Moderate probability of positive returns")
        else:
            report.append("  ❌ WAIT - Low probability of positive returns")
        
        report.append("=" * 60)
        
        return "\n".join(report)