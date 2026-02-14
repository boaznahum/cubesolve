"""
Simple test to reproduce bug with GUI seed 1, size 12.
"""
import pytest
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.Solvers import Solvers


def test_seed1_size12_simple():
    """
    Simple test: scramble with seed 1, solve, assert solved.

    If the bug occurs, solver will throw AssertionError about row corruption.
    If bug is fixed, solver completes and cube is solved.
    """
    # Setup
    app = AbstractApp.create_non_default(cube_size=12, animation=False)
    app.scramble(1, None, animation=False, verbose=False)

    # Solve
    solver = Solvers.beginner(app.op)
    solver.solve()

    # Assert solved
    assert app.cube.solved, "Cube should be solved"
