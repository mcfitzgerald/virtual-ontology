database.models
===============

.. py:module:: database.models

.. autoapi-nested-parse::

   SQLModel database models for virtual twin system

   Keeps ontologies as YAML files, stores operational data in database



Classes
-------

.. autoapisummary::

   database.models.HistoricalMESData
   database.models.EquipmentConfig
   database.models.ProductConfig
   database.models.ProductionSchedule
   database.models.TwinRun
   database.models.SimulationData
   database.models.SimulationObservable
   database.models.Experiment
   database.models.DiscoveredPattern
   database.models.ParameterRecommendation
   database.models.KPISnapshot
   database.models.ComparisonResult


Module Contents
---------------

.. py:class:: HistoricalMESData(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Historical MES data for baseline reference


   .. py:attribute:: __tablename__
      :value: 'historical_mes_data'



   .. py:attribute:: id
      :type:  Optional[int]
      :value: None



   .. py:attribute:: timestamp
      :type:  datetime.datetime
      :value: None



   .. py:attribute:: production_order_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: line_id
      :type:  str
      :value: None



   .. py:attribute:: equipment_id
      :type:  str
      :value: None



   .. py:attribute:: equipment_type
      :type:  str


   .. py:attribute:: product_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: product_name
      :type:  Optional[str]
      :value: None



   .. py:attribute:: machine_status
      :type:  str


   .. py:attribute:: downtime_reason
      :type:  Optional[str]
      :value: None



   .. py:attribute:: good_units_produced
      :type:  int


   .. py:attribute:: scrap_units_produced
      :type:  int


   .. py:attribute:: target_rate_units_per_5min
      :type:  int


   .. py:attribute:: standard_cost_per_unit
      :type:  float


   .. py:attribute:: sale_price_per_unit
      :type:  float


   .. py:attribute:: availability_score
      :type:  float


   .. py:attribute:: performance_score
      :type:  float


   .. py:attribute:: quality_score
      :type:  float


   .. py:attribute:: oee_score
      :type:  float
      :value: None



   .. py:attribute:: energy_consumption_kwh
      :type:  Optional[float]
      :value: None



   .. py:attribute:: source
      :type:  str
      :value: None



   .. py:attribute:: import_date
      :type:  datetime.datetime
      :value: None



   .. py:attribute:: data_quality_score
      :type:  Optional[float]
      :value: None



.. py:class:: EquipmentConfig(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Equipment configuration from manifests


   .. py:attribute:: __tablename__
      :value: 'equipment_config'



   .. py:attribute:: equipment_id
      :type:  str
      :value: None



   .. py:attribute:: equipment_type
      :type:  str
      :value: None



   .. py:attribute:: line_id
      :type:  str
      :value: None



   .. py:attribute:: position
      :type:  Optional[int]
      :value: None



   .. py:attribute:: base_rate
      :type:  float


   .. py:attribute:: mtbf
      :type:  float


   .. py:attribute:: mttr
      :type:  float


   .. py:attribute:: energy_consumption_rate
      :type:  float


   .. py:attribute:: failure_patterns_json
      :type:  str
      :value: None



   .. py:attribute:: performance_by_product_json
      :type:  str
      :value: None



   .. py:attribute:: active
      :type:  bool
      :value: None



   .. py:attribute:: created_at
      :type:  datetime.datetime
      :value: None



   .. py:attribute:: updated_at
      :type:  datetime.datetime
      :value: None



   .. py:property:: failure_patterns
      :type: Dict[str, Any]



   .. py:property:: performance_by_product
      :type: Dict[str, float]



.. py:class:: ProductConfig(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Product configuration from manifests


   .. py:attribute:: __tablename__
      :value: 'product_config'



   .. py:attribute:: product_id
      :type:  str
      :value: None



   .. py:attribute:: product_name
      :type:  str


   .. py:attribute:: target_rate_units_per_5min
      :type:  int


   .. py:attribute:: standard_cost_per_unit
      :type:  float


   .. py:attribute:: sale_price_per_unit
      :type:  float


   .. py:attribute:: scrap_rate_normal
      :type:  float


   .. py:attribute:: scrap_rate_startup
      :type:  float


   .. py:attribute:: scrap_rate_quality_issue
      :type:  Optional[float]
      :value: None



   .. py:attribute:: properties_json
      :type:  str
      :value: None



   .. py:attribute:: active
      :type:  bool
      :value: None



   .. py:attribute:: created_at
      :type:  datetime.datetime
      :value: None



.. py:class:: ProductionSchedule(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Production schedule from manifests


   .. py:attribute:: __tablename__
      :value: 'production_schedule'



   .. py:attribute:: schedule_id
      :type:  Optional[int]
      :value: None



   .. py:attribute:: order_id
      :type:  str
      :value: None



   .. py:attribute:: product_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: line_id
      :type:  str
      :value: None



   .. py:attribute:: scheduled_start
      :type:  datetime.datetime


   .. py:attribute:: scheduled_duration_minutes
      :type:  int


   .. py:attribute:: target_quantity
      :type:  Optional[int]
      :value: None



   .. py:attribute:: priority
      :type:  int
      :value: None



   .. py:attribute:: schedule_type
      :type:  str
      :value: None



   .. py:attribute:: simulation_run_id
      :type:  Optional[str]
      :value: None



.. py:class:: TwinRun(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Twin simulation runs (keep existing structure)


   .. py:attribute:: __tablename__
      :value: 'twin_runs'



   .. py:attribute:: run_id
      :type:  str
      :value: None



   .. py:attribute:: run_type
      :type:  str


   .. py:attribute:: ontology_version
      :type:  str


   .. py:attribute:: manifest_version
      :type:  str


   .. py:attribute:: parameter_set_json
      :type:  str


   .. py:attribute:: config_delta_json
      :type:  str


   .. py:attribute:: seed
      :type:  int


   .. py:attribute:: started_at
      :type:  datetime.datetime


   .. py:attribute:: finished_at
      :type:  Optional[datetime.datetime]
      :value: None



   .. py:attribute:: simulation_days
      :type:  int


   .. py:attribute:: status
      :type:  str


   .. py:attribute:: kpi_summary_json
      :type:  Optional[str]
      :value: None



   .. py:attribute:: output_path
      :type:  Optional[str]
      :value: None



   .. py:attribute:: data_hash
      :type:  Optional[str]
      :value: None



   .. py:attribute:: parent_run_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: notes
      :type:  Optional[str]
      :value: None



   .. py:attribute:: created_by
      :type:  str
      :value: None



.. py:class:: SimulationData(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Simulation output data (MES format)


   .. py:attribute:: __tablename__
      :value: 'simulation_data'



   .. py:attribute:: id
      :type:  Optional[int]
      :value: None



   .. py:attribute:: run_id
      :type:  str
      :value: None



   .. py:attribute:: timestamp
      :type:  datetime.datetime
      :value: None



   .. py:attribute:: production_order_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: line_id
      :type:  str
      :value: None



   .. py:attribute:: equipment_id
      :type:  str
      :value: None



   .. py:attribute:: equipment_type
      :type:  str


   .. py:attribute:: product_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: product_name
      :type:  Optional[str]
      :value: None



   .. py:attribute:: machine_status
      :type:  str


   .. py:attribute:: downtime_reason
      :type:  Optional[str]
      :value: None



   .. py:attribute:: good_units_produced
      :type:  int


   .. py:attribute:: scrap_units_produced
      :type:  int


   .. py:attribute:: target_rate_units_per_5min
      :type:  int


   .. py:attribute:: standard_cost_per_unit
      :type:  float


   .. py:attribute:: sale_price_per_unit
      :type:  float


   .. py:attribute:: availability_score
      :type:  float


   .. py:attribute:: performance_score
      :type:  float


   .. py:attribute:: quality_score
      :type:  float


   .. py:attribute:: oee_score
      :type:  float
      :value: None



   .. py:attribute:: energy_consumption_kwh
      :type:  Optional[float]
      :value: None



.. py:class:: SimulationObservable(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Raw observables from simulation (optional detailed storage)


   .. py:attribute:: __tablename__
      :value: 'simulation_observables'



   .. py:attribute:: id
      :type:  Optional[int]
      :value: None



   .. py:attribute:: run_id
      :type:  str
      :value: None



   .. py:attribute:: timestamp
      :type:  float


   .. py:attribute:: primitive_id
      :type:  str
      :value: None



   .. py:attribute:: primitive_type
      :type:  str


   .. py:attribute:: event_type
      :type:  str
      :value: None



   .. py:attribute:: details_json
      :type:  str


   .. py:attribute:: severity
      :type:  Optional[str]
      :value: None



   .. py:attribute:: store_raw
      :type:  bool
      :value: None



.. py:class:: Experiment(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Experiments for parameter discovery


   .. py:attribute:: __tablename__
      :value: 'experiments'



   .. py:attribute:: experiment_id
      :type:  str
      :value: None



   .. py:attribute:: experiment_name
      :type:  str


   .. py:attribute:: hypothesis
      :type:  Optional[str]
      :value: None



   .. py:attribute:: baseline_run_id
      :type:  str
      :value: None



   .. py:attribute:: test_runs_json
      :type:  str


   .. py:attribute:: parameter_changes_json
      :type:  str


   .. py:attribute:: created_at
      :type:  datetime.datetime
      :value: None



   .. py:attribute:: created_by
      :type:  str


   .. py:attribute:: status
      :type:  str
      :value: None



   .. py:attribute:: results_summary_json
      :type:  Optional[str]
      :value: None



   .. py:attribute:: conclusion
      :type:  Optional[str]
      :value: None



.. py:class:: DiscoveredPattern(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Patterns discovered through experiments


   .. py:attribute:: __tablename__
      :value: 'discovered_patterns'



   .. py:attribute:: pattern_id
      :type:  Optional[int]
      :value: None



   .. py:attribute:: pattern_type
      :type:  str


   .. py:attribute:: pattern_name
      :type:  str


   .. py:attribute:: description
      :type:  str


   .. py:attribute:: evidence_json
      :type:  str


   .. py:attribute:: experiment_ids_json
      :type:  str


   .. py:attribute:: confidence_score
      :type:  float
      :value: None



   .. py:attribute:: discovered_at
      :type:  datetime.datetime
      :value: None



   .. py:attribute:: discovered_by
      :type:  str


   .. py:attribute:: validated
      :type:  bool
      :value: None



   .. py:attribute:: validation_runs_json
      :type:  Optional[str]
      :value: None



.. py:class:: ParameterRecommendation(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Parameter recommendations from discoveries


   .. py:attribute:: __tablename__
      :value: 'parameter_recommendations'



   .. py:attribute:: recommendation_id
      :type:  Optional[int]
      :value: None



   .. py:attribute:: pattern_id
      :type:  Optional[int]
      :value: None



   .. py:attribute:: recommendation_type
      :type:  str


   .. py:attribute:: parameter_adjustments_json
      :type:  str


   .. py:attribute:: expected_improvement_json
      :type:  str


   .. py:attribute:: confidence
      :type:  float
      :value: None



   .. py:attribute:: created_at
      :type:  datetime.datetime
      :value: None



   .. py:attribute:: applied
      :type:  bool
      :value: None



   .. py:attribute:: applied_run_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: actual_improvement_json
      :type:  Optional[str]
      :value: None



.. py:class:: KPISnapshot(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   KPI snapshots for quick comparison


   .. py:attribute:: __tablename__
      :value: 'kpi_snapshots'



   .. py:attribute:: snapshot_id
      :type:  Optional[int]
      :value: None



   .. py:attribute:: run_id
      :type:  str
      :value: None



   .. py:attribute:: entity_type
      :type:  str


   .. py:attribute:: entity_id
      :type:  str


   .. py:attribute:: mean_oee
      :type:  float


   .. py:attribute:: mean_availability
      :type:  float


   .. py:attribute:: mean_performance
      :type:  float


   .. py:attribute:: mean_quality
      :type:  float


   .. py:attribute:: total_good_units
      :type:  int


   .. py:attribute:: total_scrap_units
      :type:  int


   .. py:attribute:: total_downtime_minutes
      :type:  float


   .. py:attribute:: additional_metrics_json
      :type:  str
      :value: None



   .. py:attribute:: period_start
      :type:  datetime.datetime


   .. py:attribute:: period_end
      :type:  datetime.datetime


   .. py:attribute:: created_at
      :type:  datetime.datetime
      :value: None



.. py:class:: ComparisonResult(**data)

   Bases: :py:obj:`sqlmodel.SQLModel`


   Results of comparing runs


   .. py:attribute:: __tablename__
      :value: 'comparison_results'



   .. py:attribute:: comparison_id
      :type:  Optional[int]
      :value: None



   .. py:attribute:: baseline_run_id
      :type:  str
      :value: None



   .. py:attribute:: comparison_run_id
      :type:  str
      :value: None



   .. py:attribute:: oee_delta
      :type:  float


   .. py:attribute:: availability_delta
      :type:  float


   .. py:attribute:: performance_delta
      :type:  float


   .. py:attribute:: quality_delta
      :type:  float


   .. py:attribute:: production_delta
      :type:  int


   .. py:attribute:: statistical_test
      :type:  Optional[str]
      :value: None



   .. py:attribute:: p_value
      :type:  Optional[float]
      :value: None



   .. py:attribute:: is_significant
      :type:  bool
      :value: None



   .. py:attribute:: analysis_json
      :type:  str


   .. py:attribute:: created_at
      :type:  datetime.datetime
      :value: None



