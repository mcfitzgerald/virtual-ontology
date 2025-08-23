#!/usr/bin/env python3
"""Debug script to understand availability calculation issues."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import simpy
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction.mes_transducer import MESTransducer


def debug_availability():
    """Debug availability calculation."""
    
    print("Debugging Availability Calculation")
    print("=" * 60)
    
    # Build model
    builder = OntologyDrivenModelBuilder(
        Path('ontology/twin_ontology.yaml'),
        Path('manifests')
    )
    
    env = simpy.Environment()
    model = builder.build_model(env)
    
    # Run for 60 minutes
    print("\nRunning 1-hour simulation...")
    env.run(until=60)
    
    # Collect observables
    all_observables = []
    equipment_states = {}
    
    for prim_id, primitive in builder.primitives.items():
        if hasattr(primitive, 'get_observables'):
            obs_list = primitive.get_observables()
            
            # Track equipment-specific events
            if hasattr(primitive, 'equipment_type'):
                equipment_states[prim_id] = {
                    'type': primitive.equipment_type,
                    'mtbf': primitive.mtbf,
                    'mttr': primitive.mttr,
                    'state_changes': [],
                    'total_downtime': 0.0,
                    'theoretical_availability': primitive.mtbf / (primitive.mtbf + primitive.mttr) * 100
                }
                
                for obs in obs_list:
                    obs['primitive_id'] = prim_id
                    all_observables.append(obs)
                    
                    if obs.get('event_type') == 'state_change':
                        equipment_states[prim_id]['state_changes'].append({
                            'timestamp': obs.get('timestamp'),
                            'old_state': obs.get('old_state') or obs.get('details', {}).get('old_state'),
                            'new_state': obs.get('new_state') or obs.get('details', {}).get('new_state'),
                            'duration': obs.get('duration_in_state') or obs.get('details', {}).get('duration_in_state', 0)
                        })
                        
                        # Calculate downtime
                        old_state = obs.get('old_state') or obs.get('details', {}).get('old_state')
                        duration = obs.get('duration_in_state') or obs.get('details', {}).get('duration_in_state', 0)
                        if old_state in ['STOPPED_FAILURE', 'STOPPED_MATERIAL']:
                            equipment_states[prim_id]['total_downtime'] += duration
            else:
                for obs in obs_list:
                    obs['primitive_id'] = prim_id
                    all_observables.append(obs)
    
    print(f"\nCollected {len(all_observables)} total observable events")
    
    # Show equipment-specific analysis
    print("\n" + "=" * 60)
    print("Equipment Availability Analysis")
    print("=" * 60)
    
    for eq_id, eq_data in sorted(equipment_states.items()):
        if eq_data['type'] in ['Filler', 'Packer', 'Palletizer']:
            print(f"\n{eq_id} ({eq_data['type']}):")
            print(f"  MTBF: {eq_data['mtbf']} min, MTTR: {eq_data['mttr']} min")
            print(f"  Theoretical Availability: {eq_data['theoretical_availability']:.1f}%")
            print(f"  State changes: {len(eq_data['state_changes'])}")
            print(f"  Total downtime: {eq_data['total_downtime']:.1f} min")
            print(f"  Actual Availability: {(60 - eq_data['total_downtime']) / 60 * 100:.1f}%")
            
            # Show first few state changes
            if eq_data['state_changes']:
                print("  First 5 state changes:")
                for i, sc in enumerate(eq_data['state_changes'][:5]):
                    print(f"    {i+1}. @{sc['timestamp']:.1f}min: {sc['old_state']} -> {sc['new_state']}, duration={sc['duration']:.1f}min")
    
    # Test MES transduction
    print("\n" + "=" * 60)
    print("MES Transduction Analysis")
    print("=" * 60)
    
    transducer = MESTransducer(time_bucket=5)
    mes_df = transducer.process_observables(all_observables, builder.manifests)
    
    if not mes_df.empty:
        # Group by equipment for analysis
        for eq_id in equipment_states.keys():
            eq_records = mes_df[mes_df['EquipmentID'] == eq_id]
            if not eq_records.empty:
                print(f"\n{eq_id}:")
                print(f"  MES records: {len(eq_records)}")
                print(f"  Avg Availability (MES): {eq_records['Availability_Score'].mean():.1f}%")
                print(f"  Machine statuses: {eq_records['MachineStatus'].value_counts().to_dict()}")
                
                # Check for downtime records
                stopped_records = eq_records[eq_records['MachineStatus'] == 'Stopped']
                if not stopped_records.empty:
                    print(f"  Stopped records: {len(stopped_records)}")
                    print(f"  Downtime reasons: {stopped_records['DowntimeReason'].value_counts().to_dict()}")
    
    return all_observables, mes_df, equipment_states


if __name__ == "__main__":
    observables, mes_df, equipment_states = debug_availability()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    # Calculate overall theoretical vs actual
    theoretical_avails = []
    actual_avails = []
    
    for eq_id, eq_data in equipment_states.items():
        if eq_data['type'] in ['Filler', 'Packer', 'Palletizer']:
            theoretical_avails.append(eq_data['theoretical_availability'])
            actual_avails.append((60 - eq_data['total_downtime']) / 60 * 100)
    
    if theoretical_avails:
        print(f"Average Theoretical Availability: {sum(theoretical_avails)/len(theoretical_avails):.1f}%")
        print(f"Average Actual Availability (from states): {sum(actual_avails)/len(actual_avails):.1f}%")
    
    if not mes_df.empty:
        print(f"Average MES Availability: {mes_df['Availability_Score'].mean():.1f}%")
        print(f"MES Downtime %: {len(mes_df[mes_df['MachineStatus'] == 'Stopped']) / len(mes_df) * 100:.1f}%")