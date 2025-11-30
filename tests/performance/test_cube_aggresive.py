"""Aggressive/stress tests for cube solving."""
import pytest
from math import ceil

from cube import config
from cube.algs import Algs
from cube.app.AbstractApp import AbstractApp
from cube.solver.SolverName import SolverName
from tests.tetser import TestRunner


@pytest.mark.slow
def test_aggressive_multiple_sizes():
    """Test solving across multiple cube sizes with multiple scrambles."""
    app = AbstractApp.create_non_default(config.CUBE_SIZE, animation=False)
    debug = False
    sizes = config.AGGRESSIVE_TEST_NUMBER_SIZES

    for size in sizes:
        app.reset(cube_size=size)
        app.run_tests(
            config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_START,
            config.AGGRESSIVE_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS // len(sizes),
            debug=debug
        )


@pytest.mark.slow
def test_aggressive_all_solvers():
    """Test all solvers across multiple sizes."""
    sizes = config.AGGRESSIVE_2_TEST_NUMBER_SIZES
    debug = False
    first_scramble_key = config.AGGRESSIVE_2_TEST_NUMBER_OF_SCRAMBLE_START
    number_of_loops = ceil(config.AGGRESSIVE_2_TEST_NUMBER_OF_SCRAMBLE_ITERATIONS / len(SolverName))
    solvers: list[SolverName] = [*SolverName]

    TestRunner.run_solvers_sizes(solvers, sizes, first_scramble_key, number_of_loops, debug)
