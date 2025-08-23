"""State persistence and management for simulation pause/resume.

This module provides functionality to save and restore simulation state,
enabling pause/resume capabilities and recovery from interruptions.
"""

import json
import dill  # type: ignore[import-untyped]  # More powerful than pickle for complex objects
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, Tuple
from dataclasses import dataclass
import simpy
from datetime import datetime
import hashlib


@dataclass
class SimulationCheckpoint:
    """Represents a saved simulation state checkpoint.

    Stores all necessary information to restore a simulation
    from a specific point in time.

    Attributes:
        checkpoint_id: Unique identifier for this checkpoint
        simulation_time: Current simulation time when saved
        real_time: Real-world timestamp when saved
        primitives_state: Serialized state of all primitives
        environment_state: SimPy environment state
        cache_path: Path to associated event cache
        metadata: Additional checkpoint metadata
    """

    checkpoint_id: str
    simulation_time: float
    real_time: datetime
    primitives_state: Dict[str, Any]
    environment_state: Dict[str, Any]
    cache_path: Optional[str]
    metadata: Dict[str, Any]

    def to_file(self, filepath: Path) -> None:
        """Save checkpoint to file.

        Args:
            filepath: Path to save checkpoint file
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Use dill for better serialization support
        with open(filepath, "wb") as f:
            dill.dump(self, f)

    @classmethod
    def from_file(cls, filepath: Path) -> "SimulationCheckpoint":
        """Load checkpoint from file.

        Args:
            filepath: Path to checkpoint file

        Returns:
            Loaded checkpoint instance
        """
        with open(filepath, "rb") as f:
            return dill.load(f)  # type: ignore[no-any-return]

    def get_summary(self) -> Dict[str, Any]:
        """Get human-readable checkpoint summary.

        Returns:
            Dictionary with checkpoint summary information
        """
        return {
            "checkpoint_id": self.checkpoint_id,
            "simulation_time": self.simulation_time,
            "real_time": self.real_time.isoformat(),
            "num_primitives": len(self.primitives_state),
            "has_cache": self.cache_path is not None,
            "metadata": self.metadata,
        }


class StateManager:
    """Manages simulation state persistence and recovery.

    Provides methods to save simulation state at checkpoints,
    restore from saved states, and manage checkpoint lifecycle.

    Attributes:
        checkpoint_dir: Directory for storing checkpoints
        max_checkpoints: Maximum number of checkpoints to retain
        compression: Whether to compress checkpoint files
        checkpoints: List of available checkpoints
    """

    def __init__(
        self, checkpoint_dir: str = "checkpoints", max_checkpoints: int = 10, compression: bool = True
    ) -> None:
        """Initialize state manager.

        Args:
            checkpoint_dir: Directory for checkpoint storage
            max_checkpoints: Maximum checkpoints to retain
            compression: Enable checkpoint compression
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_checkpoints = max_checkpoints
        self.compression = compression

        # Load existing checkpoints
        self.checkpoints: List[str] = self._load_checkpoint_list()

    def save_checkpoint(
        self,
        env: simpy.Environment,
        primitives: Dict[str, Any],
        cache_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save current simulation state as checkpoint.

        Args:
            env: SimPy environment
            primitives: Dictionary of primitive instances
            cache_path: Optional path to event cache
            metadata: Optional checkpoint metadata

        Returns:
            Checkpoint ID
        """
        # Generate checkpoint ID
        checkpoint_id = self._generate_checkpoint_id(env.now)

        # Extract primitives state
        primitives_state = {}
        for name, primitive in primitives.items():
            try:
                # Get state from primitive if it has the method
                if hasattr(primitive, "get_state"):
                    primitives_state[name] = primitive.get_state()
                else:
                    # Fallback to basic attributes
                    primitives_state[name] = {
                        "id": getattr(primitive, "id", name),
                        "type": primitive.__class__.__name__,
                        "properties": getattr(primitive, "properties", {}),
                    }
            except Exception as e:
                print(f"  Warning: Could not save state for {name}: {e}")
                primitives_state[name] = {"error": str(e)}

        # Extract environment state
        environment_state = {
            "now": env.now,
            "active_process_count": 0,  # SimPy doesn't expose active processes easily
        }

        # Create checkpoint
        checkpoint = SimulationCheckpoint(
            checkpoint_id=checkpoint_id,
            simulation_time=env.now,
            real_time=datetime.now(),
            primitives_state=primitives_state,
            environment_state=environment_state,
            cache_path=cache_path,
            metadata=metadata or {},
        )

        # Save to file
        filepath = self._get_checkpoint_filepath(checkpoint_id)

        if self.compression:
            import gzip

            with gzip.open(str(filepath) + ".gz", "wb") as f:
                dill.dump(checkpoint, f)
        else:
            checkpoint.to_file(filepath)

        # Update checkpoint list
        self.checkpoints.append(checkpoint_id)
        self._cleanup_old_checkpoints()
        self._save_checkpoint_list()

        print(f"  ✓ Checkpoint saved: {checkpoint_id} at t={env.now}")

        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: str) -> SimulationCheckpoint:
        """Load checkpoint by ID.

        Args:
            checkpoint_id: ID of checkpoint to load

        Returns:
            Loaded checkpoint

        Raises:
            ValueError: If checkpoint not found
        """
        if checkpoint_id not in self.checkpoints:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        filepath = self._get_checkpoint_filepath(checkpoint_id)

        if self.compression:
            import gzip

            with gzip.open(str(filepath) + ".gz", "rb") as f:
                checkpoint = dill.load(f)
        else:
            checkpoint = SimulationCheckpoint.from_file(filepath)

        return checkpoint  # type: ignore[no-any-return]

    def restore_simulation(
        self, checkpoint_id: str, primitive_classes: Dict[str, Type]
    ) -> Tuple[simpy.Environment, Dict[str, Any]]:
        """Restore simulation from checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to restore
            primitive_classes: Mapping of type names to primitive classes

        Returns:
            Tuple of (environment, primitives dictionary)
        """
        checkpoint = self.load_checkpoint(checkpoint_id)

        # Create new environment at saved time
        env = simpy.Environment(initial_time=checkpoint.simulation_time)

        # Restore primitives
        primitives = {}
        for name, state in checkpoint.primitives_state.items():
            if "error" in state:
                print(f"  Warning: Skipping {name} due to save error")
                continue

            # Get primitive class
            prim_type = state.get("type", "Unknown")
            if prim_type in primitive_classes:
                prim_class = primitive_classes[prim_type]

                # Create primitive instance
                # This assumes primitives have a from_state method
                if hasattr(prim_class, "from_state"):
                    primitives[name] = prim_class.from_state(env, state)
                else:
                    print(f"  Warning: {prim_type} does not support state restoration")
            else:
                print(f"  Warning: Unknown primitive type: {prim_type}")

        print(f"  ✓ Simulation restored from checkpoint {checkpoint_id}")
        print(f"    Time: {checkpoint.simulation_time}")
        print(f"    Primitives: {len(primitives)}")

        return env, primitives

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints.

        Returns:
            List of checkpoint summaries
        """
        summaries = []

        for checkpoint_id in self.checkpoints:
            try:
                checkpoint = self.load_checkpoint(checkpoint_id)
                summaries.append(checkpoint.get_summary())
            except Exception as e:
                summaries.append({"checkpoint_id": checkpoint_id, "error": str(e)})

        return summaries

    def delete_checkpoint(self, checkpoint_id: str) -> None:
        """Delete a checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to delete
        """
        if checkpoint_id in self.checkpoints:
            filepath = self._get_checkpoint_filepath(checkpoint_id)

            # Remove file
            if self.compression:
                filepath = Path(str(filepath) + ".gz")

            if filepath.exists():
                filepath.unlink()

            # Update list
            self.checkpoints.remove(checkpoint_id)
            self._save_checkpoint_list()

            print(f"  ✓ Checkpoint deleted: {checkpoint_id}")

    def _generate_checkpoint_id(self, sim_time: float) -> str:
        """Generate unique checkpoint ID.

        Args:
            sim_time: Current simulation time

        Returns:
            Unique checkpoint ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sim_str = f"{sim_time:.0f}"

        # Create short hash for uniqueness
        hash_input = f"{timestamp}_{sim_str}_{len(self.checkpoints)}"
        hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:8]

        return f"ckpt_{timestamp}_t{sim_str}_{hash_val}"

    def _get_checkpoint_filepath(self, checkpoint_id: str) -> Path:
        """Get filepath for checkpoint.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Path to checkpoint file
        """
        return self.checkpoint_dir / f"{checkpoint_id}.ckpt"

    def _cleanup_old_checkpoints(self) -> None:
        """Remove old checkpoints if exceeding max limit."""
        if len(self.checkpoints) > self.max_checkpoints:
            # Remove oldest checkpoints
            to_remove = len(self.checkpoints) - self.max_checkpoints

            for checkpoint_id in self.checkpoints[:to_remove]:
                self.delete_checkpoint(checkpoint_id)

    def _load_checkpoint_list(self) -> List[str]:
        """Load list of available checkpoints.

        Returns:
            List of checkpoint IDs
        """
        list_file = self.checkpoint_dir / "checkpoints.json"

        if list_file.exists():
            with open(list_file, "r") as f:
                return json.load(f)  # type: ignore[no-any-return]

        # Scan directory for checkpoint files
        checkpoints = []
        for filepath in self.checkpoint_dir.glob("*.ckpt*"):
            checkpoint_id = filepath.stem.replace(".ckpt", "")
            if checkpoint_id not in checkpoints:
                checkpoints.append(checkpoint_id)

        return sorted(checkpoints)

    def _save_checkpoint_list(self) -> None:
        """Save checkpoint list to file."""
        list_file = self.checkpoint_dir / "checkpoints.json"

        with open(list_file, "w") as f:
            json.dump(self.checkpoints, f, indent=2)


class SimulationRunner:
    """Enhanced simulation runner with chunking and state management.

    Provides chunked execution with automatic checkpointing,
    progress reporting, and pause/resume capabilities.

    Attributes:
        env: SimPy environment
        primitives: Dictionary of simulation primitives
        state_manager: State persistence manager
        monitor: Optional simulation monitor
        cache_path: Path to event cache
    """

    def __init__(
        self,
        env: simpy.Environment,
        primitives: Dict[str, Any],
        checkpoint_dir: str = "checkpoints",
        enable_monitoring: bool = True,
    ) -> None:
        """Initialize simulation runner.

        Args:
            env: SimPy environment
            primitives: Dictionary of primitives
            checkpoint_dir: Directory for checkpoints
            enable_monitoring: Enable performance monitoring
        """
        self.env = env
        self.primitives = primitives
        self.state_manager = StateManager(checkpoint_dir)
        self.cache_path: Optional[str] = None

        # Setup monitoring
        if enable_monitoring:
            from twin_model.primitives.base import SimulationMonitor

            self.monitor = SimulationMonitor(env)
        else:
            self.monitor = None  # type: ignore[assignment]

    def run_chunked(
        self,
        total_days: int,
        chunk_size_days: float = 1.0,
        progress_callback: Optional[Any] = None,
        checkpoint_interval: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Run simulation in chunks with progress reporting.

        Args:
            total_days: Total simulation duration in days
            chunk_size_days: Size of each execution chunk
            progress_callback: Optional progress reporter
            checkpoint_interval: Days between auto checkpoints

        Returns:
            Simulation results and metrics
        """
        import tracemalloc
        import time

        if not tracemalloc.is_tracing():
            tracemalloc.start()

        # Convert to simulation time units (minutes)
        total_time = total_days * 24 * 60
        chunk_size = chunk_size_days * 24 * 60
        checkpoint_interval_minutes = checkpoint_interval * 24 * 60 if checkpoint_interval else None

        # Tracking
        start_real_time = time.time()
        last_checkpoint_time = 0
        chunks_completed = 0
        total_events = 0

        print("\nStarting chunked simulation:")
        print(f"  Total: {total_days} days ({total_time:.0f} minutes)")
        print(f"  Chunk size: {chunk_size_days} days")
        print(f"  Checkpoints: {'Every ' + str(checkpoint_interval) + ' days' if checkpoint_interval else 'Disabled'}")

        while self.env.now < total_time:
            # Calculate chunk end time
            chunk_end = min(self.env.now + chunk_size, total_time)
            chunk_start_real = time.time()

            # Run chunk
            self.env.run(until=chunk_end)

            # Get memory usage
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            memory_mb = current_memory / (1024 * 1024)

            # Count events
            if self.monitor:
                total_events = self.monitor.metrics["events_total"]

            # Progress callback
            if progress_callback:
                progress_callback(
                    current_time=self.env.now,
                    total_time=total_time,
                    events_processed=total_events,
                    memory_usage_mb=memory_mb,
                    chunks_completed=chunks_completed + 1,
                    chunk_time=time.time() - chunk_start_real,
                )

            # Auto checkpoint
            if checkpoint_interval_minutes and (self.env.now - last_checkpoint_time) >= checkpoint_interval_minutes:
                metadata = {"chunk": chunks_completed + 1, "memory_mb": memory_mb, "events": total_events}

                _ = self.state_manager.save_checkpoint(self.env, self.primitives, self.cache_path, metadata)

                last_checkpoint_time = self.env.now  # type: ignore[assignment]

            chunks_completed += 1

            # Check for pause request (could be from file, signal, etc.)
            if self._check_pause_requested():
                print("\n  ⏸  Simulation paused")
                self._handle_pause()

        # Final statistics
        elapsed_real = time.time() - start_real_time

        results = {
            "simulation_time": self.env.now,
            "real_time_seconds": elapsed_real,
            "chunks_completed": chunks_completed,
            "speed_factor": self.env.now / elapsed_real if elapsed_real > 0 else 0,
            "total_events": total_events,
            "peak_memory_mb": peak_memory / (1024 * 1024),
            "checkpoints_saved": len(self.state_manager.checkpoints),
        }

        if self.monitor:
            results["monitor_metrics"] = self.monitor.get_metrics()  # type: ignore[assignment]

        print("\n✓ Simulation completed:")
        print(f"  Time: {results['simulation_time']:.0f} minutes")
        print(f"  Real time: {results['real_time_seconds']:.1f} seconds")
        print(f"  Speed: {results['speed_factor']:.0f}x")
        print(f"  Events: {results['total_events']:,}")

        return results

    def resume_from_checkpoint(self, checkpoint_id: str, primitive_classes: Dict[str, Type]) -> None:
        """Resume simulation from checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to resume from
            primitive_classes: Mapping of type names to classes
        """
        self.env, self.primitives = self.state_manager.restore_simulation(checkpoint_id, primitive_classes)

        # Restart monitoring if enabled
        if self.monitor:
            from twin_model.primitives.base import SimulationMonitor

            self.monitor = SimulationMonitor(self.env)

    def _check_pause_requested(self) -> bool:
        """Check if pause has been requested.

        Returns:
            True if pause requested
        """
        # Check for pause file
        pause_file = Path("PAUSE_SIMULATION")
        return pause_file.exists()

    def _handle_pause(self) -> None:
        """Handle simulation pause."""
        # Save checkpoint
        checkpoint_id = self.state_manager.save_checkpoint(
            self.env, self.primitives, self.cache_path, {"reason": "user_pause"}
        )

        print(f"  Checkpoint saved: {checkpoint_id}")
        print("  Remove PAUSE_SIMULATION file to resume")

        # Wait for resume
        pause_file = Path("PAUSE_SIMULATION")
        while pause_file.exists():
            import time

            time.sleep(1)

        print("  ▶️  Resuming simulation")
