"""Flow transducer for converting observables to MES-style records.

This module provides the FlowTransducer class that converts flow observables
into MES-style DataFrame records compatible with the ORIGINAL_2WEEK.csv format.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class FlowTransducer:
    """Converts flow observables to MES-style records."""

    def __init__(
        self,
        time_bucket: float = 5.0,
        base_timestamp: Optional[datetime] = None
    ) -> None:
        """Initialize flow transducer.

        Args:
            time_bucket: Time bucket size in minutes (default: 5 minutes)
            base_timestamp: Base timestamp for conversion (default: current time)
        """
        self.time_bucket = time_bucket
        self.base_timestamp = base_timestamp or datetime.now()

        # Column mapping for MES format
        self.mes_columns = [
            "Timestamp",
            "ProductionOrderID",
            "LineID",
            "EquipmentID",
            "EquipmentType",
            "ProductID",
            "ProductName",
            "MachineStatus",
            "DowntimeReason",
            "GoodUnitsProduced",
            "ScrapUnitsProduced",
            "TargetRate_units_per_5min",
            "StandardCost_per_unit",
            "SalePrice_per_unit",
            "Availability_Score",
            "Performance_Score",
            "Quality_Score",
            "OEE_Score"
        ]

    def process_observables(
        self,
        observables: list[dict[str, Any]],
        primitives: dict[str, Any]
    ) -> pd.DataFrame:
        """Convert observables to MES DataFrame.

        Args:
            observables: List of observable events
            primitives: Dictionary of primitive instances

        Returns:
            DataFrame in MES format
        """
        # Collect observables from all primitives
        all_observables = []
        for primitive_id, primitive in primitives.items():
            if hasattr(primitive, "observables"):
                for obs in primitive.observables:
                    obs["equipment_id"] = primitive_id
                    all_observables.append(obs)

        # Add provided observables
        all_observables.extend(observables)

        if not all_observables:
            logger.warning("No observables to process")
            return pd.DataFrame(columns=self.mes_columns)

        # Group by time buckets
        buckets = self._create_time_buckets(all_observables)

        # Convert to MES records
        records = []
        for bucket_time, bucket_data in buckets.items():
            # Group by equipment
            equipment_groups = self._group_by_equipment(bucket_data)

            for equipment_id, equipment_data in equipment_groups.items():
                record = self._create_mes_record(
                    bucket_time,
                    equipment_id,
                    equipment_data,
                    primitives.get(equipment_id)
                )
                if record:
                    records.append(record)

        # Create DataFrame
        df = pd.DataFrame(records)

        # Ensure all columns exist
        for col in self.mes_columns:
            if col not in df.columns:
                df[col] = None

        # Reorder columns and sort
        df = df[self.mes_columns]
        df = df.sort_values(["Timestamp", "LineID", "EquipmentID"])

        logger.info(f"Processed {len(all_observables)} observables into {len(df)} MES records")

        return df

    def _create_time_buckets(
        self,
        observables: list[dict[str, Any]]
    ) -> dict[float, list[dict[str, Any]]]:
        """Create time buckets for observables.

        Args:
            observables: List of observable events

        Returns:
            Dictionary mapping bucket times to observables
        """
        buckets = defaultdict(list)

        for obs in observables:
            timestamp = obs.get("timestamp", 0)
            bucket_time = (timestamp // self.time_bucket) * self.time_bucket
            buckets[bucket_time].append(obs)

        return dict(buckets)

    def _group_by_equipment(
        self,
        observables: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Group observables by equipment ID.

        Args:
            observables: List of observable events

        Returns:
            Dictionary mapping equipment IDs to observables
        """
        groups = defaultdict(list)

        for obs in observables:
            equipment_id = obs.get("equipment_id", "unknown")
            groups[equipment_id].append(obs)

        return dict(groups)

    def _create_mes_record(
        self,
        bucket_time: float,
        equipment_id: str,
        observables: list[dict[str, Any]],
        primitive: Optional[Any] = None
    ) -> Optional[dict[str, Any]]:
        """Create a single MES record.

        Args:
            bucket_time: Time bucket in minutes
            equipment_id: Equipment identifier
            observables: List of observables for this equipment/bucket
            primitive: Primitive instance (optional)

        Returns:
            MES record dictionary or None if no data
        """
        if not observables:
            return None

        # Convert bucket time to timestamp
        timestamp = self.base_timestamp + timedelta(minutes=bucket_time)

        # Extract line ID and equipment type from equipment_id
        parts = equipment_id.split("-")
        line_id = parts[0] if parts else "LINE1"
        equipment_type = parts[1] if len(parts) > 1 else "Equipment"

        # Calculate metrics from observables
        metrics = self._calculate_bucket_metrics(observables, primitive)

        # Determine machine status
        status = self._determine_status(observables)
        downtime_reason = self._get_downtime_reason(observables, status)

        # Get product information
        product_info = self._get_product_info(observables)

        # Create record
        record = {
            "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "ProductionOrderID": product_info.get("order_id", ""),
            "LineID": line_id,
            "EquipmentID": equipment_id,
            "EquipmentType": equipment_type,
            "ProductID": product_info.get("product_id", "default"),
            "ProductName": product_info.get("product_name", "Product"),
            "MachineStatus": status,
            "DowntimeReason": downtime_reason,
            "GoodUnitsProduced": metrics.get("good_units", 0),
            "ScrapUnitsProduced": metrics.get("scrap_units", 0),
            "TargetRate_units_per_5min": metrics.get("target_rate", 0),
            "StandardCost_per_unit": 1.0,  # Default cost
            "SalePrice_per_unit": 1.5,     # Default price
            "Availability_Score": metrics.get("availability", 0),
            "Performance_Score": metrics.get("performance", 0),
            "Quality_Score": metrics.get("quality", 0),
            "OEE_Score": metrics.get("oee", 0)
        }

        return record

    def _calculate_bucket_metrics(
        self,
        observables: list[dict[str, Any]],
        primitive: Optional[Any] = None
    ) -> dict[str, float]:
        """Calculate metrics for a time bucket.

        Args:
            observables: List of observables for this bucket
            primitive: Primitive instance (optional)

        Returns:
            Dictionary of calculated metrics
        """
        metrics = {
            "good_units": 0,
            "scrap_units": 0,
            "target_rate": 0,
            "availability": 100,
            "performance": 100,
            "quality": 100,
            "oee": 100
        }

        # Sum production volumes
        for obs in observables:
            if obs.get("event_type") == "batch_processed":
                metrics["good_units"] += obs.get("volume_out", 0)
                metrics["scrap_units"] += obs.get("scrap", 0)
            elif obs.get("event_type") == "products_collected":
                metrics["good_units"] += obs.get("volume", 0)

        # Get OEE metrics if available
        oee_events = [o for o in observables if o.get("event_type") == "oee_calculated"]
        if oee_events:
            latest_oee = oee_events[-1]  # Use most recent
            metrics["availability"] = latest_oee.get("availability", 100)
            metrics["performance"] = latest_oee.get("performance", 100)
            metrics["quality"] = latest_oee.get("quality", 100)
            metrics["oee"] = latest_oee.get("oee", 100)
        elif primitive and hasattr(primitive, "get_oee"):
            # Calculate from primitive
            metrics["oee"] = primitive.get_oee()
            if hasattr(primitive, "get_availability"):
                metrics["availability"] = primitive.get_availability()
            if hasattr(primitive, "get_performance"):
                metrics["performance"] = primitive.get_performance()
            if hasattr(primitive, "get_quality"):
                metrics["quality"] = primitive.get_quality()

        # Calculate target rate (units per 5 minutes)
        if primitive and hasattr(primitive, "processing"):
            nominal_rate = getattr(primitive.processing, "nominal_rate", 200)
            metrics["target_rate"] = nominal_rate * self.time_bucket
        elif primitive and hasattr(primitive, "nominal_rate"):
            metrics["target_rate"] = primitive.nominal_rate * self.time_bucket

        return metrics

    def _determine_status(self, observables: list[dict[str, Any]]) -> str:
        """Determine machine status from observables.

        Args:
            observables: List of observables

        Returns:
            Machine status string
        """
        # Check for state changes
        state_changes = [o for o in observables if o.get("event_type") == "state_change"]
        if state_changes:
            # Use the most recent state
            latest_state = state_changes[-1].get("new_state", "idle")
            return self._map_flow_state_to_status(latest_state)

        # Check for production events
        production_events = [
            o for o in observables
            if o.get("event_type") in ["batch_processed", "products_collected", "material_generated"]
        ]
        if production_events:
            return "Running"

        return "Idle"

    def _map_flow_state_to_status(self, flow_state: str) -> str:
        """Map flow state to MES machine status.

        Args:
            flow_state: Flow state from primitives

        Returns:
            MES machine status
        """
        status_map = {
            "idle": "Idle",
            "flowing": "Running",
            "starved_upstream": "Starved",
            "blocked_downstream": "Blocked",
            "failed": "Down",
            "maintenance": "Maintenance",
            "changeover": "Changeover"
        }
        return status_map.get(flow_state, "Unknown")

    def _get_downtime_reason(self, observables: list[dict[str, Any]], status: str) -> str:
        """Get downtime reason if machine is down.

        Args:
            observables: List of observables
            status: Current machine status

        Returns:
            Downtime reason or empty string
        """
        if status not in ["Down", "Maintenance", "Changeover", "Starved", "Blocked"]:
            return ""

        # Check for failure events
        failure_events = [o for o in observables if "failure" in o.get("event_type", "")]
        if failure_events:
            latest_failure = failure_events[-1]
            return latest_failure.get("failure_type", "Equipment Failure")

        # Map status to reason
        reason_map = {
            "Starved": "No Input Material",
            "Blocked": "Downstream Full",
            "Maintenance": "Planned Maintenance",
            "Changeover": "Product Changeover"
        }

        return reason_map.get(status, "Unknown")

    def _get_product_info(self, observables: list[dict[str, Any]]) -> dict[str, str]:
        """Get product information from observables.

        Args:
            observables: List of observables

        Returns:
            Dictionary with product information
        """
        info = {
            "order_id": "",
            "product_id": "default",
            "product_name": "Product"
        }

        # Check for order events
        order_events = [
            o for o in observables
            if o.get("event_type") in ["order_started", "order_completed", "material_generated"]
        ]

        if order_events:
            latest_order = order_events[-1]
            info["order_id"] = latest_order.get("order_id", "")
            info["product_id"] = latest_order.get("product_id", "default")

        # Map product ID to name
        product_names = {
            "default": "Standard Product",
            "PRODUCT-A": "Product A",
            "PRODUCT-B": "Product B",
            "PRODUCT-C": "Product C"
        }
        info["product_name"] = product_names.get(info["product_id"], info["product_id"])

        return info

    def export_to_csv(
        self,
        df: pd.DataFrame,
        filepath: str,
        append: bool = False
    ) -> None:
        """Export DataFrame to CSV file.

        Args:
            df: DataFrame to export
            filepath: Output file path
            append: Whether to append to existing file
        """
        mode = 'a' if append else 'w'
        header = not append

        df.to_csv(filepath, mode=mode, header=header, index=False)
        logger.info(f"Exported {len(df)} records to {filepath}")

    def aggregate_by_shift(
        self,
        df: pd.DataFrame,
        shift_hours: int = 8
    ) -> pd.DataFrame:
        """Aggregate MES records by shift.

        Args:
            df: MES DataFrame
            shift_hours: Hours per shift

        Returns:
            Aggregated DataFrame
        """
        if df.empty:
            return df

        # Convert timestamp to datetime
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])

        # Calculate shift
        df["Shift"] = (df["Timestamp"].dt.hour // shift_hours) + 1
        df["ShiftDate"] = df["Timestamp"].dt.date

        # Aggregate by shift
        aggregated = df.groupby(["ShiftDate", "Shift", "LineID", "EquipmentID"]).agg({
            "GoodUnitsProduced": "sum",
            "ScrapUnitsProduced": "sum",
            "Availability_Score": "mean",
            "Performance_Score": "mean",
            "Quality_Score": "mean",
            "OEE_Score": "mean"
        }).reset_index()

        return aggregated
