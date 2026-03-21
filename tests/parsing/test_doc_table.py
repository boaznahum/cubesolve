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
    DocRow("R2: outermost R layer 180°",         Algs.R.with_n(2),                "R2",       "R2"),

    # §2 Inner Slices
    DocRow("2R: 2nd layer from R only",          Algs.R[2:2],                     "2R",       "2R"),
    DocRow("3R: 3rd layer from R only",          Algs.R[3:3],                     "3R",       "3R",  sizes=(4, 5)),
    DocRow("[3:4]R: slices 3–4 from R",          Algs.R[3:4],                     "[3:4]R",   "[3:4]R", sizes=(5,),
           equivalent=Algs.R[3:3] + Algs.R[4:4], equiv_sizes=(5,)),
    DocRow("[3:]R: all from 3rd to last",         Algs.R[3:],                      "[3:]R",    "[3:]R", sizes=(5,),
           equivalent=Algs.R[3:3] + Algs.R[4:4], equiv_sizes=(5,)),
    DocRow("[:4]R: slices 1–4 from R",           Algs.R[1:4],                     "[:4]R",    "[1:4]R", sizes=(5,),
           equivalent=Algs.R + Algs.R[2:2] + Algs.R[3:3] + Algs.R[4:4], equiv_sizes=(5,)),

    # §3 Wide Moves
    DocRow("Rw: 2 outermost R-side layers",      Algs.Rw,                         "Rw",       "Rw",
           compat_3x3_parser_str="Rw", compat_3x3_expected_str="[:-1]Rw",
           equivalent=Algs.R + Algs.R[2:2], equiv_sizes=(3, 4, 5)),
    DocRow("r: 2 outermost R-side layers",        Algs.r,                          "r",        "r",
           compat_3x3_parser_str="r", compat_3x3_expected_str="[:-1]r",
           equivalent=Algs.R + Algs.R[2:2], equiv_sizes=(3, 4, 5)),
    DocRow("3Rw: 3 outermost R-side layers",      WideLayerAlg(FaceName.R, layers=3),  "3Rw",  "3Rw",
           compat_3x3_parser_str="3Rw", compat_3x3_expected_str="[:-1]Rw",
           equivalent=Algs.R + Algs.R[2:2] + Algs.R[3:3], equiv_sizes=(5,)),
    DocRow("3r: 3 outermost R-side layers",       WideLayerAlg(FaceName.R, layers=3, lowercase=True), "3r", "3r",
           compat_3x3_parser_str="3r", compat_3x3_expected_str="[:-1]r",
           equivalent=Algs.R + Algs.R[2:2] + Algs.R[3:3], equiv_sizes=(5,)),
    DocRow("[:-1]Rw: all-but-last (adaptive)",    Algs.RRw,                        "[:-1]Rw",  "[:-1]Rw",
           equivalent=Algs.R + Algs.R[2:2] + Algs.R[3:3] + Algs.R[4:4], equiv_sizes=(5,)),
    DocRow("[:-1]r: all-but-last (adaptive)",     Algs.rr,                         "[:-1]r",   "[:-1]r",
           equivalent=Algs.R + Algs.R[2:2] + Algs.R[3:3] + Algs.R[4:4], equiv_sizes=(5,)),

    # §4 Slice Moves
    DocRow("M: single center slice, like L",     Algs.M,                          "M",        "M",
           compat_3x3_parser_str="M", compat_3x3_expected_str="[:]M"),
    DocRow("[:]M: ALL inner slices, like L",      Algs.MM,                         "[:]M",     "[:]M",
           equivalent=Algs.MM[1] + Algs.MM[2] + Algs.MM[3], equiv_sizes=(5,)),

    # §5 Slice Range & Indexing
    DocRow("[1:2]R: R face + 1st inner (= Rw)",  Algs.R[1:2],                     "[1:2]R",   "[1:2]R",
           equivalent=Algs.R + Algs.R[2:2], equiv_sizes=(3, 4, 5)),
    DocRow("[2:3]R: R layers 2–3 (no outer)",     Algs.R[2:3],                     "[2:3]R",   "[2:3]R", sizes=(5,),
           equivalent=Algs.R[2:2] + Algs.R[3:3], equiv_sizes=(5,)),
    DocRow("[1:1]M: 1st M slice only",            Algs.MM[1],                      "[1]M",     "[1:1]M"),
    DocRow("[1:2]M: M slices 1–2",                Algs.MM[1:2],                    "[1:2]M",   "[1:2]M", sizes=(4, 5),
           equivalent=Algs.MM[1] + Algs.MM[2], equiv_sizes=(4, 5)),
    DocRow("[1:]M: all M slices from 1st",        Algs.MM[1:],                     "[1:]M",    "[1:]M"),

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
        assert_algs_equivalent(Algs.M, Algs.MM, 3)

    def test_5x5_M_not_equals_MM(self) -> None:
        """On 5x5, single center M != all slices MM (3 inner slices)."""
        assert_algs_equivalent(Algs.M, Algs.MM, 5, expect_equal=False)

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

    # --- Known unsupported ---

    @pytest.mark.xfail(reason="Bracket slicing on wide Rw not supported (footnote ⑧)", raises=Exception)
    def test_bracket_on_wide_Rw_not_supported(self) -> None:
        """[3:4]Rw — bracket slicing on wide moves throws InternalSWError."""
        Algs.parse("[3:4]Rw")

    @pytest.mark.xfail(reason="Bracket slicing on lowercase r not supported (footnote ⑧)", raises=Exception)
    def test_bracket_on_wide_r_not_supported(self) -> None:
        """[3:4]r — bracket slicing on lowercase wide throws InternalSWError."""
        Algs.parse("[3:4]r")

    @pytest.mark.xfail(reason="[3:4]R on 4x4 crashes at play time (footnote ⑨)", raises=Exception)
    def test_bracket_face_out_of_range_4x4(self) -> None:
        """[3:4]R on 4x4 — slice indices don't exist, runtime AssertionError."""
        from cube.domain.model.Cube import Cube
        from tests.test_utils import _test_sp
        alg = Algs.parse("[3:4]R")
        cube = Cube(4, sp=_test_sp)
        alg.play(cube)
