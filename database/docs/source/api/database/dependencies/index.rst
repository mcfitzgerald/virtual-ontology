database.dependencies
=====================

.. py:module:: database.dependencies

.. autoapi-nested-parse::

   FastAPI dependencies for database access

   Provides dependency injection for:
   - Database sessions
   - Database manager
   - Repository instances



Attributes
----------

.. autoapisummary::

   database.dependencies.SessionDep
   database.dependencies.ManagerDep
   database.dependencies.TwinRunRepoDep
   database.dependencies.SimulationDataRepoDep
   database.dependencies.ExperimentRepoDep
   database.dependencies.PatternRepoDep
   database.dependencies.RecommendationRepoDep
   database.dependencies.KPIRepoDep


Functions
---------

.. autoapisummary::

   database.dependencies.get_db_manager
   database.dependencies.get_session
   database.dependencies.get_twin_run_repo
   database.dependencies.get_simulation_data_repo
   database.dependencies.get_experiment_repo
   database.dependencies.get_pattern_repo
   database.dependencies.get_recommendation_repo
   database.dependencies.get_kpi_repo


Module Contents
---------------

.. py:function:: get_db_manager(request)

   Get database manager from app state


.. py:function:: get_session(manager)

   Create a new database session for each request

   Yields a SQLModel Session that will be automatically
   closed when the request is complete


.. py:data:: SessionDep

.. py:data:: ManagerDep

.. py:function:: get_twin_run_repo(session)

   Get TwinRun repository instance


.. py:function:: get_simulation_data_repo(session)

   Get SimulationData repository instance


.. py:function:: get_experiment_repo(session)

   Get Experiment repository instance


.. py:function:: get_pattern_repo(session)

   Get Pattern repository instance


.. py:function:: get_recommendation_repo(session)

   Get Recommendation repository instance


.. py:function:: get_kpi_repo(session)

   Get KPI repository instance


.. py:data:: TwinRunRepoDep

.. py:data:: SimulationDataRepoDep

.. py:data:: ExperimentRepoDep

.. py:data:: PatternRepoDep

.. py:data:: RecommendationRepoDep

.. py:data:: KPIRepoDep

