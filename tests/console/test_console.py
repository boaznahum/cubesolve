"""
Console tests for main_c.py

These tests call the run() function directly with injected key sequences
and verify the cube state using the returned ConsoleResult.
"""

import pytest

from cube.model import Cube
from cube.operator import Operator
from cube.algs import Algs
from cube.solver import Solvers
from cube.main_console.main_c import run, ConsoleResult
from cube.main_console.keys import Keys


@pytest.mark.console
class TestConsoleBasic:
    """Basic console operation tests."""

    def test_face_rotations_fr(self):
        """Test F and R rotations."""
        key_sequence = Keys.F + Keys.R + Keys.QUIT
        result = run(key_sequence=key_sequence)

        assert isinstance(result, ConsoleResult)
        assert not result.cube.solved, "Cube should not be solved after F R"

    def test_single_rotation(self):
        """Test single R rotation."""
        key_sequence = Keys.R + Keys.QUIT
        result = run(key_sequence=key_sequence)

        assert not result.cube.solved, "Cube should not be solved after R"

    def test_all_face_rotations(self):
        """Test all basic face rotations."""
        key_sequence = Keys.all_face_rotations() + Keys.QUIT
        result = run(key_sequence=key_sequence)

        assert isinstance(result.cube, Cube)

    def test_rotation_and_inverse_restores(self):
        """Test that R followed by R' restores the cube."""
        key_sequence = Keys.R + Keys.INV + Keys.R + Keys.QUIT
        result = run(key_sequence=key_sequence)

        assert result.cube.solved, "Cube should be solved after R R'"


@pytest.mark.console
class TestConsoleSolve:
    """Console solve operation tests."""

    def test_scramble_and_solve(self):
        """Test scramble with seed 1 and solve."""
        key_sequence = Keys.SCRAMBLE_1 + Keys.SOLVE + Keys.QUIT
        result = run(key_sequence=key_sequence)

        assert result.cube.solved, "Cube should be solved after scramble and solve"
        assert result.solver.is_solved, "Solver should report solved"

    @pytest.mark.parametrize("seed", [1, 2, 3, 4, 5, 6])
    def test_scramble_solve_verify(self, seed: int):
        """Test scramble with different seeds, solve, and verify cube.solved."""
        key_sequence = Keys.scramble_seed(seed) + Keys.SOLVE + Keys.QUIT
        result = run(key_sequence=key_sequence)

        assert result.cube.solved, f"Cube should be solved after scramble seed {seed}"
        assert result.solver.is_solved, f"Solver should report solved for seed {seed}"

    def test_scramble_without_solve(self):
        """Test that scramble leaves cube unsolved."""
        key_sequence = Keys.SCRAMBLE_1 + Keys.QUIT
        result = run(key_sequence=key_sequence)

        assert not result.cube.solved, "Cube should NOT be solved after scramble only"


@pytest.mark.console
class TestConsoleOperations:
    """Test various console operations."""

    def test_clear_resets_cube(self):
        """Test that Clear resets the cube to solved state."""
        key_sequence = Keys.SCRAMBLE_1 + Keys.CLEAR + Keys.QUIT
        result = run(key_sequence=key_sequence)

        assert result.cube.solved, "Cube should be solved after Clear"

    def test_undo_operation(self):
        """Test undo restores previous state."""
        key_sequence = Keys.R + Keys.UNDO + Keys.QUIT
        result = run(key_sequence=key_sequence)

        assert result.cube.solved, "Cube should be solved after R then Undo"

    def test_multiple_undo(self):
        """Test multiple undo operations."""
        key_sequence = Keys.R + Keys.L + Keys.UNDO + Keys.UNDO + Keys.QUIT
        result = run(key_sequence=key_sequence)

        assert result.cube.solved, "Cube should be solved after R L Undo Undo"


@pytest.mark.console
class TestConsoleCubeSize:
    """Test different cube sizes."""

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_scramble_solve_different_sizes(self, cube_size: int):
        """Test scramble and solve on different cube sizes."""
        key_sequence = Keys.SCRAMBLE_1 + Keys.SOLVE + Keys.QUIT
        result = run(key_sequence=key_sequence, cube_size=cube_size)

        assert result.cube.solved, f"Cube {cube_size}x{cube_size} should be solved"
        assert result.solver.is_solved, f"Solver should report solved for {cube_size}x{cube_size}"


@pytest.mark.console
class TestCubeSolverDirect:
    """Direct cube solver tests - test with actual Cube objects (no main_c)."""

    @pytest.mark.parametrize("seed", [1, 2, 3, 4, 5, 6])
    def test_scramble_solve_cube_object(self, seed: int):
        """Scramble cube, solve it, and verify cube.solved is True."""
        cube = Cube(3)
        op = Operator(cube)
        solver = Solvers.default(op)

        assert cube.solved, "Cube should start in solved state"

        scramble_alg = Algs.scramble(3, seed)
        op.play(scramble_alg)

        assert not cube.solved, f"Cube should not be solved after scramble with seed {seed}"

        solver.solve()

        assert cube.solved, f"Cube should be solved after solver.solve() with seed {seed}"
        assert solver.is_solved, f"Solver.is_solved should be True after solving with seed {seed}"

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_scramble_solve_different_sizes_direct(self, cube_size: int):
        """Test scramble and solve on different cube sizes (direct, no main_c)."""
        cube = Cube(cube_size)
        op = Operator(cube)
        solver = Solvers.default(op)

        scramble_alg = Algs.scramble(cube_size, 1)
        op.play(scramble_alg)

        solver.solve()

        assert cube.solved, f"Cube {cube_size}x{cube_size} should be solved"
        assert solver.is_solved, f"Solver.is_solved should be True for {cube_size}x{cube_size} cube"

    def test_multiple_scramble_solve_cycles(self):
        """Test multiple scramble-solve cycles on same cube."""
        cube = Cube(3)
        op = Operator(cube)
        solver = Solvers.default(op)

        for seed in range(1, 10):
            scramble_alg = Algs.scramble(3, seed)
            op.play(scramble_alg)
            assert not cube.solved, f"Cube should not be solved after scramble seed {seed}"

            solver.solve()
            assert cube.solved, f"Cube should be solved after solving (cycle {seed})"

            op.reset()
            assert cube.solved, "Cube should be solved after reset"
