"""Tests for LayerByLayerNxNSolver - Layer-by-Layer method for big cubes.

Currently only Layer 1 is implemented, so tests focus on:
- Layer 1 centers (SolveStep.LBL_L1_Ctr)
- Layer 1 cross (SolveStep.L1x) - centers + edges paired + edges positioned
- Layer 1 complete (SolveStep.LBL_L1) - centers + edges + corners
"""
from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver
from cube.domain.solver.solver import SolveStep
from cube.domain.solver.SolverName import SolverName
from tests.solvers.conftest import skip_if_not_supported


# =============================================================================
# Status Tests
# =============================================================================


@pytest.mark.parametrize("size", [5, 7, 9])
def test_lbl_solver_state_inspection_on_solved_cube(size: int) -> None:
    """Test state inspection methods on a solved cube."""

    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    solver = LayerByLayerNxNSolver(app.op, app.op.sp.logger)

    app.scramble(0, None, animation=False, verbose=False)

    solver.solve(what=SolveStep.LBL_SLICES_CTR, debug=False, animation=False)

    # On solved cube, use FacesTrackerHolder for inspection
    assert solver.is_l2_slices_solved()


