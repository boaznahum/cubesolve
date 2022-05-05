from typing import Callable

from _solver.icommon_op import ICommon
from _solver.base_solver import ISolver
from algs import Algs, Alg
from cube import Cube
from cube_operator import Operator
from elements import Edge, Face, Color, FaceName


class CommonOp(ICommon):
    __slots__ = ["_slv", "_start_color"]

    def __init__(self, slv: ISolver) -> None:
        super().__init__()
        self._slv = slv

        self._start_color = Color.WHITE

    @property
    def slv(self) -> ISolver:
        return self._slv

    @property
    def op(self) -> Operator:
        return self._slv.op

    @property
    def cube(self) -> Cube:
        return self._slv.cube

    @property
    def white(self) -> Color:
        """
        when ever we say 'white' we mean color of start color
        """
        return self._start_color

    @property
    def white_face(self) -> Face:
        w: Color = self.white

        f: Face = self.cube.color_2_face(w)

        #self.debug(w, " is on ", f)

        return f

    # noinspection PyMethodMayBeStatic
    def rotate_and_check(self, f: Face, pred: Callable[[], bool]) -> int:
        """
        Rotate face and check condition


        :param f:
        :param pred:
        :return: number of rotation, -1 if check fails
        restore cube state before returning, this is not count as solve step
        """

        n = 0
        try:
            for _ in range(0, 4):
                if pred():
                    return n
                f.rotate()
                n += 1
        finally:
            f.rotate(-n)

        return -1

    def bring_face_up(self, f: Face):

        if f.name != FaceName.U:

            self.debug("Need to Binging ", f, 'to', FaceName.U)

            match f.name:

                case FaceName.F:
                    self.op.op(Algs.X)

                case FaceName.B:
                    self.op.op(-Algs.X)

                case FaceName.D:
                    self.op.op(Algs.X * 2)

                case FaceName.L:
                    self.op.op(Algs.Y + Algs.X)

                case FaceName.R:
                    self.op.op(-Algs.Y + Algs.X)

    def bring_edge_to_front_by_e_rotate(self, edge: Edge) -> Alg | None:
        """
        Assume edge is on E slice
        :param edge:
        :return:
        """
        cube: Cube = self.slv.cube

        if cube.front.edge_right is edge or cube.front.edge_left is edge:
            return None  # nothing to do

        if cube.right.edge_right is edge:
            alg = -Algs.E
            self.slv.op.op(alg)
            return alg

        if cube.left.edge_left is edge:
            alg = Algs.E
            self.slv.op.op(alg)
            return alg

        raise ValueError(f"{edge} is not on E slice")

    def bring_face_to_front_by_y_rotate(self, face):
        """
        rotate over U
        :param face:  must be L , R, F, B
        :return:
        """

        if face.is_front:
            return  # nothing to do

        if face.is_left:
            return self.slv.op.op(-Algs.Y)

        if face.is_right:
            return self.slv.op.op(Algs.Y)

        if face.is_back:
            return self.slv.op.op(Algs.Y * 2)

        raise ValueError(f"{face} must be L/R/F/B")

    def bring_bottom_edge_to_front_by_d_rotate(self, edge):

        d: Face = self.slv.cube.down

        assert d.is_edge(edge)

        other: Face = edge.get_other_face(d)

        if other.is_front:
            return  # nothing to do

        if other.is_left:
            return self.slv.op.op(Algs.D)

        if other.is_right:
            return self.slv.op.op(-Algs.D)

        if other.is_back:
            return self.slv.op.op(Algs.D * 2)

        raise ValueError(f"{other} must be L/R/F/B")

    def debug(self, *args):
        self.slv.debug(args)
