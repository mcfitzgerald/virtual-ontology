Simulation Primitives
=====================

The twin model provides six core primitive types that serve as building blocks for constructing complex manufacturing simulations.

Base Primitive
--------------

All primitives inherit from :class:`twin_model.primitives.BasePrimitive`:

.. code-block:: python

   from twin_model.primitives import BasePrimitive, PrimitiveConfig
   
   class BasePrimitive:
       """Base class for all simulation primitives"""
       
       def __init__(self, env: simpy.Environment, name: str, config: PrimitiveConfig):
           self.env = env
           self.name = name
           self.config = config
           self.state = "idle"
           self.event_log = []
       
       def log_event(self, event_type: str, data: dict):
           """Log an event for pattern discovery"""
           pass
       
       def get_state(self) -> dict:
           """Get current primitive state"""
           pass

Equipment Primitive
-------------------

Models production equipment with processing capabilities and failure modes.

Configuration
~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import EquipmentPrimitive, EquipmentState
   
   equipment = EquipmentPrimitive(
       env=env,
       name="Assembly1",
       processing_time=5.0,      # Time to process one item
       failure_rate=0.01,        # Probability of failure per item
       mttr=30.0,                # Mean time to repair
       mtbf=1000.0,              # Mean time between failures
       capacity_per_hour=100,    # Theoretical maximum throughput
       quality_rate=0.98         # Percentage of good items
   )

States
~~~~~~

Equipment can be in one of four states:

* **IDLE**: Waiting for items to process
* **PROCESSING**: Actively processing an item
* **MAINTENANCE**: Scheduled or unscheduled maintenance
* **FAILED**: Equipment failure requiring repair

.. code-block:: python

   from twin_model.primitives import EquipmentState
   
   # Check equipment state
   if equipment.state == EquipmentState.PROCESSING:
       print(f"{equipment.name} is processing")
   
   # State transitions trigger events
   equipment.on_state_change = lambda old, new: 
       print(f"State changed: {old} -> {new}")

Processing Logic
~~~~~~~~~~~~~~~~

.. code-block:: python

   class CustomEquipment(EquipmentPrimitive):
       def process_item(self, item):
           """Custom processing logic"""
           # Pre-processing
           self.state = EquipmentState.PROCESSING
           self.log_event("processing_start", {"item": item.id})
           
           # Processing time with variability
           process_time = random.normalvariate(
               self.processing_time, 
               self.processing_time * 0.1
           )
           yield self.env.timeout(process_time)
           
           # Quality check
           if random.random() < self.quality_rate:
               item.quality = "good"
           else:
               item.quality = "defect"
           
           # Post-processing
           self.state = EquipmentState.IDLE
           self.log_event("processing_complete", {
               "item": item.id,
               "quality": item.quality,
               "duration": process_time
           })
           
           return item

Buffer Primitive
----------------

Manages work-in-progress inventory with configurable capacity and policies.

Configuration
~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import BufferPrimitive, BufferItem
   
   buffer = BufferPrimitive(
       env=env,
       name="Buffer1",
       capacity=50,              # Maximum items
       initial_level=10,         # Starting inventory
       policy="FIFO",            # FIFO or LIFO
       warning_level=40,         # Trigger warning when exceeded
       critical_level=45         # Trigger critical alert
   )

Buffer Operations
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Add item to buffer
   item = BufferItem(id="Product_123", type="PartA")
   success = buffer.put(item)
   
   if not success:
       print(f"Buffer {buffer.name} is full!")
   
   # Get item from buffer
   item = buffer.get()
   if item is None:
       print(f"Buffer {buffer.name} is empty!")
   
   # Check buffer status
   level = buffer.get_level()
   utilization = buffer.get_utilization()
   print(f"Buffer at {utilization:.1%} capacity ({level}/{buffer.capacity})")

Event Monitoring
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Monitor buffer events
   buffer.on_item_added = lambda item: 
       print(f"Item {item.id} added to {buffer.name}")
   
   buffer.on_item_removed = lambda item:
       print(f"Item {item.id} removed from {buffer.name}")
   
   buffer.on_threshold_exceeded = lambda level:
       print(f"WARNING: Buffer at {level} items!")

Source Primitive
----------------

Generates items according to specified arrival patterns.

Configuration
~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import SourcePrimitive, ArrivalPattern
   
   source = SourcePrimitive(
       env=env,
       name="Source1",
       arrival_pattern=ArrivalPattern.EXPONENTIAL,
       arrival_rate=10.0,       # Items per time unit
       batch_size=1,             # Items per arrival
       item_type="RawMaterial",
       max_items=1000           # Stop after generating max_items
   )

Arrival Patterns
~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import ArrivalPattern
   
   # Constant inter-arrival time
   source_constant = SourcePrimitive(
       env, "ConstantSource",
       arrival_pattern=ArrivalPattern.CONSTANT,
       arrival_rate=5.0  # Exactly 5 time units between arrivals
   )
   
   # Exponential distribution (Poisson process)
   source_exp = SourcePrimitive(
       env, "PoissonSource",
       arrival_pattern=ArrivalPattern.EXPONENTIAL,
       arrival_rate=10.0  # Average 10 arrivals per time unit
   )
   
   # Normal distribution
   source_normal = SourcePrimitive(
       env, "NormalSource",
       arrival_pattern=ArrivalPattern.NORMAL,
       arrival_rate=8.0,  # Mean inter-arrival time
       arrival_std=2.0    # Standard deviation
   )

Custom Generation
~~~~~~~~~~~~~~~~~

.. code-block:: python

   class CustomSource(SourcePrimitive):
       def generate_items(self):
           """Custom item generation logic"""
           item_count = 0
           
           while item_count < self.max_items:
               # Custom arrival logic
               if self.env.now < 480:  # First shift
                   interval = random.expovariate(1/3)
               else:  # Second shift
                   interval = random.expovariate(1/5)
               
               yield self.env.timeout(interval)
               
               # Create custom item
               item = BufferItem(
                   id=f"Item_{item_count}",
                   type=self.item_type,
                   priority=random.choice([1, 2, 3]),
                   metadata={"created_at": self.env.now}
               )
               
               # Send to output
               self.output.put(item)
               item_count += 1
               
               self.log_event("item_generated", {
                   "item": item.id,
                   "priority": item.priority
               })

Sink Primitive
--------------

Collects finished products and calculates production metrics.

Configuration
~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import SinkPrimitive, CollectedProduct
   
   sink = SinkPrimitive(
       env=env,
       name="Sink1",
       collect_stats=True,       # Enable statistics collection
       quality_threshold=0.95,   # Minimum quality for good products
       batch_collection=False,   # Collect in batches
       batch_size=10            # Items per batch (if batch_collection=True)
   )

Product Collection
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Sink automatically collects items
   # Access collected products
   products = sink.get_collected_products()
   
   for product in products:
       print(f"Product {product.id}: Quality={product.quality}")
   
   # Get production statistics
   stats = sink.get_statistics()
   print(f"Total produced: {stats['total_count']}")
   print(f"Good products: {stats['good_count']}")
   print(f"Defect rate: {stats['defect_rate']:.2%}")
   print(f"Average cycle time: {stats['avg_cycle_time']:.2f}")

Quality Metrics
~~~~~~~~~~~~~~~

.. code-block:: python

   class QualitySink(SinkPrimitive):
       def assess_quality(self, item):
           """Custom quality assessment"""
           # Multiple quality checks
           checks = {
               "dimension": random.random() > 0.02,
               "surface": random.random() > 0.01,
               "functionality": random.random() > 0.005
           }
           
           # Overall quality
           if all(checks.values()):
               item.quality = "good"
               item.grade = "A"
           elif sum(checks.values()) >= 2:
               item.quality = "good"
               item.grade = "B"
           else:
               item.quality = "defect"
               item.grade = "F"
           
           self.log_event("quality_assessment", {
               "item": item.id,
               "checks": checks,
               "grade": item.grade
           })
           
           return item

Scheduler Primitive
-------------------

Manages production orders and maintenance schedules.

Configuration
~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import (
       SchedulerPrimitive,
       ProductionOrder,
       ScheduleEvent,
       ScheduleEventType
   )
   
   scheduler = SchedulerPrimitive(
       env=env,
       name="Scheduler1",
       planning_horizon=1440,    # Plan for next 1440 time units
       optimization_interval=60  # Re-optimize every 60 time units
   )

Production Orders
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create production order
   order = ProductionOrder(
       id="PO_001",
       product_type="ProductA",
       quantity=100,
       due_date=500,
       priority=1,
       equipment_required=["Equipment1", "Equipment2"]
   )
   
   # Add to scheduler
   scheduler.add_order(order)
   
   # Schedule orders
   schedule = scheduler.create_schedule()
   
   for event in schedule:
       print(f"{event.time}: {event.type} - {event.description}")

Maintenance Scheduling
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Schedule preventive maintenance
   maintenance_event = ScheduleEvent(
       type=ScheduleEventType.MAINTENANCE,
       time=720,  # Schedule at time 720
       duration=60,
       equipment="Equipment1",
       description="Preventive maintenance"
   )
   
   scheduler.add_event(maintenance_event)
   
   # Dynamic rescheduling on equipment failure
   def on_equipment_failure(equipment):
       scheduler.add_event(ScheduleEvent(
           type=ScheduleEventType.REPAIR,
           time=env.now,
           duration=30,
           equipment=equipment.name,
           description="Emergency repair"
       ))
       scheduler.reschedule()

Monitor Primitive
-----------------

Tracks KPIs and generates performance metrics.

Configuration
~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import MonitorPrimitive, KPIType, KPIMetric
   
   monitor = MonitorPrimitive(
       env=env,
       name="Monitor1",
       update_interval=10,       # Update metrics every 10 time units
       rolling_window=100,       # Calculate rolling averages over 100 units
       kpi_targets={
           KPIType.OEE: 85.0,
           KPIType.AVAILABILITY: 90.0,
           KPIType.PERFORMANCE: 95.0,
           KPIType.QUALITY: 98.0
       }
   )

KPI Tracking
~~~~~~~~~~~~

.. code-block:: python

   # Register equipment to monitor
   monitor.register_equipment(equipment1)
   monitor.register_equipment(equipment2)
   
   # Start monitoring
   env.process(monitor.track_metrics())
   
   # Get current KPIs
   kpis = monitor.get_current_kpis()
   print(f"Current OEE: {kpis[KPIType.OEE]:.1f}%")
   
   # Get historical data
   history = monitor.get_kpi_history()
   for timestamp, metrics in history:
       print(f"{timestamp}: OEE={metrics[KPIType.OEE]:.1f}%")

Custom Metrics
~~~~~~~~~~~~~~

.. code-block:: python

   class CustomMonitor(MonitorPrimitive):
       def calculate_custom_metric(self):
           """Calculate custom KPI"""
           # Energy efficiency metric
           total_energy = sum(
               eq.energy_consumed 
               for eq in self.equipment_list
           )
           total_production = sum(
               eq.items_produced 
               for eq in self.equipment_list
           )
           
           energy_efficiency = total_production / total_energy if total_energy > 0 else 0
           
           # Add to metrics
           self.custom_metrics["energy_efficiency"] = energy_efficiency
           
           # Check against target
           if energy_efficiency < self.targets.get("energy_efficiency", 1.0):
               self.raise_alert("Low energy efficiency", severity="warning")
       
       def raise_alert(self, message, severity="info"):
           """Raise performance alert"""
           alert = {
               "timestamp": self.env.now,
               "message": message,
               "severity": severity,
               "metrics": self.get_current_kpis()
           }
           self.alerts.append(alert)
           
           # Trigger callback
           if self.on_alert:
               self.on_alert(alert)

Primitive Composition
---------------------

Building Complex Systems
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from twin_model.primitives import *
   
   class ProductionLine:
       """Composite primitive representing a production line"""
       
       def __init__(self, env, name, config):
           self.env = env
           self.name = name
           
           # Create primitives
           self.source = SourcePrimitive(env, f"{name}_Source", **config["source"])
           self.equipment = []
           self.buffers = []
           
           # Build line from config
           for i, eq_config in enumerate(config["equipment"]):
               # Create buffer before equipment
               buffer = BufferPrimitive(
                   env, f"{name}_Buffer_{i}", 
                   **config["buffers"][i]
               )
               self.buffers.append(buffer)
               
               # Create equipment
               equipment = EquipmentPrimitive(
                   env, f"{name}_Equipment_{i}",
                   **eq_config
               )
               self.equipment.append(equipment)
           
           self.sink = SinkPrimitive(env, f"{name}_Sink", **config["sink"])
           
           # Wire connections
           self._connect_primitives()
           
           # Add monitor
           self.monitor = MonitorPrimitive(env, f"{name}_Monitor")
           for eq in self.equipment:
               self.monitor.register_equipment(eq)
       
       def _connect_primitives(self):
           """Connect primitives in sequence"""
           # Source to first buffer
           self.source.set_output(self.buffers[0])
           
           # Connect buffers and equipment
           for i in range(len(self.equipment)):
               self.buffers[i].set_output(self.equipment[i])
               
               if i < len(self.equipment) - 1:
                   self.equipment[i].set_output(self.buffers[i + 1])
               else:
                   self.equipment[i].set_output(self.sink)
       
       def start(self):
           """Start all processes"""
           self.env.process(self.source.generate_items())
           for eq in self.equipment:
               self.env.process(eq.process_items())
           self.env.process(self.monitor.track_metrics())
       
       def get_metrics(self):
           """Get line metrics"""
           return {
               "production": self.sink.get_production_count(),
               "oee": self.monitor.get_average_oee(),
               "buffer_levels": [b.get_level() for b in self.buffers],
               "equipment_states": [eq.state for eq in self.equipment]
           }