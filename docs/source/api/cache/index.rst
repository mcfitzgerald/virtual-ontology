cache
=====

Write-through cache for simulation observables.

This module provides efficient storage of simulation events using
memory-mapped files and numpy arrays, preventing memory exhaustion
in long simulations while maintaining fast access.


Classes
-------

ObservableCache
~~~~~~~~~~~~~~~

Write-through cache for simulation observables using memory-mapped files.

Uses numpy memory-mapped files for efficient storage without keeping
all data in RAM. Supports incremental writes and fast retrieval.
This enables handling of millions of events with minimal memory footprint.

.. attribute:: cache_dir

   Directory for cache files

.. attribute:: max_size

   Maximum cache entries before rotation

.. attribute:: mmap_file

   Memory-mapped numpy array for event storage

.. attribute:: metadata_file

   JSON file for event metadata

.. attribute:: write_index

   Current write position in cache

.. attribute:: event_count

   Total events written

.. attribute:: file_count

   Number of cache files created

Initialize cache with memory mapping.

:param cache_dir: Directory for cache storage (created if not exists)
:param max_size: Maximum cache entries per file before rotation
:param dtype_size: Maximum bytes per event (default 1KB)


**Attributes:**

- **cache_dir** (attribute): 
- **current_file_path** (attribute): 
- **dtype_size** (attribute): 
- **event_count** (attribute): 
- **file_count** (attribute): 
- **max_size** (attribute): 
- **metadata** (attribute): 
- **mmap_file** (attribute): 
- **write_index** (attribute): 

**Methods:**

.. method:: __del__()

   Cleanup on deletion.



.. method:: __init__(cache_dir: Union[str, pathlib.Path], max_size: int = 1000000, dtype_size: int = 1024)

   Initialize cache with memory mapping.

   :param cache_dir: Directory for cache storage (created if not exists)
   :param max_size: Maximum cache entries per file before rotation
   :param dtype_size: Maximum bytes per event (default 1KB)



.. method:: _create_new_cache_file()

   Create a new memory-mapped cache file.

   Creates a new numpy memmap file for storing events and updates
   metadata tracking. Previous file is flushed and closed if exists.



.. method:: _find_event_location(global_index: int)

   Find which file and local index for a global event index.

   :param global_index: Global event index

   :returns: Tuple of (file_index, local_index) or (None, None) if not found



.. method:: _save_metadata()

   Save metadata to JSON file.



.. method:: clear()

   Clear all cache files and reset state.



.. method:: flush()

   Flush current cache file to disk.



.. method:: get_stats()

   Get cache statistics.

   :returns: Dictionary with cache statistics



.. method:: query_events(event_type: Optional[str] = None, primitive_id: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None, limit: int = 1000)

   Query events with filters.

   Efficiently queries cached events using memory-mapped arrays
   without loading all data into memory.

   :param event_type: Filter by event type
   :param primitive_id: Filter by primitive ID
   :param start_time: Minimum timestamp
   :param end_time: Maximum timestamp
   :param limit: Maximum events to return

   :returns: List of matching events



.. method:: read_event(global_index: int)

   Read single event by global index.

   :param global_index: Global event index across all files

   :returns: Event dictionary or None if not found



.. method:: read_range(start_index: int, end_index: int)

   Read range of events by indices.

   :param start_index: Starting global index (inclusive)
   :param end_index: Ending global index (exclusive)

   :returns: List of event dictionaries



.. method:: write_batch(events: List[Dict[str, Any]])

   Write batch of events to cache.

   :param events: List of event dictionaries

   :returns: List of global event indices



.. method:: write_event(event: Dict[str, Any])

   Write single event to cache.

   Serializes event to bytes and stores in memory-mapped array.
   Automatically rotates to new file when current is full.

   :param event: Event dictionary to cache

   :returns: Global event index






