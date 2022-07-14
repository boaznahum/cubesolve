import itertools
import warnings
from collections import defaultdict
from collections.abc import Iterator, Hashable, Sequence, MutableSequence, Mapping, MutableMapping, Iterable
from typing import Callable, TypeVar, Tuple, Collection

from cube.app_exceptions import InternalSWError
from . import PartEdge
from .cube import Cube
from .cube_boy import Color
from .cube_face import Face
from ._elements import PartColorsID
from ._part_slice import PartSlice, CenterSlice, EdgeWing, CornerSlice
from ._part import Edge, Part, TPartType

T = TypeVar("T")
Pred = Callable[[T], bool]
Pred0 = Callable[[], bool]


class CubeQueries:
    """
    Depricated, use CubeQueries2
    """




    @staticmethod
    def is_face(cube: Cube, pred: Pred[Face]) -> Face | None:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        s: PartSlice
        for f in cube.faces:
            if pred(f):
                return f

        return None

    @staticmethod
    def find_face(cube: Cube, pred: Pred[Face]) -> Face:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        face = CubeQueries.is_face(cube, pred)

        if face:
            return face

        raise InternalSWError(f"Can't find face with pred {pred}")

    @staticmethod
    def find_slice_in_cube_edges(cube: Cube, pred: Pred[EdgeWing]) -> EdgeWing | None:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        return CubeQueries.find_slice_in_edges(cube.edges, pred)

    @staticmethod
    def find_slice_in_edges(edges: Iterable[Edge], pred: Pred[EdgeWing]) -> EdgeWing | None:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        for e in edges:
            for i in range(e.n_slices):
                s: EdgeWing = e.get_slice(i)

                if pred(s):
                    return s

        return None

    @classmethod
    def find_edge_slice_in_cube(cls, cube: Cube, pred: Pred[EdgeWing]) -> EdgeWing | None:
        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        return CubeQueries.find_slice_in_edges(cube.edges, pred)

    @staticmethod
    def is_center_slice(cube: Cube, pred: Callable[[CenterSlice], bool]) -> CenterSlice | None:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        s: CenterSlice
        for f in cube.faces:
            for s in f.center.all_slices:
                if pred(s):
                    return s

        return None

    @staticmethod
    def find_center_slice(cube: Cube, pred: Callable[[CenterSlice], bool]) -> CenterSlice:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        s = CubeQueries.is_center_slice(cube, pred)

        if s:
            return s

        raise InternalSWError(f"No such center slice for pred{pred}")

    @staticmethod
    def find_slice_in_face_center(face: Face, pred: Pred[CenterSlice]) -> CenterSlice | None:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        s: CenterSlice
        for s in face.center.all_slices:
            if pred(s):
                return s

        return None

    @staticmethod
    def is_slice_edge(parts: Iterable[Part], pred: Callable[[PartEdge], bool]) -> PartEdge | None:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        s: PartSlice
        for p in parts:
            for s in p.all_slices:
                for e in s.edges:
                    if pred(e):
                        return e

        return None

    @staticmethod
    def find_slice_edge(parts: Iterable[Part], pred: Pred[PartEdge]) -> PartEdge:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        s: PartSlice
        for p in parts:
            for s in p.all_slices:
                for e in s.edges:
                    if pred(e):
                        return e

        raise InternalSWError(f"No such edge in {parts}  slice for pred{pred}")

    @staticmethod
    def find_corner_slice_edge_in_cube(cube: Cube, pred: Pred[PartEdge]) -> PartEdge:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        return CubeQueries.find_slice_edge(cube.corners, pred)

    @staticmethod
    def is_corner_slice_edge(cube: Cube, pred: Callable[[PartEdge], bool]) -> PartEdge | None:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        s: CornerSlice
        for c in cube.corners:
            for s in c.all_slices:
                for e in s.edges:
                    if pred(e):
                        return e

        return None

    @staticmethod
    def find_part_by_color(parts: Iterable[TPartType], color_id: PartColorsID) -> TPartType:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        for p in parts:
            if p.colors_id_by_color == color_id:
                return p

        raise InternalSWError(f"Can't find part with color id {color_id}")

    @staticmethod
    def find_part_by_position(parts: Iterable[TPartType], position_id: PartColorsID) -> TPartType:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        for p in parts:
            if p.colors_id_by_pos == position_id:
                return p

        raise InternalSWError(f"Can't find part with color id {position_id}")

    @staticmethod
    def get_four_center_points(cube: Cube, r, c) -> Iterator[Tuple[int, int]]:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        inv = cube.inv

        for _ in range(4):
            yield r, c
            (r, c) = (c, inv(r))

    @staticmethod
    def rotate_point_clockwise(cube: Cube, rc: Tuple[int, int], n=1) -> Tuple[int, int]:
        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        inv = cube.inv
        for i in range(0, n % 4):
            rc = inv(rc[1]), rc[0]

        return rc

    @staticmethod
    def rotate_point_counterclockwise(cube: Cube, rc: Tuple[int, int], n=1) -> Tuple[int, int]:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        inv = cube.inv
        for i in range(0, n % 4):
            rc = rc[1], inv(rc[0])

        return rc

    @staticmethod
    def get_two_edge_slice_points(cube: Cube, i) -> Iterable[int]:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        inv = cube.inv

        return i, inv(i)

    @staticmethod
    def print_dist(cube: Cube):
        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        for clr in Color:
            n = 0
            counter: dict[Hashable, MutableSequence[Tuple[int, int]]] = defaultdict(list)
            for f in cube.faces:
                for r in range(cube.n_slices):
                    for c in range(cube.n_slices):
                        s = f.center.get_center_slice((r, c))
                        if s.color == clr:
                            n += 1
                            key = frozenset([*CubeQueries.get_four_center_points(cube, r, c)])
                            counter[key].append((r, c))
                            # print(n, "]", s, *CubeQueries.get_four_center_points(cube, r, c))
            for k, v in counter.items():
                if len(v) != 4:
                    m = "!!!"
                else:
                    m = "+++"
                print(clr, k, f"{m}{len(v)}{m}", v)

    @staticmethod
    def get_centers_dist(cube: Cube) -> Mapping[Color, Mapping[Hashable, Sequence[Tuple[int, int]]]]:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        dist: Mapping[Color, MutableMapping[Hashable, MutableSequence[Tuple[int, int]]]]

        dist = defaultdict(lambda: defaultdict(list))

        for f in cube.faces:
            for r in range(cube.n_slices):
                for c in range(cube.n_slices):
                    s = f.center.get_center_slice((r, c))
                    clr = s.color
                    counter: MutableMapping[Hashable, MutableSequence[Tuple[int, int]]] = dist[clr]
                    key = frozenset([*CubeQueries.get_four_center_points(cube, r, c)])
                    counter[key].append((r, c))

        return dist

    @staticmethod
    def get_edges_dist(cube: Cube) -> Mapping[PartColorsID, Mapping[Hashable, Sequence[int]]]:

        """
        For each possible edge color, return list of slice corrdinates
        Slice coordinate can be i or inv(i) and in some cases it will have both equal
        :return:
        """

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        dist: Mapping[PartColorsID, MutableMapping[Hashable, MutableSequence[int]]]

        dist = defaultdict(lambda: defaultdict(list))

        e: Edge
        for e in cube.edges:
            for i in range(cube.n_slices):
                s: EdgeWing = e.get_slice(i)
                clr = s.colors_id_by_color
                counter: MutableMapping[Hashable, MutableSequence[int]] = dist[clr]
                key = frozenset([*CubeQueries.get_two_edge_slice_points(cube, i)])
                counter[key].append(i)

        return dist

    @staticmethod
    def get_sate(cube) -> Collection[PartSlice]:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        return cube.get_all_parts()

    @staticmethod
    def compare_state(cube: Cube, other: Collection[PartSlice]):

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        st2: Collection[PartSlice] = CubeQueries.get_sate(cube)

        if len(other) != len(st2):
            return False

        s1: PartSlice
        s2: PartSlice
        return all(s1.same_colors(s2) for s1, s2 in itertools.zip_longest(other, st2))

    @classmethod
    def find_edge_in_cube(cls, cube: Cube, pred: Pred[Edge]) -> Edge | None:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        for e in cube.edges:
            if pred(e):
                return e

        return None

    @classmethod
    def find_edge(cls, edges: Iterable[Edge], pred: Pred[Edge]) -> Edge | None:

        warnings.warn("Use CubeQueries2", DeprecationWarning, 2)

        for e in edges:
            if pred(e):
                return e

        return None
