"""Tests for LayerByLayerNxNSolver - full solve on even cubes."""
from __future__ import annotations

import pytest

from .conftest import get_scramble_params, CUBE_SIZES_EVEN
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
from cube.domain.solver.solver import SolveStep


class TestLBLBigCubeFullSolver:
    """Test LayerByLayerNxNSolver full solve with even cubes."""

    @pytest.mark.parametrize("cube_size", CUBE_SIZES_EVEN, ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_name,scramble_seed",
        get_scramble_params(),
        ids=lambda x: x if isinstance(x, str) else None,
    )
    def test_lbl_full_solve(
        self,
        cube_size: int,
        scramble_name: str,
        scramble_seed: int,
    ) -> None:
        """Test full solve (SolveStep.ALL) on even cubes."""
        app = AbstractApp.create_app(cube_size=cube_size)

        solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)

        app.scramble(scramble_seed, None, animation=False, verbose=False)

        solver.solve(what=SolveStep.ALL, debug=False, animation=False)

        assert app.cube.solved, (
            f"Cube not solved (size={cube_size}, scramble={scramble_name})"
        )
