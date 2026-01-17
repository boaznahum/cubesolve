"""Cube layout implementation."""

from __future__ import annotations

from collections.abc import Collection, Iterator
from typing import TYPE_CHECKING, Mapping, Tuple

from cube.domain.exceptions import GeometryError, GeometryErrorCode, InternalSWError
from cube.domain.geometric.Face2FaceTranslator import Face2FaceTranslator
from cube.domain.geometric.FRotation import FUnitRotation
from cube.domain.model.Edge import Edge
from cube.domain.model.SliceName import SliceName
from cube.domain.geometric.cube_layout import CubeLayout
from cube.domain.geometric.geometry_types import CLGColRow
from cube.domain.geometric.slice_layout import SliceLayout, _SliceLayout
from cube.utils.config_protocol import ConfigProtocol
from cube.utils.service_provider import IServiceProvider
from cube.utils.Cache import CacheManager, cached_result

from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.model._elements import AxisName, EdgePosition

# ============================================================================
# PRIVATE GEOMETRY TABLES - Only accessed through CubeLayout methods
# ============================================================================

# Opposite face pairs (canonical direction)
_OPPOSITE: dict[FaceName, FaceName] = {
    FaceName.F: FaceName.B,
    FaceName.U: FaceName.D,
    FaceName.L: FaceName.R,
}

# Reverse mapping
_REV_OPPOSITE: dict[FaceName, FaceName] = {v: k for k, v in _OPPOSITE.items()}

# Bidirectional opposite mapping
_ALL_OPPOSITE: dict[FaceName, FaceName] = {**_OPPOSITE, **_REV_OPPOSITE}

# Adjacent faces (derived from opposite)
_ADJACENT: dict[FaceName, tuple[FaceName, ...]] = {
    face: tuple(f for f in FaceName if f != face and f != _ALL_OPPOSITE[face])
    for face in FaceName
}

# Slice rotation faces: which face each slice rotates like
_SLICE_ROTATION_FACE: dict[SliceName, FaceName] = {
    SliceName.M: FaceName.L,
    SliceName.E: FaceName.D,
    SliceName.S: FaceName.F,
}

# Axis rotation faces: which face each axis rotates like
_AXIS_FACE: dict[AxisName, FaceName] = {
    AxisName.X: FaceName.R,
    AxisName.Y: FaceName.U,
    AxisName.Z: FaceName.F,
}


if TYPE_CHECKING:
    from cube.domain.algs.WholeCubeAlg import WholeCubeAlg
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
            SliceName.S: _SliceLayout(SliceName.S, self, sp),
            SliceName.E: _SliceLayout(SliceName.E, self, sp),
            SliceName.M: _SliceLayout(SliceName.M, self, sp),
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

    def get_face_neighbor(self, face_name: FaceName, position: EdgePosition) -> FaceName:
        """Get the neighboring face at a specific edge position.

        Uses the internal 3x3 cube to traverse face-edge relationships.
        """
        face = self._cube.face(face_name)
        edge = face.get_edge(position)
        return edge.get_other_face(face).name

    def get_slice_for_faces(self, source: FaceName, target: FaceName) -> SliceName | None:
        """Find which slice connects two faces."""
        for slice_name in SliceName:
            rotation_face = _SLICE_ROTATION_FACE[slice_name]
            slice_faces = _ADJACENT[rotation_face]
            if source in slice_faces and target in slice_faces:
                return slice_name
        return None

    def get_all_slices_for_faces(self, source: FaceName, target: FaceName) -> list[SliceName]:
        """Find ALL slices that connect two faces."""
        if source == target:
            return []
        result: list[SliceName] = []
        for slice_name in SliceName:
            rotation_face = _SLICE_ROTATION_FACE[slice_name]
            slice_faces = _ADJACENT[rotation_face]
            if source in slice_faces and target in slice_faces:
                result.append(slice_name)
        return result

    def get_slice_sandwiched_between_face_and_opposite(self, face: FaceName) -> SliceName:
        """Find the slice sandwiched between a face and its opposite.

        See CubeLayout.get_slice_sandwiched_between_face_and_opposite() for full documentation.
        """
        for slice_name in SliceName:
            rotation_face, opposite_face = self.get_slice_rotation_faces(slice_name)
            if face in (rotation_face, opposite_face):
                return slice_name

        raise GeometryError(GeometryErrorCode.INVALID_FACE, f"No slice sandwiched by {face}")




    def get_slice_name_parallel_to_face(self, face: FaceName) -> SliceName:
        """Find which slice is parallel to a face."""
        for slice_name in SliceName:
            rotation_face = _SLICE_ROTATION_FACE[slice_name]
            opposite_face = _ALL_OPPOSITE[rotation_face]
            if face not in (rotation_face, opposite_face):
                return slice_name
        raise ValueError(f"No slice parallel to {face}")

    def get_slice_rotation_faces(self, slice_name: SliceName) -> Tuple[FaceName, FaceName]:
        """
        claude: document his, return the two faces that parallel to slice, the rotation face in its
        opposite face
        see get_slice_rotation_face
        claude: this is SliceLayout method, need to resolve and delegate

        :param slice_name:
        :return:
        """
        return self.get_slice(slice_name).get_slice_rotation_faces()

    def get_slice_rotation_face(self, slice_name: SliceName) -> FaceName:
        """Get the face that defines the rotation direction for a slice.

        See CubeLayout.get_slice_rotation_face() for full documentation.

        cluade: this is SliceLayout method, need to resolve and delegate
        """
        return _SLICE_ROTATION_FACE[slice_name]

    def get_axis_face(self, axis_name: AxisName) -> FaceName:
        """Get the face that defines the rotation direction for a whole-cube axis.

        See CubeLayout.get_axis_face() for full documentation.
        """
        return _AXIS_FACE[axis_name]

    def get_axis_for_slice(self, slice_name: SliceName) -> tuple[AxisName, bool]:
        """Get the axis and direction relationship for a slice.

        DERIVED from _SLICE_ROTATION_FACE, get_axis_face(), and opposite().
        See CubeLayout.get_axis_for_slice() for full documentation.
        """
        slice_face = _SLICE_ROTATION_FACE[slice_name]  # M→L, E→D, S→F

        for axis_name in AxisName:
            axis_face = self.get_axis_face(axis_name)  # X→R, Y→U, Z→F

            if slice_face == axis_face:
                # Same face → same direction (S and Z both use F)
                return (axis_name, True)
            elif self.opposite(slice_face) == axis_face:
                # Opposite faces → opposite directions (M uses L, X uses R)
                return (axis_name, False)

        raise ValueError(f"No axis found for slice {slice_name}")

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

        cache_key = ("CubeLayout.translate_target_from_source", source_face.name, target_face.name, slice_name)
        cache = self.cache_manager.get(cache_key, FUnitRotation)

        unit_rotation = cache.compute(compute_unit_rotation)

        return unit_rotation

    def get_face_edge_rotation_cw(self, face: Face) -> list[Edge]:
        """
        Get the four edges of a face in clockwise rotation order.

        Returns edges in the order content moves during a clockwise face rotation:
        top → right → bottom → left → (back to top)

        IMPORTANT - Object Ownership:
            This method accepts a Face object from the CALLER'S cube and returns
            Edge objects from that SAME cube. It does NOT expose internal objects.
            The returned edges belong to face.cube, not to any internal cube.

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
            face: A Face object from the caller's cube

        Returns:
            List of 4 Edge objects from face.cube: [top, right, bottom, left]
        """
        rotation_edges: list[Edge] = [face.edge_top, face.edge_right,
                                      face.edge_bottom, face.edge_left]

        return rotation_edges

    def get_face_neighbors_cw(self, face: Face) -> list[Face]:
        """
        Get the four neighboring faces in clockwise rotation order.

        Returns the faces adjacent to the given face, in the order they appear
        when rotating clockwise around the face (viewing from outside the cube).

        IMPORTANT - Object Ownership:
            This method accepts a Face object from the CALLER'S cube and returns
            Face objects from that SAME cube. It does NOT expose internal objects.
            The returned faces belong to face.cube, not to any internal cube.

        Relationship to edges:
            The neighbor faces correspond to the edges returned by get_face_edge_rotation_cw():
            - neighbors[0] is across edge[0] (top edge)
            - neighbors[1] is across edge[1] (right edge)
            - neighbors[2] is across edge[2] (bottom edge)
            - neighbors[3] is across edge[3] (left edge)

        In LTR Coordinate System (looking at face from outside cube):

                    ┌───────────────┐
                    │  neighbor[0]  │  (top neighbor)
                    │               │
                    └───────┬───────┘
                            │
            ┌───────┐ ┌─────┴─────┐ ┌───────┐
            │ [3]   │ │           │ │  [1]  │
            │ left  │─│   FACE    │─│ right │
            │       │ │           │ │       │
            └───────┘ └─────┬─────┘ └───────┘
                            │
                    ┌───────┴───────┐
                    │  neighbor[2]  │  (bottom neighbor)
                    │               │
                    └───────────────┘

        Args:
            face: A Face object from the caller's cube

        Returns:
            List of 4 Face objects from face.cube: [top, right, bottom, left]

        Example:
            neighbors = layout.get_face_neighbors_cw(cube.front)
            # neighbors = [cube.up, cube.right, cube.down, cube.left]
        """
        edges = self.get_face_edge_rotation_cw(face)
        return [edge.get_other_face(face) for edge in edges]

    def get_face_neighbors_cw_names(self, face_name: FaceName) -> list[FaceName]:
        """Get the four neighboring face NAMES in clockwise rotation order."""
        face = self._cube.face(face_name)
        neighbors = self.get_face_neighbors_cw(face)
        return [n.name for n in neighbors]

    def does_slice_cut_rows_or_columns(self, slice_name: SliceName, face_name: FaceName) -> CLGColRow:
        """Determine if a slice cuts rows or columns on a given face.

        Delegates to the SliceLayout for this slice.
        """
        return self.get_slice(slice_name).does_slice_cut_rows_or_columns(face_name)

    @cached_result
    def get_bring_face_alg(self, target: FaceName, source: FaceName) -> "WholeCubeAlg":
        """Get the whole-cube rotation algorithm to bring source face to target position.

        This is a size-independent operation - results are cached.

        Uses Face2FaceTranslator.derive_whole_cube_alg internally.
        """
        from cube.domain.algs.WholeCubeAlg import WholeCubeAlg

        if source == target:
            raise GeometryError(
                GeometryErrorCode.SAME_FACE,
                f"Cannot bring {source} to itself"
            )

        def compute_alg() -> WholeCubeAlg:
            results = Face2FaceTranslator.derive_whole_cube_alg(self, target, source)
            # Take first solution (for adjacent faces there's only one,
            # for opposite faces we pick the first available)
            _base_alg, _steps, alg = results[0]
            return alg  # type: ignore[return-value]

        cache_key = ("CubeLayout.get_bring_face_alg", target, source)
        cache = self.cache_manager.get(cache_key, WholeCubeAlg)
        return cache.compute(compute_alg)

    @cached_result
    def get_bring_face_alg_preserve(
        self, target: FaceName, source: FaceName, preserve: FaceName
    ) -> "WholeCubeAlg":
        """Get whole-cube rotation to bring source to target while preserving a face.

        Filters derive_whole_cube_alg results to find the axis that preserves
        the requested face.
        """
        from cube.domain.algs.WholeCubeAlg import WholeCubeAlg

        if source == target:
            raise GeometryError(
                GeometryErrorCode.SAME_FACE,
                f"Cannot bring {source} to itself"
            )

        def compute_alg() -> WholeCubeAlg:
            try:
                results = Face2FaceTranslator.derive_whole_cube_alg(self, target, source)
            except ValueError:
                # No rotation connects source and target at all
                raise GeometryError(
                    GeometryErrorCode.INVALID_PRESERVE_ROTATION,
                    f"Cannot bring {source} to {target} while preserving {preserve}"
                )

            # Find the algorithm that uses an axis preserving the requested face
            # Each axis preserves two opposite faces (the axis goes through them)
            # get_axis_face() returns one of them, opposite() gives the other
            for base_alg, _steps, alg in results:
                axis_face = self.get_axis_face(base_alg.axis_name)
                axis_opposite = self.opposite(axis_face)
                if preserve == axis_face or preserve == axis_opposite:
                    return alg  # type: ignore[return-value]

            # No algorithm preserves the requested face
            raise GeometryError(
                GeometryErrorCode.INVALID_PRESERVE_ROTATION,
                f"Cannot bring {source} to {target} while preserving {preserve}"
            )

        cache_key = ("CubeLayout.get_bring_face_alg_preserve", target, source, preserve)
        cache = self.cache_manager.get(cache_key, WholeCubeAlg)
        return cache.compute(compute_alg)

