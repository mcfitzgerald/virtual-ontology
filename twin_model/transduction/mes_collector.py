"""MES Data Collector for capturing simulation events in MES format.

This module provides a data collector that captures simulation events
and formats them according to MES (Manufacturing Execution System) standards.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import simpy
from pathlib import Path

from twin_model.primitives.base_flow import BaseFlowPrimitive, FlowState

logger = logging.getLogger(__name__)


@dataclass
class MESRecord:
    """Single MES data record for a 5-minute interval."""
    
    timestamp: datetime
    production_order_id: str
    line_id: str
    equipment_id: str
    equipment_type: str
    product_id: str
    product_name: str
    machine_status: str  # Running or Stopped
    downtime_reason: Optional[str]
    good_units_produced: float
    scrap_units_produced: float
    target_rate_units_per_5min: float
    standard_cost_per_unit: float
    sale_price_per_unit: float
    availability_score: float
    performance_score: float
    quality_score: float
    oee_score: float


@dataclass
class ProductInfo:
    """Product information for MES records."""
    
    product_id: str
    product_name: str
    standard_cost: float
    sale_price: float
    target_rate: float  # Units per 5 minutes


class MESDataCollector:
    """Collects simulation data and formats it for MES output.
    
    This collector monitors equipment primitives and captures their state
    and production metrics at regular intervals (default 5 minutes).
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        interval_minutes: float = 5.0,
        start_date: Optional[datetime] = None
    ):
        """Initialize MES data collector.
        
        Args:
            env: SimPy environment
            interval_minutes: Collection interval in minutes (default 5)
            start_date: Simulation start date (default: current date)
        """
        self.env = env
        self.interval = interval_minutes
        self.start_date = start_date or datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        # Storage for collected data
        self.records: List[MESRecord] = []
        self.equipment_registry: Dict[str, BaseFlowPrimitive] = {}
        self.product_info: Dict[str, ProductInfo] = {}
        
        # Tracking for interval metrics
        self.interval_start_metrics: Dict[str, Dict[str, Any]] = {}
        self.current_order: Dict[str, str] = {}  # equipment_id -> order_id
        self.current_product: Dict[str, str] = {}  # equipment_id -> product_id
        
        # Default product info (can be overridden)
        self._setup_default_products()
        
    def _setup_default_products(self):
        """Set up default product information."""
        self.product_info = {
            "SKU-1001": ProductInfo(
                product_id="SKU-1001",
                product_name="8oz Water Bottle",
                standard_cost=0.15,
                sale_price=0.50,
                target_rate=475
            ),
            "SKU-1002": ProductInfo(
                product_id="SKU-1002",
                product_name="8oz Juice",
                standard_cost=0.25,
                sale_price=0.85,
                target_rate=475
            ),
            "SKU-2001": ProductInfo(
                product_id="SKU-2001",
                product_name="12oz Soda",
                standard_cost=0.20,
                sale_price=0.65,
                target_rate=475
            ),
            "SKU-2002": ProductInfo(
                product_id="SKU-2002",
                product_name="16oz Energy Drink",
                standard_cost=0.55,
                sale_price=1.75,
                target_rate=450
            ),
            "SKU-3001": ProductInfo(
                product_id="SKU-3001",
                product_name="20oz Sports Drink",
                standard_cost=0.35,
                sale_price=1.15,
                target_rate=450
            ),
            "SKU-3002": ProductInfo(
                product_id="SKU-3002",
                product_name="1L Juice",
                standard_cost=0.75,
                sale_price=2.50,
                target_rate=425
            )
        }
    
    def register_equipment(
        self,
        equipment_id: str,
        equipment: BaseFlowPrimitive,
        equipment_type: str,
        line_id: str
    ):
        """Register equipment for monitoring.
        
        Args:
            equipment_id: Unique equipment identifier
            equipment: Equipment primitive to monitor
            equipment_type: Type (Filler, Packer, Palletizer)
            line_id: Production line ID
        """
        self.equipment_registry[equipment_id] = {
            'primitive': equipment,
            'type': equipment_type,
            'line_id': line_id
        }
        
        # Initialize tracking
        self.interval_start_metrics[equipment_id] = self._capture_metrics(equipment)
        self.current_order[equipment_id] = "ORD-1000"  # Default order
        self.current_product[equipment_id] = "SKU-1001"  # Default product
        
    def update_production_order(
        self,
        equipment_id: str,
        order_id: str,
        product_id: str
    ):
        """Update current production order for equipment.
        
        Args:
            equipment_id: Equipment identifier
            order_id: Production order ID
            product_id: Product being produced
        """
        if equipment_id in self.equipment_registry:
            self.current_order[equipment_id] = order_id
            self.current_product[equipment_id] = product_id
            logger.debug(f"{equipment_id} now producing {product_id} for order {order_id}")
    
    def _capture_metrics(self, equipment: BaseFlowPrimitive) -> Dict[str, Any]:
        """Capture current metrics from equipment.
        
        Args:
            equipment: Equipment to capture metrics from
            
        Returns:
            Dictionary of current metrics
        """
        return {
            'total_output': equipment.total_output,
            'total_scrap': equipment.total_scrap,
            'total_input': equipment.total_input,
            'state_durations': equipment.state_durations.copy(),
            'timestamp': self.env.now
        }
    
    def _calculate_interval_metrics(
        self,
        equipment_id: str,
        equipment: BaseFlowPrimitive,
        start_metrics: Dict[str, Any],
        end_metrics: Dict[str, Any]
    ) -> Tuple[float, float, float, float, float]:
        """Calculate metrics for the collection interval.
        
        Args:
            equipment_id: Equipment identifier
            equipment: Equipment primitive
            start_metrics: Metrics at interval start
            end_metrics: Metrics at interval end
            
        Returns:
            Tuple of (good_units, scrap_units, availability, performance, quality)
        """
        # Production in this interval
        good_units = end_metrics['total_output'] - start_metrics['total_output']
        scrap_units = end_metrics['total_scrap'] - start_metrics['total_scrap']
        total_input = end_metrics['total_input'] - start_metrics['total_input']
        
        # Time calculations
        interval_duration = end_metrics['timestamp'] - start_metrics['timestamp']
        
        # State durations in this interval
        running_time = 0.0
        failed_time = 0.0
        
        for state in FlowState:
            end_duration = end_metrics['state_durations'].get(state, 0)
            start_duration = start_metrics['state_durations'].get(state, 0)
            state_time = end_duration - start_duration
            
            if state in [FlowState.FLOWING, FlowState.IDLE]:
                running_time += state_time
            elif state == FlowState.FAILED:
                failed_time += state_time
        
        # Calculate OEE components
        availability = (running_time / interval_duration * 100) if interval_duration > 0 else 0
        
        # Get nominal rate for performance calculation
        product_id = self.current_product.get(equipment_id, "SKU-1001")
        product_info = self.product_info.get(product_id)
        nominal_rate = product_info.target_rate if product_info else 450
        
        # Performance: actual vs nominal
        actual_rate = (good_units + scrap_units) / self.interval if self.interval > 0 else 0
        nominal_rate_per_min = nominal_rate / 5.0  # Convert to per minute
        performance = (actual_rate / nominal_rate_per_min * 100) if nominal_rate_per_min > 0 else 0
        performance = min(performance, 100)  # Cap at 100%
        
        # Quality: good vs total
        total_output = good_units + scrap_units
        quality = (good_units / total_output * 100) if total_output > 0 else 100
        
        return good_units, scrap_units, availability, performance, quality
    
    def collect_data(self):
        """Collect data at regular intervals (coroutine)."""
        while True:
            # Wait for collection interval
            yield self.env.timeout(self.interval)
            
            # Current timestamp
            sim_minutes = self.env.now
            current_time = self.start_date + timedelta(minutes=sim_minutes)
            
            # Collect data from all registered equipment
            for equipment_id, info in self.equipment_registry.items():
                equipment = info['primitive']
                equipment_type = info['type']
                line_id = info['line_id']
                
                # Capture current metrics
                end_metrics = self._capture_metrics(equipment)
                start_metrics = self.interval_start_metrics[equipment_id]
                
                # Calculate interval metrics
                good_units, scrap_units, availability, performance, quality = \
                    self._calculate_interval_metrics(
                        equipment_id, equipment, start_metrics, end_metrics
                    )
                
                # Determine machine status and downtime reason
                machine_status = "Running"
                downtime_reason = None
                
                if equipment.state == FlowState.FAILED:
                    machine_status = "Stopped"
                    # Get downtime reason from equipment if available
                    downtime_reason = getattr(equipment, 'downtime_reason', 'UNP-FAIL')
                elif availability < 50:
                    machine_status = "Stopped"
                    downtime_reason = "UNP-STOP"
                
                # Get product info
                product_id = self.current_product.get(equipment_id, "SKU-1001")
                product_info = self.product_info.get(product_id)
                
                if not product_info:
                    product_info = self.product_info["SKU-1001"]  # Default
                
                # Calculate OEE
                oee = (availability * performance * quality) / 10000
                
                # Create MES record
                record = MESRecord(
                    timestamp=current_time,
                    production_order_id=self.current_order.get(equipment_id, "ORD-1000"),
                    line_id=line_id,
                    equipment_id=equipment_id,
                    equipment_type=equipment_type,
                    product_id=product_id,
                    product_name=product_info.product_name,
                    machine_status=machine_status,
                    downtime_reason=downtime_reason,
                    good_units_produced=round(good_units),
                    scrap_units_produced=round(scrap_units),
                    target_rate_units_per_5min=product_info.target_rate,
                    standard_cost_per_unit=product_info.standard_cost,
                    sale_price_per_unit=product_info.sale_price,
                    availability_score=round(availability, 1),
                    performance_score=round(performance, 1),
                    quality_score=round(quality, 1),
                    oee_score=round(oee, 1)
                )
                
                self.records.append(record)
                
                # Update start metrics for next interval
                self.interval_start_metrics[equipment_id] = end_metrics
            
            # Log progress
            if len(self.records) % 100 == 0:
                logger.info(f"Collected {len(self.records)} MES records")
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert collected records to pandas DataFrame.
        
        Returns:
            DataFrame with MES records
        """
        if not self.records:
            return pd.DataFrame()
        
        data = []
        for record in self.records:
            data.append({
                'Timestamp': record.timestamp,
                'ProductionOrderID': record.production_order_id,
                'LineID': record.line_id,
                'EquipmentID': record.equipment_id,
                'EquipmentType': record.equipment_type,
                'ProductID': record.product_id,
                'ProductName': record.product_name,
                'MachineStatus': record.machine_status,
                'DowntimeReason': record.downtime_reason,
                'GoodUnitsProduced': record.good_units_produced,
                'ScrapUnitsProduced': record.scrap_units_produced,
                'TargetRate_units_per_5min': record.target_rate_units_per_5min,
                'StandardCost_per_unit': record.standard_cost_per_unit,
                'SalePrice_per_unit': record.sale_price_per_unit,
                'Availability_Score': record.availability_score,
                'Performance_Score': record.performance_score,
                'Quality_Score': record.quality_score,
                'OEE_Score': record.oee_score
            })
        
        return pd.DataFrame(data)
    
    def save_to_csv(self, filepath: Path):
        """Save collected data to CSV file.
        
        Args:
            filepath: Path to save CSV file
        """
        df = self.to_dataframe()
        df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(df)} MES records to {filepath}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of collected data.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.records:
            return {}
        
        df = self.to_dataframe()
        
        return {
            'total_records': len(df),
            'date_range': {
                'start': df['Timestamp'].min(),
                'end': df['Timestamp'].max()
            },
            'production': {
                'total_good': df['GoodUnitsProduced'].sum(),
                'total_scrap': df['ScrapUnitsProduced'].sum(),
                'scrap_rate': df['ScrapUnitsProduced'].sum() / 
                             (df['GoodUnitsProduced'].sum() + df['ScrapUnitsProduced'].sum()) * 100
            },
            'oee': {
                'mean': df['OEE_Score'].mean(),
                'std': df['OEE_Score'].std(),
                'min': df['OEE_Score'].min(),
                'max': df['OEE_Score'].max()
            },
            'availability': df['Availability_Score'].mean(),
            'performance': df['Performance_Score'].mean(),
            'quality': df['Quality_Score'].mean(),
            'downtime_percentage': (df['MachineStatus'] == 'Stopped').mean() * 100
        }