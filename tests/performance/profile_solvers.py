"""Comprehensive profiling script for all solvers and algorithms.

Run with: python -m tests.performance.profile_solvers

Features:
- Profile all implemented solvers (LBL, CFOP, KOCIEMBA, CAGE)
- Test on multiple cube sizes (3x3, 4x4, 5x5, etc.)
- cProfile for detailed function-level profiling
- Timing measurements and statistics
- Bottleneck identification and suggestions
- JSON report generation for tracking over time

Usage:
    # Full profiling run
    python -m tests.performance.profile_solvers

    # Quick benchmark (no cProfile, just timing)
    python -m tests.performance.profile_solvers --quick

    # Profile specific solver
    python -m tests.performance.profile_solvers --solver LBL

    # Profile specific cube size
    python -m tests.performance.profile_solvers --size 5

    # Save detailed report
    python -m tests.performance.profile_solvers --output report.json
"""
from __future__ import annotations

import argparse
import cProfile
import json
import os
import pstats
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Suppress debug output
os.environ["CUBE_QUIET_ALL"] = "1"

from cube.application import _config as cfg
from cube.application.config_impl import AppConfig
from cube.application.Logger import Logger
from cube.application.markers import IMarkerFactory, IMarkerManager, MarkerFactory, MarkerManager
from cube.application.state import ApplicationAndViewState
from cube.application.commands.Operator import Operator
from cube.domain.algs import Algs
from cube.domain.model.Cube import Cube
from cube.domain.solver import Solver, Solvers
from cube.domain.solver.SolverName import SolverName
from cube.utils.config_protocol import ConfigProtocol
from cube.utils.logger_protocol import ILogger
from cube.utils.service_provider import IServiceProvider


# ============================================================================
# Service Provider for Profiling
# ============================================================================

class ProfileServiceProvider(IServiceProvider):
    """Service provider for profiling tests."""

    def __init__(self) -> None:
        self._config = AppConfig()
        self._marker_factory = MarkerFactory()
        self._marker_manager = MarkerManager()
        self._logger = Logger()

    @property
    def config(self) -> ConfigProtocol:
        return self._config

    @property
    def marker_factory(self) -> IMarkerFactory:
        return self._marker_factory

    @property
    def marker_manager(self) -> IMarkerManager:
        return self._marker_manager

    @property
    def logger(self) -> ILogger:
        return self._logger


# ============================================================================
# Data Classes for Results
# ============================================================================

@dataclass
class SolveResult:
    """Result of a single solve attempt."""
    solver_name: str
    cube_size: int
    scramble_seed: int
    scramble_moves: int
    solve_moves: int
    solve_time_ms: float
    success: bool
    error: str | None = None


@dataclass
class ProfileResult:
    """Result of profiling a solver."""
    solver_name: str
    cube_size: int
    total_solves: int
    successful_solves: int
    failed_solves: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    avg_moves: float
    total_moves: int
    moves_per_second: float
    top_functions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""
    timestamp: str
    python_version: str
    cache_enabled: bool
    results: list[ProfileResult] = field(default_factory=list)
    bottlenecks: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


# ============================================================================
# Profiling Functions
# ============================================================================

def create_operator(cube_size: int) -> Operator:
    """Create an operator and cube for testing."""
    sp = ProfileServiceProvider()
    cube = Cube(cube_size, sp=sp)
    config = AppConfig()
    vs = ApplicationAndViewState(config)
    return Operator(cube, vs)


def scramble_cube(op: Operator, seed: int, n_moves: int | None = None) -> int:
    """Scramble a cube and return number of moves."""
    alg = Algs.scramble(op.cube.size, seed, n_moves)
    op.play(alg, animation=False)
    return alg.count()


def solve_cube(solver: Solver, op: Operator) -> tuple[bool, int, float, str | None]:
    """
    Solve a cube and return (success, moves, time_ms, error).
    """
    start_moves = op.count
    start_time = time.perf_counter()
    error: str | None = None

    try:
        solver.solve(animation=False, debug=False)
        success = solver.is_solved
        if not success:
            error = "Cube not solved after solve() returned"
    except Exception as e:
        success = False
        error = str(e)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    moves = op.count - start_moves

    return success, moves, elapsed_ms, error


def profile_solver(
    solver_name: SolverName,
    cube_size: int,
    n_solves: int = 5,
    scramble_moves: int | None = None,
    with_cprofile: bool = True
) -> ProfileResult:
    """Profile a solver with multiple solves."""

    # Check if solver supports this cube size
    skip_reason = solver_name.meta.get_skip_reason(cube_size)
    if skip_reason:
        return ProfileResult(
            solver_name=solver_name.display_name,
            cube_size=cube_size,
            total_solves=0,
            successful_solves=0,
            failed_solves=0,
            total_time_ms=0,
            avg_time_ms=0,
            min_time_ms=0,
            max_time_ms=0,
            avg_moves=0,
            total_moves=0,
            moves_per_second=0,
            top_functions=[{"skip_reason": skip_reason}]
        )

    results: list[SolveResult] = []
    profiler = cProfile.Profile() if with_cprofile else None

    for seed in range(n_solves):
        op = create_operator(cube_size)
        solver = Solvers.by_name(solver_name, op)

        # Scramble
        n_scramble = scramble_moves or (cube_size * 10)
        scramble_count = scramble_cube(op, seed, n_scramble)

        # Solve with optional profiling (cube is accessed via op)
        if profiler:
            profiler.enable()

        success, moves, time_ms, error = solve_cube(solver, op)

        if profiler:
            profiler.disable()

        results.append(SolveResult(
            solver_name=solver_name.display_name,
            cube_size=cube_size,
            scramble_seed=seed,
            scramble_moves=scramble_count,
            solve_moves=moves,
            solve_time_ms=time_ms,
            success=success,
            error=error
        ))

    # Aggregate results
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    if successful:
        times = [r.solve_time_ms for r in successful]
        moves_list = [r.solve_moves for r in successful]
        total_time = sum(times)
        total_moves = sum(moves_list)
        avg_time = total_time / len(successful)
        avg_moves = total_moves / len(successful)
        moves_per_sec = (total_moves / total_time * 1000) if total_time > 0 else 0
    else:
        total_time = 0
        total_moves = 0
        avg_time = 0
        avg_moves = 0
        moves_per_sec = 0
        times = [0]

    # Extract top functions from profiler
    top_functions: list[dict[str, Any]] = []
    if profiler and successful:
        stats = pstats.Stats(profiler)
        stats.strip_dirs()
        stats.sort_stats('cumulative')

        # Get top 20 functions - access stats dict (pstats internal)
        # Format: {(filename, line, name): (cc, nc, tt, ct, callers)}
        stats_dict: dict[tuple[str, int, str], tuple[int, int, float, float, dict[Any, Any]]] = getattr(stats, 'stats', {})
        for func, func_stats in sorted(
            stats_dict.items(), key=lambda x: x[1][3], reverse=True
        )[:20]:
            _cc, nc, tt, ct, _callers = func_stats
            filename, line, name = func
            top_functions.append({
                "function": f"{filename}:{line}:{name}",
                "ncalls": nc,
                "tottime": round(tt * 1000, 2),  # ms
                "cumtime": round(ct * 1000, 2),  # ms
                "percall": round(ct / nc * 1000, 4) if nc > 0 else 0  # ms
            })

    return ProfileResult(
        solver_name=solver_name.display_name,
        cube_size=cube_size,
        total_solves=len(results),
        successful_solves=len(successful),
        failed_solves=len(failed),
        total_time_ms=total_time,
        avg_time_ms=avg_time,
        min_time_ms=min(times),
        max_time_ms=max(times),
        avg_moves=avg_moves,
        total_moves=total_moves,
        moves_per_second=moves_per_sec,
        top_functions=top_functions
    )


def analyze_bottlenecks(results: list[ProfileResult]) -> tuple[list[str], list[str]]:
    """Analyze results and identify bottlenecks and suggestions."""
    bottlenecks: list[str] = []
    suggestions: list[str] = []

    # Aggregate function stats across all profiles
    function_totals: dict[str, dict[str, float]] = {}

    for result in results:
        for func in result.top_functions:
            if "skip_reason" in func:
                continue
            name = func["function"]
            if name not in function_totals:
                function_totals[name] = {"cumtime": 0, "tottime": 0, "ncalls": 0}
            function_totals[name]["cumtime"] += func["cumtime"]
            function_totals[name]["tottime"] += func["tottime"]
            function_totals[name]["ncalls"] += func["ncalls"]

    # Sort by cumulative time
    sorted_funcs = sorted(
        function_totals.items(),
        key=lambda x: x[1]["cumtime"],
        reverse=True
    )

    # Identify bottlenecks (top functions consuming >5% of total time)
    if sorted_funcs:
        total_time = sorted_funcs[0][1]["cumtime"]  # Top function's cumtime approximates total
        for name, stats in sorted_funcs[:10]:
            pct = (stats["cumtime"] / total_time * 100) if total_time > 0 else 0
            if pct > 5:
                bottlenecks.append(
                    f"{name}: {stats['cumtime']:.1f}ms ({pct:.1f}%) - {int(stats['ncalls'])} calls"
                )

    # Generate suggestions based on patterns
    for name, stats in sorted_funcs[:20]:
        name_lower = name.lower()

        # Cache-related
        if "cache" in name_lower or "colors_id" in name_lower or "position_id" in name_lower:
            if stats["ncalls"] > 1000:
                suggestions.append(
                    f"High cache access in {name} ({int(stats['ncalls'])} calls). "
                    "Consider batch operations or reducing cache invalidation."
                )

        # Part/Slice operations
        if "partslice" in name_lower or "partedge" in name_lower:
            if stats["tottime"] > 100:
                suggestions.append(
                    f"Expensive Part operations in {name}. "
                    "Consider optimizing data structures or reducing allocations."
                )

        # Face operations
        if "face" in name_lower and "rotate" in name_lower:
            if stats["ncalls"] > 500:
                suggestions.append(
                    f"Many face rotations ({int(stats['ncalls'])}). "
                    "Verify algorithm efficiency or consider move coalescing."
                )

        # Tracker operations
        if "tracker" in name_lower:
            if stats["cumtime"] > 50:
                suggestions.append(
                    f"Tracker overhead in {name}: {stats['cumtime']:.1f}ms. "
                    "Consider caching tracker state or reducing queries."
                )

    # Compare solvers
    solver_times: dict[str, list[float]] = {}
    for result in results:
        if result.successful_solves > 0:
            name = result.solver_name
            if name not in solver_times:
                solver_times[name] = []
            solver_times[name].append(result.avg_time_ms)

    if len(solver_times) > 1:
        avg_by_solver = {k: sum(v) / len(v) for k, v in solver_times.items()}
        fastest = min(avg_by_solver.items(), key=lambda x: x[1])
        slowest = max(avg_by_solver.items(), key=lambda x: x[1])
        if slowest[1] > fastest[1] * 2:
            suggestions.append(
                f"{slowest[0]} is {slowest[1]/fastest[1]:.1f}x slower than {fastest[0]}. "
                "Consider algorithm analysis for {slowest[0]}."
            )

    return bottlenecks, suggestions


def print_result(result: ProfileResult) -> None:
    """Print a single profile result."""
    print(f"\n{'='*70}")
    print(f"Solver: {result.solver_name} | Cube: {result.cube_size}x{result.cube_size}")
    print(f"{'='*70}")

    if result.total_solves == 0:
        skip = result.top_functions[0].get("skip_reason", "Unknown") if result.top_functions else "Unknown"
        print(f"SKIPPED: {skip}")
        return

    print(f"Solves: {result.successful_solves}/{result.total_solves} successful")
    if result.failed_solves > 0:
        print(f"  (!) {result.failed_solves} failed")

    if result.successful_solves > 0:
        print(f"\nTiming:")
        print(f"  Total: {result.total_time_ms:.1f}ms")
        print(f"  Avg:   {result.avg_time_ms:.1f}ms")
        print(f"  Min:   {result.min_time_ms:.1f}ms")
        print(f"  Max:   {result.max_time_ms:.1f}ms")

        print(f"\nMoves:")
        print(f"  Total: {result.total_moves}")
        print(f"  Avg:   {result.avg_moves:.1f}")
        print(f"  Rate:  {result.moves_per_second:.0f} moves/sec")

        if result.top_functions and "skip_reason" not in result.top_functions[0]:
            print(f"\nTop Functions (by cumulative time):")
            for i, func in enumerate(result.top_functions[:10], 1):
                print(f"  {i:2}. {func['function']}")
                print(f"      cumtime={func['cumtime']:.1f}ms  tottime={func['tottime']:.1f}ms  "
                      f"ncalls={func['ncalls']}")


def run_benchmark(
    solvers: list[SolverName] | None = None,
    sizes: list[int] | None = None,
    n_solves: int = 5,
    with_cprofile: bool = True,
    cache_enabled: bool = True
) -> BenchmarkReport:
    """Run a complete benchmark."""
    import datetime

    # Set cache mode
    cfg.ENABLE_CUBE_CACHE = cache_enabled

    # Default solvers and sizes
    if solvers is None:
        solvers = SolverName.implemented()
    if sizes is None:
        sizes = [3, 4, 5]

    print(f"\n{'#'*70}")
    print(f"# CUBE SOLVER PROFILER")
    print(f"# Cache: {'ENABLED' if cache_enabled else 'DISABLED'}")
    print(f"# cProfile: {'ENABLED' if with_cprofile else 'DISABLED'}")
    print(f"# Solvers: {', '.join(s.display_name for s in solvers)}")
    print(f"# Sizes: {', '.join(f'{s}x{s}' for s in sizes)}")
    print(f"# Solves per config: {n_solves}")
    print(f"{'#'*70}")

    results: list[ProfileResult] = []

    for solver in solvers:
        for size in sizes:
            print(f"\nProfiling {solver.display_name} on {size}x{size}...", end=" ", flush=True)
            result = profile_solver(solver, size, n_solves, with_cprofile=with_cprofile)
            results.append(result)
            if result.successful_solves > 0:
                print(f"{result.avg_time_ms:.1f}ms avg")
            elif result.top_functions and "skip_reason" in result.top_functions[0]:
                print(f"SKIPPED")
            else:
                print(f"FAILED")

    # Analyze bottlenecks
    bottlenecks, suggestions = analyze_bottlenecks(results)

    # Create report
    report = BenchmarkReport(
        timestamp=datetime.datetime.now().isoformat(),
        python_version=sys.version,
        cache_enabled=cache_enabled,
        results=results,
        bottlenecks=bottlenecks,
        suggestions=suggestions
    )

    return report


def print_report(report: BenchmarkReport) -> None:
    """Print the complete report."""
    for result in report.results:
        print_result(result)

    if report.bottlenecks:
        print(f"\n{'='*70}")
        print("BOTTLENECKS IDENTIFIED")
        print(f"{'='*70}")
        for i, b in enumerate(report.bottlenecks, 1):
            print(f"  {i}. {b}")

    if report.suggestions:
        print(f"\n{'='*70}")
        print("OPTIMIZATION SUGGESTIONS")
        print(f"{'='*70}")
        for i, s in enumerate(report.suggestions, 1):
            print(f"  {i}. {s}")

    # Summary table
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"{'Solver':<12} {'Size':>6} {'Solves':>8} {'Avg ms':>10} {'Moves/s':>10}")
    print("-" * 50)
    for r in report.results:
        if r.successful_solves > 0:
            print(f"{r.solver_name:<12} {r.cube_size:>4}x{r.cube_size:<1} "
                  f"{r.successful_solves:>8} {r.avg_time_ms:>10.1f} {r.moves_per_second:>10.0f}")
        else:
            skip = "SKIP" if r.top_functions and "skip_reason" in r.top_functions[0] else "FAIL"
            print(f"{r.solver_name:<12} {r.cube_size:>4}x{r.cube_size:<1} {skip:>8}")


def save_report(report: BenchmarkReport, filepath: str) -> None:
    """Save report to JSON file."""
    # Convert to dict
    data = {
        "timestamp": report.timestamp,
        "python_version": report.python_version,
        "cache_enabled": report.cache_enabled,
        "results": [asdict(r) for r in report.results],
        "bottlenecks": report.bottlenecks,
        "suggestions": report.suggestions
    }
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nReport saved to: {filepath}")


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile cube solvers and identify bottlenecks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Quick benchmark without cProfile (faster, less detail)"
    )
    parser.add_argument(
        "--solver", "-s", type=str,
        help="Profile specific solver (LBL, CFOP, KOCIEMBA, CAGE)"
    )
    parser.add_argument(
        "--size", "-z", type=int,
        help="Profile specific cube size (3, 4, 5, etc.)"
    )
    parser.add_argument(
        "--sizes", type=str,
        help="Comma-separated cube sizes (e.g., '3,4,5,8')"
    )
    parser.add_argument(
        "--solves", "-n", type=int, default=5,
        help="Number of solves per configuration (default: 5)"
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Run with cache disabled"
    )
    parser.add_argument(
        "--output", "-o", type=str,
        help="Save report to JSON file"
    )
    parser.add_argument(
        "--compare-cache", action="store_true",
        help="Compare performance with and without cache"
    )

    args = parser.parse_args()

    # Determine solvers to profile
    solvers: list[SolverName] | None = None
    if args.solver:
        try:
            solvers = [SolverName.lookup(args.solver)]
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    # Determine sizes to profile
    sizes: list[int] | None = None
    if args.size:
        sizes = [args.size]
    elif args.sizes:
        sizes = [int(s.strip()) for s in args.sizes.split(",")]

    # Compare cache modes
    if args.compare_cache:
        print("\n" + "=" * 70)
        print("COMPARING CACHE ENABLED VS DISABLED")
        print("=" * 70)

        report_cached = run_benchmark(
            solvers=solvers,
            sizes=sizes,
            n_solves=args.solves,
            with_cprofile=not args.quick,
            cache_enabled=True
        )

        report_uncached = run_benchmark(
            solvers=solvers,
            sizes=sizes,
            n_solves=args.solves,
            with_cprofile=not args.quick,
            cache_enabled=False
        )

        # Print comparison
        print(f"\n{'='*70}")
        print("CACHE COMPARISON")
        print(f"{'='*70}")
        print(f"{'Solver':<12} {'Size':>6} {'Cached':>12} {'Uncached':>12} {'Speedup':>10}")
        print("-" * 56)

        for r_cached, r_uncached in zip(report_cached.results, report_uncached.results):
            if r_cached.successful_solves > 0 and r_uncached.successful_solves > 0:
                speedup = r_uncached.avg_time_ms / r_cached.avg_time_ms
                print(f"{r_cached.solver_name:<12} {r_cached.cube_size:>4}x{r_cached.cube_size:<1} "
                      f"{r_cached.avg_time_ms:>10.1f}ms {r_uncached.avg_time_ms:>10.1f}ms "
                      f"{speedup:>9.2f}x")

        if args.output:
            save_report(report_cached, args.output.replace(".json", "_cached.json"))
            save_report(report_uncached, args.output.replace(".json", "_uncached.json"))
    else:
        # Single run
        report = run_benchmark(
            solvers=solvers,
            sizes=sizes,
            n_solves=args.solves,
            with_cprofile=not args.quick,
            cache_enabled=not args.no_cache
        )

        print_report(report)

        if args.output:
            save_report(report, args.output)


if __name__ == "__main__":
    main()
