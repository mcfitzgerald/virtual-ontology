"""Control manager for two-layer control system.

This module manages the mapping between actionable controls (what plant managers change)
and simulation parameters (internal model behavior). It loads mappings from the ontology
and applies transformations based on control values.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
import yaml
import numpy as np
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class MappingFunction(str, Enum):
    """Types of mapping functions supported."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    STEPPED = "stepped"
    POLYNOMIAL = "polynomial"
    SIGMOID = "sigmoid"


@dataclass
class ControlDefinition:
    """Definition of an actionable control."""

    name: str
    datatype: str
    bounds: List[float]
    default: float
    description: str
    options: Optional[List[str]] = None


@dataclass
class ParameterMapping:
    """Mapping from control to parameter."""

    control_name: str
    parameter_name: str
    function: MappingFunction
    config: Dict[str, Any]
    description: str


@dataclass
class ControlState:
    """Current state of all controls."""

    values: Dict[str, Any] = field(default_factory=dict)
    computed_parameters: Dict[str, float] = field(default_factory=dict)

    def get(self, control_name: str, default: Any = None) -> Any:
        """Get control value with default."""
        return self.values.get(control_name, default)

    def set(self, control_name: str, value: Any) -> None:
        """Set control value."""
        self.values[control_name] = value


class ControlManager:
    """Manages the two-layer control system.

    This class:
    1. Loads control definitions from ontology
    2. Loads control mappings from configuration
    3. Applies current control settings
    4. Computes simulation parameters from controls
    """

    def __init__(self, ontology_path: Path, mappings_path: Path, settings_path: Optional[Path] = None) -> None:
        """Initialize control manager.

        Args:
            ontology_path: Path to twin ontology with control definitions
            mappings_path: Path to control mappings configuration
            settings_path: Optional path to current control settings

        """
        self.ontology_path = ontology_path
        self.mappings_path = mappings_path
        self.settings_path = settings_path

        # Load configurations
        self.ontology = self._load_yaml(ontology_path)
        self.mappings_config = self._load_yaml(mappings_path)

        # Parse control definitions
        self.controls = self._parse_controls()
        self.mappings = self._parse_mappings()

        # Initialize state
        self.state = ControlState()

        # Load initial settings
        if settings_path:
            self.load_settings(settings_path)
        else:
            self._apply_defaults()

        # Compute initial parameters
        self.update_parameters()

        logger.info(f"Control manager initialized with {len(self.controls)} controls")

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML configuration file."""
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _parse_controls(self) -> Dict[str, ControlDefinition]:
        """Parse control definitions from ontology."""
        controls = {}

        control_system = self.ontology.get("control_system", {})
        actionable_controls = control_system.get("actionable_controls", {})

        for name, config in actionable_controls.items():
            controls[name] = ControlDefinition(
                name=name,
                datatype=config.get("datatype", "float"),
                bounds=config.get("bounds", [0, 1]),
                default=config.get("default", 0),
                description=config.get("description", ""),
                options=config.get("options"),
            )

        return controls

    def _parse_mappings(self) -> List[ParameterMapping]:
        """Parse control to parameter mappings."""
        mappings = []

        control_mappings = self.mappings_config.get("control_mappings", {})

        for control_name, control_effects in control_mappings.items():
            affects = control_effects.get("affects", {})

            for param_name, mapping_config in affects.items():
                mappings.append(
                    ParameterMapping(
                        control_name=control_name,
                        parameter_name=param_name,
                        function=MappingFunction(mapping_config.get("function", "linear")),
                        config=mapping_config,
                        description=mapping_config.get("description", ""),
                    )
                )

        return mappings

    def _apply_defaults(self) -> None:
        """Apply default control values."""
        for name, control in self.controls.items():
            self.state.set(name, control.default)

        logger.info("Applied default control values")

    def load_settings(self, path: Path) -> None:
        """Load control settings from file.

        Args:
            path: Path to control settings YAML

        """
        settings = self._load_yaml(path)
        controls = settings.get("controls", {})

        for name, value in controls.items():
            if name in self.controls:
                # Validate bounds
                control = self.controls[name]
                if control.datatype in ["float", "integer"]:
                    min_val, max_val = control.bounds
                    value = max(min_val, min(max_val, value))
                elif control.options and value not in control.options:
                    logger.warning(f"Invalid option '{value}' for {name}, using default")
                    value = control.default

                self.state.set(name, value)
            else:
                logger.warning(f"Unknown control '{name}' in settings")

        logger.info(f"Loaded control settings from {path}")

    def save_settings(self, path: Path) -> None:
        """Save current control settings to file.

        Args:
            path: Path to save settings

        """
        settings = {
            "metadata": {"name": "Control Settings Snapshot", "version": "1.0.0"},
            "controls": self.state.values,
            "computed_parameters": self.state.computed_parameters,
        }

        with open(path, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

        logger.info(f"Saved control settings to {path}")

    def get_control_value(self, name: str) -> Any:
        """Get current value of a control.

        Args:
            name: Control name

        Returns:
            Current control value

        """
        return self.state.get(name, self.controls[name].default if name in self.controls else None)

    def set_control_value(self, name: str, value: Any) -> None:
        """Set control value and recompute parameters.

        Args:
            name: Control name
            value: New value

        """
        if name not in self.controls:
            raise ValueError(f"Unknown control: {name}")

        # Validate and set
        control = self.controls[name]
        if control.datatype in ["float", "integer"]:
            min_val, max_val = control.bounds
            value = max(min_val, min(max_val, value))
        elif control.options and value not in control.options:
            raise ValueError(f"Invalid option '{value}' for {name}")

        self.state.set(name, value)
        self.update_parameters()

        logger.debug(f"Set {name} = {value}")

    def update_parameters(self) -> None:
        """Recompute all simulation parameters from current controls."""
        # Start with base parameter values
        params = {}
        param_config = self.mappings_config.get("simulation_parameters", {})

        for param_name, config in param_config.items():
            params[param_name] = config.get("base_value", 0)

        # Apply mappings
        for mapping in self.mappings:
            control_value = self.get_control_value(mapping.control_name)
            if control_value is None:
                continue

            param_value = self._apply_mapping(control_value, mapping)

            # Apply to parameter based on mapping type
            if mapping.parameter_name in params:
                base_value = params[mapping.parameter_name]

                # Determine if this is a multiplier or direct value
                # Multipliers are typically around 1.0 and modify base values
                if (
                    mapping.function in [MappingFunction.LINEAR, MappingFunction.EXPONENTIAL]
                    and mapping.config.get("base", 0) == 1.0
                ):
                    # This is likely a multiplier
                    params[mapping.parameter_name] = base_value * param_value
                elif mapping.function == MappingFunction.LOGARITHMIC:
                    # Logarithmic functions produce multipliers starting at 1.0
                    params[mapping.parameter_name] = base_value * param_value
                elif mapping.parameter_name in ["mtbf", "mttr", "changeover_duration"]:
                    # Time-based parameters typically use multipliers
                    if 0.5 <= param_value <= 2.0:
                        params[mapping.parameter_name] = base_value * param_value
                    else:
                        params[mapping.parameter_name] = param_value
                else:
                    # Direct value replacement
                    params[mapping.parameter_name] = param_value
            else:
                params[mapping.parameter_name] = param_value

        # Apply bounds
        params = self._apply_bounds(params)

        # Store computed parameters
        self.state.computed_parameters = params

        logger.debug(f"Updated {len(params)} parameters")

    def _apply_mapping(self, control_value: Any, mapping: ParameterMapping) -> float:
        """Apply a mapping function to transform control to parameter.

        Args:
            control_value: Current control value
            mapping: Mapping configuration

        Returns:
            Computed parameter value

        """
        function = mapping.function
        config = mapping.config

        if function == MappingFunction.LINEAR:
            base = config.get("base", 0)
            coefficient = config.get("coefficient", 1)
            reference = config.get("reference_point", 0)
            value = base + coefficient * (control_value - reference)

        elif function == MappingFunction.EXPONENTIAL:
            base = config.get("base", 1)
            coefficient = config.get("coefficient", 0.1)
            reference = config.get("reference_point", 0)
            value = base * np.exp(coefficient * (control_value - reference))

        elif function == MappingFunction.LOGARITHMIC:
            base = config.get("base", 1)
            coefficient = config.get("coefficient", 0.1)
            # For multipliers, we want log to start at 1.0, not 0
            # So we add 1 to make it: 1 + base * log(1 + coefficient * control_value)
            if base == 1.0:
                # This is a multiplier, start at 1.0
                value = 1.0 + np.log(1 + coefficient * control_value)
            else:
                # Direct logarithmic scaling
                value = base * np.log(1 + coefficient * control_value)

        elif function == MappingFunction.STEPPED:
            thresholds = config.get("thresholds", [])
            values = config.get("values", [])

            # Find appropriate value
            value = values[0] if values else 1.0
            for i, threshold in enumerate(thresholds):
                if (isinstance(threshold, (int, float)) and control_value >= threshold) or (
                    isinstance(threshold, str) and control_value == threshold
                ):
                    if i < len(values):
                        value = values[i]

        elif function == MappingFunction.POLYNOMIAL:
            coefficients = config.get("coefficients", [1])
            reference = config.get("reference_point", 0)
            x = control_value - reference
            value = sum(c * (x**i) for i, c in enumerate(coefficients))

        elif function == MappingFunction.SIGMOID:
            max_val = config.get("max", 1)
            steepness = config.get("steepness", 0.1)
            midpoint = config.get("midpoint", 0)
            value = max_val / (1 + np.exp(-steepness * (control_value - midpoint)))

        else:
            logger.warning(f"Unknown mapping function: {function}")
            value = control_value

        # Apply min/max if specified
        if "min" in config:
            value = max(config["min"], value)
        if "max" in config:
            value = min(config["max"], value)

        return value

    def _apply_bounds(self, params: Dict[str, float]) -> Dict[str, float]:
        """Apply parameter bounds from configuration.

        Args:
            params: Computed parameters

        Returns:
            Bounded parameters

        """
        bounds = self.mappings_config.get("parameter_bounds", {})

        for param_name, param_value in params.items():
            if param_name in bounds:
                bound_config = bounds[param_name]
                if "min" in bound_config:
                    param_value = max(bound_config["min"], param_value)
                if "max" in bound_config:
                    param_value = min(bound_config["max"], param_value)
                params[param_name] = param_value

        return params

    def get_parameter(self, name: str, default: float = 0) -> float:
        """Get computed simulation parameter.

        Args:
            name: Parameter name
            default: Default value if not found

        Returns:
            Parameter value

        """
        return self.state.computed_parameters.get(name, default)

    def get_all_parameters(self) -> Dict[str, float]:
        """Get all computed parameters.

        Returns:
            Dictionary of parameter values

        """
        return self.state.computed_parameters.copy()

    def get_scenario(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Get predefined scenario configuration.

        Args:
            scenario_name: Name of scenario

        Returns:
            Scenario configuration or None

        """
        # Try to load from system config
        if self.settings_path:
            config_dir = self.settings_path.parent
            system_config_path = config_dir / "system_config.yaml"
            if system_config_path.exists():
                system_config = self._load_yaml(system_config_path)
                scenarios = system_config.get("scenarios", {})
                return scenarios.get(scenario_name)

        return None

    def apply_scenario(self, scenario_name: str) -> bool:
        """Apply a predefined scenario.

        Args:
            scenario_name: Name of scenario to apply

        Returns:
            True if scenario was applied

        """
        scenario = self.get_scenario(scenario_name)
        if not scenario:
            logger.warning(f"Scenario '{scenario_name}' not found")
            return False

        controls = scenario.get("controls", {})
        for name, value in controls.items():
            if name in self.controls:
                self.set_control_value(name, value)

        logger.info(f"Applied scenario '{scenario_name}'")
        return True

    def describe_control(self, name: str) -> str:
        """Get human-readable description of a control.

        Args:
            name: Control name

        Returns:
            Description string

        """
        if name not in self.controls:
            return f"Unknown control: {name}"

        control = self.controls[name]
        current = self.get_control_value(name)

        desc = f"{name}: {control.description}\n"
        desc += f"  Current value: {current}\n"
        desc += f"  Bounds: {control.bounds}\n"

        if control.options:
            desc += f"  Options: {control.options}\n"

        # Show affected parameters
        affected = [m.parameter_name for m in self.mappings if m.control_name == name]
        if affected:
            desc += f"  Affects: {', '.join(affected)}\n"

        return desc

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for control improvements.

        Returns:
            List of recommendations with expected impact

        """
        recommendations = []

        # Compare current to optimal values
        for name, control in self.controls.items():
            current = self.get_control_value(name)

            # Simple heuristics for recommendations
            if name == "line_speed_setting" and current > 85:
                recommendations.append(
                    {
                        "control": name,
                        "current": current,
                        "recommended": 85,
                        "reason": "Reduce speed to improve quality",
                        "expected_impact": "+3% quality",
                    }
                )

            if name == "operator_training_hours" and current < 20:
                recommendations.append(
                    {
                        "control": name,
                        "current": current,
                        "recommended": 20,
                        "reason": "Increase training for better performance",
                        "expected_impact": "+5% OEE",
                    }
                )

            if name == "pm_schedule_compliance" and current < 80:
                recommendations.append(
                    {
                        "control": name,
                        "current": current,
                        "recommended": 80,
                        "reason": "Improve PM compliance to reduce failures",
                        "expected_impact": "+10% availability",
                    }
                )

        return recommendations
