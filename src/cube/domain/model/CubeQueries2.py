from collections import defaultdict
from collections.abc import (
    Hashable,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from typing import Callable, Tuple, TypeVar

from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.geometry_types import Point

from ..algs import Alg, Algs, NSimpleAlg
from . import Edge, Part, PartEdge
from ._elements import CubeState, PartColorsID
from .PartSlice import CenterSlice, CornerSlice, EdgeWing, PartSlice
from .Cube import Cube
from cube.domain.geometric.cube_boy import Color
from .Face import Face
from .Part import TPartType

T = TypeVar("T")
Pred = Callable[[T], bool]
Pred0 = Callable[[], bool]


# noinspection PyMethodMayBeStatic
class CubeQueries2:

    def __init__(self, cube: Cube) -> None:
        super().__init__()
        self._cube = cube

    def is_face(self, pred: Pred[Face]) -> Face | None:

        cube = self._cube

        for f in cube.faces:
            if pred(f):
                return f

        return None

    def find_face(self, pred: Pred[Face]) -> Face:

        face = self.is_face(pred)

        if face:
            return face

        raise InternalSWError(f"Can't find face with pred {pred}")

    def find_slice_in_cube_edges(self, pred: Pred[EdgeWing]) -> EdgeWing | None:

        cube = self._cube

        return self.find_slice_in_edges(cube.edges, pred)

    def find_slice_in_edges(self, edges: Iterable[Edge], pred: Pred[EdgeWing]) -> EdgeWing | None:

        for e in edges:
            for i in range(e.n_slices):
                s: EdgeWing = e.get_slice(i)

                if pred(s):
                    return s

        return None

    def find_edge_slice_in_cube(self, pred: Pred[EdgeWing]) -> EdgeWing | None:
        cube = self._cube
        return self.find_slice_in_edges(cube.edges, pred)

    def is_center_slice(self, pred: Callable[[CenterSlice], bool]) -> CenterSlice | None:

        cube = self._cube

        s: CenterSlice
        for f in cube.faces:
            for s in f.center.all_slices:
                if pred(s):
                    return s

        return None

    def find_center_slice(self, pred: Callable[[CenterSlice], bool]) -> CenterSlice:

        s = self.is_center_slice(pred)

        if s:
            return s

        raise InternalSWError(f"No such center slice for pred{pred}")

    def find_slice_in_face_center(self, face: Face, pred: Pred[CenterSlice]) -> CenterSlice | None:

        s: CenterSlice
        for s in face.center.all_slices:
            if pred(s):
                return s

        return None

    def is_slice_edge(self, parts: Iterable[Part], pred: Callable[[PartEdge], bool]) -> PartEdge | None:

        s: PartSlice
        for p in parts:
            for s in p.all_slices:
                for e in s.edges:
                    if pred(e):
                        return e

        return None

    def find_slice_edge(self, parts: Iterable[Part], pred: Pred[PartEdge]) -> PartEdge:

        s: PartSlice
        for p in parts:
            for s in p.all_slices:
                for e in s.edges:
                    if pred(e):
                        return e

        raise InternalSWError(f"No such edge in {parts}  slice for pred{pred}")

    def find_corner_slice_edge_in_cube(self, pred: Pred[PartEdge]) -> PartEdge:

        cube = self._cube

        return self.find_slice_edge(cube.corners, pred)

    def is_corner_slice_edge(self, pred: Callable[[PartEdge], bool]) -> PartEdge | None:

        cube = self._cube

        s: CornerSlice
        for c in cube.corners:
            for s in c.all_slices:
                for e in s.edges:
                    if pred(e):
                        return e

        return None

    def find_part_by_color(self, parts: Iterable[TPartType], color_id: PartColorsID) -> TPartType:

        for p in parts:
            if p.colors_id == color_id:
                return p

        raise InternalSWError(f"Can't find part with color id {color_id}")

    def find_part_by_position(self, parts: Iterable[TPartType], position_id: PartColorsID) -> TPartType:

        for p in parts:
            if p.position_id == position_id:
                return p

        raise InternalSWError(f"Can't find part with color id {position_id}")

    def get_four_center_points(self, r, c) -> Iterator[Tuple[int, int]]:

        cube = self._cube

        inv = cube.inv

        for _ in range(4):
            yield r, c
            (r, c) = (c, inv(r))

    def rotate_point_clockwise(self, rc: Tuple[int, int] | Point, n: int = 1) -> Point:
        """
        Rotate a point clockwise on the face by n * 90 degrees.

        Args:
            rc: Point (row, col) - accepts both tuple and Point
            n: Number of 90-degree rotations (supports negative for counterclockwise)

        Returns:
            Rotated point as Point
        """
        if n < 0:
            return self.rotate_point_counterclockwise(rc, -n)

        cube = self._cube
        inv = cube.inv
        r, c = rc[0], rc[1]
        for _ in range(n % 4):
            r, c = inv(c), r

        return Point(r, c)

    def rotate_point_counterclockwise(self, rc: Tuple[int, int] | Point, n: int = 1) -> Point:
        """
        Rotate a point counterclockwise on the face by n * 90 degrees.

        Args:
            rc: Point (row, col) - accepts both tuple and Point
            n: Number of 90-degree rotations (supports negative for clockwise)

        Returns:
            Rotated point as Point
        """
        if n < 0:
            return self.rotate_point_clockwise(rc, -n)

        cube = self._cube
        inv = cube.inv
        r, c = rc[0], rc[1]
        for _ in range(n % 4):
            r, c = c, inv(r)

        return Point(r, c)

    def get_two_edge_slice_points(self, i) -> Iterable[int]:

        cube = self._cube

        inv = cube.inv

        return i, inv(i)

    ####################### Rotate and check methods ##########################

    def rotate_and_check(self, alg: NSimpleAlg, pred: Callable[[], bool]) -> int:
        """
        Find how many times `alg` must be applied for `pred` to become True.

        Checks predicate before each rotation, up to 4 times (0, 1, 2, 3 applications).
        Cube state is always restored before returning (query mode - no side effects).

        Args:
            alg: The algorithm to apply repeatedly (typically a face rotation).
            pred: Predicate to check after each rotation. Takes no args, returns bool.

        Returns:
            0-3: Number of times `alg` needs to be applied for `pred` to be True.
            -1: Predicate never became True within 4 rotations.

        Note:
            Bypasses Operator - no history tracking. Similar to
            Operator.with_query_restore_state but operates directly on cube.
        """

        n = 0
        cube = self._cube
        # Skip texture direction updates during query rotations
        # Save original value to support nesting
        was_in_query_mode = cube._in_query_mode
        cube.set_in_query_mode(True)
        try:
            for _ in range(0, 4):
                if pred():
                    return n
                alg.play(cube)
                n += 1
        finally:
            (alg * n).prime.play(cube)
            cube.set_in_query_mode(was_in_query_mode)

        return -1

    def rotate_and_check_get_alg(self, alg: NSimpleAlg, pred: Pred0) -> Alg | None:
        """
        Rotate face and check condition
        :return the algorithm needed to fulfill the pred, or None if no such
        :param alg:
        :param pred:
        """
        n = self.rotate_and_check(alg, pred)

        if n >= 0:
            if n == 0:
                return Algs.no_op()
            else:
                return alg * n
        else:
            return None

    def rotate_face_and_check(self, f: Face, pred: Callable[[], bool]) -> int:
        """
        Rotate face and check condition
        Restores Cube, doesn't operate on operator
        :param f:
        :param pred:
        :return: number of rotation, -1 if check fails
        restore cube state before returning, this is not count as solve step
        """
        return self.rotate_and_check(Algs.of_face(f.name), pred)

    def rotate_face_and_check_get_alg(self, f: Face, pred: Pred0) -> Alg | None:
        """
        Rotate face and check condition
        :return the algorithm needed to fulfill the pred, or None if no such
        :param f:
        :param pred:
        """
        alg = Algs.of_face(f.name)
        n = self.rotate_and_check(alg, pred)

        if n >= 0:
            if n == 0:
                return Algs.no_op()
            else:
                return alg * n
        else:
            return None

    # Count colors
    def count_color_on_face(self, face: Face, color: Color):
        n = 0

        for s in face.center.all_slices:
            if s.color == color:
                n += 1
        return n

    ########################## State methods ################################

    def print_dist(self) -> None:
        cube = self._cube

        for clr in Color:
            n = 0
            counter: dict[Hashable, MutableSequence[Tuple[int, int]]] = defaultdict(list)
            for f in cube.faces:
                for r in range(cube.n_slices):
                    for c in range(cube.n_slices):
                        s = f.center.get_center_slice((r, c))
                        if s.color == clr:
                            n += 1
                            key = frozenset([*self.get_four_center_points(r, c)])
                            counter[key].append((r, c))
                            # print(n, "]", s, *self.get_four_center_points(cube, r, c))
            for k, v in counter.items():
                if len(v) != 4:
                    m = "!!!"
                else:
                    m = "+++"
                print(clr, k, f"{m}{len(v)}{m}", v)

    def get_centers_dist(self) -> Mapping[Color, Mapping[Hashable, Sequence[Tuple[int, int]]]]:

        cube = self._cube

        dist: Mapping[Color, MutableMapping[Hashable, MutableSequence[Tuple[int, int]]]]

        dist = defaultdict(lambda: defaultdict(list))

        for f in cube.faces:
            for r in range(cube.n_slices):
                for c in range(cube.n_slices):
                    s = f.center.get_center_slice((r, c))
                    clr = s.color
                    counter: MutableMapping[Hashable, MutableSequence[Tuple[int, int]]] = dist[clr]
                    key = frozenset([*self.get_four_center_points(r, c)])
                    counter[key].append((r, c))

        return dist

    def get_edges_dist(self) -> Mapping[PartColorsID, Mapping[Hashable, Sequence[int]]]:

        """
        For each possible edge color, return list of slice coordinates
        Slice coordinate can be i or inv(i) and in some cases it will have both equal
        :return:
        """

        cube = self._cube

        dist: Mapping[PartColorsID, MutableMapping[Hashable, MutableSequence[int]]]

        dist = defaultdict(lambda: defaultdict(list))

        e: Edge
        for e in cube.edges:
            for i in range(cube.n_slices):
                s: EdgeWing = e.get_slice(i)
                clr = s.colors_id
                counter: MutableMapping[Hashable, MutableSequence[int]] = dist[clr]
                key = frozenset([*self.get_two_edge_slice_points(i)])
                counter[key].append(i)

        return dist

    def get_sate(self) -> CubeState:

        cube = self._cube

        state: CubeState = {}

        slices = cube.get_all_part_slices()

        for p in slices:
                state[p.fixed_id] = p.colors

        return state

    def compare_state(self, other: CubeState):
        """
        Compare current: meth:'get_sate' with the other state that was also
        obtained by: meth:'get_sate'

        :param other:
        :return:
        """

        st2: CubeState = self.get_sate()

        return self.compare_states(other, st2)

    @staticmethod
    def compare_states(st1: CubeState, st2: CubeState) -> bool:
        if len(st1) != len(st2):
            return False

        for k,v in st1.items():

            v2 = st2.get(k, None)
            if not v2:
                return False
            if v != v2:
                return False

        return True


    def find_edge_in_cube(self, pred: Pred[Edge]) -> Edge | None:

        cube = self._cube

        for e in cube.edges:
            if pred(e):
                return e

        return None

    def find_edge(self, edges: Iterable[Edge], pred: Pred[Edge]) -> Edge | None:

        for e in edges:
            if pred(e):
                return e

        return None

    def is_center_in_odd(self, point: Point) -> bool:

        r = point[0]

        if r != point[1]:
            return False

        cube = self._cube

        if cube.is_even:
            return False

        n_slices = cube.n_slices

        p_center = n_slices // 2

        return r == p_center


