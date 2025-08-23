"""Profiling tool for simulation performance analysis.

This module provides profiling capabilities to identify bottlenecks
and optimize simulation performance.
"""

import cProfile
import pstats
import io
import time
import tracemalloc
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class ProfileResult:
    """Results from profiling a simulation run.
    
    Attributes:
        name: Name of the profiled run
        total_time: Total execution time
        cpu_time: Total CPU time
        memory_peak_mb: Peak memory usage
        memory_growth_mb: Memory growth during execution
        top_functions: Top time-consuming functions
        top_memory: Top memory-consuming operations
        bottlenecks: Identified performance bottlenecks
    """
    
    name: str
    total_time: float
    cpu_time: float
    memory_peak_mb: float
    memory_growth_mb: float
    top_functions: List[Dict[str, Any]]
    top_memory: List[Dict[str, Any]]
    bottlenecks: List[str]
    
    def print_summary(self) -> None:
        """Print human-readable summary of profile results."""
        print(f"\nProfile Results: {self.name}")
        print("=" * 60)
        print(f"Total time: {self.total_time:.2f}s")
        print(f"CPU time: {self.cpu_time:.2f}s")
        print(f"Peak memory: {self.memory_peak_mb:.1f}MB")
        print(f"Memory growth: {self.memory_growth_mb:.1f}MB")
        
        print("\nTop 5 Time-Consuming Functions:")
        print("-" * 40)
        for func in self.top_functions[:5]:
            print(f"  {func['function']:<40} {func['time']:.3f}s ({func['percent']:.1f}%)")
        
        if self.top_memory:
            print("\nTop 5 Memory Allocations:")
            print("-" * 40)
            for alloc in self.top_memory[:5]:
                print(f"  {alloc['traceback']:<40} {alloc['size_mb']:.1f}MB")
        
        if self.bottlenecks:
            print("\nIdentified Bottlenecks:")
            print("-" * 40)
            for bottleneck in self.bottlenecks:
                print(f"  • {bottleneck}")


class SimulationProfiler:
    """Profile simulation performance and identify bottlenecks.
    
    Provides CPU profiling, memory profiling, and bottleneck analysis
    for simulation runs.
    
    Attributes:
        profile_dir: Directory for storing profile results
        cpu_profiler: cProfile instance
        memory_snapshots: Memory usage snapshots
        results: List of profile results
    """
    
    def __init__(self, profile_dir: str = "profile_results"):
        """Initialize profiler.
        
        Args:
            profile_dir: Directory for storing results
        """
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.cpu_profiler: Optional[cProfile.Profile] = None
        self.memory_snapshots: List[tracemalloc.Snapshot] = []
        self.results: List[ProfileResult] = []
        
    def profile_function(self,
                        func: Callable,
                        args: tuple = (),
                        kwargs: Optional[dict] = None,
                        name: str = "unnamed") -> ProfileResult:
        """Profile a function execution.
        
        Args:
            func: Function to profile
            args: Function arguments
            kwargs: Function keyword arguments
            name: Name for this profile run
            
        Returns:
            Profile results
        """
        kwargs = kwargs or {}
        
        print(f"\nProfiling: {name}")
        print("-" * 40)
        
        # Start memory tracing
        tracemalloc.start()
        snapshot_start = tracemalloc.take_snapshot()
        
        # Start CPU profiling
        self.cpu_profiler = cProfile.Profile()
        self.cpu_profiler.enable()
        
        # Run function
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            print(f"Error during profiling: {e}")
            result = None
        end_time = time.time()
        
        # Stop CPU profiling
        self.cpu_profiler.disable()
        
        # Take memory snapshot
        snapshot_end = tracemalloc.take_snapshot()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Analyze results
        total_time = end_time - start_time
        
        # CPU analysis
        stats = pstats.Stats(self.cpu_profiler)
        stats.sort_stats('cumulative')
        
        # Get top functions
        top_functions = []
        total_cpu_time = sum(stat[2] for stat in stats.stats.values())  # type: ignore[attr-defined]
        
        for (filename, line, func_name), (_, _, cumtime, _, _) in \
                sorted(stats.stats.items(), key=lambda x: x[1][2], reverse=True)[:20]:  # type: ignore[attr-defined]
            
            # Skip built-in functions for clarity
            if '<' in filename:
                continue
                
            top_functions.append({
                'function': f"{Path(filename).name}:{func_name}",
                'time': cumtime,
                'percent': (cumtime / total_cpu_time * 100) if total_cpu_time > 0 else 0
            })
        
        # Memory analysis
        top_memory = []
        top_stats = snapshot_end.compare_to(snapshot_start, 'traceback')
        
        for stat in top_stats[:10]:
            if stat.size_diff > 0:
                top_memory.append({
                    'traceback': self._format_traceback(stat.traceback),
                    'size_mb': stat.size_diff / (1024 * 1024),
                    'count': stat.count_diff
                })
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(
            top_functions,
            top_memory,
            peak / (1024 * 1024),
            total_time
        )
        
        # Create result
        # Calculate memory growth from snapshots
        start_size = sum(stat.size for stat in snapshot_start.statistics('filename'))
        end_size = sum(stat.size for stat in snapshot_end.statistics('filename'))
        memory_growth = (end_size - start_size) / (1024 * 1024)
        
        profile_result = ProfileResult(
            name=name,
            total_time=total_time,
            cpu_time=total_cpu_time,
            memory_peak_mb=peak / (1024 * 1024),
            memory_growth_mb=memory_growth,
            top_functions=top_functions,
            top_memory=top_memory,
            bottlenecks=bottlenecks
        )
        
        self.results.append(profile_result)
        
        # Save detailed stats
        self._save_detailed_stats(name, stats)
        
        return profile_result
    
    def profile_simulation(self,
                          simulation_func: Callable,
                          config_name: str,
                          **kwargs) -> ProfileResult:
        """Profile a simulation run.
        
        Args:
            simulation_func: Simulation function to profile
            config_name: Name of configuration being tested
            **kwargs: Arguments for simulation function
            
        Returns:
            Profile results
        """
        return self.profile_function(
            simulation_func,
            kwargs=kwargs,
            name=f"simulation_{config_name}"
        )
    
    def compare_profiles(self, *profile_names: str) -> Dict[str, Any]:
        """Compare multiple profile results.
        
        Args:
            *profile_names: Names of profiles to compare
            
        Returns:
            Comparison dictionary
        """
        profiles_to_compare = []
        
        for name in profile_names:
            for result in self.results:
                if result.name == name:
                    profiles_to_compare.append(result)
                    break
        
        if len(profiles_to_compare) < 2:
            print("Need at least 2 profiles to compare")
            return {}
        
        comparison = {
            'profiles': profile_names,
            'time_comparison': {},
            'memory_comparison': {},
            'bottleneck_comparison': {}
        }
        
        # Compare execution times
        base_time = profiles_to_compare[0].total_time
        for profile in profiles_to_compare:
            comparison['time_comparison'][profile.name] = {  # type: ignore[index]
                'total_time': profile.total_time,
                'speedup': base_time / profile.total_time if profile.total_time > 0 else 0
            }
        
        # Compare memory usage
        for profile in profiles_to_compare:
            comparison['memory_comparison'][profile.name] = {  # type: ignore[index]
                'peak_mb': profile.memory_peak_mb,
                'growth_mb': profile.memory_growth_mb
            }
        
        # Compare bottlenecks
        for profile in profiles_to_compare:
            comparison['bottleneck_comparison'][profile.name] = profile.bottlenecks  # type: ignore[index]
        
        # Print comparison
        print("\nProfile Comparison")
        print("=" * 60)
        
        print("\nExecution Time:")
        for name, data in comparison['time_comparison'].items():  # type: ignore[attr-defined]
            print(f"  {name}: {data['total_time']:.2f}s (speedup: {data['speedup']:.2f}x)")
        
        print("\nMemory Usage:")
        for name, data in comparison['memory_comparison'].items():  # type: ignore[attr-defined]
            print(f"  {name}: {data['peak_mb']:.1f}MB peak, {data['growth_mb']:.1f}MB growth")
        
        return comparison
    
    def _identify_bottlenecks(self,
                             top_functions: List[Dict[str, Any]],
                             top_memory: List[Dict[str, Any]],
                             peak_memory_mb: float,
                             total_time: float) -> List[str]:
        """Identify performance bottlenecks.
        
        Args:
            top_functions: Top time-consuming functions
            top_memory: Top memory allocations
            peak_memory_mb: Peak memory usage
            total_time: Total execution time
            
        Returns:
            List of identified bottlenecks
        """
        bottlenecks = []
        
        # Check for slow functions
        if top_functions:
            # If top function takes >30% of time, it's a bottleneck
            if top_functions[0]['percent'] > 30:
                bottlenecks.append(
                    f"Function {top_functions[0]['function']} takes "
                    f"{top_functions[0]['percent']:.1f}% of execution time"
                )
            
            # Check for too many function calls
            slow_functions = [f for f in top_functions if f['percent'] > 10]
            if len(slow_functions) > 3:
                bottlenecks.append(
                    f"{len(slow_functions)} functions each take >10% of execution time"
                )
        
        # Check for memory issues
        if peak_memory_mb > 500:
            bottlenecks.append(f"High memory usage: {peak_memory_mb:.1f}MB")
        
        if top_memory and top_memory[0]['size_mb'] > 100:
            bottlenecks.append(
                f"Large memory allocation: {top_memory[0]['size_mb']:.1f}MB at "
                f"{top_memory[0]['traceback']}"
            )
        
        # Check for slow execution
        if total_time > 60:
            bottlenecks.append(f"Slow execution: {total_time:.1f}s total time")
        
        # If no specific bottlenecks found
        if not bottlenecks:
            bottlenecks.append("No significant bottlenecks identified")
        
        return bottlenecks
    
    def _format_traceback(self, traceback) -> str:
        """Format traceback for display.
        
        Args:
            traceback: Traceback object
            
        Returns:
            Formatted string
        """
        if not traceback:
            return "unknown"
            
        # Get most recent frame
        frame = traceback[-1] if len(traceback) > 0 else traceback
        
        return f"{Path(frame.filename).name}:{frame.lineno}"
    
    def _save_detailed_stats(self, name: str, stats: pstats.Stats) -> None:
        """Save detailed profiling statistics.
        
        Args:
            name: Profile name
            stats: pstats.Stats object
        """
        output_file = self.profile_dir / f"{name}_profile.txt"
        
        with open(output_file, 'w') as f:
            # Redirect output to file
            old_stdout = sys.stdout
            sys.stdout = f
            
            print(f"Detailed Profile: {name}")
            print("=" * 80)
            print("\nTop 50 functions by cumulative time:")
            print("-" * 80)
            stats.print_stats(50)
            
            print("\n\nTop 50 functions by total time:")
            print("-" * 80)
            stats.sort_stats('time')
            stats.print_stats(50)
            
            print("\n\nCallers for top functions:")
            print("-" * 80)
            stats.print_callers(20)
            
            sys.stdout = old_stdout
        
        print(f"  Detailed stats saved to: {output_file}")
    
    def generate_flame_graph(self, name: str) -> None:
        """Generate flame graph visualization.
        
        Note: Requires py-spy or flamegraph tools installed separately.
        
        Args:
            name: Profile name for the graph
        """
        print(f"\nFlame graph generation requires external tools:")
        print("  1. Install py-spy: pip install py-spy")
        print("  2. Run simulation with: py-spy record -o flame.svg -- python your_script.py")
        print("  3. Or use snakeviz: pip install snakeviz")
        print(f"     Then run: snakeviz {self.profile_dir}/{name}_profile.prof")
        
        # Save profile data for snakeviz
        if self.cpu_profiler:
            prof_file = self.profile_dir / f"{name}_profile.prof"
            self.cpu_profiler.dump_stats(str(prof_file))
            print(f"\n  Profile data saved for visualization: {prof_file}")
    
    def plot_performance_trends(self) -> None:
        """Plot performance trends across multiple profiles."""
        if len(self.results) < 2:
            print("Need at least 2 profiles to plot trends")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle("Performance Profile Trends", fontsize=16)
        
        names = [r.name for r in self.results]
        times = [r.total_time for r in self.results]
        cpu_times = [r.cpu_time for r in self.results]
        peak_memory = [r.memory_peak_mb for r in self.results]
        memory_growth = [r.memory_growth_mb for r in self.results]
        
        # Execution time
        axes[0, 0].bar(range(len(names)), times, color='blue')
        axes[0, 0].set_title("Total Execution Time")
        axes[0, 0].set_ylabel("Time (seconds)")
        axes[0, 0].set_xticks(range(len(names)))
        axes[0, 0].set_xticklabels(names, rotation=45, ha='right')
        
        # CPU time
        axes[0, 1].bar(range(len(names)), cpu_times, color='green')
        axes[0, 1].set_title("CPU Time")
        axes[0, 1].set_ylabel("Time (seconds)")
        axes[0, 1].set_xticks(range(len(names)))
        axes[0, 1].set_xticklabels(names, rotation=45, ha='right')
        
        # Peak memory
        axes[1, 0].bar(range(len(names)), peak_memory, color='red')
        axes[1, 0].set_title("Peak Memory Usage")
        axes[1, 0].set_ylabel("Memory (MB)")
        axes[1, 0].set_xticks(range(len(names)))
        axes[1, 0].set_xticklabels(names, rotation=45, ha='right')
        
        # Memory growth
        axes[1, 1].bar(range(len(names)), memory_growth, color='orange')
        axes[1, 1].set_title("Memory Growth")
        axes[1, 1].set_ylabel("Memory (MB)")
        axes[1, 1].set_xticks(range(len(names)))
        axes[1, 1].set_xticklabels(names, rotation=45, ha='right')
        
        plt.tight_layout()
        
        output_file = self.profile_dir / "performance_trends.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"\nPerformance trends plot saved to: {output_file}")


def profile_quick_simulation():
    """Quick profiling example."""
    import simpy
    from twin_model.primitives.base import PrimitiveConfig
    from twin_model.primitives.equipment import EquipmentPrimitive
    
    def run_simulation(duration: int = 100):
        """Simple simulation for profiling."""
        env = simpy.Environment()
        
        # Create some equipment
        for i in range(10):
            config = PrimitiveConfig(
                id=f"EQ-{i:03d}",
                type="Equipment",
                properties={"base_rate": 60.0}
            )
            equipment = EquipmentPrimitive(env, config)
            equipment.start()
        
        # Run simulation
        env.run(until=duration)
        
        return env.now
    
    # Profile the simulation
    profiler = SimulationProfiler()
    
    result = profiler.profile_function(
        run_simulation,
        args=(1000,),
        name="quick_simulation"
    )
    
    result.print_summary()
    profiler.generate_flame_graph("quick_simulation")
    
    return result


if __name__ == "__main__":
    profile_quick_simulation()
