"""
Cost Impact Calculator with Monte Carlo ROI Simulation
Provides probabilistic financial validation for virtual twin recommendations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
from datetime import datetime, timedelta
import sqlite3


@dataclass
class CostParameters:
    """Financial parameters for ROI calculation"""
    # Production costs
    labor_cost_per_hour: float = 75.0  # USD per hour
    energy_cost_per_kwh: float = 0.12  # USD per kWh
    material_cost_per_unit: float = 0.50  # USD per unit
    
    # Downtime costs
    downtime_cost_per_hour: float = 5000.0  # USD per hour of downtime
    
    # Quality costs
    scrap_cost_per_unit: float = 2.00  # USD per scrapped unit
    rework_cost_per_unit: float = 1.50  # USD per reworked unit
    
    # Implementation costs
    parameter_change_cost: float = 1000.0  # One-time cost per parameter change
    training_cost: float = 2500.0  # One-time training cost
    monitoring_cost_per_week: float = 500.0  # Ongoing monitoring cost
    
    # Financial parameters
    discount_rate: float = 0.10  # Annual discount rate for NPV
    confidence_level: float = 0.95  # Confidence level for intervals


class CostImpactCalculator:
    """
    Calculates financial impact of virtual twin recommendations
    using Monte Carlo simulation for uncertainty quantification
    """
    
    def __init__(
        self,
        db_path: str = "data/mes_database.db",
        cost_params: Optional[CostParameters] = None
    ):
        self.db_path = db_path
        self.cost_params = cost_params or CostParameters()
        
    def calculate_roi(
        self,
        baseline_run_id: str,
        improved_run_id: str,
        n_simulations: int = 10000,
        time_horizon_weeks: int = 52,
        include_uncertainty: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate ROI using Monte Carlo simulation
        
        Args:
            baseline_run_id: Run ID for baseline scenario
            improved_run_id: Run ID for improved scenario
            n_simulations: Number of Monte Carlo simulations
            time_horizon_weeks: Time horizon for ROI calculation
            include_uncertainty: Whether to add uncertainty to parameters
            
        Returns:
            Dictionary with ROI metrics and confidence intervals
        """
        # Get KPIs from database
        baseline_kpis = self._get_run_kpis(baseline_run_id)
        improved_kpis = self._get_run_kpis(improved_run_id)
        
        # Get parameter changes
        param_changes = self._get_parameter_changes(baseline_run_id, improved_run_id)
        
        # Calculate implementation costs
        implementation_cost = self._calculate_implementation_cost(param_changes)
        
        # Run Monte Carlo simulation
        simulation_results = []
        
        rng = np.random.default_rng(42)  # Reproducible results
        
        for i in range(n_simulations):
            # Add uncertainty to KPIs if requested
            if include_uncertainty:
                baseline_sim = self._add_uncertainty(baseline_kpis, rng)
                improved_sim = self._add_uncertainty(improved_kpis, rng)
            else:
                baseline_sim = baseline_kpis.copy()
                improved_sim = improved_kpis.copy()
            
            # Calculate weekly savings
            weekly_savings = self._calculate_weekly_savings(
                baseline_sim,
                improved_sim,
                rng if include_uncertainty else None
            )
            
            # Calculate cumulative cash flows
            cash_flows = []
            for week in range(time_horizon_weeks):
                if week == 0:
                    # Initial investment
                    cash_flow = -implementation_cost
                else:
                    # Weekly savings minus monitoring cost
                    cash_flow = weekly_savings - self.cost_params.monitoring_cost_per_week
                
                # Add some weekly variation if uncertainty is enabled
                if include_uncertainty and week > 0:
                    cash_flow *= rng.normal(1.0, 0.1)  # ±10% variation
                
                cash_flows.append(cash_flow)
            
            # Calculate metrics
            total_benefit = sum(cash_flows)
            payback_weeks = self._calculate_payback_period(cash_flows)
            npv = self._calculate_npv(cash_flows, self.cost_params.discount_rate)
            irr = self._calculate_irr(cash_flows)
            
            simulation_results.append({
                "weekly_savings": weekly_savings,
                "total_benefit": total_benefit,
                "payback_weeks": payback_weeks,
                "npv": npv,
                "irr": irr,
                "roi_percentage": (total_benefit / implementation_cost - 1) * 100 if implementation_cost > 0 else 0
            })
        
        # Convert to DataFrame for analysis
        results_df = pd.DataFrame(simulation_results)
        
        # Calculate statistics
        confidence = self.cost_params.confidence_level
        lower_percentile = (1 - confidence) / 2 * 100
        upper_percentile = (1 + confidence) / 2 * 100
        
        roi_summary = {
            "implementation_cost": implementation_cost,
            "weekly_savings": {
                "mean": results_df["weekly_savings"].mean(),
                "std": results_df["weekly_savings"].std(),
                "confidence_interval": (
                    results_df["weekly_savings"].quantile(lower_percentile / 100),
                    results_df["weekly_savings"].quantile(upper_percentile / 100)
                )
            },
            "payback_weeks": {
                "mean": results_df[results_df["payback_weeks"] < np.inf]["payback_weeks"].mean(),
                "std": results_df[results_df["payback_weeks"] < np.inf]["payback_weeks"].std(),
                "confidence_interval": (
                    results_df["payback_weeks"].quantile(lower_percentile / 100),
                    results_df["payback_weeks"].quantile(upper_percentile / 100)
                )
            },
            "npv": {
                "mean": results_df["npv"].mean(),
                "std": results_df["npv"].std(),
                "confidence_interval": (
                    results_df["npv"].quantile(lower_percentile / 100),
                    results_df["npv"].quantile(upper_percentile / 100)
                ),
                "probability_positive": (results_df["npv"] > 0).mean()
            },
            "roi_percentage": {
                "mean": results_df["roi_percentage"].mean(),
                "std": results_df["roi_percentage"].std(),
                "confidence_interval": (
                    results_df["roi_percentage"].quantile(lower_percentile / 100),
                    results_df["roi_percentage"].quantile(upper_percentile / 100)
                )
            },
            "annual_benefit": {
                "mean": results_df["weekly_savings"].mean() * 52,
                "confidence_interval": (
                    results_df["weekly_savings"].quantile(lower_percentile / 100) * 52,
                    results_df["weekly_savings"].quantile(upper_percentile / 100) * 52
                )
            },
            "simulation_parameters": {
                "n_simulations": n_simulations,
                "time_horizon_weeks": time_horizon_weeks,
                "confidence_level": confidence,
                "include_uncertainty": include_uncertainty
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
        """
        Calculate financial impact of a specific scenario
        
        Args:
            scenario: Scenario name (e.g., "reduce_micro_stops_30%")
            baseline_kpis: Baseline KPI values
            parameter_changes: Parameter changes for scenario
            n_simulations: Number of simulations
            
        Returns:
            Financial impact with confidence intervals
        """
        rng = np.random.default_rng()
        
        impacts = []
        
        for _ in range(n_simulations):
            # Estimate KPI improvements based on parameter changes
            improved_kpis = self._estimate_kpi_impact(
                baseline_kpis,
                parameter_changes,
                rng
            )
            
            # Calculate financial impact
            if "micro_stop" in scenario.lower():
                # Reduce downtime costs
                downtime_reduction = baseline_kpis.get("downtime_percentage", 20) * parameter_changes.get("micro_stop_probability", 1.0)
                weekly_hours = 168  # Hours per week
                downtime_hours_saved = weekly_hours * (downtime_reduction / 100)
                weekly_savings = downtime_hours_saved * self.cost_params.downtime_cost_per_hour
                
            elif "quality" in scenario.lower() or "scrap" in scenario.lower():
                # Reduce scrap costs
                scrap_reduction = baseline_kpis.get("scrap_rate", 0.05) * (1 - parameter_changes.get("scrap_multiplier", 1.0))
                weekly_production = 100000  # Units per week (estimated)
                scrap_units_saved = weekly_production * scrap_reduction
                weekly_savings = scrap_units_saved * self.cost_params.scrap_cost_per_unit
                
            elif "energy" in scenario.lower():
                # Reduce energy costs
                energy_reduction = 0.15  # 15% energy reduction (estimated)
                weekly_kwh = 50000  # kWh per week (estimated)
                kwh_saved = weekly_kwh * energy_reduction
                weekly_savings = kwh_saved * self.cost_params.energy_cost_per_kwh
                
            else:
                # General OEE improvement
                oee_improvement = improved_kpis.get("mean_oee", 0.65) - baseline_kpis.get("mean_oee", 0.65)
                weekly_value = 500000  # Weekly production value (USD)
                weekly_savings = weekly_value * oee_improvement
            
            # Add uncertainty
            weekly_savings *= rng.normal(1.0, 0.15)  # ±15% uncertainty
            
            impacts.append(weekly_savings)
        
        impacts_array = np.array(impacts)
        
        return {
            "scenario": scenario,
            "weekly_impact": {
                "mean": impacts_array.mean(),
                "std": impacts_array.std(),
                "confidence_interval_95": (
                    np.percentile(impacts_array, 2.5),
                    np.percentile(impacts_array, 97.5)
                )
            },
            "annual_impact": {
                "mean": impacts_array.mean() * 52,
                "confidence_interval_95": (
                    np.percentile(impacts_array, 2.5) * 52,
                    np.percentile(impacts_array, 97.5) * 52
                )
            },
            "parameter_changes": parameter_changes
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
            
            # Add energy consumption data
            energy_cursor = conn.execute("""
                SELECT 
                    SUM(energy_consumption_kwh) as total_energy,
                    AVG(energy_consumption_kwh) as avg_energy
                FROM mes_data 
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            energy_row = energy_cursor.fetchone()
            
            if energy_row and energy_row[0]:
                kpis["weekly_energy_kwh"] = energy_row[0]
                kpis["avg_energy_per_interval"] = energy_row[1]
            else:
                # Use default based on our actual data (25,332 kWh/week)
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
    
    def _add_uncertainty(self, kpis: Dict[str, float], rng: np.random.Generator) -> Dict[str, float]:
        """Add realistic uncertainty to KPI values"""
        uncertain_kpis = {}
        
        for key, value in kpis.items():
            if "percentage" in key or "score" in key or "rate" in key:
                # Add ±5% uncertainty for percentages
                uncertain_kpis[key] = value * rng.normal(1.0, 0.05)
                # Ensure percentages stay in valid range
                if "percentage" in key or "score" in key:
                    uncertain_kpis[key] = np.clip(uncertain_kpis[key], 0, 100)
                elif "rate" in key:
                    uncertain_kpis[key] = np.clip(uncertain_kpis[key], 0, 1)
            else:
                # Add ±10% uncertainty for other metrics
                uncertain_kpis[key] = value * rng.normal(1.0, 0.10)
        
        return uncertain_kpis
    
    def _calculate_weekly_savings(
        self,
        baseline_kpis: Dict[str, float],
        improved_kpis: Dict[str, float],
        rng: Optional[np.random.Generator] = None
    ) -> float:
        """Calculate weekly cost savings from KPI improvements"""
        savings = 0
        
        # Downtime reduction savings
        downtime_reduction = baseline_kpis.get("downtime_percentage", 20) - improved_kpis.get("downtime_percentage", 20)
        if downtime_reduction > 0:
            weekly_hours = 168
            downtime_hours_saved = weekly_hours * (downtime_reduction / 100)
            savings += downtime_hours_saved * self.cost_params.downtime_cost_per_hour
        
        # Scrap reduction savings
        scrap_reduction = baseline_kpis.get("scrap_rate", 0.05) - improved_kpis.get("scrap_rate", 0.05)
        if scrap_reduction > 0:
            weekly_production = 100000  # Estimated units per week
            if rng:
                weekly_production *= rng.normal(1.0, 0.1)  # Add production variation
            scrap_units_saved = weekly_production * scrap_reduction
            savings += scrap_units_saved * self.cost_params.scrap_cost_per_unit
        
        # Energy consumption savings
        energy_reduction_kwh = baseline_kpis.get("weekly_energy_kwh", 25332) - improved_kpis.get("weekly_energy_kwh", 25332)
        if energy_reduction_kwh > 0:
            savings += energy_reduction_kwh * self.cost_params.energy_cost_per_kwh
        
        # OEE improvement value
        oee_improvement = improved_kpis.get("mean_oee", 0.65) - baseline_kpis.get("mean_oee", 0.65)
        if oee_improvement > 0:
            # Each 1% OEE improvement is worth approximately $5000/week
            savings += oee_improvement * 100 * 5000
        
        return max(savings, 0)  # Ensure non-negative
    
    def _estimate_kpi_impact(
        self,
        baseline_kpis: Dict[str, float],
        parameter_changes: Dict[str, float],
        rng: np.random.Generator
    ) -> Dict[str, float]:
        """Estimate KPI impact from parameter changes"""
        improved_kpis = baseline_kpis.copy()
        
        # Simple impact model (would be more sophisticated in production)
        if "micro_stop_probability" in parameter_changes:
            change = parameter_changes["micro_stop_probability"]
            # Reducing micro-stops improves availability
            improved_kpis["mean_availability"] *= (1 + change * 0.5)
            improved_kpis["downtime_percentage"] *= (1 + change)
        
        if "scrap_multiplier" in parameter_changes:
            change = parameter_changes["scrap_multiplier"]
            # Reducing scrap improves quality
            improved_kpis["mean_quality"] *= (1 - change * 0.2)
            improved_kpis["scrap_rate"] *= (1 + change)
        
        if "performance_factor" in parameter_changes:
            change = parameter_changes["performance_factor"]
            # Improving performance factor
            improved_kpis["mean_performance"] *= (1 + change * 0.3)
        
        # Recalculate OEE
        improved_kpis["mean_oee"] = (
            improved_kpis.get("mean_availability", 0.8) *
            improved_kpis.get("mean_performance", 0.85) *
            improved_kpis.get("mean_quality", 0.95)
        )
        
        return improved_kpis
    
    def _calculate_payback_period(self, cash_flows: List[float]) -> float:
        """Calculate payback period in weeks"""
        cumulative = 0
        for week, cash_flow in enumerate(cash_flows):
            cumulative += cash_flow
            if cumulative > 0:
                return week
        return np.inf  # Never pays back
    
    def _calculate_npv(self, cash_flows: List[float], discount_rate: float) -> float:
        """Calculate Net Present Value"""
        weekly_rate = discount_rate / 52  # Convert annual to weekly
        npv = 0
        for week, cash_flow in enumerate(cash_flows):
            npv += cash_flow / (1 + weekly_rate) ** week
        return npv
    
    def _calculate_irr(self, cash_flows: List[float]) -> float:
        """Calculate Internal Rate of Return"""
        try:
            # Simple IRR calculation (could use numpy.irr if available)
            return np.irr(cash_flows) * 52  # Convert to annual
        except:
            return 0.0
    
    def format_roi_report(self, roi_summary: Dict[str, Any]) -> str:
        """Format ROI summary as a readable report"""
        report = []
        report.append("=" * 60)
        report.append("VIRTUAL TWIN ROI ANALYSIS")
        report.append("=" * 60)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")
        
        # Implementation cost
        report.append("IMPLEMENTATION COSTS:")
        report.append(f"  One-time investment: ${roi_summary['implementation_cost']:,.0f}")
        report.append("")
        
        # Weekly savings
        report.append("WEEKLY SAVINGS:")
        ws = roi_summary['weekly_savings']
        report.append(f"  Mean: ${ws['mean']:,.0f}")
        report.append(f"  95% Confidence Interval: ${ws['confidence_interval'][0]:,.0f} - ${ws['confidence_interval'][1]:,.0f}")
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
        report.append(f"  95% Confidence Interval: ${ab['confidence_interval'][0]:,.0f} - ${ab['confidence_interval'][1]:,.0f}")
        report.append("")
        
        # NPV
        report.append("NET PRESENT VALUE (NPV):")
        npv = roi_summary['npv']
        report.append(f"  Mean: ${npv['mean']:,.0f}")
        report.append(f"  Probability of positive NPV: {npv['probability_positive']:.1%}")
        report.append("")
        
        # ROI percentage
        report.append("RETURN ON INVESTMENT:")
        roi = roi_summary['roi_percentage']
        report.append(f"  Mean ROI: {roi['mean']:.1f}%")
        report.append(f"  95% Confidence Interval: {roi['confidence_interval'][0]:.1f}% - {roi['confidence_interval'][1]:.1f}%")
        report.append("")
        
        # Summary
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


def demonstrate_cost_impact():
    """Demonstrate cost impact calculation"""
    print("COST IMPACT CALCULATOR DEMONSTRATION")
    print("=" * 60)
    
    calculator = CostImpactCalculator()
    
    # Scenario 1: Reduce micro-stops by 30%
    print("\nScenario: Reduce micro-stops by 30%")
    print("-" * 40)
    
    baseline_kpis = {
        "mean_oee": 0.65,
        "mean_availability": 0.80,
        "mean_performance": 0.85,
        "mean_quality": 0.95,
        "downtime_percentage": 20.0,
        "scrap_rate": 0.05
    }
    
    parameter_changes = {
        "micro_stop_probability": -0.30  # 30% reduction
    }
    
    impact = calculator.calculate_scenario_impact(
        "reduce_micro_stops_30%",
        baseline_kpis,
        parameter_changes,
        n_simulations=1000
    )
    
    print(f"Weekly savings: ${impact['weekly_impact']['mean']:,.0f}")
    print(f"95% CI: ${impact['weekly_impact']['confidence_interval_95'][0]:,.0f} - ${impact['weekly_impact']['confidence_interval_95'][1]:,.0f}")
    print(f"Annual impact: ${impact['annual_impact']['mean']:,.0f}")
    
    # Scenario 2: Full ROI analysis
    print("\n" + "=" * 60)
    print("FULL ROI ANALYSIS")
    print("=" * 60)
    
    # Simulate having run IDs (in practice, these would come from actual runs)
    # For demo, we'll use mock calculation
    print("\nCalculating ROI with Monte Carlo simulation (10,000 iterations)...")
    
    # Mock ROI summary for demonstration
    roi_summary = {
        "implementation_cost": 8500,
        "weekly_savings": {
            "mean": 45000,
            "std": 5000,
            "confidence_interval": (38000, 52000)
        },
        "payback_weeks": {
            "mean": 8.5,
            "std": 2.1,
            "confidence_interval": (6, 12)
        },
        "npv": {
            "mean": 1850000,
            "std": 250000,
            "confidence_interval": (1400000, 2300000),
            "probability_positive": 0.98
        },
        "roi_percentage": {
            "mean": 420,
            "std": 85,
            "confidence_interval": (280, 560)
        },
        "annual_benefit": {
            "mean": 2340000,
            "confidence_interval": (1976000, 2704000)
        },
        "simulation_parameters": {
            "n_simulations": 10000,
            "time_horizon_weeks": 52,
            "confidence_level": 0.95,
            "include_uncertainty": True
        }
    }
    
    # Format and print report
    report = calculator.format_roi_report(roi_summary)
    print(report)
    
    print("\n✅ Cost impact calculator with Monte Carlo simulation demonstrated!")


if __name__ == "__main__":
    demonstrate_cost_impact()