"""
Test basic SimPy functionality and existing twin_model.

Ensures SimPy is installed and working, and tests the existing simulation.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSimPyBasics:
    """Test basic SimPy functionality."""
    
    def test_simpy_installed(self):
        """Test that SimPy is installed."""
        try:
            import simpy
            assert hasattr(simpy, 'Environment')
            assert hasattr(simpy, 'Resource')
            assert hasattr(simpy, 'Container')
        except ImportError:
            pytest.fail("SimPy is not installed. Run: pip install simpy")
    
    def test_simpy_version(self):
        """Check SimPy version."""
        import simpy
        version = simpy.__version__
        print(f"SimPy version: {version}")
        assert version is not None
    
    def test_basic_simulation(self):
        """Test a basic SimPy simulation."""
        import simpy
        
        def process(env, name):
            """Simple process that prints at intervals."""
            results = []
            for i in range(3):
                results.append(f"{name} at {env.now}")
                yield env.timeout(1)
            return results
        
        env = simpy.Environment()
        results = []
        
        # Run process
        proc = env.process(process(env, "Test"))
        env.run()
        
        # Process should have run
        assert env.now == 3
    
    def test_resource_basics(self):
        """Test basic SimPy Resource."""
        import simpy
        
        def user(env, resource, name, results):
            """Process that uses a resource."""
            with resource.request() as req:
                yield req
                results.append(f"{name} got resource at {env.now}")
                yield env.timeout(1)
                results.append(f"{name} released at {env.now}")
        
        env = simpy.Environment()
        resource = simpy.Resource(env, capacity=1)
        results = []
        
        # Two processes compete for resource
        env.process(user(env, resource, "A", results))
        env.process(user(env, resource, "B", results))
        
        env.run()
        
        # Both should have used resource
        assert len(results) == 4
        assert "A got resource" in results[0]
        assert "B got resource" in results[2]  # B waits for A
    
    def test_container_basics(self):
        """Test basic SimPy Container."""
        import simpy
        
        def producer(env, container):
            """Process that puts items in container."""
            for i in range(3):
                yield env.timeout(1)
                yield container.put(10)
        
        def consumer(env, container):
            """Process that gets items from container."""
            while True:
                yield container.get(5)
                yield env.timeout(0.5)
        
        env = simpy.Environment()
        container = simpy.Container(env, capacity=100, init=0)
        
        env.process(producer(env, container))
        env.process(consumer(env, container))
        
        env.run(until=5)
        
        # Container should have items
        assert container.level > 0


class TestExistingTwinModel:
    """Test the existing twin_model module."""
    
    def test_twin_model_imports(self):
        """Test that twin_model can be imported."""
        try:
            from twin_model import SimulationRunner, SimulationConfig
            assert SimulationRunner is not None
            assert SimulationConfig is not None
        except ImportError as e:
            pytest.skip(f"twin_model not importable: {e}")
    
    def test_default_config(self):
        """Test creating default configuration."""
        try:
            from twin_model import SimulationConfig
            
            config = SimulationConfig.create_default_config()
            assert config is not None
            assert hasattr(config, 'line_configs')
            assert len(config.line_configs) > 0
        except ImportError:
            pytest.skip("twin_model not available")
    
    def test_short_simulation(self):
        """Test running a very short simulation."""
        try:
            from twin_model import SimulationRunner
            
            runner = SimulationRunner()
            
            # Run for 1 hour (1/24 day)
            results = runner.run_simulation(
                duration_days=1/24,
                seed=42
            )
            
            # Check results structure
            assert results is not None
            assert hasattr(results, 'duration_minutes')
            assert hasattr(results, 'kpi_summary')
            assert hasattr(results, 'line_summaries')
            assert hasattr(results, 'mes_data')
            
            # Check KPIs
            kpis = results.kpi_summary
            assert 'mean_oee' in kpis
            assert 'total_units_produced' in kpis
            
            # OEE should be between 0 and 100
            assert 0 <= kpis['mean_oee'] <= 100
            
        except ImportError:
            pytest.skip("twin_model not available")
        except Exception as e:
            pytest.fail(f"Simulation failed: {e}")
    
    def test_mes_data_generation(self):
        """Test that MES data is generated correctly."""
        try:
            from twin_model import SimulationRunner
            
            runner = SimulationRunner()
            
            # Run for 30 minutes to get multiple snapshots
            results = runner.run_simulation(
                duration_days=30/1440,  # 30 minutes
                seed=42
            )
            
            # Should have MES snapshots
            assert len(results.mes_data) > 0
            
            # Check first snapshot structure
            first_snapshot = results.mes_data[0]
            assert 'timestamp' in first_snapshot
            assert 'line_id' in first_snapshot
            assert 'equipment_states' in first_snapshot
            assert 'buffer_levels' in first_snapshot
            assert 'production_metrics' in first_snapshot
            
        except ImportError:
            pytest.skip("twin_model not available")
    
    def test_parameter_sensitivity(self):
        """Test that parameters affect simulation."""
        try:
            from twin_model import SimulationRunner, ActionableParameters
            
            runner = SimulationRunner()
            
            # Baseline
            baseline = ActionableParameters()
            baseline_results = runner.run_simulation(
                parameters=baseline,
                duration_days=1/24,
                seed=42
            )
            baseline_oee = baseline_results.kpi_summary['mean_oee']
            
            # High performance
            high_perf = ActionableParameters()
            high_perf.performance_factor = 1.2
            high_results = runner.run_simulation(
                parameters=high_perf,
                duration_days=1/24,
                seed=42
            )
            high_oee = high_results.kpi_summary['mean_oee']
            
            # High performance should improve OEE
            assert high_oee >= baseline_oee
            
        except ImportError:
            pytest.skip("twin_model not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])