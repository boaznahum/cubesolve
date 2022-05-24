from enum import Enum, unique
from typing import Iterable, Tuple, Sequence

from cube_face import Face
from elements import SuperElement, _Cube, Edge, Center, PartSlice, EdgeSliceIndex, CenterSliceIndex, EdgeSlice, \
    CenterSlice


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
        self._name: SliceName = name
        self._left = left
        self._left_bottom = left_bottom
        self._bottom = bottom
        self._right_bottom = right_bottom
        self._right = right
        self._right_top = right_top
        self._top = top
        self._left_top = left_top

        self._edges: Sequence[Edge] = [left_top, right_top, right_bottom, left_bottom]
        self._centers: Sequence[Center] = [top, left, bottom, right]

        self.set_parts(
            left_top, top, right_top,
            right,
            right_bottom, bottom, left_bottom,
            left
        )

    def _get_slices_by_index(self, slice_index: int) -> Tuple[Sequence[EdgeSlice], Sequence[CenterSlice]]:

        # First we need to decide with which edge to start, to get consist results
        # todo replace with abstract method

        current_edge: Edge  # this determines the direction of rotation
        current_index: int
        current_face: Face

        match self._name:
            case SliceName.M:  # over R, works
                current_face = self.cube.front
                current_edge = current_face.edge_bottom
                current_index = self.inv(slice_index)

            case SliceName.E:  # over D, works
                current_face = self.cube.right
                current_edge = current_face.edge_left
                current_index = slice_index

            case SliceName.S:  # over F, works
                current_face = self.cube.up
                current_edge = current_face.edge_left
                current_index = slice_index

            case _:
                raise ValueError(f"Unknown slice name: {self._name}")

        assert current_face.is_edge(current_edge)

        n_slices = self.n_slices

        # !!! we treat start index as in LTR coordinates on start face !!!
        edges: list[EdgeSlice] = []
        centers: list[CenterSlice] = []
        for _ in range(4):
            # here start face handling

            center: Center = current_face.center

            _c: Sequence[CenterSlice]

            if current_face.is_bottom_or_top(current_edge):
                _c = [center.get_center_slice((i, current_index)) for i in range(n_slices)]
            else:
                _c = [center.get_center_slice((current_index, i)) for i in range(n_slices)]

            centers.extend(_c)

            edge_slice = current_edge.get_ltr_index(current_face, current_index)
            edges.append(edge_slice)

            # now compute next face
            next_edge: Edge = current_edge.opposite(current_face)
            next_face = next_edge.get_other_face(current_face)
            assert next_face.is_edge(next_edge)

            next_slice_index = next_edge.get_slice_index_from_ltr_index(current_face, current_index)
            # now index on next face
            current_index = next_edge.get_ltr_index_from_slice_index(next_face, next_slice_index)
            current_edge = next_edge
            current_face = next_face

        return edges, centers

    def _rotate(self, slice_index):

        n_slices = self.n_slices

        if slice_index is None:
            s_range = range(0, n_slices)
        else:
            s_range = range(slice_index, slice_index + 1)

        for i in s_range:

            elements: tuple[Sequence[EdgeSlice], Sequence[CenterSlice]] = self._get_slices_by_index(i)

            # rotate edges
            # e0 <-- e1 <-- e2 ... e[n-1]
            # e[n-1] <-- e0
            edges: Sequence[EdgeSlice] = elements[0]
            prev: EdgeSlice = edges[0]
            e0: EdgeSlice = prev.clone()
            for e in edges[1:]:
                prev.copy_colors_ver(e)
                prev = e

            edges[-1].copy_colors_ver(e0)

            # rotate centers
            # c0 <-- c1 <-- c2 ... c[n-1]
            # c[n-1] <-- c0
            centers: Sequence[CenterSlice] = elements[1]
            for j in range(n_slices):  #
                prev_c: CenterSlice = centers[j]  # on first face
                c0: CenterSlice = prev_c.clone()
                for fi in range(1, 4):  # 1 2 3
                    c = centers[j + fi * n_slices]
                    prev_c.copy_center_colors(c)
                    prev_c = c

                centers[j + 3 * n_slices].copy_center_colors(c0)

    def rotate(self, n=1, slice_index=None):

        if n == 0:
            return

        # todo: bug, due to a bug in the algorithm
        n = - n  # still

        for _ in range(n % 4):
            self._rotate(slice_index)

        self.cube.reset_after_faces_changes()
        self.cube.sanity()

    def rotate_was(self, n=1):

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

        edge_index: EdgeSliceIndex
        center_index: CenterSliceIndex | None
        edge_index: EdgeSliceIndex = self._slice_index

        if edge_index is not None:  # can be zero
            center_index: CenterSliceIndex = (-1, edge_index)
            top_index = center_index
            left_index = center_index

            # # todo: fix
            # if self._name == SliceName.E:
            #     center_index = center_index[::-1]
            # elif self._name == SliceName.S:
            #     top_index = top_index[::-1]
            #     left_index = left_index[::-1]

        else:
            center_index = None
            top_index = None
            left_index = None

        for _ in range(0, n % 4):
            saved_up: Center = top.clone()

            top.copy_colors(left, index=top_index)
            left.copy_colors(bottom, index=left_index)
            bottom.copy_colors(right, index=top_index, source_index=center_index)
            right.copy_colors(saved_up, index=center_index, source_index=top_index)

            # right_top <-- left_top <-- left_bottom < --right_bottom <-- right_top

            saved_right_top: Edge = right_top.copy()
            right_top.copy_colors_ver(left_top, index=edge_index)
            left_top.copy_colors_ver(left_bottom, index=edge_index)
            left_bottom.copy_colors_ver(right_bottom, index=edge_index)
            right_bottom.copy_colors_ver(saved_right_top, index=edge_index)

        cube.reset_after_faces_changes()
        cube.sanity()

    @property
    def slices(self) -> Iterable[PartSlice]:
        index = 0
        if index is None:
            for p in self._parts:
                yield from p.all_slices
        else:
            for e in self._edges:
                yield e.get_slice(index)

            n = self.cube.n_slices
            for c in self._centers:
                for i in range(n):
                    yield c.get_slice((i, index))
