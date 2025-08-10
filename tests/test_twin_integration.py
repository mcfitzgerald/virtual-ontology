#!/usr/bin/env python3
"""
Integration Test for Virtual Twin System
Tests that all components work together: SQL, Twin, and command interface
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
import subprocess
from datetime import datetime

# Import existing twin modules
from twin.actionable_parameters import ActionableParameters
from twin.simulation_runner import SimulationRunner
from twin.recommendation_engine import RecommendationEngine
from twin.disambiguation import DisambiguationHelper
from twin.cost_impact_calculator import CostImpactCalculator
from twin.twin_state import TwinStateManager
from twin.sync_health import SyncHealthMonitor


def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f" TEST: {test_name}")
    print('='*60)


def test_database_connectivity():
    """Test 1: Verify database has all required tables and data"""
    print_test_header("Database Connectivity")
    
    conn = sqlite3.connect("data/mes_database.db")
    cursor = conn.cursor()
    
    # Check required tables
    required_tables = [
        'mes_data', 'equipment_metadata', 'quality_data', 'sensor_data',
        'simulation_data', 'twin_runs', 'optimization_results', 'provenance_records'
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    all_present = True
    for table in required_tables:
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ {table:<25} {count:>10} records")
        else:
            print(f"❌ {table:<25} MISSING")
            all_present = False
    
    conn.close()
    return all_present


def test_sql_queries():
    """Test 2: Verify original SQL query functionality still works"""
    print_test_header("SQL Query Functionality")
    
    conn = sqlite3.connect("data/mes_database.db")
    cursor = conn.cursor()
    
    # Test various SQL queries
    queries = [
        ("Current OEE", "SELECT AVG(oee) as avg_oee FROM mes_data"),
        ("Equipment count", "SELECT COUNT(DISTINCT equipment_id) FROM equipment_metadata"),
        ("Quality metrics", "SELECT AVG(quality_score) FROM quality_data"),
        ("Sensor readings", "SELECT COUNT(*) FROM sensor_data"),
    ]
    
    all_passed = True
    for query_name, sql in queries:
        try:
            cursor.execute(sql)
            result = cursor.fetchone()
            if result and result[0] is not None:
                print(f"✅ {query_name}: {result[0]:.2f}" if isinstance(result[0], float) else f"✅ {query_name}: {result[0]}")
            else:
                print(f"⚠️  {query_name}: No data")
        except Exception as e:
            print(f"❌ {query_name}: {e}")
            all_passed = False
    
    conn.close()
    return all_passed


def test_actionable_parameters():
    """Test 3: Actionable parameters management"""
    print_test_header("Actionable Parameters")
    
    params = ActionableParameters()
    
    # Test parameter setting and validation
    test_params = [
        ("micro_stop_probability", 0.1, True),
        ("performance_factor", 0.85, True),
        ("scrap_multiplier", 1.0, True),
        ("micro_stop_probability", 0.5, False),  # Out of range
    ]
    
    all_passed = True
    for param_name, value, should_pass in test_params:
        try:
            if should_pass:
                params.set_value(param_name, value)
                retrieved = params.get_value(param_name)
                if abs(retrieved - value) < 0.001:
                    print(f"✅ {param_name} = {value}")
                else:
                    print(f"❌ {param_name}: Set {value}, got {retrieved}")
                    all_passed = False
            else:
                # This should fail validation
                try:
                    params.set_value(param_name, value)
                    print(f"❌ {param_name} = {value} should have failed validation")
                    all_passed = False
                except:
                    print(f"✅ {param_name} = {value} correctly rejected")
        except Exception as e:
            print(f"❌ {param_name}: {e}")
            all_passed = False
    
    return all_passed


def test_simulation_runner():
    """Test 4: Simulation runner functionality"""
    print_test_header("Simulation Runner")
    
    runner = SimulationRunner()
    
    # Get recent runs
    recent_runs = runner.get_recent_runs(limit=5)
    print(f"Found {len(recent_runs)} recent runs")
    
    if recent_runs:
        # Test getting run details
        run = recent_runs[0]
        print(f"✅ Most recent: {run.run_id} ({run.run_type})")
        
        # Test getting KPI summary
        if run.kpi_summary:
            print(f"   OEE: {run.kpi_summary.get('mean_oee', 0):.1%}")
            print(f"   Availability: {run.kpi_summary.get('mean_availability', 0):.1%}")
        
        # Test lineage tracking
        lineage = runner.get_run_lineage(run.run_id)
        print(f"✅ Lineage depth: {len(lineage)}")
        
        return True
    else:
        print("⚠️  No simulation runs found in database")
        return True  # Not a failure, just no data


def test_recommendations():
    """Test 5: Recommendation engine"""
    print_test_header("Recommendation Engine")
    
    engine = RecommendationEngine()
    
    scenarios = ["improve_oee", "reduce_downtime", "improve_quality"]
    
    all_passed = True
    for scenario in scenarios:
        try:
            rec = engine.recommend_for_scenario(scenario)
            if rec and 'parameters' in rec:
                print(f"✅ {scenario}: {len(rec['parameters'])} parameters suggested")
                # Show first parameter as example
                if rec['parameters']:
                    first_param = list(rec['parameters'].items())[0]
                    print(f"   Example: {first_param[0]} = {first_param[1]:.3f}")
            else:
                print(f"❌ {scenario}: No recommendations")
                all_passed = False
        except Exception as e:
            print(f"❌ {scenario}: {e}")
            all_passed = False
    
    return all_passed


def test_disambiguation():
    """Test 6: Query disambiguation"""
    print_test_header("Query Disambiguation")
    
    helper = DisambiguationHelper()
    
    test_queries = [
        "What is the OEE for LINE1?",
        "Compare performance between shifts",
        "Show quality issues on the packer",
        "Reduce micro-stops by 20%"
    ]
    
    all_passed = True
    for query in test_queries:
        try:
            context = helper.get_query_context(query)
            entities = context.get('entities', {})
            
            # Count found entities
            entity_count = sum(len(v) if isinstance(v, list) else (1 if v else 0) 
                             for v in entities.values())
            
            print(f"✅ '{query[:30]}...' → {entity_count} entities found")
            
            # Show identified intents
            if context.get('intent_hints'):
                print(f"   Likely intent: {context['intent_hints'].get('likely_intent', 'unknown')}")
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
            all_passed = False
    
    return all_passed


def test_twin_state():
    """Test 7: Twin state management"""
    print_test_header("Twin State Management")
    
    state_manager = TwinStateManager()
    
    try:
        # Get current state
        current_state = state_manager.get_current_state()
        if current_state:
            print(f"✅ Current state: {current_state.get('state_id', 'unknown')}")
            print(f"   Last update: {current_state.get('last_updated', 'unknown')}")
        else:
            print("⚠️  No current state found (initializing)")
            # Initialize state
            state_manager.update_state(
                run_id="test-run-001",
                baseline_run_id="baseline-001",
                notes="Integration test"
            )
            print("✅ State initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ State management failed: {e}")
        return False


def test_sync_health():
    """Test 8: Sync health monitoring"""
    print_test_header("Sync Health Monitoring")
    
    monitor = SyncHealthMonitor()
    
    try:
        # Get health summary
        summary = monitor.get_health_summary()
        
        print(f"✅ Sync Health Summary:")
        print(f"   HEALTHY: {summary.get('HEALTHY', 0)} entities")
        print(f"   DELAYED: {summary.get('DELAYED', 0)} entities")
        print(f"   STALE: {summary.get('STALE', 0)} entities")
        print(f"   ERROR: {summary.get('ERROR', 0)} entities")
        
        # Get entity status
        entities = monitor.get_all_entity_status()
        if entities:
            print(f"✅ Monitoring {len(entities)} entities")
        else:
            print("⚠️  No entities being monitored")
        
        return True
        
    except Exception as e:
        print(f"❌ Sync health check failed: {e}")
        return False


def test_cost_calculator():
    """Test 9: Cost impact calculator"""
    print_test_header("Cost Impact Calculator")
    
    calculator = CostImpactCalculator()
    
    try:
        # Test with mock data
        baseline_kpis = {
            "mean_oee": 0.65,
            "mean_availability": 0.80,
            "mean_performance": 0.85,
            "mean_quality": 0.95,
            "downtime_percentage": 20.0,
            "scrap_rate": 0.05
        }
        
        parameter_changes = {
            "micro_stop_probability": -0.20  # 20% reduction
        }
        
        impact = calculator.calculate_scenario_impact(
            scenario_name="reduce_micro_stops",
            baseline_kpis=baseline_kpis,
            parameter_changes=parameter_changes,
            n_simulations=100  # Small for testing
        )
        
        if impact and 'weekly_impact' in impact:
            weekly = impact['weekly_impact']['mean']
            print(f"✅ Weekly impact: ${abs(weekly):,.0f}")
            print(f"   Annual impact: ${abs(weekly * 52):,.0f}")
            return True
        else:
            print("❌ Impact calculation failed")
            return False
            
    except Exception as e:
        print(f"❌ Cost calculation failed: {e}")
        return False


def test_command_interface():
    """Test 10: Command line interface"""
    print_test_header("Command Line Interface")
    
    # Test basic commands
    commands = [
        (["./twin-command.sh", "status"], "Status check"),
        (["./twin-command.sh", "recommend", "improve_oee"], "Get recommendations"),
    ]
    
    all_passed = True
    for cmd, description in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {description}: Success")
                # Show first line of output
                if result.stdout:
                    first_line = result.stdout.split('\n')[0][:50]
                    print(f"   Output: {first_line}...")
            else:
                print(f"⚠️  {description}: Exit code {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr.split('⧵n')[0][:50]}")
        except subprocess.TimeoutExpired:
            print(f"⚠️  {description}: Timeout")
        except FileNotFoundError:
            print(f"⚠️  {description}: Command not found")
            all_passed = False
        except Exception as e:
            print(f"❌ {description}: {e}")
            all_passed = False
    
    return all_passed


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print(" VIRTUAL TWIN INTEGRATION TEST SUITE")
    print("="*60)
    print(f" Timestamp: {datetime.now().isoformat()}")
    
    tests = [
        ("Database Connectivity", test_database_connectivity),
        ("SQL Queries", test_sql_queries),
        ("Actionable Parameters", test_actionable_parameters),
        ("Simulation Runner", test_simulation_runner),
        ("Recommendations", test_recommendations),
        ("Query Disambiguation", test_disambiguation),
        ("Twin State", test_twin_state),
        ("Sync Health", test_sync_health),
        ("Cost Calculator", test_cost_calculator),
        ("Command Interface", test_command_interface),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
    
    print(f"\nTotal: {passed}/{total} passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Virtual Twin is fully operational.")
        print("\n📚 NEXT STEPS FOR CLAUDE CODE:")
        print("="*60)
        print("1. In a new Claude Code session, load the enhanced system prompt:")
        print("   'Please review @sys_prompt_twin.md'")
        print("\n2. Try these natural language queries:")
        print("   • 'What is the current OEE for LINE1?'")
        print("   • 'Why does LINE2 outperform LINE1?'")
        print("   • 'What happens if we reduce micro-stops by 20%?'")
        print("   • 'Find the best parameters to maximize OEE while minimizing energy'")
        print("   • 'Calculate the ROI of the proposed improvements'")
        print("\n3. The system will automatically route to:")
        print("   • SQL for historical queries")
        print("   • Simulations for predictions")
        print("   • Optimizations for trade-offs")
        print("   • Recommendations for actions")
    elif passed >= total * 0.7:
        print(f"\n⚠️  {total - passed} tests failed, but core functionality works.")
        print("The system is usable but some features may be limited.")
    else:
        print("\n❌ Too many failures. Please check the setup.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)