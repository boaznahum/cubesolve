"""Profile cube scramble to find performance hotspots.

Run with: python -m tests.performance.profile_scramble
"""
import cProfile
import pstats
import sys
from io import StringIO
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cube.application import _config as cfg
from cube.domain.algs import Algs
from cube.domain.model.Cube import Cube
from cube.application.config_impl import AppConfig
from cube.application.Logger import Logger
from cube.application.markers import MarkerFactory, MarkerManager
from cube.utils.config_protocol import IServiceProvider, ConfigProtocol
from cube.utils.logger_protocol import ILogger
from cube.application.markers import IMarkerFactory, IMarkerManager


class ProfileServiceProvider(IServiceProvider):
    """Service provider for profiling."""
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


def run_scramble(cube_size: int, n_moves: int, seed: int) -> None:
    """Run a scramble on a cube."""
    sp = ProfileServiceProvider()
    cube = Cube(cube_size, sp=sp)
    alg = Algs.scramble(cube.size, seed, n_moves)
    alg.play(cube)


def profile_scramble(cube_size: int = 5, n_moves: int = 1000, seed: int = 42,
                     with_cache: bool = True) -> None:
    """Profile scramble and print results."""

    # Set cache mode
    cfg.ENABLE_CUBE_CACHE = with_cache

    print(f"\n{'='*70}")
    print(f"Profiling {cube_size}x{cube_size} cube, {n_moves} moves, cache={'ON' if with_cache else 'OFF'}")
    print(f"{'='*70}\n")

    # Profile
    profiler = cProfile.Profile()
    profiler.enable()

    run_scramble(cube_size, n_moves, seed)

    profiler.disable()

    # Print results
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats(40)  # Top 40 functions by cumulative time
    print(s.getvalue())

    # Also print by total time in function
    print("\n" + "="*70)
    print("Top functions by TOTAL time (time spent IN the function):")
    print("="*70 + "\n")
    s2 = StringIO()
    stats2 = pstats.Stats(profiler, stream=s2)
    stats2.strip_dirs()
    stats2.sort_stats('tottime')
    stats2.print_stats(30)
    print(s2.getvalue())


if __name__ == "__main__":
    import os
    os.environ["CUBE_QUIET_ALL"] = "1"

    # Profile with cache disabled first
    profile_scramble(cube_size=5, n_moves=500, with_cache=False)

    # Profile with cache enabled
    profile_scramble(cube_size=5, n_moves=500, with_cache=True)
