twin_model.scheduling.config_loader
===================================

.. py:module:: twin_model.scheduling.config_loader

.. autoapi-nested-parse::

   Configuration loader for scheduler settings.

   This module provides utilities to load scheduler configuration
   from YAML files, making the scheduler fully configurable.



Attributes
----------

.. autoapisummary::

   twin_model.scheduling.config_loader.logger


Functions
---------

.. autoapisummary::

   twin_model.scheduling.config_loader.load_scheduler_config
   twin_model.scheduling.config_loader.load_scheduling_constraints
   twin_model.scheduling.config_loader.load_complete_scheduler_config
   twin_model.scheduling.config_loader.create_scheduler_from_config
   twin_model.scheduling.config_loader.validate_schedule_config


Module Contents
---------------

.. py:data:: logger

.. py:function:: load_scheduler_config(config_path: pathlib.Path) -> twin_model.scheduling.base_scheduler.SchedulerConfig

   Load scheduler configuration from YAML file.

   :param config_path: Path to YAML configuration file

   :returns: SchedulerConfig object

   :raises FileNotFoundError: If config file doesn't exist
   :raises ValueError: If config file is invalid


.. py:function:: load_scheduling_constraints(config_path: pathlib.Path) -> twin_model.scheduling.base_scheduler.SchedulingConstraints

   Load scheduling constraints from YAML file.

   :param config_path: Path to YAML configuration file

   :returns: SchedulingConstraints object

   :raises FileNotFoundError: If config file doesn't exist
   :raises ValueError: If config file is invalid


.. py:function:: load_complete_scheduler_config(config_path: pathlib.Path) -> Tuple[twin_model.scheduling.base_scheduler.SchedulerConfig, twin_model.scheduling.base_scheduler.SchedulingConstraints]

   Load both scheduler config and constraints from a single file.

   :param config_path: Path to YAML configuration file

   :returns: Tuple of (SchedulerConfig, SchedulingConstraints)

   :raises FileNotFoundError: If config file doesn't exist
   :raises ValueError: If config file is invalid


.. py:function:: create_scheduler_from_config(env, config_path: Optional[pathlib.Path] = None, catalog_path: Optional[pathlib.Path] = None, random_seed: Optional[int] = None)

   Create a ProductionScheduler from configuration files.

   :param env: SimPy environment
   :param config_path: Path to scheduler configuration YAML
   :param catalog_path: Path to product catalog YAML
   :param random_seed: Random seed for reproducibility

   :returns: Configured ProductionScheduler instance


.. py:function:: validate_schedule_config(config_path: pathlib.Path) -> List[str]

   Validate a scheduler configuration file.

   :param config_path: Path to YAML configuration file

   :returns: List of validation warnings/errors (empty if valid)


