import itertools
from collections import defaultdict
from collections.abc import Iterator, Hashable, Sequence, MutableSequence, Mapping, MutableMapping, Iterable
from typing import Callable, TypeVar, Tuple

from app_exceptions import InternalSWError
from cube import Cube
from cube_face import Face
from elements import PartSlice, CenterSlice, Color

T = TypeVar("T")
Pred = Callable[[T], bool]


class CubeQueries:

    @staticmethod
    def find_face(cube: Cube, pred: Pred[Face]) -> Face:

        s: PartSlice
        for f in cube.faces:
            if pred(f):
                return f

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
    def find_center_slice(cube: Cube, pred: Callable[[CenterSlice], bool]) -> CenterSlice | None:

        s: CenterSlice
        for f in cube.faces:
            for s in f.center.all_slices:
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
    def get_dist(cube: Cube) -> Mapping[Color, Mapping[Hashable, Sequence[Tuple[int, int]]]]:

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
                        # print(n, "]", s, *CubeQueries.get_four_center_points(cube, r, c))
        return dist

    @staticmethod
    def get_sate(cube) -> Iterable[PartSlice]:

        return cube.get_all_parts()

    @staticmethod
    def compare_state(cube: Cube, st1: Iterable[PartSlice]):

        st2 = CubeQueries.get_sate(cube)

        return all ( s1.same_colors(s2)  for s1, s2 in itertools.zip_longest(st1, st2) )