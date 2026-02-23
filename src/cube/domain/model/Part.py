import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Sequence
from typing import Self, Tuple, TypeVar

from cube.domain.model._elements import (
    CubeElement,
    PartColorsID,
    PartFixedID,
    SliceIndex,
    _Cube,
    _Face,
)
from cube.domain.model.PartSlice import PartSlice
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.model.PartEdge import PartEdge

TPartType = TypeVar("TPartType", bound="Part")


class Part(ABC, CubeElement):
    """
    Base class for cube parts (Edge, Corner, Center).

    FUNDAMENTAL CONCEPT: Parts are FIXED in 3D space - they never move!
    Only the colored stickers (represented by PartEdge.color) rotate through
    the fixed part slots during cube moves.

    Three ID Types (see design2/model-id-system.md for visual diagrams):
    - fixed_id: Based on face NAMES (FaceName enum), NEVER changes
    - position_id: Based on face CENTER colors, changes on slice/cube rotation (M,E,S,x,y,z)
    - colors_id: Actual sticker colors, changes on ANY rotation

    Two-Phase Architecture:
    - Phase 1 (Big Cube): is3x3=False, use PartSlice.colors_id
    - Phase 2 (After Reduction): is3x3=True, use Part.colors_id, Part.in_position

    Part Types by number of faces:
    - N = 1: Center (one face)
    - N = 2: Edge (two faces)
    - N = 3: Corner (three faces)
    """
    __slots__ = ["_cube", "_fixed_id", "_colors_id_by_pos", "_colors_id_by_colors"]

    def __init__(self) -> None:
        cube = next(self.all_slices).cube
        super().__init__(cube)

        self._colors_id_by_pos: PartColorsID | None = None
        self._colors_id_by_colors: PartColorsID | None = None
        self._fixed_id: PartFixedID | None = None

        s: PartSlice
        for s in self.all_slices:
            s.set_parent(self)

    @property
    @abstractmethod
    def _3x3_representative_edges(self) -> Sequence[PartEdge]:
        """
        A 3x3 representative edges, valid for 3x3 only (probably)
        :return:
        """
        pass

    @property
    @abstractmethod
    def all_slices(self) -> Iterator[PartSlice]:
        pass

    @abstractmethod
    def get_slice(self, index: SliceIndex) -> PartSlice:
        pass

    @abstractmethod
    def get_slices(self, index: SliceIndex | None) -> Iterable[PartSlice]:
        pass

    def finish_init(self):
        """
        Assign a part a fixed _id, that is not changed when face color is changed
        Must be called before any face changed
        :return:
        """

        for s in self.all_slices:
            s.finish_init()

        _id = frozenset(s.fixed_id for s in self.all_slices)

        if self._fixed_id:
            if _id != self._fixed_id:
                raise Exception(f"SW error, you are trying to re assign part id was: {self._fixed_id}, new: {_id}")
        else:
            self._fixed_id = _id

    def clear_moveable_attributes(self) -> None:
        """
        Clear color-associated attributes from all slices of this part.

        Note: Part itself does NOT have c_attributes - only PartSlice and PartEdge do.
        This method delegates to each slice's clear_moveable_attributes().
        """
        for s in self.all_slices:
            s.clear_moveable_attributes()

    @property
    def fixed_id(self) -> PartFixedID:
        """
        Structural identity based on face NAMES - NEVER changes.

        This ID identifies the physical SLOT in the cube structure.
        It is computed from FaceName enum values (F, R, U, L, B, D),
        NOT from colors. Even if you rotate the whole cube (x, y, z),
        the fixed_id remains constant.

        Example: Edge at Front-Up position has fixed_id = {FaceName.F, FaceName.U}

        See: design2/model-id-system.md for visual diagrams
        """
        assert self._fixed_id
        return self._fixed_id

    def get_face_edge(self, face: _Face) -> PartEdge:
        """
        return the edge belong to face, raise error if not found
        :param face:
        :return:
        """
        for e in self._3x3_representative_edges:
            if face is e.face:
                return e

        raise ValueError(f"Part {self} doesn't contain face {face}")

    @property
    @abstractmethod
    def is3x3(self) -> bool:
        """
        Returns True if all slices of this part have the same colors.

        This is the key property that determines which phase the cube is in:
        - is3x3=False (Phase 1): Big cube, slices not aligned. Use slice.colors_id
        - is3x3=True (Phase 2): After reduction. Part-level methods are valid

        WARNING: When is3x3=False, these properties are MEANINGLESS:
        - colors_id (returns middle slice colors, not representative)
        - in_position
        - match_faces (may return True for wrong reasons)

        See: design2/model-id-system.md section "Evolution: Big Cube → 3x3 Reduction"
        """
        pass

    def __str__(self) -> str:

        st = ""
        n_edges = len(self._3x3_representative_edges)
        for i in range(n_edges):
            es = ""
            s: PartSlice
            for s in self.all_slices:
                e = s.edges[i]
                es += str(e) + "|"
            st += es + " "

        # s = str([str(e) for e in self.all_slices])

        if self.match_faces:
            st = "+" + st
        else:
            st = "-" + st

        return st

    def __repr__(self):
        return self.__str__()

    def _replace_colors(self, source_part: "Part", *source_dest: Tuple[_Face, _Face],
                        index: SliceIndex | None = None,
                        source_index: SliceIndex | None = None):

        """
        Replace the colors of this edge with the colors from source
        Find the edge part contains source_dest[i][0] and copy it to
        edge part that matches source_dest[i][0]

        :param source:
        :return:
        """

        if source_index is None:
            source_index = index

        source_slices: Iterable[PartSlice]
        dest_slices: Iterable[PartSlice]

        source_slices = source_part.get_slices(source_index)
        dest_slices = self.get_slices(index)

        # without that they below doesn't work, it doesn't iterate all
        # slice rotate doesn't work
        source_slices = [*source_slices]
        dest_slices = [*dest_slices]

        source_slice: PartSlice
        target_slice: PartSlice

        for source_slice, target_slice in zip(source_slices, dest_slices):
            target_slice.copy_colors(source_slice, *source_dest)

        self.reset_colors_id()

    def f_color(self, f: _Face):
        """
        The color of part on given face
        :param f:
        :return:
        """
        return self.get_face_edge(f).color

    def match_face(self, face: _Face):
        """
        Part edge on given face match its color
        :return:
        """
        return self.get_face_edge(face).color == face.color

    @property
    def match_faces(self):
        """
        Returns True if part is SOLVED: correct slot AND correct orientation.

        This means every sticker color matches its face's center color.
        Example: Edge at F-U slot has Blue sticker on F face and Yellow on U face.

        Requires is3x3=True to be meaningful (all slices must be aligned).

        Relationship to other properties:
        - in_position=True, match_faces=False → Part in right slot but wrong orientation
        - in_position=True, match_faces=True → Part fully solved

        WARNING - DO NOT USE DURING BIG CUBE CENTER SOLVING:
        =====================================================
        This method compares part colors to face.color, which reads from
        the center piece at position (n_slices//2, n_slices//2).

        On even cubes (4x4, 6x6, etc.), when centers are being moved by
        commutators, face.color changes dynamically. This causes match_faces
        to return FALSE even when edges/corners are NOT disturbed!

        For checking if edges/corners are preserved during center operations,
        use relative consistency: verify each edge's colors match the colors
        of its adjacent corners on the shared faces.

        See: design2/model-id-system.md section "Key State Check Properties"
        """
        for p in self._3x3_representative_edges:
            if p.color != p.face.color:
                return False

        return True

    @property
    def in_position(self):
        """
        Returns True if part is in correct SLOT (ignoring orientation).

        Computed as: position_id == colors_id

        This means the part's sticker colors match the face center colors
        of the slot it occupies, but it may still be rotated wrong.

        Example:
        - Edge with White-Red stickers at D-R slot (White/Red centers) → in_position=True
        - Same edge may have White on D, Red on R → match_faces=True
        - Or White on R, Red on D → match_faces=False (flipped)

        Requires is3x3=True to be meaningful.

        See: design2/model-id-system.md section "Key State Check Properties"
        """
        return self.position_id == self.colors_id

    @property
    @abstractmethod
    def required_position(self) -> Self:
        """
        :return: true if part in position, ignoring orientation, position id same as color id
        """

    @property
    def position_id(self) -> PartColorsID:
        """
        Target position identity based on face CENTER colors.

        Returns the colors of the FACES this part slot is on (not the sticker colors).
        This tells you where a part SHOULD go - which slot it belongs to.

        Changes when:
        - Slice rotation (M, E, S) - moves face centers
        - Cube rotation (x, y, z) - rotates whole cube including centers

        Does NOT change when:
        - Face rotation (F, R, U, L, B, D) - centers stay fixed

        Example: Edge at F-U slot → position_id = {BLUE, YELLOW}
        (colors of Face F and Face U centers)

        See: design2/model-id-system.md section "When Does colors_id Change?"
        """

        by_pos: PartColorsID | None = self._colors_id_by_pos

        if not by_pos or (self.config.dont_optimized_part_id):
            by_pos = frozenset(e.face.color for e in self._3x3_representative_edges)
            self._colors_id_by_pos = by_pos

        return by_pos

    @classmethod
    def parts_id_by_pos(cls, parts: Sequence["Part"]) -> Sequence[PartColorsID]:

        return [p.position_id for p in parts]

    def reset_after_faces_changes(self):
        """Reset cached position IDs when face center colors change (M, E, S, x, y, z)."""
        self._colors_id_by_pos = None
        for s in self.all_slices:
            s.reset_position_id()

    @property
    def colors_id(self) -> PartColorsID:
        """
        Actual sticker colors - identifies WHICH piece this is.

        Returns the ACTUAL colors currently visible on this part's stickers.
        This tells you what piece is in this slot (its identity).

        Changes when:
        - ANY rotation (F, R, U, M, E, S, x, y, z, etc.)

        WARNING: Only meaningful when is3x3=True!
        When is3x3=False, returns middle slice colors which don't represent the part.

        Example: White-Red edge piece → colors_id = {WHITE, RED}
        (regardless of which slot it's currently in)

        Comparison with position_id:
        - position_id: Where the slot IS (face centers)
        - colors_id: What piece IS here (sticker colors)
        - in_position = (position_id == colors_id)

        See: design2/model-id-system.md for visual diagrams
        """

        colors_id: PartColorsID | None = self._colors_id_by_colors

        if not colors_id or self.config.dont_optimized_part_id:

            new_colors_id = frozenset(e.color for e in self._3x3_representative_edges)

            if colors_id and new_colors_id != colors_id:
                print("Bug here !!!!", file=sys.stderr)

            colors_id = new_colors_id

            self._colors_id_by_colors = new_colors_id

        return colors_id

    def reset_colors_id(self):
        self._colors_id_by_colors = None

    def on_face(self, f: _Face) -> PartEdge | None:
        """
        :param f:
        :return: true if any edge is on f
        """
        for p in self._3x3_representative_edges:
            if p.face is f:
                return p

        return None

    def on_face_by_name(self, name: FaceName) -> PartEdge | None:

        for p in self._3x3_representative_edges:
            if p.face.name == name:
                return p

        return None

    def face_of_actual_color(self, c: Color):

        """
        Not the color the edge is on !!!
        :param c:
        :return:
        """

        for p in self._3x3_representative_edges:
            if p.color == c:
                return p.face

        raise ValueError(f"No color {c} on {self}")

    @classmethod
    def all_match_faces(cls, parts: Sequence["Part"]):
        """
        Return true if all parts match - each part edge matches the face it is located on
        :param parts:
        :return:
        """
        return all(p.match_faces for p in parts)

    @classmethod
    def all_in_position(cls, parts: Sequence["Part"]):
        """
        Return true if all parts match - each part edge matches the face it is located on
        :param parts:
        :return:
        """
        return all(p.in_position for p in parts)

    @property
    def cube(self) -> _Cube:
        return self._cube

    def annotate(self, fixed_location: bool):
        for p in self._3x3_representative_edges:
            p.annotate(fixed_location)

    def un_annotate(self):
        for p in self._3x3_representative_edges:
            p.un_annotate()

    @property
    def annotated(self) -> bool:
        return any(p.annotated for p in self._3x3_representative_edges)

    @property
    def annotated_by_color(self) -> bool:
        return any(p.annotated_by_color for p in self._3x3_representative_edges)

    @property
    def annotated_fixed(self) -> bool:
        return any(p.annotated_fixed for p in self._3x3_representative_edges)

    @property
    def name(self):
        raise NotImplementedError

    @property
    def name_n_faces(self) -> str:  # for animation
        """
        return the name of the part with face id - name of faces is on
        Good also for non 3x3 because it is the name of the face, not color
        :return: e.g. 'Edge Front/Right'
        """
        # s1 = ""
        # s2 = ""
        #
        # for e in self._3x3_representative_edges:
        #     s1 += str(e.face.name.value)

        return self.part_name + " " + str(self.name)

    def name_n_faces_colors(self) -> str:  # for animation
        """
        return the name of the part with color ID
        For is3x3 only
        :return: e.g. 'Edge FL White/Red'
        """
        s1 = ""
        s2 = ""

        for e in self._3x3_representative_edges:
            s1 += str(e.face.name.value)
            s2 += str(e.color.long) + "/"

        s2 = s2[0:-1]

        return self.part_name + " " + s1 + " " + s2

    @property
    def name_n_colors(self) -> str:  # for animation
        """
        return the name of the part with color Faces ID and colors
        Actual colors and not colors of face(position)
        :return: e.g. 'Edge White/Red'
        """
        s_colors = ""

        for e in self._3x3_representative_edges:
            s_colors += str(e.color.long) + "/"

        s_colors = s_colors[0:-1]

        return self.part_name + " " + s_colors

    @property
    @abstractmethod
    def part_name(self) -> str:
        pass
