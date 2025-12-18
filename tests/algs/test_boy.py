import pytest

from cube.domain import algs
from cube.application.AbstractApp import AbstractApp
from cube.domain.model.Cube import Cube
from cube.domain.solver.SolverName import SolverName
from cube.application import _config as cfg
from tests.conftest import _test_sp


def test_scramble1_preserves_boy_large_cube() -> None:
    """Test that scramble1 preserves BOY orientation on larger cubes."""
    size = 7

    cube = Cube(size, sp=_test_sp)

    a: algs.Alg = algs.Algs.scramble1(cube.size)
    a.play(cube)

    assert cube.is_boy


def test_solve_preserves_boy() -> None:
    """Test that solving preserves BOY orientation."""
    size = 4

    # Check if default solver supports the cube size
    solver_name = SolverName.lookup(cfg.DEFAULT_SOLVER)
    skip_reason = solver_name.meta.get_skip_reason(size)
    if skip_reason:
        pytest.skip(f"Default solver {solver_name} doesn't support {size}x{size}: {skip_reason}")

    app = AbstractApp.create_non_default(size, animation=False)
    cube = app.cube

    a: algs.Alg = algs.Algs.scramble1(cube.size)
    a.play(cube)

    app.slv.solve()

    assert cube.is_boy
