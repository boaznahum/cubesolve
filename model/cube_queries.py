import itertools
from collections import defaultdict
from collections.abc import Iterator, Hashable, Sequence, MutableSequence, Mapping, MutableMapping, Iterable
from typing import Callable, TypeVar, Tuple, Collection

from app_exceptions import InternalSWError
from .cube import Cube
from .cube_boy import Color
from .cube_face import Face
from .elements import PartSlice, CenterSlice, PartColorsID, Edge, EdgeSlice, PartType

T = TypeVar("T")
Pred = Callable[[T], bool]


class CubeQueries:

    @staticmethod
    def is_face(cube: Cube, pred: Pred[Face]) -> Face | None:

        s: PartSlice
        for f in cube.faces:
            if pred(f):
                return f

        return None

    @staticmethod
    def find_face(cube: Cube, pred: Pred[Face]) -> Face:

        face = CubeQueries.is_face(cube, pred)

        if face:
            return face

        raise InternalSWError(f"Can't find face with pred {pred}")

    @staticmethod
    def find_slice(cube: Cube, slice_unique_id: int) -> PartSlice:

        s: PartSlice
        for f in cube.faces:
            for s in f.slices:
                if s.unique_id == slice_unique_id:
                    return s

        raise InternalSWError(f"Can't find slice with unique id {slice_unique_id}")

    @staticmethod
    def find_part_by_color(parts: Iterable[PartType], color_id: PartColorsID) -> PartType:

        for p in parts:
            if p.colors_id_by_color == color_id:
                return p

        raise InternalSWError(f"Can't find part with color id {color_id}")

    @staticmethod
    def find_part_by_position(parts: Iterable[PartType], position_id: PartColorsID) -> PartType:

        for p in parts:
            if p.colors_id_by_pos == position_id:
                return p

        raise InternalSWError(f"Can't find part with color id {position_id}")

    @staticmethod
    def is_center_slice(cube: Cube, pred: Callable[[CenterSlice], bool]) -> CenterSlice | None:

        s: CenterSlice
        for f in cube.faces:
            for s in f.center.all_slices:
                if pred(s):
                    return s

        return None

    @staticmethod
    def find_center_slice(cube: Cube, pred: Callable[[CenterSlice], bool]) -> CenterSlice:

        s = CubeQueries.is_center_slice(cube, pred)

        if s:
            return s

        raise InternalSWError(f"No such center slice for pred{pred}")

    @staticmethod
    def find_slice_in_face_center(face: Face, pred: Pred[CenterSlice]) -> CenterSlice | None:

        s: CenterSlice
        for s in face.center.all_slices:
            if pred(s):
                return s

        return None

    @staticmethod
    def get_four_center_points(cube: Cube, r, c) -> Iterator[Tuple[int, int]]:

        inv = cube.inv

        for _ in range(4):
            yield r, c
            (r, c) = (c, inv(r))

    @staticmethod
    def get_two_edge_slice_points(cube: Cube, i) -> Iterable[int]:

        inv = cube.inv

        return i, inv(i)

    @staticmethod
    def print_dist(cube: Cube):
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

        dist: Mapping[PartColorsID, MutableMapping[Hashable, MutableSequence[int]]]

        dist = defaultdict(lambda: defaultdict(list))

        e: Edge
        for e in cube.edges:
            for i in range(cube.n_slices):
                s: EdgeSlice = e.get_slice(i)
                clr = s.colors_id_by_color
                counter: MutableMapping[Hashable, MutableSequence[int]] = dist[clr]
                key = frozenset([*CubeQueries.get_two_edge_slice_points(cube, i)])
                counter[key].append(i)

        return dist

    @staticmethod
    def get_sate(cube) -> Collection[PartSlice]:

        return cube.get_all_parts()

    @staticmethod
    def compare_state(cube: Cube, other: Collection[PartSlice]):

        st2: Collection[PartSlice] = CubeQueries.get_sate(cube)

        if len(other) != len(st2):
            return False

        s1: PartSlice
        s2: PartSlice
        return all(s1.same_colors(s2) for s1, s2 in itertools.zip_longest(other, st2))

    @classmethod
    def find_slice_in_cube_edges(cls, cube: Cube, pred: Pred[EdgeSlice]) -> EdgeSlice | None:

        return CubeQueries.find_slice_in_edges(cube.edges, pred)

    @classmethod
    def find_slice_in_edges(cls, edges: Iterable[Edge], pred: Pred[EdgeSlice]) -> EdgeSlice | None:

        for e in edges:
            for i in range(e.n_slices):
                s: EdgeSlice = e.get_slice(i)

                if pred(s):
                    return s

        return None

    @classmethod
    def find_slice_in_cube(cls, cube: Cube, pred: Pred[EdgeSlice]) -> EdgeSlice | None:
        return CubeQueries.find_slice_in_edges(cube.edges, pred)

    @classmethod
    def find_edge_in_cube(cls, cube: Cube, pred: Pred[Edge]) -> Edge | None:

        for e in cube.edges:
            if pred(e):
                return e

        return None

    @classmethod
    def find_edge(cls, edges: Iterable[Edge], pred: Pred[Edge]) -> Edge | None:

        for e in edges:
            if pred(e):
                return e

        return None
