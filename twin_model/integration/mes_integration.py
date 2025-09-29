"""Integration module for MES simulation components.

This module provides integration between the production scheduler,
MES data collector, and simulation primitives.
"""

import logging
from typing import Any, Dict, List, Optional

import simpy

from twin_model.primitives.base_flow import BaseFlowPrimitive
from twin_model.primitives.source_flow import ProductionOrder as SourceOrder
from twin_model.primitives.source_flow import SourceFlow
from twin_model.scheduling.production_scheduler import ProductionScheduler
from twin_model.transduction.mes_collector import MESDataCollector

logger = logging.getLogger(__name__)


class MESSimulationCoordinator:
    """Coordinates MES simulation components.

    This coordinator manages the interaction between:
    - Production scheduler (manages orders)
    - MES data collector (captures data)
    - Equipment primitives (execute production)
    """

    def __init__(
        self,
        env: simpy.Environment,
        scheduler: ProductionScheduler,
        collector: MESDataCollector,
        primitives: Dict[str, BaseFlowPrimitive],
        lines: Dict[str, List[str]],
    ):
        """Initialize MES simulation coordinator.

        Args:
            env: SimPy environment
            scheduler: Production scheduler
            collector: MES data collector
            primitives: Dictionary of equipment primitives
            lines: Dictionary mapping line IDs to equipment IDs
        """
        self.env = env
        self.scheduler = scheduler
        self.collector = collector
        self.primitives = primitives
        self.lines = lines

        # Track sources for each line
        self.line_sources: Dict[str, SourceFlow] = {}
        self._identify_sources()

        # Start coordination process
        self.process = env.process(self.coordinate())

    def _identify_sources(self):
        """Identify source primitives for each line."""
        for line_id, equipment_ids in self.lines.items():
            for equip_id in equipment_ids:
                if equip_id.endswith("-SOURCE"):
                    primitive = self.primitives.get(equip_id)
                    if isinstance(primitive, SourceFlow):
                        self.line_sources[line_id] = primitive
                        logger.debug(f"Found source {equip_id} for line {line_id}")

    def coordinate(self):
        """Main coordination process."""
        logger.info("Starting MES simulation coordination")

        # Update interval (5 minutes)
        update_interval = 5.0

        while True:
            # Update production orders for each line
            for line_id, source in self.line_sources.items():
                self._update_line_production(line_id, source)

            # Update MES collector with current production info
            self._update_collector_production()

            # Wait for next update
            yield self.env.timeout(update_interval)

    def _update_line_production(self, line_id: str, source: SourceFlow):
        """Update production for a line.

        Args:
            line_id: Production line ID
            source: Source primitive for the line
        """
        # Get current order from scheduler
        current_order = self.scheduler.get_current_order(line_id)

        if current_order and current_order.status == self.scheduler.OrderStatus.IN_PROGRESS:
            # Check if source needs a new order
            if source.continuous_mode:
                # In continuous mode, just update the product
                source.default_product = current_order.product_id
            else:
                # In order mode, check if we need to add order to queue
                if not source.current_order or source.current_order.order_id != current_order.order_id:
                    # Convert scheduler order to source order
                    source_order = SourceOrder(
                        order_id=current_order.order_id,
                        product_id=current_order.product_id,
                        target_volume=current_order.target_volume,
                        due_time=current_order.scheduled_start + current_order.scheduled_duration,
                        priority=current_order.priority,
                    )
                    source.add_order(source_order)
                    logger.debug(f"Added order {current_order.order_id} to line {line_id} source")

            # Update all equipment on the line with current production info
            for equip_id in self.lines[line_id]:
                self.collector.update_production_order(equip_id, current_order.order_id, current_order.product_id)

    def _update_collector_production(self):
        """Update MES collector with production information."""
        # Collect production metrics from sources
        for line_id, source in self.line_sources.items():
            current_order = self.scheduler.get_current_order(line_id)

            if current_order:
                # Get production volumes from the source
                if source.current_order:
                    good_units = source.current_order.completed_volume
                    # Estimate scrap based on quality rate
                    scrap_rate = 0.068  # 6.8% from target
                    scrap_units = good_units * scrap_rate

                    # Update scheduler with progress
                    self.scheduler.update_order_progress(current_order.order_id, good_units, scrap_units)


def setup_mes_simulation(
    env: simpy.Environment, model: Dict[str, Any], simulation_duration: float, random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """Set up complete MES simulation.

    Args:
        env: SimPy environment
        model: Model dictionary from OntologyModelBuilder
        simulation_duration: Total simulation duration in minutes
        random_seed: Random seed for reproducibility

    Returns:
        Dictionary with scheduler, collector, and coordinator
    """
    # Extract primitives and lines from model
    primitives = model["primitives"]
    lines = model["lines"]

    # Create production scheduler
    scheduler = ProductionScheduler(env, random_seed=random_seed)
    scheduler.generate_initial_schedule(simulation_duration)

    # Create MES data collector
    collector = MESDataCollector(env, interval_minutes=5.0)

    # Register all equipment with collector
    for equip_id, primitive in primitives.items():
        # Determine equipment type from ID
        if "FIL" in equip_id:
            equip_type = "Filler"
        elif "PCK" in equip_id:
            equip_type = "Packer"
        elif "PAL" in equip_id:
            equip_type = "Palletizer"
        else:
            continue  # Skip sources and sinks for now

        # Get line ID from equipment ID
        line_id = equip_id.split("-")[0].replace("LINE", "")

        collector.register_equipment(
            equipment_id=equip_id, equipment=primitive, equipment_type=equip_type, line_id=line_id
        )

    # Start data collection process
    env.process(collector.collect_data())

    # Create coordinator
    coordinator = MESSimulationCoordinator(
        env=env, scheduler=scheduler, collector=collector, primitives=primitives, lines=lines
    )

    logger.info("MES simulation setup complete")

    return {"scheduler": scheduler, "collector": collector, "coordinator": coordinator}
