from elements import *
from elements import PartSlice

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "cube.Cube"  # type: ignore


class Face(SuperElement):
    """
    Faces never chane position, only the color of the parts
    """

    __slots__ = ["_name", "_original_color",
                 "_center", "_direction",
                 "_edge_left", "_edge_top", "_edge_right", "_edge_bottom",
                 "_corner_top_left", "_corner_top_right", "_corner_bottom_right", "_corner_bottom_left",
                 "_parts",
                 "_edges",
                 "_corners",
                 "_opposite"
                 ]

    _center: Center
    _direction: Direction

    _edge_left: Edge
    _edge_top: Edge
    _edge_right: Edge
    _edge_bottom: Edge

    _corner_top_left: Corner
    _corner_top_right: Corner
    _corner_bottom_right: Corner
    _corner_bottom_left: Corner

    _edges: Sequence[Edge]
    _corners: Sequence[Corner]

    _opposite: _Face

    def __init__(self, cube: _Cube, name: FaceName, color: Color) -> None:
        super().__init__(cube)

        self._name = name
        self._original_color = color
        self._center = self._create_center(color)
        self._direction = Direction.D0
        self._parts: Tuple[Part]

        # all others are created by Cube#reset

    def _create_center(self, color: Color) -> Center:
        n = self.cube.n_slices

        f = self

        slices: list[list[PartSlice]]
        slices = [[PartSlice((i, j), PartEdge(f, color)) for j in range(n)] for i in range(n)]

        return Center(slices)

    def finish_init(self):
        self._edges = (self._edge_top, self._edge_left, self._edge_right, self._edge_bottom)

        self._corners = [self._corner_top_left,
                         self._corner_top_right,
                         self._corner_bottom_right,
                         self._corner_bottom_left]

        self.set_parts(self._center, *self._edges, *self._corners)
        super().finish_init()

        n = self.cube.n_slices
        n1 = n - 1
        self._edge_bottom.get_slice(0).get_face_edge(self).attributes["origin"] = True
        self._edge_left.get_slice(0).get_face_edge(self).attributes["origin"] = True
        self._edge_top.get_slice(0).get_face_edge(self).attributes["origin"] = True
        self._edge_right.get_slice(0).get_face_edge(self).attributes["origin"] = True
        self._edge_bottom.get_slice(n1).get_face_edge(self).attributes["on_x"] = True
        self._edge_left.get_slice(n1).get_face_edge(self).attributes["on_y"] = True

        for i in range(n):
            self._edge_left.get_slice(i).get_face_edge(self).attributes["cw"] = i
            self._edge_top.get_slice(i).get_face_edge(self).attributes["cw"] = i
            self._edge_right.get_slice(i).get_face_edge(self).attributes["cw"] = n1 - i
            self._edge_bottom.get_slice(i).get_face_edge(self).attributes["cw"] = n1 - i

        for e in self._edges:
            for i in range(n):
                #cw = self._edge_bottom.get_slice(i).get_face_edge(self).attributes["cw"]
                e.get_left_top_left_edge(self, i).c_attributes["n"] = i + 1

        self._center.get_center_slice((0, 0)).get_face_edge(self).attributes["origin"] = True
        self._center.get_center_slice((0, n1)).get_face_edge(self).attributes["on_x"] = True
        self._center.get_center_slice((n1, 0)).get_face_edge(self).attributes["on_y"] = True

    # noinspection PyUnresolvedReferences

    @property
    def name(self) -> FaceName:
        return self._name

    @property
    def center(self) -> Center:
        return self._center

    @property
    def edges(self) -> Sequence[Edge]:
        # need to cache
        return self._edges

    @property
    def corners(self) -> Sequence[Corner]:
        # need to cache
        return self._corners

    @property
    def edge_left(self) -> Edge:
        return self._edge_left

    @property
    def edge_top(self) -> Edge:
        return self._edge_top

    @property
    def edge_right(self) -> Edge:
        return self._edge_right

    @property
    def edge_bottom(self) -> Edge:
        return self._edge_bottom

    @property
    def corner_top_right(self) -> Corner:
        return self._corner_top_right

    @property
    def corner_top_left(self) -> Corner:
        return self._corner_top_left

    @property
    def corner_bottom_right(self) -> Corner:
        return self._corner_bottom_right

    @property
    def corner_bottom_left(self) -> Corner:
        return self._corner_bottom_left

    @property
    def color(self):
        return self.center.color

    def __str__(self) -> str:
        return f"{self._center.edg().color.name}/{self._original_color.name}@{self._name.value}"

    def __repr__(self):
        return self.__str__()

    # for constructing only, valid only after ctor
    def create_part(self) -> PartEdge:
        e: PartEdge = PartEdge(self, self.color)
        return e

    def _get_other_face(self, e: Edge) -> _Face:
        return e.get_other_face(self)

    def rotate(self, n_rotations=1):

        # slices_indexes: EdgeSliceIndex = slice(0, self.cube.n_slices)
        #
        # to_right__indexes = Edge.inv_index(slices_indexes)

        n_slices = self.cube.n_slices

        def inv(i):
            return  n_slices -1 - i

        def _rotate():
            left: Face = self._get_other_face(self._edge_left)
            right: Face = self._get_other_face(self._edge_right)
            top: Face = self._get_other_face(self._edge_top)
            bottom: Face = self._get_other_face(self._edge_bottom)

            # top -> right -> bottom -> left -> top

            #           -->
            #           TOP
            #          0 1 2
            #       2         2
            # ^ LEFT  1         1 RIGHT  ^
            #       0         0
            #          0 1 2
            #          BOTTOM
            #          -->
            # - so bottom and right are in reverse left-top-right direction, see right-top-left-coordinates.jpg
            #  So when copying from LEFT<--BOTTOM and RIGHT<-TOP we need to switch indexes
            #
            # todo if it works, replace with slices
            saved_top: Edge = self._edge_top.copy()
            # saved_right: Edge = self._edge_right.copy()
            # saved_bottom: Edge = self._edge_bottom.copy()
            # saved_left: Edge = self._edge_left.copy()

            # not clear why is needed, but without it when rotating front, left face is not correctly colord
            # TODO: CHECK AND IMPROVE
            e_right: Edge = self._edge_right.copy()
            e_bottom: Edge = self._edge_bottom.copy()
            e_left: Edge = self._edge_left.copy()

            for index in range(n_slices):

                #todo: optimize - we can calc only once

                top_ltr_index = saved_top.get_left_top_left_slice_index(self, index)

                i_left = e_left.get_slice_index_from_ltr_index(self, top_ltr_index)
                i_top = index # saved_top.get_left_top_left_slice_index(self, index)
                i_right = e_right.get_left_top_left_slice_index(self, inv(top_ltr_index))
                i_bottom = e_bottom.get_left_top_left_slice_index(self, inv(top_ltr_index))

                # left --> top
                self._edge_top.copy_colors_horizontal(e_left, index=i_top, source_index=i_left)
                self._edge_left.copy_colors_horizontal(e_bottom, index=i_left, source_index=i_bottom)
                self._edge_bottom.copy_colors_horizontal(e_right, index=i_bottom, source_index=i_right)
                self._edge_right.copy_colors_horizontal(saved_top, index=i_right, source_index=i_top)

            saved_bottom_left = self._corner_bottom_left.copy()

            # bottom_left -> top_left -> top_right -> bottom_right -> bottom_left
            self._corner_bottom_left.replace_colors(self, self._corner_bottom_right, right, bottom, bottom, left)
            self._corner_bottom_right.replace_colors(self, self._corner_top_right, top, right, right, bottom)
            self._corner_top_right.replace_colors(self, self._corner_top_left, top, right, left, top)
            self._corner_top_left.replace_colors(self, saved_bottom_left, left, top, bottom, left)

        for _ in range(0, n_rotations % 4):
            # -1 --> 3
            _rotate()

    @property
    def solved(self):
        return (self.center.color ==
                self._edge_top.f_color(self) ==
                self._edge_right.f_color(self) ==
                self._edge_bottom.f_color(self) ==
                self._edge_left.f_color(self) ==
                self._corner_top_left.f_color(self) ==
                self._corner_top_right.f_color(self) ==
                self._corner_bottom_left.f_color(self) ==
                self._corner_bottom_right.f_color(self)
                )

    @property
    def is3x3(self):
        # todo: Optimize it !!!, reset after slice rotation
        return all(p.is3x3 for p in self.parts)

    def reset_after_faces_changes(self):
        """
        Call after faces colors aare changes , M, S, E rotations
        """
        for p in self._parts:
            p.reset_after_faces_changes()

    def find_part_by_colors(self, part_colors_id: PartColorsID) -> Part | None:
        for p in self._parts:

            if part_colors_id == p.colors_id_by_color:
                return p
        return None

    def find_part_by_pos_colors(self, part_colors_id: PartColorsID) -> Part | None:

        n = len(part_colors_id)

        assert n in range(1, 4)

        if n == 1:
            if self.center.colors_id_by_pos == part_colors_id:
                return self.center
            else:
                return None
        elif n == 2:
            return self.find_edge_by_pos_colors(part_colors_id)
        else:
            return self.find_corner_by_pos_colors(part_colors_id)

    def find_edge_by_colors(self, part_colors_id: PartColorsID) -> Edge | None:
        for p in self._edges:

            if part_colors_id == p.colors_id_by_color:
                return p
        return None

    def find_corner_by_colors(self, part_colors_id: PartColorsID) -> Corner | None:
        for p in self._corners:

            if part_colors_id == p.colors_id_by_color:
                return p
        return None

    def find_edge_by_pos_colors(self, part_colors_id: PartColorsID) -> Edge | None:
        for p in self._edges:

            if part_colors_id == p.colors_id_by_pos:
                return p
        return None

    def find_corner_by_pos_colors(self, part_colors_id: PartColorsID) -> Corner | None:

        for p in self._corners:
            if part_colors_id == p.colors_id_by_pos:
                return p
        return None

    def adjusted_faces(self) -> Iterable[_Face]:

        # todo: optimize
        for e in self.edges:
            yield e.get_other_face(self)

    def is_left_or_right(self, edge: Edge) -> bool:

        if self._edge_left is edge:
            return True
        elif self._edge_right is edge:
            return True
        else:
            return False

    def is_edge(self, edge: Edge) -> bool:
        """
        This edge belongs to face
        :param edge:
        :return:
        """
        return edge in self._edges

    @property
    def opposite(self) -> _Face:
        return self._opposite

    def set_opposite(self, o: _Face):
        """
        By cube constructor only
        :return:
        """
        self._opposite = o
        o._opposite = self

    @property
    def is_front(self):
        return self.name is FaceName.F

    @property
    def is_back(self):
        return self.name is FaceName.B

    @property
    def is_down(self):
        return self.name is FaceName.D

    @property
    def is_up(self):
        return self.name is FaceName.U

    @property
    def is_right(self):
        return self.name is FaceName.R

    @property
    def is_left(self):
        return self.name is FaceName.L

    @property
    def slices(self) -> Iterable[PartSlice]:
        for p in self._parts:
            yield from p.all_slices
