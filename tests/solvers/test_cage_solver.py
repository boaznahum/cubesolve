"""Tests for CageNxNSolver - step by step cage method."""

import pytest
from cube.application.AbstractApp import AbstractApp
from cube.domain.model import Color
from cube.domain.solver.direct.cage.CageNxNSolver import CageNxNSolver, START_FACE_COLOR


@pytest.mark.parametrize("size", [5, 7])
def test_cage_solver_start_face(size: int) -> None:
    """Test solving start face centers on odd cubes."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)
    cube = app.cube

    # Scramble
    app.scramble(42, None, animation=False, verbose=False)

    solver = CageNxNSolver(app.op)

    # Status should show start face pending
    color_name = START_FACE_COLOR.name.capitalize()
    assert f"{color_name}:Pending" in solver.status

    # Start face should NOT be solved before
    start_face = cube.color_2_face(START_FACE_COLOR)
    assert not start_face.center.is3x3, f"{color_name} face should not be 3x3 before solving"

    # Solve
    solver.solve()

    # Start face SHOULD be solved after
    start_face = cube.color_2_face(START_FACE_COLOR)
    assert start_face.center.is3x3, f"{color_name} face should be 3x3 after solving"

    # Status should show start face done
    assert f"{color_name}:Done" in solver.status


@pytest.mark.parametrize("size", [4, 6])
def test_cage_solver_rejects_even_cubes(size: int) -> None:
    """Test that CageNxNSolver rejects even cubes."""
    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    solver = CageNxNSolver(app.op)

    # Scramble first
    app.scramble(42, None, animation=False, verbose=False)

    with pytest.raises(ValueError, match="only supports odd cubes"):
        solver.solve()
