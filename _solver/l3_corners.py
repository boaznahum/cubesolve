from typing import Sequence

from _solver.base_solver import SolverElement, ISolver
from _solver.common_op import CommonOp
from _solver.tracker import EdgeTracker, CornerTracker
from algs import Algs, Alg
from cube_face import Face
from elements import FaceName, Part, Edge, Corner


def use(_):
    pass


_status = None


class L3Corners(SolverElement):

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    @property
    def cmn(self) -> CommonOp:
        return self._cmn

    def _is_solved(self):
        return Part.all_match_faces(self.white_face.opposite.corners)

    def solved(self) -> bool:
        """

        :return: true if all edges matches ignoring cross orientation.
        so you must call solve even if this return true
        """

        yf: Face = self.white_face.opposite

        return self.cmn.rotate_and_check(yf, self._is_solved) >= 0

    def solve(self):

        if self._is_solved():
            return # avoid rotating cube


        # we assume we have a cross
        self.cmn.bring_face_up(self.white_face.opposite)

        self._do_corners()

    def _do_corners(self):

        # 'yellow' face
        yf: Face = self.white_face.opposite
        assert yf.name == FaceName.U

        # no need to check rotation, because we assume already have a cross

        if Part.all_match_faces(yf.corners):
            return True

        self._do_positions(yf)
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

        if not yf.corner_bottom_left.in_position:
            self.op.op(self._ur)

        if not yf.corner_bottom_left.in_position:
            self.op.op(self._ur)

        assert Part.all_in_position

    def bring_front_right_to_position(self):

        yf: Face = self.white_face.opposite

        front_right = CornerTracker.of(yf.corner_bottom_right)

        assert not front_right.in_position

        source = front_right.actual

        if yf.corner_top_right is source:
            self.op.op(Algs.Y.prime)
            self.op.op(self._ur.prime)
            self.op.op(Algs.Y)
        elif yf.corner_top_left is source:
            self.op.op(Algs.Y.prime)
            self.op.op(self._ur)
            self.op.op(Algs.Y)
        elif yf.corner_bottom_left is source:
            self.op.op(Algs.Y)
            self.op.op(self._ur)
            self.op.op(Algs.Y.prime)

    @property
    def _ur(self) -> Alg:
        return Algs.alg("L3-UR", Algs.U, Algs.R, Algs.U.prime, Algs.L.prime, Algs.U, Algs.R.prime, Algs.U.prime, Algs.L)

    def bring_corner_to_front_right(self, c: Corner):
        """
        By Y rotation
        :param c:
        :return:
        """
        yf: Face = self.white_face.opposite

        if yf.corner_bottom_right is c:
            return

        if yf.corner_top_right is c:
            return self.op.op(Algs.Y)

        if yf.corner_top_left is c:
            return self.op.op(Algs.Y * 2)

        if yf.corner_bottom_left is c:
            return self.op.op(Algs.Y.prime)

        raise ValueError(f"Corner {c} is not on {yf}")

    def _do_orientation(self, yf: Face):

        for _ in range(0, 4):

            # we can't check all_match because we rotate the cube
            while not yf.corner_bottom_right.match_face(yf):
                self.op.op(Algs.alg("L3-RD", Algs.R.prime, Algs.D.prime, Algs.R, Algs.D)*2)

            self.op.op(Algs.U.prime)



