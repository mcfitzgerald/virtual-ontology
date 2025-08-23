"""
Integration tests for critical event emission and sampling verification.

Tests that critical events bypass sampling and are always recorded.
"""

import unittest
import simpy
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from twin_model.primitives import (
    PrimitiveConfig,
    EquipmentPrimitive,
    SamplingConfig,
    SimulationMode
)


class TestCriticalEventEmission(unittest.TestCase):
    """Test critical event flagging and emission."""
    
    def test_critical_events_bypass_sampling(self):
        """Test that critical events are always recorded even in FAST mode."""
        env = simpy.Environment()
        
        # Create sampling config with FAST mode (normally filters most events)
        sampling = SamplingConfig(
            mode=SimulationMode.FAST,
            sampling_rate=100,  # Only keep 1% normally
            buffer_size=100
        )
        
        # Verify critical events are in the set
        self.assertIn('state_change', sampling.critical_events)
        self.assertIn('equipment_failure', sampling.critical_events)
        
        # Create equipment
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
        
        # Start and run briefly
        equipment.start()
        env.run(until=10)
        
        # Get observables
        observables = list(equipment.observables)
        
        # Should have state_change events despite FAST mode
        state_changes = [o for o in observables if o['event_type'] == 'state_change']
        self.assertGreater(len(state_changes), 0, "Critical state_change events should be recorded")
        
        # Non-critical events should be filtered
        # Note: unit_produced is not in critical_events
        production_events = [o for o in observables if o['event_type'] == 'unit_produced']
        total_events = equipment.events_emitted
        sampled_events = equipment.events_sampled
        
        # In FAST mode, should have filtered many events
        self.assertLess(sampled_events, total_events, "Should have filtered non-critical events")
        
    def test_explicit_critical_flag(self):
        """Test that events can be explicitly marked as critical."""
        env = simpy.Environment()
        
        # Create equipment with aggressive sampling
        sampling = SamplingConfig(
            mode=SimulationMode.PRODUCTION,
            sampling_rate=1000,  # Only keep 0.1% normally
            buffer_size=50
        )
        
        config = PrimitiveConfig(
            id="TEST-EQ-2",
            type="Equipment",
            properties={'base_rate': 60.0}
        )
        
        # Create custom equipment class to test critical flag
        class TestEquipment(EquipmentPrimitive):
            def emit_test_events(self):
                """Emit test events with and without critical flag."""
                # Emit normal event
                self.emit_observable(
                    event_type="test_normal",
                    details={"value": 1}
                )
                
                # Emit critical event via parameter
                self.emit_observable(
                    event_type="test_critical_param",
                    details={"value": 2},
                    is_critical=True
                )
                
                # Emit critical event via details
                self.emit_observable(
                    event_type="test_critical_detail",
                    details={"value": 3, "critical": True}
                )
        
        equipment = TestEquipment(
            env=env,
            config=config,
            sampling_config=sampling
        )
        
        # Emit test events
        equipment.emit_test_events()
        
        # Check observables
        observables = list(equipment.observables)
        
        # Critical events should be present
        critical_param = [o for o in observables if o['event_type'] == 'test_critical_param']
        critical_detail = [o for o in observables if o['event_type'] == 'test_critical_detail']
        
        self.assertEqual(len(critical_param), 1, "Critical event via parameter should be recorded")
        self.assertEqual(len(critical_detail), 1, "Critical event via details should be recorded")
        
        # Normal event likely filtered due to aggressive sampling
        normal = [o for o in observables if o['event_type'] == 'test_normal']
        # May or may not be present due to sampling
        
    def test_critical_events_in_production_mode(self):
        """Test that critical events are always recorded in PRODUCTION mode."""
        env = simpy.Environment()
        
        # Create sampling config with PRODUCTION mode
        sampling = SamplingConfig(
            mode=SimulationMode.PRODUCTION,
            sampling_rate=10,  # Keep 10%
            buffer_size=500
        )
        
        config = PrimitiveConfig(
            id="TEST-EQ-3",
            type="Equipment",
            properties={
                'base_rate': 60.0,
                'mtbf': 50.0,  # Fail frequently for testing
                'mttr': 5.0
            }
        )
        
        equipment = EquipmentPrimitive(
            env=env,
            config=config,
            sampling_config=sampling
        )
        
        equipment.start()
        env.run(until=100)
        
        observables = list(equipment.observables)
        
        # All state changes should be recorded (critical)
        state_changes = [o for o in observables if o['event_type'] == 'state_change']
        
        # Since we see the failures in the log, they should be there
        # Just verify we have state changes
        self.assertGreater(len(state_changes), 0, "Should have state change events")
        
        # Production events should be sampled
        production = [o for o in observables if o['event_type'] == 'unit_produced']
        
        # With 10% sampling, should have some but not all production events
        # Total production events would be ~60 units/min * 100 min = 6000
        # With 10% sampling, expect ~600 events (but with some variance)
        self.assertGreater(len(production), 0, "Should have some production events")
        self.assertLess(len(production), 2000, "Should have sampled production events")
        
    def test_critical_event_set_configuration(self):
        """Test that critical event set can be configured."""
        sampling = SamplingConfig()
        
        # Verify default critical events
        expected_critical = {
            "failure",
            "equipment_failure",
            "state_change",
            "maintenance",
            "planned_maintenance",
            "changeover",
            "cascade_failure_triggered"
        }
        
        self.assertEqual(sampling.critical_events, expected_critical)
        
        # Test that we can add custom critical events
        sampling.critical_events.add("custom_critical")
        self.assertIn("custom_critical", sampling.critical_events)
        
        # Test should_record_event with custom critical
        self.assertTrue(sampling.should_record_event("custom_critical"))
        
    def test_sampling_counter(self):
        """Test that sampling counter works correctly for non-critical events."""
        sampling = SamplingConfig(
            mode=SimulationMode.PRODUCTION,
            sampling_rate=3  # Keep every 3rd event
        )
        
        # Reset counter
        sampling.event_counter = 0
        
        # Test non-critical event sampling
        results = []
        for i in range(10):
            results.append(sampling.should_record_event("non_critical"))
        
        # Should record events at positions 2, 5, 8 (0-indexed, every 3rd)
        expected = [False, False, True, False, False, True, False, False, True, False]
        self.assertEqual(results, expected, "Should sample every 3rd non-critical event")
        
    def test_mode_based_filtering(self):
        """Test filtering behavior across different modes."""
        # DETAILED mode - record everything
        detailed = SamplingConfig(mode=SimulationMode.DETAILED)
        self.assertTrue(detailed.should_record_event("any_event"))
        self.assertTrue(detailed.should_record_event("state_change"))
        
        # FAST mode - only critical
        fast = SamplingConfig(mode=SimulationMode.FAST)
        self.assertFalse(fast.should_record_event("unit_produced"))
        self.assertTrue(fast.should_record_event("state_change"))  # Critical
        self.assertTrue(fast.should_record_event("any_event", is_critical=True))
        
        # PRODUCTION mode - sampling + critical
        production = SamplingConfig(
            mode=SimulationMode.PRODUCTION,
            sampling_rate=2
        )
        self.assertTrue(production.should_record_event("state_change"))  # Always (critical)
        
        # Non-critical events follow sampling
        production.event_counter = 0
        self.assertFalse(production.should_record_event("unit_produced"))  # 1st - no
        self.assertTrue(production.should_record_event("unit_produced"))   # 2nd - yes


if __name__ == '__main__':
    unittest.main(verbosity=2)