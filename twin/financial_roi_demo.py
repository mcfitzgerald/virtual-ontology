#!/usr/bin/env python3
"""
Financial ROI Demonstration for Virtual Twin System
Shows complete financial impact including energy optimization
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import json

class FinancialROIAnalyzer:
    """Complete financial ROI analysis including energy costs"""
    
    def __init__(self, db_path: str = "data/mes_database.db"):
        self.db_path = db_path
        
        # Financial parameters
        self.energy_cost_per_kwh = 0.12  # $0.12 per kWh
        self.downtime_cost_per_hour = 5000  # $5000 per hour
        self.scrap_cost_per_unit = 2.00  # $2 per scrapped unit
        self.revenue_per_unit = 3.50  # $3.50 per good unit
        
    def calculate_current_state_financials(self) -> Dict[str, Any]:
        """Calculate current financial metrics from actual data"""
        with sqlite3.connect(self.db_path) as conn:
            # First, determine the actual date range in the data
            date_range_query = "SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date FROM mes_data"
            date_result = conn.execute(date_range_query).fetchone()
            
            # Use the last 7 days of available data
            if date_result and date_result[1]:
                max_date = date_result[1]
                # Calculate 7 days before the max date
                week_start = f"datetime('{max_date}', '-6 days')"
                date_filter = f"timestamp >= {week_start} AND timestamp <= '{max_date}'"
            else:
                # Fallback to specific dates if needed
                date_filter = "timestamp >= '2025-06-08' AND timestamp <= '2025-06-14'"
            
            # Get weekly energy consumption and costs
            energy_query = f"""
                SELECT 
                    COUNT(*) as intervals,
                    SUM(energy_consumption_kwh) as total_energy_kwh,
                    AVG(energy_consumption_kwh) as avg_energy_per_interval,
                    equipment_type,
                    machine_status
                FROM mes_data
                WHERE {date_filter}
                GROUP BY equipment_type, machine_status
            """
            energy_df = pd.read_sql_query(energy_query, conn)
            
            # Calculate total weekly energy cost
            total_weekly_energy_kwh = energy_df['total_energy_kwh'].sum()
            weekly_energy_cost = total_weekly_energy_kwh * self.energy_cost_per_kwh
            
            # Get production metrics
            production_query = """
                SELECT 
                    SUM(good_units_produced) as total_good_units,
                    SUM(scrap_units_produced) as total_scrap_units,
                    AVG(oee_score) as avg_oee,
                    AVG(availability_score) as avg_availability,
                    AVG(performance_score) as avg_performance,
                    AVG(quality_score) as avg_quality,
                    SUM(CASE WHEN machine_status = 'Stopped' THEN 5.0/60.0 ELSE 0 END) as downtime_hours
                FROM mes_data
                WHERE timestamp >= '2025-06-08' AND timestamp <= '2025-06-14'
            """
            prod_result = conn.execute(production_query).fetchone()
            
            # Calculate financial metrics
            total_good_units = prod_result[0] or 0
            total_scrap_units = prod_result[1] or 0
            avg_oee = prod_result[2] or 0
            downtime_hours = prod_result[6] or 0
            
            # Calculate costs
            weekly_scrap_cost = total_scrap_units * self.scrap_cost_per_unit
            weekly_downtime_cost = downtime_hours * self.downtime_cost_per_hour
            weekly_revenue = total_good_units * self.revenue_per_unit
            
            # Get energy breakdown by equipment type
            energy_breakdown_query = """
                SELECT 
                    equipment_type,
                    SUM(energy_consumption_kwh) as total_kwh,
                    AVG(energy_consumption_kwh) as avg_kwh_per_interval,
                    COUNT(*) as intervals
                FROM mes_data
                WHERE timestamp >= '2025-06-08' AND timestamp <= '2025-06-14'
                GROUP BY equipment_type
            """
            energy_breakdown = pd.read_sql_query(energy_breakdown_query, conn)
            
            return {
                "weekly_metrics": {
                    "total_good_units": int(total_good_units),
                    "total_scrap_units": int(total_scrap_units),
                    "avg_oee": round(avg_oee, 2),
                    "downtime_hours": round(downtime_hours, 2)
                },
                "weekly_costs": {
                    "energy_cost": round(weekly_energy_cost, 2),
                    "scrap_cost": round(weekly_scrap_cost, 2),
                    "downtime_cost": round(weekly_downtime_cost, 2),
                    "total_cost": round(weekly_energy_cost + weekly_scrap_cost + weekly_downtime_cost, 2)
                },
                "weekly_revenue": round(weekly_revenue, 2),
                "weekly_profit": round(weekly_revenue - (weekly_energy_cost + weekly_scrap_cost + weekly_downtime_cost), 2),
                "energy_details": {
                    "total_kwh": round(total_weekly_energy_kwh, 2),
                    "cost_per_kwh": self.energy_cost_per_kwh,
                    "breakdown_by_equipment": energy_breakdown.to_dict('records')
                },
                "annualized": {
                    "annual_energy_cost": round(weekly_energy_cost * 52, 2),
                    "annual_scrap_cost": round(weekly_scrap_cost * 52, 2),
                    "annual_downtime_cost": round(weekly_downtime_cost * 52, 2),
                    "annual_revenue": round(weekly_revenue * 52, 2),
                    "annual_profit": round((weekly_revenue - (weekly_energy_cost + weekly_scrap_cost + weekly_downtime_cost)) * 52, 2)
                }
            }
    
    def calculate_optimized_scenario(self, optimization_params: Dict[str, float]) -> Dict[str, Any]:
        """Calculate financial impact of optimization scenario"""
        current_state = self.calculate_current_state_financials()
        
        # Apply optimization parameters
        energy_reduction = optimization_params.get('energy_reduction_percent', 15) / 100
        oee_improvement = optimization_params.get('oee_improvement_percent', 10) / 100
        scrap_reduction = optimization_params.get('scrap_reduction_percent', 30) / 100
        downtime_reduction = optimization_params.get('downtime_reduction_percent', 25) / 100
        
        # Calculate optimized metrics
        optimized_energy_cost = current_state['weekly_costs']['energy_cost'] * (1 - energy_reduction)
        optimized_scrap_cost = current_state['weekly_costs']['scrap_cost'] * (1 - scrap_reduction)
        optimized_downtime_cost = current_state['weekly_costs']['downtime_cost'] * (1 - downtime_reduction)
        
        # Revenue increases with OEE improvement
        optimized_revenue = current_state['weekly_revenue'] * (1 + oee_improvement)
        
        # Calculate savings
        weekly_energy_savings = current_state['weekly_costs']['energy_cost'] - optimized_energy_cost
        weekly_scrap_savings = current_state['weekly_costs']['scrap_cost'] - optimized_scrap_cost
        weekly_downtime_savings = current_state['weekly_costs']['downtime_cost'] - optimized_downtime_cost
        weekly_revenue_increase = optimized_revenue - current_state['weekly_revenue']
        
        total_weekly_benefit = weekly_energy_savings + weekly_scrap_savings + weekly_downtime_savings + weekly_revenue_increase
        
        return {
            "optimization_parameters": optimization_params,
            "weekly_savings": {
                "energy_savings": round(weekly_energy_savings, 2),
                "scrap_savings": round(weekly_scrap_savings, 2),
                "downtime_savings": round(weekly_downtime_savings, 2),
                "revenue_increase": round(weekly_revenue_increase, 2),
                "total_benefit": round(total_weekly_benefit, 2)
            },
            "optimized_costs": {
                "energy_cost": round(optimized_energy_cost, 2),
                "scrap_cost": round(optimized_scrap_cost, 2),
                "downtime_cost": round(optimized_downtime_cost, 2),
                "total_cost": round(optimized_energy_cost + optimized_scrap_cost + optimized_downtime_cost, 2)
            },
            "optimized_revenue": round(optimized_revenue, 2),
            "optimized_profit": round(optimized_revenue - (optimized_energy_cost + optimized_scrap_cost + optimized_downtime_cost), 2),
            "annualized_benefit": {
                "annual_energy_savings": round(weekly_energy_savings * 52, 2),
                "annual_scrap_savings": round(weekly_scrap_savings * 52, 2),
                "annual_downtime_savings": round(weekly_downtime_savings * 52, 2),
                "annual_revenue_increase": round(weekly_revenue_increase * 52, 2),
                "total_annual_benefit": round(total_weekly_benefit * 52, 2)
            },
            "roi_metrics": self._calculate_roi_metrics(
                implementation_cost=15000,  # Estimated implementation cost
                weekly_benefit=total_weekly_benefit,
                time_horizon_weeks=52
            )
        }
    
    def _calculate_roi_metrics(self, implementation_cost: float, weekly_benefit: float, time_horizon_weeks: int) -> Dict[str, Any]:
        """Calculate ROI metrics"""
        # Simple payback period
        payback_weeks = implementation_cost / weekly_benefit if weekly_benefit > 0 else float('inf')
        
        # NPV calculation (simplified, weekly discount rate)
        discount_rate_weekly = 0.10 / 52  # 10% annual rate
        npv = -implementation_cost
        for week in range(1, time_horizon_weeks + 1):
            npv += weekly_benefit / (1 + discount_rate_weekly) ** week
        
        # ROI percentage
        total_benefit = weekly_benefit * time_horizon_weeks
        roi_percentage = ((total_benefit - implementation_cost) / implementation_cost) * 100 if implementation_cost > 0 else 0
        
        return {
            "implementation_cost": implementation_cost,
            "payback_weeks": round(payback_weeks, 1),
            "payback_months": round(payback_weeks / 4.33, 1),
            "npv": round(npv, 2),
            "roi_percentage": round(roi_percentage, 1),
            "break_even_date": (datetime.now() + timedelta(weeks=payback_weeks)).strftime('%Y-%m-%d') if payback_weeks < float('inf') else "N/A"
        }
    
    def generate_financial_report(self) -> str:
        """Generate comprehensive financial report"""
        current_state = self.calculate_current_state_financials()
        
        # Define optimization scenario
        optimization_params = {
            'energy_reduction_percent': 15,
            'oee_improvement_percent': 10,
            'scrap_reduction_percent': 30,
            'downtime_reduction_percent': 25
        }
        
        optimized = self.calculate_optimized_scenario(optimization_params)
        
        report = []
        report.append("=" * 80)
        report.append("VIRTUAL TWIN FINANCIAL ROI ANALYSIS")
        report.append("=" * 80)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")
        
        # Current State
        report.append("CURRENT STATE (Weekly)")
        report.append("-" * 40)
        report.append(f"  Production:")
        report.append(f"    Good Units: {current_state['weekly_metrics']['total_good_units']:,}")
        report.append(f"    Scrap Units: {current_state['weekly_metrics']['total_scrap_units']:,}")
        report.append(f"    Average OEE: {current_state['weekly_metrics']['avg_oee']}%")
        report.append(f"    Downtime Hours: {current_state['weekly_metrics']['downtime_hours']:.1f}")
        report.append("")
        report.append(f"  Energy Consumption:")
        report.append(f"    Total: {current_state['energy_details']['total_kwh']:,.1f} kWh")
        report.append(f"    Cost: ${current_state['weekly_costs']['energy_cost']:,.2f}")
        for equip in current_state['energy_details']['breakdown_by_equipment']:
            report.append(f"    {equip['equipment_type']}: {equip['total_kwh']:,.1f} kWh")
        report.append("")
        report.append(f"  Weekly Costs:")
        report.append(f"    Energy: ${current_state['weekly_costs']['energy_cost']:,.2f}")
        report.append(f"    Scrap: ${current_state['weekly_costs']['scrap_cost']:,.2f}")
        report.append(f"    Downtime: ${current_state['weekly_costs']['downtime_cost']:,.2f}")
        report.append(f"    TOTAL: ${current_state['weekly_costs']['total_cost']:,.2f}")
        report.append("")
        report.append(f"  Weekly Revenue: ${current_state['weekly_revenue']:,.2f}")
        report.append(f"  Weekly Profit: ${current_state['weekly_profit']:,.2f}")
        report.append("")
        
        # Optimization Scenario
        report.append("OPTIMIZATION SCENARIO")
        report.append("-" * 40)
        report.append(f"  Parameters:")
        report.append(f"    Energy Reduction: {optimization_params['energy_reduction_percent']}%")
        report.append(f"    OEE Improvement: {optimization_params['oee_improvement_percent']}%")
        report.append(f"    Scrap Reduction: {optimization_params['scrap_reduction_percent']}%")
        report.append(f"    Downtime Reduction: {optimization_params['downtime_reduction_percent']}%")
        report.append("")
        
        # Savings
        report.append("WEEKLY SAVINGS")
        report.append("-" * 40)
        report.append(f"  Energy Savings: ${optimized['weekly_savings']['energy_savings']:,.2f}")
        report.append(f"  Scrap Reduction: ${optimized['weekly_savings']['scrap_savings']:,.2f}")
        report.append(f"  Downtime Savings: ${optimized['weekly_savings']['downtime_savings']:,.2f}")
        report.append(f"  Revenue Increase: ${optimized['weekly_savings']['revenue_increase']:,.2f}")
        report.append(f"  TOTAL BENEFIT: ${optimized['weekly_savings']['total_benefit']:,.2f}")
        report.append("")
        
        # Annual Impact
        report.append("ANNUAL IMPACT")
        report.append("-" * 40)
        report.append(f"  Energy Savings: ${optimized['annualized_benefit']['annual_energy_savings']:,.2f}")
        report.append(f"  Scrap Savings: ${optimized['annualized_benefit']['annual_scrap_savings']:,.2f}")
        report.append(f"  Downtime Savings: ${optimized['annualized_benefit']['annual_downtime_savings']:,.2f}")
        report.append(f"  Revenue Increase: ${optimized['annualized_benefit']['annual_revenue_increase']:,.2f}")
        report.append(f"  TOTAL ANNUAL BENEFIT: ${optimized['annualized_benefit']['total_annual_benefit']:,.2f}")
        report.append("")
        
        # ROI Metrics
        report.append("RETURN ON INVESTMENT")
        report.append("-" * 40)
        roi = optimized['roi_metrics']
        report.append(f"  Implementation Cost: ${roi['implementation_cost']:,.2f}")
        report.append(f"  Payback Period: {roi['payback_weeks']:.1f} weeks ({roi['payback_months']:.1f} months)")
        report.append(f"  Break-even Date: {roi['break_even_date']}")
        report.append(f"  Net Present Value: ${roi['npv']:,.2f}")
        report.append(f"  ROI: {roi['roi_percentage']:.1f}%")
        report.append("")
        
        # Summary
        report.append("RECOMMENDATION")
        report.append("-" * 40)
        if roi['payback_weeks'] < 12:
            report.append("  ✅ STRONG BUY - Excellent ROI with quick payback")
        elif roi['payback_weeks'] < 26:
            report.append("  ✅ BUY - Good ROI with reasonable payback period")
        elif roi['payback_weeks'] < 52:
            report.append("  ⚠️  CONSIDER - Moderate ROI, evaluate alternatives")
        else:
            report.append("  ❌ WAIT - Long payback period, consider improvements")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Run financial ROI demonstration"""
    print("FINANCIAL ROI ANALYSIS")
    print("=" * 80)
    
    analyzer = FinancialROIAnalyzer()
    
    # Generate and print report
    report = analyzer.generate_financial_report()
    print(report)
    
    # Also get raw data for potential API usage
    print("\n" + "=" * 80)
    print("RAW FINANCIAL DATA (JSON Format)")
    print("=" * 80)
    
    current_state = analyzer.calculate_current_state_financials()
    print("\nCurrent State Summary:")
    print(json.dumps({
        "weekly_costs": current_state['weekly_costs'],
        "weekly_profit": current_state['weekly_profit'],
        "energy_kwh_per_week": current_state['energy_details']['total_kwh']
    }, indent=2))
    
    optimization = analyzer.calculate_optimized_scenario({
        'energy_reduction_percent': 15,
        'oee_improvement_percent': 10,
        'scrap_reduction_percent': 30,
        'downtime_reduction_percent': 25
    })
    
    print("\nOptimization Impact:")
    print(json.dumps({
        "weekly_savings": optimization['weekly_savings'],
        "roi_metrics": optimization['roi_metrics']
    }, indent=2))


if __name__ == "__main__":
    main()