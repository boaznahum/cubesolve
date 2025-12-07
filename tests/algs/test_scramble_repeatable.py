"""Tests to verify that random scramble is repeatable with same seed."""
import pytest

from cube.application.AbstractApp import AbstractApp
from cube.application.state import ApplicationAndViewState
from cube.domain.model.Cube import Cube
from cube.application.commands.Operator import Operator
from cube.domain.solver import Solver, Solvers
from tests.conftest import _test_sp


def test_scramble_repeatable():
    """Test that scramble with same key produces identical results."""
    size = 6

    app = AbstractApp.create_non_default(cube_size=size, animation=False)

    cube = Cube(size=size, sp=_test_sp)

    vs = ApplicationAndViewState()
    op: Operator = Operator(cube, vs)
    solver: Solver = Solvers.default(op)

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

    assert s1 == s2, f"Solve counts should match: {s1} vs {s2}"
