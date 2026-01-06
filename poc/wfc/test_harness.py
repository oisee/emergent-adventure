"""
Test Harness for Emergent Adventure POC

Runs batch generation tests and collects statistics.
Validates that system produces completable worlds reliably.
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import random

from .integration import WorldGenerator
from .plot import PROPP_NAMES


@dataclass
class TestResult:
    """Result of a single generation test"""
    seed: int
    success: bool
    plot_nodes: int = 0
    geo_iterations: int = 0
    attempts: int = 0
    completable: bool = False
    error: str = ""
    generation_time_ms: float = 0


@dataclass
class TestStats:
    """Aggregate statistics from test run"""
    total_tests: int = 0
    successful: int = 0
    completable: int = 0
    avg_time_ms: float = 0
    avg_attempts: float = 0
    avg_plot_nodes: float = 0

    # Failure breakdown
    plot_failures: int = 0
    geo_failures: int = 0
    reachability_failures: int = 0

    def success_rate(self) -> float:
        return self.successful / self.total_tests * 100 if self.total_tests > 0 else 0

    def completability_rate(self) -> float:
        return self.completable / self.total_tests * 100 if self.total_tests > 0 else 0


def run_single_test(seed: int, width: int = 16, height: int = 12) -> TestResult:
    """Run a single generation test"""
    result = TestResult(seed=seed, success=False)

    start_time = time.time()

    try:
        gen = WorldGenerator(width=width, height=height, seed=seed)
        success = gen.generate()

        result.success = success

        if success:
            result.plot_nodes = len(gen.world.plot.nodes)
            result.geo_iterations = gen.geo_gen.wfc.iterations
            result.attempts = gen.world.attempts

            # Verify completability
            completable, msg = gen.verify_completability()
            result.completable = completable
            if not completable:
                result.error = msg
        else:
            # Diagnose failure
            if gen.world.plot is None:
                result.error = "Plot generation failed"
            else:
                result.error = "Geography generation failed"

    except Exception as e:
        result.error = str(e)

    result.generation_time_ms = (time.time() - start_time) * 1000
    return result


def run_batch_test(num_tests: int = 100,
                   width: int = 16,
                   height: int = 12,
                   base_seed: int = None,
                   verbose: bool = False) -> Tuple[TestStats, List[TestResult]]:
    """
    Run batch of generation tests.

    Returns (stats, results).
    """
    if base_seed is None:
        base_seed = random.randint(0, 999999)

    results = []
    stats = TestStats(total_tests=num_tests)

    total_time = 0
    total_attempts = 0
    total_nodes = 0

    print(f"Running {num_tests} tests (base_seed={base_seed})...")
    print("-" * 50)

    for i in range(num_tests):
        seed = base_seed + i
        result = run_single_test(seed, width, height)
        results.append(result)

        if result.success:
            stats.successful += 1
            total_attempts += result.attempts
            total_nodes += result.plot_nodes

            if result.completable:
                stats.completable += 1

            if verbose:
                print(f"  [{i+1:3d}] seed={seed}: OK ({result.plot_nodes} nodes, "
                      f"{result.attempts} attempts, {result.generation_time_ms:.1f}ms)")
        else:
            if "Plot" in result.error:
                stats.plot_failures += 1
            elif "Geography" in result.error:
                stats.geo_failures += 1
            else:
                stats.reachability_failures += 1

            if verbose:
                print(f"  [{i+1:3d}] seed={seed}: FAIL - {result.error}")

        total_time += result.generation_time_ms

        # Progress indicator for non-verbose
        if not verbose and (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{num_tests} ({stats.successful} successful)")

    # Calculate averages
    stats.avg_time_ms = total_time / num_tests if num_tests > 0 else 0
    stats.avg_attempts = total_attempts / stats.successful if stats.successful > 0 else 0
    stats.avg_plot_nodes = total_nodes / stats.successful if stats.successful > 0 else 0

    return stats, results


def print_stats(stats: TestStats):
    """Print statistics summary"""
    print()
    print("=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    print(f"Total tests:        {stats.total_tests}")
    print(f"Successful:         {stats.successful} ({stats.success_rate():.1f}%)")
    print(f"Completable:        {stats.completable} ({stats.completability_rate():.1f}%)")
    print()
    print("Failure breakdown:")
    print(f"  Plot failures:        {stats.plot_failures}")
    print(f"  Geography failures:   {stats.geo_failures}")
    print(f"  Reachability failures:{stats.reachability_failures}")
    print()
    print("Performance:")
    print(f"  Avg generation time:  {stats.avg_time_ms:.1f} ms")
    print(f"  Avg geography attempts: {stats.avg_attempts:.1f}")
    print(f"  Avg plot nodes:       {stats.avg_plot_nodes:.1f}")


def find_interesting_seeds(num_tests: int = 50,
                          base_seed: int = None) -> List[int]:
    """
    Find seeds that produce interesting/diverse worlds.

    Criteria:
    - Successful generation
    - High number of plot nodes
    - Spread-out geography
    """
    if base_seed is None:
        base_seed = random.randint(0, 999999)

    interesting = []

    for i in range(num_tests):
        seed = base_seed + i
        result = run_single_test(seed, 20, 12)

        if result.success and result.completable:
            # Prefer more complex plots
            if result.plot_nodes >= 5:
                interesting.append((seed, result.plot_nodes, result.generation_time_ms))

    # Sort by plot complexity
    interesting.sort(key=lambda x: -x[1])

    return [seed for seed, _, _ in interesting[:10]]


def visualize_sample_worlds(seeds: List[int], width: int = 20, height: int = 12):
    """Generate and visualize sample worlds"""
    print()
    print("=" * 60)
    print("SAMPLE WORLDS")
    print("=" * 60)

    for seed in seeds:
        gen = WorldGenerator(width=width, height=height, seed=seed)
        if gen.generate():
            print()
            print(f"--- SEED {seed} ---")
            print()

            # Plot summary
            order = gen.world.plot.topological_sort()
            print("Plot:", " -> ".join(
                PROPP_NAMES[gen.world.plot.nodes[n].function]
                for n in order
            ))
            print()

            # Map
            print(gen.geo_gen.visualize())
            print()

            # Quick stats
            valid, msg = gen.verify_completability()
            print(f"Status: {msg}")
            print()


# =============================================================================
# Main
# =============================================================================

def main():
    """Run test harness"""
    print("=" * 60)
    print("EMERGENT ADVENTURE POC - TEST HARNESS")
    print("=" * 60)
    print()

    # Run batch test
    stats, results = run_batch_test(
        num_tests=50,
        width=16,
        height=12,
        base_seed=12345,
        verbose=False
    )

    print_stats(stats)

    # Find interesting seeds
    print()
    print("Finding interesting seeds...")
    interesting = find_interesting_seeds(num_tests=30, base_seed=54321)
    print(f"Found {len(interesting)} interesting seeds: {interesting[:5]}...")

    # Visualize samples
    visualize_sample_worlds(interesting[:3])


if __name__ == "__main__":
    main()
