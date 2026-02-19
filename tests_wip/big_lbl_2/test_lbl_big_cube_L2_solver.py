"""Tests for LayerByLayerNxNSolver - Layer-by-Layer method for big cubes.

Currently only Layer 1 is implemented, so tests focus on:
- Layer 1 centers (SolveStep.LBL_L1_Ctr)
- Layer 1 cross (SolveStep.L1x) - centers + edges paired + edges positioned
- Layer 1 complete (SolveStep.LBL_L1) - centers + edges + corners
"""
from __future__ import annotations

import pytest

from .conftest import get_scramble_params, CUBE_SIZES_EVEN
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
from cube.domain.solver.solver import SolveStep


class TestLBLBigCubeSolver:
    """Test LayerByLayerNxNSolver with various cube sizes and scrambles."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_EVEN, ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_name,scramble_seed",
        get_scramble_params(),
        ids=lambda x: x if isinstance(x, str) else None,
    )
    def test_lbl_l2_slices(
        self,
        cube_size: int,
        scramble_name: str,
        scramble_seed: int,
    ) -> None:
        """Test LBL_L1_Ctr step solves Layer 1 centers (even + odd cubes)."""
        app = AbstractApp.create_app(cube_size=cube_size)

        solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)

        app.scramble(scramble_seed, None, animation=False, verbose=False)

        solver.solve(what=SolveStep.LBL_L2_SLICES, debug=False, animation=False)

        assert solver.is_solved_phase(SolveStep.LBL_L2_SLICES), (
            f"L1 centers not solved (size={cube_size}, scramble={scramble_name})"
        )



