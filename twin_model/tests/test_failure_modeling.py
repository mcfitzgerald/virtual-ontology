"""Test realistic failure modeling with mixture model.

This module tests the new failure modeling implementation using
competing risks and realistic distributions for different failure types.
"""

import sys
from pathlib import Path
import numpy as np
from typing import Dict, List, Any
import simpy

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from twin_model import OntologyDrivenModelBuilder
from config.config_loader import ConfigLoader


def analyze_failure_patterns(duration_hours: float = 24.0) -> Dict[str, Any]:
    """Run simulation and analyze failure patterns.
    
    Args:
        duration_hours: Simulation duration in hours
        
    Returns:
        Dictionary containing failure analysis results
    """
    # Initialize paths
    ontology_path = Path("ontology/twin_ontology.yaml")
    manifest_dir = Path("manifests")
    
    # Build model
    builder = OntologyDrivenModelBuilder(
        ontology_path=ontology_path,
        manifest_dir=manifest_dir
    )
    
    # Create environment and build model
    env = simpy.Environment()
    model = builder.build_model(env)
    
    # Run simulation
    duration_minutes = duration_hours * 60
    env.run(until=duration_minutes)
    
    # Collect failure events from all equipment
    failure_events = []
    recovery_events = []
    
    for entity_id, entity in model.entities.items():
        if hasattr(entity, 'observables'):
            # Get failure events
            for obs in entity.observables:
                if obs['event_type'] == 'equipment_failure':
                    failure_events.append({
                        'equipment': entity_id,
                        'time': obs['timestamp'],
                        'type': obs['details'].get('failure_type', 'unknown'),
                        'duration': obs['details'].get('duration', 0),
                        'downtime_code': obs['details'].get('downtime_code', 'UNP-UNKNOWN')
                    })
                elif obs['event_type'] == 'equipment_recovered':
                    recovery_events.append({
                        'equipment': entity_id,
                        'time': obs['timestamp'],
                        'type': obs['details'].get('failure_type', 'unknown'),
                        'actual_duration': obs['details'].get('downtime_duration', 0)
                    })
    
    # Analyze failure distribution
    micro_stops = [f for f in failure_events if 'micro' in f['type'].lower()]
    minor_failures = [f for f in failure_events if 'minor' in f['type'].lower()]
    major_failures = [f for f in failure_events if 'major' in f['type'].lower()]
    
    total_failures = len(failure_events)
    
    # Calculate percentages
    results = {
        'total_failures': total_failures,
        'micro_stops': {
            'count': len(micro_stops),
            'percentage': (len(micro_stops) / total_failures * 100) if total_failures > 0 else 0,
            'avg_duration': np.mean([f['duration'] for f in micro_stops]) if micro_stops else 0,
            'min_duration': np.min([f['duration'] for f in micro_stops]) if micro_stops else 0,
            'max_duration': np.max([f['duration'] for f in micro_stops]) if micro_stops else 0
        },
        'minor_failures': {
            'count': len(minor_failures),
            'percentage': (len(minor_failures) / total_failures * 100) if total_failures > 0 else 0,
            'avg_duration': np.mean([f['duration'] for f in minor_failures]) if minor_failures else 0,
            'min_duration': np.min([f['duration'] for f in minor_failures]) if minor_failures else 0,
            'max_duration': np.max([f['duration'] for f in minor_failures]) if minor_failures else 0
        },
        'major_failures': {
            'count': len(major_failures),
            'percentage': (len(major_failures) / total_failures * 100) if total_failures > 0 else 0,
            'avg_duration': np.mean([f['duration'] for f in major_failures]) if major_failures else 0,
            'min_duration': np.min([f['duration'] for f in major_failures]) if major_failures else 0,
            'max_duration': np.max([f['duration'] for f in major_failures]) if major_failures else 0
        },
        'simulation_duration_hours': duration_hours,
        'failures_per_hour': total_failures / duration_hours if duration_hours > 0 else 0
    }
    
    # Calculate MTBF for each type
    if micro_stops:
        micro_times = sorted([f['time'] for f in micro_stops])
        if len(micro_times) > 1:
            micro_intervals = [micro_times[i+1] - micro_times[i] for i in range(len(micro_times)-1)]
            results['micro_stops']['mtbf'] = np.mean(micro_intervals)
        else:
            results['micro_stops']['mtbf'] = duration_minutes
    
    if minor_failures:
        minor_times = sorted([f['time'] for f in minor_failures])
        if len(minor_times) > 1:
            minor_intervals = [minor_times[i+1] - minor_times[i] for i in range(len(minor_times)-1)]
            results['minor_failures']['mtbf'] = np.mean(minor_intervals)
        else:
            results['minor_failures']['mtbf'] = duration_minutes
    
    if major_failures:
        major_times = sorted([f['time'] for f in major_failures])
        if len(major_times) > 1:
            major_intervals = [major_times[i+1] - major_times[i] for i in range(len(major_times)-1)]
            results['major_failures']['mtbf'] = np.mean(major_intervals)
        else:
            results['major_failures']['mtbf'] = duration_minutes
    
    # Calculate KPIs
    # Get state change events to calculate availability
    state_events = []
    for entity_id, entity in model.entities.items():
        if hasattr(entity, 'observables'):
            for obs in entity.observables:
                if obs['event_type'] == 'state_change':
                    state_events.append(obs)
    
    # Simple OEE calculation based on equipment states
    total_time = duration_minutes
    running_time = 0
    
    for entity_id, entity in model.entities.items():
        if hasattr(entity, 'state') and hasattr(entity, 'observables'):
            entity_running_time = 0
            for obs in entity.observables:
                if obs['event_type'] == 'state_change' and obs['details'].get('old_state') == 'RUNNING':
                    entity_running_time += obs['details'].get('duration_in_state', 0)
            running_time += entity_running_time
    
    # Count equipment
    equipment_count = len([e for e in model.entities.values() if hasattr(e, 'state')])
    if equipment_count > 0:
        avg_availability = (running_time / (total_time * equipment_count)) * 100
    else:
        avg_availability = 0
    
    results['kpis'] = {
        'oee': avg_availability * 0.85 * 0.95,  # Rough estimate: availability * performance * quality
        'availability': avg_availability,
        'performance': 85.0,  # Placeholder
        'quality': 95.0  # Placeholder
    }
    
    return results


def validate_failure_distributions(num_runs: int = 5) -> None:
    """Validate that failure distributions match expected patterns.
    
    Args:
        num_runs: Number of simulation runs to average
    """
    print(f"\nRunning {num_runs} simulations to validate failure distributions...")
    print("=" * 80)
    
    all_results = []
    for run in range(num_runs):
        print(f"\nRun {run + 1}/{num_runs}...")
        results = analyze_failure_patterns(duration_hours=4.0)  # Shorter 4 hour runs
        all_results.append(results)
    
    # Average results
    avg_micro_pct = np.mean([r['micro_stops']['percentage'] for r in all_results])
    avg_minor_pct = np.mean([r['minor_failures']['percentage'] for r in all_results])
    avg_major_pct = np.mean([r['major_failures']['percentage'] for r in all_results])
    
    avg_micro_duration = np.mean([r['micro_stops']['avg_duration'] for r in all_results if r['micro_stops']['count'] > 0])
    avg_minor_duration = np.mean([r['minor_failures']['avg_duration'] for r in all_results if r['minor_failures']['count'] > 0])
    avg_major_duration = np.mean([r['major_failures']['avg_duration'] for r in all_results if r['major_failures']['count'] > 0])
    
    avg_oee = np.mean([r['kpis']['oee'] for r in all_results])
    avg_availability = np.mean([r['kpis']['availability'] for r in all_results])
    
    print("\n" + "=" * 80)
    print("FAILURE DISTRIBUTION VALIDATION RESULTS")
    print("=" * 80)
    
    print(f"\nFailure Type Distribution (Target: 80% micro, 15% minor, 5% major):")
    print(f"  Micro-stops:     {avg_micro_pct:5.1f}% (Target: ~80%)")
    print(f"  Minor failures:  {avg_minor_pct:5.1f}% (Target: ~15%)")
    print(f"  Major failures:  {avg_major_pct:5.1f}% (Target: ~5%)")
    
    print(f"\nAverage Failure Durations:")
    print(f"  Micro-stops:     {avg_micro_duration:5.2f} min (Target: 0.5-3 min)")
    print(f"  Minor failures:  {avg_minor_duration:5.2f} min (Target: 5-30 min)")
    print(f"  Major failures:  {avg_major_duration:5.2f} min (Target: 30+ min)")
    
    print(f"\nKPI Impact:")
    print(f"  OEE:          {avg_oee:5.1f}% (Target: ~60%)")
    print(f"  Availability: {avg_availability:5.1f}% (Target: ~60%)")
    
    # Validation checks
    print(f"\n{'VALIDATION STATUS':^80}")
    print("-" * 80)
    
    checks = []
    
    # Check failure distribution
    if 70 <= avg_micro_pct <= 90:
        checks.append(("✓", "Micro-stop percentage in expected range"))
    else:
        checks.append(("✗", f"Micro-stop percentage out of range: {avg_micro_pct:.1f}%"))
    
    if 10 <= avg_minor_pct <= 20:
        checks.append(("✓", "Minor failure percentage in expected range"))
    else:
        checks.append(("✗", f"Minor failure percentage out of range: {avg_minor_pct:.1f}%"))
    
    if 2 <= avg_major_pct <= 10:
        checks.append(("✓", "Major failure percentage in expected range"))
    else:
        checks.append(("✗", f"Major failure percentage out of range: {avg_major_pct:.1f}%"))
    
    # Check durations
    if 0.5 <= avg_micro_duration <= 5.0:
        checks.append(("✓", "Micro-stop durations realistic"))
    else:
        checks.append(("✗", f"Micro-stop durations unrealistic: {avg_micro_duration:.2f} min"))
    
    if 5.0 <= avg_minor_duration <= 35.0:
        checks.append(("✓", "Minor failure durations realistic"))
    else:
        checks.append(("✗", f"Minor failure durations unrealistic: {avg_minor_duration:.2f} min"))
    
    if avg_major_duration >= 25.0:
        checks.append(("✓", "Major failure durations realistic"))
    else:
        checks.append(("✗", f"Major failure durations too short: {avg_major_duration:.2f} min"))
    
    # Check KPIs
    if 50 <= avg_availability <= 70:
        checks.append(("✓", "Availability in target range"))
    else:
        checks.append(("✗", f"Availability out of range: {avg_availability:.1f}%"))
    
    for status, message in checks:
        print(f"  {status} {message}")
    
    passed = all(status == "✓" for status, _ in checks)
    print("\n" + "=" * 80)
    if passed:
        print("SUCCESS: All validation checks passed!")
    else:
        print("WARNING: Some validation checks failed. Review failure parameters.")
    print("=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TESTING REALISTIC FAILURE MODELING WITH MIXTURE MODEL")
    print("=" * 80)
    
    # Quick test with shorter duration
    print("\nRunning quick failure pattern analysis (2 hours)...")
    results = analyze_failure_patterns(duration_hours=2.0)
    
    print(f"\nQuick Test Results:")
    print(f"  Total failures: {results['total_failures']}")
    print(f"  Failures/hour: {results['failures_per_hour']:.2f}")
    print(f"  Micro-stops: {results['micro_stops']['count']} ({results['micro_stops']['percentage']:.1f}%)")
    print(f"  Minor failures: {results['minor_failures']['count']} ({results['minor_failures']['percentage']:.1f}%)")
    print(f"  Major failures: {results['major_failures']['count']} ({results['major_failures']['percentage']:.1f}%)")
    
    # Reduced validation with shorter runs
    print("\nRunning validation with 1 quick run...")
    validate_failure_distributions(num_runs=1)