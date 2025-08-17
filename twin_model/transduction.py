"""
Transduction layer for converting SimPy simulation output to flat MES format.

This module provides functionality to transform hierarchical simulation data
from the twin_model into flat, tabular MES records matching the expected
format in mes_data_sample.csv.

The transduction process:
1. Flattens nested equipment states into individual records
2. Maps SimPy states to MES machine statuses
3. Adds production metadata (orders, products, costs)
4. Calculates KPI scores per equipment
5. Formats timestamps appropriately

Example:
    >>> from twin_model import SimulationRunner, ActionableParameters
    >>> from twin_model.transduction import MESTransducer
    >>> 
    >>> # Run simulation
    >>> runner = SimulationRunner(config)
    >>> results = runner.run_simulation(params)
    >>> 
    >>> # Convert to MES format
    >>> transducer = MESTransducer()
    >>> mes_df = transducer.transduce_simulation(results)
    >>> mes_df.to_csv('mes_output.csv', index=False)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import pandas as pd
from enum import Enum


class MESMachineStatus(str, Enum):
    """Valid machine statuses in MES system."""
    RUNNING = "Running"
    STOPPED = "Stopped"
    IDLE = "Idle"


@dataclass
class ProductInfo:
    """Product information for MES records.
    
    Attributes:
        product_id: Product SKU identifier
        product_name: Human-readable product name
        target_rate_per_5min: Expected production rate in units per 5 minutes
        standard_cost_per_unit: Manufacturing cost per unit
        sale_price_per_unit: Selling price per unit
    """
    product_id: str = "SKU-2001"
    product_name: str = "12oz Soda"
    target_rate_per_5min: int = 450
    standard_cost_per_unit: float = 0.20
    sale_price_per_unit: float = 0.65


@dataclass
class MESTransducer:
    """Converts SimPy simulation output to flat MES format.
    
    This class handles the transformation from hierarchical simulation data
    (one record per line per timestamp) to flat MES data (one record per
    equipment per timestamp).
    
    Attributes:
        base_timestamp: Starting timestamp for the simulation
        order_id: Production order identifier
        product_info: Product metadata for the production run
        state_mapping: Mapping from SimPy states to MES statuses
        downtime_mapping: Mapping from SimPy states to downtime reasons
    
    Example:
        >>> transducer = MESTransducer(
        ...     base_timestamp=datetime(2025, 6, 1),
        ...     order_id="ORD-1000"
        ... )
        >>> mes_records = transducer.transduce_record(sim_record)
    """
    
    base_timestamp: datetime = field(default_factory=lambda: datetime(2025, 6, 1))
    order_id: str = "ORD-1000"
    product_info: ProductInfo = field(default_factory=ProductInfo)
    
    # State mappings from SimPy to MES
    state_mapping: Dict[str, str] = field(default_factory=lambda: {
        "RUNNING": MESMachineStatus.RUNNING,
        "STOPPED_FAILURE": MESMachineStatus.STOPPED,
        "STOPPED_MAINTENANCE": MESMachineStatus.STOPPED,
        "STARVED": MESMachineStatus.STOPPED,
        "BLOCKED": MESMachineStatus.STOPPED,
        "IDLE": MESMachineStatus.IDLE,
    })
    
    downtime_mapping: Dict[str, str] = field(default_factory=lambda: {
        "STOPPED_FAILURE": "UNP-MECH",
        "STOPPED_MAINTENANCE": "PLN-PM",
        "STARVED": "UNP-MAT",
        "BLOCKED": "UNP-JAM",
    })
    
    def _calculate_timestamp(self, sim_minutes: float) -> datetime:
        """Convert simulation minutes to actual timestamp.
        
        Args:
            sim_minutes: Minutes elapsed in simulation
            
        Returns:
            Datetime timestamp for the MES record
        """
        return self.base_timestamp + timedelta(minutes=sim_minutes)
    
    def _calculate_scores(
        self,
        state: str,
        units_produced: int,
        units_scrapped: int,
        target_rate: int
    ) -> Dict[str, float]:
        """Calculate KPI scores for an equipment.
        
        Args:
            state: Current equipment state
            units_produced: Good units produced in period
            units_scrapped: Scrap units produced in period
            target_rate: Expected production rate
            
        Returns:
            Dictionary with availability, performance, quality, and OEE scores
        """
        # Availability: 100% if running, 0% if stopped
        availability = 100.0 if state == "RUNNING" else 0.0
        
        # Performance: actual vs target rate (capped at 100%)
        total_units = units_produced + units_scrapped
        performance = min(100.0, (total_units / target_rate * 100.0)) if target_rate > 0 else 0.0
        
        # Quality: good units / total units
        quality = (units_produced / total_units * 100.0) if total_units > 0 else 100.0
        
        # OEE: product of all three factors
        oee = (availability * performance * quality) / 10000.0
        
        return {
            "Availability_Score": round(availability, 1),
            "Performance_Score": round(performance, 1),
            "Quality_Score": round(quality, 1),
            "OEE_Score": round(oee, 1),
        }
    
    def transduce_record(self, sim_record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert one hierarchical simulation record to flat MES rows.
        
        Takes a single simulation snapshot (containing all equipment states)
        and converts it to multiple MES records (one per equipment).
        
        Args:
            sim_record: Hierarchical simulation record with structure:
                {
                    "timestamp": float,
                    "line_id": str,
                    "equipment_states": {
                        "EQUIP_ID": {
                            "state": str,
                            "units_produced": int,
                            "units_scrapped": int,
                            "oee": float
                        }, ...
                    }, ...
                }
                
        Returns:
            List of flat MES records, one per equipment
            
        Example:
            >>> record = {"timestamp": 5.0, "line_id": "LINE1", ...}
            >>> mes_rows = transducer.transduce_record(record)
            >>> len(mes_rows)  # One row per equipment
            3
        """
        mes_records: List[Dict[str, Any]] = []
        
        # Extract common fields
        timestamp = self._calculate_timestamp(sim_record["timestamp"])
        line_id = sim_record["line_id"]
        
        # Process each equipment
        equipment_states = sim_record.get("equipment_states", {})
        
        for equipment_id, equipment_data in equipment_states.items():
            # Determine equipment type from ID (e.g., "LINE1-FIL" -> "Filler")
            equipment_type = self._infer_equipment_type(equipment_id)
            
            # Get state and map to MES format
            simpy_state = equipment_data.get("state", "IDLE")
            machine_status = self.state_mapping.get(simpy_state, MESMachineStatus.IDLE)
            
            # Ensure we get the string value, not the enum
            if hasattr(machine_status, 'value'):
                machine_status = machine_status.value
            
            # Get downtime reason if stopped
            downtime_reason = ""
            if machine_status == MESMachineStatus.STOPPED.value:
                downtime_reason = self.downtime_mapping.get(simpy_state, "")
            
            # Extract production data
            good_units = equipment_data.get("units_produced", 0)
            scrap_units = equipment_data.get("units_scrapped", 0)
            
            # Calculate KPI scores
            scores = self._calculate_scores(
                simpy_state,
                good_units,
                scrap_units,
                self.product_info.target_rate_per_5min
            )
            
            # Build MES record
            mes_record = {
                "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "ProductionOrderID": self.order_id,
                "LineID": line_id.replace("LINE", ""),  # "LINE1" -> "1"
                "EquipmentID": equipment_id,
                "EquipmentType": equipment_type,
                "ProductID": self.product_info.product_id,
                "ProductName": self.product_info.product_name,
                "MachineStatus": machine_status,
                "DowntimeReason": downtime_reason,
                "GoodUnitsProduced": good_units,
                "ScrapUnitsProduced": scrap_units,
                "TargetRate_units_per_5min": self.product_info.target_rate_per_5min,
                "StandardCost_per_unit": self.product_info.standard_cost_per_unit,
                "SalePrice_per_unit": self.product_info.sale_price_per_unit,
                **scores  # Unpack score dictionary
            }
            
            mes_records.append(mes_record)
        
        return mes_records
    
    def _infer_equipment_type(self, equipment_id: str) -> str:
        """Infer equipment type from equipment ID.
        
        Args:
            equipment_id: Equipment identifier (e.g., "LINE1-FIL")
            
        Returns:
            Equipment type string (e.g., "Filler")
        """
        type_mapping = {
            "FIL": "Filler",
            "PCK": "Packer",
            "PAL": "Palletizer",
        }
        
        # Extract suffix after hyphen
        parts = equipment_id.split("-")
        if len(parts) >= 2:
            suffix = parts[-1]
            return type_mapping.get(suffix, "Unknown")
        
        return "Unknown"
    
    def transduce_simulation(
        self,
        sim_results: Any,
        include_empty_periods: bool = False
    ) -> pd.DataFrame:
        """Convert entire simulation results to MES DataFrame.
        
        Processes all simulation snapshots and converts them to a flat
        DataFrame matching the MES data format.
        
        Args:
            sim_results: SimulationResults object from twin_model
            include_empty_periods: Whether to include periods with no production
            
        Returns:
            DataFrame with MES records in the expected format
            
        Raises:
            ValueError: If sim_results doesn't have expected structure
            
        Example:
            >>> results = runner.run_simulation(params)
            >>> mes_df = transducer.transduce_simulation(results)
            >>> mes_df.shape
            (33, 18)  # 3 equipment * 11 timestamps = 33 rows
        """
        if not hasattr(sim_results, 'mes_data'):
            raise ValueError("sim_results must have 'mes_data' attribute")
        
        all_records: List[Dict[str, Any]] = []
        
        # Process each simulation snapshot
        for sim_record in sim_results.mes_data:
            mes_records = self.transduce_record(sim_record)
            
            # Filter empty periods if requested
            if not include_empty_periods:
                mes_records = [
                    r for r in mes_records
                    if r["GoodUnitsProduced"] > 0 or r["ScrapUnitsProduced"] > 0 or r["MachineStatus"] != "Idle"
                ]
            
            all_records.extend(mes_records)
        
        # Convert to DataFrame
        if all_records:
            df = pd.DataFrame(all_records)
            
            # Ensure column order matches mes_data_sample.csv
            column_order = [
                "Timestamp", "ProductionOrderID", "LineID", "EquipmentID",
                "EquipmentType", "ProductID", "ProductName", "MachineStatus",
                "DowntimeReason", "GoodUnitsProduced", "ScrapUnitsProduced",
                "TargetRate_units_per_5min", "StandardCost_per_unit",
                "SalePrice_per_unit", "Availability_Score", "Performance_Score",
                "Quality_Score", "OEE_Score"
            ]
            
            # Reorder columns to match expected format
            df = df[column_order]
            
            return df
        else:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=[
                "Timestamp", "ProductionOrderID", "LineID", "EquipmentID",
                "EquipmentType", "ProductID", "ProductName", "MachineStatus",
                "DowntimeReason", "GoodUnitsProduced", "ScrapUnitsProduced",
                "TargetRate_units_per_5min", "StandardCost_per_unit",
                "SalePrice_per_unit", "Availability_Score", "Performance_Score",
                "Quality_Score", "OEE_Score"
            ])


def create_transducer_from_ontology(
    ontology_path: str = "ontology/twin_ontology.yaml"
) -> MESTransducer:
    """Create a MESTransducer configured from the twin ontology.
    
    Reads the transduction_layer section from the ontology to configure
    state mappings and other transformation rules.
    
    Args:
        ontology_path: Path to twin_ontology.yaml file
        
    Returns:
        Configured MESTransducer instance
        
    Raises:
        FileNotFoundError: If ontology file doesn't exist
        KeyError: If required ontology sections are missing
        
    Example:
        >>> transducer = create_transducer_from_ontology()
        >>> transducer.state_mapping
        {'RUNNING': 'Running', 'STOPPED_FAILURE': 'Stopped', ...}
    """
    import yaml
    from pathlib import Path
    
    ontology_file = Path(ontology_path)
    if not ontology_file.exists():
        raise FileNotFoundError(f"Ontology file not found: {ontology_path}")
    
    with open(ontology_file, 'r') as f:
        ontology = yaml.safe_load(f)
    
    # Extract transduction layer configuration
    transduction_config = ontology.get("transduction_layer", {})
    
    # Build state mapping
    state_mapping = transduction_config.get("equipment_state_mapping", {})
    
    # Build downtime mapping (infer from states that map to "Stopped")
    downtime_mapping = {
        "STOPPED_FAILURE": "UNP-MECH",
        "STOPPED_MAINTENANCE": "PLN-PM",
        "STARVED": "UNP-MAT",
        "BLOCKED": "UNP-JAM",
    }
    
    # TODO: Extract product info and other metadata from ontology
    
    return MESTransducer(
        state_mapping=state_mapping if state_mapping else None,
        downtime_mapping=downtime_mapping
    )


if __name__ == "__main__":
    # Example usage and testing
    print("MES Transduction Layer Module")
    print("=" * 60)
    
    # Create example simulation record
    example_record = {
        "timestamp": 5.0,
        "line_id": "LINE1",
        "equipment_states": {
            "LINE1-FIL": {
                "state": "RUNNING",
                "units_produced": 295,
                "units_scrapped": 5,
                "oee": 98.3
            },
            "LINE1-PCK": {
                "state": "STOPPED_FAILURE",
                "units_produced": 0,
                "units_scrapped": 0,
                "oee": 0.0
            },
            "LINE1-PAL": {
                "state": "RUNNING",
                "units_produced": 245,
                "units_scrapped": 2,
                "oee": 97.6
            }
        }
    }
    
    # Test transduction
    transducer = MESTransducer()
    mes_records = transducer.transduce_record(example_record)
    
    print(f"Input: 1 hierarchical record")
    print(f"Output: {len(mes_records)} flat MES records")
    print()
    
    # Show first record
    if mes_records:
        print("First MES record:")
        for key, value in mes_records[0].items():
            print(f"  {key}: {value}")