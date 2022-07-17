import itertools
from collections import defaultdict
from collections.abc import Iterator, Hashable, Sequence, MutableSequence, Mapping, MutableMapping, Iterable
from typing import Callable, TypeVar, Tuple, Collection, Optional

from cube.app_exceptions import InternalSWError
from . import PartEdge
from .cube import Cube
from .cube_boy import Color
from .cube_face import Face
from ._elements import PartColorsID
from ._part_slice import PartSlice, CenterSlice, EdgeWing, CornerSlice
from ._part import Edge, Part, TPartType
from ..algs import Alg, Algs
from ..algs import NSimpleAlg

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

        s: PartSlice
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
            if p.colors_id_by_pos == position_id:
                return p

        raise InternalSWError(f"Can't find part with color id {position_id}")

    def get_four_center_points(self, r, c) -> Iterator[Tuple[int, int]]:

        cube = self._cube

        inv = cube.inv

        for _ in range(4):
            yield r, c
            (r, c) = (c, inv(r))

    def rotate_point_clockwise(self, rc: Tuple[int, int], n=1) -> Tuple[int, int]:
        cube = self._cube

        inv = cube.inv
        for i in range(0, n % 4):
            rc = inv(rc[1]), rc[0]

        return rc

    def rotate_point_counterclockwise(self, rc: Tuple[int, int], n=1) -> Tuple[int, int]:

        cube = self._cube

        inv = cube.inv
        for i in range(0, n % 4):
            rc = rc[1], inv(rc[0])

        return rc

    def get_two_edge_slice_points(self, i) -> Iterable[int]:

        cube = self._cube

        inv = cube.inv

        return i, inv(i)

    ####################### Rotate and check methods ##########################

    def rotate_and_check(self, alg: NSimpleAlg, pred: Callable[[], bool]) -> int:
        """
        Apply and check condition
        :param alg:
        :param pred:
        :return: number of rotation, -1 if check fails
        restore cube state before returning, this is not count as solve step
        """

        n = 0
        cube = self._cube
        try:
            for _ in range(0, 4):
                if pred():
                    return n
                alg.play(cube)
                n += 1
        finally:
            (alg * n).prime.play(cube)

        return -1

    def rotate_and_check_get_alg(self, alg: NSimpleAlg, pred: Pred0) -> Optional[Alg]:
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

    def rotate_face_and_check_get_alg_deprecated(self, f: Face, pred: Pred0) -> Alg:
        """
        Rotate face and check condition
        :return the algorithm needed to fulfill the pred
        :raise InternalSWError if no such algorithm  exists to fulfill the pred
        :param f:
        :param pred:
        :return: number of rotation, -1 if check fails
        restore cube state before returning, this is not count as solve step
        """
        alg = Algs.of_face(f.name)
        n = self.rotate_and_check(alg, pred)
        assert n >= 0

        return alg * n

    def rotate_face_and_check_get_alg(self, f: Face, pred: Pred0) -> Optional[Alg]:
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

    def print_dist(self):
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

    def get_sate(self) -> Collection[PartSlice]:

        cube = self._cube

        return cube.get_all_parts()

    def compare_state(self, other: Collection[PartSlice]):

        st2: Collection[PartSlice] = self.get_sate()

        if len(other) != len(st2):
            return False

        s1: PartSlice
        s2: PartSlice
        return all(s1.same_colors(s2) for s1, s2 in itertools.zip_longest(other, st2))

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

