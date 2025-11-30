import itertools
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Hashable, MutableSequence, Sequence
from typing import TypeAlias, Any, Tuple, TypeVar, TYPE_CHECKING

from cube import config
from cube.model.PartEdge import PartEdge
from cube.model.cube_boy import FaceName, Color
from ._elements import SliceIndex, PartColorsID, PartSliceHashID, EdgeSliceIndex, CenterSliceIndex, PartSliceColors

if TYPE_CHECKING:
    from .Face import Face
    from .Cube import Cube
    from .Part import Part
    from .Edge import Edge

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "Cube"  # type: ignore
_Part: TypeAlias = "Part"
_Edge: TypeAlias = "Edge"

_TPartSlice = TypeVar("_TPartSlice", bound="PartSlice")

# a patch
_SliceUniqueID: int = 0


class PartSlice(ABC, Hashable):
    """


    Parts never chane position, only the color of the parts.
    The fixed part of: class:`PartSlice` is the: class:'Face's that the part is on
    and the index of the part.

    In NxN cube, parts: class:`Part` are composed of slices - class:`PartSlice`
        that are composed of edges: class:`PartEdge`.
        The latter is the smallest part of the cube, and it lies on a face.
    The Corner is composed of one slice, each belongs to three faces.
    Edge if composed of N slices, each belongs to two faces.
    The Center is composed of NxN slices, each belongs to one face

    As mentioned above, ach slice if fixed in space and never moved.
    So the fixed id of slice is the faces it belongs to and the index of the slice in the cube part: class:`Part`.

    Fixed ID is defined as :
        fixed_id == frozenset(tuple([index]) + tuple(p.face.name for p in self._edges))

    Why is it unique? If we consider only the faces, then we have N or NxN with the same faces, so we add the index \
    in the slice to make it unique.

    Other type of id is: attr:`_colors_id_by_colors`, this is the colors of the faces the slice is on.
    Characteristics of this id:
    1. It is not fixed; when you rotate the cube, the colors of the faces change, so the id changes.
    2. It is defined only when the cube is reduced into 3x3 cube. Because the color of the face is the color of
    the center, and it is meaningful only when the center has homogeneous color - 3x3 cube.
    3. It is not unique because we have N or NxN slices all with the faces.



    """
    __slots__ = ["_cube", "_parent", "_index", "_edges",
                 "_fixed_id",
                 "_colors_id_by_colors",
                 "_unique_id",
                 "c_attributes"
                 ]
    _edges: MutableSequence[PartEdge]

    def __init__(self, index: SliceIndex, *edges: PartEdge) -> None:
        super().__init__()

        self._cube: _Cube = edges[0].face.cube  # we have at least one edge
        self._index: SliceIndex = index

        # n=1 for center, n=2 for edge, n=3 for corner
        self._edges: MutableSequence[PartEdge] = [*edges]

        self._colors_id_by_colors: PartColorsID | None = None
        self._fixed_id: PartSliceHashID | None = None
        self._parent: _Part | None = None
        # attributes(like color) that are move around with the slice
        self.c_attributes: dict[Hashable, Any] = defaultdict(bool)

        global _SliceUniqueID
        _SliceUniqueID += 1
        self._unique_id = _SliceUniqueID

    def set_parent(self, p: _Part):
        self._parent = p

    def finish_init(self):
        """
        Assign a part a fixed _id, that is not changed when face color is changed
        Must be called before any face changed
        :return:
        """

        for e in self._edges:
            e._parent = self

        # self._parent = parent
        _id = frozenset(tuple([self._index]) + tuple(p.face.name for p in self._edges))

        if self._fixed_id:
            if _id != self._fixed_id:
                raise Exception(f"SW error, you are trying to re assign part id was: {self._fixed_id}, new: {_id}")
        else:
            self._fixed_id = _id

    @property
    def fixed_id(self) -> PartSliceHashID:
        """
        An ID that is not changed when color ir parent face color is changed
        It actually tracks the instance of the edge, but it will same for all instances of cube
        :return:
        """
        assert self._fixed_id
        return self._fixed_id

    def __hash__(self) -> int:
        return hash(self._fixed_id)

    def __eq__(self, o: object) -> bool:

        if not isinstance(o, PartSlice):
            return False

        return self._fixed_id == o._fixed_id

    def get_face_edge(self, face: _Face) -> PartEdge:
        """
        return the edge belong to face, raise error if not found
        :param face:
        :return:
        """
        for e in self._edges:
            if face is e.face:
                return e

        raise ValueError(f"Part {self} doesn't contain face {face}")

    def __str__(self) -> str:
        s = str([str(e) for e in self._edges])

        s = "[" + str(self._index) + "]" + s

        return s

    def __repr__(self):
        return self.__str__()

    def copy_colors(self, source_slice: "PartSlice", *source_dest: Tuple[_Face, _Face]):

        """
        Replace the colors of this edge with the colors from source
        Find the edge part contains source_dest[i][0] and copy it to
        edge part that matches source_dest[i][0]

        :param source_slice:
        :return:
        """

        assert len(source_dest) == len(self._edges)
        source: _Face
        target: _Face
        for source, target in source_dest:
            source_edge: PartEdge = source_slice.get_face_edge(source)
            target_edge: PartEdge = self.get_face_edge(target)

            target_edge.copy_color(source_edge)

        self._unique_id = source_slice._unique_id
        # this is critical for 3x3
        parent = self._parent
        assert parent
        parent.reset_colors_id()

        self.reset_colors_id()

        self.c_attributes.clear()
        self.c_attributes.update(source_slice.c_attributes)

    def same_colors(self, other: "PartSlice"):
        """
        Assume both have the same structure
        :param other:
        :return:
        """

        e1: PartEdge
        e2: PartEdge

        return all(e1.color == e2.color for e1, e2 in itertools.zip_longest(self.edges, other._edges))

    def f_color(self, f: _Face):
        """
        The color of part on given face
        :param f:
        :return:
        """
        return self.get_face_edge(f).color

    def match_face(self, face: _Face):
        """
        Part edge on given face matches its color
        :return:
        """
        return self.get_face_edge(face).color == face.color

    @property
    def match_faces(self):
        """
        Part is in position, all colors match the faces
        :return:
        """
        for p in self._edges:
            if p.color != p.face.color:
                return False

        return True

    @property
    def colors_id(self) -> PartColorsID:
        """
        Return the parts actual color
        the colors of the faces it is currently on
        :return:
        """

        colors_id: PartColorsID | None = self._colors_id_by_colors

        if not colors_id or config.DONT_OPTIMIZED_PART_ID:

            new_colors_id = frozenset(e.color for e in self._edges)

            if colors_id and new_colors_id != colors_id:
                print("Bug here !!!!")

            colors_id = new_colors_id

            self._colors_id_by_colors = new_colors_id

        return colors_id

    @property
    @abstractmethod
    def colors(self) -> PartSliceColors:
        """
        Not optimized, get ordered set of colors.
        This is actually the state of the slice.
        When need use :meth:`colors_id`
        TODO: maybe make :meth:`colors_id` ordered


        :return:
        """
        ...

    def reset_colors_id(self):
        self._colors_id_by_colors = None

    def on_face(self, f: _Face) -> PartEdge | None:
        """
        :param f:
        :return: true if any edge/facet is on f
        """
        for p in self._edges:
            if p.face is f:
                return p

        return None

    def on_face_by_name(self, name: FaceName) -> PartEdge | None:

        for p in self._edges:
            if p.face.name == name:
                return p

        return None

    def face_of_actual_color(self, c: Color):

        """
        Not the color the edge is on !!!
        :param c:
        :return:
        """

        for p in self._edges:
            if p.color == c:
                return p.face

        raise ValueError(f"No color {c} on {self}")

    @classmethod
    def all_match_faces(cls, parts: Sequence[_Part]):
        """
        Return true if all parts match - each part edge matches the face it is located on
        :param parts:
        :return:
        """
        return all(p.match_faces for p in parts)

    @classmethod
    def all_in_position(cls, parts: Sequence[_Part]):
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
        for p in self._edges:
            p.annotate(fixed_location)

    def un_annotate(self):
        for p in self._edges:
            p.un_annotate()

    @property
    def annotated(self) -> bool:
        return any(p.annotated for p in self._edges)

    @property
    def annotated_by_color(self) -> bool:
        return any(p.annotated_by_color for p in self._edges)

    @property
    def annotated_fixed(self) -> bool:
        return any(p.annotated_fixed for p in self._edges)

    @property
    def edges(self) -> Sequence[PartEdge]:
        return self._edges

    def _clone_edges(self) -> Sequence[PartEdge]:
        return [e.clone() for e in self._edges]

    def clone(self: _TPartSlice) -> _TPartSlice:
        s = self._clone_basic()
        s._unique_id = self._unique_id
        s.c_attributes = self.c_attributes.copy()
        # don't need to clone f_attributes, clone is used for rotating only; f_attributes is not rotated
        return s

    @abstractmethod
    def _clone_basic(self: _TPartSlice) -> _TPartSlice:
        pass

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def parent(self) -> _Part:
        return self._parent  # type: ignore

    @property
    def index(self):
        return self._index


class EdgeWing(PartSlice):

    def __init__(self, index: int, *edges: PartEdge) -> None:
        super().__init__(index, *edges)

        assert len(edges) == 2
        self.e1: PartEdge = edges[0]
        self.e2: PartEdge = edges[1]

        # my simple index
        self._my_index = index

    def _clone_basic(self: "EdgeWing") -> "EdgeWing":
        return EdgeWing(self.index, *self._clone_edges())

    def single_shared_face(self, other: "EdgeWing") -> _Face:
        """
        Return a face that appears in both edges
        raise error more than one (how can it be) or no one
        :param other:
        :return:
        """

        f1: _Face = self.e1.face
        f2: _Face = self.e2.face

        of1: _Face = other.e1.face
        of2: _Face = other.e2.face

        e11 = f1 is of1
        e12 = f1 is of2

        e21 = f2 is of1
        e22 = f2 is of2

        count = sum([e11, e12, e21, e22])

        if count == 0:
            raise RuntimeError(f"No matches: {f1} {f2} and {of1} {of2}")

        if count > 1:
            raise RuntimeError(f"Too many matches: {f1} {f2} and {of1} {of2}")

        if e11 or e12:
            return f1
        else:
            return f2

    def get_other_face_edge(self, f: _Face) -> "PartEdge":

        """
        Get the edge that is on face that is not f
        :param f:
        :return:
        """

        e1 = self.e1
        e2 = self.e2
        if e1.face is f:
            return e2
        elif e2.face is f:
            return e1
        else:
            raise ValueError(f"Face {f} not in edge {self}")

    def get_other_face(self, f: _Face) -> _Face:

        return self.get_other_face_edge(f).face

    def copy_colors_horizontal(self,
                               source: "EdgeWing"):
        """
        Copy from edge - copy from shared face
        self and the source assume to share a face

        source_other_face, shared_face --> this_other_face, shared_face

        other |__ __| other
              shared, shared,


        :param source
        """

        shared_face = self.single_shared_face(source)
        source_other = source.get_other_face(shared_face)
        dest_other = self.get_other_face(shared_face)

        self.copy_colors(source, (shared_face, shared_face), (source_other, dest_other))

    def copy_colors_ver(self,
                        source: "EdgeWing"):
        """
        Copy from vertical-edge - copy from another face,
        self and source assume to share a face

        Other |__     __|  other
              shared,  shared

        Source_other_face, shared_face  --> shared_face,this_other_face,

        :param source
        """

        shared_face = self.single_shared_face(source)
        source_other = source.get_other_face(shared_face)
        dest_other = self.get_other_face(shared_face)

        self.copy_colors(source, (source_other, shared_face),
                         (shared_face, dest_other))

    @property
    def parent(self) -> "Edge":

        p = super().parent

        from . import Edge

        assert isinstance(p, Edge)
        return p

    @property
    def index(self) -> EdgeSliceIndex:
        return self._my_index

    @property
    def colors(self) -> PartSliceColors:
        return self.e1.color, self.e2.color


class CenterSlice(PartSlice):

    def __init__(self, index: CenterSliceIndex, *edges: PartEdge) -> None:
        super().__init__(index, *edges)

    def _clone_basic(self: "CenterSlice") -> "CenterSlice":
        return CenterSlice(self.index, self._edges[0].clone())

    @property
    def index(self) -> CenterSliceIndex:
        # todo: how to assert
        return self._index  # type: ignore

    @property
    def edge(self) -> PartEdge:
        """
        Ignoring face

        :return: The single edge in center slice
        """
        return self._edges[0]

    @property
    def color(self):
        return self.edge.color

    @property
    def face(self) -> _Face:
        return self.edge.face

    def copy_center_colors(self, other: "CenterSlice"):
        # self._edges[0].copy_color(other.edg())
        self.copy_colors(other, (other.face, self.face))

    @property
    def colors(self) -> PartSliceColors:
        return self.edge.color,


class CornerSlice(PartSlice):

    def __init__(self, p1: PartEdge, p2: PartEdge, p3: PartEdge) -> None:
        super().__init__(0, p1, p2, p3)

    def _clone_basic(self: "CornerSlice") -> "CornerSlice":
        _edges = self._clone_edges()
        return CornerSlice(_edges[0], _edges[1], _edges[2])

    @property
    def colors(self) -> PartSliceColors:
        return self._edges[0].color, self._edges[1].color, self._edges[2].color
