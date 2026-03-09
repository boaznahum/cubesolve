"""Test slice notation parsing and display."""

import pytest
from cube.application.AbstractApp import AbstractApp
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


# =============================================================================
# Discontinued (non-contiguous) slice tests
# =============================================================================

class TestDiscontinuedSliceDisplay:
    """Test that non-contiguous slices compress consecutive runs into ranges."""

    def test_sequence_compressed_to_ranges(self):
        """[1,2,4,5,6] should display as [1:2,4:6]M."""
        alg = Algs.MM[[1, 2, 4, 5, 6]]
        s = str(alg)
        assert "[1:2,4:6]" in s

    def test_non_consecutive_stays_individual(self):
        """[1,3,5] should display as [1,3,5]M."""
        alg = Algs.MM[[1, 3, 5]]
        s = str(alg)
        assert "[1,3,5]" in s

    def test_full_consecutive_becomes_range(self):
        """[1,2,3] should display as [1:3]M."""
        alg = Algs.MM[[1, 2, 3]]
        s = str(alg)
        assert "[1:3]" in s

    def test_mixed_singles_and_ranges(self):
        """[1,3,4,5,7] should display as [1,3:5,7]M."""
        alg = Algs.MM[[1, 3, 4, 5, 7]]
        s = str(alg)
        assert "[1,3:5,7]" in s

    def test_face_alg_discontinued(self):
        """Face algs also support discontinued slices."""
        alg = Algs.R[[1, 3, 4]]
        s = str(alg)
        assert "[1,3:4]" in s


# All sliceable algs to test
_SLICE_ALGS = [Algs.MM, Algs.EE, Algs.SS]
_FACE_ALGS = [Algs.R, Algs.L, Algs.U, Algs.D, Algs.F, Algs.B]


class TestDiscontinuedSliceRoundTrip:
    """Test str -> parse -> str round-trip for discontinued slices on all sliceable algs."""

    @pytest.mark.parametrize("base_alg", _SLICE_ALGS, ids=lambda a: a.code)
    def test_slice_alg_discontinued_round_trip(self, base_alg):
        """Discontinued slice on M/E/S round-trips through str/parse."""
        alg = base_alg[[1, 3, 5]]
        s = str(alg)
        parsed = Algs.parse(s)
        assert str(parsed) == s

    @pytest.mark.parametrize("base_alg", _SLICE_ALGS, ids=lambda a: a.code)
    def test_slice_alg_mixed_range_round_trip(self, base_alg):
        """Mixed range+singles on M/E/S round-trips through str/parse."""
        alg = base_alg[[1, 2, 4, 5, 6]]
        s = str(alg)
        assert "1:2,4:6" in s
        parsed = Algs.parse(s)
        assert str(parsed) == s

    @pytest.mark.parametrize("base_alg", _FACE_ALGS, ids=lambda a: a.code)
    def test_face_alg_discontinued_round_trip(self, base_alg):
        """Discontinued slice on R/L/U/D/F/B round-trips through str/parse."""
        alg = base_alg[[1, 3, 4]]
        s = str(alg)
        parsed = Algs.parse(s)
        assert str(parsed) == s

    @pytest.mark.parametrize("base_alg", _FACE_ALGS, ids=lambda a: a.code)
    def test_face_alg_mixed_range_round_trip(self, base_alg):
        """Mixed range+singles on R/L/U/D/F/B round-trips through str/parse."""
        # Use indices valid for face algs (1-based, up to cube_size-1)
        alg = base_alg[[1, 2, 5, 6]]
        s = str(alg)
        assert "1:2,5:6" in s
        parsed = Algs.parse(s)
        assert str(parsed) == s


class TestDiscontinuedSliceInverse:
    """Test that discontinued slices work correctly on cubes (play + inverse = solved)."""

    @pytest.mark.parametrize("base_alg", _SLICE_ALGS, ids=lambda a: a.code)
    @pytest.mark.parametrize("cube_size", [6, 7, 8])
    def test_slice_alg_discontinued_inverse(self, base_alg, cube_size):
        """Discontinued slice M/E/S play + inverse returns to solved."""
        app = AbstractApp.create_app(cube_size=cube_size)
        assert app.cube.solved

        max_slice = cube_size - 2
        # Pick non-contiguous indices: 1, 3 (skip 2)
        indices = [i for i in [1, 3] if i <= max_slice]
        if len(indices) < 2:
            pytest.skip(f"Not enough slices for cube_size={cube_size}")

        alg = base_alg[indices]
        alg.play(app.cube)
        alg.inv().play(app.cube)
        assert app.cube.solved

    @pytest.mark.parametrize("base_alg", _FACE_ALGS, ids=lambda a: a.code)
    @pytest.mark.parametrize("cube_size", [6, 7, 8])
    def test_face_alg_discontinued_inverse(self, base_alg, cube_size):
        """Discontinued slice R/L/U/D/F/B play + inverse returns to solved."""
        app = AbstractApp.create_app(cube_size=cube_size)
        assert app.cube.solved

        max_slice = cube_size - 1
        # Pick non-contiguous indices: 1, 3 (skip 2)
        indices = [i for i in [1, 3] if i <= max_slice]
        if len(indices) < 2:
            pytest.skip(f"Not enough slices for cube_size={cube_size}")

        alg = base_alg[indices]
        alg.play(app.cube)
        alg.inv().play(app.cube)
        assert app.cube.solved

    @pytest.mark.parametrize("base_alg", _SLICE_ALGS, ids=lambda a: a.code)
    @pytest.mark.parametrize("cube_size", [7, 8])
    def test_slice_alg_discontinued_parse_play_inverse(self, base_alg, cube_size):
        """Discontinued slice: create, str, parse, play + inverse = solved."""
        app = AbstractApp.create_app(cube_size=cube_size)
        assert app.cube.solved

        max_slice = cube_size - 2
        indices = [1, 3, max_slice]
        alg = base_alg[indices]
        s = str(alg)
        parsed = Algs.parse(s)

        parsed.play(app.cube)
        parsed.inv().play(app.cube)
        assert app.cube.solved

    @pytest.mark.parametrize("base_alg", _FACE_ALGS, ids=lambda a: a.code)
    @pytest.mark.parametrize("cube_size", [7, 8])
    def test_face_alg_discontinued_parse_play_inverse(self, base_alg, cube_size):
        """Discontinued slice: create, str, parse, play + inverse = solved."""
        app = AbstractApp.create_app(cube_size=cube_size)
        assert app.cube.solved

        max_slice = cube_size - 1
        indices = [1, 3, max_slice]
        alg = base_alg[indices]
        s = str(alg)
        parsed = Algs.parse(s)

        parsed.play(app.cube)
        parsed.inv().play(app.cube)
        assert app.cube.solved


class TestDiscontinuedSliceScramble:
    """Test that scrambles with discontinued slices round-trip correctly."""

    @pytest.mark.parametrize("seed", [100, 101, 102, 103, 104, 105])
    @pytest.mark.parametrize("cube_size", [6, 7, 8])
    def test_scramble_with_discontinued_slices_round_trip(self, seed, cube_size):
        """Scramble (which may produce discontinued slices) round-trips."""
        scramble = Algs.scramble(cube_size, seed, seq_length=20)
        printable = scramble.to_printable()
        s = str(printable)
        parsed = Algs.parse(s)

        app1 = AbstractApp.create_app(cube_size=cube_size)
        app2 = AbstractApp.create_app(cube_size=cube_size)

        printable.play(app1.cube)
        parsed.play(app2.cube)

        printable.inv().play(app1.cube)
        parsed.inv().play(app2.cube)

        assert app1.cube.solved, f"Original + inverse should return to solved"
        assert app2.cube.solved, f"Parsed + inverse should return to solved"
