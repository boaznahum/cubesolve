from contextlib import contextmanager
from typing import Callable, Generator

from cube._solver.icommon_op import ICommon
from cube._solver.base_solver import ISolver, SolverElement
from cube.algs.algs import Algs, Alg
from cube.app_exceptions import InternalSWError
from cube.model.cube import Cube
from cube.model.cube_face import Face
from cube.operator.cube_operator import Operator
from cube.model.cube_queries import Pred, CubeQueries
from cube.model.elements import Edge, Color, FaceName, EdgeSlice

TRACE_UNIQUE_ID: int = 0


class EdgeSliceTracker:

    def __init__(self, cube: Cube, pred: Pred[EdgeSlice]) -> None:
        super().__init__()
        self.pred = pred
        self.cube = cube

    @property
    def the_slice(self):
        return CubeQueries.find_slice_in_cube_edges(self.cube, self.pred)


class CommonOp(ICommon, SolverElement):
    __slots__ = ["_slv", "_start_color"]

    def __init__(self, slv: ISolver) -> None:
        super().__init__(slv)
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

            self.debug("Need to bring ", f, 'to', FaceName.U)

            with self.ann.w_annotate(h2=f"Bringing face {f.name.value} up"):

                alg: Alg

                match f.name:

                    case FaceName.F:
                        alg = Algs.X

                    case FaceName.B:
                        alg = -Algs.X

                    case FaceName.D:
                        alg = Algs.X * 2

                    case FaceName.L:
                        alg = Algs.Y + -Algs.X

                    case FaceName.R:
                        alg = Algs.Y + Algs.X

                    case _:
                        raise InternalSWError(f"Unknown face {f}")

                with self.ann.w_annotate(h3=f"{alg}"):
                    self.op.op(alg)

    def bring_face_front(self, f: Face):

        """
        By Whole cube rotation
        :param f:
        :return:
        """

        if f.name != FaceName.F:

            self.debug("Need to bring ", f, 'to', FaceName.F)

            with self.ann.w_annotate(h2=f"Bringing face {f.name.value} to front"):

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

    def bring_edge_to_front_left_by_whole_rotate(self, edge: Edge) -> Edge:

        """
        Doesn't preserve any other edge
        :param edge:
        :return:
        """

        begin_edge = edge

        cube: Cube = self.slv.cube

        if cube.front.edge_left is edge:
            return edge  # nothing to do

        max_n = 2

        _slice = edge.get_slice(0)

        s_tracker: EdgeSliceTracker
        with self.track_e_slice(_slice) as s_tracker:

            for _ in range(max_n):
                _slice = s_tracker.the_slice

                edge = _slice.parent

                if edge not in cube.front.edges:

                    # if cube.front.edge_left is edge:
                    #     return  # nothing to do

                    if edge in cube.down.edges:
                        self.op.op(Algs.X)  # Over R, now on front
                        continue

                    elif edge in cube.back.edges:
                        self.op.op(-Algs.X * 2)  # Over R, now on front

                    elif edge in cube.up.edges:
                        self.op.op(-Algs.X)  # Over R, now on front

                    elif edge in cube.right.edges:
                        self.op.op(Algs.Y * 2)  # Over U, now on front

                    elif edge in cube.left.edges:
                        self.op.op(-Algs.Y)  # Over U, now on  front

                    else:
                        raise InternalSWError(f"Unknown case {edge}")

                else:

                    if cube.front.edge_left is edge:
                        return s_tracker.the_slice.parent  # nothing to do

                    if edge is cube.front.edge_top:
                        self.op.op(Algs.Z.prime)
                    elif edge is cube.front.edge_right:
                        self.op.op(Algs.Z * 2)
                    elif edge is cube.front.edge_bottom:
                        self.op.op(Algs.Z)

                    now_edge = s_tracker.the_slice.parent

                    if s_tracker.the_slice.parent is not cube.left.edge_right:
                        raise InternalSWError(f"Internal error {begin_edge} {now_edge}")

                    return s_tracker.the_slice.parent

            now_edge = s_tracker.the_slice.parent

            raise InternalSWError(f"Too many iteration {begin_edge} {now_edge}")

    def bring_edge_to_front_right_preserve_front_left(self, edge: Edge):
        cube: Cube = self.slv.cube

        if cube.front.edge_right is edge:
            return None  # nothing to do

        if cube.front.edge_left is edge:
            raise InternalSWError("Can be of front left")

        max_n = 3

        s_tracker: EdgeSliceTracker
        with self.track_e_slice(edge.get_slice(0)) as s_tracker:

            for _ in range(max_n):
                _slice = s_tracker.the_slice

                edge = _slice.parent

                if cube.front.edge_right is edge:
                    return  # done

                # ---------------------- on back --------------------
                if edge is cube.back.edge_top:
                    self.op.op(Algs.B.prime)  # now on right
                    continue

                elif edge is cube.back.edge_right:
                    self.op.op(Algs.B.prime * 2)  # now on right

                elif edge is cube.back.edge_bottom:
                    self.op.op(Algs.B)  # now on right

                # back left is right

                # ---------------------- on top --------------------

                # up top and up right are on back/right - no need to handle

                elif edge is cube.up.edge_left:
                    self.op.op(Algs.U.prime * 2)  # now on right top

                elif edge is cube.up.edge_bottom:
                    self.op.op(Algs.U.prime)  # now on right top

                # ---------------------- front --------------------
                elif edge is cube.front.edge_bottom:
                    self.op.op(Algs.D)  # now on right bottom

                elif edge is cube.left.edge_bottom:
                    self.op.op(Algs.D.prime * 2)  # now on right bottom

                # now handle on right

                elif edge is cube.right.edge_bottom:
                    self.op.op(Algs.R)  # now on front right

                elif edge is cube.right.edge_right:
                    self.op.op(Algs.R * 2)  # Over F, now on left

                elif edge is cube.right.edge_top:
                    self.op.op(Algs.R.prime)  # Over F, now on left

                else:

                    raise InternalSWError(f"Unknown case, edge is {edge}")

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

    @staticmethod
    def face_rotate(face: Face) -> Alg:

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
    def track_e_slice(self, es: EdgeSlice) -> Generator[EdgeSliceTracker, None, None]:

        global TRACE_UNIQUE_ID

        TRACE_UNIQUE_ID += 1

        n = TRACE_UNIQUE_ID

        key = "SliceTracker:" + str(n)

        def _pred(s: EdgeSlice) -> bool:
            return key in s.c_attributes

        tracker: EdgeSliceTracker = EdgeSliceTracker(self.cube, _pred)

        es.c_attributes[key] = key

        try:
            yield tracker
        finally:
            c_att = tracker.the_slice.c_attributes
            del c_att[key]
