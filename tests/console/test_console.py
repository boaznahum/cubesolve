"""
Console tests for main_c.py

These tests run the console application with injected keyboard sequences,
and also test the cube solver directly with actual Cube objects.
"""

import pytest
from tests.console.tester import ConsoleTestRunner

from cube.model import Cube
from cube.operator import Operator
from cube.algs import Algs
from cube.solver import Solver, Solvers
from cube.main_console.keys import Keys


@pytest.mark.console
class TestConsoleBasic:
    """Basic console operation tests."""

    def test_face_rotations_frq(self):
        """Test F and R rotations then quit."""
        key_sequence = Keys.F + Keys.R + Keys.QUIT
        result = ConsoleTestRunner.run_test(
            key_sequence=key_sequence,
            timeout_sec=30.0,
            debug=True
        )
        assert result.success, f"Console test failed: {result.message}. Error: {result.error}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    def test_single_rotation(self):
        """Test single R rotation then quit."""
        key_sequence = Keys.R + Keys.QUIT
        result = ConsoleTestRunner.run_test(
            key_sequence=key_sequence,
            timeout_sec=30.0,
            debug=True
        )
        assert result.success, f"Console test failed: {result.message}"

    def test_all_face_rotations(self):
        """Test all basic face rotations."""
        key_sequence = Keys.all_face_rotations() + Keys.QUIT
        result = ConsoleTestRunner.run_test(
            key_sequence=key_sequence,
            timeout_sec=30.0,
            debug=True
        )
        assert result.success, f"Console test failed: {result.message}"


@pytest.mark.console
class TestConsoleSolve:
    """Console solve operation tests."""

    def test_scramble_and_solve(self):
        """Test scramble with seed 1 and solve."""
        key_sequence = Keys.SCRAMBLE_1 + Keys.SOLVE + Keys.QUIT
        result = ConsoleTestRunner.run_test(
            key_sequence=key_sequence,
            timeout_sec=60.0,
            debug=True
        )
        assert result.success, f"Console test failed: {result.message}"
        # Check that the output contains "Solved" status
        assert "Solved" in result.stdout, f"Cube not solved. Output: {result.stdout}"

    @pytest.mark.parametrize("seed", [1, 2, 3, 4, 5, 6])
    def test_scramble_solve_verify(self, seed: int):
        """Test scramble with different seeds, solve, and verify solved status."""
        key_sequence = Keys.scramble_seed(seed) + Keys.SOLVE + Keys.QUIT
        result = ConsoleTestRunner.run_test(
            key_sequence=key_sequence,
            timeout_sec=60.0,
            debug=True
        )
        assert result.success, f"Console test failed for seed {seed}: {result.message}"

        # Verify the cube ends in Solved state
        # The last "Status=" line should be "Solved"
        lines = result.stdout.strip().split('\n')
        status_lines = [line for line in lines if line.startswith("Status=")]
        assert len(status_lines) > 0, f"No status lines found in output for seed {seed}"

        last_status = status_lines[-1]
        assert "Solved" in last_status, f"Cube not solved after scramble seed {seed}. Last status: {last_status}"


@pytest.mark.console
class TestCubeSolverDirect:
    """Direct cube solver tests - test with actual Cube objects."""

    @pytest.mark.parametrize("seed", [1, 2, 3, 4, 5, 6])
    def test_scramble_solve_cube_object(self, seed: int):
        """Scramble cube, solve it, and verify cube.solved is True."""
        # Create cube and operator
        cube = Cube(3)
        op = Operator(cube)
        solver = Solvers.default(op)

        # Verify cube starts solved
        assert cube.solved, "Cube should start in solved state"

        # Scramble with seed
        scramble_alg = Algs.scramble(3, seed)
        op.play(scramble_alg)

        # Cube should NOT be solved after scramble
        assert not cube.solved, f"Cube should not be solved after scramble with seed {seed}"

        # Solve the cube
        solver.solve()

        # Verify cube is solved
        assert cube.solved, f"Cube should be solved after solver.solve() with seed {seed}"
        assert solver.is_solved, f"Solver.is_solved should be True after solving with seed {seed}"

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_scramble_solve_different_sizes(self, cube_size: int):
        """Test scramble and solve on different cube sizes (2x2 not supported)."""
        cube = Cube(cube_size)
        op = Operator(cube)
        solver = Solvers.default(op)

        # Scramble with seed 1
        scramble_alg = Algs.scramble(cube_size, 1)
        op.play(scramble_alg)

        # Solve
        solver.solve()

        # Verify solved
        assert cube.solved, f"Cube {cube_size}x{cube_size} should be solved"
        assert solver.is_solved, f"Solver.is_solved should be True for {cube_size}x{cube_size} cube"

    def test_multiple_scramble_solve_cycles(self):
        """Test multiple scramble-solve cycles on same cube."""
        cube = Cube(3)
        op = Operator(cube)
        solver = Solvers.default(op)

        for seed in range(1, 10):
            # Scramble
            scramble_alg = Algs.scramble(3, seed)
            op.play(scramble_alg)
            assert not cube.solved, f"Cube should not be solved after scramble seed {seed}"

            # Solve
            solver.solve()
            assert cube.solved, f"Cube should be solved after solving (cycle {seed})"

            # Reset for next cycle
            op.reset()
            assert cube.solved, "Cube should be solved after reset"
