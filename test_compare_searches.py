#!/usr/bin/env python
"""Compare block statistics between old and new search methods."""
from __future__ import annotations

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
from cube.domain.solver.solver import SolveStep


def run_with_search_method(use_new: bool, seed: int = 12345) -> dict[int, int]:
    """Run solver with given search method and return statistics."""
    # Monkey-patch the USE_NEW_SEARCH variable
    import cube.domain.solver.direct.lbl._LBLNxNCenters as lbl_module

    # We need to patch it before the method is called
    # But since it's a local variable, we'll need to do this differently
    # For now, just read from the file to know which mode we're testing

    print(f"\n{'='*70}")
    print(f"Testing: {'NEW search_big_block()' if use_new else 'OLD _search_blocks_starting_at()'}")
    print(f"{'='*70}")

    # Create cube and solver
    app = AbstractApp.create_app(cube_size=12)
    solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)

    # Apply random scramble
    print(f"Scrambling with seed {seed}...")
    app.scramble(seed, None, animation=False, verbose=False)

    # Solve
    print(f"Solving...")
    solver.solve(what=SolveStep.ALL, debug=False, animation=False)

    # Get statistics
    stats = solver.get_statistics()

    # Print stats
    total_blocks = sum(stats.values())
    total_pieces = sum(size * count for size, count in stats.items())

    print(f"\nStatistics:")
    print(f"  Total blocks: {total_blocks}")
    print(f"  Total pieces moved: {total_pieces}")
    if stats:
        print(f"  Breakdown:")
        for size in sorted(stats.keys()):
            count = stats[size]
            print(f"    {size}x1 blocks: {count} (total: {size*count} pieces)")
    else:
        print(f"  (No blocks - centers didn't need solving)")

    return stats


if __name__ == "__main__":
    # Run with both methods
    print("\n" + "="*70)
    print("COMPARISON TEST: OLD vs NEW BLOCK SEARCH")
    print("="*70)

    # First, check which method is currently enabled and report
    with open("src/cube/domain/solver/direct/lbl/_LBLNxNCenters.py", encoding="utf-8") as f:
        content = f.read()
        if "USE_NEW_SEARCH = True" in content:
            current_method = "NEW"
        else:
            current_method = "OLD"

    print(f"\nCurrent implementation: {current_method}")
    print(f"\nNote: To test both methods, you need to manually toggle USE_NEW_SEARCH in _LBLNxNCenters.py")
    print(f"      and run this script twice.\n")

    stats = run_with_search_method(current_method == "NEW")

    if stats:
        print(f"\n✓ Test generated non-zero block statistics")
    else:
        print(f"\n[!] Test generated zero block statistics (try different seed)")
