"""Cube layout implementation."""

from __future__ import annotations

from collections.abc import Collection, Iterator
from typing import TYPE_CHECKING, Mapping

from cube.domain.exceptions import InternalSWError
from cube.domain.geometric.FRotation import FUnitRotation
from cube.domain.model.Edge import Edge
from cube.domain.model.SliceName import SliceName
from cube.domain.geometric.cube_layout import (
    CubeLayout,
    _ADJACENT,
    _ALL_OPPOSITE,
    _OPPOSITE,
)
from cube.domain.geometric.cube_walking import (
    UnitCubeWalkingInfo,
    UnitFaceWalkingInfo,
    _FAKE_N_SLICES,
)
from cube.domain.geometric.slice_layout import CLGColRow, SliceLayout, _SliceLayout
from cube.utils.config_protocol import ConfigProtocol, IServiceProvider
from cube.utils.Cache import CacheManager

from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face


class _CubeLayout(CubeLayout):
    """Concrete implementation of CubeLayout protocol.

    Manages a mapping of faces to colors, with support for:
    - Read-only layouts (like the BOY singleton)
    - Mutable layouts for comparison/manipulation
    - Geometric operations (opposite, adjacent faces)

    The face geometry (opposite, adjacent) is defined at the protocol level
    and shared by all implementations.
    """

    def __init__(self, read_only: bool, faces: Mapping[FaceName, Color],
                 sp: IServiceProvider) -> None:
        """Create a new CubeLayout.

        Args:
            read_only: If True, layout cannot be modified (used for BOY singleton).
            faces: Mapping of each face to its color.
            sp: Service provider for configuration access.
        """
        self._faces: dict[FaceName, Color] = dict(faces)
        self._read_only = read_only
        self._sp = sp
        self._edge_colors: Collection[frozenset[Color]] | None = None
        self._cache_manager = CacheManager.create(sp.config)

        self._slices: Mapping[SliceName, SliceLayout] = {
            SliceName.S: _SliceLayout(SliceName.S, self),
            SliceName.E: _SliceLayout(SliceName.E, self),
            SliceName.M: _SliceLayout(SliceName.M, self),
        }

        # Lazy-initialized internal 3x3 cube for geometry queries
        self._internal_cube: Cube | None = None
        self._creating_internal_cube: bool = False

    @property
    def config(self) -> ConfigProtocol:
        """Get configuration via service provider."""
        return self._sp.config

    @property
    def cache_manager(self) -> CacheManager:
        """Get the cache manager for this layout."""
        return self._cache_manager

    @property
    def _cube(self) -> "Cube":
        """Get internal 3x3 cube for geometry queries (lazy initialization).

        This cube is used to answer template-level geometry questions that
        require traversing face/edge relationships. It's created on first access.

        Raises:
            InternalSWError: If called during cube creation (cycle detected).
        """
        if self._internal_cube is not None:
            return self._internal_cube

        if self._creating_internal_cube:
            raise InternalSWError(
                "Circular dependency detected: CubeLayout._cube accessed while "
                "creating internal cube. This indicates a geometry method was "
                "called during Cube.__init__() that requires the internal cube."
            )

        # Create the internal 3x3 cube
        self._creating_internal_cube = True
        try:
            from cube.domain.model.Cube import Cube
            self._internal_cube = Cube(3, self._sp)
            # Set the layout directly (Cube doesn't accept layout in __init__)
            self._internal_cube._original_layout = self
        finally:
            self._creating_internal_cube = False

        return self._internal_cube

    def __getitem__(self, face: FaceName) -> Color:
        """Get the color for a specific face."""
        return self._faces[face]

    def get_slice(self, slice_name: SliceName) -> SliceLayout:
        return self._slices[slice_name]

    def colors(self) -> Collection[Color]:
        """Get all colors in this layout."""
        return [*self._faces.values()]

    def edge_colors(self) -> Collection[frozenset[Color]]:
        """Get all valid edge color combinations."""
        if self._edge_colors is not None:
            return self._edge_colors

        colors: set[frozenset[Color]] = set()

        for f1, c1 in self._faces.items():
            for f2, c2 in self._faces.items():
                if f1 is not f2:
                    if f2 is not _ALL_OPPOSITE[f1]:
                        c = frozenset((c1, c2))
                        colors.add(c)

        self._edge_colors = colors

        return self._edge_colors

    def opposite_color(self, color: Color) -> Color:
        """Get the color on the face opposite to the given color's face."""
        return self._faces[self.opposite(self._find_face(color))]

    def same(self, other: CubeLayout) -> bool:
        """Check if this layout is equivalent to another.

        Args:
            other: Another layout to compare with.

        Returns:
            True if layouts are equivalent, False otherwise.
        """
        # because this might be NxN in which center color have no meaning
        # we need to check
        for c in other.colors():
            if not self._is_face(c):
                return False

        # so it safe to continue !!!

        this = self.clone()

        # Check opposite colors
        # make sure that opposite colors on this, are the same in other layout
        for f1, f2 in _OPPOSITE.items():

            c1 = other[f1]
            c2 = other[f2]

            this_c1_face: FaceName = this._find_face(c1)
            this_c2_face = _ALL_OPPOSITE[this_c1_face]

            this_c2 = this._faces[this_c2_face]
            if c2 != this_c2:
                return False

        # find color of other front
        other_f_color: Color = other[FaceName.F]

        this_f_match = this._find_face(other_f_color)

        this._bring_face_to_front(this_f_match)
        assert this._faces[FaceName.F] == other_f_color

        # find UP color on other
        other_u_color = other[FaceName.U]

        this_u_match = this._find_face(other_u_color)
        if this_u_match == FaceName.B:
            return False  # on this it is on Back, can't match other layout

        this._bring_face_up_preserve_front(this_u_match)  # preserve front
        assert this._faces[FaceName.U] == other_u_color

        other_l_color = other[FaceName.L]

        this_l_color = this._faces[FaceName.L]

        if other_l_color != this_l_color:
            return False

        return True  # same layout

    def is_boy(self) -> bool:
        """Check if this layout matches the standard BOY color scheme."""
        from cube.domain.geometric import cube_boy
        return self.same(cube_boy.get_boy_layout(self._sp))

    def clone(self) -> _CubeLayout:
        """Create a mutable copy of this layout."""
        return _CubeLayout(False, self._faces, self._sp)

    def opposite(self, fn: FaceName) -> FaceName:
        """Get the face opposite to the given face."""
        return _ALL_OPPOSITE[fn]

    def is_adjacent(self, face1: FaceName, face2: FaceName) -> bool:
        """Check if two faces are adjacent (share an edge)."""
        return face2 in _ADJACENT[face1]

    def get_adjacent_faces(self, face: FaceName) -> tuple[FaceName, ...]:
        """Get all faces adjacent to the given face."""
        return _ADJACENT[face]

    def get_slice_for_faces(self, source: FaceName, target: FaceName) -> SliceName | None:
        """Find which slice connects two faces."""
        from cube.domain.geometric.cube_layout import _get_slice_for_faces
        return _get_slice_for_faces(source, target)

    def get_all_slices_for_faces(self, source: FaceName, target: FaceName) -> list[SliceName]:
        """Find ALL slices that connect two faces."""
        from cube.domain.geometric.cube_layout import _get_all_slices_for_faces
        return _get_all_slices_for_faces(source, target)

    def get_slice_parallel_to_face(self, face: FaceName) -> SliceName:
        """Find which slice is parallel to a face."""
        from cube.domain.geometric.cube_layout import _get_slice_parallel_to_face
        return _get_slice_parallel_to_face(face)

    def iterate_orthogonal_face_center_pieces(
            self,
            cube: "Cube",
            layer1_face: "Face",
            side_face: "Face",
            layer_slice_index: int,
    ) -> Iterator[tuple[int, int]]:
        return cube.sized_layout.iterate_orthogonal_face_center_pieces(
            layer1_face, side_face, layer_slice_index
        )

    def _is_face(self, color: Color) -> FaceName | None:
        """Find which face has the given color, or None if not found."""
        for f, c in self._faces.items():
            if c == color:
                return f
        return None

    def _find_face(self, color: Color) -> FaceName:
        """Find which face has the given color.

        Args:
            color: The color to find.

        Returns:
            The face with that color.

        Raises:
            InternalSWError: If color is not found.
        """
        fn = self._is_face(color)

        if fn:
            return fn

        raise InternalSWError(f"No such color {color} in {self}")

    def _bring_face_to_front(self, f: FaceName) -> None:
        """Rotate layout so the given face becomes Front.

        Used internally by same() for layout comparison.

        Args:
            f: The face to bring to front position.
        """
        assert not self._read_only

        if f != FaceName.F:

            match f:

                case FaceName.U:
                    self._rotate_x(-1)

                case FaceName.B:
                    self._rotate_x(-2)

                case FaceName.D:
                    self._rotate_x(1)

                case FaceName.L:
                    self._rotate_y(-1)

                case FaceName.R:
                    self._rotate_y(1)

                case _:
                    raise InternalSWError(f"Unknown face {f}")

    def _bring_face_up_preserve_front(self, face: FaceName) -> None:
        """Rotate layout so the given face becomes Up, keeping Front unchanged.

        Only works for faces adjacent to Front (not Back).

        Args:
            face: The face to bring to up position.

        Raises:
            InternalSWError: If face is Back (cannot preserve Front).
        """
        if face == FaceName.U:
            return

        if face == FaceName.B:
            raise InternalSWError(f"{face} is not supported")

        match face:

            case FaceName.L:
                self._rotate_z(1)

            case FaceName.D:
                self._rotate_z(2)

            case FaceName.R:
                self._rotate_z(-1)

            case _:
                raise InternalSWError(f" Unknown face {face.name}")

    def _rotate_x(self, n: int) -> None:
        """Rotate layout around R axis (like cube rotation x).

        Args:
            n: Number of 90° rotations (positive = U→F→D→B direction).
        """
        faces = self._faces

        for _ in range(n % 4):
            self._check()
            f = faces[FaceName.F]
            faces[FaceName.F] = faces[FaceName.D]
            faces[FaceName.D] = faces[FaceName.B]
            faces[FaceName.B] = faces[FaceName.U]
            faces[FaceName.U] = f
            self._check()

    def _rotate_y(self, n: int) -> None:
        """Rotate layout around U axis (like cube rotation y).

        Args:
            n: Number of 90° rotations (positive = F→L→B→R direction).
        """
        faces = self._faces

        for _ in range(n % 4):
            self._check()
            f = faces[FaceName.F]
            faces[FaceName.F] = faces[FaceName.R]
            faces[FaceName.R] = faces[FaceName.B]
            faces[FaceName.B] = faces[FaceName.L]
            faces[FaceName.L] = f
            self._check()

    def _rotate_z(self, n: int) -> None:
        """Rotate layout around F axis (like cube rotation z).

        Args:
            n: Number of 90° rotations (positive = U→L→D→R direction).
        """
        faces = self._faces

        for _ in range(n % 4):
            self._check()
            u = faces[FaceName.U]
            faces[FaceName.U] = faces[FaceName.L]
            faces[FaceName.L] = faces[FaceName.D]
            faces[FaceName.D] = faces[FaceName.R]
            faces[FaceName.R] = u
            self._check()

    def __str__(self) -> str:
        faces: dict[FaceName, Color] = self._faces

        s = ""

        s += "-" + str(faces[FaceName.B].value) + "-" + "\n"
        s += "-" + str(faces[FaceName.U].value) + "-" + "\n"
        s += str(faces[FaceName.L].value) + str(faces[FaceName.F].value) + str(faces[FaceName.R].value) + "\n"
        s += "-" + str(faces[FaceName.D].value) + "-" + "\n"

        return s

    def __repr__(self) -> str:
        return self.__str__()

    def _check(self) -> None:
        """Verify layout sanity (if config enables it)."""
        if not self.config.check_cube_sanity:
            return

        for c in Color:
            assert self._find_face(c)

    def translate_target_from_source(self,
                                     source_face: Face,
                                     target_face: Face,
                                     source_coord: tuple[int, int],
                                     slice_name: SliceName
                                     ) -> FUnitRotation:

        def compute_unit_rotation() -> FUnitRotation:
            return source_face.cube.sized_layout.translate_target_from_source(
                source_face, target_face, source_coord, slice_name
            )

        cache_key = (source_face.name, target_face.name, slice_name)
        cache = self.cache_manager.get("CubeLayout.translate_target_from_source",
                                       FUnitRotation)

        unit_rotation = cache.compute(cache_key, compute_unit_rotation)

        return unit_rotation

    def get_face_edge_rotation_cw(self, face: Face) -> list[Edge]:
        """
        Get the four edges of a face in clockwise rotation order.

        Returns edges in the order content moves during a clockwise face rotation:
        top → right → bottom → left → (back to top)

        In LTR Coordinate System (looking at face from outside cube):
        ============================================================

                        T (top direction)
                        ↑
                        │
                ┌───────┴───────┐
                │   edge_top    │
                │               │
          L ←───│edge    edge   │───→ R (right direction)
                │_left   _right │
                │               │
                │  edge_bottom  │
                └───────┬───────┘
                        │
                        ↓
                       -T

        Clockwise rotation order: [0]=top, [1]=right, [2]=bottom, [3]=left

        When face rotates CW, content flows: T → R → (-T) → (-R) → T
        - Content at top edge moves to right edge
        - Content at right edge moves to bottom edge
        - Content at bottom edge moves to left edge
        - Content at left edge moves to top edge

        Args:
            face: The face to get edges for.

        Returns:
            List of 4 edges in clockwise order: [top, right, bottom, left]
        """
        rotation_edges: list[Edge] = [face.edge_top, face.edge_right,
                                      face.edge_bottom, face.edge_left]

        return rotation_edges

    def does_slice_cut_rows_or_columns(self, slice_name: SliceName, face_name: FaceName) -> CLGColRow:
        """Determine if a slice cuts rows or columns on a given face.

        Delegates to the SliceLayout for this slice.
        """
        return self.get_slice(slice_name).does_slice_cut_rows_or_columns(face_name)

    def create_unit_walking_info(self, slice_name: SliceName) -> UnitCubeWalkingInfo:
        """
        Create size-independent walking info for a slice.

        Uses fake n_slices to compute FUnitRotation for each face.
        The FUnitRotation is size-independent (CW0, CW1, CW2, CW3).
        """

        def compute() -> UnitCubeWalkingInfo:
            cube = self._cube
            n_slices = _FAKE_N_SLICES

            def inv(x: int) -> int:
                return n_slices - 1 - x

            # Get slice layout and rotation face
            slice_layout: SliceLayout = self.get_slice(slice_name)
            rotation_face_name = slice_layout.get_face_name()
            rotation_face = cube.face(rotation_face_name)

            # Get edges in clockwise order around rotation face
            rotation_edges = self.get_face_edge_rotation_cw(rotation_face)
            cycle_faces_ordered = [edge.get_other_face(rotation_face) for edge in rotation_edges]

            # Pick first two faces (deterministic)
            first_face = cycle_faces_ordered[0]
            second_face = cycle_faces_ordered[1]

            # Find shared edge
            shared_edge: Edge | None = first_face.get_shared_edge(second_face)
            assert shared_edge is not None

            current_face = first_face
            current_edge = shared_edge
            current_index: int = 0
            slot: int = 0

            if not slice_layout.does_slice_of_face_start_with_face(current_face.name):
                current_index = inv(current_index)

            unit_face_infos: list[UnitFaceWalkingInfo] = []
            first_reference_point: tuple[int, int] | None = None

            for _ in range(4):
                # Compute reference_point
                is_horizontal = current_face.is_bottom_or_top(current_edge)
                is_slot_inverted = (
                    current_face.is_top_edge(current_edge) if is_horizontal
                    else current_face.is_right_edge(current_edge)
                )

                if is_horizontal:
                    reference_point = (inv(slot) if is_slot_inverted else slot, current_index)
                else:
                    reference_point = (current_index, inv(slot) if is_slot_inverted else slot)

                # Compute FUnitRotation
                if first_reference_point is None:
                    first_reference_point = reference_point
                    unit_rotation = FUnitRotation.CW0
                else:
                    unit_rotation = FUnitRotation.of(
                        n_slices, first_reference_point, reference_point
                    )

                # Determine edge position
                if current_edge is current_face.edge_top:
                    edge_position = "top"
                elif current_edge is current_face.edge_bottom:
                    edge_position = "bottom"
                elif current_edge is current_face.edge_left:
                    edge_position = "left"
                else:
                    edge_position = "right"

                unit_face_infos.append(UnitFaceWalkingInfo(
                    face_name=current_face.name,
                    edge_position=edge_position,
                    unit_rotation=unit_rotation,
                ))

                # Move to next face
                if len(unit_face_infos) < 4:
                    next_face = current_edge.get_other_face(current_face)
                    next_edge: Edge = current_edge.opposite(next_face)
                    next_slice_index = current_edge.get_slice_index_from_ltr_index(
                        current_face, current_index
                    )
                    current_index = current_edge.get_ltr_index_from_slice_index(
                        next_face, next_slice_index
                    )
                    current_edge = next_edge
                    current_face = next_face

            return UnitCubeWalkingInfo(
                slice_name=slice_name,
                rotation_face=rotation_face_name,
                face_infos=tuple(unit_face_infos)
            )

        cache_key = slice_name
        cache = self._cache_manager.get("_CubeLayout.create_unit_walking_info", UnitCubeWalkingInfo)
        return cache.compute(cache_key, compute)

