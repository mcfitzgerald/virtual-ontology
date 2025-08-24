"""Calibrate twin model parameters to match historical KPIs."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import yaml
import numpy as np
import pandas as pd
from typing import Dict, Tuple
import simpy
import random
from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.transduction import MESTransducer


class TwinCalibrator:
    """Calibrate twin model parameters to match historical data."""
    
    def __init__(self, target_csv: str):
        """Initialize calibrator with target historical data.
        
        Args:
            target_csv: Path to historical MES data with KPIs
        """
        self.target_df = pd.read_csv(target_csv)
        self.calculate_target_kpis()
        
    def calculate_target_kpis(self) -> None:
        """Calculate target KPIs from historical data."""
        # Filter valid data
        valid = self.target_df[self.target_df['OEE_Score'] > 0]
        
        self.target_kpis = {
            'oee': valid['OEE_Score'].mean(),
            'availability': valid['Availability_Score'].mean(),
            'performance': valid['Performance_Score'].mean(),
            'quality': valid['Quality_Score'].mean(),
            'downtime_pct': (self.target_df['MachineStatus'] == 'Stopped').mean() * 100,
            'scrap_rate': (self.target_df['ScrapUnitsProduced'].sum() / 
                          (self.target_df['GoodUnitsProduced'].sum() + 
                           self.target_df['ScrapUnitsProduced'].sum()) * 100)
        }
        
        print("Target KPIs from historical data:")
        for key, value in self.target_kpis.items():
            print(f"  {key}: {value:.1f}%")
    
    def test_parameters(self, params: Dict[str, float], 
                       simulation_days: int = 1) -> Dict[str, float]:
        """Test a set of parameters and return KPIs.
        
        Args:
            params: Parameter values to test
            simulation_days: Days to simulate
            
        Returns:
            Dictionary of resulting KPIs
        """
        # Set seed for reproducibility
        random.seed(42)
        np.random.seed(42)
        
        # Build model with custom parameters
        ontology_path = Path("ontology/twin_ontology.yaml")
        manifest_dir = Path("manifests")
        
        # Apply parameter overrides to manifests
        self._apply_parameters(manifest_dir, params)
        
        builder = OntologyDrivenModelBuilder(
            ontology_path=ontology_path,
            manifest_dir=manifest_dir
        )
        
        env = simpy.Environment()
        model = builder.build_model(env)
        
        # Run simulation
        simulation_minutes = simulation_days * 24 * 60
        env.run(until=simulation_minutes)
        
        # Collect observables
        all_observables = []
        for primitive_id, primitive in builder.primitives.items():
            if hasattr(primitive, 'get_observables'):
                observables = primitive.get_observables()
                for obs in observables:
                    obs['primitive_id'] = primitive_id
                    all_observables.append(obs)
        
        # Transduce to MES format
        transducer = MESTransducer(time_bucket=5)
        mes_df = transducer.process_observables(all_observables, builder.manifests)
        
        # Calculate KPIs
        if len(mes_df) > 0:
            valid = mes_df[mes_df['OEE_Score'] > 0]
            
            kpis = {
                'oee': valid['OEE_Score'].mean() if len(valid) > 0 else 0,
                'availability': valid['Availability_Score'].mean() if len(valid) > 0 else 0,
                'performance': valid['Performance_Score'].mean() if len(valid) > 0 else 0,
                'quality': valid['Quality_Score'].mean() if len(valid) > 0 else 0,
                'downtime_pct': (mes_df['MachineStatus'] == 'Stopped').mean() * 100,
                'scrap_rate': (mes_df['ScrapUnitsProduced'].sum() / 
                              (mes_df['GoodUnitsProduced'].sum() + 
                               mes_df['ScrapUnitsProduced'].sum() + 0.01) * 100)
            }
        else:
            kpis = {k: 0 for k in self.target_kpis.keys()}
        
        return kpis
    
    def _apply_parameters(self, manifest_dir: Path, params: Dict[str, float]) -> None:
        """Apply parameter overrides to manifests.
        
        Args:
            manifest_dir: Directory containing manifests
            params: Parameters to apply
        """
        # Load equipment manifest
        equipment_manifest_path = manifest_dir / "equipment_manifest.yaml"
        with open(equipment_manifest_path, 'r') as f:
            equipment_manifest = yaml.safe_load(f)
        
        # Apply parameters
        if 'arrival_rate' in params:
            for src_id in ['LINE1-SRC', 'LINE2-SRC', 'LINE3-SRC']:
                if src_id in equipment_manifest['equipment']:
                    equipment_manifest['equipment'][src_id]['arrival_rate'] = params['arrival_rate']
        
        if 'base_rate' in params:
            for eq_id, eq_data in equipment_manifest['equipment'].items():
                if any(x in eq_id for x in ['FIL', 'PCK', 'PAL']):
                    eq_data['base_rate'] = params['base_rate']
        
        if 'buffer_capacity_multiplier' in params:
            for buf_id, buf_data in equipment_manifest['equipment'].items():
                if 'BUF' in buf_id:
                    if 'capacity' in buf_data:
                        buf_data['capacity'] = int(buf_data['capacity'] * params['buffer_capacity_multiplier'])
        
        if 'mtbf_multiplier' in params:
            for pattern in equipment_manifest.get('failure_patterns', {}).values():
                for failure_mode in pattern.values():
                    if 'mtbf' in failure_mode:
                        failure_mode['mtbf'] *= params['mtbf_multiplier']
        
        if 'mttr_multiplier' in params:
            for pattern in equipment_manifest.get('failure_patterns', {}).values():
                for failure_mode in pattern.values():
                    if 'mttr' in failure_mode:
                        failure_mode['mttr'] *= params['mttr_multiplier']
        
        # Save modified manifest temporarily
        temp_path = manifest_dir / "equipment_manifest_temp.yaml"
        with open(temp_path, 'w') as f:
            yaml.dump(equipment_manifest, f)
        
        # Rename to replace original (for this run)
        import shutil
        shutil.move(temp_path, equipment_manifest_path)
    
    def calculate_error(self, kpis: Dict[str, float]) -> float:
        """Calculate total error between current and target KPIs.
        
        Args:
            kpis: Current KPI values
            
        Returns:
            Total weighted error
        """
        weights = {
            'oee': 2.0,  # Most important
            'performance': 1.5,  # Key driver
            'availability': 1.0,
            'quality': 0.5,
            'downtime_pct': 0.5,
            'scrap_rate': 0.3
        }
        
        total_error = 0
        for key, weight in weights.items():
            target = self.target_kpis.get(key, 0)
            current = kpis.get(key, 0)
            if target > 0:
                error = abs(target - current) / target * 100  # Percentage error
                total_error += error * weight
        
        return total_error
    
    def grid_search(self, param_ranges: Dict[str, list], 
                   simulation_days: int = 1) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Perform grid search to find optimal parameters.
        
        Args:
            param_ranges: Dictionary of parameter names and value lists
            simulation_days: Days to simulate for each test
            
        Returns:
            Tuple of (best_params, best_kpis)
        """
        best_params = None
        best_kpis = None
        best_error = float('inf')
        
        # Generate all combinations
        import itertools
        param_names = list(param_ranges.keys())
        param_values = [param_ranges[name] for name in param_names]
        
        for values in itertools.product(*param_values):
            params = dict(zip(param_names, values))
            
            print(f"\nTesting parameters: {params}")
            
            # Test these parameters
            kpis = self.test_parameters(params, simulation_days)
            error = self.calculate_error(kpis)
            
            print(f"  Results: OEE={kpis['oee']:.1f}%, Performance={kpis['performance']:.1f}%")
            print(f"  Error: {error:.1f}")
            
            if error < best_error:
                best_error = error
                best_params = params
                best_kpis = kpis
                print("  ✓ New best!")
        
        return best_params, best_kpis
    
    def quick_calibration(self) -> Dict[str, float]:
        """Perform quick calibration with limited parameter sweep.
        
        Returns:
            Best parameters found
        """
        print("\n" + "="*60)
        print("QUICK CALIBRATION")
        print("="*60)
        
        # Define parameter ranges to test
        param_ranges = {
            'arrival_rate': [100, 125, 150],  # Source arrival rate
            'base_rate': [70, 85, 100],  # Equipment processing rate
            'buffer_capacity_multiplier': [1.0, 1.5, 2.0],  # Buffer size multiplier
            'mtbf_multiplier': [2.0, 3.0, 4.0],  # Increase time between failures
            'mttr_multiplier': [0.5, 0.7, 1.0],  # Reduce repair time
        }
        
        best_params, best_kpis = self.grid_search(param_ranges, simulation_days=1)
        
        print("\n" + "="*60)
        print("CALIBRATION RESULTS")
        print("="*60)
        print("\nBest Parameters:")
        for key, value in best_params.items():
            print(f"  {key}: {value}")
        
        print("\nResulting KPIs:")
        for key, value in best_kpis.items():
            target = self.target_kpis[key]
            gap = value - target
            print(f"  {key}: {value:.1f}% (target: {target:.1f}%, gap: {gap:+.1f}%)")
        
        # Save calibration results
        calibration = {
            'parameters': best_params,
            'kpis': best_kpis,
            'target_kpis': self.target_kpis
        }
        
        with open('calibration_results.yaml', 'w') as f:
            yaml.dump(calibration, f)
        
        print("\n✓ Calibration results saved to calibration_results.yaml")
        
        return best_params


def main():
    """Main calibration routine."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Calibrate twin model to match historical data')
    parser.add_argument('--target', type=str, 
                       default='archive/misc/data/mes_data_with_kpis.csv',
                       help='Path to target historical data CSV')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick calibration with limited parameter sweep')
    
    args = parser.parse_args()
    
    # Create calibrator
    calibrator = TwinCalibrator(args.target)
    
    if args.quick:
        # Run quick calibration
        best_params = calibrator.quick_calibration()
    else:
        # Run full calibration
        param_ranges = {
            'arrival_rate': [75, 100, 125, 150, 175],
            'base_rate': [60, 70, 80, 90, 100, 110],
            'buffer_capacity_multiplier': [0.5, 1.0, 1.5, 2.0, 2.5],
            'mtbf_multiplier': [1.0, 2.0, 3.0, 4.0, 5.0],
            'mttr_multiplier': [0.3, 0.5, 0.7, 1.0, 1.3],
        }
        
        best_params, best_kpis = calibrator.grid_search(param_ranges, simulation_days=2)
        
        print("\n" + "="*60)
        print("FULL CALIBRATION COMPLETE")
        print("="*60)
        print("\nOptimal Parameters:")
        for key, value in best_params.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()