"""MES Transduction Layer.

This module converts rich SimPy observables into MES-compatible data format
matching the structure of mes_data_with_kpis.csv. It extracts the subset
of information visible to a real MES system from comprehensive simulation events.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
from pathlib import Path
import logging

# Import centralized logging
try:
    from twin_model.logging_config import SimulationLogger

    logger = SimulationLogger.get_logger(__name__)
except ImportError:
    # Fallback to standard logging if logging_config not available
    logger = logging.getLogger(__name__)


class MESTransducer:
    """Converts SimPy observables to MES data format.

    The transducer extracts MES-visible events from the comprehensive
    observable stream and formats them into the standard MES structure.
    """

    def __init__(self, time_bucket: int = 5):
        """Initialize MES transducer.

        Args:
            time_bucket: Time bucket in minutes (default 5 for 5-minute intervals)

        """
        self.time_bucket = time_bucket
        self.mes_records: List[Dict[str, Any]] = []

        # Track equipment states for MES reporting
        self.equipment_states: Dict[str, Dict[str, Any]] = {}

        # Track production metrics per bucket
        self.bucket_metrics: Dict[Tuple[int, str], Dict[str, Any]] = defaultdict(
            lambda: {
                "good_units": 0,
                "scrap_units": 0,
                "downtime_minutes": 0,
                "runtime_minutes": 0,
                "energy_consumption": 0,
                "last_status": "Idle",
                "downtime_reason": None,
                "product_id": None,
                "product_name": None,
                "order_id": None,
            }
        )

    def process_observables(
        self,
        observables: List[Dict[str, Any]],
        manifests: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Process observables into MES format.

        Args:
            observables: List of observable events from simulation
            manifests: Optional manifests for product/equipment details

        Returns:
            DataFrame in MES format

        """
        # Sort observables by timestamp
        sorted_obs = sorted(observables, key=lambda x: x.get("timestamp", 0))

        # Process each observable
        for obs in sorted_obs:
            self._process_observable(obs, manifests)

        # Generate MES records from bucket metrics
        mes_data = self._generate_mes_records(manifests)

        # Convert to DataFrame
        if mes_data:
            df = pd.DataFrame(mes_data)
            # Sort by timestamp and equipment
            df = df.sort_values(["Timestamp", "LineID", "EquipmentID"])
            return df

        return pd.DataFrame()

    def _process_observable(self, obs: Dict[str, Any], manifests: Optional[Dict[str, Any]] = None) -> None:
        """Process single observable event.

        Args:
            obs: Observable event
            manifests: Optional manifests for context

        """
        event_type = obs.get("event_type")
        primitive_type = obs.get("primitive_type")
        primitive_id = obs.get("primitive_id")
        timestamp = obs.get("timestamp", 0)

        # Calculate time bucket
        bucket = int(timestamp // self.time_bucket)
        # bucket_key = (bucket, primitive_id)  # Not used in this method

        # Process equipment events (handle various equipment types)
        equipment_types = ["Equipment", "Filler", "Packer", "Palletizer"]
        if primitive_type in equipment_types or "Equipment" in str(primitive_type):
            self._process_equipment_event(obs, (bucket, primitive_id or ""), manifests)

        # Track order assignment
        elif event_type == "order_assigned":
            self._process_order_assignment(obs, (bucket, primitive_id or ""))

    def _process_equipment_event(
        self,
        obs: Dict[str, Any],
        bucket_key: Tuple[int, str],
        manifests: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Process equipment-specific events.

        Args:
            obs: Equipment observable
            bucket_key: Time bucket and equipment ID
            manifests: Optional manifests

        """
        event_type = obs.get("event_type")
        # equipment_id = obs.get('primitive_id')  # May be used for future enhancements

        # Track state changes
        if event_type == "state_change":
            new_state = obs.get("new_state")
            old_state = obs.get("old_state")
            duration = obs.get("duration_in_state", 0)

            # Update runtime/downtime (if duration not provided, use 1 minute default)
            if duration == 0:
                duration = 1

            if old_state == "RUNNING":
                self.bucket_metrics[bucket_key]["runtime_minutes"] += duration
            elif old_state in ["STOPPED_FAILURE", "STOPPED_MATERIAL", "CHANGEOVER"]:
                self.bucket_metrics[bucket_key]["downtime_minutes"] += duration

            # Track current state
            self.bucket_metrics[bucket_key]["last_status"] = self._map_state_to_mes(new_state or "")

            # Track downtime reason if stopped
            if new_state in ["STOPPED_FAILURE", "STOPPED_MATERIAL"]:
                self.bucket_metrics[bucket_key]["downtime_reason"] = obs.get("failure_mode", "UNP-OTH")
                self.bucket_metrics[bucket_key]["last_status"] = "Stopped"

        # Track production
        elif event_type == "unit_produced":
            self.bucket_metrics[bucket_key]["good_units"] += 1
            self.bucket_metrics[bucket_key]["product_id"] = obs.get("product_id")
            self.bucket_metrics[bucket_key]["product_name"] = self._get_product_name(
                obs.get("product_id") or "", manifests
            )

        elif event_type == "unit_scrapped":
            self.bucket_metrics[bucket_key]["scrap_units"] += 1

        # Track energy
        elif event_type == "energy_consumed":
            self.bucket_metrics[bucket_key]["energy_consumption"] += obs.get("amount", 0)

        # Track failures
        elif event_type == "equipment_failure":
            self.bucket_metrics[bucket_key]["downtime_reason"] = obs.get("failure_mode", "UNP-OTH")
            self.bucket_metrics[bucket_key]["last_status"] = "Stopped"

    def _process_order_assignment(self, obs: Dict[str, Any], bucket_key: Tuple[int, str]) -> None:
        """Process order assignment events.

        Args:
            obs: Order assignment observable
            bucket_key: Time bucket and equipment ID

        """
        order_id = obs.get("order_id")
        line_id = obs.get("line_id")

        # Track order for all equipment on line
        if line_id:
            # This would need line-equipment mapping from manifests
            self.bucket_metrics[bucket_key]["order_id"] = order_id

    def _generate_mes_records(self, manifests: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate MES records from bucket metrics.

        Args:
            manifests: Optional manifests for equipment details

        Returns:
            List of MES records

        """
        mes_records = []

        # Get equipment manifest if available
        equipment_data = {}
        if manifests and "equipment_manifest" in manifests:
            eq_manifest = manifests["equipment_manifest"]
            if eq_manifest and "equipment" in eq_manifest:
                equipment_data = eq_manifest["equipment"]

        # Get product manifest if available
        product_data = {}
        if manifests and "production_manifest" in manifests:
            prod_manifest = manifests["production_manifest"]
            if prod_manifest and "products" in prod_manifest:
                product_data = prod_manifest["products"]

        # Generate record for each bucket
        for (bucket, equipment_id), metrics in self.bucket_metrics.items():
            # FIX: Infer runtime when units are produced but no runtime recorded
            if (metrics["good_units"] > 0 or metrics["scrap_units"] > 0) and metrics["runtime_minutes"] == 0:
                logger.warning(
                    f"Inferring runtime from production for {equipment_id}",
                    extra={
                        "extra_data": {
                            "equipment_id": equipment_id,
                            "good_units": metrics["good_units"],
                            "scrap_units": metrics["scrap_units"],
                            "original_runtime": 0,
                            "inferred_runtime": self.time_bucket,
                            "bucket": bucket,
                        }
                    },
                )
                metrics["runtime_minutes"] = self.time_bucket
                metrics["last_status"] = "Running"

            # FIX: Correct status if production detected but status is Idle
            if metrics["good_units"] > 0 and metrics["last_status"] == "Idle":
                logger.warning(
                    f"Correcting status from Idle to Running for {equipment_id} due to production",
                    extra={
                        "extra_data": {
                            "equipment_id": equipment_id,
                            "good_units": metrics["good_units"],
                            "original_status": "Idle",
                            "corrected_status": "Running",
                        }
                    },
                )
                metrics["last_status"] = "Running"

            # Include all buckets with any state information
            if metrics["last_status"] == "Idle" and metrics["good_units"] == 0 and metrics["runtime_minutes"] == 0:
                continue  # Skip only if truly idle with no activity

            # Calculate timestamp
            timestamp = datetime(2025, 6, 1) + timedelta(minutes=bucket * self.time_bucket)

            # Get equipment details
            equipment_info = equipment_data.get(equipment_id, {})
            equipment_type = self._determine_equipment_type(equipment_id, equipment_info)
            line_id = self._extract_line_id(equipment_id, equipment_info)

            # Get product details
            product_id = metrics["product_id"] or "UNKNOWN"
            product_info = product_data.get(product_id, {})

            # Calculate KPIs
            availability = self._calculate_availability(metrics)
            performance = self._calculate_performance(metrics, equipment_info, product_info)
            quality = self._calculate_quality(metrics)
            oee = availability * performance * quality / 10000  # Convert from percentages

            # Create MES record
            record = {
                "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "ProductionOrderID": metrics["order_id"] or f"ORD-{1000 + bucket % 100}",
                "LineID": line_id,
                "EquipmentID": equipment_id,
                "EquipmentType": equipment_type,
                "ProductID": product_id,
                "ProductName": metrics["product_name"] or product_info.get("name", "Unknown Product"),
                "MachineStatus": metrics["last_status"],
                "DowntimeReason": metrics["downtime_reason"] if metrics["last_status"] == "Stopped" else "",
                "GoodUnitsProduced": metrics["good_units"],
                "ScrapUnitsProduced": metrics["scrap_units"],
                "TargetRate_units_per_5min": product_info.get("target_rate_units_per_5min", 350),
                "StandardCost_per_unit": product_info.get("standard_cost_per_unit", 0.45),
                "SalePrice_per_unit": product_info.get("sale_price_per_unit", 1.5),
                "Availability_Score": round(availability, 1),
                "Performance_Score": round(performance, 1),
                "Quality_Score": round(quality, 1),
                "OEE_Score": round(oee, 1),
                "Energy_Consumption_kWh": round(metrics["energy_consumption"], 3),
            }

            mes_records.append(record)

        return mes_records

    def _map_state_to_mes(self, state: str) -> str:
        """Map SimPy state to MES status.

        Args:
            state: SimPy equipment state

        Returns:
            MES machine status

        """
        state_mapping = {
            "RUNNING": "Running",
            "IDLE": "Idle",
            "STOPPED_FAILURE": "Stopped",
            "STOPPED_MATERIAL": "Stopped",
            "STARVED": "Stopped",
            "BLOCKED": "Stopped",
            "CHANGEOVER": "Changeover",
            "MAINTENANCE": "Maintenance",
        }
        return state_mapping.get(state, "Unknown")

    def _determine_equipment_type(self, equipment_id: str, equipment_info: Dict[str, Any]) -> str:
        """Determine equipment type from ID or manifest.

        Args:
            equipment_id: Equipment identifier
            equipment_info: Equipment manifest data

        Returns:
            Equipment type string

        """
        # Try manifest first
        if equipment_info and "type" in equipment_info:
            return str(equipment_info["type"])

        # Infer from ID
        if "FIL" in equipment_id:
            return "Filler"
        elif "PCK" in equipment_id:
            return "Packer"
        elif "PAL" in equipment_id:
            return "Palletizer"
        elif "BUF" in equipment_id:
            return "Buffer"

        return "Equipment"

    def _extract_line_id(self, equipment_id: str, equipment_info: Dict[str, Any]) -> str:
        """Extract line ID from equipment ID or manifest.

        Args:
            equipment_id: Equipment identifier
            equipment_info: Equipment manifest data

        Returns:
            Line ID

        """
        # Try manifest first
        if equipment_info and "line_id" in equipment_info:
            return str(equipment_info["line_id"])

        # Extract from ID (e.g., LINE1-FIL -> LINE1)
        if "LINE" in equipment_id:
            parts = equipment_id.split("-")
            if parts:
                return parts[0].replace("LINE", "")

        return "1"  # Default

    def _get_product_name(self, product_id: str, manifests: Optional[Dict[str, Any]] = None) -> str:
        """Get product name from manifests.

        Args:
            product_id: Product identifier
            manifests: Optional manifests

        Returns:
            Product name

        """
        if manifests and "production_manifest" in manifests:
            prod_manifest = manifests["production_manifest"]
            if prod_manifest and "products" in prod_manifest:
                products = prod_manifest["products"]
                if product_id in products:
                    return str(products[product_id].get("name", "Unknown Product"))

        # Default names
        default_names = {
            "SKU-1001": "12oz Sparkling Water",
            "SKU-1002": "16oz Energy Drink",
            "SKU-2001": "32oz Premium Juice",
            "SKU-2002": "64oz Family Juice",
            "SKU-3001": "8oz Kids Drink",
            "SKU-3002": "12oz Sports Drink",
        }

        return default_names.get(product_id, "Unknown Product")

    def _calculate_availability(self, metrics: Dict[str, Any]) -> float:
        """Calculate availability score.

        Args:
            metrics: Bucket metrics

        Returns:
            Availability percentage

        """
        total_time = self.time_bucket  # Total bucket time in minutes
        downtime = metrics["downtime_minutes"]

        if total_time > 0:
            availability = ((total_time - downtime) / total_time) * 100
            return float(min(100, max(0, availability)))

        return 0.0

    def _calculate_performance(
        self,
        metrics: Dict[str, Any],
        equipment_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ) -> float:
        """Calculate performance score with safety checks.

        Args:
            metrics: Bucket metrics
            equipment_info: Equipment manifest data
            product_info: Product manifest data

        Returns:
            Performance percentage

        """
        try:
            # Get target rate with fallback
            target_rate = product_info.get("target_rate_units_per_5min", 350)

            # Adjust for equipment-specific performance
            if equipment_info:
                base_rate = equipment_info.get("base_rate", 60) * self.time_bucket
                product_id = metrics["product_id"]
                perf_by_product = equipment_info.get("performance_by_product", {})

                if product_id in perf_by_product:
                    base_rate *= perf_by_product[product_id]

                target_rate = min(target_rate, base_rate)

            # Calculate actual production
            actual_units = metrics["good_units"] + metrics["scrap_units"]

            # Determine effective runtime
            effective_runtime = metrics["runtime_minutes"]
            if actual_units > 0 and effective_runtime == 0:
                # FIX: Units produced but no runtime recorded - use full bucket
                logger.debug(
                    "Using full bucket time for performance calculation",
                    extra={
                        "extra_data": {
                            "actual_units": actual_units,
                            "original_runtime": 0,
                            "effective_runtime": self.time_bucket,
                        }
                    },
                )
                effective_runtime = self.time_bucket

            # Calculate performance with safety checks
            if target_rate > 0 and effective_runtime > 0:
                # Adjust target for actual runtime
                adjusted_target = (target_rate * effective_runtime) / self.time_bucket
                performance = (actual_units / adjusted_target) * 100

                logger.debug(
                    "Performance calculated",
                    extra={
                        "extra_data": {
                            "actual_units": actual_units,
                            "adjusted_target": adjusted_target,
                            "performance": performance,
                            "runtime": effective_runtime,
                        }
                    },
                )

                return float(min(110, max(0, performance)))  # Cap at 110% for over-performance

            return 0.0

        except Exception as e:
            logger.error(
                "Performance calculation failed",
                extra={"extra_data": {"error": str(e), "metrics": metrics}},
                exc_info=True,
            )
            return 0.0

    def _calculate_quality(self, metrics: Dict[str, Any]) -> float:
        """Calculate quality score.

        Args:
            metrics: Bucket metrics

        Returns:
            Quality percentage

        """
        total_units = metrics["good_units"] + metrics["scrap_units"]

        if total_units > 0:
            quality = (metrics["good_units"] / total_units) * 100
            return float(min(100, max(0, quality)))

        return 0.0 if metrics["runtime_minutes"] == 0 else 100.0

    def save_to_csv(self, df: pd.DataFrame, filepath: Path) -> None:
        """Save MES data to CSV file.

        Args:
            df: MES DataFrame
            filepath: Output file path

        """
        df.to_csv(filepath, index=False)
        print(f"✓ MES data saved to {filepath}")

    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics from MES data.

        Args:
            df: MES DataFrame

        Returns:
            Dictionary of summary statistics

        """
        if df.empty:
            return {}

        # Overall metrics
        overall_oee = df["OEE_Score"].mean()
        overall_availability = df["Availability_Score"].mean()
        overall_performance = df["Performance_Score"].mean()
        overall_quality = df["Quality_Score"].mean()

        # Production metrics
        total_good_units = df["GoodUnitsProduced"].sum()
        total_scrap_units = df["ScrapUnitsProduced"].sum()
        scrap_rate = (
            total_scrap_units / (total_good_units + total_scrap_units)
            if (total_good_units + total_scrap_units) > 0
            else 0
        )

        # Downtime analysis
        downtime_records = df[df["MachineStatus"] == "Stopped"]
        downtime_reasons = (
            downtime_records["DowntimeReason"].value_counts().to_dict() if not downtime_records.empty else {}
        )

        # Line performance
        line_oee = df.groupby("LineID")["OEE_Score"].mean().to_dict()

        # Product performance
        product_quality = df.groupby("ProductID")["Quality_Score"].mean().to_dict()

        return {
            "overall_metrics": {
                "oee": round(overall_oee, 1),
                "availability": round(overall_availability, 1),
                "performance": round(overall_performance, 1),
                "quality": round(overall_quality, 1),
            },
            "production": {
                "total_good_units": int(total_good_units),
                "total_scrap_units": int(total_scrap_units),
                "scrap_rate": round(scrap_rate * 100, 2),
            },
            "downtime": {
                "total_stops": len(downtime_records),
                "reasons": downtime_reasons,
            },
            "line_performance": {k: round(v, 1) for k, v in line_oee.items()},
            "product_quality": {k: round(v, 1) for k, v in product_quality.items()},
        }
