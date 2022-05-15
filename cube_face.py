from elements import *

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "cube.Cube"  # type: ignore


class Face(SuperElement):
    """
    Faces never chane position, only the color of the parts
    """
    __slots__ = ["_center", "_direction", "_name",
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
        self._center = Center(PartEdge(self, color))
        self._direction = Direction.D0
        self._parts: Tuple[Part]

        # all others are created by Cube#reset

    def finish_init(self):
        self._edges = (self._edge_top, self._edge_left, self._edge_right, self._edge_bottom)

        self._corners = [self.corner_top_left,
                         self._corner_top_right,
                         self._corner_bottom_right,
                         self._corner_bottom_left]

        self.set_and_finish_init(self._center, *self._edges, *self._corners)

    # noinspection PyUnresolvedReferences
    @property
    def cube(self) -> _Cube:
        return self._cube

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
        return f"{self._center.edg().color.name}@{self._name.value}"

    def __repr__(self):
        return self.__str__()

    # for constructing only, valid only after ctor
    def create_part(self) -> PartEdge:
        e: PartEdge = PartEdge(self, self.color)
        return e

    def _get_other_face(self, e: Edge) -> _Face:
        return e.get_other_face(self)

    def rotate(self, n=1):
        def _rotate():
            left: Face = self._get_other_face(self._edge_left)
            right: Face = self._get_other_face(self._edge_right)
            top: Face = self._get_other_face(self._edge_top)
            bottom: Face = self._get_other_face(self._edge_bottom)

            # top -> right -> bottom -> left -> top

            saved_top: Edge = self._edge_top.copy()
            # left --> top
            self._edge_top.replace_colors(self, self._edge_left)
            self._edge_left.replace_colors(self, self._edge_bottom)
            self._edge_bottom.replace_colors(self, self._edge_right)
            self._edge_right.replace_colors(self, saved_top)

            saved_bottom_left = self._corner_bottom_left.copy()

            # bottom_left -> top_left -> top_right -> bottom_right -> bottom_left
            self._corner_bottom_left.replace_colors(self, self._corner_bottom_right, right, bottom, bottom, left)
            self._corner_bottom_right.replace_colors(self, self._corner_top_right, top, right, right, bottom)
            self._corner_top_right.replace_colors(self, self._corner_top_left, top, right, left, top)
            self._corner_top_left.replace_colors(self, saved_bottom_left, left, top, bottom, left)

        for _ in range(0, n % 4):
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
    def parts(self) -> Sequence[Part]:
        return self._parts
