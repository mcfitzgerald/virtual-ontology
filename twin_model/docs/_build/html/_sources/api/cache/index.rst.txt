cache
=====

.. py:module:: cache

.. autoapi-nested-parse::

   Write-through cache for simulation observables.

   This module provides efficient storage of simulation events using
   memory-mapped files and numpy arrays, preventing memory exhaustion
   in long simulations while maintaining fast access.



Classes
-------

.. autoapisummary::

   cache.ObservableCache


Module Contents
---------------

.. py:class:: ObservableCache(cache_dir: Union[str, pathlib.Path], max_size: int = 1000000, dtype_size: int = 1024)

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


   .. py:attribute:: cache_dir


   .. py:attribute:: max_size
      :value: 1000000



   .. py:attribute:: dtype_size
      :value: 1024



   .. py:attribute:: write_index
      :type:  int
      :value: 0



   .. py:attribute:: event_count
      :type:  int
      :value: 0



   .. py:attribute:: file_count
      :type:  int
      :value: 0



   .. py:attribute:: mmap_file
      :type:  Optional[numpy.memmap]
      :value: None



   .. py:attribute:: current_file_path
      :type:  Optional[pathlib.Path]
      :value: None



   .. py:attribute:: metadata
      :type:  Dict[str, Any]


   .. py:method:: write_event(event: Dict[str, Any]) -> int

      Write single event to cache.

      Serializes event to bytes and stores in memory-mapped array.
      Automatically rotates to new file when current is full.

      :param event: Event dictionary to cache

      :returns: Global event index



   .. py:method:: write_batch(events: List[Dict[str, Any]]) -> List[int]

      Write batch of events to cache.

      :param events: List of event dictionaries

      :returns: List of global event indices



   .. py:method:: read_event(global_index: int) -> Optional[Dict[str, Any]]

      Read single event by global index.

      :param global_index: Global event index across all files

      :returns: Event dictionary or None if not found



   .. py:method:: read_range(start_index: int, end_index: int) -> List[Dict[str, Any]]

      Read range of events by indices.

      :param start_index: Starting global index (inclusive)
      :param end_index: Ending global index (exclusive)

      :returns: List of event dictionaries



   .. py:method:: query_events(event_type: Optional[str] = None, primitive_id: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None, limit: int = 1000) -> List[Dict[str, Any]]

      Query events with filters.

      Efficiently queries cached events using memory-mapped arrays
      without loading all data into memory.

      :param event_type: Filter by event type
      :param primitive_id: Filter by primitive ID
      :param start_time: Minimum timestamp
      :param end_time: Maximum timestamp
      :param limit: Maximum events to return

      :returns: List of matching events



   .. py:method:: flush() -> None

      Flush current cache file to disk.



   .. py:method:: get_stats() -> Dict[str, Any]

      Get cache statistics.

      :returns: Dictionary with cache statistics



   .. py:method:: clear() -> None

      Clear all cache files and reset state.



