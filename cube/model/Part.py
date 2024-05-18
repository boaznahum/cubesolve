import warnings
from abc import ABC, abstractmethod
from collections.abc import Sequence, Iterator, Iterable
from typing import Tuple, Optional, TypeVar, Self

from cube import config
from cube.model import PartSlice, PartEdge, SliceIndex, FaceName, Color
from cube.model._elements import CubeElement, PartColorsID, PartFixedID, _Face, _Cube
from cube.model.cube_boy import color2long

TPartType = TypeVar("TPartType", bound="Part")


class Part(ABC, CubeElement):
    """


    Parts never chane position, only the color of the parts


    N = 1 - center
    n = 2 - edge
    n = 3 - corner
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

        # todo - check that all slices matches faces
        #   all edges with same index has the same face, see is3x3
        # all edges with same size (1, 2, 3)

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

    # todo: fix to iterator
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

    @property
    def fixed_id(self) -> PartFixedID:
        """
        An ID that is not changed when color ir parent face color is changed
        It actually tracks the instance of the edge, but it will same for all instances of cube
        :return:
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
                        source_index: Optional[SliceIndex] = None):

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

        # for debug only unpack todo:
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
        Part is in position, all colors match the faces
        :return:
        """
        for p in self._3x3_representative_edges:
            if p.color != p.face.color:
                return False

        return True

    @property
    def in_position(self):
        """
        :return: true if part in position, ignoring orientation, position id same as color id
        """
        return self.colors_id_by_pos == self.colors_id

    @property
    @abstractmethod
    def required_position(self) -> Self:
        """
        :return: true if part in position, ignoring orientation, position id same as color id
        """

    @property
    def position_id(self) -> PartColorsID:
        """
        Return the parts required colors, assume it was in place, not actual colors
        the colors of the faces it is currently on
        This id can be changed only if faces are changed in slice and whole cube rotation
        :return:
        """

        by_pos: PartColorsID | None = self._colors_id_by_pos

        if not by_pos or (False and config.DONT_OPTIMIZED_PART_ID):
            by_pos = frozenset(e.face.color for e in self._3x3_representative_edges)
            self._colors_id_by_pos = by_pos

        return by_pos

    @property
    def colors_id_by_pos(self) -> PartColorsID:
        """
        :deprecated, use: position_id
        """
        warnings.warn("Use position_id", DeprecationWarning, 2)

        return self.position_id

    @classmethod
    def parts_id_by_pos(cls, parts: Sequence["Part"]) -> Sequence[PartColorsID]:

        return [p.position_id for p in parts]

    def reset_after_faces_changes(self):
        self._colors_id_by_pos = None

    @property
    def colors_id(self) -> PartColorsID:
        """
        Return the parts actual colors
        the colors of the faces it is currently on
        Valid for 3x3 mode
        :return:
        """

        colors_id: PartColorsID | None = self._colors_id_by_colors

        if not colors_id or config.DONT_OPTIMIZED_PART_ID:

            new_colors_id = frozenset(e.color for e in self._3x3_representative_edges)

            if colors_id and new_colors_id != colors_id:
                print("Bug here !!!!")

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
        :return: e.g. 'Edge White/Red'
        """
        s1 = ""
        s2 = ""

        for e in self._3x3_representative_edges:
            s1 += str(e.face.name.value)
            s2 += str(color2long(e.color).value) + "/"

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
            s_colors += str(color2long(e.color).value) + "/"

        s_colors = s_colors[0:-1]

        return self.part_name + " " + s_colors

    @property
    @abstractmethod
    def part_name(self) -> str:
        pass
