"""Tests to verify that random scramble is repeatable with same seed."""
import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.model.Cube import Cube
from cube.application.commands.Operator import Operator
from cube.domain.solver import Solver, Solvers
from cube.domain.solver.SolverName import SolverName
from tests.test_utils import _test_sp

# All solvers (unsupported ones will be skipped via skip_if_not_supported)
ALL_SOLVERS = SolverName.implemented()


def skip_if_not_supported(solver_name: SolverName, cube_size: int) -> None:
    """Skip test if solver doesn't support this cube size."""
    skip_reason = solver_name.meta.get_skip_reason(cube_size)
    if skip_reason:
        pytest.skip(skip_reason)


@pytest.mark.parametrize("solver_name", ALL_SOLVERS)
def test_scramble_repeatable(solver_name: SolverName):
    """Test that scramble with same key produces identical results."""
    size = 6
    skip_if_not_supported(solver_name, size)

    app = AbstractApp.create_non_default(cube_size=size, animation=False, solver=solver_name)

    cube = Cube(size=size, sp=_test_sp)

    # Use vs from app (which has config)
    vs = app.vs
    op: Operator = Operator(cube, vs)
    solver: Solver = Solvers.by_name(solver_name, op)

    scramble_key = 203
    alg1 = app.scramble(scramble_key, None, False, True)
    alg2 = app.scramble(scramble_key, None, False, True)

    # Verify both algs produce same cube state
    alg1.play(cube)
    st1 = cube.cqr.get_sate()
    cube.reset()
    alg2.play(cube)

    assert cube.cqr.compare_state(st1), "Cube should be in same state after alg1/alg2"

    # Verify solve counts are identical
    op.reset()
    alg1.play(cube)
    solver.solve(debug=False)
    s1 = op.count

    op.reset()
    alg2.play(cube)
    solver.solve(debug=False)
    s2 = op.count

    assert s1 == s2, f"Solve counts should match for {solver_name.name}: {s1} vs {s2}"
