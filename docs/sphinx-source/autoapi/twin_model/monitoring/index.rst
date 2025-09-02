twin_model.monitoring
=====================

.. py:module:: twin_model.monitoring

.. autoapi-nested-parse::

   Monitoring module for real-time flow analysis and bottleneck detection.



Submodules
----------

.. toctree::
   :maxdepth: 1

   /autoapi/twin_model/monitoring/flow_monitor/index


Classes
-------

.. autoapisummary::

   twin_model.monitoring.BottleneckInfo
   twin_model.monitoring.FlowMonitor
   twin_model.monitoring.FlowSnapshot


Package Contents
----------------

.. py:class:: BottleneckInfo

   Information about a detected bottleneck.


   .. py:attribute:: equipment_id
      :type:  str


   .. py:attribute:: severity
      :type:  float


   .. py:attribute:: upstream_blocked
      :type:  list[str]
      :value: []



   .. py:attribute:: downstream_starved
      :type:  list[str]
      :value: []



   .. py:attribute:: duration
      :type:  float
      :value: 0.0



   .. py:attribute:: impact
      :type:  str
      :value: 'Low'



.. py:class:: FlowMonitor(env: simpy.Environment, monitoring_interval: float = 1.0, history_size: int = 100)

   Monitors flow and detects bottlenecks in real-time.


   .. py:attribute:: env


   .. py:attribute:: monitoring_interval
      :value: 1.0



   .. py:attribute:: history_size
      :value: 100



   .. py:attribute:: snapshots
      :type:  dict[str, collections.deque]


   .. py:attribute:: bottlenecks
      :type:  list[BottleneckInfo]
      :value: []



   .. py:attribute:: current_bottleneck
      :type:  BottleneckInfo | None
      :value: None



   .. py:attribute:: line_throughput
      :type:  dict[str, float]


   .. py:attribute:: line_oee
      :type:  dict[str, float]


   .. py:attribute:: primitives
      :type:  dict[str, twin_model.primitives.BaseFlowPrimitive]


   .. py:attribute:: topology
      :type:  dict[str, list[str]]


   .. py:attribute:: monitoring_process
      :type:  simpy.Process | None
      :value: None



   .. py:method:: register_primitives(primitives: dict[str, twin_model.primitives.BaseFlowPrimitive], topology: dict[str, list[str]] | None = None) -> None

      Register primitives to monitor.

      :param primitives: Dictionary of primitive instances
      :param topology: Connection topology (optional)



   .. py:method:: start() -> None

      Start monitoring process.



   .. py:method:: get_current_status() -> dict[str, Any]

      Get current monitoring status.

      :returns: Dictionary with current status information



   .. py:method:: get_bottleneck_history() -> list[dict[str, Any]]

      Get history of detected bottlenecks.

      :returns: List of bottleneck records



.. py:class:: FlowSnapshot

   Snapshot of flow metrics at a point in time.


   .. py:attribute:: timestamp
      :type:  float


   .. py:attribute:: equipment_id
      :type:  str


   .. py:attribute:: state
      :type:  twin_model.primitives.FlowState


   .. py:attribute:: input_level
      :type:  float


   .. py:attribute:: output_level
      :type:  float


   .. py:attribute:: throughput_rate
      :type:  float


   .. py:attribute:: utilization
      :type:  float


   .. py:attribute:: oee
      :type:  float


