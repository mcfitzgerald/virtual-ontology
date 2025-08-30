"""Monitor primitive for KPI tracking and aggregation.

This module provides a monitor primitive that tracks key performance indicators,
aggregates metrics across the system, and provides real-time visibility into
production performance.
"""

from typing import Dict, Any, List, Optional, Generator, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import simpy

from .base import BasePrimitive, PrimitiveConfig


class KPIType(str, Enum):
    """Types of KPIs tracked."""

    OEE = "OEE"
    AVAILABILITY = "AVAILABILITY"
    PERFORMANCE = "PERFORMANCE"
    QUALITY = "QUALITY"
    THROUGHPUT = "THROUGHPUT"
    CYCLE_TIME = "CYCLE_TIME"
    LEAD_TIME = "LEAD_TIME"
    SCRAP_RATE = "SCRAP_RATE"
    ENERGY_CONSUMPTION = "ENERGY_CONSUMPTION"
    MTBF = "MTBF"
    MTTR = "MTTR"
    UTILIZATION = "UTILIZATION"


@dataclass
class KPIMetric:
    """A KPI metric with history.

    Attributes:
        name: KPI name
        type: KPI type
        value: Current value
        target: Target value
        history: Historical values
        unit: Measurement unit
        aggregation: How to aggregate (avg, sum, max, min)

    """

    name: str
    type: KPIType
    value: float = 0.0
    target: Optional[float] = None
    history: List[Tuple[float, float]] = field(default_factory=list)  # (timestamp, value)
    unit: str = ""
    aggregation: str = "avg"

    def add_value(self, timestamp: float, value: float) -> None:
        """Add a value to history."""
        self.value = value
        self.history.append((timestamp, value))

        # Limit history size
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

    def get_average(self, window: Optional[float] = None, current_time: Optional[float] = None) -> float:
        """Get average value over time window."""
        if not self.history:
            return 0.0

        if window and current_time:
            recent = [(t, v) for t, v in self.history if t >= current_time - window]
            if recent:
                return statistics.mean([v for _, v in recent])

        return statistics.mean([v for _, v in self.history])

    def get_trend(self) -> str:
        """Get trend direction."""
        if len(self.history) < 2:
            return "stable"

        recent_avg = statistics.mean([v for _, v in self.history[-5:]])
        older_avg = (
            statistics.mean([v for _, v in self.history[-10:-5]]) if len(self.history) >= 10 else self.history[0][1]
        )

        if recent_avg > older_avg * 1.05:
            return "improving"
        elif recent_avg < older_avg * 0.95:
            return "declining"
        else:
            return "stable"


class MonitorPrimitive(BasePrimitive):
    """Monitor for tracking system-wide KPIs and metrics.

    Emits observables for:
    - KPI updates and trends
    - Target violations
    - Performance alerts
    - Aggregated metrics
    - Real-time dashboards
    """

    def __init__(self, env: simpy.Environment, config: PrimitiveConfig) -> None:
        """Initialize monitor with configuration.

        Args:
            env: SimPy environment
            config: Monitor configuration containing:
                - kpi_definitions: KPIs to track
                - update_interval: How often to update KPIs (minutes)
                - aggregation_window: Time window for aggregations
                - alert_thresholds: Thresholds for alerts
                - monitored_primitives: List of primitives to monitor

        """
        super().__init__(env, config)

        # Monitor parameters
        self.update_interval = config.get_property("update_interval", 5.0)
        self.aggregation_window = config.get_property("aggregation_window", 60.0)
        self.alert_thresholds = config.get_property("alert_thresholds", {})

        # KPI storage
        self.kpis: Dict[str, KPIMetric] = {}
        self._init_kpis()

        # Monitored primitives
        self.monitored_primitives: Dict[str, Any] = {}

        # Alert tracking
        self.active_alerts: List[Dict[str, Any]] = []
        self.alert_history: List[Dict[str, Any]] = []

        # Aggregated metrics
        self.line_metrics: Dict[str, Dict[str, float]] = {}
        self.product_metrics: Dict[str, Dict[str, float]] = {}
        self.shift_metrics: Dict[str, Dict[str, float]] = {}

    def _init_kpis(self) -> None:
        """Initialize KPI definitions from config."""
        kpi_defs = self.config.get_property("kpi_definitions", {})

        # Default KPIs if none specified
        if not kpi_defs:
            kpi_defs = {
                "overall_oee": {
                    "type": KPIType.OEE,
                    "target": 65.0,
                    "unit": "%",
                    "aggregation": "avg",
                },
                "throughput": {
                    "type": KPIType.THROUGHPUT,
                    "target": 50.0,
                    "unit": "units/min",
                    "aggregation": "avg",
                },
                "availability": {
                    "type": KPIType.AVAILABILITY,
                    "target": 90.0,
                    "unit": "%",
                    "aggregation": "avg",
                },
                "quality_rate": {
                    "type": KPIType.QUALITY,
                    "target": 98.0,
                    "unit": "%",
                    "aggregation": "avg",
                },
                "energy_consumption": {
                    "type": KPIType.ENERGY_CONSUMPTION,
                    "target": 100.0,
                    "unit": "kWh",
                    "aggregation": "sum",
                },
            }

        for name, definition in kpi_defs.items():
            self.kpis[name] = KPIMetric(
                name=name,
                type=KPIType(definition.get("type", KPIType.OEE)),
                target=definition.get("target"),
                unit=definition.get("unit", ""),
                aggregation=definition.get("aggregation", "avg"),
            )

    def start(self) -> None:
        """Start the monitoring process."""
        self.is_running = True
        self.process = self.env.process(self.monitor_process())
        self.env.process(self.alert_process())

        self.emit_observable(
            event_type="monitor_started",
            details={
                "kpis_tracked": list(self.kpis.keys()),
                "update_interval": self.update_interval,
                "aggregation_window": self.aggregation_window,
            },
        )

    def monitor_process(self) -> Generator:
        """Run monitoring process."""
        while self.is_running:
            # Wait for update interval
            yield self.env.timeout(self.update_interval)

            # Update all KPIs
            self._update_kpis()

            # Calculate aggregated metrics
            self._update_aggregations()

            # Check for threshold violations
            self._check_thresholds()

            # Emit monitoring update
            self.emit_observable(
                event_type="kpi_update",
                details={
                    "kpis": {
                        name: {
                            "value": kpi.value,
                            "target": kpi.target,
                            "trend": kpi.get_trend(),
                            "unit": kpi.unit,
                        }
                        for name, kpi in self.kpis.items()
                    },
                    "timestamp": self.env.now,
                },
            )

    def _update_kpis(self) -> None:
        """Update all KPI values from monitored primitives."""
        # Overall OEE calculation
        if "overall_oee" in self.kpis:
            oee_values = []
            for primitive in self.monitored_primitives.values():
                if hasattr(primitive, "calculate_oee"):
                    oee_values.append(primitive.calculate_oee())

            if oee_values:
                avg_oee = statistics.mean(oee_values)
                self.kpis["overall_oee"].add_value(self.env.now, avg_oee)

        # Throughput calculation
        if "throughput" in self.kpis:
            throughput_sum = 0
            for primitive in self.monitored_primitives.values():
                if hasattr(primitive, "units_produced"):
                    # Calculate rate over window
                    window_production = self._get_production_in_window(primitive)
                    throughput_sum += window_production / self.update_interval

            self.kpis["throughput"].add_value(self.env.now, throughput_sum)

        # Availability calculation
        if "availability" in self.kpis:
            availability_values = []
            for primitive in self.monitored_primitives.values():
                if hasattr(primitive, "state"):
                    availability = self._calculate_availability(primitive)
                    availability_values.append(availability)

            if availability_values:
                avg_availability = statistics.mean(availability_values)
                self.kpis["availability"].add_value(self.env.now, avg_availability)

        # Quality rate calculation
        if "quality_rate" in self.kpis:
            total_good = 0
            total_produced = 0

            for primitive in self.monitored_primitives.values():
                if hasattr(primitive, "units_produced") and hasattr(primitive, "units_scrapped"):
                    total_good += primitive.units_produced
                    total_produced += primitive.units_produced + primitive.units_scrapped

            if total_produced > 0:
                quality_rate = (total_good / total_produced) * 100
                self.kpis["quality_rate"].add_value(self.env.now, quality_rate)

        # Energy consumption
        if "energy_consumption" in self.kpis:
            total_energy = 0
            for primitive in self.monitored_primitives.values():
                if hasattr(primitive, "energy_consumed"):
                    total_energy += primitive.energy_consumed

            self.kpis["energy_consumption"].add_value(self.env.now, total_energy)

    def _get_production_in_window(self, primitive: Any) -> int:
        """Get production count in recent window.

        Args:
            primitive: Primitive to check

        Returns:
            Production count in window

        """
        if not hasattr(primitive, "observables"):
            return 0

        window_start = self.env.now - self.update_interval
        production_events = [
            o
            for o in primitive.observables
            if o.get("event_type") == "unit_produced" and o.get("timestamp", 0) >= window_start
        ]

        return len(production_events)

    def _calculate_availability(self, primitive: Any) -> float:
        """Calculate availability for a primitive.

        Args:
            primitive: Primitive to calculate for

        Returns:
            Availability percentage

        """
        if not hasattr(primitive, "observables"):
            return 0.0

        window_start = self.env.now - self.aggregation_window
        state_events = [
            o
            for o in primitive.observables
            if o.get("event_type") == "state_change" and o.get("timestamp", 0) >= window_start
        ]

        if not state_events:
            return 100.0  # Assume available if no state changes

        # Calculate time in running state
        running_time = 0
        last_time = window_start
        last_state = None

        for event in sorted(state_events, key=lambda x: x.get("timestamp", 0)):
            if last_state == "RUNNING":
                running_time += event["timestamp"] - last_time
            last_time = event["timestamp"]
            last_state = event.get("new_state")

        # Add time from last event to now
        if last_state == "RUNNING":
            running_time += self.env.now - last_time

        window_duration = self.env.now - window_start
        return (running_time / window_duration * 100) if window_duration > 0 else 0

    def _update_aggregations(self) -> None:
        """Update aggregated metrics by line, product, shift."""
        # Line aggregation
        for line_id, primitives in self._group_by_line().items():
            self.line_metrics[line_id] = {
                "oee": self._aggregate_oee(primitives),
                "throughput": self._aggregate_throughput(primitives),
                "availability": self._aggregate_availability(primitives),
            }

        # Product aggregation
        for product_id, primitives in self._group_by_product().items():
            self.product_metrics[product_id] = {
                "volume": self._aggregate_volume(primitives),
                "quality": self._aggregate_quality(primitives),
                "cycle_time": self._aggregate_cycle_time(primitives),
            }

        # Shift aggregation
        current_shift = self._get_current_shift()
        if current_shift:
            self.shift_metrics[current_shift] = {
                "oee": self.kpis["overall_oee"].value if "overall_oee" in self.kpis else 0.0,
                "throughput": self.kpis["throughput"].value if "throughput" in self.kpis else 0.0,
                "incidents": len(self.active_alerts),
            }

    def _group_by_line(self) -> Dict[str, List[Any]]:
        """Group monitored primitives by production line."""
        lines: Dict[str, List[Any]] = {}
        for name, primitive in self.monitored_primitives.items():
            if hasattr(primitive, "config"):
                line_id = primitive.config.properties.get("line_id", "DEFAULT")
                if line_id not in lines:
                    lines[line_id] = []
                lines[line_id].append(primitive)
        return lines

    def _group_by_product(self) -> Dict[str, List[Any]]:
        """Group monitored primitives by current product."""
        products: Dict[str, List[Any]] = {}
        for primitive in self.monitored_primitives.values():
            if hasattr(primitive, "current_product") and primitive.current_product:
                product_id = primitive.current_product
                if product_id not in products:
                    products[product_id] = []
                products[product_id].append(primitive)
        return products

    def _aggregate_oee(self, primitives: List[Any]) -> float:
        """Calculate aggregated OEE for a group of primitives."""
        oee_values = []
        for p in primitives:
            if hasattr(p, "calculate_oee"):
                oee_values.append(p.calculate_oee())
        return statistics.mean(oee_values) if oee_values else 0.0

    def _aggregate_throughput(self, primitives: List[Any]) -> float:
        """Calculate aggregated throughput for a group of primitives."""
        total = 0
        for p in primitives:
            total += self._get_production_in_window(p)
        return total / self.update_interval if self.update_interval > 0 else 0

    def _aggregate_availability(self, primitives: List[Any]) -> float:
        """Calculate aggregated availability for a group of primitives."""
        avail_values = []
        for p in primitives:
            avail_values.append(self._calculate_availability(p))
        return statistics.mean(avail_values) if avail_values else 0.0

    def _aggregate_volume(self, primitives: List[Any]) -> int:
        """Calculate total volume for a group of primitives."""
        total = 0
        for p in primitives:
            if hasattr(p, "units_produced"):
                total += p.units_produced
        return total

    def _aggregate_quality(self, primitives: List[Any]) -> float:
        """Calculate aggregated quality for a group of primitives."""
        total_good = 0
        total_all = 0
        for p in primitives:
            if hasattr(p, "units_produced") and hasattr(p, "units_scrapped"):
                total_good += p.units_produced
                total_all += p.units_produced + p.units_scrapped
        return (total_good / total_all * 100) if total_all > 0 else 0.0

    def _aggregate_cycle_time(self, primitives: List[Any]) -> float:
        """Calculate average cycle time for a group of primitives."""
        cycle_times = []
        for p in primitives:
            if hasattr(p, "observables"):
                production_events = [
                    o for o in p.observables if o.get("event_type") == "unit_produced" and "cycle_time" in o
                ]
                cycle_times.extend([e["cycle_time"] for e in production_events[-10:]])  # Last 10

        return statistics.mean(cycle_times) if cycle_times else 0.0

    def _get_current_shift(self) -> Optional[str]:
        """Determine current shift based on time."""
        hour = (self.env.now / 60) % 24  # Convert to hour of day

        if 6 <= hour < 14:
            return "shift1"
        elif 14 <= hour < 22:
            return "shift2"
        else:
            return "shift3"

    def _check_thresholds(self) -> None:
        """Check KPIs against configured thresholds."""
        for kpi_name, kpi in self.kpis.items():
            if kpi.target is not None:
                # Check if below target
                if kpi.value < kpi.target * 0.9:  # 10% below target
                    self._create_alert(
                        kpi_name=kpi_name,
                        severity="WARNING",
                        message=f"{kpi_name} below target: {kpi.value:.1f} < {kpi.target:.1f}",
                    )
                elif kpi.value < kpi.target * 0.8:  # 20% below target
                    self._create_alert(
                        kpi_name=kpi_name,
                        severity="ERROR",
                        message=f"{kpi_name} critically below target: {kpi.value:.1f} < {kpi.target:.1f}",
                    )

            # Check custom thresholds
            if kpi_name in self.alert_thresholds:
                threshold = self.alert_thresholds[kpi_name]
                if isinstance(threshold, dict):
                    if "min" in threshold and kpi.value < threshold["min"]:
                        self._create_alert(
                            kpi_name=kpi_name,
                            severity="ERROR",
                            message=f"{kpi_name} below minimum: {kpi.value:.1f}",
                        )
                    if "max" in threshold and kpi.value > threshold["max"]:
                        self._create_alert(
                            kpi_name=kpi_name,
                            severity="WARNING",
                            message=f"{kpi_name} above maximum: {kpi.value:.1f}",
                        )

    def _create_alert(self, kpi_name: str, severity: str, message: str) -> None:
        """Create an alert.

        Args:
            kpi_name: KPI that triggered alert
            severity: Alert severity
            message: Alert message

        """
        alert = {
            "timestamp": self.env.now,
            "kpi": kpi_name,
            "severity": severity,
            "message": message,
            "value": self.kpis[kpi_name].value if kpi_name in self.kpis else None,
        }

        # Check if already active
        existing = [a for a in self.active_alerts if a["kpi"] == kpi_name]
        if not existing:
            self.active_alerts.append(alert)
            self.alert_history.append(alert)

            self.emit_observable(event_type="alert_created", details=alert, severity=severity)

    def alert_process(self) -> Generator:
        """Process for managing alerts."""
        while self.is_running:
            # Check every minute
            yield self.env.timeout(1.0)

            # Clear resolved alerts
            for alert in self.active_alerts[:]:
                kpi = self.kpis.get(alert["kpi"])
                if kpi and kpi.target:
                    # Check if back to normal
                    if kpi.value >= kpi.target * 0.95:
                        self.active_alerts.remove(alert)

                        self.emit_observable(
                            event_type="alert_resolved",
                            details={
                                "kpi": alert["kpi"],
                                "duration": self.env.now - alert["timestamp"],
                            },
                        )

    def register_primitive(self, name: str, primitive: Any) -> None:
        """Register a primitive to monitor.

        Args:
            name: Primitive identifier
            primitive: Primitive instance

        """
        self.monitored_primitives[name] = primitive

        self.emit_observable(
            event_type="primitive_registered",
            details={
                "name": name,
                "type": primitive.__class__.__name__,
                "total_monitored": len(self.monitored_primitives),
            },
        )

    def get_kpi_value(self, kpi_name: str) -> Optional[float]:
        """Get current value of a KPI.

        Args:
            kpi_name: Name of KPI

        Returns:
            Current KPI value or None

        """
        if kpi_name in self.kpis:
            return self.kpis[kpi_name].value
        return None

    def get_kpi_history(self, kpi_name: str, window: Optional[float] = None) -> List[Tuple[float, float]]:
        """Get historical values of a KPI.

        Args:
            kpi_name: Name of KPI
            window: Time window to retrieve

        Returns:
            List of (timestamp, value) tuples

        """
        if kpi_name not in self.kpis:
            return []

        kpi = self.kpis[kpi_name]

        if window:
            cutoff = self.env.now - window
            return [(t, v) for t, v in kpi.history if t >= cutoff]

        return kpi.history

    def get_dashboard(self) -> Dict[str, Any]:
        """Get dashboard summary of all metrics.

        Returns:
            Dictionary with dashboard data

        """
        return {
            "timestamp": self.env.now,
            "kpis": {
                name: {
                    "value": kpi.value,
                    "target": kpi.target,
                    "trend": kpi.get_trend(),
                    "achievement": (kpi.value / kpi.target * 100) if kpi.target else None,
                }
                for name, kpi in self.kpis.items()
            },
            "line_metrics": dict(self.line_metrics),
            "product_metrics": dict(self.product_metrics),
            "shift_metrics": dict(self.shift_metrics),
            "active_alerts": len(self.active_alerts),
            "alert_list": self.active_alerts[:5],  # Top 5 alerts
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get monitor statistics.

        Returns:
            Dictionary of monitor metrics

        """
        return {
            "kpis_tracked": len(self.kpis),
            "primitives_monitored": len(self.monitored_primitives),
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alert_history),
            "lines_tracked": len(self.line_metrics),
            "products_tracked": len(self.product_metrics),
            "current_shift": self._get_current_shift(),
            "update_interval": self.update_interval,
        }
