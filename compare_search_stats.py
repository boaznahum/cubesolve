#!/usr/bin/env python
"""Compare block statistics between old and new search methods."""
from __future__ import annotations

from cube.domain.algs import Algs
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
from cube.domain.solver.solver import SolveStep


def run_test(use_new_search: bool) -> dict[int, int]:
    """Run solver and return block statistics."""
    # Monkey-patch the toggle
    import cube.domain.solver.direct.lbl._LBLNxNCenters as lbl_module

    # Create cube and solver
    app = AbstractApp.create_non_default(cube_size=12, animation=False)
    solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)

    # Apply scramble
    alg = Algs.E[1:4] + Algs.E[7:8]
    app.op.play(alg)

    # Solve
    solver.solve(what=SolveStep.ALL, debug=False, animation=False)

    # Get statistics
    stats = solver.get_statistics()
    print(f"\n{'='*60}")
    print(f"Search method: {'NEW (CommutatorHelper.search_big_block)' if use_new_search else 'OLD (_search_blocks_starting_at)'}")
    print(f"{'='*60}")
    print(f"Block statistics: {stats}")
    print(f"Total blocks: {sum(stats.values())}")
    print(f"Total pieces moved: {sum(size * count for size, count in stats.items())}")

    # Print breakdown
    for size in sorted(stats.keys()):
        count = stats[size]
        print(f"  {size}x1 blocks: {count}")

    return stats


if __name__ == "__main__":
    print("Running comparison test...")
    print("\n" + "="*60)
    print("TEST 1: OLD SEARCH METHOD")
    print("="*60)
    # We'll need to manually toggle the USE_NEW_SEARCH variable
    # For now, just run once
    stats = run_test(use_new_search=False)
    print("\nTest completed!")
