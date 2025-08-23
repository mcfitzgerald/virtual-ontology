Usage Examples
==============

This section provides comprehensive examples of using the Virtual Ontology Twin Model in real-world scenarios.

Production Simulation
---------------------

End-to-End Production Line
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin_model import OntologyDrivenModelBuilder
   from pathlib import Path
   import simpy
   import pandas as pd
   
   class ProductionSimulation:
       def __init__(self, ontology_path: Path, manifest_dir: Path):
           self.builder = OntologyDrivenModelBuilder(ontology_path, manifest_dir)
           self.env = None
           self.model = None
           self.results = []
       
       def setup(self, seed=42):
           """Setup simulation environment"""
           self.env = simpy.Environment()
           self.model = self.builder.build_model(self.env)
           
           # Set random seed for reproducibility
           import random
           random.seed(seed)
           
       def run(self, duration=1440):  # Default 24 hours
           """Run simulation"""
           print(f"Starting simulation for {duration} time units...")
           
           # Start all processes
           self.model.start_processes()
           
           # Run simulation
           self.env.run(until=duration)
           
           print(f"Simulation completed at time {self.env.now}")
           
           # Collect results
           self.results = self.model.get_results()
           return self.results
       
       def analyze_results(self):
           """Analyze simulation results"""
           analysis = {
               'production': self._analyze_production(),
               'equipment': self._analyze_equipment(),
               'quality': self._analyze_quality(),
               'bottlenecks': self._identify_bottlenecks()
           }
           return analysis
       
       def _analyze_production(self):
           """Analyze production metrics"""
           sink_data = self.model.get_sink_data()
           
           return {
               'total_produced': sink_data['total_count'],
               'production_rate': sink_data['total_count'] / self.env.now,
               'good_products': sink_data['good_count'],
               'defect_rate': sink_data['defect_rate'],
               'avg_cycle_time': sink_data['avg_cycle_time']
           }
       
       def _analyze_equipment(self):
           """Analyze equipment performance"""
           equipment_stats = {}
           
           for eq in self.model.get_equipment():
               stats = eq.get_statistics()
               equipment_stats[eq.name] = {
                   'utilization': stats['utilization'],
                   'availability': stats['availability'],
                   'mtbf': stats.get('mtbf', 0),
                   'mttr': stats.get('mttr', 0),
                   'items_processed': stats['items_processed']
               }
           
           return equipment_stats
       
       def _identify_bottlenecks(self):
           """Identify production bottlenecks"""
           bottlenecks = []
           
           for buffer in self.model.get_buffers():
               stats = buffer.get_statistics()
               
               if stats['avg_utilization'] > 0.8:
                   bottlenecks.append({
                       'location': buffer.name,
                       'severity': 'high' if stats['avg_utilization'] > 0.9 else 'medium',
                       'avg_utilization': stats['avg_utilization'],
                       'max_level': stats['max_level'],
                       'overflow_count': stats.get('overflow_count', 0)
                   })
           
           return bottlenecks
   
   # Usage
   sim = ProductionSimulation(
       ontology_path=Path("ontology/twin_ontology.yaml"),
       manifest_dir=Path("manifests/")
   )
   
   sim.setup(seed=42)
   results = sim.run(duration=2880)  # 48 hours
   analysis = sim.analyze_results()
   
   print(f"Total Production: {analysis['production']['total_produced']}")
   print(f"Defect Rate: {analysis['production']['defect_rate']:.2%}")
   print(f"Bottlenecks Found: {len(analysis['bottlenecks'])}")

Scenario Testing
----------------

A/B Testing Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin_model import OntologyDrivenModelBuilder
   import numpy as np
   import matplotlib.pyplot as plt
   
   class ScenarioTester:
       def __init__(self, base_ontology: Path, base_manifests: Path):
           self.base_ontology = base_ontology
           self.base_manifests = base_manifests
           self.results = {}
       
       def test_scenario(self, name: str, modifications: dict, 
                        replications: int = 10):
           """Test a scenario with modifications"""
           
           scenario_results = []
           
           for rep in range(replications):
               # Create builder with modifications
               builder = self._create_modified_builder(modifications)
               
               # Run simulation
               env = simpy.Environment()
               model = builder.build_model(env)
               model.start_processes()
               env.run(until=1440)
               
               # Collect results
               results = model.get_results()
               scenario_results.append(results)
           
           # Store aggregated results
           self.results[name] = self._aggregate_results(scenario_results)
           
           return self.results[name]
       
       def _create_modified_builder(self, modifications: dict):
           """Create builder with modified parameters"""
           builder = OntologyDrivenModelBuilder(
               self.base_ontology, 
               self.base_manifests
           )
           
           # Apply modifications
           for path, value in modifications.items():
               builder.override_parameter(path, value)
           
           return builder
       
       def _aggregate_results(self, results: list):
           """Aggregate results from multiple replications"""
           
           # Extract KPIs
           oee_values = [r['kpi_summary']['oee'] for r in results]
           production_values = [r['production']['total'] for r in results]
           
           return {
               'oee': {
                   'mean': np.mean(oee_values),
                   'std': np.std(oee_values),
                   'ci_95': np.percentile(oee_values, [2.5, 97.5])
               },
               'production': {
                   'mean': np.mean(production_values),
                   'std': np.std(production_values),
                   'ci_95': np.percentile(production_values, [2.5, 97.5])
               }
           }
       
       def compare_scenarios(self):
           """Compare all tested scenarios"""
           
           # Create comparison plot
           fig, axes = plt.subplots(1, 2, figsize=(12, 5))
           
           # OEE Comparison
           scenarios = list(self.results.keys())
           oee_means = [self.results[s]['oee']['mean'] for s in scenarios]
           oee_stds = [self.results[s]['oee']['std'] for s in scenarios]
           
           axes[0].bar(scenarios, oee_means, yerr=oee_stds, capsize=5)
           axes[0].set_ylabel('OEE (%)')
           axes[0].set_title('OEE Comparison')
           axes[0].grid(True, alpha=0.3)
           
           # Production Comparison
           prod_means = [self.results[s]['production']['mean'] for s in scenarios]
           prod_stds = [self.results[s]['production']['std'] for s in scenarios]
           
           axes[1].bar(scenarios, prod_means, yerr=prod_stds, capsize=5)
           axes[1].set_ylabel('Production (units)')
           axes[1].set_title('Production Comparison')
           axes[1].grid(True, alpha=0.3)
           
           plt.tight_layout()
           return fig
   
   # Usage
   tester = ScenarioTester(
       base_ontology=Path("ontology/twin_ontology.yaml"),
       base_manifests=Path("manifests/")
   )
   
   # Test baseline
   tester.test_scenario("Baseline", {}, replications=20)
   
   # Test improved processing
   tester.test_scenario("Fast Processing", {
       "Equipment1.processing_time": 4.0,
       "Equipment2.processing_time": 2.5
   }, replications=20)
   
   # Test increased buffer
   tester.test_scenario("Large Buffers", {
       "Buffer1.capacity": 100,
       "Buffer2.capacity": 80
   }, replications=20)
   
   # Compare results
   fig = tester.compare_scenarios()
   plt.show()

Optimization Studies
--------------------

Parameter Optimization
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from scipy.optimize import differential_evolution
   from twin_model import OntologyDrivenModelBuilder
   
   class ParameterOptimizer:
       def __init__(self, ontology_path: Path, manifest_dir: Path):
           self.ontology_path = ontology_path
           self.manifest_dir = manifest_dir
           self.best_params = None
           self.best_score = None
       
       def objective_function(self, params):
           """Objective function to minimize (negative OEE)"""
           
           # Map parameters
           param_dict = {
               "Equipment1.processing_time": params[0],
               "Equipment2.processing_time": params[1],
               "Buffer1.capacity": int(params[2]),
               "Buffer2.capacity": int(params[3])
           }
           
           # Run simulation
           builder = OntologyDrivenModelBuilder(
               self.ontology_path,
               self.manifest_dir
           )
           
           for path, value in param_dict.items():
               builder.override_parameter(path, value)
           
           env = simpy.Environment()
           model = builder.build_model(env)
           model.start_processes()
           env.run(until=1440)
           
           # Get OEE (we want to maximize, so return negative)
           results = model.get_results()
           oee = results['kpi_summary']['oee']
           
           # Add penalty for constraint violations
           penalty = 0
           if results['bottlenecks']:
               penalty = len(results['bottlenecks']) * 5
           
           return -(oee - penalty)
       
       def optimize(self, bounds):
           """Run optimization"""
           
           result = differential_evolution(
               self.objective_function,
               bounds=bounds,
               maxiter=50,
               popsize=15,
               seed=42
           )
           
           self.best_params = result.x
           self.best_score = -result.fun
           
           return {
               "Equipment1.processing_time": self.best_params[0],
               "Equipment2.processing_time": self.best_params[1],
               "Buffer1.capacity": int(self.best_params[2]),
               "Buffer2.capacity": int(self.best_params[3]),
               "best_oee": self.best_score
           }
   
   # Usage
   optimizer = ParameterOptimizer(
       ontology_path=Path("ontology/twin_ontology.yaml"),
       manifest_dir=Path("manifests/")
   )
   
   # Define parameter bounds
   bounds = [
       (3.0, 7.0),    # Equipment1 processing time
       (2.0, 5.0),    # Equipment2 processing time
       (20, 100),     # Buffer1 capacity
       (20, 100)      # Buffer2 capacity
   ]
   
   optimal_params = optimizer.optimize(bounds)
   print(f"Optimal parameters found:")
   print(f"  Equipment1 processing: {optimal_params['Equipment1.processing_time']:.2f}")
   print(f"  Equipment2 processing: {optimal_params['Equipment2.processing_time']:.2f}")
   print(f"  Buffer1 capacity: {optimal_params['Buffer1.capacity']}")
   print(f"  Buffer2 capacity: {optimal_params['Buffer2.capacity']}")
   print(f"  Best OEE: {optimal_params['best_oee']:.1f}%")

Real-time Integration
---------------------

Live Data Streaming
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   import json
   from datetime import datetime
   from twin_model import OntologyDrivenModelBuilder
   
   class RealTimeSimulation:
       def __init__(self, ontology_path: Path, manifest_dir: Path):
           self.builder = OntologyDrivenModelBuilder(ontology_path, manifest_dir)
           self.env = None
           self.model = None
           self.streaming = False
           self.clients = []
       
       async def start_simulation(self):
           """Start real-time simulation"""
           self.env = simpy.Environment()
           self.model = self.builder.build_model(self.env)
           self.model.start_processes()
           
           self.streaming = True
           
           # Run simulation in steps
           while self.streaming and self.env.now < 10000:
               # Run for 1 time unit
               self.env.run(until=self.env.now + 1)
               
               # Broadcast updates
               await self.broadcast_update()
               
               # Real-time delay (adjust for speed)
               await asyncio.sleep(0.1)
       
       async def broadcast_update(self):
           """Broadcast current state to clients"""
           
           update = {
               "timestamp": datetime.now().isoformat(),
               "simulation_time": self.env.now,
               "kpis": self.model.get_current_kpis(),
               "equipment_states": self._get_equipment_states(),
               "buffer_levels": self._get_buffer_levels(),
               "production": self.model.get_production_count()
           }
           
           message = json.dumps(update)
           
           # Send to all connected clients
           for client in self.clients:
               await client.send(message)
       
       def _get_equipment_states(self):
           """Get current equipment states"""
           states = {}
           for eq in self.model.get_equipment():
               states[eq.name] = {
                   "state": eq.state,
                   "utilization": eq.get_utilization()
               }
           return states
       
       def _get_buffer_levels(self):
           """Get current buffer levels"""
           levels = {}
           for buffer in self.model.get_buffers():
               levels[buffer.name] = {
                   "level": buffer.get_level(),
                   "capacity": buffer.capacity,
                   "utilization": buffer.get_utilization()
               }
           return levels
       
       async def handle_client(self, websocket, path):
           """Handle WebSocket client connection"""
           self.clients.append(websocket)
           
           try:
               async for message in websocket:
                   # Handle client commands
                   command = json.loads(message)
                   
                   if command['action'] == 'pause':
                       self.streaming = False
                   elif command['action'] == 'resume':
                       self.streaming = True
                   elif command['action'] == 'modify':
                       self._modify_parameter(
                           command['parameter'],
                           command['value']
                       )
           finally:
               self.clients.remove(websocket)
       
       def _modify_parameter(self, parameter: str, value):
           """Modify simulation parameter at runtime"""
           # Parse parameter path
           parts = parameter.split('.')
           primitive_name = parts[0]
           param_name = parts[1]
           
           # Find and update primitive
           primitive = self.model.get_primitive(primitive_name)
           if primitive and hasattr(primitive, param_name):
               setattr(primitive, param_name, value)
               print(f"Updated {parameter} to {value}")

Digital Twin Synchronization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from database import TwinDatabaseIntegration
   
   class DigitalTwinSync:
       def __init__(self, model, database_integration):
           self.model = model
           self.db = database_integration
           self.sync_interval = 10  # Sync every 10 time units
           self.last_sync = 0
       
       def sync_process(self):
           """Process to sync twin with database"""
           while True:
               # Wait for sync interval
               yield self.model.env.timeout(self.sync_interval)
               
               # Sync state
               self.sync_state()
               
               # Sync metrics
               self.sync_metrics()
               
               # Check for parameter updates
               self.check_updates()
               
               self.last_sync = self.model.env.now
       
       def sync_state(self):
           """Sync current state to database"""
           
           state = {
               "timestamp": self.model.env.now,
               "equipment": {},
               "buffers": {},
               "production": {}
           }
           
           # Collect equipment state
           for eq in self.model.get_equipment():
               state["equipment"][eq.name] = {
                   "state": eq.state,
                   "items_processed": eq.items_processed,
                   "failures": eq.failure_count
               }
           
           # Collect buffer state
           for buffer in self.model.get_buffers():
               state["buffers"][buffer.name] = {
                   "level": buffer.get_level(),
                   "total_throughput": buffer.total_items
               }
           
           # Store in database
           self.db.store_twin_state(state)
       
       def sync_metrics(self):
           """Sync KPI metrics to database"""
           
           metrics = self.model.get_kpi_metrics()
           
           self.db.store_metrics(
               timestamp=self.model.env.now,
               metrics=metrics
           )
       
       def check_updates(self):
           """Check for parameter updates from database"""
           
           updates = self.db.get_parameter_updates(
               since=self.last_sync
           )
           
           for update in updates:
               self.model.update_parameter(
                   update['parameter'],
                   update['value']
               )
               print(f"Applied update: {update['parameter']} = {update['value']}")

Pattern Discovery
-----------------

Event Pattern Mining
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.transduction import MESTransducer
   import pandas as pd
   from sklearn.cluster import DBSCAN
   
   class PatternDiscovery:
       def __init__(self, model):
           self.model = model
           self.transducer = MESTransducer()
           self.patterns = []
       
       def discover_patterns(self):
           """Discover patterns in simulation data"""
           
           # Get event log
           events = self.model.get_event_log()
           
           # Convert to DataFrame
           df = pd.DataFrame(events)
           
           # Discover different pattern types
           self.patterns.extend(self._find_temporal_patterns(df))
           self.patterns.extend(self._find_cascade_patterns(df))
           self.patterns.extend(self._find_quality_patterns(df))
           
           return self.patterns
       
       def _find_temporal_patterns(self, df):
           """Find temporal patterns in events"""
           patterns = []
           
           # Group events by equipment
           for equipment, group in df.groupby('primitive'):
               # Calculate inter-event times
               group = group.sort_values('time')
               group['inter_event'] = group['time'].diff()
               
               # Cluster inter-event times
               if len(group) > 10:
                   X = group['inter_event'].dropna().values.reshape(-1, 1)
                   clustering = DBSCAN(eps=0.5, min_samples=5).fit(X)
                   
                   # Identify pattern clusters
                   unique_labels = set(clustering.labels_) - {-1}
                   
                   for label in unique_labels:
                       cluster_points = X[clustering.labels_ == label]
                       
                       pattern = {
                           'type': 'temporal',
                           'equipment': equipment,
                           'mean_interval': np.mean(cluster_points),
                           'std_interval': np.std(cluster_points),
                           'frequency': len(cluster_points) / len(X)
                       }
                       patterns.append(pattern)
           
           return patterns
       
       def _find_cascade_patterns(self, df):
           """Find cascade failure patterns"""
           patterns = []
           
           # Look for failure cascades
           failures = df[df['event'] == 'failure'].sort_values('time')
           
           # Identify cascades (failures within short time window)
           cascade_window = 10  # Time units
           
           cascades = []
           current_cascade = []
           
           for _, failure in failures.iterrows():
               if current_cascade and \
                  failure['time'] - current_cascade[-1]['time'] > cascade_window:
                   # End of cascade
                   if len(current_cascade) > 1:
                       cascades.append(current_cascade)
                   current_cascade = [failure.to_dict()]
               else:
                   current_cascade.append(failure.to_dict())
           
           # Analyze cascades
           for cascade in cascades:
               pattern = {
                   'type': 'cascade',
                   'length': len(cascade),
                   'duration': cascade[-1]['time'] - cascade[0]['time'],
                   'equipment_sequence': [e['primitive'] for e in cascade],
                   'trigger': cascade[0]['primitive']
               }
               patterns.append(pattern)
           
           return patterns