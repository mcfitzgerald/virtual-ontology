#!/usr/bin/env python3
"""Test script to verify state duration tracking is working correctly."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import simpy
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction.mes_transducer import MESTransducer


def test_state_duration_tracking():
    """Test that equipment state changes include duration."""
    
    print("Testing State Duration Tracking")
    print("=" * 60)
    
    # Build model
    builder = OntologyDrivenModelBuilder(
        Path('ontology/twin_ontology.yaml'),
        Path('manifests')
    )
    
    env = simpy.Environment()
    model = builder.build_model(env)
    
    # Run for 60 minutes to ensure some state changes
    print("\nRunning 1-hour simulation...")
    env.run(until=60)
    
    # Collect all observables using the proper method
    all_observables = []
    state_changes = []
    
    for prim_id, primitive in builder.primitives.items():
        # Use get_observables() method instead of direct access
        if hasattr(primitive, 'get_observables'):
            obs_list = primitive.get_observables()
            
            # Track all observables
            for obs in obs_list:
                obs['primitive_id'] = prim_id  # Ensure primitive_id is set
                all_observables.append(obs)
                
                # Track state changes specifically
                if obs.get('event_type') == 'state_change':
                    state_changes.append({
                        'primitive': prim_id,
                        'old_state': obs.get('old_state'),
                        'new_state': obs.get('new_state'),
                        'duration': obs.get('duration_in_state', 0),
                        'failure_mode': obs.get('failure_mode'),
                        'timestamp': obs.get('timestamp')
                    })
    
    print(f"\nCollected {len(all_observables)} total observable events")
    print(f"Found {len(state_changes)} state change events")
    
    # Show sample state changes
    if state_changes:
        print("\nSample State Changes (first 10):")
        for i, sc in enumerate(state_changes[:10]):
            duration_str = f"{sc['duration']:.2f}" if sc['duration'] > 0 else "0"
            failure_str = f" [{sc['failure_mode']}]" if sc['failure_mode'] else ""
            print(f"  {i+1}. @{sc['timestamp']:.1f}min: {sc['primitive']}: "
                  f"{sc['old_state']} -> {sc['new_state']}, "
                  f"duration={duration_str}min{failure_str}")
        
        # Check for missing durations
        missing_duration = sum(1 for sc in state_changes if sc['duration'] == 0)
        print(f"\nDuration Statistics:")
        print(f"  State changes with duration > 0: {len(state_changes) - missing_duration}/{len(state_changes)}")
        print(f"  State changes with duration = 0: {missing_duration}/{len(state_changes)}")
        
        if missing_duration == len(state_changes):
            print("  ❌ All durations are 0 - state tracking not working!")
        elif missing_duration > 0:
            print(f"  ⚠️  Some durations are 0 (expected for initial state changes)")
        else:
            print("  ✅ All state changes have durations!")
    
    # Test MES transduction
    print("\n" + "=" * 60)
    print("Testing MES Transduction")
    print("=" * 60)
    
    transducer = MESTransducer(time_bucket=5)
    mes_df = transducer.process_observables(all_observables, builder.manifests)
    
    print(f"\nMES Records Generated: {len(mes_df)}")
    
    if not mes_df.empty:
        # Calculate KPIs from MES data
        avg_availability = mes_df['Availability_Score'].mean()
        avg_performance = mes_df['Performance_Score'].mean()
        avg_quality = mes_df['Quality_Score'].mean()
        avg_oee = mes_df['OEE_Score'].mean()
        
        downtime_pct = (len(mes_df[mes_df['MachineStatus'] == 'Stopped']) / len(mes_df)) * 100
        
        print(f"\nCalculated KPIs:")
        print(f"  Availability: {avg_availability:.1f}%")
        print(f"  Performance:  {avg_performance:.1f}%")
        print(f"  Quality:      {avg_quality:.1f}%")
        print(f"  OEE:          {avg_oee:.1f}%")
        print(f"  Downtime:     {downtime_pct:.1f}%")
        
        # Check if availability is responding to failures
        if avg_availability > 95:
            print("\n  ⚠️  Availability still very high - check if downtime is being tracked")
        else:
            print("\n  ✅ Availability is responding to failures!")
    
    return all_observables, mes_df


if __name__ == "__main__":
    observables, mes_df = test_state_duration_tracking()
    
    # Save for inspection if needed
    if not mes_df.empty:
        mes_df.to_csv('test_mes_output.csv', index=False)
        print("\n✅ Test MES data saved to test_mes_output.csv")