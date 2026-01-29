"""Tests that L3 edge solving does NOT modify already-solved edges.

The bug: _solve_layer3_edges() calls NxNEdges.solve_face_edges() which uses
algorithms that destroy L1 edges and middle-slice edge wings.

The fix: L3 edge solving must use only safe moves (U + commutators that
restore R/L/M moves).

This test verifies the fix by:plea
1. Solving up to L3 centers
2. Verifying L1 and middle slices are solved (using is_solved_phase)
3. Running L3 edge solving
4. Verifying L1 and middle slices are STILL solved
"""
from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
from cube.domain.solver.solver import SolveStep

# =============================================================================
# Test Configuration
# =============================================================================

# Odd cube sizes only (even cubes have different parity issues)
CUBE_SIZES_ODD: list[int] = [5, 7]

# Scramble seeds to test
SCRAMBLE_SEEDS: list[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


# =============================================================================
# Tests
# =============================================================================

class TestL3EdgesPreserveOthers:
    """Test that L3 edge solving preserves L1 and middle edges."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_ODD, ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize("scramble_seed", SCRAMBLE_SEEDS, ids=lambda s: f"seed_{s}")
    def test_l3_edges_do_not_modify_solved_edges(
        self,
        cube_size: int,
        scramble_seed: int,
    ) -> None:
        """L3 edge solving must not modify L1 or middle-slice edges."""

        # Setup
        app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
        solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)

        # Scramble
        app.scramble(scramble_seed, None, animation=False, verbose=False)

        # Solve up to L3 centers (L1 + middle slices + L3 centers)
        solver.solve(what=SolveStep.LBL_L3_CENTER, debug=False, animation=False)

        # Verify pre-conditions using is_solved_phase
        assert solver.is_solved_phase(SolveStep.LBL_L1), (
            f"Pre-condition failed: L1 not solved (size={cube_size}, seed={scramble_seed})"
        )
        assert solver.is_solved_phase(SolveStep.LBL_SLICES_CTR), (
            f"Pre-condition failed: middle slices not solved (size={cube_size}, seed={scramble_seed})"
        )
        assert solver.is_solved_phase(SolveStep.LBL_L3_CENTER), (
            f"Pre-condition failed: L3 centers not solved (size={cube_size}, seed={scramble_seed})"
        )

        # Now solve L3 edges (this is where the bug occurs)
        solver.solve(what=SolveStep.LBL_L3_CROSS, debug=False, animation=False)

        # Verify L1 and middle slices are STILL solved after L3 edges
        assert solver.is_solved_phase(SolveStep.LBL_L1), (
            f"BUG: L3 edge solving destroyed L1! (size={cube_size}, seed={scramble_seed})"
        )
        assert solver.is_solved_phase(SolveStep.LBL_SLICES_CTR), (
            f"BUG: L3 edge solving destroyed middle slices! (size={cube_size}, seed={scramble_seed})"
        )


class TestL3EdgesPreserveOthersExtended:
    """Extended tests with more scrambles for thorough coverage."""

    @pytest.mark.parametrize("cube_size", [5], ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_seed",
        list(range(0, 100)),  # Test 100 scrambles
        ids=lambda s: f"seed_{s}",
    )
    def test_l3_edges_5x5_many_scrambles(
        self,
        cube_size: int,
        scramble_seed: int,
    ) -> None:
        """Test 5x5 L3 edges with many scrambles to find edge cases."""

        app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
        solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)

        app.scramble(scramble_seed, None, animation=False, verbose=False)
        solver.solve(what=SolveStep.LBL_L3_CENTER, debug=False, animation=False)

        # Skip if pre-conditions not met
        if not solver.is_solved_phase(SolveStep.LBL_L3_CENTER):
            pytest.skip(f"Pre-condition failed: L3 centers not solved (seed={scramble_seed})")

        # Solve L3 edges
        solver.solve(what=SolveStep.LBL_L3_CROSS, debug=False, animation=False)

        # Check L1 and middle slices preserved
        l1_ok = solver.is_solved_phase(SolveStep.LBL_L1)
        slices_ok = solver.is_solved_phase(SolveStep.LBL_SLICES_CTR)

        assert l1_ok and slices_ok, (
            f"BUG: L3 edge solving destroyed earlier phases! "
            f"(seed={scramble_seed}, L1={l1_ok}, slices={slices_ok})"
        )
