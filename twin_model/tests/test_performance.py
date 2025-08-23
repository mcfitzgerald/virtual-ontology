"""Performance Testing Suite for SimPy optimizations.

This module provides comprehensive performance benchmarks and regression
testing for the optimized simulation system.
"""

import simpy
import time
import tracemalloc
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import numpy as np

from twin_model.primitives.base import (
    PrimitiveConfig,
    SamplingConfig,
    SimulationMode,
    ConsoleProgressReporter
)
from twin_model.primitives.equipment import EquipmentPrimitive
from twin_model.config import PerformanceConfig, ConfigPreset
from twin_model.storage.cache import ObservableCache
from twin_model.state_manager import SimulationRunner


@dataclass
class BenchmarkResult:
    """Results from a performance benchmark run.
    
    Attributes:
        config_name: Name of configuration used
        simulation_days: Duration of simulation
        num_primitives: Number of primitives
        real_time_seconds: Wall clock time
        simulation_time: Simulated time
        speed_factor: Simulation speed multiplier
        memory_peak_mb: Peak memory usage
        memory_avg_mb: Average memory usage
        events_total: Total events generated
        events_per_second: Event processing rate
        cache_size_mb: Final cache size
        checkpoints_saved: Number of checkpoints
        errors: Any errors encountered
    """
    
    config_name: str
    simulation_days: float
    num_primitives: int
    real_time_seconds: float
    simulation_time: float
    speed_factor: float
    memory_peak_mb: float
    memory_avg_mb: float
    events_total: int
    events_per_second: float
    cache_size_mb: float
    checkpoints_saved: int
    errors: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def score(self) -> float:
        """Calculate performance score (higher is better).
        
        Returns:
            Performance score combining speed and memory efficiency
        """
        if self.errors:
            return 0.0
            
        # Weighted score: speed (60%) + memory efficiency (40%)
        speed_score = min(100, self.speed_factor / 10)  # Cap at 1000x
        memory_score = max(0, 100 - (self.memory_peak_mb / 10))  # Penalize >1GB
        
        return (speed_score * 0.6) + (memory_score * 0.4)


class PerformanceBenchmark:
    """Performance benchmarking suite for simulations.
    
    Provides automated benchmarks for different configurations
    and simulation scales with detailed performance metrics.
    
    Attributes:
        results_dir: Directory for storing benchmark results
        results: List of benchmark results
        baseline: Baseline results for comparison
    """
    
    def __init__(self, results_dir: str = "benchmark_results"):
        """Initialize benchmark suite.
        
        Args:
            results_dir: Directory for storing results
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.baseline: Optional[BenchmarkResult] = None
        
    def run_benchmark(self,
                      config: PerformanceConfig,
                      num_primitives: int,
                      simulation_days: float,
                      name: Optional[str] = None) -> BenchmarkResult:
        """Run a single benchmark with given configuration.
        
        Args:
            config: Performance configuration to test
            num_primitives: Number of primitives to simulate
            simulation_days: Duration of simulation
            name: Optional name for this benchmark
            
        Returns:
            Benchmark results
        """
        print(f"\nRunning benchmark: {name or config.name}")
        print(f"  Primitives: {num_primitives}")
        print(f"  Duration: {simulation_days} days")
        
        # Setup temporary directories
        cache_dir = Path(tempfile.mkdtemp())
        checkpoint_dir = Path(tempfile.mkdtemp())
        
        try:
            # Start memory tracking
            tracemalloc.start()
            start_memory = tracemalloc.get_traced_memory()[0]
            memory_samples = []
            
            # Create environment
            env = simpy.Environment()
            
            # Create primitives
            primitives = {}
            for i in range(num_primitives):
                prim_config = PrimitiveConfig(
                    id=f"BENCH-{i:04d}",
                    type="Equipment",
                    properties={
                        "base_rate": 60.0,
                        "mtbf": 480.0,
                        "mttr": 30.0
                    }
                )
                
                sampling = SamplingConfig(
                    mode=config.simulation_mode,
                    sampling_rate=config.sampling_rate,
                    buffer_size=config.observable_buffer_size,
                    aggregation_interval=config.aggregation_interval,
                    enable_global_observables=config.enable_global_observables
                )
                
                equipment = EquipmentPrimitive(env, prim_config, sampling_config=sampling)
                equipment.start()
                primitives[f"eq{i}"] = equipment
            
            # Setup cache
            cache = ObservableCache(
                cache_dir,
                max_size=config.cache_max_size,
                dtype_size=512
            )
            
            # Create runner
            runner = SimulationRunner(
                env,
                primitives,
                checkpoint_dir=str(checkpoint_dir),
                enable_monitoring=config.enable_monitoring
            )
            runner.cache_path = str(cache_dir)
            
            # Run simulation
            start_time = time.time()
            errors = []
            
            try:
                # Use progress callback to track memory
                def progress_callback(**kwargs):
                    current, _ = tracemalloc.get_traced_memory()
                    memory_samples.append(current / (1024 * 1024))
                
                results = runner.run_chunked(
                    total_days=simulation_days,  # type: ignore[arg-type]
                    chunk_size_days=config.chunk_size_days,
                    progress_callback=progress_callback if config.enable_progress else None,
                    checkpoint_interval=config.checkpoint_interval / 1440 if config.checkpoint_interval else None
                )
                
            except Exception as e:
                errors.append(str(e))
                results = {
                    "simulation_time": env.now,
                    "checkpoints_saved": 0,
                    "total_events": 0
                }
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            # Get final memory
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Get cache stats
            cache_stats = cache.get_stats()
            
            # Calculate metrics
            total_events = sum(p.events_emitted for p in primitives.values())
            
            result = BenchmarkResult(
                config_name=name or config.name,
                simulation_days=simulation_days,
                num_primitives=num_primitives,
                real_time_seconds=elapsed,
                simulation_time=results["simulation_time"],
                speed_factor=results["simulation_time"] / elapsed if elapsed > 0 else 0,
                memory_peak_mb=peak_memory / (1024 * 1024),
                memory_avg_mb=np.mean(memory_samples) if memory_samples else 0,
                events_total=total_events,
                events_per_second=total_events / elapsed if elapsed > 0 else 0,
                cache_size_mb=cache_stats["total_size_mb"],
                checkpoints_saved=results.get("checkpoints_saved", 0),
                errors=errors if errors else None  # type: ignore[arg-type]
            )
            
            self.results.append(result)
            
            print(f"  ✓ Completed in {elapsed:.2f}s")
            print(f"    Speed: {result.speed_factor:.0f}x")
            print(f"    Memory: {result.memory_peak_mb:.1f}MB peak")
            print(f"    Events: {result.events_total:,} ({result.events_per_second:.0f}/s)")
            
            return result
            
        finally:
            # Cleanup
            shutil.rmtree(cache_dir, ignore_errors=True)
            shutil.rmtree(checkpoint_dir, ignore_errors=True)
    
    def run_preset_comparison(self, num_primitives: int = 10, 
                            simulation_days: float = 1.0) -> Dict[str, BenchmarkResult]:
        """Run benchmarks for all configuration presets.
        
        Args:
            num_primitives: Number of primitives to test
            simulation_days: Duration of simulation
            
        Returns:
            Dictionary mapping preset names to results
        """
        print("\n" + "=" * 60)
        print("PRESET COMPARISON BENCHMARK")
        print("=" * 60)
        
        results = {}
        
        for preset in ConfigPreset:
            config = PerformanceConfig.from_preset(preset)
            result = self.run_benchmark(
                config,
                num_primitives,
                simulation_days,
                name=preset.value
            )
            results[preset.value] = result
            
        return results
    
    def run_scaling_benchmark(self, config: PerformanceConfig) -> List[BenchmarkResult]:
        """Run benchmarks with increasing scale.
        
        Tests how performance scales with simulation size.
        
        Args:
            config: Configuration to use for all tests
            
        Returns:
            List of results for different scales
        """
        print("\n" + "=" * 60)
        print("SCALING BENCHMARK")
        print("=" * 60)
        
        scales = [
            (5, 0.1),    # Small: 5 primitives, 2.4 hours
            (10, 1),     # Medium: 10 primitives, 1 day
            (50, 1),     # Large: 50 primitives, 1 day
            (10, 7),     # Long: 10 primitives, 1 week
            (100, 1),    # Very large: 100 primitives, 1 day
            (10, 30),    # Very long: 10 primitives, 1 month
        ]
        
        results = []
        
        for num_primitives, days in scales:
            name = f"scale_{num_primitives}p_{days}d"
            result = self.run_benchmark(
                config,
                num_primitives,
                days,
                name=name
            )
            results.append(result)
            
        return results
    
    def run_memory_stress_test(self) -> BenchmarkResult:
        """Run memory stress test with aggressive settings.
        
        Returns:
            Benchmark result from stress test
        """
        print("\n" + "=" * 60)
        print("MEMORY STRESS TEST")
        print("=" * 60)
        
        # Create config with very limited memory
        config = PerformanceConfig.from_preset(ConfigPreset.MEMORY_OPTIMIZED)
        config.max_memory_mb = 25.0  # Very low limit
        config.observable_buffer_size = 10  # Minimal buffer
        config.cache_max_size = 100  # Tiny cache
        
        return self.run_benchmark(
            config,
            num_primitives=20,
            simulation_days=1.0,
            name="memory_stress"
        )
    
    def compare_with_baseline(self, result: BenchmarkResult) -> Dict[str, float]:
        """Compare result with baseline.
        
        Args:
            result: Result to compare
            
        Returns:
            Dictionary with percentage improvements
        """
        if not self.baseline:
            self.baseline = result
            return {"status": "set_as_baseline"}  # type: ignore[dict-item]
            
        improvements = {
            "speed": ((result.speed_factor / self.baseline.speed_factor) - 1) * 100,
            "memory": ((self.baseline.memory_peak_mb / result.memory_peak_mb) - 1) * 100,
            "events_rate": ((result.events_per_second / self.baseline.events_per_second) - 1) * 100,
            "score": ((result.score() / self.baseline.score()) - 1) * 100
        }
        
        return improvements
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate performance report.
        
        Args:
            output_file: Optional file to save report
            
        Returns:
            Report text
        """
        lines = [
            "PERFORMANCE BENCHMARK REPORT",
            "=" * 60,
            f"Total benchmarks run: {len(self.results)}",
            ""
        ]
        
        if self.results:
            # Sort by score
            sorted_results = sorted(self.results, key=lambda r: r.score(), reverse=True)
            
            lines.append("TOP PERFORMERS:")
            lines.append("-" * 40)
            
            for i, result in enumerate(sorted_results[:5], 1):
                lines.append(f"{i}. {result.config_name}")
                lines.append(f"   Score: {result.score():.1f}")
                lines.append(f"   Speed: {result.speed_factor:.0f}x")
                lines.append(f"   Memory: {result.memory_peak_mb:.1f}MB")
                lines.append(f"   Events/s: {result.events_per_second:.0f}")
                lines.append("")
            
            # Statistics
            speeds = [r.speed_factor for r in self.results if not r.errors]
            memories = [r.memory_peak_mb for r in self.results if not r.errors]
            
            if speeds:
                lines.append("STATISTICS:")
                lines.append("-" * 40)
                lines.append(f"Speed factor range: {min(speeds):.0f}x - {max(speeds):.0f}x")
                lines.append(f"Memory usage range: {min(memories):.1f}MB - {max(memories):.1f}MB")
                lines.append(f"Average speed: {np.mean(speeds):.0f}x")
                lines.append(f"Average memory: {np.mean(memories):.1f}MB")
                lines.append("")
            
            # Errors
            error_results = [r for r in self.results if r.errors]
            if error_results:
                lines.append("ERRORS:")
                lines.append("-" * 40)
                for result in error_results:
                    lines.append(f"{result.config_name}: {', '.join(result.errors)}")
                lines.append("")
        
        report = "\n".join(lines)
        
        if output_file:
            output_path = self.results_dir / output_file
            with open(output_path, 'w') as f:
                f.write(report)
            print(f"Report saved to: {output_path}")
            
        return report
    
    def save_results(self, filename: str = "benchmark_results.json") -> None:
        """Save benchmark results to JSON file.
        
        Args:
            filename: Name of results file
        """
        output_path = self.results_dir / filename
        
        data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": [r.to_dict() for r in self.results],
            "baseline": self.baseline.to_dict() if self.baseline else None
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Results saved to: {output_path}")
    
    def plot_comparison(self, output_file: str = "benchmark_comparison.png") -> None:
        """Generate comparison plots.
        
        Args:
            output_file: Name of plot file
        """
        if len(self.results) < 2:
            print("Need at least 2 results to plot comparison")
            return
            
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle("Performance Benchmark Comparison", fontsize=16)
        
        names = [r.config_name for r in self.results]
        speeds = [r.speed_factor for r in self.results]
        memories = [r.memory_peak_mb for r in self.results]
        events = [r.events_per_second for r in self.results]
        scores = [r.score() for r in self.results]
        
        # Speed comparison
        axes[0, 0].bar(names, speeds, color='blue')
        axes[0, 0].set_title("Simulation Speed")
        axes[0, 0].set_ylabel("Speed Factor (x)")
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Memory comparison
        axes[0, 1].bar(names, memories, color='red')
        axes[0, 1].set_title("Peak Memory Usage")
        axes[0, 1].set_ylabel("Memory (MB)")
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Event rate comparison
        axes[1, 0].bar(names, events, color='green')
        axes[1, 0].set_title("Event Processing Rate")
        axes[1, 0].set_ylabel("Events/second")
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Overall score
        axes[1, 1].bar(names, scores, color='purple')
        axes[1, 1].set_title("Overall Performance Score")
        axes[1, 1].set_ylabel("Score")
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        output_path = self.results_dir / output_file
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Comparison plot saved to: {output_path}")


def run_quick_benchmark():
    """Run a quick benchmark for testing."""
    print("\n" + "=" * 60)
    print("QUICK PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    benchmark = PerformanceBenchmark()
    
    # Test PRODUCTION preset
    config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
    result = benchmark.run_benchmark(
        config,
        num_primitives=5,
        simulation_days=0.1,  # 2.4 hours
        name="quick_test"
    )
    
    print(f"\nQuick benchmark score: {result.score():.1f}")
    
    return result


def run_full_benchmark_suite():
    """Run complete benchmark suite."""
    print("\n" + "=" * 60)
    print("FULL PERFORMANCE BENCHMARK SUITE")
    print("=" * 60)
    
    benchmark = PerformanceBenchmark()
    
    # 1. Compare presets (small scale)
    print("\n1. Comparing configuration presets...")
    preset_results = benchmark.run_preset_comparison(
        num_primitives=5,
        simulation_days=0.5
    )
    
    # 2. Scaling test with PRODUCTION config
    print("\n2. Testing scaling behavior...")
    config = PerformanceConfig.from_preset(ConfigPreset.PRODUCTION)
    scaling_results = benchmark.run_scaling_benchmark(config)
    
    # 3. Memory stress test
    print("\n3. Running memory stress test...")
    stress_result = benchmark.run_memory_stress_test()
    
    # Generate report
    print("\n4. Generating report...")
    report = benchmark.generate_report("full_benchmark_report.txt")
    print("\n" + report)
    
    # Save results
    benchmark.save_results()
    
    # Generate plots
    try:
        benchmark.plot_comparison()
    except ImportError:
        print("Matplotlib not available, skipping plots")
    
    return benchmark


if __name__ == "__main__":
    # Run quick test by default
    run_quick_benchmark()
