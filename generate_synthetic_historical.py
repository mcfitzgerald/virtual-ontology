#!/usr/bin/env python3
"""
Generate synthetic historical baseline data for the Virtual Twin POC.

This script generates realistic manufacturing data by running multiple simulations
with variations to create a rich historical dataset that matches the target profile:
- OEE: ~47% (Availability: 69%, Performance: 52%, Quality: 63%)
- Downtime: ~30% of intervals
- Scrap Rate: 8-9%

The data is stored in the historical_mes_data table with source='synthetic' for clarity.

Author: Virtual Twin Team
Date: 2025-01-22
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import simpy
import json
import random
import hashlib
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from twin_model.model_builder import OntologyDrivenModelBuilder
from twin_model.config import PerformanceConfig, ConfigPreset
from twin_model.primitives.base import SamplingConfig, SimulationMode
from twin_model.transduction.mes_transducer import MESTransducer
from database.manager import TwinDatabaseManager
from database.models import HistoricalMESData, TwinRun
from sqlmodel import Session, select


class SyntheticHistoricalGenerator:
    """
    Generates synthetic historical data for manufacturing POC.
    
    This class runs multiple simulations with parameter variations to create
    realistic historical data that matches the target OEE profile of ~47%.
    """
    
    def __init__(self, 
                 db_manager: Optional[TwinDatabaseManager] = None,
                 target_days: int = 30,
                 variations: int = 3):
        """
        Initialize the synthetic historical data generator.
        
        Args:
            db_manager: Database manager instance
            target_days: Number of days of historical data to generate
            variations: Number of simulation variations to run and combine
        """
        self.db_manager = db_manager or TwinDatabaseManager()
        self.target_days = target_days
        self.variations = variations
        self.target_oee = 47.0  # Target OEE percentage
        self.target_availability = 69.0  # Target availability
        self.target_performance = 52.0  # Target performance  
        self.target_quality = 63.0  # Target quality
        
    def generate_parameter_variation(self, base_seed: int) -> Dict[str, float]:
        """
        Generate parameter variations for realistic diversity.
        
        Args:
            base_seed: Base random seed for this variation
            
        Returns:
            Dictionary of parameter multipliers
        """
        random.seed(base_seed)
        
        # Create variations around baseline (1.0)
        # These affect the failure rates and performance
        params = {
            'micro_stop_probability': random.uniform(0.9, 1.2),  # ±20% variation
            'performance_factor': random.uniform(0.95, 1.05),    # ±5% variation
            'scrap_multiplier': random.uniform(0.95, 1.1),       # +10%/-5% variation
            'material_reliability': random.uniform(0.9, 1.05),   # ±5-10% variation
            'cascade_sensitivity': random.uniform(0.95, 1.15),   # ±5-15% variation
        }
        
        return params
    
    def run_simulation_variant(self, 
                              variant_id: int,
                              parameters: Dict[str, float],
                              seed: int) -> pd.DataFrame:
        """
        Run a single simulation variant with specific parameters.
        
        Args:
            variant_id: Identifier for this variant
            parameters: Parameter multipliers for this run
            seed: Random seed for reproducibility
            
        Returns:
            DataFrame with MES-format simulation results
        """
        print(f"\n  Running variant {variant_id} with seed {seed}")
        print(f"    Parameters: {json.dumps(parameters, indent=6)}")
        
        # Configure performance for balanced data collection
        config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
        config.sampling_rate = 1  # Keep ALL events for accurate data (1 = every event)
        
        # Build model
        ontology_path = Path("ontology/twin_ontology.yaml")
        manifest_dir = Path("manifests")
        
        builder = OntologyDrivenModelBuilder(
            ontology_path=ontology_path,
            manifest_dir=manifest_dir
        )
        
        # Create SimPy environment with seed
        random.seed(seed)
        np.random.seed(seed)
        env = simpy.Environment()
        
        # Build model with parameters
        model = builder.build_model(env)
        
        # Apply parameter variations to primitives
        for prim_id, primitive in builder.primitives.items():
            if hasattr(primitive, 'config'):
                # Apply performance factor
                if hasattr(primitive.config.properties, 'base_rate'):
                    primitive.config.properties['base_rate'] *= parameters.get('performance_factor', 1.0)
                
                # Apply scrap multiplier
                if hasattr(primitive.config.properties, 'base_scrap_rate'):
                    primitive.config.properties['base_scrap_rate'] *= parameters.get('scrap_multiplier', 1.0)
                
                # Apply micro-stop probability to failure patterns
                if hasattr(primitive, 'failure_patterns'):
                    for pattern in primitive.failure_patterns.values():
                        if 'probability_per_5min' in pattern:
                            pattern['probability_per_5min'] *= parameters.get('micro_stop_probability', 1.0)
        
        # Configure sampling
        sampling = SamplingConfig(
            mode=SimulationMode.PRODUCTION,
            sampling_rate=1,  # Keep ALL events (1 = every event)
            buffer_size=config.observable_buffer_size,
            aggregation_interval=5.0,  # 5-minute buckets
            enable_global_observables=False
        )
        
        # Apply sampling to primitives
        for primitive in builder.primitives.values():
            if hasattr(primitive, 'sampling_config'):
                primitive.sampling_config = sampling
        
        # Run simulation
        simulation_minutes = self.target_days * 24 * 60
        print(f"    Running {self.target_days}-day simulation...")
        env.run(until=simulation_minutes)
        
        # Collect observables
        all_observables = []
        for primitive_id, primitive in builder.primitives.items():
            if hasattr(primitive, 'observables'):
                for obs in primitive.observables:
                    obs['primitive_id'] = primitive_id
                    obs['primitive_type'] = type(primitive).__name__
                    obs['variant_id'] = variant_id
                    all_observables.append(obs)
        
        print(f"    Collected {len(all_observables):,} observable events")
        
        # Transduce to MES format
        transducer = MESTransducer(time_bucket=5)
        mes_df = transducer.process_observables(all_observables, builder.manifests)
        
        # Add variant identifier
        mes_df['variant_id'] = variant_id
        
        return mes_df
    
    def combine_variants(self, variant_dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Combine multiple variant DataFrames into unified historical data.
        
        This method interleaves data from different variants to create
        realistic variation patterns in the historical data.
        
        Args:
            variant_dfs: List of DataFrames from different simulation variants
            
        Returns:
            Combined DataFrame with realistic variations
        """
        print("\n📊 Combining variant data...")
        
        # Concatenate all variants
        combined_df = pd.concat(variant_dfs, ignore_index=True)
        
        # Sort by timestamp and equipment to maintain consistency
        combined_df = combined_df.sort_values(['Timestamp', 'LineID', 'EquipmentID'])
        
        # Add time-based variations (shift patterns, weekly cycles)
        combined_df = self.add_temporal_patterns(combined_df)
        
        # Calculate aggregated statistics
        stats = self.calculate_statistics(combined_df)
        print(f"\n  Combined Statistics:")
        print(f"    Total records: {len(combined_df):,}")
        print(f"    Mean OEE: {stats['mean_oee']:.1f}%")
        print(f"    Mean Availability: {stats['mean_availability']:.1f}%")
        print(f"    Mean Performance: {stats['mean_performance']:.1f}%")
        print(f"    Mean Quality: {stats['mean_quality']:.1f}%")
        print(f"    Downtime percentage: {stats['downtime_pct']:.1f}%")
        print(f"    Overall scrap rate: {stats['scrap_rate']:.1f}%")
        
        return combined_df
    
    def add_temporal_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add realistic temporal patterns to the data.
        
        Args:
            df: DataFrame with simulation data
            
        Returns:
            DataFrame with added temporal patterns
        """
        # Convert timestamp to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['Timestamp']):
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # Add hour of day
        df['hour'] = df['Timestamp'].dt.hour
        
        # Add day of week
        df['day_of_week'] = df['Timestamp'].dt.dayofweek
        
        # Add shift (1: 6am-2pm, 2: 2pm-10pm, 3: 10pm-6am)
        df['shift'] = df['hour'].apply(lambda h: 1 if 6 <= h < 14 else (2 if 14 <= h < 22 else 3))
        
        # Apply shift-based performance variations
        shift_factors = {1: 1.0, 2: 0.95, 3: 0.90}  # Night shift has lower performance
        
        for shift, factor in shift_factors.items():
            shift_mask = df['shift'] == shift
            df.loc[shift_mask, 'Performance_Score'] *= factor
            df.loc[shift_mask, 'OEE_Score'] = (
                df.loc[shift_mask, 'Availability_Score'] * 
                df.loc[shift_mask, 'Performance_Score'] * 
                df.loc[shift_mask, 'Quality_Score'] / 10000
            )
        
        # Apply weekend effects (lower performance on weekends)
        weekend_mask = df['day_of_week'].isin([5, 6])  # Saturday, Sunday
        df.loc[weekend_mask, 'Performance_Score'] *= 0.85
        df.loc[weekend_mask, 'Quality_Score'] *= 0.95
        
        # Recalculate OEE for weekend
        df.loc[weekend_mask, 'OEE_Score'] = (
            df.loc[weekend_mask, 'Availability_Score'] * 
            df.loc[weekend_mask, 'Performance_Score'] * 
            df.loc[weekend_mask, 'Quality_Score'] / 10000
        )
        
        # Drop temporary columns
        df = df.drop(columns=['hour', 'day_of_week', 'shift'])
        
        return df
    
    def calculate_statistics(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate key statistics from the data.
        
        Args:
            df: DataFrame with MES data
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'mean_oee': df['OEE_Score'].mean() if 'OEE_Score' in df else 0,
            'mean_availability': df['Availability_Score'].mean() if 'Availability_Score' in df else 0,
            'mean_performance': df['Performance_Score'].mean() if 'Performance_Score' in df else 0,
            'mean_quality': df['Quality_Score'].mean() if 'Quality_Score' in df else 0,
            'total_good_units': df['GoodUnitsProduced'].sum() if 'GoodUnitsProduced' in df else 0,
            'total_scrap_units': df['ScrapUnitsProduced'].sum() if 'ScrapUnitsProduced' in df else 0,
            'downtime_pct': 0,
            'scrap_rate': 0
        }
        
        # Calculate downtime percentage
        if 'MachineStatus' in df:
            stopped_count = len(df[df['MachineStatus'] == 'Stopped'])
            stats['downtime_pct'] = (stopped_count / len(df)) * 100 if len(df) > 0 else 0
        
        # Calculate overall scrap rate
        total_units = stats['total_good_units'] + stats['total_scrap_units']
        if total_units > 0:
            stats['scrap_rate'] = (stats['total_scrap_units'] / total_units) * 100
        
        return stats
    
    def store_to_database(self, df: pd.DataFrame, run_id: str) -> None:
        """
        Store synthetic data in the historical_mes_data table.
        
        Args:
            df: DataFrame with synthetic historical data
            run_id: Identifier for this generation run
        """
        print("\n💾 Storing synthetic historical data in database...")
        
        with Session(self.db_manager.engine) as session:
            # Clear existing synthetic historical data
            existing = session.exec(
                select(HistoricalMESData).where(HistoricalMESData.source == "synthetic")
            ).all()
            
            if existing:
                print(f"  Clearing {len(existing)} existing synthetic records...")
                for record in existing:
                    session.delete(record)
                session.commit()
            
            # Prepare data for insertion
            records_added = 0
            batch_size = 1000
            
            # Adjust timestamps to be in the past (last 30 days)
            base_date = datetime.now() - timedelta(days=self.target_days)
            
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                
                for _, row in batch_df.iterrows():
                    # Calculate historical timestamp
                    if pd.notna(row.get('Timestamp')):
                        # Convert simulation time to historical date
                        sim_minutes = i * 5  # Assuming 5-minute intervals
                        historical_timestamp = base_date + timedelta(minutes=sim_minutes)
                    else:
                        historical_timestamp = base_date
                    
                    record = HistoricalMESData(
                        timestamp=historical_timestamp,
                        production_order_id=row.get('ProductionOrderID'),
                        line_id=str(row.get('LineID', '')),
                        equipment_id=row.get('EquipmentID', ''),
                        equipment_type=row.get('EquipmentType', ''),
                        product_id=row.get('ProductID'),
                        product_name=row.get('ProductName'),
                        machine_status=row.get('MachineStatus', 'Unknown'),
                        downtime_reason=row.get('DowntimeReason'),
                        good_units_produced=int(row.get('GoodUnitsProduced', 0)),
                        scrap_units_produced=int(row.get('ScrapUnitsProduced', 0)),
                        target_rate_units_per_5min=int(row.get('TargetRate_units_per_5min', 0)),
                        standard_cost_per_unit=float(row.get('StandardCost_per_unit', 0)),
                        sale_price_per_unit=float(row.get('SalePrice_per_unit', 0)),
                        availability_score=float(row.get('Availability_Score', 0)),
                        performance_score=float(row.get('Performance_Score', 0)),
                        quality_score=float(row.get('Quality_Score', 0)),
                        oee_score=float(row.get('OEE_Score', 0)),
                        energy_consumption_kwh=float(row.get('Energy_Consumption_kWh', 0)) if 'Energy_Consumption_kWh' in row else None,
                        source="synthetic",  # Mark as synthetic data
                        import_date=datetime.utcnow(),
                        data_quality_score=0.85  # Synthetic data quality score
                    )
                    session.add(record)
                    records_added += 1
                
                # Commit batch
                if records_added % batch_size == 0:
                    session.commit()
                    print(f"    Stored {records_added:,} records...")
            
            # Final commit
            session.commit()
            print(f"  ✓ Stored {records_added:,} synthetic historical records")
    
    def export_to_csv(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        """
        Export synthetic historical data to CSV file.
        
        Args:
            df: DataFrame with synthetic data
            filename: Optional filename (defaults to timestamped name)
            
        Returns:
            Path to exported CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"synthetic_historical_{timestamp}.csv"
        
        # Ensure data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        csv_path = data_dir / filename
        df.to_csv(csv_path, index=False)
        
        file_size_mb = csv_path.stat().st_size / (1024 * 1024)
        print(f"\n  ✓ Exported to: {csv_path}")
        print(f"  ✓ File size: {file_size_mb:.2f}MB")
        
        return csv_path
    
    def generate(self) -> Tuple[pd.DataFrame, str]:
        """
        Main method to generate synthetic historical data.
        
        Returns:
            Tuple of (DataFrame with synthetic data, run_id)
        """
        print("=" * 70)
        print(" " * 15 + "SYNTHETIC HISTORICAL DATA GENERATOR")
        print("=" * 70)
        print()
        print(f"📋 Configuration:")
        print(f"  Target days: {self.target_days}")
        print(f"  Variations: {self.variations}")
        print(f"  Target OEE: {self.target_oee}%")
        print(f"  Target metrics: A={self.target_availability}%, P={self.target_performance}%, Q={self.target_quality}%")
        print()
        
        # Generate run ID
        run_id = f"synthetic_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Run multiple variants
        variant_dfs = []
        for i in range(self.variations):
            print(f"\n🔄 Generating variant {i+1}/{self.variations}")
            
            # Generate parameters for this variant
            seed = 42 + i * 1000  # Different seed for each variant
            params = self.generate_parameter_variation(seed)
            
            # Run simulation
            variant_df = self.run_simulation_variant(i+1, params, seed)
            variant_dfs.append(variant_df)
            
            # Show variant statistics
            variant_stats = self.calculate_statistics(variant_df)
            print(f"    Variant {i+1} OEE: {variant_stats['mean_oee']:.1f}%")
        
        # Combine variants
        combined_df = self.combine_variants(variant_dfs)
        
        # Store in database
        self.store_to_database(combined_df, run_id)
        
        # Export to CSV
        csv_path = self.export_to_csv(combined_df)
        
        # Final summary
        print("\n" + "=" * 70)
        print(" " * 20 + "GENERATION COMPLETE! 🎉")
        print("=" * 70)
        
        final_stats = self.calculate_statistics(combined_df)
        print("\n📊 Final Statistics:")
        print(f"  Total records: {len(combined_df):,}")
        print(f"  Mean OEE: {final_stats['mean_oee']:.1f}% (target: {self.target_oee}%)")
        print(f"  Mean Availability: {final_stats['mean_availability']:.1f}% (target: {self.target_availability}%)")
        print(f"  Mean Performance: {final_stats['mean_performance']:.1f}% (target: {self.target_performance}%)")
        print(f"  Mean Quality: {final_stats['mean_quality']:.1f}% (target: {self.target_quality}%)")
        print(f"  Downtime: {final_stats['downtime_pct']:.1f}% (target: ~30%)")
        print(f"  Scrap rate: {final_stats['scrap_rate']:.1f}% (target: 8-9%)")
        print()
        print("📂 Output:")
        print(f"  Database: historical_mes_data table (source='synthetic')")
        print(f"  CSV file: {csv_path}")
        print(f"  Run ID: {run_id}")
        print()
        
        return combined_df, run_id


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic historical data for Virtual Twin POC')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days of historical data to generate (default: 30)')
    parser.add_argument('--variations', type=int, default=3,
                       help='Number of simulation variations to combine (default: 3)')
    parser.add_argument('--export-only', action='store_true',
                       help='Only export to CSV without storing in database')
    args = parser.parse_args()
    
    try:
        # Create generator
        generator = SyntheticHistoricalGenerator(
            target_days=args.days,
            variations=args.variations
        )
        
        # Generate data
        df, run_id = generator.generate()
        
        print("✅ Synthetic historical data generation completed successfully!")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()