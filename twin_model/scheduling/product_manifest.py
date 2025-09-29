"""Product manifest loader and manager.

This module provides comprehensive product information management
for production scheduling and cost optimization.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class PhysicalAttributes:
    """Physical characteristics of a product."""

    volume_ml: float
    volume_oz: float
    container_type: str
    container_weight_g: float
    fill_weight_g: float
    package_size: int  # Units per case
    pallet_size: int  # Cases per pallet
    case_dimensions_cm: List[float] = field(default_factory=list)
    gross_weight_kg: float = 0.0


@dataclass
class ProductionAttributes:
    """Production characteristics and rates."""

    nominal_rate_per_min: float
    target_rate_5min: float
    quality_rate: float
    scrap_rate: float
    efficiency_by_line: Dict[str, Optional[float]] = field(default_factory=dict)
    rework_possible: bool = False
    startup_waste_units: int = 0
    shutdown_waste_units: int = 0


@dataclass
class EconomicAttributes:
    """Economic and cost attributes."""

    material_cost: float
    packaging_cost: float
    labor_cost: float
    overhead_cost: float
    total_standard_cost: float
    sale_price: float
    wholesale_price: float
    margin_percentage: float
    contribution_margin: float
    holding_cost_per_day: float
    obsolescence_cost: float = 0.0


@dataclass
class ChangeoverAttributes:
    """Changeover requirements and costs."""

    group: str
    family: str
    cleaning_required_to: Dict[str, bool] = field(default_factory=dict)
    setup_time_minutes: Dict[str, float] = field(default_factory=dict)
    conversion_cost: Dict[str, float] = field(default_factory=dict)


@dataclass
class InventoryAttributes:
    """Inventory management parameters."""

    min_stock_units: int
    max_stock_units: int
    reorder_point: int
    reorder_quantity: int
    safety_stock: int
    shelf_life_days: int
    fifo_required: bool
    demand_pattern: str
    average_daily_demand: float
    demand_variability: float
    seasonal_factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class QualityAttributes:
    """Quality specifications and defect costs."""

    critical_parameters: List[str] = field(default_factory=list)
    specification_limits: Dict[str, List[float]] = field(default_factory=dict)
    defect_categories: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    inspection_time_seconds: float = 0.0
    sampling_rate: float = 0.01


@dataclass
class ProductConstraints:
    """Production constraints and requirements."""

    max_continuous_run_hours: float
    min_batch_size: int
    max_batch_size: int
    optimal_batch_size: int
    requires_quality_check_interval: int
    temperature_range_celsius: List[float] = field(default_factory=list)
    humidity_range_percent: List[float] = field(default_factory=list)
    requires_allergen_control: bool = False


@dataclass
class Product:
    """Complete product specification."""

    product_id: str
    name: str
    category: str
    family: str
    status: str
    physical: PhysicalAttributes
    production: ProductionAttributes
    economics: EconomicAttributes
    changeover: ChangeoverAttributes
    inventory: InventoryAttributes
    quality: QualityAttributes
    constraints: ProductConstraints
    line_compatibility: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ProductManifest:
    """Manages product specifications and relationships."""

    def __init__(self, manifest_path: Optional[Path] = None):
        """Initialize product manifest.

        Args:
            manifest_path: Path to product manifest YAML file
        """
        self.products: Dict[str, Product] = {}
        self.product_families: Dict[str, Dict[str, Any]] = {}
        self.changeover_matrix_overrides: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.cost_factors: Dict[str, float] = {}
        self.performance_targets: Dict[str, float] = {}

        if manifest_path and manifest_path.exists():
            self.load_from_yaml(manifest_path)

    def load_from_yaml(self, filepath: Path) -> None:
        """Load product manifest from YAML file.

        Args:
            filepath: Path to YAML file
        """
        with open(filepath) as f:
            data = yaml.safe_load(f)

        # Load products
        for product_id, product_data in data.get("products", {}).items():
            product = self._parse_product(product_id, product_data)
            self.products[product_id] = product

        # Load product families
        self.product_families = data.get("product_families", {})

        # Load changeover matrix overrides
        if "changeover_matrix" in data and "overrides" in data["changeover_matrix"]:
            self.changeover_matrix_overrides = data["changeover_matrix"]["overrides"]

        # Load cost factors
        self.cost_factors = data.get("cost_factors", {})

        # Load performance targets
        self.performance_targets = data.get("performance_targets", {})

        logger.info(f"Loaded {len(self.products)} products from {filepath}")

    def _parse_product(self, product_id: str, data: Dict[str, Any]) -> Product:
        """Parse product data from dictionary.

        Args:
            product_id: Product identifier
            data: Product data dictionary

        Returns:
            Product object
        """
        # Parse physical attributes
        physical_data = data.get("physical", {})
        physical = PhysicalAttributes(
            volume_ml=physical_data.get("volume_ml", 0),
            volume_oz=physical_data.get("volume_oz", 0),
            container_type=physical_data.get("container_type", ""),
            container_weight_g=physical_data.get("container_weight_g", 0),
            fill_weight_g=physical_data.get("fill_weight_g", 0),
            package_size=physical_data.get("package_size", 1),
            pallet_size=physical_data.get("pallet_size", 1),
            case_dimensions_cm=physical_data.get("case_dimensions_cm", []),
            gross_weight_kg=physical_data.get("gross_weight_kg", 0),
        )

        # Parse production attributes
        production_data = data.get("production", {})
        production = ProductionAttributes(
            nominal_rate_per_min=production_data.get("nominal_rate_per_min", 0),
            target_rate_5min=production_data.get("target_rate_5min", 0),
            quality_rate=production_data.get("quality_rate", 1.0),
            scrap_rate=production_data.get("scrap_rate", 0.0),
            efficiency_by_line=production_data.get("efficiency_by_line", {}),
            rework_possible=production_data.get("rework_possible", False),
            startup_waste_units=production_data.get("startup_waste_units", 0),
            shutdown_waste_units=production_data.get("shutdown_waste_units", 0),
        )

        # Parse economic attributes
        economics_data = data.get("economics", {})
        economics = EconomicAttributes(
            material_cost=economics_data.get("material_cost", 0),
            packaging_cost=economics_data.get("packaging_cost", 0),
            labor_cost=economics_data.get("labor_cost", 0),
            overhead_cost=economics_data.get("overhead_cost", 0),
            total_standard_cost=economics_data.get("total_standard_cost", 0),
            sale_price=economics_data.get("sale_price", 0),
            wholesale_price=economics_data.get("wholesale_price", 0),
            margin_percentage=economics_data.get("margin_percentage", 0),
            contribution_margin=economics_data.get("contribution_margin", 0),
            holding_cost_per_day=economics_data.get("holding_cost_per_day", 0),
            obsolescence_cost=economics_data.get("obsolescence_cost", 0),
        )

        # Parse changeover attributes
        changeover_data = data.get("changeover", {})
        changeover = ChangeoverAttributes(
            group=changeover_data.get("group", ""),
            family=changeover_data.get("family", ""),
            cleaning_required_to=changeover_data.get("cleaning_required_to", {}),
            setup_time_minutes=changeover_data.get("setup_time_minutes", {}),
            conversion_cost=changeover_data.get("conversion_cost", {}),
        )

        # Parse inventory attributes
        inventory_data = data.get("inventory", {})
        inventory = InventoryAttributes(
            min_stock_units=inventory_data.get("min_stock_units", 0),
            max_stock_units=inventory_data.get("max_stock_units", 0),
            reorder_point=inventory_data.get("reorder_point", 0),
            reorder_quantity=inventory_data.get("reorder_quantity", 0),
            safety_stock=inventory_data.get("safety_stock", 0),
            shelf_life_days=inventory_data.get("shelf_life_days", 365),
            fifo_required=inventory_data.get("fifo_required", True),
            demand_pattern=inventory_data.get("demand_pattern", "steady"),
            average_daily_demand=inventory_data.get("average_daily_demand", 0),
            demand_variability=inventory_data.get("demand_variability", 0),
            seasonal_factors=inventory_data.get("seasonal_factors", {}),
        )

        # Parse quality attributes
        quality_data = data.get("quality", {})
        quality = QualityAttributes(
            critical_parameters=quality_data.get("critical_parameters", []),
            specification_limits=quality_data.get("specification_limits", {}),
            defect_categories=quality_data.get("defect_categories", {}),
            inspection_time_seconds=quality_data.get("inspection_time_seconds", 0),
            sampling_rate=quality_data.get("sampling_rate", 0.01),
        )

        # Parse constraints
        constraints_data = data.get("constraints", {})
        constraints = ProductConstraints(
            max_continuous_run_hours=constraints_data.get("max_continuous_run_hours", 24),
            min_batch_size=constraints_data.get("min_batch_size", 1),
            max_batch_size=constraints_data.get("max_batch_size", 100000),
            optimal_batch_size=constraints_data.get("optimal_batch_size", 10000),
            requires_quality_check_interval=constraints_data.get("requires_quality_check_interval", 1000),
            temperature_range_celsius=constraints_data.get("temperature_range_celsius", [0, 40]),
            humidity_range_percent=constraints_data.get("humidity_range_percent", [0, 100]),
            requires_allergen_control=constraints_data.get("requires_allergen_control", False),
        )

        # Create product
        product = Product(
            product_id=product_id,
            name=data.get("name", product_id),
            category=data.get("category", ""),
            family=data.get("family", ""),
            status=data.get("status", "active"),
            physical=physical,
            production=production,
            economics=economics,
            changeover=changeover,
            inventory=inventory,
            quality=quality,
            constraints=constraints,
            line_compatibility=data.get("line_compatibility", {}),
        )

        return product

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID.

        Args:
            product_id: Product identifier

        Returns:
            Product object or None if not found
        """
        return self.products.get(product_id)

    def get_changeover_time(self, from_product_id: str, to_product_id: str) -> float:
        """Get changeover time between products.

        Args:
            from_product_id: Current product
            to_product_id: Next product

        Returns:
            Changeover time in minutes
        """
        if from_product_id == to_product_id:
            return 0.0

        # Check for specific override
        if (
            from_product_id in self.changeover_matrix_overrides
            and to_product_id in self.changeover_matrix_overrides[from_product_id]
        ):
            override = self.changeover_matrix_overrides[from_product_id][to_product_id]
            return override.get("time_minutes", 30)

        # Use product changeover attributes
        from_product = self.get_product(from_product_id)
        to_product = self.get_product(to_product_id)

        if not from_product or not to_product:
            return 30.0  # Default

        # Check if cleaning required
        to_category = to_product.category
        if from_product.changeover.cleaning_required_to.get(to_category, False):
            return from_product.changeover.setup_time_minutes.get("with_cleaning", 60)

        # Check family relationship
        if from_product.family == to_product.family:
            return from_product.changeover.setup_time_minutes.get("same_family", 15)
        elif from_product.changeover.group == to_product.changeover.group:
            return from_product.changeover.setup_time_minutes.get("same_group", 30)
        else:
            return from_product.changeover.setup_time_minutes.get("different_group", 45)

    def get_changeover_cost(self, from_product_id: str, to_product_id: str) -> float:
        """Get changeover cost between products.

        Args:
            from_product_id: Current product
            to_product_id: Next product

        Returns:
            Changeover cost in currency units
        """
        if from_product_id == to_product_id:
            return 0.0

        # Check for specific override
        if (
            from_product_id in self.changeover_matrix_overrides
            and to_product_id in self.changeover_matrix_overrides[from_product_id]
        ):
            override = self.changeover_matrix_overrides[from_product_id][to_product_id]
            return override.get("cost", 500)

        # Use product changeover attributes
        from_product = self.get_product(from_product_id)
        to_product = self.get_product(to_product_id)

        if not from_product or not to_product:
            return 500.0  # Default

        # Check if cleaning required
        to_category = to_product.category
        if from_product.changeover.cleaning_required_to.get(to_category, False):
            return from_product.changeover.conversion_cost.get("with_cleaning", 1000)

        # Check family relationship
        if from_product.family == to_product.family:
            return from_product.changeover.conversion_cost.get("same_family", 200)
        elif from_product.changeover.group == to_product.changeover.group:
            return from_product.changeover.conversion_cost.get("same_group", 400)
        else:
            return from_product.changeover.conversion_cost.get("different_group", 600)

    def get_line_efficiency(self, product_id: str, line_id: str) -> Optional[float]:
        """Get efficiency of product on specific line.

        Args:
            product_id: Product identifier
            line_id: Line identifier (e.g., "Line1", "1", etc.)

        Returns:
            Efficiency factor (0-1) or None if not capable
        """
        product = self.get_product(product_id)
        if not product:
            return None

        # Check line compatibility
        if line_id in product.line_compatibility:
            return product.line_compatibility[line_id].get("efficiency")

        # Check production attributes with original line_id
        efficiency = product.production.efficiency_by_line.get(line_id)
        if efficiency is not None:
            return efficiency

        # Handle Line1 -> 1, Line2 -> 2, etc. conversion
        if line_id.startswith("Line"):
            line_num = line_id.replace("Line", "")
            efficiency = product.production.efficiency_by_line.get(line_num)
            if efficiency is not None:
                return efficiency

        # Handle 1 -> Line1 conversion
        elif line_id.isdigit():
            line_name = f"Line{line_id}"
            # Check line_compatibility with converted name
            if line_name in product.line_compatibility:
                return product.line_compatibility[line_name].get("efficiency")
            # Check efficiency_by_line with converted name
            efficiency = product.production.efficiency_by_line.get(line_name)
            if efficiency is not None:
                return efficiency

        return None

    def is_product_capable_on_line(self, product_id: str, line_id: str) -> bool:
        """Check if product can be produced on line.

        Args:
            product_id: Product identifier
            line_id: Line identifier

        Returns:
            True if capable, False otherwise
        """
        efficiency = self.get_line_efficiency(product_id, line_id)
        return efficiency is not None and efficiency > 0

    def get_preferred_line(self, product_id: str) -> Optional[str]:
        """Get preferred production line for product.

        Args:
            product_id: Product identifier

        Returns:
            Preferred line ID or None
        """
        product = self.get_product(product_id)
        if not product:
            return None

        # Find preferred line
        for line_id, compatibility in product.line_compatibility.items():
            if compatibility.get("preferred", False):
                return line_id

        # Return line with highest efficiency
        best_line = None
        best_efficiency = 0.0

        for line_id, compatibility in product.line_compatibility.items():
            efficiency = compatibility.get("efficiency", 0)
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_line = line_id

        return best_line

    def get_product_family_members(self, family: str) -> List[str]:
        """Get all products in a family.

        Args:
            family: Family name

        Returns:
            List of product IDs in the family
        """
        if family in self.product_families:
            return self.product_families[family].get("products", [])

        # Search by product family attribute
        members = []
        for product_id, product in self.products.items():
            if product.family == family:
                members.append(product_id)

        return members

    def calculate_campaign_cost(
        self, product_id: str, volume: float, duration_hours: float, line_id: str
    ) -> Dict[str, float]:
        """Calculate total cost of a production campaign.

        Args:
            product_id: Product to produce
            volume: Production volume in units
            duration_hours: Campaign duration in hours
            line_id: Production line

        Returns:
            Dictionary of cost components
        """
        product = self.get_product(product_id)
        if not product:
            return {}

        costs = {}

        # Material costs
        costs["material"] = volume * product.economics.material_cost
        costs["packaging"] = volume * product.economics.packaging_cost

        # Labor costs
        labor_rate = self.cost_factors.get("labor_cost_per_hour", 25.0)
        costs["labor"] = duration_hours * labor_rate

        # Overhead costs
        costs["overhead"] = volume * product.economics.overhead_cost

        # Startup/shutdown waste
        waste_units = product.production.startup_waste_units + product.production.shutdown_waste_units
        costs["waste"] = waste_units * product.economics.total_standard_cost

        # Quality costs (inspection)
        inspection_cost = self.cost_factors.get("quality_inspection_cost_per_sample", 2.0)
        samples = volume * product.quality.sampling_rate
        costs["quality"] = samples * inspection_cost

        # Inventory holding costs
        avg_inventory = volume / 2  # Assume linear consumption
        holding_days = duration_hours / 24
        costs["holding"] = avg_inventory * product.economics.holding_cost_per_day * holding_days

        # Total
        costs["total"] = sum(costs.values())

        return costs

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of loaded products.

        Returns:
            Summary dictionary
        """
        summary: Dict[str, Any] = {
            "total_products": len(self.products),
            "products_by_category": {},
            "products_by_family": {},
            "active_products": 0,
            "average_margin": 0.0,
            "line_capabilities": {},
        }

        margins = []

        for product in self.products.values():
            # Count by category
            if product.category not in summary["products_by_category"]:
                summary["products_by_category"][product.category] = 0
            summary["products_by_category"][product.category] += 1

            # Count by family
            if product.family not in summary["products_by_family"]:
                summary["products_by_family"][product.family] = 0
            summary["products_by_family"][product.family] += 1

            # Count active
            if product.status == "active":
                summary["active_products"] += 1

            # Collect margins
            margins.append(product.economics.margin_percentage)

            # Track line capabilities
            for line_id, compatibility in product.line_compatibility.items():
                if line_id not in summary["line_capabilities"]:
                    summary["line_capabilities"][line_id] = {"capable_products": 0, "preferred_products": 0}

                if compatibility.get("capable", False):
                    summary["line_capabilities"][line_id]["capable_products"] += 1

                if compatibility.get("preferred", False):
                    summary["line_capabilities"][line_id]["preferred_products"] += 1

        # Calculate average margin
        if margins:
            summary["average_margin"] = sum(margins) / len(margins)

        return summary
