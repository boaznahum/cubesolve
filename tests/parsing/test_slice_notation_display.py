"""Test slice notation parsing and display."""

import pytest
from cube.domain.algs import Algs


class TestSliceNotationDisplay:
    """Test Alg → String (display)."""

    def test_face_alg_hides_single_slice(self):
        """R[1] should display as 'R' since R = R[1]."""
        assert str(Algs.R[1]) == "R"
        assert str(Algs.R) == "R"

    def test_slice_alg_shows_single_slice(self):
        """M[1] must NOT display as 'M' since M ≠ M[1]."""
        assert str(Algs.MM[1]) != str(Algs.MM)
        assert "1" in str(Algs.MM[1])

    def test_all_slice_algs_show_single_slice(self):
        """E[1] and S[1] should also show the slice index."""
        assert str(Algs.EE[1]) != str(Algs.EE)
        assert str(Algs.SS[1]) != str(Algs.SS)


class TestSliceNotationParsing:
    """Test String → Alg (parsing) round-trip."""

    def test_parse_face_slice_round_trip(self):
        """parse(str(R[1])) should work."""
        r1 = Algs.R[1]
        parsed = Algs.parse(str(r1))
        assert str(parsed) == str(r1)

    def test_parse_slice_alg_round_trip(self):
        """parse(str(MM[1])) should give back MM[1], not MM."""
        m1 = Algs.MM[1]
        m1_str = str(m1)
        parsed = Algs.parse(m1_str)
        assert str(parsed) == m1_str
        assert str(parsed) != str(Algs.MM)
