"""Aggressive/stress tests for cube solving."""
from __future__ import annotations

import pytest
from math import ceil

from cube.application import _config as config
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver.SolverName import SolverName
from tests.tetser import TestRunner


def _get_default_solver() -> SolverName:
    """Get the default solver from config."""
    return SolverName.lookup(config.DEFAULT_SOLVER)


def _size_id(size: int) -> str:
    """Generate test ID including solver name from config."""
    return f"{config.DEFAULT_SOLVER}-size_{size}"


@pytest.mark.slow
@pytest.mark.parametrize("cube_size", config.AGGRESSIVE_TEST_NUMBER_SIZES, ids=_size_id)
def test_aggressive_multiple_sizes(cube_size: int) -> None:
    """Test default solver across multiple cube sizes with multiple scrambles."""
    solver_name = _get_default_solver()

    # Check if solver supports this cube size
    skip_reason = solver_name.meta.get_skip_reason(cube_size)
    if skip_reason:
        pytest.skip(skip_reason)

    app = AbstractApp.create_non_default(cube_size, animation=False)
    iterations = config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS // len(config.AGGRESSIVE_TEST_NUMBER_SIZES)
    app.run_tests(
        config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_START,
        iterations,
        debug=False
    )


@pytest.mark.slow
@pytest.mark.parametrize("solver_name", list(SolverName), ids=lambda s: s.display_name)
@pytest.mark.parametrize("cube_size", config.AGGRESSIVE_2_TEST_NUMBER_SIZES, ids=lambda s: f"size_{s}")
def test_aggressive_all_solvers(solver_name: SolverName, cube_size: int) -> None:
    """Test all solvers across multiple sizes."""
    # Check if solver supports this cube size
    skip_reason = solver_name.meta.get_skip_reason(cube_size)
    if skip_reason:
        pytest.skip(skip_reason)

    first_scramble_key = config.AGGRESSIVE_2_TEST_NUMBER_OF_SCRAMBLE_START
    number_of_loops = ceil(config.AGGRESSIVE_2_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS / len(SolverName))

    TestRunner.run_solvers_sizes([solver_name], [cube_size], first_scramble_key, number_of_loops, debug=False)
