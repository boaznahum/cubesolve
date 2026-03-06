"""Layer 3 orientation solver for 2x2 beginner method.

Orients all 4 top-layer corners so that the yellow sticker faces up.
This is the 2x2 equivalent of OLL (Orientation of Last Layer).

IMPORTANT — No face colors:
    Like all 2x2 solvers, this works entirely with corner sticker colors.
    Never accesses Face.color, self.white_face, match_faces, in_position,
    or any API that reads face colors from centers.

Strategy (R' D' R D twist):
1. After L1 is solved, find which face has white corners and bring to DOWN
2. Find yellow_color (the color opposite to white — never shares a corner)
3. For each of the 4 UP corners (cycling with U'):
   - Apply (R' D' R D) * 2 until the FRU corner has yellow facing up
   - Rotate U' to bring the next corner to FRU
4. This temporarily scrambles the bottom layer but restores it after all 4
"""

from __future__ import annotations

from cube.domain.algs import Algs, Alg
from cube.domain.model import Color, Corner
from cube.domain.model.Face import Face
from cube.domain.solver._2x2_beginner._l3_utils import find_yellow_color, find_white_face, bring_white_to_down
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.SolverHelper import StepSolver
from cube.domain.solver.protocols import SolverElementsProvider


class L3Orient(StepSolver):
    """Last layer corner orientation solver for 2x2.

    Works purely with corner sticker colors — no face colors.
    """

    __slots__: list[str] = []

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "L3Orient")

    @property
    def is_solved(self) -> bool:
        """Check if all 4 top-layer corners have yellow facing up."""
        white_color: Color = self.cmn.white
        yellow_color: Color = find_yellow_color(self.cube, white_color)

        white_face: Face | None = find_white_face(self.cube, white_color)
        if white_face is None:
            return False

        yellow_face: Face = white_face.opposite
        return self._all_oriented(yellow_face, yellow_color)

    def solve(self) -> None:
        """Orient all last-layer corners (yellow face up)."""
        if self.is_solved:
            return

        with self._logger.tab("Doing L3 Orient"):
            with self.ann.annotate(h1="Doing L3 Orient"):
                self._solve()

    def _solve(self) -> None:
        white_color: Color = self.cmn.white
        yellow_color: Color = find_yellow_color(self.cube, white_color)

        bring_white_to_down(self, white_color)

        up: Face = self.cube.up
        self._do_orient(up, yellow_color)

    def _do_orient(self, up: Face, yellow_color: Color) -> None:
        """Twist each corner at FRU until yellow faces up, then rotate U'."""

        # (R' D' R D) * 2 — twists the FRU corner 120° in place
        twist: Alg = Algs.alg(
            None, Algs.R.prime, Algs.D.prime, Algs.R, Algs.D,
        ) * 2

        for _ in range(4):
            n: int = self._twist_count(up, yellow_color, self.cube.front, self.cube.right, self.cube.fru)

            if n > 0:
                with self.ann.annotate((up.corner_bottom_right, AnnWhat.Both)):
                    self.op.play((twist * n).simplify())

            assert self.cube.fru.face_color(up) == yellow_color

            # Rotate to bring next corner to FRU
            self.op.play(Algs.U.prime)

        assert self._all_oriented(up, yellow_color), "L3 Orient failed"

    @staticmethod
    def _twist_count(up: Face, yellow_color: Color, cube_front: Face, cube_right: Face,
                     fru: Corner) -> int:
        """Compute how many (R' D' R D)*2 twists FRU needs so yellow faces up.

        The twist rotates the FRU corner 120° clockwise (viewed from corner).
        - Yellow on UP    → 0
        - Yellow on Right → 1  (one 120° twist brings it to UP)
        - Yellow on Front → 2  (two 120° twists bring it to UP)
        """
        if fru.face_color(up) == yellow_color:
            return 0
        if fru.face_color(cube_right) == yellow_color:
            return 1
        assert fru.face_color(cube_front) == yellow_color
        return 2

    def _all_oriented(self, up: Face, yellow_color: Color) -> bool:
        """Check if all 4 corners on UP have yellow facing up."""
        return all(
            c.face_color(up) == yellow_color
            for c in up.corners
        )
