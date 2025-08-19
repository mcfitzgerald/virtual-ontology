"""SimPy Primitives Framework for Ontology-Driven Virtual Twin.

This module provides generic building blocks (primitives) that compose into
complex manufacturing systems. Primitives emit rich observables for
discovery-based learning without prescriptive mappings.
"""

from .base import BasePrimitive, PrimitiveConfig
from .equipment import EquipmentPrimitive, EquipmentState
from .buffer import BufferPrimitive, BufferItem
from .source import SourcePrimitive, ArrivalPattern
from .sink import SinkPrimitive, CollectedProduct
from .scheduler import (
    SchedulerPrimitive,
    ScheduleEvent,
    ScheduleEventType,
    ProductionOrder,
)
from .monitor import MonitorPrimitive, KPIType, KPIMetric

__all__ = [
    "BasePrimitive",
    "PrimitiveConfig",
    "EquipmentPrimitive",
    "EquipmentState",
    "BufferPrimitive",
    "BufferItem",
    "SourcePrimitive",
    "ArrivalPattern",
    "SinkPrimitive",
    "CollectedProduct",
    "SchedulerPrimitive",
    "ScheduleEvent",
    "ScheduleEventType",
    "ProductionOrder",
    "MonitorPrimitive",
    "KPIType",
    "KPIMetric",
]
