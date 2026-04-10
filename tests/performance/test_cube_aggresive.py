"""Aggressive/stress tests for cube solving."""
from __future__ import annotations

from math import ceil

import pytest

from cube.application.config_impl import AppConfig
from cube.domain.solver.SolverName import SolverName
from tests import test_utils
from tests.tetser import TestRunner


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate parametrized test cases from ConfigProtocol at collection time."""
    if "cube_size" in metafunc.fixturenames:
        cfg = test_utils._test_sp.config
        metafunc.parametrize("cube_size", cfg.aggressive_2_test_number_sizes,
                             ids=lambda s: f"size_{s}")
    if "solver_name" in metafunc.fixturenames:
        metafunc.parametrize("solver_name", list(SolverName),
                             ids=lambda s: s.display_name)


@pytest.mark.slow
def test_aggressive_all_solvers(solver_name: SolverName, cube_size: int) -> None:
    """Test all solvers across multiple sizes."""
    # Check if solver supports this cube size
    skip_reason = solver_name.meta.get_skip_reason(cube_size)
    if skip_reason:
        pytest.skip(skip_reason)

    cfg = test_utils._test_sp.config
    first_scramble_key = cfg.aggressive_2_test_number_of_scramble_start
    number_of_loops = ceil(cfg.aggressive_2_test_number_of_scramble_iterations / len(SolverName))

    TestRunner.run_solvers_sizes([solver_name], [cube_size], first_scramble_key, number_of_loops, debug=False)
