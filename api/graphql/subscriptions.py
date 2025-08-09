"""
GraphQL Subscriptions for Real-time Updates
"""

import strawberry
import asyncio
from typing import AsyncGenerator, List
from datetime import datetime
import random

from .types import SyncHealthReport, SimulationProgress, SyncHealthStatus


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def sync_health_updates(
        self, 
        info: strawberry.Info
    ) -> AsyncGenerator[List[SyncHealthReport], None]:
        """
        Stream synchronization health updates every 5 seconds
        """
        monitor = info.context["sync_monitor"]
        
        try:
            while True:
                # Get current health status
                health_data = monitor.get_all_sync_status()
                
                reports = []
                for entity_id, data in health_data.items():
                    status_str = data.get("health_status", "STALE")
                    try:
                        status = SyncHealthStatus[status_str]
                    except KeyError:
                        status = SyncHealthStatus.STALE
                    
                    reports.append(SyncHealthReport(
                        entity_id=entity_id,
                        entity_type=data.get("entity_type", "Equipment"),
                        health_status=status,
                        last_update=datetime.fromisoformat(
                            data.get("last_update", datetime.now().isoformat())
                        ),
                        sync_interval_minutes=data.get("sync_interval_minutes", 5),
                        data_freshness_seconds=data.get("data_freshness_seconds", 0)
                    ))
                
                yield reports
                
                # Wait before next update
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            # Clean shutdown when client disconnects
            pass
    
    @strawberry.subscription
    async def simulation_progress(
        self,
        run_id: str,
        info: strawberry.Info
    ) -> AsyncGenerator[SimulationProgress, None]:
        """
        Stream simulation progress updates
        """
        try:
            # Simulate progress updates
            steps = [
                "Initializing simulation",
                "Loading configuration",
                "Generating synthetic data",
                "Calculating KPIs",
                "Running optimization",
                "Finalizing results"
            ]
            
            for i, step in enumerate(steps):
                progress = SimulationProgress(
                    run_id=run_id,
                    status="running",
                    progress_percentage=(i + 1) / len(steps) * 100,
                    current_step=step,
                    estimated_completion=datetime.now(),
                    messages=[f"Completed: {step}"]
                )
                
                yield progress
                
                # Simulate work being done
                await asyncio.sleep(2)
            
            # Final complete status
            yield SimulationProgress(
                run_id=run_id,
                status="completed",
                progress_percentage=100,
                current_step="Complete",
                estimated_completion=datetime.now(),
                messages=["Simulation completed successfully"]
            )
            
        except asyncio.CancelledError:
            # Clean shutdown
            pass