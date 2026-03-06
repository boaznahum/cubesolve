"""Layer 3 permutation solver for 2x2 beginner method.

Permutes the 4 top-layer corners into their correct positions.
Orientation is ignored — L3Orient runs after this step.

IMPORTANT — No face colors:
    Like all 2x2 solvers, this works entirely with corner sticker colors.
    Never accesses Face.color, self.white_face, match_faces, in_position,
    or any API that reads face colors from centers.

Strategy (3-cycle + adjacent swap):
1. U-rotate until FLU corner is in position (always possible on 2x2).
2. Apply 3-cycle (U R U' L' U R' U' L) until BLU is in position.
   The 3-cycle leaves FLU fixed, cycles FRU/BRU/BLU. Max 2 applications.
3. If FRU and BRU are still swapped: U' swap U to fix them.
4. U-align to match top and bottom layers.

The swap algorithm is: R' F R' B2 R F' R' B2 R2 U'
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

    # R' F R' B2 R F' R' B2 R2 U' — adjacent corner swap
    _SWAP: Alg = Algs.alg(
        None,
        Algs.R.prime, Algs.F, Algs.R.prime, Algs.B * 2,
        Algs.R, Algs.F.prime, Algs.R.prime, Algs.B * 2,
        Algs.R * 2, Algs.U.prime,
    )

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "L3Permute")

    @property
    def is_solved(self) -> bool:
        """Check if all 4 top-layer corners are in correct positions.

        Ignores orientation — only checks that each top corner's
        non-yellow colors match the bottom corner below it.
        Uses query mode so no moves are visible.
        """
        white_color: Color = self.cmn.white
        yellow_color: Color = find_yellow_color(self.cube, white_color)

        white_face: Face | None = find_white_face(self.cube, white_color)
        if white_face is None:
            return False

        yellow_face: Face = white_face.opposite

        return self._is_u_aligned(yellow_face, white_face, white_color, yellow_color)

    def solve(self) -> None:
        """Permute last-layer corners into correct positions."""
        if self.is_solved:
            # Corners are in position but may need U-alignment
            self._align_u_layer()
            return

        with self.ann.annotate(h1="Doing L3 Permute"):
            self._solve()

    def _align_u_layer(self) -> None:
        """Align top layer with bottom using U rotations."""
        white_color: Color = self.cmn.white
        white_face: Face | None = find_white_face(self.cube, white_color)

        yellow_color: Color = find_yellow_color(self.cube, white_color)


        assert white_face is not None  # we must reach here after L1 is solved

        yellow_face: Face = white_face.opposite
        self._try_u_alignment(yellow_face, white_face, white_color, yellow_color)

    def _solve(self) -> None:
        white_color: Color = self.cmn.white
        yellow_color: Color = find_yellow_color(self.cube, white_color)

        bring_white_to_down(self, white_color)

        up: Face = self.cube.up
        down: Face = self.cube.down
        self._do_permute(up, down, white_color, yellow_color)

    def _do_permute(self, up: Face, down: Face, white_color: Color, yellow_color: Color) -> None:
        """Place corners using 3-cycle + swap."""

        # Step 1: U-rotate until FLU is in position (always possible on 2x2)
        self._bring_correct_to_flu(up, down, white_color, yellow_color)

        # Step 2: Apply 3-cycle until BLU is in position (max 2)
        with self.ann.annotate(
                (up.corner_top_right, AnnWhat.Moved),
                (up.corner_top_left, AnnWhat.Moved),
                (up.corner_bottom_right, AnnWhat.Moved),
                h2="Cycling corners",
        ):
            for _ in range(2):
                if self._corner_in_position(up.corner_top_left, down.corner_bottom_left,
                                            white_color, yellow_color):
                    break
                self.op.play(self._CYCLE)

        assert self._corner_in_position(up.corner_top_left, down.corner_bottom_left,
                                        white_color, yellow_color), "BLU not in position after cycling"

        # Step 3: If FRU and BRU are swapped, do U swap U' to bring them to front
        if not self._all_in_position(up, down, white_color, yellow_color):
            with self.ann.annotate(
                    (up.corner_bottom_right, AnnWhat.Moved),
                    (up.corner_top_right, AnnWhat.Moved),
                    h2="Swapping corners",
            ):
                self.op.play(Algs.U)
                self.op.play(self._SWAP)
                self.op.play(Algs.U.prime)

        # Step 4: U-align
        assert self._try_u_alignment(up, down, white_color, yellow_color), (
            "L3 Permute failed"
        )

    def _bring_correct_to_flu(self, up: Face, down: Face,
                              white_color: Color, yellow_color: Color) -> None:
        """U-rotate until FLU corner is in its correct position."""
        for _ in range(4):
            if self._corner_in_position(up.corner_bottom_left, down.corner_top_left,
                                        white_color, yellow_color):
                return
            self.op.play(Algs.U)

        raise AssertionError("No corner found in position after 4 U rotations")

    def _is_u_aligned(self, up: Face, down: Face,
                      white_color: Color, yellow_color: Color) -> bool:
        """Check if any U rotation aligns top with bottom. No moves made."""
        with self.op.with_query_restore_state():
            for _ in range(4):
                if self._all_in_position(up, down, white_color, yellow_color):
                    return True
                self.op.play(Algs.U)
        return False

    def _try_u_alignment(self, up: Face, down: Face,
                         white_color: Color, yellow_color: Color) -> bool:
        """Apply U rotations to align top layer with bottom. Returns True if aligned."""

        def _try() -> int:

            n = 0
            with self.op.with_query_restore_state():
                for _ in range(4):
                    if self._all_in_position(up, down, white_color, yellow_color):
                        return n
                    self.op.play(Algs.U)
                    n += 1

                return -1


        # After 4 U rotations we're back to the original state
        n = _try()
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
