"""
Comprehensive unit tests for OEE calculations.

Tests the fixes for:
- Runtime inference when units are produced
- Performance calculation with zero runtime
- Status correction when production detected
- Safe division and error handling
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from twin_model.transduction.mes_transducer import MESTransducer


class TestOEECalculations(unittest.TestCase):
    """Test OEE calculation fixes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.transducer = MESTransducer(time_bucket=5)
        
    def test_performance_with_zero_runtime_but_production(self):
        """Test performance calculation when runtime is zero but units produced."""
        metrics = {
            'good_units': 100,
            'scrap_units': 5,
            'runtime_minutes': 0,  # Zero runtime
            'downtime_minutes': 0,
            'product_id': 'PROD-001'  # Add missing product_id
        }
        
        equipment_info = {'base_rate': 60}
        product_info = {'target_rate_units_per_5min': 350}
        
        # Calculate performance - should not raise division by zero
        performance = self.transducer._calculate_performance(
            metrics, equipment_info, product_info
        )
        
        # Performance should be > 0 when units produced
        self.assertGreater(performance, 0, "Performance should be > 0 when units produced")
        self.assertLessEqual(performance, 110, "Performance should be capped at 110%")
        
    def test_performance_with_no_production(self):
        """Test performance calculation with no production."""
        metrics = {
            'good_units': 0,
            'scrap_units': 0,
            'runtime_minutes': 5,
            'downtime_minutes': 0,
            'product_id': 'PROD-001'  # Add missing product_id
        }
        
        equipment_info = {'base_rate': 60}
        product_info = {'target_rate_units_per_5min': 350}
        
        performance = self.transducer._calculate_performance(
            metrics, equipment_info, product_info
        )
        
        # Performance should be 0 with no production
        self.assertEqual(performance, 0, "Performance should be 0 with no production")
        
    def test_runtime_inference_in_generate_records(self):
        """Test that runtime is inferred when units are produced."""
        # Set up bucket metrics with production but no runtime
        self.transducer.bucket_metrics[(0, 'EQ-001')] = {
            'good_units': 50,
            'scrap_units': 2,
            'runtime_minutes': 0,  # No runtime recorded
            'downtime_minutes': 0,
            'last_status': 'Idle',
            'energy_consumption': 0,
            'downtime_reason': None,
            'product_id': 'PROD-001',
            'product_name': 'Product 1',
            'order_id': 'ORD-001'
        }
        
        # Generate MES records
        mes_records = self.transducer._generate_mes_records()
        
        # Verify runtime was inferred
        if mes_records:
            record = mes_records[0]
            # Performance should not be 0 since units were produced
            self.assertNotEqual(
                record.get('Performance_Score', 0), 
                0, 
                "Performance should not be 0 when units produced"
            )
            
    def test_status_correction_with_production(self):
        """Test that status is corrected from Idle to Running when production detected."""
        # Set up bucket metrics with production but Idle status
        bucket_key = (0, 'EQ-002')
        self.transducer.bucket_metrics[bucket_key] = {
            'good_units': 75,  # Production detected
            'scrap_units': 0,
            'runtime_minutes': 0,
            'downtime_minutes': 0,
            'last_status': 'Idle',  # Incorrect status
            'energy_consumption': 0,
            'downtime_reason': None,
            'product_id': 'PROD-001',
            'product_name': 'Product 1',
            'order_id': 'ORD-001'
        }
        
        # Generate MES records
        mes_records = self.transducer._generate_mes_records()
        
        # Verify status was corrected to Running
        # (The fix changes the status internally during generation)
        self.assertEqual(
            self.transducer.bucket_metrics[bucket_key]['last_status'],
            'Running',
            "Status should be corrected to Running when production detected"
        )
        
    def test_availability_calculation(self):
        """Test availability calculation."""
        metrics = {
            'runtime_minutes': 4,
            'downtime_minutes': 1
        }
        
        availability = self.transducer._calculate_availability(metrics)
        
        # Availability = (Total Time - Downtime) / Total Time * 100
        # = (5 - 1) / 5 * 100 = 80%
        self.assertEqual(availability, 80.0, "Availability should be 80%")
        
    def test_quality_calculation(self):
        """Test quality calculation."""
        metrics = {
            'good_units': 95,
            'scrap_units': 5
        }
        
        quality = self.transducer._calculate_quality(metrics)
        
        # Quality = Good Units / Total Units * 100
        # = 95 / 100 * 100 = 95%
        self.assertEqual(quality, 95.0, "Quality should be 95%")
        
    def test_oee_calculation_complete(self):
        """Test complete OEE calculation with all components."""
        # Set up metrics for a complete OEE calculation
        self.transducer.bucket_metrics[(0, 'EQ-003')] = {
            'good_units': 280,
            'scrap_units': 20,
            'runtime_minutes': 4,
            'downtime_minutes': 1,
            'last_status': 'Running',
            'energy_consumption': 10,
            'downtime_reason': None,
            'product_id': 'PROD-001',
            'product_name': 'Product 1',
            'order_id': 'ORD-001'
        }
        
        manifests = {
            'equipment_manifest': {
                'equipment': {
                    'EQ-003': {
                        'base_rate': 60,
                        'equipment_type': 'Filler'
                    }
                }
            },
            'production_manifest': {
                'products': {
                    'PROD-001': {
                        'target_rate_units_per_5min': 350
                    }
                }
            }
        }
        
        # Generate MES records
        mes_records = self.transducer._generate_mes_records(manifests)
        
        self.assertGreater(len(mes_records), 0, "Should generate MES records")
        
        record = mes_records[0]
        
        # Verify OEE components
        self.assertIn('Availability_Score', record)
        self.assertIn('Performance_Score', record)
        self.assertIn('Quality_Score', record)
        self.assertIn('OEE_Score', record)
        
        # OEE should be reasonable (between 0 and 100)
        oee = record['OEE_Score']
        self.assertGreaterEqual(oee, 0, "OEE should be >= 0")
        self.assertLessEqual(oee, 100, "OEE should be <= 100")
        
    def test_performance_calculation_error_handling(self):
        """Test that performance calculation handles errors gracefully."""
        metrics = {
            'good_units': 'invalid',  # Invalid data type
            'scrap_units': 5,
            'runtime_minutes': 5
        }
        
        equipment_info = {'base_rate': 60}
        product_info = {'target_rate_units_per_5min': 350}
        
        # Should handle error and return 0
        performance = self.transducer._calculate_performance(
            metrics, equipment_info, product_info
        )
        
        self.assertEqual(performance, 0.0, "Should return 0 on error")
        
    def test_process_observable_state_tracking(self):
        """Test that state changes are properly tracked."""
        observables = [
            {
                'timestamp': 0,
                'event_type': 'state_change',
                'primitive_type': 'Equipment',
                'primitive_id': 'EQ-001',
                'state': 'IDLE',
                'details': {
                    'old_state': 'STARTUP',
                    'new_state': 'IDLE',
                    'duration_in_old_state': 0
                }
            },
            {
                'timestamp': 1,
                'event_type': 'state_change',
                'primitive_type': 'Equipment',
                'primitive_id': 'EQ-001',
                'state': 'RUNNING',
                'details': {
                    'old_state': 'IDLE',
                    'new_state': 'RUNNING',
                    'duration_in_old_state': 1
                }
            },
            {
                'timestamp': 2,
                'event_type': 'unit_produced',
                'primitive_type': 'Equipment',
                'primitive_id': 'EQ-001',
                'state': 'RUNNING',
                'value': 1
            }
        ]
        
        # Process observables
        df = self.transducer.process_observables(observables)
        
        # Should track state and production
        bucket_key = (0, 'EQ-001')
        self.assertIn(bucket_key, self.transducer.bucket_metrics)
        
        metrics = self.transducer.bucket_metrics[bucket_key]
        self.assertEqual(metrics['good_units'], 1, "Should track production")
        self.assertGreater(metrics['runtime_minutes'], 0, "Should track runtime")


class TestMESTransducerIntegration(unittest.TestCase):
    """Integration tests for MES transducer with simulated data."""
    
    def test_30_minute_simulation_data(self):
        """Test processing of a 30-minute simulation with various events."""
        transducer = MESTransducer(time_bucket=5)
        
        # Create realistic simulation events
        events = []
        timestamp = 0
        
        # Equipment starts idle
        events.append({
            'timestamp': timestamp,
            'event_type': 'state_change',
            'primitive_type': 'Equipment',
            'primitive_id': 'LINE1-FILLER',
            'state': 'IDLE',
            'details': {'new_state': 'IDLE', 'old_state': 'STARTUP'}
        })
        
        # Start production
        timestamp = 1
        events.append({
            'timestamp': timestamp,
            'event_type': 'state_change',
            'primitive_type': 'Equipment',
            'primitive_id': 'LINE1-FILLER',
            'state': 'RUNNING',
            'details': {'new_state': 'RUNNING', 'old_state': 'IDLE'}
        })
        
        # Produce units for 4 minutes
        for i in range(240):  # 60 units/min * 4 min
            timestamp += 1/60
            events.append({
                'timestamp': timestamp,
                'event_type': 'unit_produced',
                'primitive_type': 'Equipment',
                'primitive_id': 'LINE1-FILLER',
                'state': 'RUNNING',
                'value': 1
            })
        
        # Equipment failure
        timestamp = 5
        events.append({
            'timestamp': timestamp,
            'event_type': 'state_change',
            'primitive_type': 'Equipment',
            'primitive_id': 'LINE1-FILLER',
            'state': 'STOPPED_FAILURE',
            'details': {'new_state': 'STOPPED_FAILURE', 'old_state': 'RUNNING'}
        })
        
        # Process events
        df = transducer.process_observables(events)
        
        # Should generate MES records
        self.assertFalse(df.empty, "Should generate MES records")
        
        # First bucket should have production and reasonable OEE
        first_record = df.iloc[0]
        self.assertGreater(first_record['GoodUnitsProduced'], 0, "Should have production")
        self.assertGreater(first_record['OEE_Score'], 0, "Should have non-zero OEE")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)