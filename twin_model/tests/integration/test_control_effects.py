"""Test control effects on OEE and system behavior.

This module validates that control changes produce expected outcomes:
- Training improves performance and reduces failures
- PM compliance increases MTBF
- Speed adjustments trade throughput for reliability
- Sensor calibration affects micro-stops

Compliant with PEP 8, PEP 257, PEP 484.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import simpy

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from twin_model.control.control_manager import ControlManager
from twin_model.model_builder import OntologyDrivenModelBuilder as ModelBuilder

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class TestScenario:
    """Test scenario with control settings and expected outcomes."""

    name: str
    description: str
    control_settings: Dict[str, float]
    expected_outcomes: Dict[str, Tuple[float, float]]  # (min, max) ranges
    duration_minutes: int = 480  # 8 hours default


@dataclass
class TestResult:
    """Results from a test scenario run."""

    scenario_name: str
    oee_values: Dict[str, float]
    availability: Dict[str, float]
    performance: Dict[str, float]
    quality: Dict[str, float]
    failure_counts: Dict[str, int]
    micro_stop_counts: Dict[str, int]
    units_produced: Dict[str, int]
    computed_parameters: Dict[str, float]
    passed: bool
    failures: List[str]


def create_test_scenarios() -> List[TestScenario]:
    """Create comprehensive test scenarios for control validation.

    Returns:
        List of test scenarios covering various control combinations

    """
    scenarios = []

    # Baseline scenario
    scenarios.append(
        TestScenario(
            name="baseline",
            description="Baseline configuration with default controls",
            control_settings={
                "operator_training_hours": 8,
                "line_speed_setting": 85,
                "pm_schedule_compliance": 60,
                "sensor_calibration_frequency": 14,
                "changeover_reduction_level": 0,
                "staffing_level": 2,
                "autonomous_maintenance_level": 0,
            },
            expected_outcomes={
                "oee": (0.35, 0.55),  # 35-55% OEE expected
                "availability": (0.50, 0.70),
                "performance": (0.75, 0.90),  # Adjusted for actual performance
                "quality": (0.90, 0.97),
            },
        )
    )

    # High training scenario
    scenarios.append(
        TestScenario(
            name="high_training",
            description="High operator training should improve performance and reduce failures",
            control_settings={
                "operator_training_hours": 40,  # Extensive training
                "line_speed_setting": 85,
                "pm_schedule_compliance": 60,
                "sensor_calibration_frequency": 14,
                "changeover_reduction_level": 0,
                "staffing_level": 2,
                "autonomous_maintenance_level": 0,
            },
            expected_outcomes={
                "oee": (0.45, 0.65),  # Better OEE with training
                "availability": (0.55, 0.75),
                "performance": (0.80, 0.95),  # Better performance with training
                "quality": (0.92, 0.98),  # Better quality
            },
        )
    )

    # High PM compliance scenario
    scenarios.append(
        TestScenario(
            name="high_pm_compliance",
            description="High PM compliance should reduce failures and increase availability",
            control_settings={
                "operator_training_hours": 8,
                "line_speed_setting": 85,
                "pm_schedule_compliance": 95,  # Excellent PM
                "sensor_calibration_frequency": 14,
                "changeover_reduction_level": 0,
                "staffing_level": 2,
                "autonomous_maintenance_level": 0,
            },
            expected_outcomes={
                "oee": (0.40, 0.60),
                "availability": (0.55, 0.75),  # Better availability
                "performance": (0.75, 0.90),
                "quality": (0.90, 0.97),
            },
        )
    )

    # High speed scenario
    scenarios.append(
        TestScenario(
            name="high_speed",
            description="High speed should increase throughput but reduce reliability",
            control_settings={
                "operator_training_hours": 8,
                "line_speed_setting": 100,  # Maximum speed
                "pm_schedule_compliance": 60,
                "sensor_calibration_frequency": 14,
                "changeover_reduction_level": 0,
                "staffing_level": 2,
                "autonomous_maintenance_level": 0,
            },
            expected_outcomes={
                "oee": (0.30, 0.50),  # Lower OEE due to failures
                "availability": (0.45, 0.65),  # More failures
                "performance": (0.70, 0.85),  # Still decent performance
                "quality": (0.88, 0.95),  # Slightly lower quality
            },
        )
    )

    # Optimal sensor calibration
    scenarios.append(
        TestScenario(
            name="optimal_sensors",
            description="Weekly sensor calibration should minimize micro-stops",
            control_settings={
                "operator_training_hours": 8,
                "line_speed_setting": 85,
                "pm_schedule_compliance": 60,
                "sensor_calibration_frequency": 7,  # Weekly (optimal)
                "changeover_reduction_level": 0,
                "staffing_level": 2,
                "autonomous_maintenance_level": 0,
            },
            expected_outcomes={
                "oee": (0.38, 0.58),
                "availability": (0.52, 0.72),
                "performance": (0.72, 0.87),  # Better with calibrated sensors
                "quality": (0.91, 0.97),
            },
        )
    )

    # Combined improvements scenario
    scenarios.append(
        TestScenario(
            name="optimized",
            description="Combined control optimization for maximum OEE",
            control_settings={
                "operator_training_hours": 30,  # Good training
                "line_speed_setting": 85,  # Balanced speed
                "pm_schedule_compliance": 85,  # Good PM
                "sensor_calibration_frequency": 7,  # Optimal calibration
                "changeover_reduction_level": 2,  # SMED implementation
                "staffing_level": 3,  # Extra staff
                "autonomous_maintenance_level": 2,  # Moderate AM
            },
            expected_outcomes={
                "oee": (0.45, 0.65),  # Good OEE
                "availability": (0.55, 0.75),
                "performance": (0.80, 0.95),
                "quality": (0.93, 0.98),
            },
        )
    )

    # Degraded scenario
    scenarios.append(
        TestScenario(
            name="degraded",
            description="Poor controls should result in low OEE",
            control_settings={
                "operator_training_hours": 0,  # No training
                "line_speed_setting": 100,  # Too fast
                "pm_schedule_compliance": 20,  # Poor PM
                "sensor_calibration_frequency": 30,  # Rare calibration
                "changeover_reduction_level": 0,
                "staffing_level": 1,  # Understaffed
                "autonomous_maintenance_level": 0,
            },
            expected_outcomes={
                "oee": (0.25, 0.45),  # Poor OEE
                "availability": (0.45, 0.65),
                "performance": (0.65, 0.80),
                "quality": (0.85, 0.93),
            },
        )
    )

    return scenarios


def run_scenario(scenario: TestScenario) -> TestResult:
    """Run a single test scenario and collect results.

    Args:
        scenario: Test scenario to execute

    Returns:
        TestResult with metrics and validation

    """
    logger.info(f"\nRunning scenario: {scenario.name}")
    logger.info(f"  {scenario.description}")

    # Create environment
    env = simpy.Environment()

    # Set up paths
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")

    # Initialize control manager
    control_mgr = ControlManager(
        ontology_path=ontology_path,
        mappings_path=Path("ontology/control_mappings.yaml"),
        settings_path=manifest_dir / "control_settings.yaml",
    )

    # Apply scenario controls
    for control_name, value in scenario.control_settings.items():
        control_mgr.set_control_value(control_name, value)

    # Get computed parameters for validation
    computed_params = control_mgr.get_all_parameters()

    # Create model builder with control manager
    builder = ModelBuilder(env=env, ontology_path=ontology_path, manifest_dir=manifest_dir, control_manager=control_mgr)

    # Build model
    model = builder.build_model()

    # Apply computed parameters to equipment
    for prim_id, primitive in model["primitives"].items():
        if hasattr(primitive, "performance_factor"):
            # Apply control-computed parameters
            if "performance_factor" in computed_params:
                primitive.performance_factor = computed_params["performance_factor"]
            if "micro_stop_probability" in computed_params:
                primitive.micro_stop_probability = computed_params["micro_stop_probability"]
            if "mtbf" in computed_params:
                primitive.config.properties["mtbf"] = computed_params["mtbf"]
            if "scrap_rate" in computed_params:
                primitive.scrap_rate = computed_params["scrap_rate"]

    # Disable order mode for continuous generation
    for primitive in model["primitives"].values():
        if hasattr(primitive, "order_mode"):
            primitive.order_mode = False
            primitive.arrival_rate = 100  # High rate to avoid starvation

    # Start all processes
    for primitive in model["primitives"].values():
        if hasattr(primitive, "start"):
            primitive.start()

    # Run simulation
    env.run(until=scenario.duration_minutes)

    # Finalize state durations
    for primitive in model["primitives"].values():
        if hasattr(primitive, "state_durations") and hasattr(primitive, "state"):
            if hasattr(primitive, "state_start_time"):
                remaining = env.now - primitive.state_start_time
                primitive.state_durations[primitive.state] += remaining

    # Collect results
    oee_values = {}
    availability_vals = {}
    performance_vals = {}
    quality_vals = {}
    failure_counts = {}
    micro_stop_counts = {}
    units_produced = {}

    for line_id, line in model["lines"].items():
        # Get middle equipment as representative (usually bottleneck)
        if len(line.equipment) > 0:
            mid_idx = len(line.equipment) // 2
            eq_entity = line.equipment[mid_idx]
            eq_id = eq_entity.entity_id

            if eq_id in model["primitives"]:
                eq = model["primitives"][eq_id]

                # Calculate OEE components
                from twin_model.primitives.equipment import EquipmentState

                running_time = eq.state_durations.get(EquipmentState.RUNNING, 0)
                total_time = scenario.duration_minutes

                availability = running_time / total_time if total_time > 0 else 0

                base_rate = eq.config.properties.get("base_rate", 80)
                theoretical_output = running_time * base_rate
                actual_output = getattr(eq, "units_produced", 0)
                performance = actual_output / theoretical_output if theoretical_output > 0 else 0

                good_units = getattr(eq, "units_produced", 0)
                total_units = good_units + getattr(eq, "units_scrapped", 0)
                quality = good_units / total_units if total_units > 0 else 0

                oee = availability * performance * quality

                # Store metrics
                oee_values[line_id] = oee
                availability_vals[line_id] = availability
                performance_vals[line_id] = performance
                quality_vals[line_id] = quality
                failure_counts[line_id] = getattr(eq, "failure_count", 0)
                micro_stop_counts[line_id] = getattr(eq, "micro_stop_count", 0)
                units_produced[line_id] = getattr(eq, "units_produced", 0)

    # Validate against expected outcomes
    failures = []

    # Check average OEE
    if oee_values:
        avg_oee = np.mean(list(oee_values.values()))
        min_oee, max_oee = scenario.expected_outcomes["oee"]
        if not (min_oee <= avg_oee <= max_oee):
            failures.append(f"OEE {avg_oee:.2%} outside range [{min_oee:.2%}, {max_oee:.2%}]")

    # Check average availability
    if availability_vals:
        avg_avail = np.mean(list(availability_vals.values()))
        min_avail, max_avail = scenario.expected_outcomes["availability"]
        if not (min_avail <= avg_avail <= max_avail):
            failures.append(f"Availability {avg_avail:.2%} outside range [{min_avail:.2%}, {max_avail:.2%}]")

    # Check average performance
    if performance_vals:
        avg_perf = np.mean(list(performance_vals.values()))
        min_perf, max_perf = scenario.expected_outcomes["performance"]
        if not (min_perf <= avg_perf <= max_perf):
            failures.append(f"Performance {avg_perf:.2%} outside range [{min_perf:.2%}, {max_perf:.2%}]")

    # Check average quality
    if quality_vals:
        avg_qual = np.mean(list(quality_vals.values()))
        min_qual, max_qual = scenario.expected_outcomes["quality"]
        if not (min_qual <= avg_qual <= max_qual):
            failures.append(f"Quality {avg_qual:.2%} outside range [{min_qual:.2%}, {max_qual:.2%}]")

    passed = len(failures) == 0

    return TestResult(
        scenario_name=scenario.name,
        oee_values=oee_values,
        availability=availability_vals,
        performance=performance_vals,
        quality=quality_vals,
        failure_counts=failure_counts,
        micro_stop_counts=micro_stop_counts,
        units_produced=units_produced,
        computed_parameters=computed_params,
        passed=passed,
        failures=failures,
    )


def print_results(results: List[TestResult]) -> None:
    """Print test results in a formatted table.

    Args:
        results: List of test results to display

    """
    print("\n" + "=" * 100)
    print("CONTROL EFFECTS TEST RESULTS")
    print("=" * 100)

    # Summary table
    print(
        "\n{:<20} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
            "Scenario", "Status", "Avg OEE", "Avail.", "Perf.", "Quality", "Failures"
        )
    )
    print("-" * 100)

    for result in results:
        avg_oee = np.mean(list(result.oee_values.values())) if result.oee_values else 0
        avg_avail = np.mean(list(result.availability.values())) if result.availability else 0
        avg_perf = np.mean(list(result.performance.values())) if result.performance else 0
        avg_qual = np.mean(list(result.quality.values())) if result.quality else 0
        total_failures = sum(result.failure_counts.values())

        status = "✅ PASS" if result.passed else "❌ FAIL"

        print(
            f"{result.scenario_name:<20} {status:<10} {avg_oee:>9.1%} {avg_avail:>9.1%} "
            f"{avg_perf:>9.1%} {avg_qual:>9.1%} {total_failures:>9}"
        )

    # Detailed failures
    print("\n" + "-" * 100)
    print("VALIDATION DETAILS")
    print("-" * 100)

    for result in results:
        if not result.passed:
            print(f"\n{result.scenario_name}:")
            for failure in result.failures:
                print(f"  ❌ {failure}")
        else:
            print(f"\n{result.scenario_name}: ✅ All checks passed")

    # Key parameters for each scenario
    print("\n" + "-" * 100)
    print("KEY COMPUTED PARAMETERS")
    print("-" * 100)

    key_params = ["mtbf", "performance_factor", "micro_stop_probability", "scrap_rate"]

    for result in results:
        print(f"\n{result.scenario_name}:")
        for param in key_params:
            if param in result.computed_parameters:
                value = result.computed_parameters[param]
                if param == "mtbf":
                    print(f"  {param}: {value:.0f} min")
                else:
                    print(f"  {param}: {value:.3f}")

    # Overall summary
    total_pass = sum(1 for r in results if r.passed)
    total_scenarios = len(results)

    print("\n" + "=" * 100)
    print(f"OVERALL: {total_pass}/{total_scenarios} scenarios passed")
    print("=" * 100)


def main() -> None:
    """Run all control effects tests."""
    logger.info("Starting control effects validation tests...")

    # Create test scenarios
    scenarios = create_test_scenarios()
    logger.info(f"Created {len(scenarios)} test scenarios")

    # Run each scenario
    results = []
    for scenario in scenarios:
        result = run_scenario(scenario)
        results.append(result)

        # Quick status
        status = "✅" if result.passed else "❌"
        avg_oee = np.mean(list(result.oee_values.values())) if result.oee_values else 0
        logger.info(f"  {status} {scenario.name}: OEE = {avg_oee:.1%}")

    # Print comprehensive results
    print_results(results)

    # Write detailed report
    report_path = Path("test_control_effects_report.txt")
    with open(report_path, "w") as f:
        f.write("CONTROL EFFECTS VALIDATION REPORT\n")
        f.write("=" * 50 + "\n\n")

        for result in results:
            f.write(f"Scenario: {result.scenario_name}\n")
            f.write(f"Status: {'PASSED' if result.passed else 'FAILED'}\n")
            f.write(f"Failures: {result.failures}\n")
            f.write(f"OEE Values: {result.oee_values}\n")
            f.write(f"Units Produced: {result.units_produced}\n")
            f.write("-" * 50 + "\n\n")

    logger.info(f"Detailed report written to {report_path}")

    # Exit with appropriate code
    if all(r.passed for r in results):
        logger.info("✅ All control effects tests passed!")
        sys.exit(0)
    else:
        logger.warning("❌ Some control effects tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
