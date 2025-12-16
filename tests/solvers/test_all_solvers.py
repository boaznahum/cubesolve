"""
Comprehensive solver tests.

Tests all known solvers against various cube sizes and scrambles.
Each test verifies that a solver can successfully solve a scrambled cube.

Test Matrix:
- Solvers: LBL, CFOP, KOCIEMBA (all from SolverName enum)
- Cube sizes: 3, 4, 5, 8
- Scrambles: GUI seeds 0-9 (same as keyboard keys) + seeds 101, 202, 303 + random

Split into two test methods for incremental sanity checks:
- test_solver_quick: First 1/3 of scrambles (seeds 0-3)
- test_solver_full: Remaining 2/3 of scrambles (seeds 4-9, 101, 202, 303, random)
"""
from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.domain.solver import Solvers
from cube.domain.solver.SolverName import SolverName

from tests.solvers.conftest import (
    get_scramble_params_first_third,
    get_scramble_params_remaining,
    get_solver_names,
    get_cube_sizes,
    skip_if_not_supported,
)


def _run_solver_test(
    solver_name: SolverName,
    cube_size: int,
    scramble_name: str,
    scramble_seed: int | None,
    session_random_seed: int,
) -> None:
    """Shared test logic for solver tests."""
    # Check if solver supports this cube size (skip with reason if not)
    skip_if_not_supported(solver_name, cube_size)

    # Determine actual seed (use session random if not predefined)
    actual_seed: int = scramble_seed if scramble_seed is not None else session_random_seed

    # Create app (provides vs with config, operator, and cube)
    app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)

    # Create solver using app's operator (same as GUI)
    solver = Solvers.by_name(solver_name, app.op)

    # Scramble using app.scramble() - equivalent to GUI command:
    #   Commands.SCRAMBLE_0 through SCRAMBLE_9 (keys 0-9)
    #   ScrambleCommand(seed).execute(ctx) calls ctx.app.scramble(seed, None, ...)
    app.scramble(actual_seed, None, animation=False, verbose=False)

    # Verify cube is scrambled (not solved)
    assert not solver.is_solved, (
        f"Cube should be scrambled after applying scramble "
        f"(solver={solver_name.value}, size={cube_size}, scramble={scramble_name})"
    )

    # Solve the cube
    solver.solve(debug=False, animation=False)

    # Verify cube is solved
    assert solver.is_solved, (
        f"Solver {solver_name.value} failed to solve cube "
        f"(size={cube_size}, scramble={scramble_name}, seed={actual_seed})"
    )


class TestAllSolvers:
    """Test suite for all solvers with various scrambles."""

    @pytest.mark.parametrize("solver_name", get_solver_names(), ids=lambda s: s.value)
    @pytest.mark.parametrize("cube_size", get_cube_sizes(), ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_name,scramble_seed",
        get_scramble_params_first_third(),
        ids=lambda x: x if isinstance(x, str) else None,
    )
    def test_solver_quick(
        self,
        solver_name: SolverName,
        cube_size: int,
        scramble_name: str,
        scramble_seed: int | None,
        session_random_seed: int,
    ) -> None:
        """Quick sanity check with first 1/3 of scrambles."""
        _run_solver_test(solver_name, cube_size, scramble_name, scramble_seed, session_random_seed)

    @pytest.mark.parametrize("solver_name", get_solver_names(), ids=lambda s: s.value)
    @pytest.mark.parametrize("cube_size", get_cube_sizes(), ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_name,scramble_seed",
        get_scramble_params_remaining(),
        ids=lambda x: x if isinstance(x, str) else None,
    )
    def test_solver_full(
        self,
        solver_name: SolverName,
        cube_size: int,
        scramble_name: str,
        scramble_seed: int | None,
        session_random_seed: int,
    ) -> None:
        """Full test with remaining 2/3 of scrambles."""
        _run_solver_test(solver_name, cube_size, scramble_name, scramble_seed, session_random_seed)


class TestSolverBasics:
    """Basic sanity tests for solver infrastructure."""

    def test_all_solvers_are_tested(self) -> None:
        """Verify that our test covers all known solvers."""
        tested_solvers = set(get_solver_names())
        all_solvers = set(SolverName)

        assert tested_solvers == all_solvers, (
            f"Test configuration is missing solvers: {all_solvers - tested_solvers}"
        )

    @pytest.mark.parametrize("solver_name", get_solver_names(), ids=lambda s: s.value)
    def test_solver_reports_solved_for_fresh_cube(
        self,
        solver_name: SolverName,
    ) -> None:
        """Test that solvers correctly identify a fresh cube as solved."""
        # Check if solver is testable (skip with reason if not)
        skip_if_not_supported(solver_name, 3)

        # Use app's operator (same as GUI)
        app = AbstractApp.create_non_default(cube_size=3, animation=False)
        solver = Solvers.by_name(solver_name, app.op)

        assert solver.is_solved, (
            f"Solver {solver_name.value} should report fresh cube as solved"
        )
