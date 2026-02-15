"""Tests for algorithm parsing (multiline format)."""
import pytest

from cube.domain.algs import Algs
from cube.domain.model.Cube import Cube
from tests.test_utils import _test_sp


# NOTE: Tests for file-based algorithms (f1.txt - f5.txt) were removed
# because those files are user-editable and not suitable for testing.
# User algorithms can contain invalid syntax or slice indices at any time.


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
