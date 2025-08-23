"""
Performance benchmarks for logging and event emission improvements.

This module validates the performance improvements from the logging strategy.
"""

import unittest
import time
import simpy
import sys
from pathlib import Path
from typing import Dict, Any
import gc

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from twin_model.primitives import (
    PrimitiveConfig,
    EquipmentPrimitive,
    SamplingConfig,
    SimulationMode
)
from twin_model.logging_config import SimulationLogger, setup_default_logging


class LoggingPerformanceBenchmark(unittest.TestCase):
    """Benchmark tests for logging and event emission performance."""
    
    @classmethod
    def setUpClass(cls):
        """Setup logging for benchmarks."""
        setup_default_logging(level="WARNING", enable_file=False)
        
    def setUp(self):
        """Reset memory before each benchmark."""
        gc.collect()
        
    def test_mode_performance(self):
        """Verify performance characteristics of different modes."""
        print("\n" + "="*60)
        print("SIMULATION MODE PERFORMANCE TEST")
        print("="*60)
        
        results = {}
        
        for mode in [SimulationMode.DETAILED, SimulationMode.PRODUCTION, SimulationMode.FAST]:
            # Setup
            env = simpy.Environment()
            
            # Create sampling config
            sampling = SamplingConfig(
                mode=mode,
                sampling_rate=10 if mode == SimulationMode.PRODUCTION else 1,
                buffer_size=1000,
                enable_global_observables=False
            )
            
            # Create equipment
            equipment_list = []
            for i in range(5):
                config = PrimitiveConfig(
                    id=f"EQ-{i:03d}",
                    type="Equipment",
                    properties={
                        'base_rate': 60.0,
                        'mtbf': 100.0,
                        'mttr': 10.0
                    }
                )
                eq = EquipmentPrimitive(
                    env=env,
                    config=config,
                    sampling_config=sampling
                )
                eq.start()
                equipment_list.append(eq)
            
            # Run simulation
            start_time = time.perf_counter()
            env.run(until=1440)  # 1 day
            elapsed = time.perf_counter() - start_time
            
            # Collect statistics
            total_events_emitted = sum(eq.events_emitted for eq in equipment_list)
            total_events_sampled = sum(eq.events_sampled for eq in equipment_list)
            total_observables = sum(len(list(eq.observables)) for eq in equipment_list)
            
            results[mode.value] = {
                'elapsed_seconds': elapsed,
                'events_emitted': total_events_emitted,
                'events_sampled': total_events_sampled,
                'observables_stored': total_observables,
                'sampling_efficiency': (total_events_sampled / total_events_emitted * 100) if total_events_emitted > 0 else 0
            }
            
            print(f"\n{mode.value.upper()} Mode:")
            print(f"  Elapsed: {elapsed:.3f}s")
            print(f"  Events Emitted: {total_events_emitted:,}")
            print(f"  Events Sampled: {total_events_sampled:,}")
            print(f"  Observables Stored: {total_observables:,}")
            print(f"  Sampling Efficiency: {results[mode.value]['sampling_efficiency']:.1f}%")
        
        # Verify performance characteristics
        self.assertLess(
            results['fast']['elapsed_seconds'],
            results['detailed']['elapsed_seconds'],
            "FAST mode should be faster than DETAILED"
        )
        
        self.assertLess(
            results['fast']['observables_stored'],
            results['detailed']['observables_stored'],
            "FAST mode should store fewer observables"
        )
        
        # Check sampling efficiency instead of absolute numbers
        self.assertLess(
            results['production']['sampling_efficiency'],
            results['detailed']['sampling_efficiency'],
            "PRODUCTION mode should sample fewer events than DETAILED"
        )
        
        print("\n✓ Performance characteristics verified")
    
    def test_critical_event_preservation(self):
        """Verify critical events are preserved even with aggressive sampling."""
        print("\n" + "="*60)
        print("CRITICAL EVENT PRESERVATION TEST")
        print("="*60)
        
        env = simpy.Environment()
        
        # Very aggressive sampling
        sampling = SamplingConfig(
            mode=SimulationMode.PRODUCTION,
            sampling_rate=1000,  # Only keep 0.1% of events
            buffer_size=500
        )
        
        # Create equipment with frequent failures
        config = PrimitiveConfig(
            id="TEST-EQ",
            type="Equipment",
            properties={
                'base_rate': 60.0,
                'mtbf': 20.0,  # Frequent failures
                'mttr': 5.0
            }
        )
        
        equipment = EquipmentPrimitive(
            env=env,
            config=config,
            sampling_config=sampling
        )
        
        equipment.start()
        env.run(until=1440)  # 1 day
        
        observables = list(equipment.observables)
        
        # Count critical events
        critical_events = [
            o for o in observables 
            if o['event_type'] in ['state_change', 'equipment_failure']
        ]
        
        production_events = [
            o for o in observables
            if o['event_type'] == 'unit_produced'
        ]
        
        print(f"\nTotal events emitted: {equipment.events_emitted:,}")
        print(f"Total events sampled: {equipment.events_sampled:,}")
        print(f"Observables in buffer: {len(observables):,}")
        print(f"Critical events preserved: {len(critical_events)}")
        print(f"Production events sampled: {len(production_events)}")
        
        # Critical events should be present
        self.assertGreater(
            len(critical_events),
            0,
            "Critical events should be preserved despite aggressive sampling"
        )
        
        # Production events should be heavily sampled
        expected_production = equipment.events_emitted * 0.001  # ~0.1% sampling
        self.assertLess(
            len(production_events),
            expected_production * 2,  # Allow some variance
            "Production events should be heavily sampled"
        )
        
        print("✓ Critical events preserved with aggressive sampling")
    
    def test_memory_bounded(self):
        """Verify memory usage is bounded with circular buffers."""
        print("\n" + "="*60)
        print("MEMORY BOUNDEDNESS TEST")
        print("="*60)
        
        buffer_sizes = [100, 500, 1000]
        
        for buffer_size in buffer_sizes:
            env = simpy.Environment()
            
            sampling = SamplingConfig(
                mode=SimulationMode.DETAILED,  # Keep all events
                buffer_size=buffer_size
            )
            
            config = PrimitiveConfig(
                id="TEST-EQ",
                type="Equipment",
                properties={'base_rate': 60.0}
            )
            
            equipment = EquipmentPrimitive(
                env=env,
                config=config,
                sampling_config=sampling
            )
            
            equipment.start()
            env.run(until=1440)  # Generate many events
            
            observables = list(equipment.observables)
            
            print(f"\nBuffer size {buffer_size}:")
            print(f"  Events emitted: {equipment.events_emitted:,}")
            print(f"  Observables stored: {len(observables)}")
            
            # Buffer should not exceed configured size
            self.assertLessEqual(
                len(observables),
                buffer_size,
                f"Buffer should not exceed {buffer_size} events"
            )
        
        print("\n✓ Memory usage bounded by buffer size")
    
    def test_logging_overhead(self):
        """Measure logging overhead."""
        print("\n" + "="*60)
        print("LOGGING OVERHEAD TEST")
        print("="*60)
        
        # Test with logging disabled
        SimulationLogger.setup_logging(
            log_level="CRITICAL",  # Minimal logging
            enable_console=False,
            enable_file=False
        )
        
        env = simpy.Environment()
        sampling = SamplingConfig(mode=SimulationMode.PRODUCTION)
        
        equipment_list = []
        for i in range(10):
            config = PrimitiveConfig(
                id=f"EQ-{i:03d}",
                type="Equipment",
                properties={'base_rate': 60.0}
            )
            eq = EquipmentPrimitive(env=env, config=config, sampling_config=sampling)
            eq.start()
            equipment_list.append(eq)
        
        start = time.perf_counter()
        env.run(until=60)  # 1 hour
        no_logging_time = time.perf_counter() - start
        
        # Test with logging enabled
        SimulationLogger.setup_logging(
            log_level="INFO",
            enable_console=False,
            enable_file=True
        )
        
        env = simpy.Environment()
        equipment_list = []
        for i in range(10):
            config = PrimitiveConfig(
                id=f"EQ-{i:03d}",
                type="Equipment",
                properties={'base_rate': 60.0}
            )
            eq = EquipmentPrimitive(env=env, config=config, sampling_config=sampling)
            eq.start()
            equipment_list.append(eq)
        
        start = time.perf_counter()
        env.run(until=60)
        with_logging_time = time.perf_counter() - start
        
        overhead_percent = ((with_logging_time - no_logging_time) / no_logging_time) * 100
        
        print(f"\nNo logging: {no_logging_time:.3f}s")
        print(f"With logging: {with_logging_time:.3f}s")
        print(f"Overhead: {overhead_percent:.1f}%")
        
        # Logging overhead should be reasonable
        self.assertLess(
            overhead_percent,
            50,  # Less than 50% overhead
            "Logging overhead should be reasonable"
        )
        
        print("✓ Logging overhead is acceptable")


if __name__ == '__main__':
    unittest.main(verbosity=2)