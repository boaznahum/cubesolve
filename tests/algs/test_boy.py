import pytest

from cube.domain import algs
from cube.application.AbstractApp import AbstractApp
from cube.domain.model.Cube import Cube
from cube.domain.solver.SolverName import SolverName
from tests.test_utils import _test_sp

# All solvers (unsupported ones will be skipped via skip_if_not_supported)
def skip_if_not_supported(solver_name: SolverName, cube_size: int) -> None:
    """Skip test if solver doesn't support this cube size."""
    skip_reason = solver_name.meta.get_skip_reason(cube_size)
    if skip_reason:
        pytest.skip(skip_reason)


def test_scramble1_preserves_boy_large_cube() -> None:
    """Test that scramble1 preserves BOY orientation on larger cubes."""
    size = 7

    cube = Cube(size, sp=_test_sp)

    a: algs.Alg = algs.Algs.scramble1(cube.size)
    a.play(cube)

    assert cube.is_in_original_scheme


@pytest.mark.parametrize("solver", SolverName.implemented())
def test_solve_preserves_boy(solver: SolverName) -> None:
    """Test that solving preserves BOY orientation."""
    size = 4
    skip_if_not_supported(solver, size)

    app = AbstractApp.create_app(size, solver=solver)
    cube = app.cube

    a: algs.Alg = algs.Algs.scramble1(cube.size)
    a.play(cube)

    app.slv.solve()

    assert cube.is_in_original_scheme, f"Solver {solver.name} should preserve original color scheme"
