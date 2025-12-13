"""
Comprehensive solver tests.

Tests all known solvers against various cube sizes and scrambles.
Each test verifies that a solver can successfully solve a scrambled cube.

Test Matrix:
- Solvers: LBL, CFOP, KOCIEMBA (all from SolverName enum)
- Cube sizes: 3 (extensible to 4, 5, etc.)
- Scrambles: Predefined seeds (101, 202, 303) + one random per session
"""
from __future__ import annotations

import pytest

from cube.application.AbstractApp import AbstractApp
from cube.application.commands.Operator import Operator
from cube.domain.algs.Algs import Algs
from cube.domain.model.Cube import Cube
from cube.domain.solver import Solvers
from cube.domain.solver.SolverName import SolverName

from tests.conftest import _test_sp
from tests.solvers.conftest import (
    get_scramble_params,
    get_solver_names,
    get_cube_sizes,
)


class TestAllSolvers:
    """Test suite for all solvers with various scrambles."""

    @pytest.mark.parametrize("solver_name", get_solver_names(), ids=lambda s: s.value)
    @pytest.mark.parametrize("cube_size", get_cube_sizes(), ids=lambda s: f"size_{s}")
    @pytest.mark.parametrize(
        "scramble_name,scramble_seed",
        get_scramble_params(),
        ids=lambda x: x if isinstance(x, str) else None,
    )
    def test_solver_solves_scrambled_cube(
        self,
        solver_name: SolverName,
        cube_size: int,
        scramble_name: str,
        scramble_seed: int | None,
        session_random_seed: int,
        test_sp,
    ) -> None:
        """Test that a solver can solve a scrambled cube.

        Args:
            solver_name: The solver to test (LBL, CFOP, KOCIEMBA)
            cube_size: Size of the cube (3 for 3x3, etc.)
            scramble_name: Human-readable scramble identifier
            scramble_seed: Seed for scramble (None means use session random)
            session_random_seed: Unique random seed for this test session
            test_sp: Test service provider fixture
        """
        # Determine actual seed (use session random if not predefined)
        actual_seed: int = scramble_seed if scramble_seed is not None else session_random_seed

        # Create app (provides vs with config) and cube
        app = AbstractApp.create_non_default(cube_size=cube_size, animation=False)
        cube = Cube(size=cube_size, sp=test_sp)

        # Create operator using app's vs (which has config)
        op = Operator(cube, app.vs)

        # Create solver
        solver = Solvers.by_name(solver_name, op)

        # Generate and apply scramble
        scramble = Algs.scramble(cube_size, seed=actual_seed)
        scramble.play(cube)

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


class TestSolverBasics:
    """Basic sanity tests for solver infrastructure."""

    def test_all_solvers_are_tested(self) -> None:
        """Verify that our test covers all known solvers (except WIP ones).

        Note: Some solvers are excluded from testing because they are WIP.
        Currently excluded: CAGE (non-reduction solver, under development)
        """
        tested_solvers = set(get_solver_names())
        all_solvers = set(SolverName)
        wip_solvers = {SolverName.CAGE}  # Solvers under development

        expected = all_solvers - wip_solvers
        assert tested_solvers == expected, (
            f"Test configuration is missing solvers: {expected - tested_solvers}"
        )

    @pytest.mark.parametrize("solver_name", get_solver_names(), ids=lambda s: s.value)
    def test_solver_reports_solved_for_fresh_cube(
        self,
        solver_name: SolverName,
        test_sp,
    ) -> None:
        """Test that solvers correctly identify a fresh cube as solved."""
        app = AbstractApp.create_non_default(cube_size=3, animation=False)
        cube = Cube(size=3, sp=test_sp)
        op = Operator(cube, app.vs)
        solver = Solvers.by_name(solver_name, op)

        assert solver.is_solved, (
            f"Solver {solver_name.value} should report fresh cube as solved"
        )
