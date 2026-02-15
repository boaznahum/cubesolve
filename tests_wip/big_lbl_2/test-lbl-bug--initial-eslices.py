"""Tests for LayerByLayerNxNSolver - full solve on even cubes."""
from __future__ import annotations

import pytest

from cube.domain.algs import Algs
from .conftest import get_scramble_params, CUBE_SIZES_EVEN
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
from cube.domain.solver.solver import SolveStep


class TestLBLBigCubeFullSolver:
    """Test LayerByLayerNxNSolver full solve with even cubes."""

    @pytest.mark.parametrize("cube_size", [12], ids=lambda s: f"size_{s}")
    def test_lbl_full_solve(
        self,
        cube_size: int
    ) -> None:
        """Test full solve (SolveStep.ALL) on even cubes."""
        app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

        solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)


        alg = Algs.E[1:4] + Algs.E[7:8]

        app.op.play(alg)

        solver.solve(what=SolveStep.ALL, debug=True, animation=False)

        assert app.cube.solved, (
            f"Cube not solved (size={cube_size})"
        )
