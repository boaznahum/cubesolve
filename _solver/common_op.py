from contextlib import contextmanager
from typing import Callable, Generator

from _solver.icommon_op import ICommon
from _solver.base_solver import ISolver
from algs import Algs, Alg
from app_exceptions import InternalSWError
from cube import Cube
from cube_face import Face
from cube_operator import Operator
from cube_queries import Pred, CubeQueries
from elements import Edge, Color, FaceName, EdgeSlice


TRACE_UNIQUE_ID : int = 0
class EdgeSliceTracker:

    def __init__(self, cube: Cube, pred: Pred[EdgeSlice]) -> None:
        super().__init__()
        self.pred = pred
        self.cube = cube

    @property
    def the_slice(self):
        return CubeQueries.find_slice_in_cube_edges(self.cube, self.pred)


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

        # self.debug(w, " is on ", f)

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
                    self.op.op(Algs.Y + -Algs.X)

                case FaceName.R:
                    self.op.op(Algs.Y + Algs.X)

    def bring_face_front(self, f: Face):

        """
        By Whole cube rotation
        :param f:
        :return:
        """

        if f.name != FaceName.F:

            self.debug("Need to Binging ", f, 'to', FaceName.F)

            match f.name:

                case FaceName.U:
                    self.op.op(Algs.X.prime)

                case FaceName.B:
                    self.op.op(-Algs.X.prime * 2)

                case FaceName.D:
                    self.op.op(Algs.X)

                case FaceName.L:
                    self.op.op(Algs.Y.prime)

                case FaceName.R:
                    self.op.op(Algs.Y)

                case _:
                    raise InternalSWError(f"Unknown face {f}")

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

    def bring_edge_to_front_left_by_whole_rotate(self, edge: Edge):

        """
        Doesn't preserve any other edge
        :param edge:
        :return:
        """
        cube: Cube = self.slv.cube

        if cube.front.edge_left is edge:
            return None  # nothing to do

        max_n = 2

        slice = edge.get_slice(0)

        s_tracker: EdgeSliceTracker
        with self._track_e_slice(slice) as s_tracker:

            for _ in range(max_n):
                slice = s_tracker.the_slice

                edge = slice.parent

                if cube.front.edge_left is edge:
                    return  # nothing to do

                if edge in cube.down.edges:
                    self.op.op(Algs.Z)  # Over F, now on left
                    continue

                elif edge in cube.back.edges:
                    self.op.op(-Algs.Y)  # Over U, now on left

                elif edge in cube.up.edges:
                    self.op.op(-Algs.Z)  # Over F, now on left

                elif edge in cube.right.edges:
                    self.op.op(Algs.Z * 2)  # Over F, now on left

                elif edge in cube.front.edges:
                    self.op.op(Algs.Y )  # Over U, now on left

                else:

                    assert edge in cube.front.edges

                    if edge is cube.left.edge_top:
                        self.op.op(Algs.L)
                    elif edge is cube.left.edge_left:
                        self.op.op(Algs.L * 2)
                    elif edge is cube.left.edge_bottom:
                        self.op.op(-Algs.L)

                    assert s_tracker.the_slice.parent is cube.left.edge_right

                    return

            raise InternalSWError("Too many iteration")






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

    def face_rotate(self, face: Face) -> Alg:

        match face.name:

            case FaceName.U:
                return Algs.U
            case FaceName.F:
                return Algs.F
            case FaceName.R:
                return Algs.R
            case FaceName.L:
                return Algs.L
            case FaceName.D:
                return Algs.D
            case FaceName.B:
                return Algs.B

            case _:
                raise ValueError(f"Unknown face {face.name}")


    @contextmanager
    def _track_e_slice(self, es: EdgeSlice) -> Generator[EdgeSliceTracker, None, None]:

        global TRACE_UNIQUE_ID

        TRACE_UNIQUE_ID += 1

        n = TRACE_UNIQUE_ID

        key = "SliceTracker:" + str(n)

        def _pred(s : EdgeSlice) -> bool:
            return key in s.c_attributes

        tracker: EdgeSliceTracker = EdgeSliceTracker(self.cube, _pred)

        es.c_attributes[key] = key

        try:
            yield tracker
        finally:
            c_att = tracker.the_slice.c_attributes
            del c_att[key]




