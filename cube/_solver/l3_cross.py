from cube._solver.base_solver import SolverElement, ISolver
from cube._solver.common_op import CommonOp
from cube._solver.tracker import EdgeTracker
from cube.algs.algs import Algs
from cube.app_exceptions import EvenCubeEdgeParityException
from cube.model.cube_face import Face
from cube.model.elements import FaceName, Part, Edge


def use(_):
    pass


_status = None


class L3Cross(SolverElement):

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)

    @property
    def cmn(self) -> CommonOp:
        return self._cmn

    def _is_solved(self):
        opposite = self.white_face.opposite
        return Part.all_match_faces(opposite.edges)

    def solved(self) -> bool:
        """

        :return: true if all edges matches ignoring cross orientation.
        so you must call solve even if this return true
        """

        yf: Face = self.white_face.opposite

        return self.cmn.rotate_and_check(yf, self._is_solved) >= 0

    def solve(self):

        if self._is_solved():
            return  # avoid rotating cube

        # quick without rotating cube:

        # 'yellow' face
        yf: Face = self.white_face.opposite

        n = self.cmn.rotate_and_check(yf, self._is_solved)
        if n >= 0:
            if n > 0:
                # the query solves by rotate  n, so we need
                self.op.op(self.cmn.face_rotate(yf) * n)
            return

        self.cmn.bring_face_up(self.white_face.opposite)
        # yf is no longer valid - need to track
        wf = self.white_face
        op = wf.opposite
        assert self.white_face.opposite.name == FaceName.U

        self._do_cross()

    def _do_cross(self):

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

        if not n in [0, 2, 4]:
            if self.cube.n_slices % 2 == 0:
                raise EvenCubeEdgeParityException()

        assert n in [0, 2, 4]
        if n == 4:
            return  # done

        if n == 0:
            with self.ann.w_annotate(*zip(yf.edges, [False] * 4)):
                self.op.op(self._fur)  # --> |
                self.op.op(Algs.U)  # --> -
                self.op.op(self._fru)  # --> +
            return

        if n == 2:
            if left and right:  # -
                with self.ann.w_annotate(*zip([yf.edge_top, yf.edge_bottom], [False] * 2)):
                    self.op.op(self._fru)  # --> +

                return
            elif top and bottom:  # |
                with self.ann.w_annotate(*zip([yf.edge_right, yf.edge_left], [False] * 2)):
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

                with self.ann.w_annotate(*zip([yf.edge_bottom, yf.edge_right], [False] * 2)):
                    self.op.op(self._fur)  # op L | --> +
                return

    def _do_cross_position(self):
        """Assume we have yellow cross"""

        yf = self.white_face.opposite

        right = EdgeTracker.of_position(yf.edge_right)

        self.debug(f"L3-Cross-Pos, right before moving:{right}")
        self._bring_edge_to_right_up(right.actual)
        self.debug(f"L3-Cross-Pos, right after moving:{right}")

        assert right.match

        # right is in place
        top = EdgeTracker.of_position(yf.edge_top)

        # now we try to make top and right matches, by fixing top
        if not top.match:
            # where is top ?
            if yf.edge_left is top.actual:
                with self.ann.w_annotate((yf.edge_left, False), (yf.edge_top, False)):
                    # need to swap top and left
                    self.op.op(Algs.U.prime)
                    self.op.op(self._ru)
                    self.op.op(Algs.U)
            else:
                # it is on bottom
                # need to swap bottom and left , then top and left
                with self.ann.w_annotate((yf.edge_left, False), (yf.edge_bottom, False)):
                    self.op.op(self._ru)

                with self.ann.w_annotate((yf.edge_top, False), (yf.edge_right, False)):
                    self.op.op(Algs.U.prime)
                    self.op.op(self._ru)
                    self.op.op(Algs.U)

            assert top.match

        # now bottom and left
        if not yf.edge_left.match_faces:
            # need to swap bottom and left
            with self.ann.w_annotate((yf.edge_bottom, False), (yf.edge_left, False)):
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
