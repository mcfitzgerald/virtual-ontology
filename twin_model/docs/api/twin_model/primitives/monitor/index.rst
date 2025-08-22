twin_model.primitives.monitor
=============================

.. py:module:: twin_model.primitives.monitor

.. autoapi-nested-parse::

   Monitor primitive for KPI tracking and aggregation.

   This module provides a monitor primitive that tracks key performance indicators,
   aggregates metrics across the system, and provides real-time visibility into
   production performance.



Classes
-------

.. autoapisummary::

   twin_model.primitives.monitor.KPIType
   twin_model.primitives.monitor.KPIMetric
   twin_model.primitives.monitor.MonitorPrimitive


Module Contents
---------------

.. py:class:: KPIType

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Types of KPIs tracked.

   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: OEE
      :value: 'OEE'



   .. py:attribute:: AVAILABILITY
      :value: 'AVAILABILITY'



   .. py:attribute:: PERFORMANCE
      :value: 'PERFORMANCE'



   .. py:attribute:: QUALITY
      :value: 'QUALITY'



   .. py:attribute:: THROUGHPUT
      :value: 'THROUGHPUT'



   .. py:attribute:: CYCLE_TIME
      :value: 'CYCLE_TIME'



   .. py:attribute:: LEAD_TIME
      :value: 'LEAD_TIME'



   .. py:attribute:: SCRAP_RATE
      :value: 'SCRAP_RATE'



   .. py:attribute:: ENERGY_CONSUMPTION
      :value: 'ENERGY_CONSUMPTION'



   .. py:attribute:: MTBF
      :value: 'MTBF'



   .. py:attribute:: MTTR
      :value: 'MTTR'



   .. py:attribute:: UTILIZATION
      :value: 'UTILIZATION'



.. py:class:: KPIMetric

   A KPI metric with history.

   .. attribute:: name

      KPI name

   .. attribute:: type

      KPI type

   .. attribute:: value

      Current value

   .. attribute:: target

      Target value

   .. attribute:: history

      Historical values

   .. attribute:: unit

      Measurement unit

   .. attribute:: aggregation

      How to aggregate (avg, sum, max, min)


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: type
      :type:  KPIType


   .. py:attribute:: value
      :type:  float
      :value: 0.0



   .. py:attribute:: target
      :type:  Optional[float]
      :value: None



   .. py:attribute:: history
      :type:  List[Tuple[float, float]]
      :value: []



   .. py:attribute:: unit
      :type:  str
      :value: ''



   .. py:attribute:: aggregation
      :type:  str
      :value: 'avg'



   .. py:method:: add_value(timestamp: float, value: float) -> None

      Add a value to history.



   .. py:method:: get_average(window: Optional[float] = None, current_time: Optional[float] = None) -> float

      Get average value over time window.



   .. py:method:: get_trend() -> str

      Get trend direction.



.. py:class:: MonitorPrimitive(env: simpy.Environment, config: twin_model.primitives.base.PrimitiveConfig)

   Bases: :py:obj:`twin_model.primitives.base.BasePrimitive`


   Monitor for tracking system-wide KPIs and metrics.

   Emits observables for:
   - KPI updates and trends
   - Target violations
   - Performance alerts
   - Aggregated metrics
   - Real-time dashboards

   Initialize monitor with configuration.

   :param env: SimPy environment
   :param config: Monitor configuration containing:
                  - kpi_definitions: KPIs to track
                  - update_interval: How often to update KPIs (minutes)
                  - aggregation_window: Time window for aggregations
                  - alert_thresholds: Thresholds for alerts
                  - monitored_primitives: List of primitives to monitor


   .. py:attribute:: update_interval


   .. py:attribute:: aggregation_window


   .. py:attribute:: alert_thresholds


   .. py:attribute:: kpis
      :type:  Dict[str, KPIMetric]


   .. py:attribute:: monitored_primitives
      :type:  Dict[str, Any]


   .. py:attribute:: active_alerts
      :type:  List[Dict[str, Any]]
      :value: []



   .. py:attribute:: alert_history
      :type:  List[Dict[str, Any]]
      :value: []



   .. py:attribute:: line_metrics
      :type:  Dict[str, Dict[str, float]]


   .. py:attribute:: product_metrics
      :type:  Dict[str, Dict[str, float]]


   .. py:attribute:: shift_metrics
      :type:  Dict[str, Dict[str, float]]


   .. py:method:: start() -> None

      Start the monitoring process.



   .. py:method:: monitor_process() -> Generator

      Main monitoring process.



   .. py:method:: alert_process() -> Generator

      Process for managing alerts.



   .. py:method:: register_primitive(name: str, primitive: Any) -> None

      Register a primitive to monitor.

      :param name: Primitive identifier
      :param primitive: Primitive instance



   .. py:method:: get_kpi_value(kpi_name: str) -> Optional[float]

      Get current value of a KPI.

      :param kpi_name: Name of KPI

      :returns: Current KPI value or None



   .. py:method:: get_kpi_history(kpi_name: str, window: Optional[float] = None) -> List[Tuple[float, float]]

      Get historical values of a KPI.

      :param kpi_name: Name of KPI
      :param window: Time window to retrieve

      :returns: List of (timestamp, value) tuples



   .. py:method:: get_dashboard() -> Dict[str, Any]

      Get dashboard summary of all metrics.

      :returns: Dictionary with dashboard data



   .. py:method:: get_statistics() -> Dict[str, Any]

      Get monitor statistics.

      :returns: Dictionary of monitor metrics



