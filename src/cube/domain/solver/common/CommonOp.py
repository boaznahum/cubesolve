import warnings
from contextlib import contextmanager
from typing import Callable, ContextManager, Generator, Sequence, Tuple

from typing_extensions import deprecated

from cube.domain.algs import Alg, Algs
from cube.domain.exceptions import InternalSWError
from cube.domain.model import Color, Edge, EdgeWing, FaceName
from cube.domain.model.Cube import Cube
from cube.domain.model.Face import Face
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.protocols import (
    AnnotationProtocol,
    OperatorProtocol,
    SolverElementsProvider,
    SupportsAnnotation,
)

from ...model.CubeQueries2 import Pred, Pred0

TRACE_UNIQUE_ID: int = 0


class EdgeSliceTracker:

    def __init__(self, cube: Cube, pred: Pred[EdgeWing]) -> None:
        super().__init__()
        self.pred = pred
        self.cube = cube

    @property
    def the_slice(self) -> EdgeWing | None:
        return self.cube.cqr.find_slice_in_cube_edges(self.pred)

    @property
    def the_slice_nl(self) -> EdgeWing:
        s = self.cube.cqr.find_slice_in_cube_edges(self.pred)
        assert s is not None
        return s


class CommonOp:
    __slots__ = ["_slv",
                 "_start_color",
                 "_ann"]

    def __init__(self, provider: SolverElementsProvider) -> None:
        super().__init__()
        self._slv = provider
        self._ann = provider.op.annotation

        # Get first face color from config (default: WHITE)
        self._start_color = provider.op.app_state.config.first_face_color

    @property
    def slv(self) -> SolverElementsProvider:
        return self._slv

    @property
    def op(self) -> OperatorProtocol:
        return self._slv.op

    @property
    def cube(self) -> Cube:
        return self._slv.cube

    @property
    def ann(self) -> AnnotationProtocol:
        return self._ann

    def annotate(self, *elements: Tuple[SupportsAnnotation, AnnWhat],
                 h1: str | Callable[[], str] | None = None,
                 h2: str | Callable[[], str] | None = None,
                 h3: str | Callable[[], str] | None = None,
                 animation: bool = True) -> ContextManager[None]:
        return self.ann.annotate(*elements, h1=h1, h2=h2, h3=h3, animation=animation)

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

    def l2_edges(self) -> Sequence[Edge]:

        edges: list[Edge] = []

        wf: Face = self.white_face
        d: Face = wf.opposite

        for f in self.white_face.adjusted_faces():
            for e in f.edges:
                # all edges that do not touch up and down faces
                if not e.on_face(wf) and not e.on_face(d):
                    if e not in edges:  # by id ?
                        edges.append(e)
                        if len(edges) == 4:  # optimize
                            return edges

        return edges

    # noinspection PyMethodMayBeStatic
    @deprecated("Use CubeQueries2 instead")
    def rotate_and_check(self, alg: Alg, pred: Callable[[], bool]) -> int:
        """
        Rotate face and check condition


        :param alg:
        :param pred:
        :return: number of rotation, -1 if check fails
        restore cube state before returning, this is not count as solve step
        """

        #new todo use cube.application.commands.Operator.Operator.with_query_restore_state

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        n = 0
        cube = self.cube
        try:
            for _ in range(0, 4):
                if pred():
                    return n
                alg.play(cube)
                n += 1
        finally:
            (alg * n).prime.play(cube)

        return -1

    @deprecated("Use CubeQueries2 instead")
    def rotate_and_check_get_alg(self, alg: Alg, pred: Pred0) -> Alg | None:
        """
        Rotate face and check condition
        :return the algorithm needed to fulfill the pred, or None if no such


        :param alg:
        :param pred:
        """

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        n = self.cube.cqr.rotate_and_check(alg, pred)  # type: ignore[arg-type]  # deprecated backward compat

        if n >= 0:
            if n == 0:
                return Algs.no_op()
            else:
                return alg * n
        else:
            return None

    @deprecated("Use CubeQueries2 instead")
    def rotate_face_and_check(self, f: Face, pred: Callable[[], bool]) -> int:
        """
        Rotate face and check condition
        Restores Cube, doesn't operate on operator


        :param f:
        :param pred:
        :return: number of rotation, -1 if check fails
        restore cube state before returning, this is not count as solve step
        """

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        return self.cube.cqr.rotate_and_check(Algs.of_face(f.name), pred)

    @deprecated("Use CubeQueries2 instead")
    def rotate_face_and_check_get_alg_deprecated(self, f: Face, pred: Pred0) -> Alg:
        """
        Rotate face and check condition
        :return the algorithm needed to fulfill the pred
        :raise InternalSWError if no such algorithm  exists to fullfil the pred


        :param f:
        :param pred:
        :return: number of rotation, -1 if check fails
        restore cube state before returning, this is not count as solve step
        """

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        alg = Algs.of_face(f.name)
        n = self.cube.cqr.rotate_and_check(alg, pred)
        assert n >= 0

        return alg * n

    @deprecated("Use CubeQueries2 instead")
    def rotate_face_and_check_get_alg(self, f: Face, pred: Pred0) -> Alg | None:
        """
        Rotate face and check condition
        :return the algorithm needed to fulfill the pred, or None if no such


        :param f:
        :param pred:
        """

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        alg = Algs.of_face(f.name)
        n = self.cube.cqr.rotate_and_check(alg, pred)

        if n >= 0:
            if n == 0:
                return Algs.no_op()
            else:
                return alg * n
        else:
            return None

    def rotate_till(self, alg: Alg, pred: Callable[[], bool]) -> int:
        """
        Do alg and check condition
        if after 3 rotation condition is false then raise exception

        THIS METHOD MODIFY CUBE AND USE OPERATOR


        :param alg:
        :param pred:
        :return number of rotations made
        """

        n = 0
        for _ in range(0, 3):
            if pred():
                return n

            self.op.play(alg)
            n += 1

        if pred():
            return n

        raise InternalSWError()

    def rotate_face_till(self, f: Face, pred: Callable[[], bool]) -> int:
        """
        Rotate face and check condition
        if after 3 rotation condition is false then raise exception

        THIS METHOD MODIFY CUBE AND USE OPERATOR

        :param f:
        :param pred:
        :return number of rotations made
        """

        return self.rotate_till(Algs.of_face(f.name), pred)

    def bring_face_up(self, f: Face) -> None:
        """Bring the given face to the UP position using whole-cube rotations.

        This method uses only whole-cube rotations (X, Y, Z) which change the
        cube's viewing orientation without moving any pieces relative to each other.
        All edges, corners, and centers stay in their same relative positions -
        only the perspective changes.

        This is safe to call at any point during solving because it doesn't
        disturb any solved pieces or relationships between pieces.

        Args:
            f: The face to bring to UP position

        Raises:
            InternalSWError: If f is not a valid face
        """
        if f.name != FaceName.U:

            self.debug("Need to bring ", f, 'to', FaceName.U)

            with self.ann.annotate(h2=f"Bringing face {f.name.value} {f.color} up"):

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

                self.op.play(alg)

    # NEVER TESTED !!
    def bring_face_down(self, f: Face) -> None:
        """Bring the given face to the DOWN position using whole-cube rotations.

        This method uses only whole-cube rotations (X, Y, Z) which change the
        cube's viewing orientation without moving any pieces relative to each other.
        All edges, corners, and centers stay in their same relative positions -
        only the perspective changes.

        This is safe to call at any point during solving because it doesn't
        disturb any solved pieces or relationships between pieces.

        Args:
            f: The face to bring to UP position

        Raises:
            InternalSWError: If f is not a valid face
        """
        if f.name != FaceName.D:

            self.debug("Need to bring ", f, 'to', FaceName.D)

            with self.ann.annotate(h2=f"Bringing face {f.name.value} {f.color} down"):

                alg: Alg

                match f.name:

                    case FaceName.F:
                        alg = Algs.X.prime

                    case FaceName.B:
                        alg = Algs.X

                    case FaceName.U:
                        alg = Algs.X * 2

                    case FaceName.L:
                        alg = -Algs.Y + -Algs.X

                    case FaceName.R:
                        alg = Algs.Y -  Algs.X

                    case _:
                        raise InternalSWError(f"Unknown face {f}")

                self.op.play(alg)

    def bring_face_front(self, f: Face):

        """
        By Whole cube rotation
        #claude: dcumnet it nicely like above
        :param f:
        :return:
        """

        if f.name != FaceName.F:

            self.debug("Need to bring ", f, 'to', FaceName.F)

            with self.ann.annotate(h2=f"Bringing face {f.name.value} {f.color} to front"):

                match f.name:

                    case FaceName.U:
                        self.op.play(Algs.X.prime)

                    case FaceName.B:
                        self.op.play(-Algs.X.prime * 2)

                    case FaceName.D:
                        self.op.play(Algs.X)

                    case FaceName.L:
                        self.op.play(Algs.Y.prime)

                    case FaceName.R:
                        self.op.play(Algs.Y)

                    case _:
                        raise InternalSWError(f"Unknown face {f}")

    def bring_face_up_preserve_front(self, face: Face) -> None:

        #claude: documnet it like niceother whole cube roatation
        if face.name != FaceName.U:

            self.debug("Need to bring ", face, 'to', FaceName.U)


            front = self.cube.front

            with self.ann.annotate(h2=f"Bringing face preserve front{face.name.value} {face.color} up"):

                alg: Alg

                match face.name:

                    case FaceName.F:
                        raise InternalSWError(f"You cannot bring front  {face} up and preserve front{face.name.value} ")

                    case FaceName.B:
                        raise InternalSWError(f"You cannot bring back {face} up and preserve front{face.name.value} ")

                    case FaceName.D:
                        alg = Algs.Z * 2

                    case FaceName.L:
                        alg = Algs.Z

                    case FaceName.R:
                        alg = Algs.Z.prime

                    case _:
                        raise InternalSWError(f"Unknown face {face}")

                self.op.play(alg)

                assert self.cube.front is front

    # NEVER TESTED
    def bring_face_down_preserve_front(self, face: Face) -> None:

        #claude: documnet it like niceother whole cube roatation
        if face.name != FaceName.U:

            self.debug("Need to bring ", face, 'to', FaceName.U)


            front = self.cube.front

            with self.ann.annotate(h2=f"Bringing face preserve front{face.name.value} {face.color} up"):

                alg: Alg

                match face.name:

                    case FaceName.F:
                        raise InternalSWError(f"You cannot bring front  {face} up and preserve front{face.name.value} ")

                    case FaceName.B:
                        raise InternalSWError(f"You cannot bring back {face} up and preserve front{face.name.value} ")

                    case FaceName.D:
                        alg = Algs.Z * 2

                    case FaceName.L:
                        alg = Algs.Z

                    case FaceName.R:
                        alg = Algs.Z.prime

                    case _:
                        raise InternalSWError(f"Unknown face {face}")

                self.op.play(alg)

                assert self.cube.front is front

    def bring_face_front_preserve_down(self, face: Face) -> None:

        #claude: documnet it like niceother whole cube roatation
        if face.name != FaceName.F:

            self.debug("Need to bring ", face, 'to', FaceName.U)


            front = self.cube.front

            with self.ann.annotate(h2=f"Bringing face {face.name.value} {face.color}  preserving front up"):

                alg: Alg

                match face.name:

                    case FaceName.D | FaceName.U:
                        raise InternalSWError(f"You cannot bring front  {face}  front  "
                                              f"preserving down {front} ")


                    case FaceName.B:
                        alg = Algs.Y * 2

                    case FaceName.L:
                        alg = -Algs.Y

                    case FaceName.R:
                        alg = Algs.Y

                    case _:
                        raise InternalSWError(f"Unknown face {face}")

                self.op.play(alg)

                assert self.cube.front is front


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
            self.slv.op.play(alg)
            return alg

        if cube.left.edge_left is edge:
            alg = Algs.E
            self.slv.op.play(alg)
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
                _slice = s_tracker.the_slice_nl

                edge = _slice.parent

                if edge not in cube.front.edges:

                    # if cube.front.edge_left is edge:
                    #     return  # nothing to do

                    if edge in cube.down.edges:
                        self.op.play(Algs.X)  # Over R, now on front
                        continue

                    elif edge in cube.back.edges:
                        self.op.play(-Algs.X * 2)  # Over R, now on front

                    elif edge in cube.up.edges:
                        self.op.play(-Algs.X)  # Over R, now on front

                    elif edge in cube.right.edges:
                        self.op.play(Algs.Y * 2)  # Over U, now on front

                    elif edge in cube.left.edges:
                        self.op.play(-Algs.Y)  # Over U, now on  front

                    else:
                        raise InternalSWError(f"Unknown case {edge}")

                else:

                    if cube.front.edge_left is edge:
                        return s_tracker.the_slice_nl.parent  # nothing to do

                    if edge is cube.front.edge_top:
                        self.op.play(Algs.Z.prime)
                    elif edge is cube.front.edge_right:
                        self.op.play(Algs.Z * 2)
                    elif edge is cube.front.edge_bottom:
                        self.op.play(Algs.Z)

                    now_edge = s_tracker.the_slice_nl.parent

                    if now_edge is not cube.left.edge_right:
                        raise InternalSWError(f"Internal error {begin_edge} {now_edge}")

                    return now_edge

            now_edge = s_tracker.the_slice_nl.parent

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
                _slice = s_tracker.the_slice_nl

                edge = _slice.parent

                if cube.front.edge_right is edge:
                    return  # done

                # ---------------------- on back --------------------
                if edge is cube.back.edge_top:
                    self.op.play(Algs.B.prime)  # now on right
                    continue

                elif edge is cube.back.edge_right:
                    self.op.play(Algs.B.prime * 2)  # now on right

                elif edge is cube.back.edge_bottom:
                    self.op.play(Algs.B)  # now on right

                # back left is right

                # ---------------------- on top --------------------

                # up top and up right are on back/right - no need to handle

                elif edge is cube.up.edge_left:
                    self.op.play(Algs.U.prime * 2)  # now on right top

                elif edge is cube.up.edge_bottom:
                    self.op.play(Algs.U.prime)  # now on right top

                # ---------------------- front --------------------
                elif edge is cube.front.edge_bottom:
                    self.op.play(Algs.D)  # now on right bottom

                elif edge is cube.left.edge_bottom:
                    self.op.play(Algs.D.prime * 2)  # now on right bottom

                # now handle on right

                elif edge is cube.right.edge_bottom:
                    self.op.play(Algs.R)  # now on front right

                elif edge is cube.right.edge_right:
                    self.op.play(Algs.R * 2)  # Over F, now on left

                elif edge is cube.right.edge_top:
                    self.op.play(Algs.R.prime)  # Over F, now on left

                else:

                    raise InternalSWError(f"Unknown case, edge is {edge}")

    def bring_face_to_front_by_y_rotate(self, face) -> None:
        """
        rotate over U
        :param face:  must be L , R, F, B
        :return:
        """

        if face.is_front:
            return  # nothing to do

        if face.is_left:
            self.slv.op.play(-Algs.Y)
            return

        if face.is_right:
            self.slv.op.play(Algs.Y)
            return

        if face.is_back:
            self.slv.op.play(Algs.Y * 2)
            return

        raise ValueError(f"{face} must be L/R/F/B")

    def bring_bottom_edge_to_front_by_d_rotate(self, edge: Edge) -> None:

        d: Face = self.slv.cube.down

        assert d.is_edge(edge)

        other: Face = edge.get_other_face(d)

        if other.is_front:
            return  # nothing to do

        if other.is_left:
            self.slv.op.play(Algs.D)
            return

        if other.is_right:
            self.slv.op.play(-Algs.D)
            return

        if other.is_back:
            self.slv.op.play(Algs.D * 2)
            return

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
    def track_e_slice(self, es: EdgeWing) -> Generator[EdgeSliceTracker, None, None]:

        global TRACE_UNIQUE_ID

        TRACE_UNIQUE_ID += 1

        n = TRACE_UNIQUE_ID

        key = "SliceTracker:" + str(n)

        def _pred(s: EdgeWing) -> bool:
            return key in s.c_attributes

        tracker: EdgeSliceTracker = EdgeSliceTracker(self.cube, _pred)

        es.c_attributes[key] = key

        try:
            yield tracker
        finally:
            c_att = tracker.the_slice_nl.c_attributes
            del c_att[key]
