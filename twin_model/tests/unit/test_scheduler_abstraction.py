"""Unit tests for scheduler abstraction.

Tests the BaseScheduler abstract class and ProductionScheduler
implementation with configurable behavior.
"""

import tempfile
from pathlib import Path

import simpy
import yaml

from twin_model.scheduling import ProductionOrder, ProductionScheduler, SchedulerConfig, SchedulingConstraints
from twin_model.scheduling.config_loader import (
    create_scheduler_from_config,
    load_scheduler_config,
    load_scheduling_constraints,
    validate_schedule_config,
)


class TestSchedulerConfig:
    """Test scheduler configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SchedulerConfig()

        assert config.min_order_duration_hours == 2.0
        assert config.max_order_duration_hours == 8.0
        assert config.efficiency_factor == 0.7
        assert config.min_priority == 1
        assert config.max_priority == 10
        assert config.same_family_changeover_minutes == 15.0
        assert config.different_family_changeover_minutes == 30.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = SchedulerConfig(
            min_order_duration_hours=1.0,
            max_order_duration_hours=12.0,
            efficiency_factor=0.85,
            same_family_changeover_minutes=10.0,
        )

        assert config.min_order_duration_hours == 1.0
        assert config.max_order_duration_hours == 12.0
        assert config.efficiency_factor == 0.85
        assert config.same_family_changeover_minutes == 10.0


class TestSchedulingConstraints:
    """Test scheduling constraints."""

    def test_empty_constraints(self):
        """Test empty constraints."""
        constraints = SchedulingConstraints()

        assert constraints.horizon_hours is None
        assert constraints.maintenance_windows is None
        assert constraints.product_line_compatibility is None
        assert constraints.forbidden_sequences is None

    def test_constraints_with_values(self):
        """Test constraints with specific values."""
        constraints = SchedulingConstraints(
            horizon_hours=168.0,
            maintenance_windows=[(0, 60), (240, 300)],
            product_line_compatibility={"P1": ["L1", "L2"], "P2": ["L2", "L3"]},
            forbidden_sequences=[("P1", "P2")],
            min_campaign_length=2.0,
            max_campaign_length=24.0,
        )

        assert constraints.horizon_hours == 168.0
        assert len(constraints.maintenance_windows) == 2
        assert "P1" in constraints.product_line_compatibility
        assert ("P1", "P2") in constraints.forbidden_sequences
        assert constraints.min_campaign_length == 2.0
        assert constraints.max_campaign_length == 24.0


class TestProductionScheduler:
    """Test ProductionScheduler implementation."""

    def setup_method(self):
        """Set up test environment."""
        self.env = simpy.Environment()
        self.config = SchedulerConfig(min_order_duration_hours=2.0, max_order_duration_hours=4.0, efficiency_factor=0.8)
        self.constraints = SchedulingConstraints(
            product_line_compatibility={"SKU-1001": ["1", "2"], "SKU-2001": ["2", "3"], "SKU-3001": ["3"]}
        )

    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        scheduler = ProductionScheduler(env=self.env, config=self.config, constraints=self.constraints, random_seed=42)

        assert scheduler.env == self.env
        assert scheduler.config == self.config
        assert scheduler.constraints == self.constraints
        assert len(scheduler.product_catalog) > 0

    def test_generate_schedule(self):
        """Test schedule generation."""
        scheduler = ProductionScheduler(env=self.env, config=self.config, constraints=self.constraints, random_seed=42)

        # Generate schedule
        lines = ["1", "2", "3"]
        products = ["SKU-1001", "SKU-2001", "SKU-3001"]
        duration = 480.0  # 8 hours

        schedule = scheduler.generate_schedule(lines=lines, products=products, duration=duration)

        # Verify schedule structure
        assert isinstance(schedule, dict)
        assert all(line in schedule for line in lines)

        # Verify orders
        for line_id, orders in schedule.items():
            assert isinstance(orders, list)
            for order in orders:
                assert isinstance(order, ProductionOrder)
                assert order.line_id == line_id
                assert order.product_id in products

    def test_optimize_schedule_minimize_changeover(self):
        """Test schedule optimization for changeover minimization."""
        scheduler = ProductionScheduler(env=self.env, config=self.config, constraints=self.constraints, random_seed=42)

        # Create a simple schedule with mixed products
        orders = [
            ProductionOrder(
                order_id="O1",
                product_id="SKU-1001",
                product_name="Product 1",
                target_volume=100,
                line_id="1",
                scheduled_start=0,
                scheduled_duration=60,
            ),
            ProductionOrder(
                order_id="O2",
                product_id="SKU-2001",
                product_name="Product 2",
                target_volume=100,
                line_id="1",
                scheduled_start=60,
                scheduled_duration=60,
            ),
            ProductionOrder(
                order_id="O3",
                product_id="SKU-1001",
                product_name="Product 1",
                target_volume=100,
                line_id="1",
                scheduled_start=120,
                scheduled_duration=60,
            ),
        ]

        current_schedule = {"1": orders}

        # Optimize schedule
        optimized = scheduler.optimize_schedule(current_schedule, objective="minimize_changeover")

        # Should group same products together
        assert len(optimized["1"]) == 3
        # First two orders should be same product
        products = [o.product_id for o in optimized["1"]]
        assert products[0] == products[1] or products[1] == products[2]

    def test_reschedule_after_disruption(self):
        """Test rescheduling after a disruption."""
        scheduler = ProductionScheduler(env=self.env, config=self.config, constraints=self.constraints, random_seed=42)

        # Generate initial schedule
        scheduler.generate_schedule(lines=["1"], products=["SKU-1001"], duration=240.0)

        # Simulate disruption at 60 minutes
        rescheduled = scheduler.reschedule(
            disruption_time=60.0, disruption_type="equipment_failure", affected_resources=["1"], duration=30.0
        )

        # Verify orders are delayed
        assert "1" in rescheduled
        for order in rescheduled["1"]:
            if order.scheduled_start >= 60:
                # Orders after disruption should be delayed
                assert order.scheduled_start >= 90  # 60 + 30 delay

    def test_schedule_validation(self):
        """Test schedule validation against constraints."""
        scheduler = ProductionScheduler(env=self.env, config=self.config, constraints=self.constraints, random_seed=42)

        # Create a schedule that violates constraints
        invalid_order = ProductionOrder(
            order_id="O1",
            product_id="SKU-3001",  # Only allowed on line 3
            product_name="Product 3",
            target_volume=100,
            line_id="1",  # Wrong line!
            scheduled_start=0,
            scheduled_duration=60,
        )

        invalid_schedule = {"1": [invalid_order]}

        # Validate schedule
        is_valid, violations = scheduler.validate_schedule(invalid_schedule)

        assert not is_valid
        assert len(violations) > 0
        assert any("not allowed on line" in v for v in violations)

    def test_schedule_metrics(self):
        """Test calculation of schedule metrics."""
        scheduler = ProductionScheduler(env=self.env, config=self.config, constraints=self.constraints, random_seed=42)

        # Generate schedule
        schedule = scheduler.generate_schedule(lines=["1", "2"], products=["SKU-1001", "SKU-2001"], duration=480.0)

        # Calculate metrics
        metrics = scheduler.calculate_metrics(schedule)

        assert "total_orders" in metrics
        assert "total_production_time" in metrics
        assert "line_utilization" in metrics
        assert "product_volumes" in metrics
        assert metrics["total_orders"] > 0
        assert all(u >= 0 for u in metrics["line_utilization"].values())


class TestConfigLoader:
    """Test configuration loading utilities."""

    def test_load_config_from_yaml(self):
        """Test loading configuration from YAML file."""
        # Create temporary YAML file
        config_data = {
            "scheduler_config": {
                "min_order_duration_hours": 3.0,
                "max_order_duration_hours": 10.0,
                "efficiency_factor": 0.75,
                "same_family_changeover_minutes": 20.0,
            },
            "scheduling_constraints": {
                "horizon_hours": 168,
                "maintenance_windows": [{"start_hour": 24, "duration_hours": 2}],
                "product_line_compatibility": {"P1": ["1", "2"]},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            # Load configuration
            config = load_scheduler_config(temp_path)
            constraints = load_scheduling_constraints(temp_path)

            # Verify loaded values
            assert config.min_order_duration_hours == 3.0
            assert config.max_order_duration_hours == 10.0
            assert config.efficiency_factor == 0.75
            assert config.same_family_changeover_minutes == 20.0

            assert constraints.horizon_hours == 168
            assert len(constraints.maintenance_windows) == 1
            assert "P1" in constraints.product_line_compatibility

        finally:
            temp_path.unlink()

    def test_validate_config(self):
        """Test configuration validation."""
        # Create invalid configuration
        invalid_config = {
            "scheduler_config": {
                "min_order_duration_hours": 10.0,  # Min > Max!
                "max_order_duration_hours": 5.0,
                "efficiency_factor": 1.5,  # > 1!
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(invalid_config, f)
            temp_path = Path(f.name)

        try:
            warnings = validate_schedule_config(temp_path)

            assert len(warnings) > 0
            assert any("min_order_duration_hours" in w for w in warnings)
            assert any("efficiency_factor" in w for w in warnings)

        finally:
            temp_path.unlink()

    def test_create_scheduler_from_config(self):
        """Test creating scheduler from configuration file."""
        env = simpy.Environment()

        # Test with default config (no file)
        scheduler = create_scheduler_from_config(env=env, random_seed=42)

        assert isinstance(scheduler, ProductionScheduler)
        assert scheduler.config.efficiency_factor == 0.7  # Default value
