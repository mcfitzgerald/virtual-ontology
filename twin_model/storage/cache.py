"""Write-through cache for simulation observables.

This module provides efficient storage of simulation events using
memory-mapped files and numpy arrays, preventing memory exhaustion
in long simulations while maintaining fast access.
"""

from pathlib import Path
import numpy as np
from typing import Optional, Union, Dict, Any, List, Tuple
import json
from datetime import datetime


class ObservableCache:
    """Write-through cache for simulation observables using memory-mapped files.

    Uses numpy memory-mapped files for efficient storage without keeping
    all data in RAM. Supports incremental writes and fast retrieval.
    This enables handling of millions of events with minimal memory footprint.

    Attributes:
        cache_dir: Directory for cache files
        max_size: Maximum cache entries before rotation
        mmap_file: Memory-mapped numpy array for event storage
        metadata_file: JSON file for event metadata
        write_index: Current write position in cache
        event_count: Total events written
        file_count: Number of cache files created
    """

    def __init__(
        self,
        cache_dir: Union[str, Path],
        max_size: int = 1_000_000,
        dtype_size: int = 1024,  # Bytes per event
    ) -> None:
        """Initialize cache with memory mapping.

        Args:
            cache_dir: Directory for cache storage (created if not exists)
            max_size: Maximum cache entries per file before rotation
            dtype_size: Maximum bytes per event (default 1KB)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_size = max_size
        self.dtype_size = dtype_size

        # Current cache file info
        self.write_index: int = 0
        self.event_count: int = 0
        self.file_count: int = 0

        # Memory-mapped array
        self.mmap_file: Optional[np.memmap] = None
        self.current_file_path: Optional[Path] = None

        # Metadata storage
        self.metadata: Dict[str, Any] = {"created": datetime.now().isoformat(), "files": [], "total_events": 0}

        # Initialize first cache file
        self._create_new_cache_file()

    def _create_new_cache_file(self) -> None:
        """Create a new memory-mapped cache file.

        Creates a new numpy memmap file for storing events and updates
        metadata tracking. Previous file is flushed and closed if exists.
        """
        # Close previous file if exists
        if self.mmap_file is not None:
            self.mmap_file.flush()
            del self.mmap_file

        # Generate new filename
        self.file_count += 1
        filename = f"cache_{self.file_count:04d}.mmap"
        self.current_file_path = self.cache_dir / filename

        # Create memory-mapped array
        # Using structured dtype for mixed data storage
        self.mmap_file = np.memmap(  # type: ignore[call-overload]
            self.current_file_path,
            dtype=np.dtype(
                [
                    ("timestamp", np.float64),
                    ("event_type", "U32"),  # Unicode string, max 32 chars
                    ("primitive_id", "U32"),
                    ("data", np.uint8, (self.dtype_size,)),  # Raw bytes for JSON
                ]
            ),
            mode="w+",
            shape=(self.max_size,),
        )

        # Reset write index
        self.write_index = 0

        # Update metadata
        self.metadata["files"].append(
            {
                "filename": filename,
                "created": datetime.now().isoformat(),
                "max_events": self.max_size,
                "current_events": 0,
            }
        )

        self._save_metadata()

    def write_event(self, event: Dict[str, Any]) -> int:
        """Write single event to cache.

        Serializes event to bytes and stores in memory-mapped array.
        Automatically rotates to new file when current is full.

        Args:
            event: Event dictionary to cache

        Returns:
            Global event index
        """
        # Check if we need a new file
        if self.write_index >= self.max_size:
            self._create_new_cache_file()

        # Serialize event data (excluding fields we store separately)
        event_copy = event.copy()
        timestamp = event_copy.pop("timestamp", 0.0)
        event_type = event_copy.pop("event_type", "unknown")[:32]
        primitive_id = event_copy.pop("primitive_id", "unknown")[:32]

        # Serialize remaining data to JSON bytes with datetime handling
        # Convert datetime objects to ISO strings
        def json_default(obj):
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        json_bytes = json.dumps(event_copy, default=json_default).encode("utf-8")

        # Truncate or pad to fit dtype_size
        if len(json_bytes) > self.dtype_size:
            json_bytes = json_bytes[: self.dtype_size]
        else:
            json_bytes = json_bytes + b"\0" * (self.dtype_size - len(json_bytes))

        # Write to memory-mapped array
        if self.mmap_file is not None:
            self.mmap_file[self.write_index] = (
                timestamp,
                event_type,
                primitive_id,
                np.frombuffer(json_bytes, dtype=np.uint8),
            )

        # Update indices
        self.write_index += 1
        self.event_count += 1

        # Update metadata for current file
        self.metadata["files"][-1]["current_events"] = self.write_index
        self.metadata["total_events"] = self.event_count

        # Periodic flush for durability
        if self.write_index % 1000 == 0 and self.mmap_file is not None:
            self.mmap_file.flush()

        return self.event_count - 1

    def write_batch(self, events: List[Dict[str, Any]]) -> List[int]:
        """Write batch of events to cache.

        Args:
            events: List of event dictionaries

        Returns:
            List of global event indices
        """
        indices = []
        for event in events:
            idx = self.write_event(event)
            indices.append(idx)

        # Flush after batch
        if self.mmap_file is not None:
            self.mmap_file.flush()

        return indices

    def read_event(self, global_index: int) -> Optional[Dict[str, Any]]:
        """Read single event by global index.

        Args:
            global_index: Global event index across all files

        Returns:
            Event dictionary or None if not found
        """
        if global_index >= self.event_count or global_index < 0:
            return None

        # Find which file contains this event
        file_idx, local_idx = self._find_event_location(global_index)

        if file_idx is None:
            return None

        # Open the specific file
        file_info = self.metadata["files"][file_idx]
        file_path = self.cache_dir / file_info["filename"]

        # Read from memory-mapped file
        dtype = (
            self.mmap_file.dtype
            if self.mmap_file is not None
            else np.dtype(
                [
                    ("timestamp", np.float64),
                    ("event_type", "U32"),
                    ("primitive_id", "U32"),
                    ("data", np.uint8, (self.dtype_size,)),
                ]
            )
        )
        mmap = np.memmap(  # type: ignore[call-overload]
            file_path, dtype=dtype, mode="r", shape=(file_info["max_events"],)
        )

        # Read event
        row = mmap[local_idx]

        # Reconstruct event dictionary
        json_bytes = row["data"].tobytes()
        json_str = json_bytes.rstrip(b"\0").decode("utf-8")

        event = json.loads(json_str) if json_str else {}
        event["timestamp"] = float(row["timestamp"])
        event["event_type"] = str(row["event_type"])
        event["primitive_id"] = str(row["primitive_id"])

        del mmap  # Close memory map

        return event

    def read_range(self, start_index: int, end_index: int) -> List[Dict[str, Any]]:
        """Read range of events by indices.

        Args:
            start_index: Starting global index (inclusive)
            end_index: Ending global index (exclusive)

        Returns:
            List of event dictionaries
        """
        events = []

        for idx in range(start_index, min(end_index, self.event_count)):
            event = self.read_event(idx)
            if event:
                events.append(event)

        return events

    def query_events(
        self,
        event_type: Optional[str] = None,
        primitive_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Query events with filters.

        Efficiently queries cached events using memory-mapped arrays
        without loading all data into memory.

        Args:
            event_type: Filter by event type
            primitive_id: Filter by primitive ID
            start_time: Minimum timestamp
            end_time: Maximum timestamp
            limit: Maximum events to return

        Returns:
            List of matching events
        """
        results: list[Dict[str, Any]] = []

        # Iterate through cache files
        for file_info in self.metadata["files"]:
            if len(results) >= limit:
                break

            file_path = self.cache_dir / file_info["filename"]
            if not file_path.exists():
                continue

            # Open memory-mapped file for reading
            dtype = (
                self.mmap_file.dtype
                if self.mmap_file is not None
                else np.dtype(
                    [
                        ("timestamp", np.float64),
                        ("event_type", "U32"),
                        ("primitive_id", "U32"),
                        ("data", np.uint8, (self.dtype_size,)),
                    ]
                )
            )
            mmap = np.memmap(  # type: ignore[call-overload]
                file_path, dtype=dtype, mode="r", shape=(file_info["max_events"],)
            )

            # Read only populated entries
            num_events = file_info["current_events"]
            data = mmap[:num_events]

            # Apply filters using numpy operations (very fast)
            mask = np.ones(num_events, dtype=bool)

            if event_type:
                mask &= data["event_type"] == event_type

            if primitive_id:
                mask &= data["primitive_id"] == primitive_id

            if start_time is not None:
                mask &= data["timestamp"] >= start_time

            if end_time is not None:
                mask &= data["timestamp"] <= end_time

            # Get matching indices
            matches = np.where(mask)[0]

            # Convert to events
            for idx in matches[: limit - len(results)]:
                row = data[idx]

                # Reconstruct event
                json_bytes = row["data"].tobytes()
                json_str = json_bytes.rstrip(b"\0").decode("utf-8")

                event = json.loads(json_str) if json_str else {}
                event["timestamp"] = float(row["timestamp"])
                event["event_type"] = str(row["event_type"])
                event["primitive_id"] = str(row["primitive_id"])

                results.append(event)

            del mmap  # Close memory map

        return results

    def _find_event_location(self, global_index: int) -> Tuple[Optional[int], Optional[int]]:
        """Find which file and local index for a global event index.

        Args:
            global_index: Global event index

        Returns:
            Tuple of (file_index, local_index) or (None, None) if not found
        """
        current_offset = 0

        for file_idx, file_info in enumerate(self.metadata["files"]):
            file_events = file_info["current_events"]

            if global_index < current_offset + file_events:
                local_idx = global_index - current_offset
                return file_idx, local_idx

            current_offset += file_events

        return None, None

    def _save_metadata(self) -> None:
        """Save metadata to JSON file."""
        metadata_path = self.cache_dir / "metadata.json"

        with open(metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def flush(self) -> None:
        """Flush current cache file to disk."""
        if self.mmap_file is not None:
            self.mmap_file.flush()
        self._save_metadata()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_size = sum(
            (self.cache_dir / f["filename"]).stat().st_size
            for f in self.metadata["files"]
            if (self.cache_dir / f["filename"]).exists()
        )

        return {
            "cache_dir": str(self.cache_dir),
            "total_events": self.event_count,
            "total_files": self.file_count,
            "current_file_events": self.write_index,
            "total_size_mb": total_size / (1024 * 1024),
            "events_per_file": self.max_size,
            "bytes_per_event": self.dtype_size,
        }

    def clear(self) -> None:
        """Clear all cache files and reset state."""
        # Close current mmap
        if self.mmap_file is not None:
            del self.mmap_file
            self.mmap_file = None

        # Remove all cache files
        for f in self.metadata["files"]:
            file_path = self.cache_dir / f["filename"]
            if file_path.exists():
                file_path.unlink()

        # Remove metadata
        metadata_path = self.cache_dir / "metadata.json"
        if metadata_path.exists():
            metadata_path.unlink()

        # Reset state
        self.write_index = 0
        self.event_count = 0
        self.file_count = 0
        self.metadata = {"created": datetime.now().isoformat(), "files": [], "total_events": 0}

        # Create new cache file
        self._create_new_cache_file()

    def __del__(self):
        """Cleanup on deletion."""
        if self.mmap_file is not None:
            try:
                self.mmap_file.flush()
                del self.mmap_file
            except Exception:
                pass  # Ignore errors during cleanup
