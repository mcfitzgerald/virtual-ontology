database.schemas
================

.. py:module:: database.schemas

.. autoapi-nested-parse::

   Pydantic schemas for API request/response models

   These models define the structure of data sent to and from the API,
   separate from the SQLModel database models



Classes
-------

.. autoapisummary::

   database.schemas.RunType
   database.schemas.RunStatus
   database.schemas.PatternType
   database.schemas.SimulationRequest
   database.schemas.ExperimentRequest
   database.schemas.SQLQueryRequest
   database.schemas.CleanupRequest
   database.schemas.BackupRequest
   database.schemas.DatabaseStats
   database.schemas.TableInfo
   database.schemas.SimulationResponse
   database.schemas.ExperimentResponse
   database.schemas.PatternResponse
   database.schemas.RecommendationResponse
   database.schemas.KPISummary
   database.schemas.ComparisonResponse
   database.schemas.SQLQueryResponse
   database.schemas.BackupResponse
   database.schemas.OperationResponse
   database.schemas.SimulationListResponse
   database.schemas.ExperimentListResponse
   database.schemas.PatternListResponse
   database.schemas.RecommendationListResponse


Module Contents
---------------

.. py:class:: RunType

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Types of simulation runs

   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: BASELINE
      :value: 'baseline'



   .. py:attribute:: EXPERIMENT
      :value: 'experiment'



   .. py:attribute:: OPTIMIZATION
      :value: 'optimization'



   .. py:attribute:: RECOMMENDATION
      :value: 'recommendation'



.. py:class:: RunStatus

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Status of a simulation run

   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: PENDING
      :value: 'pending'



   .. py:attribute:: RUNNING
      :value: 'running'



   .. py:attribute:: COMPLETED
      :value: 'completed'



   .. py:attribute:: FAILED
      :value: 'failed'



.. py:class:: PatternType

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Types of discovered patterns

   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: CORRELATION
      :value: 'correlation'



   .. py:attribute:: CAUSATION
      :value: 'causation'



   .. py:attribute:: THRESHOLD
      :value: 'threshold'



   .. py:attribute:: ANOMALY
      :value: 'anomaly'



.. py:class:: SimulationRequest(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Request to run a simulation

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: run_type
      :type:  RunType


   .. py:attribute:: parameters
      :type:  Dict[str, Any]
      :value: None



   .. py:attribute:: days
      :type:  int
      :value: None



   .. py:attribute:: parent_run_id
      :type:  Optional[str]
      :value: None



   .. py:attribute:: notes
      :type:  Optional[str]
      :value: None



.. py:class:: ExperimentRequest(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Request to create and run an experiment

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: name
      :type:  str
      :value: None



   .. py:attribute:: hypothesis
      :type:  str
      :value: None



   .. py:attribute:: parameter_changes
      :type:  Dict[str, Any]
      :value: None



   .. py:attribute:: days
      :type:  int
      :value: None



   .. py:attribute:: num_runs
      :type:  int
      :value: None



.. py:class:: SQLQueryRequest(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Request to execute SQL query

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: sql
      :type:  str
      :value: None



   .. py:attribute:: limit
      :type:  Optional[int]
      :value: None



.. py:class:: CleanupRequest(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Request to clean database

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: category
      :type:  Optional[str]
      :value: None



   .. py:attribute:: tables
      :type:  Optional[List[str]]
      :value: None



   .. py:attribute:: older_than_days
      :type:  Optional[int]
      :value: None



   .. py:attribute:: preserve
      :type:  List[str]
      :value: None



.. py:class:: BackupRequest(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Request to create database backup

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: description
      :type:  Optional[str]
      :value: None



   .. py:attribute:: compress
      :type:  bool
      :value: None



.. py:class:: DatabaseStats(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Database statistics

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: database_path
      :type:  str


   .. py:attribute:: file_size_mb
      :type:  float


   .. py:attribute:: total_tables
      :type:  int


   .. py:attribute:: total_records
      :type:  int


   .. py:attribute:: tables
      :type:  Dict[str, int]


   .. py:attribute:: ontology_version
      :type:  str


   .. py:attribute:: manifest_version
      :type:  str


   .. py:attribute:: categories
      :type:  Dict[str, Dict[str, Any]]


.. py:class:: TableInfo(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Information about a database table

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: record_count
      :type:  int


   .. py:attribute:: columns
      :type:  List[str]


   .. py:attribute:: indexes
      :type:  List[str]


   .. py:attribute:: sample_data
      :type:  Optional[List[Dict[str, Any]]]
      :value: None



.. py:class:: SimulationResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Response from simulation run

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: run_id
      :type:  str


   .. py:attribute:: status
      :type:  RunStatus


   .. py:attribute:: started_at
      :type:  datetime.datetime


   .. py:attribute:: finished_at
      :type:  Optional[datetime.datetime]


   .. py:attribute:: kpi_summary
      :type:  Optional[Dict[str, float]]


   .. py:attribute:: message
      :type:  str


.. py:class:: ExperimentResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Response from experiment creation

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: experiment_id
      :type:  str


   .. py:attribute:: name
      :type:  str


   .. py:attribute:: status
      :type:  str


   .. py:attribute:: baseline_run_id
      :type:  str


   .. py:attribute:: test_run_ids
      :type:  List[str]


   .. py:attribute:: results_summary
      :type:  Optional[Dict[str, Any]]


   .. py:attribute:: conclusion
      :type:  Optional[str]


.. py:class:: PatternResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Discovered pattern information

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: pattern_id
      :type:  int


   .. py:attribute:: pattern_type
      :type:  PatternType


   .. py:attribute:: pattern_name
      :type:  str


   .. py:attribute:: description
      :type:  str


   .. py:attribute:: confidence_score
      :type:  float


   .. py:attribute:: validated
      :type:  bool


   .. py:attribute:: discovered_at
      :type:  datetime.datetime


   .. py:attribute:: evidence
      :type:  Dict[str, Any]


.. py:class:: RecommendationResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Parameter recommendation

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: recommendation_id
      :type:  int


   .. py:attribute:: recommendation_type
      :type:  str


   .. py:attribute:: parameter_adjustments
      :type:  Dict[str, Any]


   .. py:attribute:: expected_improvement
      :type:  Dict[str, float]


   .. py:attribute:: confidence
      :type:  float


   .. py:attribute:: applied
      :type:  bool


   .. py:attribute:: created_at
      :type:  datetime.datetime


.. py:class:: KPISummary(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   KPI summary data

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


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


   .. py:attribute:: scrap_rate
      :type:  float


   .. py:attribute:: total_downtime_minutes
      :type:  Optional[float]


.. py:class:: ComparisonResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Comparison between two runs

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: baseline_run_id
      :type:  str


   .. py:attribute:: comparison_run_id
      :type:  str


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


   .. py:attribute:: is_significant
      :type:  bool


   .. py:attribute:: analysis
      :type:  Dict[str, Any]


.. py:class:: SQLQueryResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Response from SQL query

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: query
      :type:  str


   .. py:attribute:: columns
      :type:  List[str]


   .. py:attribute:: data
      :type:  List[Dict[str, Any]]


   .. py:attribute:: row_count
      :type:  int


   .. py:attribute:: limited
      :type:  bool


   .. py:attribute:: execution_time_ms
      :type:  float


.. py:class:: BackupResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Response from backup operation

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: backup_path
      :type:  str


   .. py:attribute:: size_mb
      :type:  float


   .. py:attribute:: tables_backed_up
      :type:  int


   .. py:attribute:: records_backed_up
      :type:  int


   .. py:attribute:: created_at
      :type:  datetime.datetime


   .. py:attribute:: compressed
      :type:  bool


.. py:class:: OperationResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   Generic operation response

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: success
      :type:  bool


   .. py:attribute:: message
      :type:  str


   .. py:attribute:: details
      :type:  Optional[Dict[str, Any]]
      :value: None



.. py:class:: SimulationListResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   List of simulation runs

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: runs
      :type:  List[SimulationResponse]


   .. py:attribute:: total
      :type:  int


   .. py:attribute:: page
      :type:  int


   .. py:attribute:: page_size
      :type:  int


.. py:class:: ExperimentListResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   List of experiments

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: experiments
      :type:  List[ExperimentResponse]


   .. py:attribute:: total
      :type:  int


.. py:class:: PatternListResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   List of discovered patterns

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: patterns
      :type:  List[PatternResponse]


   .. py:attribute:: total
      :type:  int


.. py:class:: RecommendationListResponse(/, **data: Any)

   Bases: :py:obj:`pydantic.BaseModel`


   List of recommendations

   Create a new model by parsing and validating input data from keyword arguments.

   Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
   validated to form a valid model.

   `self` is explicitly positional-only to allow `self` as a field name.


   .. py:attribute:: recommendations
      :type:  List[RecommendationResponse]


   .. py:attribute:: total
      :type:  int


