twin.sync_health
================

.. py:module:: twin.sync_health

.. autoapi-nested-parse::

   Synchronization Health Monitoring for Virtual Twin
   Monitors the health status of synchronization between virtual and physical systems



Classes
-------

.. autoapisummary::

   twin.sync_health.SyncHealthStatus
   twin.sync_health.SyncMetadata
   twin.sync_health.SyncHealthMonitor


Module Contents
---------------

.. py:class:: SyncHealthStatus(*args, **kwds)

   Bases: :py:obj:`enum.Enum`


   Synchronization health states per ISO 23247


   .. py:attribute:: HEALTHY
      :value: 'HEALTHY'



   .. py:attribute:: DELAYED
      :value: 'DELAYED'



   .. py:attribute:: STALE
      :value: 'STALE'



   .. py:attribute:: UNKNOWN
      :value: 'UNKNOWN'



.. py:class:: SyncMetadata

   Metadata for entity synchronization


   .. py:attribute:: entity_id
      :type:  str


   .. py:attribute:: entity_type
      :type:  str


   .. py:attribute:: last_update
      :type:  datetime.datetime


   .. py:attribute:: sync_interval_minutes
      :type:  int


   .. py:attribute:: source_run_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: data_hash
      :type:  Optional[str]
      :value: None



   .. py:attribute:: health_status
      :type:  SyncHealthStatus


.. py:class:: SyncHealthMonitor(db_path: Optional[str] = None)

   Monitors synchronization health between virtual twin and data sources
   Compliant with ISO 23247 synchronization requirements

   Configuration is REQUIRED - all values must come from config

   Initialize the SyncHealthMonitor.
   Configuration is required - will raise error if not available.

   :param db_path: Path to the SQLite database (uses config if None)

   :raises RuntimeError: If configuration is not available
   :raises ValueError: If required config values are missing


   .. py:attribute:: config
      :value: None



   .. py:attribute:: db_path
      :type:  str
      :value: None



   .. py:attribute:: default_sync_interval
      :value: None



   .. py:attribute:: alert_threshold
      :value: None



   .. py:attribute:: status_thresholds
      :value: None



   .. py:attribute:: sync_log_retention_days
      :value: None



   .. py:attribute:: default_history_hours
      :value: None



   .. py:method:: init_sync_tables() -> None

      Initialize synchronization metadata tables



   .. py:method:: update_sync_metadata(entity_id: str, entity_type: str, data: Optional[Dict[str, Any]] = None, source_run_id: Optional[str] = None, sync_interval_minutes: Optional[int] = None) -> None

      Update synchronization metadata for an entity

      :param entity_id: Unique identifier for the entity
      :param entity_type: Type of entity (Equipment, Line, etc.)
      :param data: Optional data to hash for change detection
      :param source_run_id: Optional simulation run that generated this data
      :param sync_interval_minutes: Expected sync interval (uses config default if None)



   .. py:method:: get_sync_health(entity_id: Optional[str] = None) -> List[SyncMetadata]

      Get synchronization health for one or all entities

      :param entity_id: Optional specific entity ID, or None for all

      :returns: List of SyncMetadata objects



   .. py:method:: check_health_alerts(threshold_minutes: Optional[int] = None) -> List[Dict[str, Any]]

      Check for entities requiring health alerts

      :param threshold_minutes: Minutes before raising alert (uses config if None)

      :returns: List of entities requiring alerts



   .. py:method:: get_health_summary() -> Dict[str, Any]

      Get overall health summary statistics

      :returns: Dictionary with health statistics



   .. py:method:: get_sync_history(entity_id: str, hours: Optional[int] = None) -> List[Dict[str, Any]]

      Get synchronization history for an entity

      :param entity_id: Entity identifier
      :param hours: Hours of history to retrieve (uses config if None)

      :returns: List of sync history records



   .. py:method:: cleanup_old_logs(days_to_keep: Optional[int] = None) -> int

      Clean up old synchronization logs

      :param days_to_keep: Number of days of logs to retain (uses config if None)

      :returns: Number of records deleted



   .. py:method:: get_entity_types() -> List[str]

      Get list of all entity types being monitored

      :returns: List of unique entity types



   .. py:method:: export_health_report() -> Dict[str, Any]

      Export comprehensive health report

      :returns: Dictionary containing full health report



