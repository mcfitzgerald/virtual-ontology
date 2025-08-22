Performance Optimization
========================

The Twin Model framework has been optimized through 6 comprehensive phases to achieve production-scale performance.

Performance Achievements
------------------------

After optimization:

* **Memory**: 90%+ reduction (5.5MB → 0.5MB)
* **30-Day Simulations**: <500MB memory, <5 minutes
* **Event Processing**: 99% reduction through batching
* **Database**: 20,000+ events/second insertion

Optimization Phases
-------------------

Phase 1: Memory Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Circular Buffers**

.. code-block:: python

   from collections import deque
   
   class ObservableBuffer:
       def __init__(self, buffer_size=1000):
           self.buffer = deque(maxlen=buffer_size)
           # Automatically discards oldest when full

**Sampling Strategies**

.. code-block:: python

   class SamplingConfig:
       mode: SimulationMode
       sampling_rate: int  # Keep 1 in N events
       buffer_size: int
       
   # Example: Keep 1% of events
   sampling = SamplingConfig(
       mode=SimulationMode.FAST,
       sampling_rate=100,
       buffer_size=100
   )

Phase 2: Event Processing
^^^^^^^^^^^^^^^^^^^^^^^^^

**Event Batching**

.. code-block:: python

   class EventBatcher:
       def batch_events(self, events, window=60):
           """Group events by type and time window"""
           batches = defaultdict(list)
           for event in events:
               key = (event['type'], event['time'] // window)
               batches[key].append(event)
           return batches

**Incremental Aggregation**

.. code-block:: python

   class IncrementalAggregator:
       """Welford's algorithm for stable statistics"""
       def update(self, value):
           self.count += 1
           delta = value - self.mean
           self.mean += delta / self.count
           self.m2 += delta * (value - self.mean)

Phase 3: Storage Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Write-Through Cache**

.. code-block:: python

   class ObservableCache:
       def __init__(self, cache_dir, max_size=1_000_000):
           self.mmap_file = np.memmap(
               cache_path,
               dtype=np.uint8,
               mode='w+',
               shape=(max_size, dtype_size)
           )

**Batch Database Operations**

.. code-block:: python

   def batch_insert_events(self, events, batch_size=1000):
       """Insert events in batches"""
       for i in range(0, len(events), batch_size):
           batch = events[i:i+batch_size]
           session.bulk_insert_mappings(SimulationData, batch)
           session.commit()

Phase 4: Progress & State
^^^^^^^^^^^^^^^^^^^^^^^^^

**State Persistence**

.. code-block:: python

   @dataclass
   class SimulationCheckpoint:
       checkpoint_id: str
       simulation_time: float
       primitives_state: Dict[str, Any]
       
   def save_checkpoint(self):
       with open(f"checkpoint_{self.id}.pkl", 'wb') as f:
           dill.dump(self.checkpoint, f)

**Progress Monitoring**

.. code-block:: python

   class ConsoleProgressReporter:
       def report(self, current, total, memory_mb):
           print(f"Progress: {current}/{total} days")
           print(f"Memory: {memory_mb:.1f}MB")

Phase 5: Configuration System
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Performance Presets**

.. code-block:: python

   class ConfigPreset(Enum):
       DEVELOPMENT = "development"     # Full data
       PRODUCTION = "production"       # Balanced
       FAST = "fast"                  # Maximum speed
       MEMORY_OPTIMIZED = "memory"    # Minimal memory
       LONG_RUNNING = "long_running"  # 30+ days
       REAL_TIME = "real_time"        # Live monitoring

**Memory Estimation**

.. code-block:: python

   def estimate_memory_usage(self, num_primitives, days):
       events_per_day = num_primitives * 1440 / self.sampling_rate
       buffer_mb = (self.buffer_size * 8 * num_primitives) / 1_048_576
       cache_mb = (events_per_day * days * 100) / 1_048_576
       return {'buffer_mb': buffer_mb, 'cache_mb': cache_mb}

Phase 6: Integration
^^^^^^^^^^^^^^^^^^^^

**Adaptive Optimization**

.. code-block:: python

   def adaptive_mode_switch(self):
       """Switch modes based on memory pressure"""
       if self.get_memory_usage() > self.max_memory_mb:
           self.switch_to_fast_mode()

**Profiling Integration**

.. code-block:: python

   class SimulationProfiler:
       def profile_function(self, func):
           profiler = cProfile.Profile()
           profiler.enable()
           result = func()
           profiler.disable()
           return self.analyze_profile(profiler)

Best Practices
--------------

Choosing the Right Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**For Development/Debugging**

.. code-block:: python

   config = PerformanceConfig.from_preset(ConfigPreset.DEVELOPMENT)
   # Full observables, no sampling

**For Production (7-day runs)**

.. code-block:: python

   config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
   # Balanced performance, 10% sampling

**For Long Simulations (30+ days)**

.. code-block:: python

   config = PerformanceConfig.from_preset(ConfigPreset.LONG_RUNNING)
   # Aggressive sampling, checkpointing enabled

Memory Management Tips
^^^^^^^^^^^^^^^^^^^^^^

1. **Use Circular Buffers**: Prevent unbounded growth
2. **Enable Sampling**: Reduce data volume
3. **Batch Processing**: Group operations
4. **Clear Unused Data**: Explicitly delete large objects
5. **Monitor Memory**: Track usage during runs

Performance Monitoring
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import tracemalloc
   
   # Start monitoring
   tracemalloc.start()
   
   # Run simulation
   env.run(until=duration)
   
   # Get peak memory
   current, peak = tracemalloc.get_traced_memory()
   print(f"Peak memory: {peak / 1_048_576:.1f}MB")
   tracemalloc.stop()

Optimization Checklist
-----------------------

Before running large simulations:

☐ Choose appropriate performance preset
☐ Configure sampling rate based on needs
☐ Set reasonable buffer sizes
☐ Enable checkpointing for very long runs
☐ Monitor memory usage during development
☐ Use batch operations for database writes
☐ Profile code to identify bottlenecks
☐ Clear observables after processing

Benchmarks
----------

**Standard 7-Day Simulation**

================ ============ ============
Configuration    Memory (MB)  Time (sec)
================ ============ ============
DEVELOPMENT      250          45
PRODUCTION       50           30
FAST             15           20
MEMORY_OPTIMIZED 10           35
================ ============ ============

**30-Day Simulation**

================ ============ ============
Configuration    Memory (MB)  Time (sec)
================ ============ ============
LONG_RUNNING     450          240
FAST             200          180
MEMORY_OPTIMIZED 150          300
================ ============ ============

Troubleshooting Performance
----------------------------

**High Memory Usage**
   - Reduce buffer sizes
   - Increase sampling rate
   - Enable more aggressive mode
   - Check for memory leaks in custom code

**Slow Execution**
   - Use FAST preset
   - Reduce observable emissions
   - Batch database operations
   - Profile to find bottlenecks

**Database Bottlenecks**
   - Increase batch size
   - Use async inserts
   - Consider write-through cache
   - Optimize indexes