"""
Test current twin_model simulation with proper configuration.

This script tests the existing twin_model to understand its behavior
before we build the ontology-driven primitives framework.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from twin_model import (
    SimulationRunner,
    ActionableParameters,
    SimulationConfig,
)
from twin_model.config import (
    LineConfig,
    EquipmentConfig,
    EquipmentType,
)


def create_test_config() -> SimulationConfig:
    """Create a test configuration with one production line.
    
    Returns:
        SimulationConfig: Configured simulation with one line
    """
    # Create equipment for LINE1
    equipment_configs: List[EquipmentConfig] = [
        EquipmentConfig(
            equipment_id="LINE1-FIL",
            equipment_type=EquipmentType.FILLER,
            base_rate=60.0,  # units per minute
            mtbf=480.0,  # mean time between failures (minutes)
            mttr=30.0,  # mean time to repair (minutes)
            base_scrap_rate=0.02,
            upstream_buffer_capacity=200,
            downstream_buffer_capacity=150,
        ),
        EquipmentConfig(
            equipment_id="LINE1-PCK",
            equipment_type=EquipmentType.PACKER,
            base_rate=55.0,
            mtbf=600.0,
            mttr=20.0,
            base_scrap_rate=0.01,
            upstream_buffer_capacity=150,
            downstream_buffer_capacity=100,
        ),
        EquipmentConfig(
            equipment_id="LINE1-PAL",
            equipment_type=EquipmentType.PALLETIZER,
            base_rate=50.0,
            mtbf=720.0,
            mttr=15.0,
            base_scrap_rate=0.005,
            upstream_buffer_capacity=100,
            downstream_buffer_capacity=50,
        ),
    ]
    
    # Create line configuration
    line_config = LineConfig(
        line_id="LINE1",
        equipment_configs=equipment_configs,
        source_arrival_rate=65.0,  # units per minute
    )
    
    # Create simulation configuration
    config = SimulationConfig(
        duration_days=1/24,  # 1 hour
        mes_logging_interval=5.0,  # log every 5 minutes
        line_configs=[line_config],
        random_seed=42,
    )
    
    return config


def analyze_mes_data(mes_data: List[Dict[str, Any]]) -> None:
    """Analyze and print MES data summary.
    
    Args:
        mes_data: List of MES records
    """
    if not mes_data:
        print("No MES data generated!")
        return
    
    print(f"\nMES Data Analysis:")
    print(f"  Total records: {len(mes_data)}")
    
    # Check first record structure
    if mes_data:
        first_record = mes_data[0]
        print(f"  Fields in MES record: {list(first_record.keys())}")
        
    # Analyze equipment states
    states: Dict[str, int] = {}
    for record in mes_data:
        state = record.get("MachineStatus", "Unknown")
        states[state] = states.get(state, 0) + 1
    
    print(f"  Machine states:")
    for state, count in states.items():
        print(f"    {state}: {count} records")
    
    # Check for production data
    total_good = sum(record.get("GoodUnitsProduced", 0) for record in mes_data)
    total_scrap = sum(record.get("ScrapUnitsProduced", 0) for record in mes_data)
    
    print(f"  Total production:")
    print(f"    Good units: {total_good:,.0f}")
    print(f"    Scrap units: {total_scrap:,.0f}")


def main() -> None:
    """Run the simulation test."""
    print("Testing current twin_model simulation")
    print("=" * 50)
    
    # Create configuration
    config = create_test_config()
    print(f"\nConfiguration created:")
    print(f"  Lines: {len(config.line_configs)}")
    print(f"  Duration: {config.duration_days * 24:.1f} hours")
    print(f"  MES logging interval: {config.mes_logging_interval} minutes")
    
    # Create parameters (using defaults)
    params = ActionableParameters()
    print(f"\nActionable Parameters (all at baseline 1.0):")
    print(f"  micro_stop_probability: {params.micro_stop_probability}")
    print(f"  performance_factor: {params.performance_factor}")
    print(f"  scrap_multiplier: {params.scrap_multiplier}")
    print(f"  material_reliability: {params.material_reliability}")
    print(f"  cascade_sensitivity: {params.cascade_sensitivity}")
    
    # Create and run simulation
    runner = SimulationRunner(config)
    print(f"\nRunning simulation...")
    
    try:
        results = runner.run_simulation(params, duration_days=1/24, seed=42)
        
        print(f"\nSimulation completed!")
        print(f"  Duration: {results.duration_minutes:.1f} minutes")
        print(f"  MES records generated: {len(results.mes_data)}")
        
        # Analyze KPIs
        kpis = results.kpi_summary
        print(f"\nKPI Summary:")
        print(f"  Mean OEE: {kpis.get('mean_oee', 0):.1f}%")
        print(f"  Mean Availability: {kpis.get('mean_availability', 0):.1f}%")
        print(f"  Mean Performance: {kpis.get('mean_performance', 0):.1f}%")
        print(f"  Mean Quality: {kpis.get('mean_quality', 0):.1f}%")
        print(f"  Total Output: {kpis.get('total_output', 0):,.0f} units")
        print(f"  Total Scrap: {kpis.get('total_scrap', 0):,.0f} units")
        
        # Analyze MES data
        analyze_mes_data(results.mes_data)
        
        # Check line summaries
        print(f"\nLine Summaries:")
        for line_id, summary in results.line_summaries.items():
            print(f"  {line_id}:")
            print(f"    Total input: {summary.get('total_input', 0):,.0f}")
            print(f"    Total output: {summary.get('total_output', 0):,.0f}")
            print(f"    Total scrap: {summary.get('total_scrap', 0):,.0f}")
            
            line_oee = summary.get('line_oee', {})
            print(f"    OEE: {line_oee.get('oee', 0):.1f}%")
            
    except Exception as e:
        print(f"\nError running simulation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()