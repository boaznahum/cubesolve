from typing import Sequence

from _solver.base_solver import SolverElement, ISolver
from _solver.common_op import CommonOp
from _solver.tracker import EdgeTracker
from algs import Algs
from elements import Face, FaceName, Part, Edge


def use(_):
    pass


_status = None


class L3Cross(SolverElement):

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    @property
    def cmn(self) -> CommonOp:
        return self._cmn

    def solved(self) -> bool:
        """

        :return: true if all edges matches ignoring cross orientation.
        so you must call solve even if this return true
        """

        yf: Face = self.white_face.opposite

        def pred(): return Part.all_match_faces(yf.edges)

        return self.cmn.rotate_and_check(yf, pred) >= 0

    def solve(self):

        self.cmn.bring_face_up(self.white_face.opposite)

        self._do_cross()

    def _do_cross(self):

        # 'yellow' face
        yf: Face = self.white_face.opposite
        assert yf.name == FaceName.U

        def pred():
            return Part.all_match_faces(yf.edges)

        n = self.cmn.rotate_and_check(yf, pred)
        if n >= 0:
            if n > 0:
                # the query solves by rotate  n, so we need
                self.op.op(Algs.U * n)
            return

        self._do_yellow_cross()
        assert self._is_yellow_cross()
        self._do_cross_position()

    def _is_yellow_cross(self):
        yf: Face = self.white_face.opposite

        left = int(yf.edge_left.match_face(yf))
        right = int(yf.edge_right.match_face(yf))
        top = int(yf.edge_top.match_face(yf))
        bottom = int(yf.edge_bottom.match_face(yf))
        n: int = left + right + top + bottom

        return n == 4

    def _do_yellow_cross(self):
        """ignore position"""

        yf: Face = self.white_face.opposite

        # number of yellow on face
        left = int(yf.edge_left.match_face(yf))
        right = int(yf.edge_right.match_face(yf))
        top = int(yf.edge_top.match_face(yf))
        bottom = int(yf.edge_bottom.match_face(yf))
        n: int = left + right + top + bottom

        self.debug(f"L3 cross-color: {n} match {yf}")

        assert n in [0, 2, 4]
        if n == 4:
            return  # done

        if n == 0:
            self.op.op(self._fur)  # --> |
            self.op.op(Algs.U)  # --> -
            self.op.op(self._fru)  # --> +
            return

        if n == 2:
            if left and right:  # -
                self.op.op(self._fru)  # --> +
                return
            elif top and bottom:  # |
                self.op.op(Algs.U)  # --> -
                self.op.op(self._fru)  # --> +
                return

            else:
                # from here it is L

                if left and top:
                    pass
                elif top and right:
                    self.op.op(Algs.U.prime)  # --> -
                elif right and bottom:
                    self.op.op(Algs.U * 2)  # --> -
                elif bottom and left:
                    self.op.op(Algs.U)  # --> -
                else:
                    ValueError(f"Unrecognized {left=} {top=} {right=} {bottom=} ")

                self.op.op(self._fur)  # --| --> +
                return

    def _do_cross_position(self):
        """Assume we have yellow cross"""

        yf = self.white_face.opposite
        edges: Sequence[EdgeTracker] = EdgeTracker.of_many(self.white_face.opposite.edges)

        right = EdgeTracker.of(yf.edge_right)

        self.debug(f"L3-Cross-Pos, right before moving:{right}")
        self._bring_edge_to_right_up(right.actual)
        self.debug(f"L3-Cross-Pos, right after moving:{right}")

        assert right.match

        # right is in place
        top = EdgeTracker.of(yf.edge_top)

        # now we try to make top and right matches, by fixing top
        if not top.match:
            # where is top ?
            if yf.edge_left is top.actual:
                # need to swap top and left
                self.op.op(Algs.U.prime)
                self.op.op(self._ru)
                self.op.op(Algs.U)
            else:
                # it is on bottom
                # need to swap bottom and left , then top and left
                self.op.op(self._ru)

                self.op.op(Algs.U.prime)
                self.op.op(self._ru)
                self.op.op(Algs.U)

            assert top.match

        # now bottom and left
        if not yf.edge_left.match_faces:
            # need to swap bottom and left
            self.op.op(self._ru)
            assert yf.edge_left.match_faces

        assert yf.edge_bottom.match_faces

    @property
    def _fur(self):
        return Algs.alg("L3-FUR", Algs.F, Algs.U, Algs.R, Algs.U.prime, Algs.R.prime, Algs.F.prime)

    @property
    def _fru(self):
        return Algs.alg("L3-FRU", Algs.F, Algs.R, Algs.U, Algs.R.prime, Algs.U.prime, Algs.F.prime)

    @property
    def _ru(self):
        return Algs.alg("L3-RU", Algs.R, Algs.U, Algs.R.prime, Algs.U, Algs.R, Algs.U * 2, Algs.R.prime, Algs.U)

    def _bring_edge_to_right_up(self, e: Edge):
        """
        U Movement, edge must be on up
        :param  e:
        :return:
        """

        up: Face = self.cube.up

        if up.edge_bottom is e:
            return self.op.op(Algs.U.prime)

        if up.edge_left is e:
            return self.op.op(Algs.U * 2)

        if up.edge_right is e:
            return

        if up.edge_top is e:
            return self.op.op(Algs.U)

        raise ValueError(f"Edge {e} is not on {up}")
