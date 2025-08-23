Quick Start Guide
=================

This guide will help you get started with the Virtual Ontology Twin Model.

Installation
------------

The twin model is part of the Virtual Ontology system. Ensure you have the required dependencies:

.. code-block:: bash

   pip install simpy numpy pandas pyyaml pydantic

Basic Setup
-----------

1. Create a Simple Model
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import simpy
   from twin_model.primitives import (
       EquipmentPrimitive,
       BufferPrimitive,
       SourcePrimitive,
       SinkPrimitive,
       MonitorPrimitive
   )
   
   # Create simulation environment
   env = simpy.Environment()
   
   # Create primitives
   source = SourcePrimitive(env, "Source1", arrival_rate=2.0)
   buffer = BufferPrimitive(env, "Buffer1", capacity=10)
   equipment = EquipmentPrimitive(env, "Equipment1", processing_time=5.0)
   sink = SinkPrimitive(env, "Sink1")
   monitor = MonitorPrimitive(env, "Monitor1")
   
   # Connect primitives
   source.set_output(buffer)
   buffer.set_output(equipment)
   equipment.set_output(sink)
   
   # Start processes
   env.process(source.generate_items())
   env.process(equipment.process_items())
   env.process(monitor.track_metrics())
   
   # Run simulation
   env.run(until=100)
   
   # Get results
   print(f"Items produced: {sink.get_production_count()}")
   print(f"Average OEE: {monitor.get_average_oee()}")

2. Using the Ontology Builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from twin_model import OntologyDrivenModelBuilder
   import simpy
   
   # Initialize builder with ontology
   builder = OntologyDrivenModelBuilder(
       ontology_path=Path("ontology/twin_ontology.yaml"),
       manifest_dir=Path("manifests/")
   )
   
   # Create environment and build model
   env = simpy.Environment()
   model = builder.build_model(env)
   
   # Configure simulation parameters
   model.configure(
       duration=1000,
       random_seed=42,
       log_events=True
   )
   
   # Run simulation
   results = model.run()
   
   # Access results
   print(f"Simulation completed at: {env.now}")
   print(f"KPIs: {results['kpi_summary']}")

Working with Ontologies
-----------------------

Defining Twin Ontology
~~~~~~~~~~~~~~~~~~~~~~

Create ``ontology/twin_ontology.yaml``:

.. code-block:: yaml

   twin_model:
     name: "Production Line Twin"
     version: "2.0.0"
     
     primitives:
       Equipment:
         class: "EquipmentPrimitive"
         properties:
           processing_time: float
           failure_rate: float
           mttr: float
           mtbf: float
         relationships:
           input_from: "Buffer"
           output_to: "Buffer"
       
       Buffer:
         class: "BufferPrimitive"
         properties:
           capacity: int
           initial_level: int
         relationships:
           receives_from: ["Equipment", "Source"]
           sends_to: ["Equipment", "Sink"]
     
     production_lines:
       Line1:
         components:
           - {type: "Source", id: "Source1"}
           - {type: "Buffer", id: "Buffer1"}
           - {type: "Equipment", id: "Equipment1"}
           - {type: "Buffer", id: "Buffer2"}
           - {type: "Equipment", id: "Equipment2"}
           - {type: "Sink", id: "Sink1"}
         flow:
           - {from: "Source1", to: "Buffer1"}
           - {from: "Buffer1", to: "Equipment1"}
           - {from: "Equipment1", to: "Buffer2"}
           - {from: "Buffer2", to: "Equipment2"}
           - {from: "Equipment2", to: "Sink1"}

Creating Manifests
~~~~~~~~~~~~~~~~~~

Create ``manifests/equipment_manifest.yaml``:

.. code-block:: yaml

   equipment:
     Equipment1:
       type: "Assembly"
       processing_time: 5.0
       failure_rate: 0.01
       mttr: 30.0
       mtbf: 1000.0
       capacity_per_hour: 100
     
     Equipment2:
       type: "Packaging"
       processing_time: 3.0
       failure_rate: 0.005
       mttr: 20.0
       mtbf: 2000.0
       capacity_per_hour: 150
   
   buffers:
     Buffer1:
       capacity: 50
       initial_level: 0
     
     Buffer2:
       capacity: 30
       initial_level: 0

Simulation Scenarios
--------------------

Baseline Simulation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin_model import OntologyDrivenModelBuilder
   import simpy
   
   def run_baseline_simulation():
       # Build model
       builder = OntologyDrivenModelBuilder(
           ontology_path=Path("ontology/twin_ontology.yaml"),
           manifest_dir=Path("manifests/")
       )
       
       env = simpy.Environment()
       model = builder.build_model(env)
       
       # Run for 1 day (1440 minutes)
       env.run(until=1440)
       
       # Collect metrics
       metrics = model.get_kpi_metrics()
       
       return {
           "oee": metrics["overall_oee"],
           "availability": metrics["availability"],
           "performance": metrics["performance"],
           "quality": metrics["quality"],
           "production": metrics["total_production"]
       }
   
   results = run_baseline_simulation()
   print(f"Baseline OEE: {results['oee']:.2f}%")

Scenario Comparison
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def compare_scenarios():
       scenarios = {
           "baseline": {"processing_time": 5.0, "failure_rate": 0.01},
           "optimized": {"processing_time": 4.5, "failure_rate": 0.005},
           "stressed": {"processing_time": 6.0, "failure_rate": 0.02}
       }
       
       results = {}
       
       for name, params in scenarios.items():
           # Override parameters
           builder = OntologyDrivenModelBuilder(
               ontology_path=Path("ontology/twin_ontology.yaml"),
               manifest_dir=Path("manifests/")
           )
           
           # Apply scenario parameters
           builder.override_parameters("Equipment1", params)
           
           env = simpy.Environment()
           model = builder.build_model(env)
           env.run(until=1440)
           
           results[name] = model.get_kpi_metrics()
       
       return results
   
   scenario_results = compare_scenarios()
   
   for name, metrics in scenario_results.items():
       print(f"{name}: OEE={metrics['overall_oee']:.1f}%")

Real-time Monitoring
--------------------

Event Callbacks
~~~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import EquipmentPrimitive
   
   class MonitoredEquipment(EquipmentPrimitive):
       def __init__(self, env, name, **kwargs):
           super().__init__(env, name, **kwargs)
           self.event_callbacks = []
       
       def add_callback(self, callback):
           self.event_callbacks.append(callback)
       
       def process_item(self, item):
           # Trigger callbacks
           for callback in self.event_callbacks:
               callback(self, "processing_start", item)
           
           # Process item
           yield self.env.timeout(self.processing_time)
           
           for callback in self.event_callbacks:
               callback(self, "processing_complete", item)
   
   # Usage
   def log_event(equipment, event, item):
       print(f"[{env.now}] {equipment.name}: {event} - {item}")
   
   equipment = MonitoredEquipment(env, "Equipment1", processing_time=5.0)
   equipment.add_callback(log_event)

Live Metrics Dashboard
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import threading
   import time
   from twin_model.primitives import MonitorPrimitive
   
   class LiveDashboard:
       def __init__(self, monitor: MonitorPrimitive):
           self.monitor = monitor
           self.running = False
       
       def start(self):
           self.running = True
           self.thread = threading.Thread(target=self._update_loop)
           self.thread.start()
       
       def stop(self):
           self.running = False
           self.thread.join()
       
       def _update_loop(self):
           while self.running:
               metrics = self.monitor.get_current_metrics()
               self._display_metrics(metrics)
               time.sleep(1)
       
       def _display_metrics(self, metrics):
           print(f"\r[{metrics['timestamp']}] "
                 f"OEE: {metrics['oee']:.1f}% | "
                 f"Prod: {metrics['production']} | "
                 f"Queue: {metrics['buffer_level']}", 
                 end="")
   
   # Usage
   monitor = MonitorPrimitive(env, "Monitor1")
   dashboard = LiveDashboard(monitor)
   dashboard.start()
   
   # Run simulation
   env.run(until=100)
   
   dashboard.stop()

Data Export
-----------

Export to CSV
~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   from twin_model.transduction import MESTransducer
   
   def export_simulation_data(model, output_path):
       # Get transducer
       transducer = MESTransducer()
       
       # Convert events to MES format
       mes_records = []
       for event in model.get_event_log():
           mes_record = transducer.transduce_event(event)
           mes_records.append(mes_record)
       
       # Create DataFrame
       df = pd.DataFrame(mes_records)
       
       # Add calculated fields
       df['OEE_Score'] = (df['Availability_Score'] * 
                          df['Performance_Score'] * 
                          df['Quality_Score']) / 10000
       
       # Export to CSV
       df.to_csv(output_path, index=False)
       print(f"Exported {len(df)} records to {output_path}")
       
       return df
   
   # Usage
   data = export_simulation_data(model, "simulation_output.csv")

Integration with Database
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from database import TwinDatabaseIntegration
   
   def store_simulation_results(model, experiment_name):
       db = TwinDatabaseIntegration()
       
       # Store run metadata
       run_id = db.store_simulation_run(
           experiment_name=experiment_name,
           parameters=model.get_parameters(),
           results=model.get_kpi_metrics()
       )
       
       # Store detailed events
       for event in model.get_event_log():
           db.store_event(run_id, event)
       
       print(f"Stored simulation run: {run_id}")
       return run_id

Advanced Configuration
----------------------

Custom Arrival Patterns
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import SourcePrimitive, ArrivalPattern
   import numpy as np
   
   class CustomArrivalPattern(ArrivalPattern):
       def __init__(self, morning_rate=10, afternoon_rate=5):
           self.morning_rate = morning_rate
           self.afternoon_rate = afternoon_rate
       
       def get_next_arrival(self, current_time):
           # Higher rate in morning, lower in afternoon
           hour = (current_time % 1440) / 60  # Hour of day
           
           if hour < 12:
               return np.random.exponential(1/self.morning_rate)
           else:
               return np.random.exponential(1/self.afternoon_rate)
   
   # Use custom pattern
   source = SourcePrimitive(
       env, "Source1",
       arrival_pattern=CustomArrivalPattern()
   )

Failure Modeling
~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import EquipmentPrimitive
   
   class ReliableEquipment(EquipmentPrimitive):
       def __init__(self, env, name, mtbf=1000, mttr=30, **kwargs):
           super().__init__(env, name, **kwargs)
           self.mtbf = mtbf  # Mean time between failures
           self.mttr = mttr  # Mean time to repair
           self.env.process(self.failure_process())
       
       def failure_process(self):
           while True:
               # Wait for next failure
               yield self.env.timeout(
                   np.random.exponential(self.mtbf)
               )
               
               # Equipment fails
               self.state = "failed"
               print(f"[{self.env.now}] {self.name} failed")
               
               # Repair time
               yield self.env.timeout(
                   np.random.exponential(self.mttr)
               )
               
               # Equipment repaired
               self.state = "idle"
               print(f"[{self.env.now}] {self.name} repaired")

Next Steps
----------

* Explore :doc:`primitives` for detailed component documentation
* Review :doc:`ontology_driven` for advanced model building
* See :doc:`usage` for real-world examples
* Check :doc:`api/index` for complete API reference