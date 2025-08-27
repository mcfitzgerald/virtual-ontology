"""Control system for virtual twin.

This module provides the two-layer control system that maps
actionable controls (what plant managers change) to simulation
parameters (internal model behavior).
"""

from .control_manager import (
    ControlManager,
    ControlState,
    ControlDefinition,
    ParameterMapping,
    MappingFunction
)

__all__ = [
    'ControlManager',
    'ControlState',
    'ControlDefinition',
    'ParameterMapping',
    'MappingFunction'
]