"""SimPy Primitives Framework for Ontology-Driven Virtual Twin.

This module provides generic building blocks (primitives) that compose into
complex manufacturing systems. Primitives emit rich observables for
discovery-based learning without prescriptive mappings.
"""

from .base import BasePrimitive, PrimitiveConfig, SamplingConfig, SimulationMode
from .equipment import EquipmentPrimitiveV2 as EquipmentPrimitive, EquipmentState
from .buffer import BufferPrimitive, BufferItem
from .source import SourcePrimitiveV2 as SourcePrimitive, ArrivalPattern
from .sink import SinkPrimitiveV2 as SinkPrimitive, CollectedProduct
from .scheduler import (
    SchedulerPrimitiveV2 as SchedulerPrimitive,
    ProductionOrder,
    Product,
    ProductCategory,
)
from .monitor import MonitorPrimitive, KPIType, KPIMetric

__all__ = [
    "BasePrimitive",
    "PrimitiveConfig",
    "SamplingConfig",
    "SimulationMode",
    "EquipmentPrimitive",
    "EquipmentState",
    "BufferPrimitive",
    "BufferItem",
    "SourcePrimitive",
    "ArrivalPattern",
    "SinkPrimitive",
    "CollectedProduct",
    "SchedulerPrimitive",
    "ProductionOrder",
    "Product",
    "ProductCategory",
    "MonitorPrimitive",
    "KPIType",
    "KPIMetric",
]
