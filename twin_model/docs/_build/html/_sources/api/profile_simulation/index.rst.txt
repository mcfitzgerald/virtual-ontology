profile_simulation
==================

.. py:module:: profile_simulation

.. autoapi-nested-parse::

   Profiling tool for simulation performance analysis.

   This module provides profiling capabilities to identify bottlenecks
   and optimize simulation performance.



Classes
-------

.. autoapisummary::

   profile_simulation.ProfileResult
   profile_simulation.SimulationProfiler


Functions
---------

.. autoapisummary::

   profile_simulation.profile_quick_simulation


Module Contents
---------------

.. py:class:: ProfileResult

   Results from profiling a simulation run.

   .. attribute:: name

      Name of the profiled run

   .. attribute:: total_time

      Total execution time

   .. attribute:: cpu_time

      Total CPU time

   .. attribute:: memory_peak_mb

      Peak memory usage

   .. attribute:: memory_growth_mb

      Memory growth during execution

   .. attribute:: top_functions

      Top time-consuming functions

   .. attribute:: top_memory

      Top memory-consuming operations

   .. attribute:: bottlenecks

      Identified performance bottlenecks


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: total_time
      :type:  float


   .. py:attribute:: cpu_time
      :type:  float


   .. py:attribute:: memory_peak_mb
      :type:  float


   .. py:attribute:: memory_growth_mb
      :type:  float


   .. py:attribute:: top_functions
      :type:  List[Dict[str, Any]]


   .. py:attribute:: top_memory
      :type:  List[Dict[str, Any]]


   .. py:attribute:: bottlenecks
      :type:  List[str]


   .. py:method:: print_summary() -> None

      Print human-readable summary of profile results.



.. py:class:: SimulationProfiler(profile_dir: str = 'profile_results')

   Profile simulation performance and identify bottlenecks.

   Provides CPU profiling, memory profiling, and bottleneck analysis
   for simulation runs.

   .. attribute:: profile_dir

      Directory for storing profile results

   .. attribute:: cpu_profiler

      cProfile instance

   .. attribute:: memory_snapshots

      Memory usage snapshots

   .. attribute:: results

      List of profile results

   Initialize profiler.

   :param profile_dir: Directory for storing results


   .. py:attribute:: profile_dir


   .. py:attribute:: cpu_profiler
      :type:  Optional[cProfile.Profile]
      :value: None



   .. py:attribute:: memory_snapshots
      :type:  List[tracemalloc.Snapshot]
      :value: []



   .. py:attribute:: results
      :type:  List[ProfileResult]
      :value: []



   .. py:method:: profile_function(func: Callable, args: tuple = (), kwargs: dict = None, name: str = 'unnamed') -> ProfileResult

      Profile a function execution.

      :param func: Function to profile
      :param args: Function arguments
      :param kwargs: Function keyword arguments
      :param name: Name for this profile run

      :returns: Profile results



   .. py:method:: profile_simulation(simulation_func: Callable, config_name: str, **kwargs) -> ProfileResult

      Profile a simulation run.

      :param simulation_func: Simulation function to profile
      :param config_name: Name of configuration being tested
      :param \*\*kwargs: Arguments for simulation function

      :returns: Profile results



   .. py:method:: compare_profiles(*profile_names: str) -> Dict[str, Any]

      Compare multiple profile results.

      :param \*profile_names: Names of profiles to compare

      :returns: Comparison dictionary



   .. py:method:: generate_flame_graph(name: str) -> None

      Generate flame graph visualization.

      Note: Requires py-spy or flamegraph tools installed separately.

      :param name: Profile name for the graph



   .. py:method:: plot_performance_trends() -> None

      Plot performance trends across multiple profiles.



.. py:function:: profile_quick_simulation()

   Quick profiling example.


