from collections.abc import Sequence
from typing import Callable

from .cube_boy import FaceName
from .Center import Center
from .Corner import Corner
from .Edge import Edge
from .PartEdge import PartEdge
from .Part import Part
from ._elements import *
from ._part_slice import PartSlice, CenterSlice
from .SuperElement import SuperElement
from cube.domain.model.VMarker import VMarker, viewer_add_view_marker

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "cube.Cube"  # type: ignore


class Face(SuperElement, Hashable):
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

        slices: list[list[CenterSlice]]
        slices = [[CenterSlice((i, j), PartEdge(f, color)) for j in range(n)] for i in range(n)]

        return Center(slices)

    def __hash__(self) -> int:
        # we use faces in set in nxn_centers
        return hash(self._name)

    def __eq__(self, __o: object) -> bool:
        # we use faces in set in nxn_centers
        return isinstance(__o, Face) and __o._name == self._name

    def finish_init(self):
        self._edges = (self._edge_top, self._edge_left, self._edge_right, self._edge_bottom)

        self._corners = [self._corner_top_left,
                         self._corner_top_right,
                         self._corner_bottom_right,
                         self._corner_bottom_left]

        self.set_parts(self._center, *self._edges, *self._corners)
        super().finish_init()

        sample_markers = self.config.gui_draw_sample_markers

        n = self.cube.n_slices
        n1 = n - 1
        self._edge_bottom.get_slice(0).get_face_edge(self).attributes["origin"] = True
        self._edge_left.get_slice(0).get_face_edge(self).attributes["origin"] = True
        self._edge_top.get_slice(0).get_face_edge(self).attributes["origin"] = True
        self._edge_right.get_slice(0).get_face_edge(self).attributes["origin"] = True
        self._edge_bottom.get_slice(n1).get_face_edge(self).attributes["on_x"] = True
        self._edge_left.get_slice(n1).get_face_edge(self).attributes["on_y"] = True

        for i in range(n):
            if sample_markers:
                viewer_add_view_marker(self._edge_left.get_slice(i).get_face_edge(self).c_attributes, VMarker.C1)
                viewer_add_view_marker(self._edge_right.get_slice(i).get_face_edge(self).f_attributes, VMarker.C2)

            self._edge_left.get_slice(i).get_face_edge(self).attributes["cw"] = i
            self._edge_top.get_slice(i).get_face_edge(self).attributes["cw"] = i
            self._edge_right.get_slice(i).get_face_edge(self).attributes["cw"] = n1 - i
            self._edge_bottom.get_slice(i).get_face_edge(self).attributes["cw"] = n1 - i

        for e in self._edges:
            for i in range(n):
                # cw = self._edge_bottom.get_slice(i).get_face_edge(self).attributes["cw"]
                e.get_left_top_left_edge(self, i).c_attributes["n"] = i + 1

        self._center.get_center_slice((0, 0)).get_face_edge(self).attributes["origin"] = True
        self._center.get_center_slice((0, n1)).get_face_edge(self).attributes["on_x"] = True
        self._center.get_center_slice((n1, 0)).get_face_edge(self).attributes["on_y"] = True

        for r in range(n):
            for c in range(n):
                self._center.get_center_slice((r, c)).edge.c_attributes["n"] = r * n + c

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
        """
        The color of center, valid in 3x3 only or for odd cubes !!!
        :return:
        """
        return self.center.color

    @property
    def original_color(self) -> Color:
        """
        The color the face was born with, never changed, doesn't move
        good only for locate physical faces
        :return:
        """
        return self._original_color

    def __str__(self) -> str:
        # return f"{self._center.edg().color.name}/{self._original_color.name}@{self._name.value}"
        return f"{self._center.edg().color.name}@{self._name.value}"

    def __repr__(self):
        return self.__str__()

    # for constructing only, valid only after ctor
    def create_part(self) -> PartEdge:
        e: PartEdge = PartEdge(self, self.color)
        return e

    def _get_other_face(self, e: Edge) -> _Face:
        return e.get_other_face(self)

    def rotate(self, n_rotations=1) -> None:

        # slices_indexes: EdgeSliceIndex = slice(0, self.cube.n_slices)
        #
        # to_right__indexes = Edge.inv_index(slices_indexes)

        n_slices = self.cube.n_slices

        inv: Callable[[int], int] = self.inv

        def _rotate() -> None:
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
                # todo: optimize - we can calc only once

                top_ltr_index = saved_top.get_ltr_index_from_slice_index(self, index)

                i_left = e_left.get_slice_index_from_ltr_index(self, top_ltr_index)
                i_top = index  # saved_top.get_left_top_left_slice_index(self, index)
                i_right = e_right.get_ltr_index_from_slice_index(self, inv(top_ltr_index))
                i_bottom = e_bottom.get_ltr_index_from_slice_index(self, inv(top_ltr_index))

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

            # rotate center
            center = self._center
            saved_center = center.clone()
            # e.g n = 3
            is_odd = n_slices % 2
            n_half = n_slices // 2  # = 1 (assume ceil)

            def _c1(tr, tc, sr, sc):
                center.get_center_slice((tr, tc)).edge.copy_color(saved_center.get_center_slice((sr, sc)).edge)

            def _cs(r, c):

                # copy 4 points on the ...
                # for example n = 6, r,c = 1,2
                #  1,2 = 2,4
                #  2, 4 = 4,3
                #  4, 3 = 3, 1
                #  3, 1 = 1, 2
                #  ~1, ~0 =
                for _ in range(4):
                    s = (c, inv(r))
                    _c1(r, c, s[0], s[1])
                    (r, c) = s

            for column in range(n_half):  # 0, 1
                for row in range(n_half):  # 0, 1
                    _cs(row, column)

            if is_odd:
                for column in range(n_half):
                    _cs(n_half, column)

        for _ in range(0, n_rotations % 4):
            # -1 --> 3
            _rotate()
            # Update texture directions for all affected stickers
            # See: design2/face-slice-rotation.md for details
            self._update_texture_directions_after_rotate(1)
            self.cube.modified()
            self.cube.sanity()

    def _update_texture_directions_after_rotate(self, quarter_turns: int) -> None:
        """Update texture direction for stickers affected by this face's rotation.

        When a face rotates:
        - Stickers ON this face rotate in place → direction changes
        - Stickers on ADJACENT edges/corners also rotate → direction changes

        Args:
            quarter_turns: Number of 90° CW rotations (1 for CW, -1 for CCW)
        """
        # Skip texture updates during query rotations (rotate_and_check)
        if self.cube._skip_texture_updates:
            return

        n_slices = self.cube.n_slices

        # 1. Edge stickers ON THIS face
        for edge in [self._edge_top, self._edge_right, self._edge_bottom, self._edge_left]:
            for i in range(n_slices):
                part_edge = edge.get_slice(i).get_face_edge(self)
                part_edge.rotate_texture(quarter_turns)

        # 2. Corner stickers ON THIS face
        for corner in [self._corner_top_left, self._corner_top_right,
                       self._corner_bottom_right, self._corner_bottom_left]:
            part_edge = corner.get_face_edge(self)
            part_edge.rotate_texture(quarter_turns)

        # 3. Center stickers (only exist on this face)
        center = self._center
        n = self.cube.size - 2  # Center grid is (size-2) x (size-2)
        for row in range(n):
            for col in range(n):
                part_edge = center.get_center_slice((row, col)).get_face_edge(self)
                part_edge.rotate_texture(quarter_turns)

        # 4. ADJACENT stickers - per-edge logic based on geometry
        #
        # The rule: update adjacent sticker when rotation axis affects that face's "up" direction
        # Face "up" directions: F,B,R,L have up=Y; U has up=Z-; D has up=Z+
        # Rotation axes: F,B around Z; U,D around Y; R,L around X
        #
        # Analysis per rotating face:
        # - F (Z-axis): R,L,D have up=Y (affected by Z), U has up=Z (not affected)
        #   But empirically F needs ALL adjacent updated
        # - L (X-axis): F,B have up=Y (affected by X), U,D have up=Z (affected by X)
        #   Empirically L needs ALL adjacent updated
        # - U,D (Y-axis): all adjacent have up=Y (not affected) → no updates
        # - R (X-axis): same geometry as L but empirically partial...
        # - B (Z-axis): same geometry as F but empirically no updates needed
        #
        # Empirical pattern: F and L need full adjacent updates
        # R needs updates only for faces with up=Y (F and B), not U and D
        from cube.domain.model.cube_boy import FaceName

        def should_update_adjacent(rotating_face: FaceName, adjacent_face: "Face") -> bool:
            """Determine if adjacent face stickers need texture update."""
            adj_name = adjacent_face.name
            if rotating_face == FaceName.F:
                return True  # F: all adjacent need update
            elif rotating_face == FaceName.L:
                return True  # L: all adjacent need update
            elif rotating_face == FaceName.R:
                # R: only F and B (faces with up=Y on sides)
                return adj_name in (FaceName.F, FaceName.B)
            else:
                return False  # U, D, B: no adjacent updates

        # Update adjacent edge stickers (conditionally)
        for edge in [self._edge_top, self._edge_right, self._edge_bottom, self._edge_left]:
            adjacent_face = edge.get_other_face(self)
            if should_update_adjacent(self.name, adjacent_face):
                for i in range(n_slices):
                    part_edge_adj = edge.get_slice(i).get_face_edge(adjacent_face)
                    part_edge_adj.rotate_texture(quarter_turns)

        # Update adjacent corner stickers (conditionally)
        for corner in [self._corner_top_left, self._corner_top_right,
                       self._corner_bottom_right, self._corner_bottom_left]:
            for part_edge in corner.slice.edges:
                if part_edge.face != self:
                    if should_update_adjacent(self.name, part_edge.face):
                        part_edge.rotate_texture(quarter_turns)

    @property
    def solved(self):
        if not self.is3x3:
            return False

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
        return all(p.is3x3 for p in self.edges) and self.center.is3x3

    def reset_after_faces_changes(self):
        """
        Call after faces colors aare changes , M, S, E rotations
        """
        for p in self._parts:
            p.reset_after_faces_changes()

    def find_part_by_colors(self, part_colors_id: PartColorsID) -> Part | None:
        for p in self._parts:

            if part_colors_id == p.colors_id:
                return p
        return None

    def find_part_by_pos_colors(self, part_colors_id: PartColorsID) -> Part | None:

        n = len(part_colors_id)

        assert n in range(1, 4)

        if n == 1:
            if self.center.position_id == part_colors_id:
                return self.center
            else:
                return None
        elif n == 2:
            return self.find_edge_by_pos_colors(part_colors_id)
        else:
            return self.find_corner_by_pos_colors(part_colors_id)

    def find_edge_by_colors(self, part_colors_id: PartColorsID) -> Edge | None:
        for p in self._edges:

            if part_colors_id == p.colors_id:
                return p
        return None

    def find_corner_by_colors(self, part_colors_id: PartColorsID) -> Corner | None:
        for p in self._corners:

            if part_colors_id == p.colors_id:
                return p
        return None

    def find_edge_by_pos_colors(self, part_colors_id: PartColorsID) -> Edge | None:
        for p in self._edges:

            if part_colors_id == p.position_id:
                return p
        return None

    def find_corner_by_pos_colors(self, part_colors_id: PartColorsID) -> Corner | None:

        for p in self._corners:
            if part_colors_id == p.position_id:
                return p
        return None

    def adjusted_faces(self) -> Iterable[_Face]:

        # todo: optimize
        for e in self.edges:
            yield e.get_other_face(self)

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

    def is_bottom_or_top(self, e: Edge):
        return e is self._edge_top or e is self._edge_bottom

    def is_top_edge(self, e: Edge):
        return e is self._edge_top

    def is_bottom_edge(self, e: Edge):
        return e is self._edge_bottom

    def is_right_edge(self, e: Edge):
        return e is self._edge_right

    def is_left_or_right(self, e: Edge):
        return e is self.edge_right or e is self.edge_left

    @property
    def slices(self) -> Iterable[PartSlice]:
        for p in self._parts:
            yield from p.all_slices
