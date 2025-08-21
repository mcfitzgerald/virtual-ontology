"""Test Phase 5 Configuration System and Performance Suite.

This test validates the configuration management system and
runs performance benchmarks to verify optimization effectiveness.
"""

import tempfile
import json
from pathlib import Path
from typing import Dict, Any

from twin_model.config import (
    PerformanceConfig,
    ConfigPreset,
    SimulationMode
)
from twin_model.tests.test_performance import (
    PerformanceBenchmark,
    BenchmarkResult
)


def test_config_presets():
    """Test configuration preset loading."""
    print("\nTesting Configuration Presets...")
    
    # Test all presets load correctly
    for preset in ConfigPreset:
        config = PerformanceConfig.from_preset(preset)
        assert config.name == preset.value
        assert len(config.validate()) == 0, f"Preset {preset.value} has validation errors"
        print(f"  ✓ {preset.value}: {config.description}")
    
    print("✓ All presets loaded successfully")


def test_config_validation():
    """Test configuration validation."""
    print("\nTesting Configuration Validation...")
    
    # Test valid config
    config = PerformanceConfig()
    errors = config.validate()
    assert len(errors) == 0, "Default config should be valid"
    
    # Test invalid buffer size
    config = PerformanceConfig(observable_buffer_size=5)
    errors = config.validate()
    assert "observable_buffer_size must be at least 10" in errors
    
    # Test invalid memory
    config = PerformanceConfig(max_memory_mb=5)
    errors = config.validate()
    assert "max_memory_mb must be at least 10MB" in errors
    
    # Test inconsistent intervals
    config = PerformanceConfig(
        aggregation_interval=600,
        flush_interval=300
    )
    errors = config.validate()
    assert "flush_interval should be >= aggregation_interval" in errors
    
    # Test mode consistency
    config = PerformanceConfig(
        simulation_mode=SimulationMode.FAST,
        sampling_rate=1
    )
    errors = config.validate()
    assert "FAST mode incompatible with sampling_rate=1" in errors
    
    print("✓ Validation rules working correctly")


def test_config_serialization():
    """Test configuration save/load."""
    print("\nTesting Configuration Serialization...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create config
        config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
        config.max_memory_mb = 256.0
        config.sampling_rate = 20
        
        # Test JSON save/load
        json_path = tmpdir / "config.json"
        config.to_json(json_path)
        
        loaded = PerformanceConfig.from_json(json_path)
        assert loaded.max_memory_mb == 256.0
        assert loaded.sampling_rate == 20
        assert loaded.simulation_mode == SimulationMode.PRODUCTION
        
        print("  ✓ JSON serialization working")
        
        # Test YAML save/load (if available)
        try:
            yaml_path = tmpdir / "config.yaml"
            config.to_yaml(yaml_path)
            
            loaded = PerformanceConfig.from_yaml(yaml_path)
            assert loaded.max_memory_mb == 256.0
            assert loaded.sampling_rate == 20
            
            print("  ✓ YAML serialization working")
        except ImportError:
            print("  ⚠️  YAML not available, skipping")
    
    print("✓ Configuration serialization working")


def test_memory_estimation():
    """Test memory usage estimation."""
    print("\nTesting Memory Estimation...")
    
    config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
    
    # Estimate for small simulation
    estimates = config.estimate_memory_usage(
        num_primitives=10,
        simulation_days=1
    )
    
    assert "buffer_mb" in estimates
    assert "cache_mb" in estimates
    assert "total_mb" in estimates
    assert estimates["total_mb"] > 0
    
    print(f"  10 primitives, 1 day: {estimates['total_mb']:.1f}MB estimated")
    
    # Estimate for large simulation
    estimates = config.estimate_memory_usage(
        num_primitives=100,
        simulation_days=30
    )
    
    print(f"  100 primitives, 30 days: {estimates['total_mb']:.1f}MB estimated")
    
    print("✓ Memory estimation working")


def test_config_recommendation():
    """Test configuration recommendation system."""
    print("\nTesting Configuration Recommendations...")
    
    # Small simulation
    config = PerformanceConfig().recommend_settings(
        num_primitives=5,
        simulation_days=1,
        available_memory_mb=100
    )
    
    assert config.max_memory_mb <= 100
    errors = config.validate()
    assert len(errors) == 0, "Recommended config should be valid"
    
    print(f"  Small sim: {config.name} preset recommended")
    
    # Large simulation
    config = PerformanceConfig().recommend_settings(
        num_primitives=100,
        simulation_days=30,
        available_memory_mb=500
    )
    
    assert config.max_memory_mb <= 500
    print(f"  Large sim: {config.name} preset recommended")
    
    # Memory constrained
    config = PerformanceConfig().recommend_settings(
        num_primitives=50,
        simulation_days=7,
        available_memory_mb=50
    )
    
    assert config.max_memory_mb <= 50
    print(f"  Memory constrained: {config.name} preset, buffer={config.observable_buffer_size}")
    
    print("✓ Recommendation system working")


def test_config_summary():
    """Test configuration summary generation."""
    print("\nTesting Configuration Summary...")
    
    config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
    summary = config.get_summary()
    
    assert "Performance Configuration: production" in summary
    assert "Memory Settings:" in summary
    assert "Sampling Settings:" in summary
    assert "Mode: production" in summary
    
    print("Sample summary:")
    print("-" * 40)
    print(summary)
    print("-" * 40)
    
    print("✓ Summary generation working")


def test_performance_benchmark():
    """Test performance benchmark suite."""
    print("\nTesting Performance Benchmark Suite...")
    
    benchmark = PerformanceBenchmark()
    
    # Run minimal benchmark
    config = PerformanceConfig.from_preset(ConfigPreset.FAST)
    result = benchmark.run_benchmark(
        config,
        num_primitives=3,
        simulation_days=0.01,  # ~15 minutes
        name="minimal_test"
    )
    
    assert isinstance(result, BenchmarkResult)
    assert result.speed_factor > 0
    assert result.memory_peak_mb > 0
    assert result.events_total > 0
    assert result.score() > 0
    
    print(f"\n  Benchmark score: {result.score():.1f}")
    
    # Test comparison
    improvements = benchmark.compare_with_baseline(result)
    assert "status" in improvements or "speed" in improvements
    
    print("✓ Benchmark suite working")


def test_preset_performance_comparison():
    """Compare performance of different presets."""
    print("\nTesting Preset Performance Comparison...")
    
    benchmark = PerformanceBenchmark()
    
    # Test subset of presets with tiny simulation
    presets_to_test = [
        ConfigPreset.FAST,
        ConfigPreset.PRODUCTION,
        ConfigPreset.MEMORY_OPTIMIZED
    ]
    
    results = {}
    for preset in presets_to_test:
        config = PerformanceConfig.from_preset(preset)
        result = benchmark.run_benchmark(
            config,
            num_primitives=2,
            simulation_days=0.01,  # ~15 minutes
            name=preset.value
        )
        results[preset.value] = result
    
    # Compare results
    fast_score = results["fast"].score()
    prod_score = results["production"].score()
    mem_score = results["memory_optimized"].score()
    
    print(f"\n  Scores:")
    print(f"    FAST: {fast_score:.1f}")
    print(f"    PRODUCTION: {prod_score:.1f}")
    print(f"    MEMORY_OPTIMIZED: {mem_score:.1f}")
    
    # FAST should generally have highest speed
    assert results["fast"].speed_factor >= results["memory_optimized"].speed_factor
    
    # MEMORY_OPTIMIZED should use least memory
    assert results["memory_optimized"].memory_peak_mb <= results["production"].memory_peak_mb
    
    print("✓ Preset performance comparison completed")


def test_benchmark_reporting():
    """Test benchmark report generation."""
    print("\nTesting Benchmark Reporting...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        benchmark = PerformanceBenchmark(results_dir=tmpdir)
        
        # Run a few quick benchmarks
        for preset in [ConfigPreset.FAST, ConfigPreset.PRODUCTION]:
            config = PerformanceConfig.from_preset(preset)
            benchmark.run_benchmark(
                config,
                num_primitives=2,
                simulation_days=0.01,
                name=preset.value
            )
        
        # Generate report
        report = benchmark.generate_report()
        
        assert "PERFORMANCE BENCHMARK REPORT" in report
        assert "TOP PERFORMERS:" in report
        assert "Total benchmarks run: 2" in report
        
        # Save results
        benchmark.save_results("test_results.json")
        
        results_file = Path(tmpdir) / "test_results.json"
        assert results_file.exists()
        
        with open(results_file) as f:
            data = json.load(f)
            assert "results" in data
            assert len(data["results"]) == 2
        
        print("✓ Benchmark reporting working")


def run_all_tests():
    """Run all Phase 5 tests."""
    print("=" * 60)
    print("PHASE 5 CONFIGURATION & PERFORMANCE TESTS")
    print("=" * 60)
    
    try:
        # Configuration tests
        test_config_presets()
        test_config_validation()
        test_config_serialization()
        test_memory_estimation()
        test_config_recommendation()
        test_config_summary()
        
        # Performance tests
        test_performance_benchmark()
        test_preset_performance_comparison()
        test_benchmark_reporting()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASE 5 TESTS PASSED")
        print("=" * 60)
        print("\nPhase 5 features successfully implemented:")
        print("  • Configuration presets for common scenarios")
        print("  • Configuration validation and serialization")
        print("  • Memory usage estimation")
        print("  • Automatic configuration recommendations")
        print("  • Performance benchmarking suite")
        print("  • Preset performance comparison")
        print("  • Benchmark reporting and analysis")
        print("\nPerformance optimization complete!")
        print("Ready for Phase 6 integration!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()