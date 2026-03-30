"""Layer 3 permutation solver for 2x2 beginner method.

Permutes the 4 top-layer corners into their correct positions.
Orientation is ignored — L3Orient runs after this step.

IMPORTANT — No face colors:
    Like all 2x2 solvers, this works entirely with corner sticker colors.
    Never accesses Face.color, self.white_face, match_faces, in_position,
    or any API that reads face colors from centers.

Strategy (3-cycle + Y rotations — no extra algorithms):
1. Find any top corner that is in its correct position.
2. If none found (derangement), apply the 3-cycle once to create one.
3. Y-rotate the in-position corner to FLU (whole-cube rotation preserves matching).
4. Apply the 3-cycle (which fixes FLU) 1-2 times to solve the remaining 3.
5. If the permutation is odd (2x2 parity — impossible on 3x3), all of the above
   fails. Undo, apply D to shift the bottom reference frame (flipping parity
   from odd to even), and retry.
"""

from __future__ import annotations

from cube.domain.algs import Algs, Alg
from cube.domain.model import Color, Corner
from cube.domain.model.Face import Face
from cube.domain.solver._2x2_beginner._l3_utils import find_yellow_color, find_white_face, bring_white_to_down
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.SolverHelper import StepSolver
from cube.domain.solver.protocols import SolverElementsProvider


class L3Permute(StepSolver):
    """Last layer corner permutation solver for 2x2.

    Works purely with corner sticker colors — no face colors.
    """

    __slots__: list[str] = []

    # U' L' U R U' L U R' — 3-corner cycle, leaves FLU fixed
    _CYCLE: Alg = Algs.alg(
        None,
        Algs.U.prime, Algs.L.prime, Algs.U, Algs.R,
        Algs.U.prime, Algs.L, Algs.U, Algs.R.prime,
    )

    # Y rotations to bring corner at index to FLU position.
    # Index: 0=FLU (no rotation), 1=FRU, 2=BRU, 3=BLU.
    # Y rotates the whole cube same direction as U (clockwise from above),
    # so after Y the corner that was at FRU is now at FLU, etc.
    _Y_TO_FLU: list[Alg | None] = [
        None,                   # 0: FLU — already there
        Algs.Y,                 # 1: FRU → FLU
        Algs.Y * 2,             # 2: BRU → FLU
        Algs.Y.prime,           # 3: BLU → FLU
    ]

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "L3Permute")

    @property
    def is_solved(self) -> bool:
        """Check using default white color."""
        return self.is_solved_with(self.cmn.white)

    def is_solved_with(self, white_color: Color) -> bool:
        """Check if all 4 top-layer corners are in correct positions.

        Ignores orientation — only checks that each top corner's
        non-yellow colors match the bottom corner below it.
        Uses query mode so no moves are visible.
        """
        yellow_color: Color = find_yellow_color(self.cube, white_color)

        white_face: Face | None = find_white_face(self.cube, white_color)
        if white_face is None:
            return False

        yellow_face: Face = white_face.opposite

        return self._is_u_aligned(yellow_face, white_face, white_color, yellow_color) >= 0

    def solve(self, white_color: Color | None = None) -> None:
        """Permute last-layer corners into correct positions."""
        wc: Color = white_color or self.cmn.white
        if self.is_solved_with(wc):
            self._align_u_layer(wc)
            return

        with self._logger.tab("Doing L3 Permute"):
            with self.ann.annotate(h1="Doing L3 Permute"):
                self._solve(wc)

    def _align_u_layer(self, white_color: Color) -> None:
        """Align top layer with bottom using U rotations."""
        yellow_color: Color = find_yellow_color(self.cube, white_color)
        white_face: Face | None = find_white_face(self.cube, white_color)

        assert white_face is not None  # we must reach here after L1 is solved

        yellow_face: Face = white_face.opposite
        self._try_u_alignment(yellow_face, white_face, white_color, yellow_color)

    def _solve(self, white_color: Color) -> None:
        yellow_color: Color = find_yellow_color(self.cube, white_color)

        bring_white_to_down(self, white_color)

        up: Face = self.cube.up
        down: Face = self.cube.down

        # On a 2x2, the top-layer permutation can be odd (a single transposition
        # or 4-cycle), which is impossible on a 3x3. When parity is odd,
        # _do_permute detects the failure and returns True. Applying D shifts
        # the bottom reference frame (flipping parity from odd to even) while
        # keeping L1 solved (white still down). D is a 4-cycle (odd permutation),
        # so each D application flips the parity. At most 2 attempts needed.
        for d_count in range(4):
            swap_detected = self._do_permute(up, down, white_color, yellow_color)
            if not swap_detected:
                return  # success

            # _do_permute already undid its moves. Apply D to try next alignment.
            with self.ann.annotate(h2="Breaking parity (2x2 swap)"):
                self.op.play(Algs.D)

        raise AssertionError("L3 Permute: parity not resolved after 4 D rotations")

    def _do_permute(self, up: Face, down: Face, white_color: Color,
                    yellow_color: Color) -> bool:
        """Try to place all 4 top-layer corners using 3-cycles and Y rotations.

        Algorithm:
        1. If already solvable with U-alignment, align and return success.
        2. Find any corner in position. If none (derangement), apply one
           3-cycle — for even derangements this always creates a fixed point.
        3. Y-rotate the in-position corner to FLU (preserves matching).
        4. Apply the 3-cycle (fixes FLU, cycles FRU/BLU/BRU) 1-2 times.
        5. If all in position, return success. Otherwise, odd parity — undo all.

        Returns False on success (all corners placed).
        Returns True if odd parity detected — all moves undone so
        the caller can apply D and retry.
        """
        history_start = len(self.op.history())

        # Quick check: already solvable with U-alignment?
        if self._is_u_aligned(up, down, white_color, yellow_color) >= 0:
            self._try_u_alignment(up, down, white_color, yellow_color)
            return False  # success

        # Find any corner in position
        pos = self._find_any_in_position(up, down, white_color, yellow_color)

        if pos is None:
            # Derangement: apply cycle once to create a fixed point.
            # For even derangements (double transpositions), one 3-cycle
            # application always produces at least one fixed point.
            self.op.play(self._CYCLE)
            pos = self._find_any_in_position(up, down, white_color, yellow_color)

        if pos is None:
            # No fixed point even after cycle → odd parity (4-cycle)
            self._undo_to(history_start)
            return True  # odd parity, caller should apply D and retry

        # Y-rotate the in-position corner to FLU.
        # Y is a whole-cube rotation that preserves top-bottom matching,
        # so the corner stays in position after Y.
        y_alg = self._Y_TO_FLU[pos]
        if y_alg is not None:
            self.op.play(y_alg)

        # After Y, face references are still valid (Y preserves up/down)
        # but corners at each position have changed.

        # Cycle remaining 3 corners (FRU, BLU, BRU) with FLU fixed.
        # For even permutations with FLU fixed, the remaining 3 form
        # a 3-cycle, solvable in 1-2 cycle applications.
        with self.ann.annotate(
                (up.corner_top_right, AnnWhat.Moved),
                (up.corner_top_left, AnnWhat.Moved),
                (up.corner_bottom_right, AnnWhat.Moved),
                h2="Cycling corners",
        ):
            for _ in range(2):
                if self._all_in_position(up, down, white_color, yellow_color):
                    break
                self.op.play(self._CYCLE)

        if not self._all_in_position(up, down, white_color, yellow_color):
            # Residual is a transposition → total permutation was odd
            self._undo_to(history_start)
            return True  # odd parity, caller should apply D and retry

        # All corners in position — U-align if needed
        assert self._try_u_alignment(up, down, white_color, yellow_color), (
            "L3 Permute: U-alignment failed after positioning"
        )
        return False  # success

    def _undo_to(self, history_start: int) -> None:
        """Undo all moves back to the given history point."""
        moves_to_undo = len(self.op.history()) - history_start
        for _ in range(moves_to_undo):
            self.op.undo(animation=False)

    def _find_any_in_position(self, up: Face, down: Face,
                              white_color: Color, yellow_color: Color) -> int | None:
        """Find any top corner that matches the bottom corner below it.

        Returns the position index (0=FLU, 1=FRU, 2=BRU, 3=BLU) or None.
        """
        pairs = [
            (up.corner_bottom_left, down.corner_top_left),       # 0: FLU / DFL
            (up.corner_bottom_right, down.corner_top_right),     # 1: FRU / DFR
            (up.corner_top_right, down.corner_bottom_right),     # 2: BRU / DBR
            (up.corner_top_left, down.corner_bottom_left),       # 3: BLU / DBL
        ]
        for i, (tc, bc) in enumerate(pairs):
            if self._corner_in_position(tc, bc, white_color, yellow_color):
                return i
        return None

    def _is_u_aligned(self, up: Face, down: Face,
                      white_color: Color, yellow_color: Color) -> int:
        """Check if any U rotation aligns top with bottom. No moves made.

        :return >= 0 if is aligned the number o required rotations to align
        """

        n = 0
        with self.op.with_query_restore_state():
            for _ in range(4):
                if self._all_in_position(up, down, white_color, yellow_color):
                    return n
                self.op.play(Algs.U)
                n += 1

            return -1

    def _try_u_alignment(self, up: Face, down: Face,
                         white_color: Color, yellow_color: Color) -> bool:
        """Apply U rotations to align top layer with bottom. Returns True if aligned."""

        # After 4 U rotations we're back to the original state
        n = self._is_u_aligned(up, down, white_color, yellow_color)
        if n < 0:
            return False
        else:
            self.op.play( (Algs.U * n).simplify())
            return True


    def _corner_in_position(self, top_corner: Corner, bottom_corner: Corner,
                            white_color: Color, yellow_color: Color) -> bool:
        """Check if a single top corner matches the bottom corner below it."""
        tc_colors: frozenset[Color] = top_corner.colors_id - {yellow_color}
        bc_colors: frozenset[Color] = bottom_corner.colors_id - {white_color}
        return tc_colors == bc_colors

    def _all_in_position(
        self, up: Face, down: Face,
        white_color: Color, yellow_color: Color,
    ) -> bool:
        """Check if all 4 top corners match their bottom counterparts."""
        pairs = [
            (up.corner_bottom_right, down.corner_top_right),   # FRU / FRD
            (up.corner_bottom_left, down.corner_top_left),     # FLU / FLD
            (up.corner_top_right, down.corner_bottom_right),   # BRU / BRD
            (up.corner_top_left, down.corner_bottom_left),     # BLU / BLD
        ]
        return all(
            self._corner_in_position(tc, bc, white_color, yellow_color)
            for tc, bc in pairs
        )
