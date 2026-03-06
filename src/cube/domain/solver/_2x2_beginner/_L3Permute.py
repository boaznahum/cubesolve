"""Layer 3 permutation solver for 2x2 beginner method.

Permutes the 4 top-layer corners into their correct positions.
At this point all corners are already oriented (yellow on top).
This is the 2x2 equivalent of PLL (Permutation of Last Layer).

IMPORTANT — No face colors:
    Like all 2x2 solvers, this works entirely with corner sticker colors.
    Never accesses Face.color, self.white_face, match_faces, in_position,
    or any API that reads face colors from centers.

Strategy (bar + adjacent swap):
1. Find a "bar" — two adjacent UP corners that show the same color
   on their shared side face.
2. Position the bar at the BACK using Y rotations.
3. Apply the swap algorithm: R' F R' B2 R F' R' B2 R2 U'
4. If no bar found, apply swap once from any angle — a bar will appear.
5. At most 2 applications needed.

The swap algorithm preserves corner orientation (yellow stays on UP).
"""

from __future__ import annotations

from cube.domain.algs import Algs, Alg
from cube.domain.model import Color
from cube.domain.model.Face import Face
from cube.domain.solver._2x2_beginner._l3_utils import find_yellow_color, find_white_face, bring_white_to_down
from cube.domain.solver.common.SolverHelper import StepSolver
from cube.domain.solver.protocols import SolverElementsProvider


class L3Permute(StepSolver):
    """Last layer corner permutation solver for 2x2.

    Works purely with corner sticker colors — no face colors.
    """

    __slots__: list[str] = []

    # R' F R' B2 R F' R' B2 R2 U' — adjacent corner swap, preserves orientation
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

        Solved means every side face has all 4 corners showing the same color.
        Equivalently: each top corner's non-yellow side colors match the
        bottom corner directly below it.
        """
        white_color: Color = self.cmn.white
        yellow_color: Color = find_yellow_color(self.cube, white_color)

        white_face: Face | None = find_white_face(self.cube, white_color)
        if white_face is None:
            return False

        yellow_face: Face = white_face.opposite

        return self._all_in_position(yellow_face, white_face, white_color, yellow_color)

    def solve(self) -> None:
        """Permute last-layer corners into correct positions."""
        if self.is_solved:
            return

        with self.ann.annotate(h1="Doing L3 Permute"):
            self._solve()

    def _solve(self) -> None:
        white_color: Color = self.cmn.white
        yellow_color: Color = find_yellow_color(self.cube, white_color)

        bring_white_to_down(self, white_color)

        up: Face = self.cube.up
        down: Face = self.cube.down
        self._do_permute(up, down, white_color, yellow_color)

    def _do_permute(self, up: Face, down: Face, white_color: Color, yellow_color: Color) -> None:
        """Position bar at back and apply swap. At most 2 iterations."""

        for _ in range(3):
            if self._try_u_alignment(up, down, white_color, yellow_color):
                return

            # Find a bar (two adjacent UP corners with same color on shared side face)
            bar_face: Face | None = self._find_bar(up)

            if bar_face is not None:
                # Position the bar at the BACK
                self._bring_bar_to_back(bar_face)

            # Apply swap
            self.op.play(self._SWAP)

        assert self._try_u_alignment(up, down, white_color, yellow_color), (
            "L3 Permute failed after 3 swap applications"
        )

    def _try_u_alignment(self, up: Face, down: Face, white_color: Color, yellow_color: Color) -> bool:
        """Try U, U2, U3 rotations to align top layer with bottom. Return True if aligned."""
        for _ in range(4):
            if self._all_in_position(up, down, white_color, yellow_color):
                return True
            self.op.play(Algs.U)
        # After 4 U rotations we're back to the original state
        return False

    def _find_bar(self, up: Face) -> Face | None:
        """Find a side face where both UP corners show the same color.

        Returns the side face, or None if no bar exists.
        """
        cube = self.cube
        # Check each side face: the two UP corners on that face should match
        side_faces = [cube.front, cube.right, cube.back, cube.left]

        for sf in side_faces:
            # Get the two UP corners that touch this side face
            corners_on_sf = [c for c in up.corners if c.on_face(sf)]
            assert len(corners_on_sf) == 2
            c1, c2 = corners_on_sf
            if c1.face_color(sf) == c2.face_color(sf):
                return sf

        return None

    def _bring_bar_to_back(self, bar_face: Face) -> None:
        """Rotate the whole cube so the bar face is at the BACK."""
        cube = self.cube
        if bar_face is cube.back:
            return
        elif bar_face is cube.right:
            self.op.play(Algs.Y)
        elif bar_face is cube.front:
            self.op.play(Algs.Y * 2)
        elif bar_face is cube.left:
            self.op.play(Algs.Y.prime)

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
            (tc.colors_id - {yellow_color}) == (bc.colors_id - {white_color})
            for tc, bc in pairs
        )
