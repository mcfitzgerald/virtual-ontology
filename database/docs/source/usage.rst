Usage Examples
==============

This section provides real-world examples of using the Virtual Ontology Database module.

Data Import and Export
----------------------

Importing Historical MES Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   from pathlib import Path
   from database import TwinDatabaseManager
   
   # Initialize manager
   db_manager = TwinDatabaseManager()
   
   # Import from CSV with data validation
   def import_mes_data_with_validation(csv_path: Path):
       # Read and validate data
       df = pd.read_csv(csv_path)
       
       # Data validation
       required_columns = [
           'Timestamp', 'LineID', 'EquipmentID', 
           'OEE_Score', 'GoodUnitsProduced'
       ]
       
       missing_cols = set(required_columns) - set(df.columns)
       if missing_cols:
           raise ValueError(f"Missing required columns: {missing_cols}")
       
       # Clean data
       df['Timestamp'] = pd.to_datetime(df['Timestamp'])
       df['OEE_Score'] = df['OEE_Score'].clip(0, 100)
       
       # Import to database
       db_manager.import_historical_data(csv_path)
       print(f"Imported {len(df)} records")
       
       return df
   
   # Usage
   data = import_mes_data_with_validation(Path("data/mes_data.csv"))

Exporting Data for Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sqlmodel import Session, select
   from database.models import HistoricalMESData
   import pandas as pd
   
   def export_oee_analysis(db_manager, output_path: Path):
       with Session(db_manager.engine) as session:
           # Query data
           statement = select(HistoricalMESData).where(
               HistoricalMESData.oee_score > 0
           )
           results = session.exec(statement).all()
           
           # Convert to DataFrame
           df = pd.DataFrame([r.dict() for r in results])
           
           # Calculate statistics
           stats = df.groupby('equipment_id').agg({
               'oee_score': ['mean', 'std', 'min', 'max'],
               'good_units_produced': 'sum',
               'scrap_units_produced': 'sum'
           })
           
           # Export
           stats.to_csv(output_path)
           print(f"Exported analysis to {output_path}")
           
           return stats

Simulation Integration
----------------------

Storing Simulation Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from database.integration import TwinDatabaseIntegration
   from datetime import datetime
   import json
   
   class SimulationRecorder:
       def __init__(self):
           self.db = TwinDatabaseIntegration()
           self.experiment_id = None
       
       def start_experiment(self, name: str, description: str):
           """Start a new experiment run"""
           self.experiment_id = self.db.create_experiment(
               name=name,
               description=description,
               metadata={
                   "start_time": datetime.now().isoformat(),
                   "version": "2.0.0"
               }
           )
           return self.experiment_id
       
       def record_simulation(self, parameters: dict, results: dict):
           """Record a single simulation run"""
           run_id = self.db.store_simulation_run(
               experiment_id=self.experiment_id,
               parameters=parameters,
               results=results,
               metadata={
                   "timestamp": datetime.now().isoformat(),
                   "duration": results.get("simulation_time", 0)
               }
           )
           
           # Store KPI metrics
           kpis = results.get("kpi_metrics", {})
           self.db.store_kpi_metrics(run_id, kpis)
           
           return run_id
       
       def finalize_experiment(self):
           """Finalize the experiment with summary statistics"""
           if self.experiment_id:
               self.db.update_experiment(
                   self.experiment_id,
                   metadata={
                       "end_time": datetime.now().isoformat(),
                       "status": "completed"
                   }
               )

Comparative Analysis
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from database.integration import TwinDatabaseIntegration
   import pandas as pd
   import matplotlib.pyplot as plt
   
   class SimulationComparator:
       def __init__(self):
           self.db = TwinDatabaseIntegration()
       
       def compare_experiments(self, experiment_names: list):
           """Compare multiple experiments"""
           results = {}
           
           for name in experiment_names:
               runs = self.db.get_experiment_runs(name)
               
               # Extract KPI metrics
               kpis = []
               for run in runs:
                   kpi_data = run.results.get("kpi_metrics", {})
                   kpi_data["run_id"] = run.id
                   kpi_data["parameters"] = run.parameters
                   kpis.append(kpi_data)
               
               results[name] = pd.DataFrame(kpis)
           
           return results
       
       def plot_oee_comparison(self, results: dict):
           """Plot OEE comparison across experiments"""
           fig, ax = plt.subplots(figsize=(10, 6))
           
           for name, df in results.items():
               if 'oee' in df.columns:
                   ax.plot(df.index, df['oee'], 
                          label=name, marker='o')
           
           ax.set_xlabel('Run Number')
           ax.set_ylabel('OEE (%)')
           ax.set_title('OEE Comparison Across Experiments')
           ax.legend()
           ax.grid(True, alpha=0.3)
           
           return fig

Pattern Discovery
-----------------

Bottleneck Detection
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from database.models import HistoricalMESData, DiscoveredPattern
   from sqlmodel import Session, select
   from typing import List, Dict
   import numpy as np
   
   class BottleneckDetector:
       def __init__(self, db_manager):
           self.db_manager = db_manager
       
       def detect_equipment_bottlenecks(self, 
                                       threshold: float = 0.7) -> List[Dict]:
           """Detect equipment that are bottlenecks"""
           with Session(self.db_manager.engine) as session:
               # Query equipment performance
               statement = select(HistoricalMESData)
               data = session.exec(statement).all()
               
               # Group by equipment
               equipment_stats = {}
               for record in data:
                   eq_id = record.equipment_id
                   if eq_id not in equipment_stats:
                       equipment_stats[eq_id] = []
                   
                   equipment_stats[eq_id].append({
                       'availability': record.availability_score,
                       'performance': record.performance_score,
                       'downtime': record.downtime_reason
                   })
               
               # Identify bottlenecks
               bottlenecks = []
               for eq_id, stats in equipment_stats.items():
                   availability_scores = [s['availability'] for s in stats]
                   mean_availability = np.mean(availability_scores)
                   
                   if mean_availability < threshold * 100:
                       bottleneck = {
                           'equipment_id': eq_id,
                           'mean_availability': mean_availability,
                           'frequency': len(stats),
                           'common_downtime': self._most_common_downtime(stats)
                       }
                       bottlenecks.append(bottleneck)
                       
                       # Store as discovered pattern
                       self._store_pattern(session, bottleneck)
               
               session.commit()
               return bottlenecks
       
       def _most_common_downtime(self, stats: List[Dict]) -> str:
           """Find most common downtime reason"""
           reasons = [s['downtime'] for s in stats if s['downtime']]
           if not reasons:
               return "Unknown"
           return max(set(reasons), key=reasons.count)
       
       def _store_pattern(self, session: Session, bottleneck: Dict):
           """Store discovered bottleneck pattern"""
           pattern = DiscoveredPattern(
               pattern_type="bottleneck",
               description=f"Equipment {bottleneck['equipment_id']} bottleneck",
               confidence=1 - (bottleneck['mean_availability'] / 100),
               support=bottleneck['frequency'],
               metadata=bottleneck
           )
           session.add(pattern)

Production Optimization
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from database.integration import TwinDatabaseIntegration
   from typing import Dict, List, Tuple
   import pandas as pd
   from scipy import optimize
   
   class ProductionOptimizer:
       def __init__(self):
           self.db = TwinDatabaseIntegration()
       
       def find_optimal_parameters(self, 
                                  target_metric: str = "oee") -> Dict:
           """Find optimal production parameters"""
           # Get historical data
           runs = self.db.get_all_simulation_runs()
           
           # Create parameter-result mapping
           data = []
           for run in runs:
               params = run.parameters
               results = run.results.get("kpi_metrics", {})
               
               if target_metric in results:
                   data.append({
                       **params,
                       target_metric: results[target_metric]
                   })
           
           df = pd.DataFrame(data)
           
           # Find best performing parameters
           best_idx = df[target_metric].idxmax()
           best_params = df.iloc[best_idx].to_dict()
           
           # Store as pattern
           self.db.store_pattern(
               pattern_type="optimal_parameters",
               description=f"Optimal parameters for {target_metric}",
               confidence=0.95,
               metadata=best_params
           )
           
           return best_params
       
       def sensitivity_analysis(self, 
                               parameter: str,
                               target_metric: str = "oee") -> pd.DataFrame:
           """Analyze parameter sensitivity"""
           runs = self.db.get_all_simulation_runs()
           
           # Extract parameter values and results
           param_values = []
           metric_values = []
           
           for run in runs:
               if parameter in run.parameters:
                   param_values.append(run.parameters[parameter])
                   metric_values.append(
                       run.results.get("kpi_metrics", {}).get(target_metric, 0)
                   )
           
           # Create sensitivity DataFrame
           sensitivity_df = pd.DataFrame({
               parameter: param_values,
               target_metric: metric_values
           })
           
           # Calculate correlation
           correlation = sensitivity_df.corr()[parameter][target_metric]
           
           print(f"Correlation between {parameter} and {target_metric}: {correlation:.3f}")
           
           return sensitivity_df

Real-time Monitoring
--------------------

WebSocket Updates
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import FastAPI, WebSocket
   from database.integration import TwinDatabaseIntegration
   import asyncio
   import json
   
   app = FastAPI()
   db = TwinDatabaseIntegration()
   
   @app.websocket("/ws/monitoring")
   async def websocket_endpoint(websocket: WebSocket):
       await websocket.accept()
       
       try:
           while True:
               # Get latest metrics
               latest_data = db.get_latest_metrics()
               
               # Send to client
               await websocket.send_json({
                   "timestamp": latest_data.timestamp.isoformat(),
                   "oee": latest_data.oee_score,
                   "availability": latest_data.availability_score,
                   "performance": latest_data.performance_score,
                   "quality": latest_data.quality_score,
                   "production": latest_data.good_units_produced
               })
               
               # Wait before next update
               await asyncio.sleep(5)
               
       except Exception as e:
           print(f"WebSocket error: {e}")
       finally:
           await websocket.close()

Dashboard Data Provider
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from database.integration import TwinDatabaseIntegration
   from datetime import datetime, timedelta
   from typing import Dict, List
   
   class DashboardDataProvider:
       def __init__(self):
           self.db = TwinDatabaseIntegration()
       
       def get_dashboard_data(self) -> Dict:
           """Get comprehensive dashboard data"""
           now = datetime.now()
           
           return {
               "current_metrics": self._get_current_metrics(),
               "hourly_trend": self._get_hourly_trend(hours=24),
               "equipment_status": self._get_equipment_status(),
               "production_summary": self._get_production_summary(),
               "alerts": self._get_active_alerts(),
               "patterns": self._get_recent_patterns()
           }
       
       def _get_current_metrics(self) -> Dict:
           """Get current KPI metrics"""
           latest = self.db.get_latest_metrics()
           return {
               "oee": latest.oee_score,
               "availability": latest.availability_score,
               "performance": latest.performance_score,
               "quality": latest.quality_score,
               "timestamp": latest.timestamp.isoformat()
           }
       
       def _get_hourly_trend(self, hours: int = 24) -> List[Dict]:
           """Get hourly trend data"""
           start_time = datetime.now() - timedelta(hours=hours)
           data = self.db.get_metrics_range(start_time, datetime.now())
           
           # Aggregate by hour
           hourly_data = []
           for hour in range(hours):
               hour_start = start_time + timedelta(hours=hour)
               hour_end = hour_start + timedelta(hours=1)
               
               hour_records = [
                   d for d in data 
                   if hour_start <= d.timestamp < hour_end
               ]
               
               if hour_records:
                   hourly_data.append({
                       "hour": hour_start.isoformat(),
                       "oee": np.mean([r.oee_score for r in hour_records]),
                       "production": sum([r.good_units_produced for r in hour_records])
                   })
           
           return hourly_data

Advanced Queries
----------------

Complex Filtering
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sqlmodel import Session, select, and_, or_
   from database.models import HistoricalMESData
   from datetime import datetime, timedelta
   
   def advanced_query_examples(db_manager):
       with Session(db_manager.engine) as session:
           # Multi-condition filtering
           statement = select(HistoricalMESData).where(
               and_(
                   HistoricalMESData.oee_score > 80,
                   HistoricalMESData.equipment_type == "Assembly",
                   or_(
                       HistoricalMESData.downtime_reason.is_(None),
                       HistoricalMESData.downtime_reason == "Scheduled"
                   )
               )
           )
           high_performers = session.exec(statement).all()
           
           # Time-based queries
           last_week = datetime.now() - timedelta(days=7)
           statement = select(HistoricalMESData).where(
               HistoricalMESData.timestamp >= last_week
           ).order_by(HistoricalMESData.timestamp.desc())
           recent_data = session.exec(statement).all()
           
           # Aggregation queries
           from sqlmodel import func
           
           statement = select(
               HistoricalMESData.equipment_id,
               func.avg(HistoricalMESData.oee_score).label("avg_oee"),
               func.count(HistoricalMESData.id).label("record_count")
           ).group_by(
               HistoricalMESData.equipment_id
           ).having(
               func.avg(HistoricalMESData.oee_score) > 75
           )
           
           equipment_stats = session.exec(statement).all()
           
           return {
               "high_performers": high_performers,
               "recent_data": recent_data,
               "equipment_stats": equipment_stats
           }