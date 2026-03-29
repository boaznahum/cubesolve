from __future__ import annotations

from collections.abc import Generator, Iterable, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Sequence

from cube.domain.exceptions import InternalSWError
from cube.domain.model._elements import EdgePosition, SliceIndex
from cube.domain.model.PartSlice import EdgeWing, PartSlice
from cube.domain.model.Part import Part
from cube.domain.model.PartEdge import PartEdge
from cube.domain.model.Color import Color
from cube.domain.model import PartColorsID
from cube.domain.geometric import geometry_utils as geometry

from ._elements import EdgeSliceIndex
from .part_names import EdgeName, faces_to_edge_name

if TYPE_CHECKING:
    from .Face import Face
    from cube.domain.model.EdgesColorsProvider import EdgesColorsProvider



class Edge(Part):
    """
    An edge part shared by exactly two faces.

    Each edge contains multiple EdgeWing slices (n-2 slices for an NxN cube).
    The right_top_left_same_direction flag controls slice index mapping
    between the two faces.

    See: design2/edge-coordinate-system.md for visual explanation
    """

    def __init__(self, f1: Face, f2: Face, right_top_left_same_direction: bool,
                 slices: Sequence[EdgeWing]) -> None:
        """
        Initialize an Edge between two faces.

        Args:
            f1: First face sharing this edge
            f2: Second face sharing this edge
            right_top_left_same_direction: If True, both faces index slices the same way.
                If False, slice indices are inverted between f1 and f2.
                See design2/edge-coordinate-system.md for detailed explanation.
            slices: The EdgeWing slices that make up this edge
        """
        # assign before call to init because _edges is called from ctor
        self._slices: Sequence[EdgeWing] = slices
        self._f1: Face = f1
        self._f2: Face = f2
        self.right_top_left_same_direction = right_top_left_same_direction
        self._edges_provider: EdgesColorsProvider | None = None
        self._edge_3x3_mode: bool = False  # must be set only with color provider !!!
        if not slices:
            self._cube = f1.cube  # 2x2: provide cube for Part.__init__ fallback
        super().__init__()

        assert f1 is not f2
        if slices:
            assert f1 is self.e1.face or f1 is self.e2.face
            assert f2 is self.e1.face or f2 is self.e2.face

        # FU, FR
        self._name: str = str(f1.name) + str(f2.name)

    @property
    def e1(self) -> "PartEdge":
        return self._3x3_representative_edges[0]

    @property
    def e2(self) -> "PartEdge":
        return self._3x3_representative_edges[1]

    def __hash__(self) -> int:
        # we use faces in set in nxn_centers
        return hash(self._name)

    def __eq__(self, __o: object) -> bool:
        # we use faces in set in nxn_centers
        return isinstance(__o, Edge) and __o._name == self._name

    @property
    def _3x3_representative_edges(self) -> Sequence[PartEdge]:
        if not self._slices:
            return ()  # 2x2: no edge slices
        return self._slices[self.n_slices // 2].edges

    @property
    def is3x3(self) -> bool:
        """
        Returns True if all slices of this edge have the same colors.

        This indicates the edge has been "reduced" - all its wing pieces
        are grouped together as if it were a 3x3 edge.

        Phase implications:
        - is3x3=False: Big cube phase, work with individual slice.colors_id
        - is3x3=True: Reduced phase, edge.colors_id is meaningful

        Example for 5x5:
        - NOT reduced: slices have colors {R,B}, {O,G}, {R,B}, {G,O}, {R,B}
        - Reduced: all slices have {R,B}, {R,B}, {R,B}, {R,B}, {R,B}

        See: design2/model-id-system.md section "Evolution: Big Cube → 3x3 Reduction"
        """
        assert self._slices, f"is3x3 should not be called on 2x2 edge {self._name} with no slices"

        if self._edge_3x3_mode:
            return True

        slices = self.all_slices

        s0 = next(slices)

        c1, c2 = (s0.e1.color, s0.e2.color)

        for s in slices:
            _c1, _c2 = (s.e1.color, s.e2.color)

            if c1 != _c1 or c2 != _c2:
                return False

        return True

    @property
    def all_slices(self) -> Iterator[EdgeWing]:
        return self._slices.__iter__()

    @property
    def n_slices(self):
        return self.cube.size - 2

    def get_slice(self, index: SliceIndex) -> EdgeWing:
        """
        In unpractical order
        :param index:
        :return:
        """
        assert isinstance(index, int)
        return self._slices[index]

    def get_face_ltr_index_from_edge_slice_index(self, face: Face, i: int) -> int:
        """
        Convert edge's internal slice index to face's ltr coordinate.

        The edge serves the face's coordinate system. Each face has its own
        consistent ltr system, and this method translates from the edge's
        internal storage to the face's view.

        Critical insight: The returned ltr is always consistent with the face's
        own ltr system. Edge-face ltr = Face ltr (guaranteed by translation).

        Translation rules:
        - same_direction=True: Both faces see same order (no translation)
        - same_direction=False: f1 direct, f2 inverts

        See: docs/design2/edge-face-coordinate-system-approach2.md

        Args:
            face: The face requesting its ltr coordinate
            i: Edge's internal slice index

        Returns:
            The ltr coordinate in the face's coordinate system
        """
        assert face is self._f1 or face is self._f2

        if self.right_top_left_same_direction:
            return i
        else:
            if face is self._f1:
                return i  # arbitrary f1 was chosen
            else:
                return self.inv_index(i)  # type: ignore

    def get_edge_slice_index_from_face_ltr_index(self, face: Face, ltr_i: int) -> int:
        """
        Convert face's ltr coordinate to edge's internal slice index.

        The edge serves the face's coordinate system. The face provides its
        ltr coordinate, and this method translates to the edge's internal
        storage index.

        Critical insight: The face's ltr is the input - the edge translates
        to find the correct internal slice. Edge-face ltr = Face ltr.

        Translation rules:
        - same_direction=True: Both faces see same order (no translation)
        - same_direction=False: f1 direct, f2 inverts

        See: docs/design2/edge-face-coordinate-system-approach2.md

        Args:
            face: The face providing its ltr coordinate
            ltr_i: The face's ltr coordinate

        Returns:
            Edge's internal slice index
        """
        assert face is self._f1 or face is self._f2

        si: int
        if self.right_top_left_same_direction:
            si = ltr_i
        else:
            if face is self._f1:
                si = ltr_i  # arbitrary f1 was chosen
            else:
                si = self.inv_index(ltr_i)  # type: ignore

        assert ltr_i == self.get_face_ltr_index_from_edge_slice_index(face, si)

        return si

    def get_edge_slice_index_from_face_ltr_index_arbitrary_n_slices(self, n_slices: int, face: Face, ltr_i: int) -> int:
        """
        Convert face's ltr coordinate to edge's internal slice index.

        The edge serves the face's coordinate system. The face provides its
        ltr coordinate, and this method translates to the edge's internal
        storage index.

        Critical insight: The face's ltr is the input - the edge translates
        to find the correct internal slice. Edge-face ltr = Face ltr.

        Translation rules:
        - same_direction=True: Both faces see same order (no translation)
        - same_direction=False: f1 direct, f2 inverts

        See: docs/design2/edge-face-coordinate-system-approach2.md

        Args:
            face: The face providing its ltr coordinate
            ltr_i: The face's ltr coordinate

        Returns:
            Edge's internal slice index
            :param ltr_i:
            :param face:
            :param n_slices:
        """
        assert face is self._f1 or face is self._f2

        si: int
        if self.right_top_left_same_direction:
            si = ltr_i
        else:
            if face is self._f1:
                si = ltr_i  # arbitrary f1 was chosen
            else:
                si = geometry.inv(n_slices, ltr_i)  # type: ignore

        assert ltr_i == self.get_ltr_index_from_slice_index_arbitrary_n_slices(n_slices, face, si)

        return si

    def get_ltr_index_from_slice_index_arbitrary_n_slices(self, n_slices: int, face: Face, i: int) -> int:
        """
        Convert edge's internal slice index to face's ltr coordinate.

        The edge serves the face's coordinate system. Each face has its own
        consistent ltr system, and this method translates from the edge's
        internal storage to the face's view.

        Critical insight: The returned ltr is always consistent with the face's
        own ltr system. Edge-face ltr = Face ltr (guaranteed by translation).

        Translation rules:
        - same_direction=True: Both faces see same order (no translation)
        - same_direction=False: f1 direct, f2 inverts

        See: docs/design2/edge-face-coordinate-system-approach2.md

        Args:
            face: The face requesting its ltr coordinate
            i: Edge's internal slice index

        Returns:
            The ltr coordinate in the face's coordinate system
            :param i:
            :param face:
            :param n_slices:
        """
        assert face is self._f1 or face is self._f2

        if self.right_top_left_same_direction:
            return i
        else:
            if face is self._f1:
                return i  # arbitrary f1 was chosen
            else:
                return geometry.inv(n_slices, i)


    def get_slice_by_ltr_index(self, face: Face, i) -> EdgeWing:
        """
        Given an index of slice in direction from left to right, or left to top
        find it's actual slice.

        :param face: The face perspective
        :param i: Left-to-right index
        :return: The edge wing at that position
        """
        return self.get_slice(self.get_face_ltr_index_from_edge_slice_index(face, i))

    def get_left_top_left_edge(self, face: Face, i) -> PartEdge:
        """
        todo: optimize, combine both methods
        :param face:
        :param i:
        :return:
        """
        return self.get_slice_by_ltr_index(face, i).get_face_edge(face)

    def get_slices(self, index: SliceIndex | None) -> Iterable[PartSlice]:

        if index is not None:  # can be zero
            assert isinstance(index, int)
            if index < 0:
                yield from self.all_slices
            else:
                yield self.get_slice(index)
        else:
            yield from self.all_slices

    def get_other_face_edge(self, f: Face) -> "PartEdge":

        """
        Get the edge that is on face that is not f
        :param f:
        :return:
        """
        if not self._slices:
            raise ValueError(f"Edge {self._name} has no slices (2x2 cube)")
        return self._slices[0].get_other_face_edge(f)

    def get_other_face(self, f: Face) -> Face:
        if not self._slices:
            # 2x2: use stored face references
            if f is self._f1:
                return self._f2
            else:
                return self._f1
        return self.get_other_face_edge(f).face

    def get_position_on_face(self, face: Face) -> EdgePosition:
        """
        Get the position (LEFT, RIGHT, TOP, BOTTOM) of this edge on the given face.

        This is the inverse of Face.get_edge_position(edge).

        Args:
            face: The face to get the position on (must be one of the two faces this edge belongs to)

        Returns:
            EdgePosition indicating where this edge is on the face

        Raises:
            InternalSWError: If this edge doesn't belong to the given face

        Example:
            edge = cube.front.edge_top
            pos = edge.get_position_on_face(cube.front)  # Returns EdgePosition.TOP
        """
        return face.get_edge_position(self)

    def copy(self) -> "Edge":
        """
        Used as temporary for rotate, must not be used in cube
        :return:
        """
        slices: list[EdgeWing] = [s.clone() for s in self._slices]
        return Edge(self._f1, self._f2, self.right_top_left_same_direction, slices)

    def single_shared_face(self, other: "Edge"):
        """
        Return a face that appears in both edges
        raise error more than one (how can it be) or no one
        :param other:
        :return:
        """
        if not self._slices or not other._slices:
            raise ValueError("Edge has no slices (2x2 cube)")

        return self._slices[0].single_shared_face(other._slices[0])

    def inv_index(self, slices_indexes: EdgeSliceIndex) -> EdgeSliceIndex:

        n = self.n_slices

        if isinstance(slices_indexes, int):
            return n - 1 - slices_indexes
        else:
            assert False

    def _find_cw(self, face: Face, cw: int) -> PartEdge:
        """
        Don't use, not optimized
        :param face:
        :return:  values of 'n' ordered by 'cw'
        """
        sl: EdgeWing
        for sl in self.all_slices:
            e: PartEdge = sl.get_face_edge(face)
            _cw = e.fixed_attributes["cw"]
            if _cw == cw:
                return e

        assert False, f"No cw {cw} in edge {self} on face {face}"

    def cw_s(self, face: Face):
        """

        :param face:
        :return:  values of 'n' ordered by 'cw'
        """
        n = self.n_slices
        cw_s = ""
        n_s = ""
        for i in range(n):
            sl: PartEdge = self._find_cw(face, i)
            cw_s += str(self.get_slice(i).get_face_edge(face).fixed_attributes["cw"])
            n_s += str(sl.moveable_attributes["n"])

        return cw_s + " " + n_s

    def opposite(self, face: Face):
        """
        todo: optimize !!!
        :param face:
        :return: opposite edge on face
        """


        my_other: Face = self.get_other_face(face)
        other_opposite = my_other.opposite

        for e in other_opposite.edges:
            if face.is_edge(e):
                return e

        raise InternalSWError(f"Can't find opposite of {self} on {face}")

    def __str__(self) -> str:
        return f"{self.e1.face.name.value}{self.e2.face.name.value} " + super().__str__()

    @property
    def part_name(self) -> str:
        return "Edge"

    @property
    def name(self) -> EdgeName:
        if not self._slices:
            # 2x2: use stored face references instead of slices
            return faces_to_edge_name((self._f1.name, self._f2.name))
        return faces_to_edge_name((self.e1.face.name, self.e2.face.name))

    @property
    def colors_id(self) -> PartColorsID:
        """Override Part.colors_id to use provider colors when active."""
        if self._edges_provider is not None:
            return self._edges_provider.get_edge_colors(self)
        return super().colors_id

    def face_color(self, f: Face) -> Color:
        """Override Part.face_color to use provider colors when active."""
        if self._edges_provider is not None:
            return self._edges_provider.get_edge_face_color(self, f)
        return super().face_color(f)

    def match_face(self, face: Face) -> bool:
        """Override Part.match_face to use provider colors when active."""
        if self._edges_provider is not None:
            return self.face_color(face) == face.color
        return super().match_face(face)

    @property
    def match_faces(self) -> bool:
        """Override Part.match_faces to use provider colors when active."""
        if self._edges_provider is not None:
            for e in self._3x3_representative_edges:
                if self.face_color(e.face) != e.face.color:
                    return False
            return True
        return super().match_faces

    @contextmanager
    def with_edges_color_provider(self, provider: EdgesColorsProvider,
                                  edge_3x3_mode: bool = False) -> Generator[None, None, None]:
        """Context manager that sets an edge color provider and restores on exit."""
        assert not edge_3x3_mode or provider is not None, \
            "edge_3x3_mode requires a color provider"
        prev = self._edges_provider
        prev_3x3 = self._edge_3x3_mode
        self._edges_provider = provider
        self._edge_3x3_mode = edge_3x3_mode
        try:
            yield
        finally:
            self._edges_provider = prev
            self._edge_3x3_mode = prev_3x3

    @property
    def required_position(self) -> "Edge":
        return self.cube.find_edge_by_pos_colors(self.colors_id)
