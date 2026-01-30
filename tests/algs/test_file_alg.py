"""Tests for file-based algorithms (f1.txt - f5.txt)."""
import pytest

from cube.domain.algs import Algs
from cube.domain.model.Cube import Cube
from cube.resources.algs import load_file_alg
from tests.test_utils import _test_sp


class TestFileAlg:
    """Tests for loading and executing file algorithms."""

    @pytest.mark.parametrize("slot", [1, 2, 3, 4, 5])
    def test_load_file_alg(self, slot: int) -> None:
        """Test that file algorithms can be loaded."""
        try:
            alg = load_file_alg(slot)
            assert alg is not None
        except FileNotFoundError:
            pytest.skip(f"f{slot}.txt not found")
        except ValueError as e:
            pytest.skip(f"f{slot}.txt is empty: {e}")

    @pytest.mark.parametrize("slot", [1, 2, 3, 4, 5])
    def test_file_alg_prime_returns_to_original(self, slot: int) -> None:
        """Test that alg + alg.prime returns cube to original state.

        This is the key invariant: any algorithm's inverse should undo it.
        Bug reproduction: F5 then Shift+F5 should return to original state.

        Note: Some algorithms use slice notation (e.g., [3]M) which requires
        larger cubes. We use 5x5 to support these.
        """
        try:
            alg = load_file_alg(slot)
        except (FileNotFoundError, ValueError):
            pytest.skip(f"f{slot}.txt not found or empty")

        # Use 5x5 cube to support slice notation like [3]M
        cube = Cube(5, sp=_test_sp)

        # Scramble first to ensure we're not just at solved state
        scramble = Algs.scramble(5, seed="test_file_alg")
        scramble.play(cube)

        # Save state before algorithm
        state_before = cube.cqr.get_sate()

        # Play algorithm
        alg.play(cube)

        # Play inverse (prime)
        alg.prime.play(cube)

        # Should be back to original state
        assert cube.cqr.compare_state(state_before), (
            f"f{slot}.txt: alg + alg.prime did not return to original state!\n"
            f"Algorithm: {alg}"
        )

    @pytest.mark.parametrize("slot", [1, 2, 3, 4, 5])
    def test_file_alg_prime_returns_to_original_big_cube(self, slot: int) -> None:
        """Test alg + alg.prime on a bigger cube (5x5)."""
        try:
            alg = load_file_alg(slot)
        except (FileNotFoundError, ValueError):
            pytest.skip(f"f{slot}.txt not found or empty")

        cube = Cube(5, sp=_test_sp)

        scramble = Algs.scramble(5, seed="test_file_alg_big")
        scramble.play(cube)

        state_before = cube.cqr.get_sate()

        alg.play(cube)
        alg.prime.play(cube)

        assert cube.cqr.compare_state(state_before), (
            f"f{slot}.txt: alg + alg.prime did not return to original state on 5x5!\n"
            f"Algorithm: {alg}"
        )


class TestParseMultiline:
    """Tests for Algs.parse_multiline."""

    def test_parse_multiline_simple(self) -> None:
        """Test parsing a simple multi-line algorithm."""
        alg = Algs.parse_multiline("""
            R U R'
        """)
        assert alg is not None

    def test_parse_multiline_with_comments(self) -> None:
        """Test parsing with comments and empty lines."""
        alg = Algs.parse_multiline("""
            # This is a comment
            R U R'

            # Another comment
            U' L' U L
        """)
        assert alg is not None

    def test_parse_multiline_prime_returns_to_original(self) -> None:
        """Test that parsed multi-line alg + prime returns to original."""
        alg = Algs.parse_multiline("""
            # Setup
            R U R'

            # Main
            U' L' U L
        """)

        cube = Cube(3, sp=_test_sp)
        scramble = Algs.scramble(3, seed="multiline_test")
        scramble.play(cube)

        state_before = cube.cqr.get_sate()

        alg.play(cube)
        alg.prime.play(cube)

        assert cube.cqr.compare_state(state_before)

    def test_parse_multiline_empty_raises(self) -> None:
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError):
            Algs.parse_multiline("")

        with pytest.raises(ValueError):
            Algs.parse_multiline("# only comments")
