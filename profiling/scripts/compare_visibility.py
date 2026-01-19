"""Compare solver performance with has_visible_presentation True vs False.

This script measures the performance impact of texture direction updates
by running solvers with visibility enabled and disabled.

Usage:
    # Quick timing comparison
    python -m profiling.scripts.compare_visibility

    # With cProfile details
    python -m profiling.scripts.compare_visibility --profile

    # Custom sizes and runs
    python -m profiling.scripts.compare_visibility --sizes 3,5,7 --runs 10

    # Output as markdown
    python -m profiling.scripts.compare_visibility --markdown
"""
from __future__ import annotations

import argparse
import cProfile
import os
import pstats
import sys
import time
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Suppress debug output
os.environ["CUBE_QUIET_ALL"] = "1"

from cube.application.config_impl import AppConfig
from cube.application.Logger import Logger
from cube.application.markers import MarkerFactory, MarkerManager
from cube.application.state import ApplicationAndViewState
from cube.application.commands.Operator import Operator
from cube.domain.algs import Algs
from cube.domain.model.Cube import Cube
from cube.domain.solver import Solvers
from cube.domain.solver.SolverName import SolverName
from cube.utils.service_provider import IServiceProvider


class TestServiceProvider(IServiceProvider):
    """Minimal service provider for benchmarking."""

    def __init__(self) -> None:
        self._config = AppConfig()
        self._mf = MarkerFactory()
        self._mm = MarkerManager()
        self._logger = Logger()

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def marker_factory(self) -> MarkerFactory:
        return self._mf

    @property
    def marker_manager(self) -> MarkerManager:
        return self._mm

    @property
    def logger(self) -> Logger:
        return self._logger


@dataclass
class ProfileStats:
    """Aggregated profiling statistics."""
    total_time_ms: float = 0.0
    top_functions: list[dict[str, Any]] = field(default_factory=list)


def extract_top_functions(profiler: cProfile.Profile, n: int = 15) -> list[dict[str, Any]]:
    """Extract top N functions from profiler by cumulative time."""
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats('cumulative')

    top_functions: list[dict[str, Any]] = []
    stats_dict = getattr(stats, 'stats', {})

    for func, func_stats in sorted(
        stats_dict.items(), key=lambda x: x[1][3], reverse=True
    )[:n]:
        _cc, nc, tt, ct, _callers = func_stats
        filename, line, name = func
        top_functions.append({
            "function": f"{filename}:{line}:{name}",
            "short_name": name,
            "ncalls": nc,
            "tottime_ms": round(tt * 1000, 2),
            "cumtime_ms": round(ct * 1000, 2),
        })

    return top_functions


def benchmark(
    cube_size: int,
    solver_name: SolverName,
    visible_presentation: bool,
    n_runs: int = 5,
    with_profile: bool = False
) -> tuple[float, ProfileStats | None]:
    """Run solver multiple times and return (avg_time_ms, profile_stats)."""
    times: list[float] = []
    profiler = cProfile.Profile() if with_profile else None

    for seed in range(n_runs):
        sp = TestServiceProvider()
        cube = Cube(cube_size, sp=sp)

        # Set visibility BEFORE any operations
        cube.has_visible_presentation = visible_presentation

        config = AppConfig()
        vs = ApplicationAndViewState(config)
        op = Operator(cube, vs)
        solver = Solvers.by_name(solver_name, op)

        # Scramble
        alg = Algs.scramble(cube_size, seed, cube_size * 10)
        op.play(alg, animation=False)

        # Solve and time (with optional profiling)
        if profiler:
            profiler.enable()

        start = time.perf_counter()
        solver.solve(animation=False, debug=False)
        elapsed = (time.perf_counter() - start) * 1000

        if profiler:
            profiler.disable()

        times.append(elapsed)

    avg_time = sum(times) / len(times)

    profile_stats = None
    if profiler:
        profile_stats = ProfileStats(
            total_time_ms=sum(times),
            top_functions=extract_top_functions(profiler)
        )

    return avg_time, profile_stats


@dataclass
class ComparisonResult:
    """Result of comparing visibility True vs False."""
    solver: str
    size: int
    time_false: float
    time_true: float
    slowdown: float
    profile_false: ProfileStats | None = None
    profile_true: ProfileStats | None = None
    skip: str | None = None


def run_comparison(
    sizes: list[int] | None = None,
    solvers: list[SolverName] | None = None,
    n_runs: int = 5,
    with_profile: bool = False
) -> list[ComparisonResult]:
    """Run comparison and return results."""
    if sizes is None:
        sizes = [3, 4, 5]
    if solvers is None:
        solvers = [SolverName.LBL, SolverName.CFOP, SolverName.KOCIEMBA]

    results: list[ComparisonResult] = []

    for solver in solvers:
        for size in sizes:
            skip = solver.meta.get_skip_reason(size)
            if skip:
                results.append(ComparisonResult(
                    solver=solver.display_name,
                    size=size,
                    time_false=0,
                    time_true=0,
                    slowdown=0,
                    skip=skip
                ))
                continue

            print(f"  Benchmarking {solver.display_name} {size}x{size}...", end=" ", flush=True)

            time_false, profile_false = benchmark(
                size, solver, False, n_runs=n_runs, with_profile=with_profile
            )
            time_true, profile_true = benchmark(
                size, solver, True, n_runs=n_runs, with_profile=with_profile
            )
            slowdown = time_true / time_false if time_false > 0 else 0

            print(f"False={time_false:.1f}ms, True={time_true:.1f}ms, slowdown={slowdown:.2f}x")

            results.append(ComparisonResult(
                solver=solver.display_name,
                size=size,
                time_false=time_false,
                time_true=time_true,
                slowdown=slowdown,
                profile_false=profile_false,
                profile_true=profile_true
            ))

    return results


def print_results(results: list[ComparisonResult], show_profile: bool = False) -> None:
    """Print results as a table."""
    print()
    print("=" * 80)
    print("PERFORMANCE COMPARISON: has_visible_presentation = False vs True")
    print("=" * 80)
    print()
    print(f"{'Solver':<12} {'Size':>6} {'False (ms)':>12} {'True (ms)':>12} {'Slowdown':>10}")
    print("-" * 54)

    for r in results:
        if r.skip:
            print(f"{r.solver:<12} {r.size:>4}x{r.size:<1} {'SKIP':>12} {'SKIP':>12}")
        else:
            print(
                f"{r.solver:<12} {r.size:>4}x{r.size:<1} "
                f"{r.time_false:>10.1f}ms {r.time_true:>10.1f}ms "
                f"{r.slowdown:>9.2f}x"
            )

    print()
    print("Slowdown = time with True / time with False")
    print("Higher slowdown = more time spent on texture updates when visible")

    # Show profile details if requested
    if show_profile:
        for r in results:
            if r.skip or not r.profile_false or not r.profile_true:
                continue

            print()
            print("=" * 80)
            print(f"PROFILE DETAILS: {r.solver} {r.size}x{r.size}")
            print("=" * 80)

            # Find functions that differ significantly
            false_funcs = {f["short_name"]: f for f in r.profile_false.top_functions}
            true_funcs = {f["short_name"]: f for f in r.profile_true.top_functions}

            # Show top functions from visible=True (these include texture updates)
            print()
            print("Top functions with visible=True:")
            print(f"  {'Function':<40} {'cumtime':>10} {'tottime':>10} {'ncalls':>10}")
            print("  " + "-" * 72)
            for f in r.profile_true.top_functions[:10]:
                print(
                    f"  {f['short_name']:<40} "
                    f"{f['cumtime_ms']:>8.1f}ms "
                    f"{f['tottime_ms']:>8.1f}ms "
                    f"{f['ncalls']:>10}"
                )

            # Show functions unique to visible=True or with much higher time
            print()
            print("Functions with significant overhead when visible=True:")
            print(f"  {'Function':<40} {'False':>10} {'True':>10} {'Diff':>10}")
            print("  " + "-" * 72)

            for name, true_f in true_funcs.items():
                false_f = false_funcs.get(name)
                if false_f:
                    diff = true_f["cumtime_ms"] - false_f["cumtime_ms"]
                    if diff > 1.0:  # Only show if diff > 1ms
                        print(
                            f"  {name:<40} "
                            f"{false_f['cumtime_ms']:>8.1f}ms "
                            f"{true_f['cumtime_ms']:>8.1f}ms "
                            f"{diff:>+8.1f}ms"
                        )
                else:
                    # Function only appears in True
                    if true_f["cumtime_ms"] > 1.0:
                        print(
                            f"  {name:<40} "
                            f"{'N/A':>10} "
                            f"{true_f['cumtime_ms']:>8.1f}ms "
                            f"{'(new)':>10}"
                        )


def print_markdown(results: list[ComparisonResult]) -> None:
    """Print results as markdown table."""
    print()
    print("| Solver | Size | False (ms) | True (ms) | Slowdown |")
    print("|--------|------|------------|-----------|----------|")

    for r in results:
        if r.skip:
            print(f"| {r.solver} | {r.size}x{r.size} | SKIP | SKIP | - |")
        else:
            print(
                f"| {r.solver} | {r.size}x{r.size} | "
                f"{r.time_false:.1f} | {r.time_true:.1f} | "
                f"{r.slowdown:.2f}x |"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare solver performance with visibility True vs False",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--sizes", type=str, default="3,4,5",
        help="Comma-separated cube sizes (default: 3,4,5)"
    )
    parser.add_argument(
        "--runs", "-n", type=int, default=5,
        help="Number of runs per configuration (default: 5)"
    )
    parser.add_argument(
        "--profile", "-p", action="store_true",
        help="Enable cProfile and show detailed function breakdown"
    )
    parser.add_argument(
        "--markdown", "-m", action="store_true",
        help="Output as markdown table"
    )

    args = parser.parse_args()

    sizes = [int(s.strip()) for s in args.sizes.split(",")]

    print()
    print("#" * 70)
    print("# VISIBILITY COMPARISON BENCHMARK")
    print(f"# Sizes: {', '.join(f'{s}x{s}' for s in sizes)}")
    print(f"# Runs per config: {args.runs}")
    print(f"# cProfile: {'ENABLED' if args.profile else 'DISABLED'}")
    print("#" * 70)
    print()

    results = run_comparison(
        sizes=sizes,
        n_runs=args.runs,
        with_profile=args.profile
    )

    if args.markdown:
        print_markdown(results)
    else:
        print_results(results, show_profile=args.profile)


if __name__ == "__main__":
    main()
