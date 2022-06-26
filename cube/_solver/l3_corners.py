from cube._solver.base_solver import SolverElement, ISolver, AnnWhat
from cube._solver.common_op import CommonOp
from cube._solver.tracker import CornerTracker
from cube.algs.algs import Algs, Alg
from cube.app_exceptions import InternalSWError, EvenCubeCornerSwapException
from cube.model.cube_face import Face
from cube.model.elements import FaceName, Part, Corner


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
            return  # avoid rotating cube

        # we assume we have a cross
        self.cmn.bring_face_up(self.white_face.opposite)

        self._do_corners()

        assert self._is_solved()

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

        # at most two cycles
        if not yf.corner_bottom_left.in_position:
            with self.ann.w_annotate2(
                    (yf.corner_top_right, AnnWhat.FindLocationTrackByColor),
                    (yf.corner_top_left, AnnWhat.FindLocationTrackByColor),
                    (yf.corner_bottom_left, AnnWhat.FindLocationTrackByColor),
            ):

                for _ in [1, 1]:
                    if not yf.corner_bottom_left.in_position:
                        self.op.op(self._ur)

        if not Part.all_in_position(yf.corners):
            if self.cube.n_slices % 2 == 0:
                # Even cube
                n = sum(c.in_position for c in yf.corners)
                if n == 2:
                    self._do_corner_swap()
                    raise EvenCubeCornerSwapException()

                raise InternalSWError("Cube not all corners in position, don't know why")
            else:
                raise InternalSWError("Odd cube not all corners in position")

    def bring_front_right_to_position(self):

        yf: Face = self.white_face.opposite

        with self.ann.w_annotate2((yf.corner_bottom_right, AnnWhat.FindLocationTrackByColor),
                              (yf.corner_bottom_right, AnnWhat.Position)):

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

        with self.ann.w_annotate((c, False), (yf.corner_top_right, True)):

            if yf.corner_top_right is c:
                return self.op.op(Algs.Y)

            if yf.corner_top_left is c:
                return self.op.op(Algs.Y * 2)

            if yf.corner_bottom_left is c:
                return self.op.op(Algs.Y.prime)

        raise ValueError(f"Corner {c} is not on {yf}")

    def _do_orientation(self, yf: Face):

        for _ in range(0, 4):

            with self.ann.w_annotate((yf.corner_bottom_right, False), (yf.corner_bottom_right, True)):
                # we can't check all_match because we rotate the cube
                while not yf.corner_bottom_right.match_face(yf):
                    self.op.op(Algs.alg("L3-RD", Algs.R.prime, Algs.D.prime, Algs.R, Algs.D) * 2)

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

        alg = Algs.alg("c-swap",
                       Algs.R[2:nh + 1] * 2, Algs.U * 2,
                       Algs.R[2:nh + 1] * 2, Algs.U[1:nh + 1] * 2,
                       Algs.R[2:nh + 1] * 2, Algs.U[1:nh + 1] * 2)

        self.op.op(alg)
