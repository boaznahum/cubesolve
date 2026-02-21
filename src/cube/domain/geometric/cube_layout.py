"""CubeLayout Protocol - Interface for cube face-color layouts.

A CubeLayout represents the mapping of faces to colors on a Rubik's cube.
It also provides geometric utilities for determining face relationships
(opposite, adjacent) which are fundamental to cube operations.

The standard layout is BOY (Blue-Orange-Yellow on Front-Left-Up corner).
See cube_color_schemes.py for predefined color schemes.
"""
from __future__ import annotations

import sys
from abc import abstractmethod
from collections.abc import Collection, Iterator, Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable, Tuple, Callable

from cube.domain.geometric.cube_color_scheme import CubeColorScheme
from cube.domain.geometric.FRotation import FUnitRotation
from cube.domain.geometric.geometry_types import CLGColRow
from cube.domain.geometric.slice_layout import SliceLayout
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.model.SliceName import SliceName
from cube.domain.model._elements import AxisName, EdgePosition

if TYPE_CHECKING:
    from cube.domain.algs.WholeCubeAlg import WholeCubeAlg
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face
    from cube.domain.model.Edge import Edge
    from cube.domain.model._part import EdgeName, CornerName
    from cube.utils.config_protocol import ConfigProtocol
    from cube.utils.Cache import CacheManager
    from cube.utils.service_provider import IServiceProvider


# ============================================================================
# CubeLayout Protocol
# ============================================================================
#
# All geometry tables (_OPPOSITE, _ADJACENT, _SLICE_ROTATION_FACE, _AXIS_FACE)
# are defined in _CubeLayout.py and accessed ONLY through protocol methods.
#
# Key methods:
#   - opposite(face) → opposite face
#   - is_adjacent(f1, f2) → True if faces share an edge
#   - get_adjacent_faces(face) → tuple of 4 adjacent faces
#   - get_slice_rotation_face(slice) → face the slice rotates like (M→L, E→D, S→F)
#   - get_axis_face(axis) → face the axis rotates like (X→R, Y→U, Z→F)
#   - get_axis_for_slice(slice) → (axis, same_direction) derived relationship
# ============================================================================

@runtime_checkable
class CubeLayout(Protocol):
    """Protocol for cube face-color layout management.

    A CubeLayout maps each face (F, R, U, L, D, B) to a color.

    Usage:
        layout = cube.layout
        color = layout[FaceName.F]  # Get front face color
        opp = layout.opposite_color(Color.BLUE)  # Get color opposite to blue
        opposite_face = layout.opposite(FaceName.F)  # Returns FaceName.B
        is_adj = layout.is_adjacent(FaceName.F, FaceName.U)  # Returns True
        adjacent = layout.get_adjacent_faces(FaceName.F)  # (U, R, D, L)
    """

    _layout_cache: "dict[frozenset[tuple[FaceName, Color]], CubeLayout]" = {}

    @staticmethod
    def create_layout(
        faces: "Mapping[FaceName, Color]",
        sp: "IServiceProvider"
    ) -> "CubeLayout":
        """Create a CubeLayout from face-color mapping.

        Factory method to create layout instances without exposing
        the private implementation class.

        Layouts are cached by their face→color mapping,
        so multiple cubes with the same color scheme share one instance.

        Args:
            faces: Mapping of each face to its color.
            sp: Service provider for configuration access.

        Returns:
            CubeLayout instance with the given configuration.
        """
        from cube.domain.geometric._CubeLayout import _CubeLayout

        key = frozenset(faces.items())
        cached = CubeLayout._layout_cache.get(key)
        if cached is not None:
            return cached

        layout: CubeLayout = _CubeLayout(faces, sp)
        CubeLayout._layout_cache[key] = layout
        return layout

    @staticmethod
    def sanity_cost_assert_matches_scheme(
            cube: "Cube",
            faces: Callable[[], "Mapping[FaceName, Color]"]) -> None:
        """Assert that *faces* match the cube's original color scheme.

        Gated behind ``solver_sanity_check_is_a_boy`` config flag.
        """
        if not cube.sp.config.solver_sanity_check_is_a_boy:
            return

        face_colors = faces()
        candidate = CubeColorScheme(face_colors)

        ok = cube.original_scheme.same(candidate)

        if not ok:
            print(candidate, file=sys.stderr)

        assert ok, f"\n{candidate}"


    @property
    @abstractmethod
    def config(self) -> "ConfigProtocol":
        """Get configuration via service provider."""
        ...

    @property
    @abstractmethod
    def cache_manager(self) -> "CacheManager":
        """Get the cache manager for this layout."""
        ...

    @abstractmethod
    def __getitem__(self, face: FaceName) -> Color:
        """Get the color for a specific face.

        Args:
            face: The face to get the color for.

        Returns:
            The color assigned to that face.

        Example:
            color = layout[FaceName.F]  # Get front face color
        """
        ...

    @abstractmethod
    def get_slice(self, slice_name: SliceName) -> SliceLayout:
        """Get the slice layout for a specific slice.

        Args:
            slice_name: The slice (M, E, or S).

        Returns:
            SliceLayout for that slice.
        """
        ...

    @abstractmethod
    def colors(self) -> Collection[Color]:
        """Get all colors in this layout.

        Returns:
            Collection of all 6 face colors.
        """
        ...

    @abstractmethod
    def edge_colors(self) -> Collection[frozenset[Color]]:
        """Get all valid edge color combinations.

        An edge has exactly 2 colors, from adjacent (non-opposite) faces.

        Returns:
            Collection of frozensets, each containing 2 colors that can
            appear together on an edge piece.
        """
        ...

    @abstractmethod
    def edge_faces(self) -> dict["EdgeName", tuple[FaceName, FaceName]]:
        """Get mapping from EdgeName to the two faces it connects.

        Returns:
            Dictionary mapping each EdgeName to a tuple of (face1, face2).
            The two faces are adjacent (share an edge) and non-opposite.

        Example:
            edge_faces()[EdgeName.FU] = (FaceName.F, FaceName.U)
        """
        ...

    @abstractmethod
    def corner_faces(self) -> dict["CornerName", tuple[FaceName, FaceName, FaceName]]:
        """Get mapping from CornerName to the three faces it connects.

        Returns:
            Dictionary mapping each CornerName to a tuple of (face1, face2, face3).
            The three faces meet at a corner (all mutually adjacent).

        Example:
            corner_faces()[CornerName.FRU] = (FaceName.F, FaceName.R, FaceName.U)
        """
        ...

    @abstractmethod
    def opposite_color(self, color: Color) -> Color:
        """Get the color on the face opposite to the given color's face.

        Args:
            color: A color that appears on one of the faces.

        Returns:
            The color on the opposite face.

        Raises:
            InternalSWError: If color is not found in this layout.
        """
        ...


    @abstractmethod
    def clone(self) -> CubeLayout:
        """Create a mutable copy of this layout.

        Returns:
            A new CubeLayout with the same face-color mapping.
        """
        ...

    # =========================================================================
    # Geometry Instance Methods
    # =========================================================================

    @abstractmethod
    def opposite(self, fn: FaceName) -> FaceName:
        """Get the face opposite to the given face.

        Opposite faces never share an edge or corner. On a solved cube,
        opposite faces have complementary colors.

        Opposite pairs:
            F ↔ B (Front/Back)
            U ↔ D (Up/Down)
            L ↔ R (Left/Right)

        Args:
            fn: The face to get the opposite of.

        Returns:
            The opposite FaceName.

        Example:
            layout.opposite(FaceName.F)  # Returns FaceName.B
        """
        ...

    @abstractmethod
    def is_adjacent(self, face1: FaceName, face2: FaceName) -> bool:
        """Check if two faces are adjacent (share an edge).

        Two faces are adjacent if they are neither the same nor opposite.
        Adjacent faces share exactly one edge on the cube.

        Example:
            F and U are adjacent (share top edge of F)
            F and B are NOT adjacent (they are opposite)
            F and F are NOT adjacent (same face)

        Args:
            face1: First face.
            face2: Second face.

        Returns:
            True if faces share an edge, False otherwise.
        """
        ...

    @abstractmethod
    def get_adjacent_faces(self, face: FaceName) -> tuple[FaceName, ...]:
        """Get all faces adjacent to the given face (faces that share an edge).

        Each face has exactly 4 adjacent faces (all except itself and its opposite).

        Args:
            face: The face to get adjacent faces for.

        Returns:
            Tuple of 4 adjacent FaceNames.

        Example:
            layout.get_adjacent_faces(FaceName.F)  # (U, R, D, L)
        """
        ...

    @abstractmethod
    def get_face_neighbor(self, face_name: FaceName, position: EdgePosition) -> FaceName:
        """Get the neighboring face at a specific edge position.

        Given a face and a position (LEFT, RIGHT, TOP, BOTTOM), returns the
        face on the other side of that edge.

        Args:
            face_name: The face to get the neighbor for.
            position: Which edge position (LEFT, RIGHT, TOP, or BOTTOM).

        Returns:
            The FaceName of the neighboring face at that position.

        Example:
            layout.get_face_neighbor(FaceName.F, EdgePosition.LEFT)  # FaceName.L
            layout.get_face_neighbor(FaceName.F, EdgePosition.RIGHT)  # FaceName.R
        """
        ...

    @abstractmethod
    def get_slice_for_faces(self, source: FaceName, target: FaceName) -> SliceName | None:
        """Find which slice connects two faces.

        For opposite faces, returns only the FIRST matching slice.
        Use get_all_slices_for_faces() to get ALL connecting slices.

        Args:
            source: First face.
            target: Second face.

        Returns:
            SliceName if a slice connects the faces, None if same face.

        Example:
            layout.get_slice_for_faces(FaceName.F, FaceName.U)  # SliceName.M
        """
        ...

    @abstractmethod
    def get_all_slices_for_faces(self, source: FaceName, target: FaceName) -> list[SliceName]:
        """Find ALL slices that connect two faces.

        For adjacent faces: returns 1 slice.
        For opposite faces: returns 2 slices.

        Args:
            source: First face.
            target: Second face.

        Returns:
            List of SliceNames. Empty if faces are the same.

        Example:
            layout.get_all_slices_for_faces(FaceName.F, FaceName.B)  # [SliceName.M, SliceName.E]
        """
        ...

    @abstractmethod
    def get_slice_sandwiched_between_face_and_opposite(self, face: FaceName) -> SliceName:
        """Find the slice that is sandwiched between a face and its opposite.

        Each slice lies between two opposite faces:
        - E slice is sandwiched between U and D (horizontal slices)
        - M slice is sandwiched between L and R (vertical slices, left-right)
        - S slice is sandwiched between F and B (vertical slices, front-back)

        ASCII Diagram (side view, E slice between U and D):
        ::

                    ┌─────────────┐
                    │      U      │  ← U face
                    ├─────────────┤
                    │    E[2]     │  ← E slice index 2 (closest to U)
                    ├─────────────┤
                    │    E[1]     │  ← E slice index 1
                    ├─────────────┤
                    │    E[0]     │  ← E slice index 0 (closest to D)
                    ├─────────────┤
                    │      D      │  ← D face
                    └─────────────┘

        Args:
            face: Any face (U, D, L, R, F, or B).

        Returns:
            SliceName of the slice sandwiched between this face and its opposite:
            - U or D → SliceName.E
            - L or R → SliceName.M
            - F or B → SliceName.S

        Raises:
            GeometryError: If no matching slice found (should never happen).

        Example:
            layout.get_slice_sandwiched_between_face_and_opposite(FaceName.D)  # SliceName.E
            layout.get_slice_sandwiched_between_face_and_opposite(FaceName.L)  # SliceName.M

        Relationship with get_slice_name_parallel_to_face:
            These two methods are COMPLEMENTS - they partition the 3 slices:
            - sandwiched: returns the ONE slice whose axis includes this face
            - parallel: returns a slice whose axis does NOT include this face

            For any face, sandwiched and parallel return DIFFERENT slices.

            ::

                Face │ sandwiched │ parallel
                ─────┼────────────┼──────────
                 U   │     E      │    S
                 D   │     E      │    S
                 L   │     M      │    S
                 R   │     M      │    S
                 F   │     S      │    M
                 B   │     S      │    M
        """
        ...

    @abstractmethod
    def get_slice_name_parallel_to_face(self, face: FaceName) -> SliceName:
        """Find a slice whose axis does NOT include this face.

        NAMING NOTE: "parallel" here means the slice does NOT pass through the face,
        so rotating this slice affects the given face. This is the opposite of
        geometric parallelism (where the slice plane would be parallel to the face).

        Each slice has an axis (the two faces it's sandwiched between):
        - M: axis = L/R → does NOT include U, D, F, B
        - E: axis = U/D → does NOT include L, R, F, B
        - S: axis = F/B → does NOT include U, D, L, R

        Returns the FIRST matching slice (iteration order: S, M, E).

        Args:
            face: The face to find a non-axis slice for.

        Returns:
            SliceName of a slice whose axis does not include this face:
            - U, D, L, R → SliceName.S (first match)
            - F, B → SliceName.M (S doesn't match since F/B are on S's axis)

        Example:
            layout.get_slice_name_parallel_to_face(FaceName.U)  # SliceName.S
            layout.get_slice_name_parallel_to_face(FaceName.F)  # SliceName.M

        See Also:
            get_slice_sandwiched_between_face_and_opposite: Returns the slice whose
            axis DOES include this face (the complement of this method).
        """
        ...

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
        ...

    @abstractmethod
    def get_slice_rotation_face(self, slice_name: SliceName) -> FaceName:
        """Get the face that defines the rotation direction for a slice.

        Standard Rubik's cube slice notation:
            M - rotates like L (clockwise when looking at L face)
            E - rotates like D (clockwise when looking at D face)
            S - rotates like F (clockwise when looking at F face)

        Args:
            slice_name: The slice (M, E, or S)

        Returns:
            M → L, E → D, S → F

        Example:
            layout.get_slice_rotation_face(SliceName.M)  # FaceName.L
        """
        ...

    @abstractmethod
    def get_axis_face(self, axis_name: AxisName) -> FaceName:
        """Get the face that defines the rotation direction for a whole-cube axis.

        Standard Rubik's cube notation (https://alg.cubing.net/):

            X - Rotate entire cube on R-L axis, in the direction of R move
                (clockwise when looking at R face from outside)
                Content moves: D → F → U → B → D

            Y - Rotate entire cube on U-D axis, in the direction of U move
                (clockwise when looking at U face from outside)
                Content moves: F → L → B → R → F

            Z - Rotate entire cube on F-B axis, in the direction of F move
                (clockwise when looking at F face from outside)
                Content moves: U → R → D → L → U

        The face returned is the one that defines the positive rotation direction
        (the face that rotates clockwise when the algorithm is applied).

        TODO: This mapping could be derived from cube geometry, but keeping it
        explicit for now as it matches the standard notation convention.

        Args:
            axis_name: The axis (X, Y, or Z)

        Returns:
            X axis → R face (rotation like R, clockwise facing R)
            Y axis → U face (rotation like U, clockwise facing U)
            Z axis → F face (rotation like F, clockwise facing F)

        Example:
            layout.get_axis_face(AxisName.X)  # FaceName.R
        """
        ...

    @abstractmethod
    def get_axis_for_slice(self, slice_name: SliceName) -> tuple[AxisName, bool]:
        """Get the axis and direction relationship for a slice.

        DERIVED from:
            - _SLICE_ROTATION_FACE: which face the slice rotates like (M→L, E→D, S→F)
            - get_axis_face(): which face the axis rotates like (X→R, Y→U, Z→F)
            - opposite(): face opposite relationship

        Logic:
            Slice is on axis if slice_face and axis_face are on same axis
            (i.e., same face OR opposite faces).

            Direction is SAME if slice_face == axis_face,
            OPPOSITE if slice_face == opposite(axis_face).

        Args:
            slice_name: The slice (M, E, or S)

        Returns:
            Tuple of (axis_name, is_same_direction):
            - M → (X, False)  # M like L, X like R → opposite directions
            - E → (Y, False)  # E like D, Y like U → opposite directions
            - S → (Z, True)   # S like F, Z like F → same direction

        Example:
            axis, same_dir = layout.get_axis_for_slice(SliceName.M)
            # axis = AxisName.X, same_dir = False
        """
        ...

    @abstractmethod
    def iterate_orthogonal_face_center_pieces(
            self,
            cube: "Cube",
            layer1_face: "Face",
            side_face: "Face",
            layer_slice_index: int,
    ) -> Iterator[tuple[int, int]]:
        """
        Yield (row, col) positions on side_face for the given layer slice.

        A "layer slice" is a horizontal layer parallel to layer1_face (L1).
        Layer slice 0 is the one closest to L1.

        Args:
            cube: The cube (for n_slices)
            layer1_face: The Layer 1 face (base layer, e.g., white face)
            side_face: A face orthogonal to layer1_face
            layer_slice_index: 0 = closest to L1, n_slices-1 = farthest

        Yields:
            (row, col) in LTR coordinates on side_face

        Raises:
            ValueError: if side_face is not orthogonal to layer1_face

        Example 1: L1=DOWN, side_face=FRONT, 5x5 cube (n_slices=3)
        =========================================================

            Looking at FRONT face:

                      U
                ┌───┬───┬───┐
            row2│   │   │   │  ← layer_slice_index=2 (closest to U)
                ├───┼───┼───┤
            row1│   │   │   │  ← layer_slice_index=1
                ├───┼───┼───┤
            row0│ * │ * │ * │  ← layer_slice_index=0 (closest to D=L1)
                └───┴───┴───┘
                      D (L1)

            layer_slice_index=0 yields: (0,0), (0,1), (0,2)

        Example 2: L1=LEFT, side_face=FRONT, 5x5 cube (n_slices=3)
        ==========================================================

            Looking at FRONT face:

                L1        R
                (L)
                ┌───┬───┬───┐
                │ * │   │   │  row2
                ├───┼───┼───┤
                │ * │   │   │  row1
                ├───┼───┼───┤
                │ * │   │   │  row0
                └───┴───┴───┘
                col0 col1 col2

                ↑ layer_slice_index=0 (closest to L=L1)

            layer_slice_index=0 yields: (0,0), (1,0), (2,0)

        Example 3: L1=UP, side_face=FRONT, 5x5 cube (n_slices=3)
        =========================================================

            Looking at FRONT face:

                      U (L1)
                ┌───┬───┬───┐
            row2│ * │ * │ * │  ← layer_slice_index=0 (closest to U=L1)
                ├───┼───┼───┤
            row1│   │   │   │  ← layer_slice_index=1
                ├───┼───┼───┤
            row0│   │   │   │  ← layer_slice_index=2 (closest to D)
                └───┴───┴───┘
                      D

            layer_slice_index=0 yields: (2,0), (2,1), (2,2)
        """
        ...


    def translate_target_from_source(
            self,
            source_face: Face,
            target_face: Face,
            source_coord: tuple[int, int],
            slice_name: SliceName
    ) -> FUnitRotation:
        """
        Find the coordinate on target_face where content from source_face will move to.

        Given a position on the source face where we have content,
        find the corresponding position on the target face where that content
        will appear after applying a movement algorithm.

        This is the inverse operation of translate_source_from_target():
        If translate_source_from_target(TF, SF, tc) returns sc,
        then translate_target_from_source(SF, TF, sc) returns tc.

        Uses geometric derivation based on Slice traversal logic:
        - Uses the provided slice_name to determine traversal path
        - Uses edge-based coordinate translation (like Slice._get_slices_by_index)
        - Caches the derived FUnitRotation for efficiency

        Args:
            source_face: Where content currently is
            target_face: Where we want to know where content will go
            source_coord: (row, col) position on source_face (0-indexed)
            slice_name: Which slice (M, E, S) connects the faces

        Returns:
            (row, col) on target_face where the content will appear.

        Raises:
            ValueError: If source_face == target_face (no translation needed)
            ValueError: If source_coord is out of bounds for cube size

        Example::

            # I have content at (1, 2) on Right face, where will it go on Front face?
            target_coord = Face2FaceTranslator.translate_target_from_source(
                cube.right, cube.front, (1, 2), SliceName.E
            )
        """
        ...

    def get_face_edge_rotation_cw(self, face: "Face") -> list["Edge"]:
        """
        Get the four edges of a face in clockwise rotation order.

        Returns edges in the order content moves during a clockwise face rotation:
        top → right → bottom → left → (back to top)

        IMPORTANT - Object Ownership:
            This method accepts a Face object from the CALLER'S cube and returns
            Edge objects from that SAME cube. It does NOT expose internal objects.
            The returned edges belong to face.cube, not to any internal cube.

        In LTR Coordinate System (looking at face from outside cube):

                        top edge
                    ┌───────────────┐
                    │               │
            left    │     FACE      │    right
            edge    │               │    edge
                    │               │
                    └───────────────┘
                        bottom edge

        Args:
            face: A Face object from the caller's cube

        Returns:
            List of 4 Edge objects from face.cube: [top, right, bottom, left]
        """
        ...

    @abstractmethod
    def get_face_neighbors_cw(self, face: "Face") -> list["Face"]:
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
            # Get neighbors of Front face
            neighbors = layout.get_face_neighbors_cw(cube.front)
            # neighbors = [cube.up, cube.right, cube.down, cube.left]
        """
        ...

    @abstractmethod
    def get_face_neighbors_cw_names(self, face_name: FaceName) -> list[FaceName]:
        """
        Get the four neighboring face NAMES in clockwise rotation order.

        Same as get_face_neighbors_cw() but works with FaceNames only,
        without requiring a Cube instance. Useful for static/pure topology queries.

        Args:
            face_name: The face to get neighbors for

        Returns:
            List of 4 FaceNames: [top, right, bottom, left] neighbors

        Example:
            neighbors = layout.get_face_neighbors_cw_names(FaceName.F)
            # neighbors = [FaceName.U, FaceName.R, FaceName.D, FaceName.L]
        """
        ...

    @abstractmethod
    def does_slice_cut_rows_or_columns(self, slice_name: SliceName, face_name: FaceName) -> CLGColRow:
        """
        Determine if a slice cuts rows or columns on a given face.

        This is a template-level geometry question - the answer depends only on
        the slice type and face, not on a specific cube instance.

        Slice Traversal (content movement during rotation):
            M: F → U → B → D → F  (vertical cycle, like L rotation)
            E: R → B → L → F → R  (horizontal cycle, like D rotation)
            S: U → R → D → L → U  (around F/B axis, like F rotation)

        Args:
            slice_name: Which slice (M, E, or S)
            face_name: Which face to check

        Returns:
            CLGColRow.ROW if slice cuts through rows (forms vertical strips)
            CLGColRow.COL if slice cuts through columns (forms horizontal strips)

        Example:
            M slice on Front face cuts columns (vertical strips) → returns ROW
            E slice on Front face cuts rows (horizontal strips) → returns COL
        """
        ...

    @abstractmethod
    def get_bring_face_alg(self, target: FaceName, source: FaceName) -> "WholeCubeAlg":
        """
        Get the whole-cube rotation algorithm to bring source face to target position.

        This is a size-independent operation - the algorithm is the same for
        3x3, 5x5, or any cube size.

        Results are cached since they are pure topology.

        Args:
            target: The target face position (e.g., FaceName.U)
            source: The source face to move (e.g., FaceName.F)

        Returns:
            Whole-cube rotation algorithm (e.g., Algs.X, Algs.Y * 2)

        Raises:
            GeometryError: If source == target (SAME_FACE code)

        Example:
            alg = layout.get_bring_face_alg(FaceName.U, FaceName.F)  # Returns Algs.X
            alg = layout.get_bring_face_alg(FaceName.D, FaceName.U)  # Returns Algs.X * 2
        """
        ...

    @abstractmethod
    def get_bring_face_alg_preserve(
        self, target: FaceName, source: FaceName, preserve: FaceName
    ) -> "WholeCubeAlg":
        """Get whole-cube rotation to bring source to target while preserving a face.

        Uses constrained rotation - only the axis that keeps preserve fixed:
        - Preserve F or B: uses Z rotation (moves L, U, R, D)
        - Preserve U or D: uses Y rotation (moves R, F, L, B)
        - Preserve L or R: uses X rotation (moves D, F, U, B)

        Filters results from derive_whole_cube_alg to find the one that preserves
        the requested face (axis name matches preserve face or its opposite).

        Args:
            target: The target face position
            source: The source face to move
            preserve: The face that must stay fixed

        Returns:
            Whole-cube rotation algorithm using the constrained axis

        Raises:
            GeometryError: SAME_FACE if source == target
            GeometryError: INVALID_PRESERVE_ROTATION if no valid rotation exists
        """
        ...





