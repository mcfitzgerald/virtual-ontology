"""
Test script for the SimPy twin model.

Validates functionality and demonstrates parameter sensitivity.
"""

import sys
import os

# Add parent directory to path to import twin_model
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from twin_model import SimulationRunner, SimulationConfig, ActionableParameters
import time


def test_basic_simulation() -> None:
    """Test basic simulation functionality."""
    print("=" * 60)
    print("TEST 1: Basic Simulation")
    print("=" * 60)

    # Create runner with default config
    runner = SimulationRunner()

    # Run short simulation (1 hour)
    start_time = time.time()
    results = runner.run_simulation(
        duration_days=1 / 24,  # 1 hour
        seed=42,
    )
    elapsed = time.time() - start_time

    print(f"Simulation completed in {elapsed:.2f} seconds")
    print(f"Duration: {results.duration_minutes:.0f} minutes")
    print(f"MES snapshots collected: {len(results.mes_data)}")

    # Display KPIs
    print("\nKey Performance Indicators:")
    for key, value in results.kpi_summary.items():
        # Format numeric values with 2 decimal places
        print(f"  {key}: {value:.2f}")

    # Display line summaries
    print("\nLine Summaries:")
    for line_id, summary in results.line_summaries.items():
        print(f"\n  {line_id}:")
        print(f"    Total Input: {summary['total_input']}")
        print(f"    Total Output: {summary['total_output']}")
        print(f"    Total Scrap: {summary['total_scrap']}")
        print(f"    Line Efficiency: {summary['line_efficiency']:.1f}%")
        print(f"    OEE: {summary['line_oee']['oee']:.1f}%")
        if summary["bottleneck"]:
            print(f"    Bottleneck: {summary['bottleneck']}")


def test_parameter_sensitivity() -> None:
    """Test parameter sensitivity."""
    print("\n" + "=" * 60)
    print("TEST 2: Parameter Sensitivity")
    print("=" * 60)

    runner = SimulationRunner()

    # Test each parameter
    parameters_to_test = [
        ("micro_stop_probability", [0.5, 1.0, 2.0]),
        ("performance_factor", [0.8, 1.0, 1.2]),
        ("scrap_multiplier", [0.5, 1.0, 2.0]),
        ("material_reliability", [0.8, 1.0, 1.2]),
        ("cascade_sensitivity", [0.5, 1.0, 2.0]),
    ]

    for param_name, values in parameters_to_test:
        print(f"\nTesting {param_name}:")

        for value in values:
            # Create parameters with single change
            params = ActionableParameters()
            setattr(params, param_name, value)

            # Run simulation
            results = runner.run_simulation(
                parameters=params,
                duration_days=1 / 24,  # 1 hour
                seed=42,
            )

            mean_oee = results.kpi_summary["mean_oee"]
            total_output = results.kpi_summary["total_units_produced"]

            print(
                f"  {param_name}={value:.1f}: OEE={mean_oee:.1f}%, Output={total_output}"
            )


def test_parameter_impact() -> None:
    """Calculate parameter impact on OEE."""
    print("\n" + "=" * 60)
    print("TEST 3: Parameter Impact Analysis")
    print("=" * 60)

    runner = SimulationRunner()

    # Baseline simulation
    baseline_params = ActionableParameters()
    baseline_results = runner.run_simulation(
        parameters=baseline_params,
        duration_days=1 / 12,  # 2 hours for more stable results
        seed=42,
    )
    baseline_oee = baseline_results.kpi_summary["mean_oee"]

    print(f"Baseline OEE: {baseline_oee:.1f}%")

    # Test range for each parameter
    test_cases = [
        ("micro_stop_probability", 0.5, 2.0),  # Less to more failures
        ("performance_factor", 0.8, 1.2),  # Slower to faster
        ("scrap_multiplier", 0.5, 2.0),  # Better to worse quality
        ("material_reliability", 0.8, 1.2),  # Less to more reliable
        ("cascade_sensitivity", 0.5, 2.0),  # Loose to tight coupling
    ]

    print("\nParameter Impact on OEE:")

    for param_name, low_value, high_value in test_cases:
        # Test low value
        low_params = ActionableParameters()
        setattr(low_params, param_name, low_value)
        low_results = runner.run_simulation(
            parameters=low_params, duration_days=1 / 12, seed=42
        )
        low_oee = low_results.kpi_summary["mean_oee"]

        # Test high value
        high_params = ActionableParameters()
        setattr(high_params, param_name, high_value)
        high_results = runner.run_simulation(
            parameters=high_params, duration_days=1 / 12, seed=42
        )
        high_oee = high_results.kpi_summary["mean_oee"]

        # Calculate impact
        impact = abs(high_oee - low_oee)
        direction = "positive" if high_oee > low_oee else "negative"

        print(f"  {param_name}:")
        print(f"    Low ({low_value}): {low_oee:.1f}%")
        print(f"    High ({high_value}): {high_oee:.1f}%")
        print(f"    Impact: {impact:.1f}% ({direction})")
        if baseline_oee > 0:
            print(f"    Relative change: {impact / baseline_oee * 100:.1f}%")
        else:
            print("    Relative change: N/A (baseline OEE is 0)")


def test_bottleneck_detection() -> None:
    """Test bottleneck detection."""
    print("\n" + "=" * 60)
    print("TEST 4: Bottleneck Detection")
    print("=" * 60)

    # Create custom config with clear bottleneck
    config = SimulationConfig.create_default_config()

    # Make the packer much slower in LINE1
    config.line_configs[0].equipment_configs[1].base_rate = 30.0  # Half speed

    runner = SimulationRunner(config)
    results = runner.run_simulation(duration_days=1 / 24, seed=42)

    for line_id, summary in results.line_summaries.items():
        print(f"\n{line_id}:")
        print(f"  Bottleneck: {summary['bottleneck']}")

        # Show equipment OEEs
        for eq_stats in summary["equipment_stats"]:
            print(f"  {eq_stats['equipment_id']}: OEE={eq_stats['oee']:.1f}%")


def test_mes_data_structure() -> None:
    """Test MES data structure."""
    print("\n" + "=" * 60)
    print("TEST 5: MES Data Structure")
    print("=" * 60)

    runner = SimulationRunner()
    results = runner.run_simulation(
        duration_days=1 / 24,  # 1 hour
        seed=42,
    )

    if results.mes_data:
        # Show first snapshot structure
        first_snapshot = results.mes_data[0]
        print(f"MES Snapshot at t={first_snapshot['timestamp']:.1f} minutes:")
        print(f"  Line: {first_snapshot['line_id']}")
        print(f"  OEE: {first_snapshot['line_oee']['oee']:.1f}%")
        print(f"  Bottleneck: {first_snapshot['bottleneck']}")

        print("\n  Equipment States:")
        for eq_id, state_info in first_snapshot["equipment_states"].items():
            print(f"    {eq_id}: {state_info['state']}")

        print("\n  Buffer Levels:")
        for buffer_id, level_info in first_snapshot["buffer_levels"].items():
            print(
                f"    {buffer_id}: {level_info['level']}/{level_info['capacity']} ({level_info['utilization']:.1f}%)"
            )


def main() -> None:
    """Run all tests."""
    print("SimPy Twin Model Test Suite")
    print("=" * 60)

    # Check if simpy is installed
    try:
        import simpy

        print(f"SimPy version: {simpy.__version__}")
    except ImportError:
        print("ERROR: SimPy not installed. Please run: pip install simpy")
        return

    # Run tests
    test_basic_simulation()
    test_parameter_sensitivity()
    test_parameter_impact()
    test_bottleneck_detection()
    test_mes_data_structure()

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
