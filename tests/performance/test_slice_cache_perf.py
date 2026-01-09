"""Performance comparison for Slice caching.

Compares slice rotation performance with cache enabled vs disabled.
Run with: pytest tests/performance/test_slice_cache_perf.py -v -s
"""
import time

import pytest

from cube.application import _config as cfg
from cube.domain.algs import Algs
from cube.domain.model.Cube import Cube
from tests.test_utils import TestServiceProvider


def _scramble_cube(cube: Cube, n_moves: int, seed: int) -> float:
    """Scramble cube and return elapsed time in seconds."""
    alg = Algs.scramble(cube.size, seed, n_moves)
    start = time.perf_counter()
    alg.play(cube)
    elapsed = time.perf_counter() - start
    return elapsed


@pytest.mark.slow
@pytest.mark.benchmark
def test_slice_cache_performance():
    """Compare slice rotation performance with and without cache.

    This test measures the time to perform many scrambles (which include
    slice rotations M, E, S) with caching enabled vs disabled.
    """
    # Test parameters
    cube_size = 5  # 5x5 has n_slices=3, good for testing
    n_scrambles = 20
    moves_per_scramble = 100

    # Store original config value
    original_cache_setting = cfg.ENABLE_CUBE_CACHE

    try:
        # ===== Test WITHOUT cache =====
        cfg.ENABLE_CUBE_CACHE = False
        sp_no_cache = TestServiceProvider()

        total_time_no_cache = 0.0
        for seed in range(n_scrambles):
            cube = Cube(cube_size, sp=sp_no_cache)
            elapsed = _scramble_cube(cube, moves_per_scramble, seed)
            total_time_no_cache += elapsed

        # ===== Test WITH cache =====
        cfg.ENABLE_CUBE_CACHE = True
        sp_with_cache = TestServiceProvider()

        total_time_with_cache = 0.0
        for seed in range(n_scrambles):
            cube = Cube(cube_size, sp=sp_with_cache)
            elapsed = _scramble_cube(cube, moves_per_scramble, seed)
            total_time_with_cache += elapsed

        # Calculate statistics
        total_moves = n_scrambles * moves_per_scramble
        speedup = total_time_no_cache / total_time_with_cache if total_time_with_cache > 0 else 0

        # Report results
        print(f"\n{'='*60}")
        print(f"Slice Cache Performance Test")
        print(f"{'='*60}")
        print(f"Cube size: {cube_size}x{cube_size}")
        print(f"Total moves: {total_moves} ({n_scrambles} scrambles x {moves_per_scramble} moves)")
        print(f"")
        print(f"WITHOUT cache: {total_time_no_cache:.3f}s ({total_moves/total_time_no_cache:.0f} moves/s)")
        print(f"WITH cache:    {total_time_with_cache:.3f}s ({total_moves/total_time_with_cache:.0f} moves/s)")
        print(f"")
        print(f"Speedup: {speedup:.2f}x")
        print(f"{'='*60}")

        # Basic sanity check - cache should not be slower
        # (Allow some margin for measurement noise)
        assert speedup >= 0.9, f"Cache unexpectedly slower: {speedup:.2f}x"

    finally:
        # Restore original config
        cfg.ENABLE_CUBE_CACHE = original_cache_setting


@pytest.mark.slow
@pytest.mark.benchmark
def test_slice_only_rotations():
    """Test slice-only rotations (M, E, S) to isolate caching effect.

    This test focuses specifically on slice rotations where the cache
    has the most impact.
    """
    cube_size = 5
    n_iterations = 100

    # Store original config value
    original_cache_setting = cfg.ENABLE_CUBE_CACHE

    try:
        # ===== Test WITHOUT cache =====
        cfg.ENABLE_CUBE_CACHE = False
        sp_no_cache = TestServiceProvider()
        cube = Cube(cube_size, sp=sp_no_cache)

        start = time.perf_counter()
        for _ in range(n_iterations):
            Algs.M.play(cube)
            Algs.E.play(cube)
            Algs.S.play(cube)
        time_no_cache = time.perf_counter() - start

        # ===== Test WITH cache =====
        cfg.ENABLE_CUBE_CACHE = True
        sp_with_cache = TestServiceProvider()
        cube = Cube(cube_size, sp=sp_with_cache)

        start = time.perf_counter()
        for _ in range(n_iterations):
            Algs.M.play(cube)
            Algs.E.play(cube)
            Algs.S.play(cube)
        time_with_cache = time.perf_counter() - start

        # Calculate statistics
        total_moves = n_iterations * 3  # M, E, S each iteration
        speedup = time_no_cache / time_with_cache if time_with_cache > 0 else 0

        # Report results
        print(f"\n{'='*60}")
        print(f"Slice-Only Rotation Test (M, E, S)")
        print(f"{'='*60}")
        print(f"Cube size: {cube_size}x{cube_size}")
        print(f"Total slice rotations: {total_moves}")
        print(f"")
        print(f"WITHOUT cache: {time_no_cache:.3f}s ({total_moves/time_no_cache:.0f} ops/s)")
        print(f"WITH cache:    {time_with_cache:.3f}s ({total_moves/time_with_cache:.0f} ops/s)")
        print(f"")
        print(f"Speedup: {speedup:.2f}x")
        print(f"{'='*60}")

    finally:
        # Restore original config
        cfg.ENABLE_CUBE_CACHE = original_cache_setting
