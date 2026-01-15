from collections.abc import Hashable, Iterable, Sequence
from typing import Callable, Tuple, TypeAlias

from cube.domain.exceptions import InternalSWError

from ._elements import CenterSliceIndex, Direction, EdgePosition, PartColorsID
from .PartSlice import CenterSlice, PartSlice
from .Center import Center
from .Corner import Corner
from cube.domain.geometric.cube_boy import Color, FaceName
from .Edge import Edge
from .Part import Part
from .PartEdge import PartEdge
from .SuperElement import SuperElement

_Face: TypeAlias = "Face"
_Cube: TypeAlias = "cube.Cube"  # type: ignore  # noqa: F821


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
                 "_edge_by_position",
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
    _edge_by_position: dict[EdgePosition, Edge]
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

        self._edge_by_position = {
            EdgePosition.LEFT: self._edge_left,
            EdgePosition.RIGHT: self._edge_right,
            EdgePosition.TOP: self._edge_top,
            EdgePosition.BOTTOM: self._edge_bottom,
        }

        self._corners = [self._corner_top_left,
                         self._corner_top_right,
                         self._corner_bottom_right,
                         self._corner_bottom_left]

        self.set_parts(self._center, *self._edges, *self._corners)
        super().finish_init()

        markers_cfg = self.config.markers_config
        draw_markers = markers_cfg.GUI_DRAW_MARKERS
        sample_markers = markers_cfg.GUI_DRAW_SAMPLE_MARKERS
        draw_ltr_cords = markers_cfg.GUI_DRAW_LTR_ORIGIN_ARROWS
        mf = self.cube.sp.marker_factory
        mm = self.cube.sp.marker_manager

        n = self.cube.n_slices
        n1 = n - 1

        if draw_ltr_cords:
            # LTR Coordinate System Markers:
            # - Origin (bottom-left corner): filled black circle
            # - X-axis (bottom edge, pointing right): red arrow
            # - Y-axis (left edge, pointing up): blue arrow

            # Origin marker on bottom-left corner
            corner_bl = self._corner_bottom_left.slice.get_face_edge(self)
            mm.add_fixed_marker(corner_bl, "ltr_origin", mf.ltr_origin())

            # X-axis arrow on bottom edge (LTR index 0 = nearest to origin)
            # Each edge has its own conversion - use the specific edge's method
            x_slice_idx = self._edge_bottom.get_slice_index_from_ltr_index(self, 0)
            edge_x = self._edge_bottom.get_slice(x_slice_idx).get_face_edge(self)
            mm.add_fixed_marker(edge_x, "ltr_arrow_x", mf.ltr_arrow_x())

            # Y-axis arrow on left edge (LTR index 0 = nearest to origin)
            # Each edge has its own conversion - use the specific edge's method
            y_slice_idx = self._edge_left.get_slice_index_from_ltr_index(self, 0)
            edge_y = self._edge_left.get_slice(y_slice_idx).get_face_edge(self)
            mm.add_fixed_marker(edge_y, "ltr_arrow_y", mf.ltr_arrow_y())

        if draw_markers:
            # Set origin markers on edges (slot 0 of each edge)
            origin_marker = mf.origin()
            mm.add_fixed_marker(self._edge_bottom.get_slice(0).get_face_edge(self), "origin", origin_marker)
            mm.add_fixed_marker(self._edge_left.get_slice(0).get_face_edge(self), "origin", origin_marker)
            mm.add_fixed_marker(self._edge_top.get_slice(0).get_face_edge(self), "origin", origin_marker)
            mm.add_fixed_marker(self._edge_right.get_slice(0).get_face_edge(self), "origin", origin_marker)

            # Set on_x marker (X-axis direction)
            mm.add_fixed_marker(self._edge_bottom.get_slice(n1).get_face_edge(self), "on_x", mf.on_x())

            # Set on_y marker (Y-axis direction)
            mm.add_fixed_marker(self._edge_left.get_slice(n1).get_face_edge(self), "on_y", mf.on_y())

            # Set coordinate markers on center pieces
            mm.add_fixed_marker(self._center.get_center_slice((0, 0)).get_face_edge(self), "origin", origin_marker)
            mm.add_fixed_marker(self._center.get_center_slice((0, n1)).get_face_edge(self), "on_x", mf.on_x())
            mm.add_fixed_marker(self._center.get_center_slice((n1, 0)).get_face_edge(self), "on_y", mf.on_y())

        for i in range(n):
            if sample_markers:
                # Sample markers for debugging: C1 on left edge, C2 on right edge
                mm.add_marker(self._edge_left.get_slice(i).get_face_edge(self), f"sample_c1_{i}", mf.c1(), moveable=True)
                mm.add_marker(self._edge_right.get_slice(i).get_face_edge(self), f"sample_c2_{i}", mf.c2(), moveable=False)

            self._edge_left.get_slice(i).get_face_edge(self).attributes["cw"] = i
            self._edge_top.get_slice(i).get_face_edge(self).attributes["cw"] = i
            self._edge_right.get_slice(i).get_face_edge(self).attributes["cw"] = n1 - i
            self._edge_bottom.get_slice(i).get_face_edge(self).attributes["cw"] = n1 - i

        for e in self._edges:
            for i in range(n):
                # cw = self._edge_bottom.get_slice(i).get_face_edge(self).attributes["cw"]
                e.get_left_top_left_edge(self, i).c_attributes["n"] = i + 1

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

    def get_center_slice(self, index: CenterSliceIndex) -> "CenterSlice":
        """
        A short cut for center.get_center_slice()
        Row, Column
        :param index:
        :return:
        """
        return self.center.get_center_slice(index)


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

    def get_edge(self, position: EdgePosition) -> Edge:
        """
        Get the edge at the specified position on this face.

        Args:
            position: Which edge to get (LEFT, RIGHT, TOP, or BOTTOM)

        Returns:
            The Edge at that position

        Example:
            face.get_edge(EdgePosition.LEFT)  # same as face.edge_left
        """
        return self._edge_by_position[position]

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
    def color(self) -> Color:
        """
        The DYNAMIC color of the face's center - reads from center piece at (n//2, n//2).

        WARNING - UNRELIABLE DURING BIG CUBE CENTER SOLVING:
        =====================================================
        On even cubes (4x4, 6x6, etc.), this reads from ONE center piece
        at position (n_slices//2, n_slices//2). When centers are being
        moved by commutators, this value changes dynamically!

        Example: On a 4x4 cube, if a commutator moves the center piece at
        position (1,1) from U to F, then U.color suddenly returns BLUE
        instead of YELLOW - even though U face edges are still Yellow!

        Use cases:
        - Valid: After full reduction (all centers same color)
        - Valid: On odd cubes (center piece is fixed)
        - INVALID: During center solving on even cubes

        For checking state during center solving, use relative consistency
        between edges and corners instead of comparing to face colors.

        :return: Color of center piece at (n_slices//2, n_slices//2)
        """
        return self.center.color

    @property
    def color_at_face_str(self) -> str:
        """Return a string representation of color at this face position.

        Format: "{color}@{face_name}" e.g. "WHITE@D", "BLUE@F"

        Useful for debug messages and annotations to show both
        what color is currently on a face and which face it is.

        Returns:
            String in format "COLOR@FACE" like "WHITE@D"
        """
        return f"{self.color}@{self.name}"


    @property
    def original_color(self) -> Color:
        """
        The FIXED color this face was born with - never changes, doesn't move.

        This is the face's permanent identity regardless of what center pieces
        are currently on it. Use this during big cube center solving when
        face.color is unreliable.

        Example: U face always has original_color=YELLOW, even if a Blue
        center piece is currently at position (1,1).

        :return: The face's birth color (constant)
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

            # CLOCKWISE ROTATION: left → top → right → bottom → left
            #
            # Face's LTR coordinate system:
            # ┌─────────────────────────────────────┐
            # │            TOP (horizontal)         │
            # │           ltr: 0 → 1 → 2            │
            # │         ┌─────────────┐             │
            # │  LEFT   │             │   RIGHT     │
            # │  (vert) │      F      │   (vert)    │
            # │  ltr:   │             │   ltr:      │
            # │   2 ↑   │             │   2 ↑       │
            # │   1 │   │             │   1 │       │
            # │   0 ┘   │             │   0 ┘       │
            # │         └─────────────┘             │
            # │           ltr: 0 → 1 → 2            │
            # │           BOTTOM (horizontal)       │
            # └─────────────────────────────────────┘
            #
            # Clockwise rotation mapping (in face's ltr):
            #   LEFT[ltr=0] → TOP[ltr=0]      (bottom-left corner stays at ltr=0)
            #   LEFT[ltr=2] → TOP[ltr=2]      (top-left corner stays at ltr=2)
            #
            #   TOP[ltr=0]  → RIGHT[ltr=2]    (left of top → TOP of right = ltr inverts!)
            #   TOP[ltr=2]  → RIGHT[ltr=0]    (right of top → BOTTOM of right)
            #
            # Pattern: LEFT[ltr] → TOP[ltr] → RIGHT[inv(ltr)] → BOTTOM[inv(ltr)] → LEFT[ltr]
            #
            # The edge translation layer (get_slice_index_from_ltr_index) handles f1/f2
            # differences automatically. The face only works in its own ltr system!
            #
            # See: docs/design2/edge-face-coordinate-system-approach2.md
            #
            # Rotate edges using 4-cycle reference rotation (no cloning needed)
            # Each EdgeWing has 2 PartEdges: one on self, one on the adjacent face
            # Pattern: top ← left ← bottom ← right ← top
            e_top = self._edge_top
            e_left = self._edge_left
            e_bottom = self._edge_bottom
            e_right = self._edge_right

            for index in range(n_slices):
                # Compute index mappings using the face's ltr coordinate system
                top_ltr_index = e_top.get_ltr_index_from_slice_index(self, index)

                i_top = index
                i_left = e_left.get_slice_index_from_ltr_index(self, top_ltr_index)
                i_right = e_right.get_ltr_index_from_slice_index(self, inv(top_ltr_index))
                i_bottom = e_bottom.get_ltr_index_from_slice_index(self, inv(top_ltr_index))

                # Get the 4 EdgeWings at their mapped indices
                ew_top = e_top.get_slice(i_top)
                ew_left = e_left.get_slice(i_left)
                ew_bottom = e_bottom.get_slice(i_bottom)
                ew_right = e_right.get_slice(i_right)

                # Cycle 1: PartEdges on the rotating face (self)
                # top[self] ← left[self] ← bottom[self] ← right[self]
                PartEdge.rotate_4cycle(
                    ew_top.get_face_edge(self),
                    ew_left.get_face_edge(self),
                    ew_bottom.get_face_edge(self),
                    ew_right.get_face_edge(self)
                )

                # Cycle 2: PartEdges on the adjacent faces
                # top[top_face] ← left[left_face] ← bottom[bottom_face] ← right[right_face]
                PartEdge.rotate_4cycle(
                    ew_top.get_face_edge(top),
                    ew_left.get_face_edge(left),
                    ew_bottom.get_face_edge(bottom),
                    ew_right.get_face_edge(right)
                )

                # Rotate PartSlice tracking data (unique_id, c_attributes)
                PartSlice.rotate_4cycle_slice_data(ew_top, ew_left, ew_bottom, ew_right)

            # Rotate corners using 3 independent 4-cycles (no cloning needed)
            # Each corner has 3 PartEdges on 3 faces: self, and 2 adjacent faces
            # The 4 corners form 3 separate 4-cycles for their 3 respective PartEdges
            c_bl = self._corner_bottom_left
            c_br = self._corner_bottom_right
            c_tr = self._corner_top_right
            c_tl = self._corner_top_left

            # Cycle 1: PartEdges on the rotating face (self)
            # bottom_left[self] ← bottom_right[self] ← top_right[self] ← top_left[self]
            PartEdge.rotate_4cycle(
                c_bl.get_face_edge(self),
                c_br.get_face_edge(self),
                c_tr.get_face_edge(self),
                c_tl.get_face_edge(self)
            )

            # Cycle 2: PartEdges that form cycle through bottom→right→top→left
            # bottom_left[bottom] ← bottom_right[right] ← top_right[top] ← top_left[left]
            PartEdge.rotate_4cycle(
                c_bl.get_face_edge(bottom),
                c_br.get_face_edge(right),
                c_tr.get_face_edge(top),
                c_tl.get_face_edge(left)
            )

            # Cycle 3: PartEdges that form cycle through left→bottom→right→top
            # bottom_left[left] ← bottom_right[bottom] ← top_right[right] ← top_left[top]
            PartEdge.rotate_4cycle(
                c_bl.get_face_edge(left),
                c_br.get_face_edge(bottom),
                c_tr.get_face_edge(right),
                c_tl.get_face_edge(top)
            )

            # Rotate PartSlice tracking data for corners
            PartSlice.rotate_4cycle_slice_data(c_bl.slice, c_br.slice, c_tr.slice, c_tl.slice)

            # rotate center using 4-cycle reference rotation (no cloning needed)
            center = self._center
            is_odd = n_slices % 2
            n_half = n_slices // 2

            def _cs(r: int, c: int) -> None:
                # Collect the 4 positions in the cycle:
                # (r, c) ← (c, inv(r)) ← (inv(r), inv(c)) ← (inv(c), r) ← (r, c)
                r0, c0 = r, c
                r1, c1 = c0, inv(r0)
                r2, c2 = inv(r0), inv(c0)
                r3, c3 = inv(c0), r0

                # Get the 4 PartEdges
                p0 = center.get_center_slice((r0, c0)).edge
                p1 = center.get_center_slice((r1, c1)).edge
                p2 = center.get_center_slice((r2, c2)).edge
                p3 = center.get_center_slice((r3, c3)).edge

                # Rotate using reference swapping - O(1) for c_attributes
                PartEdge.rotate_4cycle(p0, p1, p2, p3)

            for column in range(n_half):
                for row in range(n_half):
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

        Configuration is loaded from texture_rotation_config.yaml for easy iteration.

        Args:
            quarter_turns: Number of 90° CW rotations (1 for CW, -1 for CCW)
        """
        # Skip texture updates during query mode (rotate_and_check, parity detection)
        if self.cube._in_query_mode:
            return

        # Load config from YAML (cached, reloads on file change)
        from cube.presentation.gui import texture_rotation_loader as trl
        face_name = self.name.name  # FaceName.F -> "F"
        n_slices = self.cube.n_slices

        # 1. Stickers ON THIS face (self)
        delta_self = trl.get_delta(face_name, 'self')
        if delta_self != 0:
            for edge in [self._edge_top, self._edge_right, self._edge_bottom, self._edge_left]:
                for i in range(n_slices):
                    part_edge = edge.get_slice(i).get_face_edge(self)
                    part_edge.rotate_texture(quarter_turns * delta_self)

            for corner in [self._corner_top_left, self._corner_top_right,
                           self._corner_bottom_right, self._corner_bottom_left]:
                part_edge = corner.get_face_edge(self)
                part_edge.rotate_texture(quarter_turns * delta_self)

            center = self._center
            n = self.cube.size - 2
            for row in range(n):
                for col in range(n):
                    part_edge = center.get_center_slice((row, col)).get_face_edge(self)
                    part_edge.rotate_texture(quarter_turns * delta_self)

        # 2. ADJACENT stickers - edges
        for edge in [self._edge_top, self._edge_right, self._edge_bottom, self._edge_left]:
            adjacent_face = edge.get_other_face(self)
            delta = trl.get_delta(face_name, adjacent_face.name.name)
            if delta != 0:
                for i in range(n_slices):
                    part_edge_adj = edge.get_slice(i).get_face_edge(adjacent_face)
                    part_edge_adj.rotate_texture(quarter_turns * delta)

        # 3. ADJACENT stickers - corners
        for corner in [self._corner_top_left, self._corner_top_right,
                       self._corner_bottom_right, self._corner_bottom_left]:
            for part_edge in corner.slice.edges:
                if part_edge.face != self:
                    delta = trl.get_delta(face_name, part_edge.face.name.name)
                    if delta != 0:
                        part_edge.rotate_texture(quarter_turns * delta)

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
        for e in self.edges:
            yield e.get_other_face(self)

    @property
    def others_faces(self) -> Iterable[_Face]:
        """
        All other faces adjusted and opposite
        :return:
        """

        yield from self.adjusted_faces()
        yield self.opposite

    @property
    def opposite(self) -> _Face:
        return self._opposite

    def find_shared_edge(self, face2: _Face) -> Edge | None:
        """
        Find the edge shared by two faces, or None if they're opposite.

        Returns:
            The shared Edge if faces are adjacent, None if opposite
        """
        for edge in self._edges:
            other_face = edge.get_other_face(self)
            if other_face is face2:
                return edge
        return None

    def get_shared_edge(self, face2: _Face) -> Edge:
        """
        get the edge shared by two faces, or None if they're opposite.

        Returns:
            The shared Edge if faces are adjacent, raise error if opposite
        """

        edge = self.find_shared_edge(face2)

        if edge is None:
            raise InternalSWError(f"{self} has no shared edge with {face2}")

        return edge

    def is_edge(self, edge: Edge) -> bool:
        """
        This edge belongs to face
        :param edge:
        :return:
        """
        return edge in self._edges


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

    # -------------------------------------------------------------------------
    # Edge Coordinate System Methods (Issue #53)
    # -------------------------------------------------------------------------
    # The ltr (left-to-right) coordinate system belongs to the Face.
    # Each edge translates between face's ltr and its internal slice index.
    # See: docs/design2/edge-face-coordinate-system-approach2.md
    # -------------------------------------------------------------------------

    def get_horizontal_slice_index_from_ltr(self, ltr_i: int) -> int:
        """
        Convert ltr index to slice index for horizontal edges (top/bottom).

        The face's ltr system is consistent by definition. The edge translates
        to its internal index. Edge-face ltr = Face ltr.

        See: docs/design2/edge-face-coordinate-system-approach2.md

        Args:
            ltr_i: Left-to-right index from this face's perspective

        Returns:
            Internal slice index
        """
        return self._edge_top.get_slice_index_from_ltr_index(self, ltr_i)

    def get_horizontal_ltr_from_slice_index(self, slice_i: int) -> int:
        """
        Convert slice index to ltr index for horizontal edges (top/bottom).

        The face's ltr system is consistent by definition. The edge translates
        from its internal index. Edge-face ltr = Face ltr.

        See: docs/design2/edge-face-coordinate-system-approach2.md

        Args:
            slice_i: Internal slice index

        Returns:
            Left-to-right index from this face's perspective
        """
        return self._edge_top.get_ltr_index_from_slice_index(self, slice_i)

    def get_vertical_slice_index_from_ltr(self, ltr_i: int) -> int:
        """
        Convert ltr index to slice index for vertical edges (left/right).

        The face's ltr system is consistent by definition. The edge translates
        to its internal index. Edge-face ltr = Face ltr.

        See: docs/design2/edge-face-coordinate-system-approach2.md

        Args:
            ltr_i: Bottom-to-top index from this face's perspective

        Returns:
            Internal slice index
        """
        return self._edge_left.get_slice_index_from_ltr_index(self, ltr_i)

    def get_vertical_ltr_from_slice_index(self, slice_i: int) -> int:
        """
        Convert slice index to ltr index for vertical edges (left/right).

        The face's ltr system is consistent by definition. The edge translates
        from its internal index. Edge-face ltr = Face ltr.

        See: docs/design2/edge-face-coordinate-system-approach2.md

        Args:
            slice_i: Internal slice index

        Returns:
            Bottom-to-top index from this face's perspective
        """
        return self._edge_left.get_ltr_index_from_slice_index(self, slice_i)
