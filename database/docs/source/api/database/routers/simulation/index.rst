database.routers.simulation
===========================

.. py:module:: database.routers.simulation

.. autoapi-nested-parse::

   Simulation management endpoints

   Provides API for running and managing twin simulations



Attributes
----------

.. autoapisummary::

   database.routers.simulation.router


Functions
---------

.. autoapisummary::

   database.routers.simulation.run_simulation
   database.routers.simulation.list_simulations
   database.routers.simulation.get_simulation
   database.routers.simulation.get_simulation_data
   database.routers.simulation.get_simulation_kpis
   database.routers.simulation.compare_simulations
   database.routers.simulation.delete_simulation


Module Contents
---------------

.. py:data:: router

.. py:function:: run_simulation(request, manager)
   :async:


   Run a new simulation with specified parameters

   This endpoint:
   1. Creates a new simulation run record
   2. Executes the SimPy simulation
   3. Stores results in MES format
   4. Calculates KPIs
   5. Returns run summary


.. py:function:: list_simulations(session, run_type = None, status = None, page = Query(1, ge=1), page_size = Query(10, ge=1, le=100))
   :async:


   List simulation runs with optional filtering

   Filter by:
   - run_type: baseline, experiment, optimization, recommendation
   - status: pending, running, completed, failed


.. py:function:: get_simulation(run_id, session)
   :async:


   Get details of a specific simulation run


.. py:function:: get_simulation_data(run_id, session, limit = Query(1000, ge=1, le=10000), offset = Query(0, ge=0))
   :async:


   Get raw simulation data in MES format

   Returns the simulation output data with pagination


.. py:function:: get_simulation_kpis(run_id, session)
   :async:


   Get KPI summary for a simulation run

   Calculates:
   - Mean OEE, Availability, Performance, Quality
   - Total production and scrap
   - Scrap rate


.. py:function:: compare_simulations(baseline_run_id, comparison_run_id, session)
   :async:


   Compare two simulation runs

   Calculates deltas for all KPIs and determines
   if the difference is statistically significant


.. py:function:: delete_simulation(run_id, session)
   :async:


   Delete a simulation run and all associated data

   This will remove:
   - The run record
   - All simulation data
   - Any KPI snapshots


