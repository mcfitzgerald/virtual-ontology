twin.virtual_sensors
====================

.. py:module:: twin.virtual_sensors

.. autoapi-nested-parse::

   Virtual Sensor Layer - Derives observations from production data

   This module implements the virtual sensor abstraction layer that observes
   and derives metrics from MES production data, rather than generating
   synthetic sensor readings. This addresses the reality that many facilities
   have excellent MES data but lack comprehensive IoT sensor infrastructure.



Attributes
----------

.. autoapisummary::

   twin.virtual_sensors.logger


Classes
-------

.. autoapisummary::

   twin.virtual_sensors.SensorObservation
   twin.virtual_sensors.VirtualSensor
   twin.virtual_sensors.PowerMeterSensor
   twin.virtual_sensors.ThroughputSensor
   twin.virtual_sensors.DefectRateSensor
   twin.virtual_sensors.BottleneckDetector
   twin.virtual_sensors.LineCouplingMonitor
   twin.virtual_sensors.DowntimePatternSensor
   twin.virtual_sensors.VirtualSensorObserver


Module Contents
---------------

.. py:data:: logger

.. py:class:: SensorObservation

   Represents a single observation from a virtual sensor.


   .. py:attribute:: sensor_id
      :type:  str


   .. py:attribute:: equipment_id
      :type:  str


   .. py:attribute:: timestamp
      :type:  datetime.datetime


   .. py:attribute:: observable_property
      :type:  str


   .. py:attribute:: value
      :type:  float


   .. py:attribute:: unit
      :type:  str


   .. py:attribute:: confidence
      :type:  float
      :value: 1.0



   .. py:attribute:: metadata
      :type:  Optional[Dict[str, Any]]
      :value: None



.. py:class:: VirtualSensor(sensor_type: str, config: Optional[Dict] = None)

   Bases: :py:obj:`abc.ABC`


   Base class for virtual sensors that observe production data.

   Initialize virtual sensor.

   :param sensor_type: Type identifier for the sensor
   :param config: Optional configuration dictionary


   .. py:attribute:: sensor_type


   .. py:attribute:: config


   .. py:method:: observe(production_data: pandas.DataFrame) -> List[SensorObservation]
      :abstractmethod:


      Derive observations from production data.

      :param production_data: DataFrame containing MES/simulation data

      :returns: List of sensor observations



.. py:class:: PowerMeterSensor(config: Optional[Dict] = None)

   Bases: :py:obj:`VirtualSensor`


   Virtual power meter that derives energy consumption from production patterns.

   Initialize power meter sensor.

   :param config: Configuration with energy parameters


   .. py:attribute:: base_power


   .. py:attribute:: idle_power


   .. py:attribute:: confidence


   .. py:attribute:: product_power_factor


   .. py:method:: observe(production_data: pandas.DataFrame) -> List[SensorObservation]

      Calculate energy consumption from production patterns.

      :param production_data: DataFrame with production data

      :returns: List of power consumption observations



.. py:class:: ThroughputSensor(config: Optional[Dict] = None)

   Bases: :py:obj:`VirtualSensor`


   Observes production rate vs target to identify efficiency.

   Initialize throughput sensor.


   .. py:attribute:: confidence


   .. py:method:: observe(production_data: pandas.DataFrame) -> List[SensorObservation]

      Observe throughput efficiency from production data.

      :param production_data: DataFrame with production data

      :returns: List of throughput observations



.. py:class:: DefectRateSensor(config: Optional[Dict] = None)

   Bases: :py:obj:`VirtualSensor`


   Observes quality through scrap patterns.

   Initialize defect rate sensor.


   .. py:attribute:: confidence


   .. py:method:: observe(production_data: pandas.DataFrame) -> List[SensorObservation]

      Observe defect rates from production data.

      :param production_data: DataFrame with production data

      :returns: List of defect rate observations



.. py:class:: BottleneckDetector(config: Optional[Dict] = None)

   Bases: :py:obj:`VirtualSensor`


   Identifies production bottlenecks from OEE patterns.

   Initialize bottleneck detector.


   .. py:attribute:: window_size


   .. py:attribute:: significance_threshold


   .. py:attribute:: confidence


   .. py:method:: observe(production_data: pandas.DataFrame) -> List[SensorObservation]

      Identify bottlenecks from OEE patterns.

      :param production_data: DataFrame with production data

      :returns: List of bottleneck observations



.. py:class:: LineCouplingMonitor(config: Optional[Dict] = None)

   Bases: :py:obj:`VirtualSensor`


   Monitors equipment coupling and cascade effects.

   Initialize line coupling monitor.


   .. py:attribute:: cascade_threshold


   .. py:attribute:: confidence


   .. py:method:: observe(production_data: pandas.DataFrame) -> List[SensorObservation]

      Monitor cascade effects between equipment.

      :param production_data: DataFrame with production data

      :returns: List of coupling strength observations



.. py:class:: DowntimePatternSensor(config: Optional[Dict] = None)

   Bases: :py:obj:`VirtualSensor`


   Analyzes downtime patterns and trends.

   Initialize downtime pattern sensor.


   .. py:attribute:: confidence


   .. py:method:: observe(production_data: pandas.DataFrame) -> List[SensorObservation]

      Analyze downtime patterns from production data.

      :param production_data: DataFrame with production data

      :returns: List of downtime pattern observations



.. py:class:: VirtualSensorObserver(config: Optional[Dict] = None)

   Orchestrates all virtual sensors to observe production data.

   Initialize the virtual sensor observer.

   :param config: Configuration dictionary for sensors


   .. py:attribute:: config


   .. py:attribute:: sensors


   .. py:method:: observe_production(production_data: pandas.DataFrame, sensors: Optional[List[str]] = None) -> pandas.DataFrame

      Run virtual sensors and collect observations.

      :param production_data: DataFrame containing production data
      :param sensors: Optional list of sensor types to run (runs all if None)

      :returns: DataFrame of sensor observations



   .. py:method:: get_sensor_summary(observations_df: pandas.DataFrame) -> Dict[str, Any]

      Generate summary statistics from sensor observations.

      :param observations_df: DataFrame of sensor observations

      :returns: Dictionary of summary statistics



