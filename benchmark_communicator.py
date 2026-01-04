"""
Performance comparison: Old vs New (without cache) vs New (with cache) CommunicatorHelper API.

This benchmark compares three approaches for executing communicator operations:
1. OLD: separate get_natural_source_ltr() + do_communicator() calls
2. NEW_NO_CACHE: single execute_communicator() without caching
3. NEW_WITH_CACHE: dry_run=True, then execute_communicator() with _cached_secret

Run with: python benchmark_communicator.py
"""

import time
from typing import Tuple

from cube.application.AbstractApp import AbstractApp
from cube.domain.model.Face import Face
from cube.domain.model.cube_layout.cube_boy import FaceName
from cube.domain.solver.common.big_cube.commun.CommunicatorHelper import CommunicatorHelper
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver

Point = Tuple[int, int]


def benchmark_old_method(helper: CommunicatorHelper, source_face: Face, target_face: Face,
                        target_point: Point, source_point: Point, iterations: int = 100) -> float:
    """OLD API: Two separate calls."""
    start = time.perf_counter()

    for _ in range(iterations):
        # Reset cube for clean state
        cube = helper.cube
        cube.reset()

        # OLD: Two separate calls
        # Step 1: Get natural source position
        natural_source = helper.get_natural_source_ltr(source_face, target_face, target_point)

        # Step 2: Execute communicator
        _ = helper.do_communicator(
            source_face=source_face,
            target_face=target_face,
            target_block=(target_point, target_point),
            source_block=(source_point, source_point),
            preserve_state=True
        )

    elapsed = time.perf_counter() - start
    return elapsed


def benchmark_new_no_cache(helper: CommunicatorHelper, source_face: Face, target_face: Face,
                          target_point: Point, source_point: Point, iterations: int = 100) -> float:
    """NEW API: Single call without caching."""
    start = time.perf_counter()

    for _ in range(iterations):
        # Reset cube for clean state
        cube = helper.cube
        cube.reset()

        # NEW (NO CACHE): Single call, dry_run=False, no _cached_secret
        result = helper.execute_communicator(
            source_face=source_face,
            target_face=target_face,
            target_block=(target_point, target_point),
            source_block=(source_point, source_point),
            preserve_state=True,
            dry_run=False
        )

    elapsed = time.perf_counter() - start
    return elapsed


def benchmark_new_with_cache(helper: CommunicatorHelper, source_face: Face, target_face: Face,
                            target_point: Point, source_point: Point, iterations: int = 100) -> float:
    """NEW API: With optimization - dry_run first, then execute with cache."""
    start = time.perf_counter()

    for _ in range(iterations):
        # Reset cube for clean state
        cube = helper.cube
        cube.reset()

        # NEW (WITH CACHE): Two-phase approach
        # Phase 1: Dry run to get source position and cache computation
        dry_result = helper.execute_communicator(
            source_face=source_face,
            target_face=target_face,
            target_block=(target_point, target_point),
            dry_run=True
        )

        # Phase 2: Execute with cached computation
        result = helper.execute_communicator(
            source_face=source_face,
            target_face=target_face,
            target_block=(target_point, target_point),
            source_block=(source_point, source_point),
            preserve_state=True,
            dry_run=False,
            _cached_secret=dry_result  # ← OPTIMIZATION: Reuse computation
        )

    elapsed = time.perf_counter() - start
    return elapsed


def main():
    """Run benchmarks for all three approaches."""
    print("=" * 80)
    print("CommunicatorHelper Performance Benchmark")
    print("=" * 80)
    print()

    # Configuration
    CUBE_SIZE = 7  # 7x7 cube
    ITERATIONS = 100  # Run each benchmark 100 times
    FACE_PAIR = (FaceName.U, FaceName.F)
    TARGET_POINT = (2, 1)  # Use middle position
    SOURCE_POINT = (2, 1)

    print(f"Configuration:")
    print(f"  Cube Size: {CUBE_SIZE}x{CUBE_SIZE}")
    print(f"  Iterations per benchmark: {ITERATIONS}")
    print(f"  Face Pair: {FACE_PAIR[0].name} → {FACE_PAIR[1].name}")
    print(f"  Target Position (LTR): {TARGET_POINT}")
    print(f"  Source Position (LTR): {SOURCE_POINT}")
    print(f"  Animation: DISABLED (animation=False)")
    print()

    # Create test environment with animation disabled
    print("Setting up test environment...")
    app = AbstractApp.create_non_default(cube_size=CUBE_SIZE, animation=False)
    solver = CageNxNSolver(app.op)
    helper = CommunicatorHelper(solver)
    cube = app.cube

    source_face = cube.face(FACE_PAIR[0])
    target_face = cube.face(FACE_PAIR[1])

    print(f"✓ Created {CUBE_SIZE}x{CUBE_SIZE} cube with animation disabled")
    print()

    # Run benchmarks
    print("Running benchmarks...")
    print("-" * 80)

    # Benchmark 1: OLD
    print(f"\n1️⃣  OLD METHOD (two separate calls)")
    print("   get_natural_source_ltr() + do_communicator()")
    time_old = benchmark_old_method(helper, source_face, target_face, TARGET_POINT, SOURCE_POINT,
                                     ITERATIONS)
    print(f"   Time: {time_old:.4f}s ({time_old / ITERATIONS * 1000:.2f}ms per iteration)")

    # Benchmark 2: NEW without cache
    print(f"\n2️⃣  NEW METHOD (no caching)")
    print("   execute_communicator(dry_run=False) without _cached_secret")
    time_new_no_cache = benchmark_new_no_cache(helper, source_face, target_face, TARGET_POINT,
                                                SOURCE_POINT, ITERATIONS)
    print(
        f"   Time: {time_new_no_cache:.4f}s ({time_new_no_cache / ITERATIONS * 1000:.2f}ms per iteration)")

    # Benchmark 3: NEW with cache
    print(f"\n3️⃣  NEW METHOD (with caching)")
    print("   execute_communicator(dry_run=True) + execute_communicator(dry_run=False, _cached_secret=result)")
    time_new_with_cache = benchmark_new_with_cache(helper, source_face, target_face, TARGET_POINT,
                                                     SOURCE_POINT, ITERATIONS)
    print(
        f"   Time: {time_new_with_cache:.4f}s ({time_new_with_cache / ITERATIONS * 1000:.2f}ms per iteration)")

    # Print results
    print()
    print("=" * 80)
    print("RESULTS & ANALYSIS")
    print("=" * 80)

    # Baseline
    baseline = time_old
    print(f"\nBaseline (OLD): {time_old:.4f}s")
    print()

    # New without cache
    diff_no_cache = time_new_no_cache - baseline
    pct_no_cache = (diff_no_cache / baseline) * 100
    improvement_no_cache = "slower" if diff_no_cache > 0 else "faster"
    print(f"NEW (no cache): {time_new_no_cache:.4f}s")
    print(f"  Difference: {abs(diff_no_cache):+.4f}s ({pct_no_cache:+.1f}%) {improvement_no_cache}")

    # New with cache
    diff_with_cache = time_new_with_cache - baseline
    pct_with_cache = (diff_with_cache / baseline) * 100
    improvement_with_cache = "slower" if diff_with_cache > 0 else "faster"
    print(f"\nNEW (with cache): {time_new_with_cache:.4f}s")
    print(f"  Difference: {abs(diff_with_cache):+.4f}s ({pct_with_cache:+.1f}%) {improvement_with_cache}")

    # Cache benefit
    cache_benefit = time_new_no_cache - time_new_with_cache
    cache_pct = (cache_benefit / time_new_no_cache) * 100 if time_new_no_cache > 0 else 0
    print(f"\n💾 Cache Optimization Benefit: {cache_benefit:.4f}s ({cache_pct:.1f}% faster with cache)")

    # Per-iteration breakdown
    print()
    print("Per-iteration timings:")
    print(f"  OLD:                {time_old / ITERATIONS * 1000:7.3f} ms")
    print(f"  NEW (no cache):     {time_new_no_cache / ITERATIONS * 1000:7.3f} ms")
    print(f"  NEW (with cache):   {time_new_with_cache / ITERATIONS * 1000:7.3f} ms")

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if abs(diff_with_cache) < baseline * 0.1:  # Within 10% of baseline
        status = "✅ OPTIMIZED - New API with cache performs comparably"
    elif diff_with_cache < 0:
        status = f"✅ FASTER - New API with cache is {abs(pct_with_cache):.1f}% faster"
    else:
        status = f"⚠️  SLOWER - New API with cache is {pct_with_cache:.1f}% slower"

    print(f"{status}")
    print()
    print(f"Recommendation: Use NEW API with caching for {cache_pct:.1f}% improvement")
    print("=" * 80)


if __name__ == "__main__":
    main()
