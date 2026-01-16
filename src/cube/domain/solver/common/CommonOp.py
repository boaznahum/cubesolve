from contextlib import contextmanager
from typing import Callable, ContextManager, Generator, Sequence, Tuple

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

from ...model.CubeQueries2 import Pred

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


#claud: document all methods in this class with diagrams, ask me if something is not cleat
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

        Delegates to bring_face_to(cube.up, f).
        """
        if f.name != FaceName.U:
            self.bring_face_to(self.cube.up, f)

    def bring_face_down(self, f: Face) -> None:
        """Bring the given face to the DOWN position using whole-cube rotations.

        Delegates to bring_face_to(cube.down, f).
        """
        if f.name != FaceName.D:
            self.bring_face_to(self.cube.down, f)

    def bring_face_front(self, f: Face) -> None:
        """Bring the given face to the FRONT position using whole-cube rotations.

        Delegates to bring_face_to(cube.front, f).
        """
        if f.name != FaceName.F:
            self.bring_face_to(self.cube.front, f)

    def bring_face_to(self, target: Face, source: Face) -> None:
        """Bring the source face to the target face position using whole-cube rotations.

        This is a generic method that can bring any face to any other face position.
        It uses only whole-cube rotations (X, Y, Z) which change the cube's viewing
        orientation without moving any pieces relative to each other.

        Args:
            target: The target face position (where source should end up)
            source: The source face (the face to move)

        """
        if source.name == target.name:
            return  # Already at target, nothing to do

        self.debug("Need to bring ", source, 'to', target.name)

        with self.ann.annotate(h2=f"Bringing face {source.color_at_face_str} to {target.name.value}"):
            # Use CubeLayout's cached method to get the rotation algorithm
            alg = self.cube.layout.get_bring_face_alg(target.name, source.name)
            self.op.play(alg)

    def bring_face_to_preserve(self, target: Face, source: Face, preserve: Face) -> None:
        """Bring source face to target position while keeping preserve face fixed.

        Uses constrained whole-cube rotation - only the axis that keeps preserve fixed:
        - Preserve F or B: uses Z rotation (moves L, U, R, D)
        - Preserve U or D: uses Y rotation (moves R, F, L, B)
        - Preserve L or R: uses X rotation (moves D, F, U, B)

        Args:
            target: The target face position (where source should end up)
            source: The source face (the face to move)
            preserve: The face that must stay fixed

        Raises:
            GeometryError: INVALID_PRESERVE_ROTATION if rotation is impossible
        """
        if source.name == target.name:
            return  # Already at target, nothing to do

        self.debug("Need to bring ", source, 'to', target.name, 'preserving', preserve.name)

        with self.ann.annotate(
            h2=f"Bringing {source.color_at_face_str} to {target.name.value}, "
               f"preserving {preserve.color_at_face_str}"
        ):
            alg = self.cube.layout.get_bring_face_alg_preserve(
                target.name, source.name, preserve.name
            )
            self.op.play(alg)

    def bring_face_up_preserve_front(self, face: Face) -> None:
        """Bring the given face to UP position while preserving the FRONT face."""
        self.bring_face_to_preserve(self.cube.up, face, self.cube.front)

    def bring_face_down_preserve_front(self, face: Face) -> None:
        """Bring the given face to DOWN position while preserving the FRONT face."""
        self.bring_face_to_preserve(self.cube.down, face, self.cube.front)

    def bring_face_front_preserve_down(self, face: Face) -> None:
        """Bring the given face to FRONT position while preserving the DOWN face."""
        self.bring_face_to_preserve(self.cube.front, face, self.cube.down)

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

    def bring_face_to_front_by_y_rotate(self, face: Face) -> None:
        """Bring the given face to FRONT position using only Y-axis rotation.

        This method uses only Y whole-cube rotations which rotate around
        the up-down axis. This preserves both UP and DOWN faces while
        moving the target face to FRONT.

        Only L, R, and B faces can be brought to FRONT this way.
        U and D cannot be moved to FRONT with Y rotations.

        Args:
            face: The face to bring to FRONT position (must be L, R, F, or B)

        Raises:
            ValueError: If face is U or D
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
            return key in s.moveable_attributes

        tracker: EdgeSliceTracker = EdgeSliceTracker(self.cube, _pred)

        es.moveable_attributes[key] = key

        try:
            yield tracker
        finally:
            c_att = tracker.the_slice_nl.moveable_attributes
            del c_att[key]
