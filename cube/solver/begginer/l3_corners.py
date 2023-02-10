from cube.algs import Algs, Alg
from cube.app_exceptions import InternalSWError, EvenCubeCornerSwapException
from cube.model.cube_face import Face
from cube.model import FaceName, Part, Corner
from cube.operator.op_annotation import AnnWhat
from cube.solver.common.solver_element import SolverElement
from cube.solver.common.common_op import CommonOp
from cube.solver.common.base_solver import BaseSolver
from cube.solver.common.tracker import CornerTracker


def use(_):
    pass


_status = None


class L3Corners(SolverElement):

    def __init__(self, slv: BaseSolver) -> None:
        super().__init__(slv)


    def _is_solved(self):
        return Part.all_match_faces(self.white_face.opposite.corners)

    def solved(self) -> bool:
        """

        :return: true if all edges matches ignoring cross orientation.
        so you must call solve even if this return true
        """

        yf: Face = self.white_face.opposite

        return self.cmn.rotate_face_and_check(yf, self._is_solved) >= 0

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
                        self.op.op(self._ur)

        if not Part.all_in_position(yf.corners):
            if self.cube.n_slices % 2 == 0:
                # Even cube
                n = sum(c.in_position for c in yf.corners)
                if n == 2:
                    self.debug(f"L3 cross-color: Found PLL(Corner swap Parity), doing corner swap")
                    self._do_corner_swap()
                    self.debug(f"L3 cross-color: Found PLL(Corner swap Parity), raising EvenCubeCornerSwapException")
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
                return self.op.op(Algs.Y)

            if yf.corner_top_left is c:
                return self.op.op(Algs.Y * 2)

            if yf.corner_bottom_left is c:
                return self.op.op(Algs.Y.prime)

        raise ValueError(f"Corner {c} is not on {yf}")

    def _do_orientation(self, yf: Face):

        for _ in range(0, 4):

            with self.ann.annotate((yf.corner_bottom_right, AnnWhat.Both)):
                # we can't check all_match because we rotate the cube
                while not yf.corner_bottom_right.match_face(yf):
                    self.op.op(Algs.alg(None, Algs.R.prime, Algs.D.prime, Algs.R, Algs.D) * 2)

            # before U'
            self.op.op(Algs.U.prime)

    def _do_corner_swap(self):

        n_slices = self.cube.n_slices
        assert n_slices % 2 == 0

        # self.op.toggle_animation_on(enable=True)

        self.debug("Doing corner swap")

        nh = n_slices // 2

        # 2-kRw2 U2
        # 2-kRw2  kUw2   // half cube
        # 2-kRw2 kUw2  // half cube

        alg = Algs.alg(None,
                       Algs.R[2:nh + 1] * 2, Algs.U * 2,
                       Algs.R[2:nh + 1] * 2 + Algs.U[1:nh + 1] * 2,
                       Algs.R[2:nh + 1] * 2, Algs.U[1:nh + 1] * 2
                       )

        with self.ann.annotate(h1="Corner swap(PLL Parity)"):
            self.op.op(alg)
