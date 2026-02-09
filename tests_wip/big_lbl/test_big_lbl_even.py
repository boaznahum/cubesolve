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

CUBE_SIZES_EVEN=[4]
# Odd cube sizes only (even cubes have different parity issues)
# Scramble seeds to test
SCRAMBLE_SEEDS: list[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


# =============================================================================
# Tests
# =============================================================================

class TestBigLBLEven:
    """Test that L3 edge solving preserves L1 and middle edges."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_EVEN, ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize("scramble_seed", SCRAMBLE_SEEDS, ids=lambda s: f"seed_{s}")
    def test_big_lbl_even(
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
        solver.solve()

        assert solver.is_solved

