"""Ontology-driven virtual twin model.

This package provides an ontology-driven simulation framework for generating
synthetic MES (Manufacturing Execution System) data using SimPy discrete event
simulation with rich observables for pattern discovery.
"""

# Import primitives with their actual names
from .primitives import (
    BasePrimitive,
    PrimitiveConfig,
    EquipmentPrimitive as Equipment,
    EquipmentState,
    ProductionUnit,
    SourcePrimitive as Source,
    ArrivalPattern,
    SinkPrimitive as Sink,
    CollectedProduct,
    SchedulerPrimitive as Scheduler,
    ProductionOrder,
    Product,
    ProductCategory,
    MonitorPrimitive as Monitor,
    KPIType,
    KPIMetric,
)

# Import model builder
from .model_builder import OntologyDrivenModelBuilder

# Import transduction
from .transduction import MESTransducer

__version__ = "2.0.0"

__all__ = [
    # Core
    "BasePrimitive",
    "PrimitiveConfig",
    # Equipment
    "Equipment",
    "EquipmentState",
    "ProductionUnit",
    # Source
    "Source",
    "ArrivalPattern",
    # Sink
    "Sink",
    "CollectedProduct",
    # Scheduler
    "Scheduler",
    "ProductionOrder",
    "Product",
    "ProductCategory",
    # Monitor
    "Monitor",
    "KPIType",
    "KPIMetric",
    # Model Builder
    "OntologyDrivenModelBuilder",
    # Transduction
    "MESTransducer",
]
