#!/bin/bash

# Virtual Twin Command Interface
# Natural language command interface for Virtual Twin operations
# Similar to query-log.sh but for twin-specific commands

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_CMD="${PYTHON_CMD:-python3}"
DB_PATH="${DB_PATH:-data/mes_database.db}"
LOG_FILE="${LOG_FILE:-twin_commands.log}"

# Show help
show_help() {
    cat << EOF
Virtual Twin Command Interface
==============================

USAGE:
    ./twin-command.sh COMMAND [OPTIONS]

COMMANDS:
    simulate    Run a simulation (baseline, scenario, optimization, monte_carlo)
    optimize    Run multi-objective optimization
    roi         Calculate ROI between two runs
    recommend   Get recommendations for a scenario
    status      Show current twin state and recent runs
    demo        Run interactive demo scenarios
    nlp         Process natural language query
    help        Show this help message

EXAMPLES:
    # Run baseline simulation
    ./twin-command.sh simulate baseline

    # Run optimization for OEE and energy
    ./twin-command.sh optimize "oee,energy" "quality>=0.95"

    # Calculate ROI
    ./twin-command.sh roi baseline-001 improved-001

    # Get recommendations
    ./twin-command.sh recommend improve_oee

    # Process natural language
    ./twin-command.sh nlp "What if we reduce micro-stops by 20%?"

    # Run demo
    ./twin-command.sh demo financial_impact

SIMULATION TYPES:
    baseline      Current state simulation
    scenario      What-if scenario
    optimization  Multi-objective optimization
    monte_carlo   Uncertainty analysis

DEMO SCENARIOS:
    financial_impact  Financial impact of reducing micro-stops
    line_comparison   Compare performance between lines
    optimization      Multi-objective optimization demo
    what_if          What-if cascade sensitivity analysis
    root_cause       Root cause analysis for quality issues

EOF
}

# Log command
log_command() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Run simulation
run_simulation() {
    local sim_type="${1:-baseline}"
    local duration="${2:-100}"
    
    echo -e "${BLUE}Running $sim_type simulation...${NC}"
    log_command "simulate" "$sim_type" "$duration"
    
    $PYTHON_CMD << EOF
import sys
sys.path.append('$SCRIPT_DIR')
from twin.simulation_runner import SimulationRunner, RunType

runner = SimulationRunner(db_path='$DB_PATH')

run_type_map = {
    'baseline': RunType.BASELINE,
    'scenario': RunType.SCENARIO,
    'optimization': RunType.OPTIMIZATION,
    'monte_carlo': RunType.MONTE_CARLO
}

result = runner.run_simulation(
    run_type=run_type_map['$sim_type'],
    duration=$duration
)

print(f"\n✅ Simulation complete: {result['run_id']}")
print(f"   Type: $sim_type")
print(f"   Status: {result['status']}")
if 'kpi_summary' in result:
    kpis = result['kpi_summary']
    print(f"   OEE: {kpis.get('mean_oee', 0):.1%}")
    print(f"   Availability: {kpis.get('mean_availability', 0):.1%}")
    print(f"   Performance: {kpis.get('mean_performance', 0):.1%}")
    print(f"   Quality: {kpis.get('mean_quality', 0):.1%}")
EOF
}

# Run optimization
run_optimization() {
    local objectives="${1:-oee,energy}"
    local constraints="${2:-}"
    
    echo -e "${BLUE}Running multi-objective optimization...${NC}"
    echo "Objectives: $objectives"
    echo "Constraints: $constraints"
    log_command "optimize" "$objectives" "$constraints"
    
    $PYTHON_CMD << EOF
import sys
sys.path.append('$SCRIPT_DIR')
from twin.optimization_engine import OptimizationEngine

optimizer = OptimizationEngine()

objectives_list = '$objectives'.split(',')
constraints_list = ['$constraints'] if '$constraints' else []

print("\nOptimizing for:", objectives_list)
if constraints_list[0]:
    print("With constraints:", constraints_list)

result = optimizer.optimize(
    objectives=[f"maximize:{obj}" if obj in ['oee', 'availability', 'performance', 'quality'] 
                else f"minimize:{obj}" for obj in objectives_list],
    constraints=constraints_list,
    n_generations=20,  # Reduced for demo
    population_size=50
)

if 'pareto_front' in result:
    print(f"\n✅ Optimization complete!")
    print(f"   Found {len(result['pareto_front'])} Pareto-optimal solutions")
    print(f"\nTop 3 solutions:")
    for i, sol in enumerate(result['pareto_front'][:3], 1):
        print(f"\n   Solution {i}:")
        for obj in objectives_list:
            if obj in sol:
                print(f"     {obj}: {sol[obj]:.3f}")
EOF
}

# Calculate ROI
calculate_roi() {
    local baseline_id="${1}"
    local improved_id="${2}"
    
    if [ -z "$baseline_id" ] || [ -z "$improved_id" ]; then
        echo -e "${RED}Error: Please provide baseline and improved run IDs${NC}"
        echo "Usage: ./twin-command.sh roi baseline-001 improved-001"
        return 1
    fi
    
    echo -e "${BLUE}Calculating ROI...${NC}"
    log_command "roi" "$baseline_id" "$improved_id"
    
    $PYTHON_CMD << EOF
import sys
sys.path.append('$SCRIPT_DIR')
from twin.cost_impact_calculator import CostImpactCalculator
from twin.simulation_runner import SimulationRunner

runner = SimulationRunner(db_path='$DB_PATH')
calculator = CostImpactCalculator(runner)

try:
    roi = calculator.calculate_roi(
        baseline_run_id='$baseline_id',
        improved_run_id='$improved_id',
        n_simulations=1000
    )
    
    print(f"\n💰 ROI Analysis Complete!")
    print(f"   Implementation Cost: \${roi['implementation_cost']:,.0f}")
    print(f"   Weekly Savings: \${roi['weekly_savings']['mean']:,.0f}")
    print(f"   95% Confidence: \${roi['weekly_savings']['confidence_interval'][0]:,.0f} - \${roi['weekly_savings']['confidence_interval'][1]:,.0f}")
    print(f"   Payback Period: {roi['payback_weeks']['mean']:.1f} weeks")
    print(f"   NPV: \${roi['npv']['mean']:,.0f}")
    print(f"   Probability of Positive NPV: {roi['npv']['probability_positive']:.1%}")
    
except Exception as e:
    print(f"Error: {e}")
    print("Make sure both run IDs exist in the database")
EOF
}

# Get recommendations
get_recommendations() {
    local scenario="${1:-improve_oee}"
    
    echo -e "${BLUE}Getting recommendations for: $scenario${NC}"
    log_command "recommend" "$scenario"
    
    $PYTHON_CMD << EOF
import sys
sys.path.append('$SCRIPT_DIR')
from twin.recommendation_engine import RecommendationEngine

engine = RecommendationEngine()
recommendations = engine.recommend_for_scenario('$scenario')

print(f"\n💡 Recommendations for {recommendations['scenario_description']}:")
print(f"\nRecommended Parameter Changes:")
for param, value in recommendations['parameters'].items():
    print(f"  • {param}: {value:.3f}")

print(f"\nExpected Impact:")
print(f"  • {recommendations['expected_impact']}")

print(f"\nImplementation Steps:")
for i, step in enumerate(recommendations['implementation_steps'], 1):
    print(f"  {i}. {step}")
EOF
}

# Show status
show_status() {
    echo -e "${BLUE}Virtual Twin Status${NC}"
    log_command "status"
    
    $PYTHON_CMD << EOF
import sys
import sqlite3
from datetime import datetime
sys.path.append('$SCRIPT_DIR')

conn = sqlite3.connect('$DB_PATH')
cursor = conn.cursor()

# Get recent runs
cursor.execute("""
    SELECT run_id, run_type, status, timestamp 
    FROM twin_runs 
    ORDER BY timestamp DESC 
    LIMIT 5
""")
runs = cursor.fetchall()

print("\n📊 Recent Simulation Runs:")
print("-" * 60)
for run in runs:
    run_id, run_type, status, timestamp = run
    print(f"{run_id:<20} {run_type:<12} {status:<10} {timestamp}")

# Get record counts
tables = ['mes_data', 'simulation_data', 'quality_data', 'sensor_data']
print("\n📈 Database Statistics:")
print("-" * 60)
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table:<20} {count:>10} records")

conn.close()
EOF
}

# Run demo
run_demo() {
    local scenario="${1:-financial_impact}"
    
    echo -e "${BLUE}Running demo scenario: $scenario${NC}"
    log_command "demo" "$scenario"
    
    $PYTHON_CMD << EOF
import sys
sys.path.append('$SCRIPT_DIR')
from twin.demo_scenarios import VirtualTwinDemo

demo = VirtualTwinDemo()
demo.demonstrate_scenario('$scenario')
EOF
}

# Process natural language
process_nlp() {
    local query="$*"
    
    if [ -z "$query" ]; then
        echo -e "${RED}Error: Please provide a natural language query${NC}"
        echo "Usage: ./twin-command.sh nlp \"What if we reduce micro-stops by 20%?\""
        return 1
    fi
    
    echo -e "${BLUE}Processing: $query${NC}"
    log_command "nlp" "$query"
    
    $PYTHON_CMD << EOF
import sys
sys.path.append('$SCRIPT_DIR')
from twin.natural_language_patterns import NaturalLanguageProcessor, IntentType
from twin.simulation_runner import SimulationRunner

nlp = NaturalLanguageProcessor()
query = "$query"

# Classify intent
intent = nlp.classify_intent(query)
entities = nlp.extract_entities(query)

print(f"\n🧠 Natural Language Analysis:")
print(f"   Intent: {intent.value}")
print(f"   Entities: {entities}")

# Route to appropriate handler
if intent == IntentType.STATUS:
    print("\n→ This requires current data. Use SQL query:")
    print("   ./query-log.sh POST /query -d @query.json")
    
elif intent == IntentType.PREDICTION:
    print("\n→ This requires simulation. Running predictive analysis...")
    runner = SimulationRunner(db_path='$DB_PATH')
    # Would run actual simulation based on extracted parameters
    print("   Simulation would adjust parameters based on: {entities}")
    
elif intent == IntentType.OPTIMIZATION:
    print("\n→ This requires optimization. Use:")
    print("   ./twin-command.sh optimize \"oee,energy\"")
    
elif intent == IntentType.RECOMMENDATION:
    print("\n→ Getting recommendations...")
    print("   ./twin-command.sh recommend improve_oee")
    
else:
    print(f"\n→ Intent type {intent.value} identified")
    print("   Further processing needed based on specific query")
EOF
}

# Main command router
case "${1:-help}" in
    simulate)
        run_simulation "${2}" "${3}"
        ;;
    optimize)
        run_optimization "${2}" "${3}"
        ;;
    roi)
        calculate_roi "${2}" "${3}"
        ;;
    recommend)
        get_recommendations "${2}"
        ;;
    status)
        show_status
        ;;
    demo)
        run_demo "${2}"
        ;;
    nlp)
        shift
        process_nlp "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Use './twin-command.sh help' for usage information"
        exit 1
        ;;
esac