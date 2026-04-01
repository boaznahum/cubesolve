"""
Tests that verify the Summary Table in docs/algorithm_notation.md.

For each row: Code and Parser must produce equivalent algorithms,
and str() must round-trip correctly.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from cube.domain.algs.Alg import Alg
from cube.domain.algs.Algs import Algs
from cube.domain.algs._parser import parse_alg
from cube.domain.algs.WideLayerAlg import WideLayerAlg
from cube.domain.model import FaceName
from tests.utils._alg_utils import assert_algs_equivalent


@dataclass(frozen=True)
class DocRow:
    """One row from the doc summary table."""
    description: str
    code: Alg
    parser_str: str
    expected_str: str
    sizes: tuple[int, ...] = (3, 4, 5)
    compat_3x3_parser_str: str | None = None  # None means same as parser_str
    compat_3x3_expected_str: str | None = None  # None means same as expected_str
    equivalent: Alg | None = None  # Decomposition into primitives
    equiv_sizes: tuple[int, ...] = (3, 4, 5)  # Sizes where equivalence holds


# fmt: off
DOC_ROWS: list[DocRow] = [
    # §1 Face Moves
    DocRow("R: outermost R layer CW",           Algs.R,                          "R",        "R"),
    DocRow("R': outermost R layer CCW",          Algs.R.prime,                    "R'",       "R'"),
    DocRow("R2: outermost R layer 180°",         Algs.R * 2,                "R2",       "R2"),

    # §2 Inner Slices
    DocRow("2R: 2nd layer (rmul)",              2 * Algs.R,                      "2R",       "2R"),
    DocRow("2R: 2nd layer (int index)",          Algs.R[2],                       "2R",       "2R"),
    DocRow("2R: 2nd layer (slice)",              Algs.R[2:2],                     "2R",       "2R"),
    DocRow("3R: 3rd layer (rmul)",              3 * Algs.R,                      "3R",       "3R",  sizes=(4, 5)),
    DocRow("3R: 3rd layer (int index)",          Algs.R[3],                       "3R",       "3R",  sizes=(4, 5)),
    DocRow("3R: 3rd layer (slice)",              Algs.R[3:3],                     "3R",       "3R",  sizes=(4, 5)),
    DocRow("[3:4]R: slices 3–4 from R",          Algs.R[3:4],                     "[3:4]R",   "[3:4]R", sizes=(4, 5),
           equivalent=Algs.parse("3R") + Algs.L.prime, equiv_sizes=(4,)),
    DocRow("[3:4]R: slices 3–4 (5×5, no span)", Algs.R[3:4],                     "[3:4]R",   "[3:4]R", sizes=(5,),
           equivalent=Algs.parse("3R 4R"), equiv_sizes=(5,)),
    DocRow("[3:4]Rw: slices 3–4 via Rw",        Algs.Rw[3:4],                    "[3:4]Rw",  "[3:4]R", sizes=(4, 5)),
    DocRow("[3:4]r: slices 3–4 via r",           Algs.r[3:4],                     "[3:4]r",   "[3:4]R", sizes=(4, 5)),
    DocRow("[3:]R: all from 3rd to last",         Algs.R[3:],                      "[3:]R",    "[3:]R", sizes=(5,),
           equivalent=Algs.parse("3R 4R") + Algs.L.prime, equiv_sizes=(5,)),
    DocRow("[3:]r: all from 3rd to last via r",  Algs.r[3:],                      "[3:]r",    "[3:]R", sizes=(5,)),
    DocRow("[:]R: all R layers (≡ X)",             Algs.R[:],                       "[:]R",     "[:]R",
           equivalent=Algs.X, equiv_sizes=(3, 4, 5)),
    DocRow("[:]Rw: all R layers via Rw (≡ X)",    Algs.Rw[:],                      "[:]Rw",    "[:]R",
           equivalent=Algs.X, equiv_sizes=(3, 4, 5)),
    DocRow("[:]r: all R layers via r (≡ X)",       Algs.r[:],                       "[:]r",     "[:]R",
           equivalent=Algs.X, equiv_sizes=(3, 4, 5)),
    DocRow("[1:]R: all layers (adaptive, ≡ X)",   Algs.R[1:],                      "[1:]R",    "[1:]R",
           equivalent=Algs.X, equiv_sizes=(3, 4, 5)),
    DocRow("[:2]R: layers 1–2 (≡ Rw)",           Algs.R[:2],                      "[:2]R",    "[1:2]R",
           equivalent=Algs.Rw, equiv_sizes=(3, 4, 5)),
    DocRow("[:2]r: layers 1–2 via r",            Algs.r[:2],                      "[:2]r",    "[1:2]R"),
    DocRow("[:3]R: layers 1–3 (≡ [1:3]R)",      Algs.R[:3],                      "[:3]R",    "[1:3]R", sizes=(5,),
           equivalent=Algs.parse("R 2R 3R"), equiv_sizes=(5,)),
    DocRow("[:3]r: layers 1–3 via r",            Algs.r[:3],                      "[:3]r",    "[1:3]R", sizes=(5,)),

    # §3 Wide Moves
    DocRow("Rw: 2 outermost R-side layers",      Algs.Rw,                         "Rw",       "Rw",
           compat_3x3_parser_str="Rw", compat_3x3_expected_str="[:-1]Rw",
           equivalent=Algs.parse("R 2R"), equiv_sizes=(3, 4, 5)),
    DocRow("r: 2 outermost R-side layers",        Algs.r,                          "r",        "r",
           compat_3x3_parser_str="r", compat_3x3_expected_str="[:-1]r",
           equivalent=Algs.parse("R 2R"), equiv_sizes=(3, 4, 5)),
    DocRow("3Rw: 3 outermost R-side layers",      3 * Algs.Rw,  "3Rw",  "3Rw",
           compat_3x3_parser_str="3Rw", compat_3x3_expected_str="3Rw",
           equivalent=Algs.parse("R 2R 3R"), equiv_sizes=(5,)),
    DocRow("3r: 3 outermost R-side layers",       3 * Algs.r, "3r", "3r",
           compat_3x3_parser_str="3r", compat_3x3_expected_str="3r",
           equivalent=Algs.parse("R 2R 3R"), equiv_sizes=(5,)),
    DocRow("[:-1]Rw: all-but-last (adaptive)",    Algs.RRw,                        "[:-1]Rw",  "[:-1]Rw",
           equivalent=Algs.parse("R 2R 3R 4R"), equiv_sizes=(5,)),
    DocRow("[:-1]r: all-but-last (adaptive)",     Algs.rr,                         "[:-1]r",   "[:-1]r",
           equivalent=Algs.parse("R 2R 3R 4R"), equiv_sizes=(5,)),

    # §4 Slice Moves
    DocRow("M: single center slice, like L",     Algs.M,                          "M",        "M",
           compat_3x3_parser_str="M", compat_3x3_expected_str="m"),
    DocRow("m: ALL inner slices, like L",         Algs.m,                         "m",        "m",
           equivalent=Algs.parse("[1:1]m [2:2]m [3:3]m"), equiv_sizes=(5,)),

    # §5 Slice Range & Indexing
    DocRow("[1:2]R: R face + 1st inner (= Rw)",  Algs.R[1:2],                     "[1:2]R",   "[1:2]R",
           equivalent=Algs.parse("R 2R"), equiv_sizes=(3, 4, 5)),
    DocRow("[2:3]R: R layers 2–3 (no outer)",     Algs.R[2:3],                     "[2:3]R",   "[2:3]R", sizes=(5,),
           equivalent=Algs.parse("2R 3R"), equiv_sizes=(5,)),
    DocRow("[1:1]m: 1st m slice only",            Algs.m[1],                      "[1]m",     "[1:1]m"),
    DocRow("[1:2]m: m slices 1–2",                Algs.m[1:2],                    "[1:2]m",   "[1:2]m", sizes=(4, 5),
           equivalent=Algs.parse("[1:1]m [2:2]m"), equiv_sizes=(4, 5)),
    DocRow("[1:]m: all m slices from 1st",        Algs.m[1:],                     "[1:]m",    "[1:]m"),

    # §6 Whole Cube Rotations
    DocRow("X: rotate whole cube like R",         Algs.X,                          "X",        "X"),
    DocRow("Y: rotate whole cube like U",         Algs.Y,                          "Y",        "Y"),
    DocRow("Z: rotate whole cube like F",         Algs.Z,                          "Z",        "Z"),
]
# fmt: on


class TestDocTable:
    """Verify each doc table row: code == parser, str() round-trips."""

    @pytest.mark.parametrize(
        "row", DOC_ROWS, ids=[r.description for r in DOC_ROWS]
    )
    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_code_vs_parser(self, row: DocRow, cube_size: int) -> None:
        """Code constant and parser produce equivalent algorithms."""
        if cube_size not in row.sizes:
            pytest.skip(f"not applicable for {cube_size}x{cube_size}")
        parsed = Algs.parse(row.parser_str)
        assert_algs_equivalent(row.code, parsed, cube_size)

    @pytest.mark.parametrize(
        "row", DOC_ROWS, ids=[r.description for r in DOC_ROWS]
    )
    def test_str_round_trip(self, row: DocRow) -> None:
        """str(code) and str(parsed) both match expected_str."""
        assert str(row.code) == row.expected_str
        assert str(Algs.parse(row.parser_str)) == row.expected_str

    @pytest.mark.parametrize(
        "row",
        [r for r in DOC_ROWS if r.equivalent is not None],
        ids=[r.description for r in DOC_ROWS if r.equivalent is not None],
    )
    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_equivalent_decomposition(self, row: DocRow, cube_size: int) -> None:
        """Code equals its decomposition into primitives."""
        assert row.equivalent is not None
        if cube_size not in row.equiv_sizes:
            pytest.skip(f"equivalence not applicable for {cube_size}x{cube_size}")
        assert_algs_equivalent(row.code, row.equivalent, cube_size)

    @pytest.mark.parametrize(
        "row",
        [r for r in DOC_ROWS if r.compat_3x3_parser_str is not None],
        ids=[r.description for r in DOC_ROWS if r.compat_3x3_parser_str is not None],
    )
    def test_compat_3x3_str(self, row: DocRow) -> None:
        """compat_3x3 parser output matches documented str()."""
        assert row.compat_3x3_parser_str is not None
        assert row.compat_3x3_expected_str is not None
        compat = parse_alg(row.compat_3x3_parser_str, compat_3x3=True)
        assert str(compat) == row.compat_3x3_expected_str


class TestSpecialCases:
    """Cross-row equivalences and size-dependent behavior."""

    # --- Notation equivalences ---

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_Rw_equals_r(self, cube_size: int) -> None:
        """Rw and r are the same move (different display only)."""
        assert_algs_equivalent(Algs.Rw, Algs.r, cube_size)

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_bracket_1_2_R_equals_Rw(self, cube_size: int) -> None:
        """[1:2]R is equivalent to Rw."""
        assert_algs_equivalent(Algs.R[1:2], Algs.Rw, cube_size)

    def test_3x3_2L_equals_M(self) -> None:
        """On 3x3, 2L (2nd layer from L) is the same as M."""
        assert_algs_equivalent(Algs.parse("2L"), Algs.M, 3)

    # --- Size-dependent: M vs MM ---

    def test_3x3_M_equals_MM(self) -> None:
        """On 3x3, single center M == all slices MM (only 1 inner slice)."""
        assert_algs_equivalent(Algs.M, Algs.m, 3)

    def test_5x5_M_not_equals_MM(self) -> None:
        """On 5x5, single center M != all slices MM (3 inner slices)."""
        assert_algs_equivalent(Algs.M, Algs.m, 5, expect_equal=False)

    # --- Size-dependent: clamping ---

    def test_3x3_3Rw_clamped_to_Rw(self) -> None:
        """On 3x3, 3Rw clamps to min(3, 2) = 2 layers = Rw."""
        assert_algs_equivalent(WideLayerAlg(FaceName.R, layers=3), Algs.Rw, 3)

    # --- Size-dependent: Rw vs adaptive ---

    def test_3x3_Rw_equals_adaptive(self) -> None:
        """On 3x3, Rw (2 layers) == [:-1]Rw (also 2 layers)."""
        assert_algs_equivalent(Algs.Rw, Algs.RRw, 3)

    def test_5x5_Rw_not_equals_adaptive(self) -> None:
        """On 5x5, Rw (2 layers) != [:-1]Rw (4 layers)."""
        assert_algs_equivalent(Algs.Rw, Algs.RRw, 5, expect_equal=False)

    # --- Known unsupported: bracket on wide moves ---

    # --- Opposite face via inner slice indexing ---

    # --- Opposite face via inner slice indexing (all faces) ---

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    @pytest.mark.parametrize("face,opposite_prime", [
        (Algs.R, Algs.L.prime),
        (Algs.L, Algs.R.prime),
        (Algs.U, Algs.D.prime),
        (Algs.D, Algs.U.prime),
        (Algs.F, Algs.B.prime),
        (Algs.B, Algs.F.prime),
    ])
    def test_last_layer_equals_opposite_prime(self, face: Alg, opposite_prime: Alg, cube_size: int) -> None:
        """nR on NxN (n=N) == opposite face prime (e.g. 4R on 4x4 == L')."""
        last_index = cube_size
        sliced = face[last_index:last_index]
        assert_algs_equivalent(sliced, opposite_prime, cube_size)

    # --- Known unsupported ---

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_all_slices_R_equals_X(self, cube_size: int) -> None:
        """[:]R = all layers = X on all sizes."""
        assert_algs_equivalent(Algs.R[:], Algs.X, cube_size)

    def test_all_slices_R_str(self) -> None:
        """str(R[:]) == '[:]R'."""
        assert str(Algs.R[:]) == "[:]R"

    def test_all_slices_R_parse_round_trip(self) -> None:
        """parse('[:]R') round-trips correctly."""
        assert str(Algs.parse("[:]R")) == "[:]R"

    def test_all_slices_Rw_parse_round_trip(self) -> None:
        """parse('[:]Rw') round-trips correctly."""
        assert str(Algs.parse("[:]Rw")) == "[:]R"

    def test_all_slices_r_parse_round_trip(self) -> None:
        """parse('[:]r') round-trips correctly."""
        assert str(Algs.parse("[:]r")) == "[:]R"

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_all_slices_R_parse_equals_X(self, cube_size: int) -> None:
        """parse('[:]R') == X."""
        assert_algs_equivalent(Algs.parse("[:]R"), Algs.X, cube_size)

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_parse_all_slices_Rw_equals_X(self, cube_size: int) -> None:
        """parse('[:]Rw') = all layers = X."""
        assert_algs_equivalent(Algs.parse("[:]Rw"), Algs.X, cube_size)

    @pytest.mark.parametrize("cube_size", [3, 4, 5])
    def test_parse_all_slices_r_equals_X(self, cube_size: int) -> None:
        """parse('[:]r') = all layers = X."""
        assert_algs_equivalent(Algs.parse("[:]r"), Algs.X, cube_size)

    def test_bracket_on_wide_Rw_equals_R(self) -> None:
        """[3:4]Rw == [3:4]R — wide slicing produces same as face slicing."""
        assert_algs_equivalent(Algs.Rw[3:4], Algs.R[3:4], 5)

    def test_bracket_on_wide_r_equals_R(self) -> None:
        """[3:4]r == [3:4]R — lowercase wide slicing produces same as face slicing."""
        assert_algs_equivalent(Algs.r[3:4], Algs.R[3:4], 5)

    def test_parse_bracket_Rw_equals_R(self) -> None:
        """parse("[3:4]Rw") == parse("[3:4]R")."""
        assert_algs_equivalent(Algs.parse("[3:4]Rw"), Algs.parse("[3:4]R"), 5)

    def test_parse_bracket_r_equals_R(self) -> None:
        """parse("[3:4]r") == parse("[3:4]R")."""
        assert_algs_equivalent(Algs.parse("[3:4]r"), Algs.parse("[3:4]R"), 5)

    # --- SiGN range syntax (3-4R) ---

    def test_parse_sign_range_R(self) -> None:
        """parse("3-4R") == parse("[3:4]R")."""
        assert_algs_equivalent(Algs.parse("3-4R"), Algs.parse("[3:4]R"), 5)

    def test_parse_sign_range_Rw(self) -> None:
        """parse("3-4Rw") == parse("[3:4]R")."""
        assert_algs_equivalent(Algs.parse("3-4Rw"), Algs.parse("[3:4]R"), 5)

    def test_parse_sign_range_r(self) -> None:
        """parse("3-4r") == parse("[3:4]R")."""
        assert_algs_equivalent(Algs.parse("3-4r"), Algs.parse("[3:4]R"), 5)

    def test_parse_sign_range_str_round_trip(self) -> None:
        """parse("3-4R") produces str == "[3:4]R"."""
        assert str(Algs.parse("3-4R")) == "[3:4]R"

    def test_bracket_face_spans_opposite_4x4(self) -> None:
        """[3:4]R on 4x4 — spans to opposite face: 3R + L'."""
        assert_algs_equivalent(Algs.R[3:4], Algs.R[3:3] + Algs.L.prime, 4)
