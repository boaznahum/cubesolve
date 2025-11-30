from cube.algs import Algs
from cube.app.app_exceptions import EvenCubeEdgeParityException
from cube.model import FaceName, Part, Edge
from cube.model.Face import Face
from cube.operator.op_annotation import AnnWhat
from cube.solver.common.BaseSolver import BaseSolver
from cube.solver.common.SolverElement import SolverElement
from cube.solver.common.Tracker import EdgeTracker


def use(_):
    pass


_status = None


class L3Cross(SolverElement):

    def __init__(self, slv: BaseSolver) -> None:
        super().__init__(slv)

    def _is_solved(self):
        opposite = self.white_face.opposite
        return Part.all_match_faces(opposite.edges)

    def solved(self) -> bool:
        """

        :return: true if all edges matches ignoring cross orientation.
        so you must call solve even if this return true
        """

        yf: Face = self.white_face.opposite

        return self.cqr.rotate_face_and_check(yf, self._is_solved) >= 0

    def solve(self):

        if self._is_solved():
            return  # avoid rotating cube

        # quick without rotating cube:

        with self.ann.annotate(h1="Doing L3 Cross"):
            self._solve()

    def _solve(self) -> None:
        # 'yellow' face
        yf: Face = self.white_face.opposite

        n = self.cqr.rotate_face_and_check(yf, self._is_solved)
        if n >= 0:
            if n > 0:
                # the query solves by rotate  n, so we need
                self.op.play(self.cmn.face_rotate(yf) * n)
            return

        self.cmn.bring_face_up(self.white_face.opposite)
        # yf is no longer valid - need to track
        assert self.white_face.opposite.name == FaceName.U

        self._do_cross()

    def _do_cross(self) -> None:

        self._do_yellow_cross()
        assert self._is_yellow_cross()
        self._do_cross_position()

    def _is_yellow_cross(self) -> bool:
        yf: Face = self.white_face.opposite

        left = int(yf.edge_left.match_face(yf))
        right = int(yf.edge_right.match_face(yf))
        top = int(yf.edge_top.match_face(yf))
        bottom = int(yf.edge_bottom.match_face(yf))
        n: int = left + right + top + bottom

        return n == 4

    def _do_yellow_cross(self) -> None:
        """ignore position"""

        yf: Face = self.white_face.opposite

        # number of yellow on face
        left = int(yf.edge_left.match_face(yf))
        right = int(yf.edge_right.match_face(yf))
        top = int(yf.edge_top.match_face(yf))
        bottom = int(yf.edge_bottom.match_face(yf))
        n: int = left + right + top + bottom

        self.debug(f"L3 cross-color: {n} match {yf}")

        if n not in [0, 2, 4]:
            if self.cube.n_slices % 2 == 0:
                self.debug(f"L3 cross-color: Found OLL(Edge Parity), raising EvenCubeEdgeParityException")
                raise EvenCubeEdgeParityException()

        assert n in [0, 2, 4]
        if n == 4:
            return  # done

        if n == 0:
            with self.ann.annotate((yf.edges, AnnWhat.Moved)):
                self.op.play(self._fur)  # --> |
                self.op.play(Algs.U)  # --> -
                self.op.play(self._fru)  # --> +
            return

        if n == 2:
            if left and right:  # -
                with self.ann.annotate(([yf.edge_top, yf.edge_bottom], AnnWhat.Moved)):
                    self.op.play(self._fru)  # --> +

                return
            elif top and bottom:  # |
                with self.ann.annotate(([yf.edge_right, yf.edge_left], AnnWhat.Moved)):
                    self.op.play(Algs.U)  # --> -
                    self.op.play(self._fru)  # --> +
                return

            else:
                # from here it is L

                if left and top:
                    pass
                elif top and right:
                    self.op.play(Algs.U.prime)  # --> -
                elif right and bottom:
                    self.op.play(Algs.U * 2)  # --> -
                elif bottom and left:
                    self.op.play(Algs.U)  # --> -
                else:
                    ValueError(f"Unrecognized {left=} {top=} {right=} {bottom=} ")

                with self.ann.annotate(([yf.edge_bottom, yf.edge_right], AnnWhat.Moved)):
                    self.op.play(self._fur)  # op L | --> +
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
                with self.ann.annotate(([yf.edge_left, yf.edge_top], AnnWhat.Moved)):
                    # need to swap top and left
                    self.op.play(Algs.U.prime)
                    self.op.play(self._ru)
                    self.op.play(Algs.U)
            else:
                # it is on bottom
                # need to swap bottom and left , then top and left
                with self.ann.annotate(([yf.edge_left, yf.edge_bottom], AnnWhat.Moved)):
                    self.op.play(self._ru)

                with self.ann.annotate(([yf.edge_top, yf.edge_right], AnnWhat.Moved)):
                    self.op.play(Algs.U.prime)
                    self.op.play(self._ru)
                    self.op.play(Algs.U)

            assert top.match

        # now bottom and left
        if not yf.edge_left.match_faces:
            # need to swap bottom and left
            with self.ann.annotate(([yf.edge_bottom, yf.edge_left], AnnWhat.Moved)):
                self.op.play(self._ru)

            assert yf.edge_left.match_faces

        assert yf.edge_bottom.match_faces

    @property
    def _fur(self):
        return Algs.alg(None, Algs.F, Algs.U, Algs.R, Algs.U.prime, Algs.R.prime, Algs.F.prime)

    @property
    def _fru(self):
        return Algs.alg(None, Algs.F, Algs.R, Algs.U, Algs.R.prime, Algs.U.prime, Algs.F.prime)

    @property
    def _ru(self):
        return Algs.alg(None, Algs.R, Algs.U, Algs.R.prime, Algs.U, Algs.R, Algs.U * 2, Algs.R.prime, Algs.U)

    def _bring_edge_to_right_up(self, e: Edge):
        """
        U Movement, edge must be on up
        :param  e:
        :return:
        """

        up: Face = self.cube.up

        if up.edge_bottom is e:
            return self.op.play(Algs.U.prime)

        if up.edge_left is e:
            return self.op.play(Algs.U * 2)

        if up.edge_right is e:
            return

        if up.edge_top is e:
            return self.op.play(Algs.U)

        raise ValueError(f"Edge {e} is not on {up}")
