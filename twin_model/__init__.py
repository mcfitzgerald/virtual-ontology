"""Twin Model - Container-based continuous flow simulation framework."""

from .model_builder import FlowModelBuilder
from .primitives import (
    BaseFlowPrimitive,
    EquipmentFlow,
    FailureParameters,
    FlowCapacity,
    FlowMetrics,
    FlowState,
    OEEMetrics,
    ProcessingParameters,
    ProductionOrder,
    ProductionWindow,
    SinkFlow,
    SourceFlow,
)

__version__ = "1.0.0"

__all__ = [
    # Model builder
    "FlowModelBuilder",
    # Base classes
    "BaseFlowPrimitive",
    "FlowCapacity",
    "FlowState",
    "FlowMetrics",
    # Equipment
    "EquipmentFlow",
    "ProcessingParameters",
    "FailureParameters",
    # Source
    "SourceFlow",
    "ProductionOrder",
    # Sink
    "SinkFlow",
    "ProductionWindow",
    "OEEMetrics",
]
