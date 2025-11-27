"""
Cube integration tests with GUI backends.

These tests verify that the cube model works correctly with GUI backends,
including rendering, operations, and solving. Uses CubeTestDriver for
clean abstraction of key sequences and cube operations.

The CubeTestDriver handles:
- Key-to-algorithm mapping (R -> Algs.R, R' -> Algs.Ri, etc.)
- Sequence injection into backend
- Cube state management
- Solver integration
"""

import pytest

from cube.algs import Algs
from cube.gui.types import Keys

# Import CubeTestDriver from conftest (available via fixture)
from tests.backends.conftest import CubeTestDriver


class TestCubeRotations:
    """Test basic cube rotations via key sequences."""

    def test_single_rotation(self, cube_driver: CubeTestDriver, backend_name: str):
        """Single rotation should change cube state."""
        assert cube_driver.solved

        cube_driver.execute("R")

        assert not cube_driver.solved
        assert cube_driver.history == ["R"]

    def test_multiple_rotations(self, cube_driver: CubeTestDriver, backend_name: str):
        """Multiple rotations via sequence."""
        cube_driver.execute("RLU")

        assert not cube_driver.solved
        assert cube_driver.history == ["R", "L", "U"]

    def test_all_face_rotations(self, cube_driver: CubeTestDriver, backend_name: str):
        """All six face rotations."""
        cube_driver.execute("RLUDFB")

        assert not cube_driver.solved
        assert len(cube_driver.history) == 6

    def test_inverse_rotations(self, cube_driver: CubeTestDriver, backend_name: str):
        """Inverse rotations using prime notation."""
        cube_driver.execute("R")
        assert not cube_driver.solved

        cube_driver.execute("R'")  # R inverse should undo R
        assert cube_driver.solved

    def test_rotation_sequence_undo(self, cube_driver: CubeTestDriver, backend_name: str):
        """Rotation followed by its inverse returns to solved."""
        sequences = ["RR'", "LL'", "UU'", "DD'", "FF'", "BB'"]

        for seq in sequences:
            cube_driver.reset().execute(seq)
            assert cube_driver.solved, f"Sequence {seq} should return to solved"


class TestCubeSolving:
    """Test cube solving with various configurations."""

    @pytest.mark.parametrize("seed", [1, 2, 3, 42, 123])
    def test_scramble_and_solve(self, cube_driver: CubeTestDriver, backend_name: str, seed: int):
        """Scramble cube, then solve it."""
        cube_driver.scramble(seed=seed)
        assert not cube_driver.solved

        cube_driver.solve()
        assert cube_driver.solved

    def test_solve_after_key_sequence(self, cube_driver: CubeTestDriver, backend_name: str):
        """Solve after applying key sequence."""
        cube_driver.execute("RLUDFB")
        assert not cube_driver.solved

        cube_driver.solve()
        assert cube_driver.solved

    def test_multiple_scramble_solve_cycles(self, cube_driver: CubeTestDriver, backend_name: str):
        """Multiple scramble-solve cycles."""
        for seed in range(1, 6):
            cube_driver.scramble(seed=seed)
            assert not cube_driver.solved

            cube_driver.solve()
            assert cube_driver.solved

            cube_driver.reset()


class TestCubeSizes:
    """Test different cube sizes."""

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_different_cube_sizes(
        self,
        cube_driver_factory,
        backend_name: str,
        cube_size: int,
    ):
        """Test scramble and solve on different cube sizes."""
        driver = cube_driver_factory(cube_size)

        driver.scramble(seed=42)
        assert not driver.solved

        driver.solve()
        assert driver.solved, f"{cube_size}x{cube_size} cube should be solved"


class TestUndoRedo:
    """Test undo functionality."""

    def test_undo_single_move(self, cube_driver: CubeTestDriver, backend_name: str):
        """Undo a single move."""
        cube_driver.execute("R")
        assert not cube_driver.solved

        cube_driver.undo()
        assert cube_driver.solved

    def test_undo_multiple_moves(self, cube_driver: CubeTestDriver, backend_name: str):
        """Undo multiple moves."""
        cube_driver.execute("RLU")

        cube_driver.undo(3)
        assert cube_driver.solved

    def test_undo_sequence(self, cube_driver: CubeTestDriver, backend_name: str):
        """Undo after sequence of moves."""
        cube_driver.execute("RLUDFB")
        initial_history_len = len(cube_driver.operator.history())

        cube_driver.undo(initial_history_len)
        assert cube_driver.solved


class TestDirectAlgorithms:
    """Test executing algorithms directly."""

    def test_execute_algorithm(self, cube_driver: CubeTestDriver, backend_name: str):
        """Execute algorithm directly (not via keys)."""
        cube_driver.execute_alg(Algs.R)
        assert not cube_driver.solved

    def test_sexy_move(self, cube_driver: CubeTestDriver, backend_name: str):
        """Execute sexy move (R U R' U') six times returns to solved."""
        sexy_move = Algs.alg("R U R' U'")

        for _ in range(6):
            cube_driver.execute_alg(sexy_move)

        assert cube_driver.solved

    def test_pll_algorithm(self, cube_driver: CubeTestDriver, backend_name: str):
        """Apply PLL algorithm and verify it changes state."""
        # T-perm: R U R' U' R' F R2 U' R' U' R U R' F'
        cube_driver.execute_alg(Algs.alg("R U R' U' R' F R2 U' R' U' R U R' F'"))

        # Apply same algorithm 2 more times to return to solved (T-perm has order 2)
        cube_driver.execute_alg(Algs.alg("R U R' U' R' F R2 U' R' U' R U R' F'"))
        assert cube_driver.solved


class TestRenderingWithCube:
    """Test rendering during cube operations."""

    def test_render_after_rotation(self, cube_driver: CubeTestDriver, backend_name: str):
        """Render frame after rotation."""
        cube_driver.execute("R")
        cube_driver.render_frame()

        assert not cube_driver.solved

    def test_render_during_solve(self, cube_driver: CubeTestDriver, backend_name: str):
        """Render frames during solve sequence."""
        cube_driver.scramble(seed=42)

        # Render before solve
        cube_driver.render_frame()
        assert not cube_driver.solved

        # Solve
        cube_driver.solve()

        # Render after solve
        cube_driver.render_frame()
        assert cube_driver.solved

    def test_multiple_render_frames(self, cube_driver: CubeTestDriver, backend_name: str):
        """Multiple render frames during operations."""
        for move in "RLUDFB":
            cube_driver.execute(move)
            cube_driver.render_frame()

        assert not cube_driver.solved


class TestKeyMapping:
    """Test custom key mappings."""

    def test_custom_key_handler(self, cube_driver: CubeTestDriver, backend_name: str):
        """Register custom key handler."""
        custom_called = []

        def custom_handler(event):
            custom_called.append(event.symbol)

        cube_driver.register_key(Keys.Q, custom_handler)
        cube_driver.execute_keys(Keys.Q)

        assert Keys.Q in custom_called

    def test_override_key_mapping(self, cube_driver: CubeTestDriver, backend_name: str):
        """Override default key mapping."""
        # Make R key do L move instead
        cube_driver.set_key_mapping(Keys.R, Algs.L)

        cube_driver.execute("R")  # Should actually do L

        # Undo with actual L' to verify L was executed
        cube_driver.execute_alg(Algs.L.prime)
        assert cube_driver.solved


class TestChaining:
    """Test method chaining."""

    def test_method_chaining(self, cube_driver: CubeTestDriver, backend_name: str):
        """Test fluent interface with method chaining."""
        result = (
            cube_driver
            .scramble(seed=42)
            .render_frame()
            .solve()
            .render_frame()
        )

        assert result is cube_driver
        assert cube_driver.solved

    def test_execute_chain(self, cube_driver: CubeTestDriver, backend_name: str):
        """Chain multiple execute calls."""
        cube_driver.execute("R").execute("L").execute("U")

        assert not cube_driver.solved
        assert len(cube_driver.history) == 3

    def test_reset_clears_history(self, cube_driver: CubeTestDriver, backend_name: str):
        """Reset clears execution history."""
        cube_driver.execute("RLU")
        assert len(cube_driver.history) == 3

        cube_driver.reset()
        assert cube_driver.history == []
        assert cube_driver.solved


class TestBatchOperations:
    """Test batch operations (headless advantage)."""

    def test_batch_scramble_solve(self, cube_driver_factory, backend_name: str):
        """Batch test multiple scramble-solve operations."""
        results = []

        for seed in range(1, 11):
            driver = cube_driver_factory(3)
            driver.scramble(seed=seed)
            driver.solve()
            results.append({
                'seed': seed,
                'solved': driver.solved,
                'move_count': len(driver.operator.history()),
            })

        # All should be solved
        assert all(r['solved'] for r in results)

        # Verify we got varying move counts (not all same)
        move_counts = [r['move_count'] for r in results]
        assert len(set(move_counts)) > 1  # At least 2 different counts

    @pytest.mark.parametrize("cube_size,seed", [
        (3, 1), (3, 2), (3, 3),
        (4, 1), (4, 2),
        (5, 1),
    ])
    def test_parameterized_cube_solve(
        self,
        cube_driver_factory,
        backend_name: str,
        cube_size: int,
        seed: int,
    ):
        """Parameterized test for various cube sizes and seeds."""
        driver = cube_driver_factory(cube_size)
        driver.scramble(seed=seed).solve()

        assert driver.solved, f"{cube_size}x{cube_size} cube with seed {seed} should be solved"
