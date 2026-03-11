from cube.domain.algs import Alg, Algs
from cube.domain.exceptions import EvenCubeCornerSwapException, InternalSWError
from cube.domain.model import Corner, FaceName, Part
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.tracker.Tracker import CornerTracker
from cube.domain.solver.protocols import SolverElementsProvider


class L3Corners(SolverHelper):

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "L3Corners")


    def _is_solved(self):
        return Part.all_match_faces(self.white_face.opposite.corners)

    def solved(self) -> bool:
        """

        :return: true if all edges matches ignoring cross orientation.
        so you must call solve even if this return true
        """

        yf: Face = self.white_face.opposite

        return self.cqr.rotate_face_and_check(yf, self._is_solved, self.op) >= 0

    def solve(self):

        if self._is_solved():
            return  # avoid rotating cube

        with self.ann.annotate(h1="Doing L3 Corners"):
            self._solve()

    def _solve(self):

        # we assume we have a cross
        self.cmn.bring_face_up(self.white_face.opposite)

        self._do_corners()

        assert self._is_solved()

    def _do_corners(self) -> None:

        # 'yellow' face
        yf: Face = self.white_face.opposite
        assert yf.name == FaceName.U

        # no need to check rotation, because we assume already have a cross

        if Part.all_match_faces(yf.corners):
            return

        with self.ann.annotate(h1="+- Position"):
            self._do_positions(yf)

        with self.ann.annotate(h1="+- Orientation"):
            self._do_orientation(yf)

    def _do_positions(self, yf: Face):

        # find a least on that is in position
        in_position: Corner | None = None
        for c in yf.corners:
            if c.in_position:
                in_position = c
                self.bring_corner_to_front_right(in_position)
                break

        if not in_position:
            # bring front-right to position
            self.bring_front_right_to_position()

        assert yf.corner_bottom_right.in_position

        # at most two cycles
        if not yf.corner_bottom_left.in_position:
            with self.ann.annotate(
                    (yf.corner_top_right, AnnWhat.Moved),
                    (yf.corner_top_left, AnnWhat.Moved),
                    (yf.corner_bottom_left, AnnWhat.Moved),
            ):

                for _ in [1, 1]:
                    if not yf.corner_bottom_left.in_position:
                        self.op.play(self._ur)

        if not Part.all_in_position(yf.corners):
            if self.cube.n_slices % 2 == 0 or self.cube.is_even_cube_shadow:
                # Even cube
                n = sum(c.in_position for c in yf.corners)
                if n == 2:
                    # Corner swap parity detected on even cube
                    # Raise exception - orchestrator will call reducer.fix_corner_parity()
                    # This matches the edge parity pattern: detect -> throw -> catch -> fix
                    self.debug("L3 corners: PLL parity detected (2 corners in position)")
                    raise EvenCubeCornerSwapException()

                raise InternalSWError("Cube not all corners in position, don't know why")
            else:
                raise InternalSWError("Odd cube not all corners in position")

    def bring_front_right_to_position(self)  -> None:

        yf: Face = self.white_face.opposite

        with self.ann.annotate((yf.corner_bottom_right, AnnWhat.Both)):

            front_right = CornerTracker.of_position(yf.corner_bottom_right)

            assert not front_right.in_position

            source = front_right.actual

            if yf.corner_top_right is source:
                self.op.play(Algs.Y.prime)
                self.op.play(self._ur.prime)
                self.op.play(Algs.Y)
            elif yf.corner_top_left is source:
                self.op.play(Algs.Y.prime)
                self.op.play(self._ur)
                self.op.play(Algs.Y)
            elif yf.corner_bottom_left is source:
                self.op.play(Algs.Y)
                self.op.play(self._ur)
                self.op.play(Algs.Y.prime)

    @property
    def _ur(self) -> Alg:
        return Algs.alg(None, Algs.U, Algs.R, Algs.U.prime, Algs.L.prime, Algs.U, Algs.R.prime, Algs.U.prime, Algs.L)

    def bring_corner_to_front_right(self, c: Corner):
        """
        By Y rotation
        :param c:
        :return:
        """
        yf: Face = self.white_face.opposite

        if yf.corner_bottom_right is c:
            return

        with self.ann.annotate((c, AnnWhat.Moved), (yf.corner_top_right, AnnWhat.FixedPosition)):

            if yf.corner_top_right is c:
                return self.op.play(Algs.Y)

            if yf.corner_top_left is c:
                return self.op.play(Algs.Y * 2)

            if yf.corner_bottom_left is c:
                return self.op.play(Algs.Y.prime)

        raise ValueError(f"Corner {c} is not on {yf}")

    def _do_orientation(self, yf: Face) -> None:
        """Orient all last-layer corners so yellow faces up.

        Searches CCW for unoriented corners, skipping already-oriented ones.
        Computes exact twist count (1 or 2) instead of iterating.
        """

        twist: Alg = Algs.alg(None, Algs.R.prime, Algs.D.prime, Algs.R, Algs.D) * 2

        total_u: int = 0

        for _ in range(4):
            n: int = self._find_next_unoriented_ccw(yf)
            if n < 0:
                break  # all oriented

            if n > 0:
                self.op.play((Algs.U.prime * n).simplify())
                total_u += n

            twist_n: int = self._twist_count(yf, self.cube.front, self.cube.right)
            assert twist_n > 0
            with self.ann.annotate((yf.corner_bottom_right, AnnWhat.Both)):
                self.op.play((twist * twist_n).simplify())

        # Realign U layer
        remaining: int = (4 - total_u % 4) % 4
        if remaining > 0:
            self.op.play((Algs.U.prime * remaining).simplify())

    @staticmethod
    def _find_next_unoriented_ccw(yf: Face) -> int:
        """Find the next unoriented corner searching CCW from FRU.

        Returns 0-3 (number of U' rotations to bring it to FRU) or -1 if all oriented.
        CCW order: FRU(0), FLU(1), BLU(2), BRU(3).
        """
        corners: list[Corner] = [
            yf.corner_bottom_right,  # FRU
            yf.corner_bottom_left,   # FLU
            yf.corner_top_left,      # BLU
            yf.corner_top_right,     # BRU
        ]
        for i, corner in enumerate(corners):
            if not corner.match_face(yf):
                return i
        return -1

    @staticmethod
    def _twist_count(yf: Face, cube_front: Face, cube_right: Face) -> int:
        """Compute how many (R' D' R D)*2 twists FRU needs so yellow faces up.

        The twist rotates the FRU corner 120 degrees clockwise (viewed from corner).
        - Yellow on UP    -> 0 (already oriented)
        - Yellow on Right -> 1 twist
        - Yellow on Front -> 2 twists
        """
        fru: Corner = yf.corner_bottom_right
        yellow = yf.color
        if fru.face_color(yf) == yellow:
            return 0
        if fru.face_color(cube_right) == yellow:
            return 1
        assert fru.face_color(cube_front) == yellow
        return 2
