"""Detailed profiling of Face.rotate to identify exact bottlenecks.

Run with: python -m tests.performance.profile_face_rotate
"""
from __future__ import annotations

import cProfile
import os
import pstats
import sys
import time
from io import StringIO
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

os.environ["CUBE_QUIET_ALL"] = "1"

from cube.application.config_impl import AppConfig
from cube.application.Logger import Logger
from cube.application.markers import IMarkerFactory, IMarkerManager, MarkerFactory, MarkerManager
from cube.domain.algs import Algs
from cube.domain.model.Cube import Cube
from cube.utils.config_protocol import ConfigProtocol
from cube.utils.logger_protocol import ILogger
from cube.utils.service_provider import IServiceProvider


class ProfileServiceProvider(IServiceProvider):
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


def profile_face_rotate(cube_size: int, n_rotations: int) -> None:
    """Profile face rotations in isolation."""
    sp = ProfileServiceProvider()
    cube = Cube(cube_size, sp=sp)

    # Get the front face
    face = cube.front

    # Warm up
    for _ in range(10):
        face.rotate(1)
        face.rotate(-1)

    print(f"\n{'='*70}")
    print(f"Profiling Face.rotate on {cube_size}x{cube_size} cube")
    print(f"Rotations: {n_rotations}")
    print(f"{'='*70}\n")

    # Profile
    profiler = cProfile.Profile()
    start = time.perf_counter()
    profiler.enable()

    for _ in range(n_rotations):
        face.rotate(1)

    profiler.disable()
    elapsed = time.perf_counter() - start

    print(f"Total time: {elapsed*1000:.1f}ms")
    print(f"Time per rotation: {elapsed/n_rotations*1000:.3f}ms")
    print(f"Rotations per second: {n_rotations/elapsed:.0f}")

    # Print detailed stats
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats(30)
    print(s.getvalue())

    # Print by tottime (time in function itself)
    print("\n" + "="*70)
    print("Top functions by TOTAL time (time IN the function):")
    print("="*70 + "\n")
    s2 = StringIO()
    stats2 = pstats.Stats(profiler, stream=s2)
    stats2.strip_dirs()
    stats2.sort_stats('tottime')
    stats2.print_stats(30)
    print(s2.getvalue())


def profile_scramble(cube_size: int, n_moves: int, seed: int = 42) -> None:
    """Profile scramble which uses a mix of rotations."""
    sp = ProfileServiceProvider()
    cube = Cube(cube_size, sp=sp)
    alg = Algs.scramble(cube_size, seed, n_moves)

    print(f"\n{'='*70}")
    print(f"Profiling scramble on {cube_size}x{cube_size} cube")
    print(f"Moves: {n_moves}")
    print(f"{'='*70}\n")

    # Profile
    profiler = cProfile.Profile()
    start = time.perf_counter()
    profiler.enable()

    alg.play(cube)

    profiler.disable()
    elapsed = time.perf_counter() - start

    print(f"Total time: {elapsed*1000:.1f}ms")
    print(f"Time per move: {elapsed/n_moves*1000:.3f}ms")
    print(f"Moves per second: {n_moves/elapsed:.0f}")

    # Print detailed stats
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.strip_dirs()
    stats.sort_stats('tottime')  # Sort by time IN the function
    stats.print_stats(40)
    print(s.getvalue())


def profile_solve_detailed(cube_size: int, seed: int = 0) -> None:
    """Profile a solve with detailed breakdown by function."""
    from cube.application.state import ApplicationAndViewState
    from cube.application.commands.Operator import Operator
    from cube.domain.solver import Solvers

    sp = ProfileServiceProvider()
    cube = Cube(cube_size, sp=sp)
    config = AppConfig()
    vs = ApplicationAndViewState(config)
    op = Operator(cube, vs)
    solver = Solvers.beginner(op)

    # Scramble
    alg = Algs.scramble(cube_size, seed, cube_size * 10)
    op.play(alg, animation=False)

    print(f"\n{'='*70}")
    print(f"Profiling LBL solve on {cube_size}x{cube_size} cube")
    print(f"{'='*70}\n")

    # Profile solve
    profiler = cProfile.Profile()
    start = time.perf_counter()
    profiler.enable()

    solver.solve(animation=False, debug=False)

    profiler.disable()
    elapsed = time.perf_counter() - start

    print(f"Total solve time: {elapsed*1000:.1f}ms")
    print(f"Moves: {op.count}")

    # Print by tottime (time in function itself, excluding subcalls)
    print("\n" + "="*70)
    print("Top functions by TOTAL time (time spent IN the function body):")
    print("This shows where actual CPU cycles are being spent.")
    print("="*70 + "\n")
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.strip_dirs()
    stats.sort_stats('tottime')
    stats.print_stats(50)
    print(s.getvalue())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["rotate", "scramble", "solve"], default="solve")
    parser.add_argument("--size", type=int, default=5)
    parser.add_argument("--n", type=int, default=1000, help="Number of rotations/moves")
    args = parser.parse_args()

    if args.mode == "rotate":
        profile_face_rotate(args.size, args.n)
    elif args.mode == "scramble":
        profile_scramble(args.size, args.n)
    else:
        profile_solve_detailed(args.size)
