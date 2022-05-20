from collections.abc import Sequence
from enum import Enum, unique
from typing import Iterable

from cube_face import Face
from elements import SuperElement, _Cube, Edge, Center, PartSlice


@unique
class SliceName(Enum):
    S = "S"  # Middle over F
    M = "M"  # Middle over R
    E = "E"  # Middle over D


class Slice(SuperElement):
    __slots__ = [
        "_name",
        "_slice_index",
        "_left", "_left_bottom", "_bottom",
        "_right_bottom", "_right", "_right_top",
        "_top", "_left_top",
        "_edges", "_centers",
        "_for_debug"

    ]

    def __init__(self, cube: _Cube, name: SliceName,
                 left_top: Edge, top: Center, right_top: Edge,
                 right: Center,
                 right_bottom: Edge, bottom: Center, left_bottom: Edge,
                 left: Center) -> None:
        super().__init__(cube)
        self._name = name
        self._slice_index = 0
        self._left = left
        self._left_bottom = left_bottom
        self._bottom = bottom
        self._right_bottom = right_bottom
        self._right = right
        self._right_top = right_top
        self._top = top
        self._left_top = left_top

        self._edges: Sequence[Edge] = [left_top, right_top, right_bottom, left_bottom]
        self._centers: Sequence[Center] = [ top, left, bottom, right ]

        self.set_parts(
            left_top, top, right_top,
            right,
            right_bottom, bottom, left_bottom,
            left
        )

    def rotate(self, n=1):

        if n == 0:
            return

        left: Center = self._left
        left_bottom: Edge = self._left_bottom
        bottom: Center = self._bottom
        right_bottom: Edge = self._right_bottom
        right: Center = self._right
        right_top: Edge = self._right_top
        top: Center = self._top
        left_top: Edge = self._left_top

        cube = self.cube
        cube.sanity()
        index = self._slice_index

        for _ in range(0, n % 4):
            saved_up: Center = top.copy()

            top.copy_colors(left)
            left.copy_colors(bottom)
            bottom.copy_colors(right)
            right.copy_colors(saved_up)

            # right_top <-- left_top <-- left_bottom < --right_bottom <-- right_top

            saved_right_top: Edge = right_top.copy()
            right_top.copy_colors_ver(left_top, index=index)
            left_top.copy_colors_ver(left_bottom, index=index)
            left_bottom.copy_colors_ver(right_bottom, index=index)
            right_bottom.copy_colors_ver(saved_right_top, index=index)

        cube.reset_after_faces_changes()
        cube.sanity()

    @property
    def slices(self) -> Iterable[PartSlice]:
        index = self._slice_index
        if index < 0:
            for p in self._parts:
                yield from p.all_slices
        else:
            for e in self._edges:
                    yield e.get_slice(index)

            n = self.cube.n_slices
            for c in self._centers:
                for i in range(n):
                    yield c.get_slice(i, index)
