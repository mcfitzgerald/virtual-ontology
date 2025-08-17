"""
Debug test to understand why production is not flowing.
"""

import sys
import os

# Add parent directory to path to import twin_model
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from twin_model import SimulationRunner


def debug_simulation() -> None:
    """Debug simulation to see what's happening."""
    print("DEBUG: Running extended simulation")
    print("=" * 60)

    runner = SimulationRunner()

    # Run for 1 day to see if production flows
    results = runner.run_simulation(duration_days=1, seed=42)

    print(f"Simulation ran for {results.duration_minutes} minutes")
    print(f"MES snapshots: {len(results.mes_data)}")

    # Check each line
    for line_id, summary in results.line_summaries.items():
        print(f"\n{line_id}:")
        print(f"  Input: {summary['total_input']}")
        print(f"  Output: {summary['total_output']}")
        print(f"  Scrap: {summary['total_scrap']}")

        # Check equipment
        print("  Equipment:")
        for eq_stats in summary["equipment_stats"]:
            print(f"    {eq_stats['equipment_id']}:")
            print(f"      Units produced: {eq_stats['units_produced']}")
            print(f"      Units scrapped: {eq_stats['units_scrapped']}")
            print(f"      State durations: {eq_stats['state_durations']}")
            print(f"      Failures: {eq_stats['failure_count']}")
            print(f"      Starvations: {eq_stats['starvation_count']}")
            print(f"      Blockages: {eq_stats['blockage_count']}")

        # Check buffers
        print("  Buffers:")
        for buf_stats in summary["buffer_stats"]:
            print(f"    {buf_stats['buffer_id']}:")
            print(
                f"      Current: {buf_stats['current_level']}/{buf_stats['capacity']}"
            )
            print(f"      Total puts: {buf_stats['total_puts']}")
            print(f"      Total gets: {buf_stats['total_gets']}")
            print(f"      Max level: {buf_stats['max_level']}")


if __name__ == "__main__":
    debug_simulation()
