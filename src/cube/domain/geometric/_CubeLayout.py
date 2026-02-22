"""Cube layout implementation."""

from __future__ import annotations

from collections.abc import Collection, Iterator
from typing import TYPE_CHECKING, Mapping, Tuple

from cube.domain.exceptions import GeometryError, GeometryErrorCode, InternalSWError
from cube.domain.geometric.Face2FaceTranslator import Face2FaceTranslator
from cube.domain.geometric.FRotation import FUnitRotation
from cube.domain.geometric.cube_color_scheme import CubeColorScheme
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

from cube.domain.geometric.schematic_cube import SchematicCube

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
    from cube.domain.model._part import EdgeName, CornerName


class _CubeLayout(CubeLayout):
    """Concrete implementation of CubeLayout protocol.

    Manages a mapping of faces to colors, with support for:
    - Read-only layouts (like the BOY singleton)
    - Mutable layouts for comparison/manipulation
    - Geometric operations (opposite, adjacent faces)

    Color-scheme logic (face↔color lookup, comparison, rotation)
    is delegated to the contained ``CubeColorScheme``.
    """

    __slots__ = (
        "_color_scheme",
        "_sp",
        "_cache_manager",
        "_slices",
        "_internal_cube",
        "_creating_internal_cube",
        "_scheme",
    )

    def __init__(self, faces: Mapping[FaceName, Color],
                 sp: IServiceProvider) -> None:
        """Create a new CubeLayout.

        Args:
            faces: Mapping of each face to its color.
            sp: Service provider for configuration access.
        """
        self._color_scheme = CubeColorScheme(faces)
        self._sp = sp
        self._cache_manager = CacheManager.create(sp.config)
        self._scheme: SchematicCube = SchematicCube.inst()

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
        finally:
            self._creating_internal_cube = False

        return self._internal_cube

    # ------------------------------------------------------------------
    # Delegated to CubeColorScheme
    # ------------------------------------------------------------------

    def colors_schema(self) -> CubeColorScheme:
        return self._color_scheme

    def colors(self) -> Collection[Color]:
        """Get all colors in this layout."""
        return self._color_scheme.colors()

    def edge_colors(self) -> Collection[frozenset[Color]]:
        """Get all valid edge color combinations."""
        return self._color_scheme.edge_colors()

    def opposite_color(self, color: Color) -> Color:
        """Get the color on the face opposite to the given color's face."""
        return self._color_scheme.opposite_color(color)


    def clone(self) -> _CubeLayout:
        """Create a copy of this layout."""
        return _CubeLayout(self._color_scheme._faces, self._sp)

    # ------------------------------------------------------------------
    # Geometry (delegated to SchematicCube)
    # ------------------------------------------------------------------

    def get_slice(self, slice_name: SliceName) -> SliceLayout:
        return self._slices[slice_name]

    def edge_faces(self) -> dict["EdgeName", tuple[FaceName, FaceName]]:
        """Get mapping from EdgeName to the two faces it connects."""
        return self._scheme.edge_faces()

    def corner_faces(self) -> dict["CornerName", tuple[FaceName, FaceName, FaceName]]:
        """Get mapping from CornerName to the three faces it connects."""
        return self._scheme.corner_faces()

    def opposite(self, fn: FaceName) -> FaceName:
        """Get the face opposite to the given face."""
        return self._scheme.opposite(fn)

    def is_adjacent(self, face1: FaceName, face2: FaceName) -> bool:
        """Check if two faces are adjacent (share an edge)."""
        return self._scheme.is_adjacent(face1, face2)

    def get_adjacent_faces(self, face: FaceName) -> tuple[FaceName, ...]:
        """Get all faces adjacent to the given face."""
        return self._scheme.get_adjacent_faces(face)

    def get_face_neighbor(self, face_name: FaceName, position: EdgePosition) -> FaceName:
        """Get the neighboring face at a specific edge position."""
        return self._scheme.get_face_neighbor(face_name, position)

    def get_slice_for_faces(self, source: FaceName, target: FaceName) -> SliceName | None:
        """Find which slice connects two faces."""
        for slice_name in SliceName:
            rotation_face = _SLICE_ROTATION_FACE[slice_name]
            slice_faces = self._scheme.get_adjacent_faces(rotation_face)
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
            slice_faces = self._scheme.get_adjacent_faces(rotation_face)
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
            opposite_face = self._scheme.opposite(rotation_face)
            if face not in (rotation_face, opposite_face):
                return slice_name
        raise ValueError(f"No slice parallel to {face}")

    def get_slice_rotation_faces(self, slice_name: SliceName) -> Tuple[FaceName, FaceName]:
        """
        Get the two faces that the slice is parallel to.

        Args:
            slice_name: Which slice (M, E, or S)

        Returns:
            A tuple of (rotation_face, opposite_face):
            - rotation_face: The face that defines the slice's rotation direction
            - opposite_face: The face opposite to rotation_face

            Examples:
                M slice → (L, R) - parallel to L and R, rotates like L
                E slice → (D, U) - parallel to D and U, rotates like D
                S slice → (F, B) - parallel to F and B, rotates like F
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

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return str(self._color_scheme)

    def __repr__(self) -> str:
        return self.__str__()

    # ------------------------------------------------------------------
    # Face translation / edge geometry
    # ------------------------------------------------------------------

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
        return self._scheme.get_face_neighbors_cw_names(face_name)

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
                    return alg.simplify()  # type: ignore[return-value]

            # No algorithm preserves the requested face
            raise GeometryError(
                GeometryErrorCode.INVALID_PRESERVE_ROTATION,
                f"Cannot bring {source} to {target} while preserving {preserve}"
            )

        cache_key = ("CubeLayout.get_bring_face_alg_preserve", target, source, preserve)
        cache = self.cache_manager.get(cache_key, WholeCubeAlg)
        return cache.compute(compute_alg)
