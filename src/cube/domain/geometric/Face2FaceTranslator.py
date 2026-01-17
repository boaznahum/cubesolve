"""
Face2FaceTranslator - Central API for face-to-face coordinate translation.

Documentation: docs/face-coordinate-system/Face2FaceTranslator.md

Replaces scattered methods in Edge.py, Face.py, and Slice.py:
- Edge.get_slice_index_from_ltr_index()
- Edge.get_ltr_index_from_slice_index()
- Face.is_bottom_or_top() for axis detection
- Slice navigation logic

DEFINITION:
    translate(target_face, source_face, target_coord) returns a FaceTranslationResult with:

    - source_coord: Position on source_face where the content originates
    - whole_cube_alg: Algorithm (X/Y/Z) that brings source_face content to target_face
    - slice_algorithms: Algorithm(s) (M/E/S) that bring content from source to target

    USAGE CONTRACT:
        1. Place a marker at source_coord on source_face
        2. Apply any of the returned algorithms (whole_cube_alg or slice_algorithms)
        3. The marker will appear at target_coord on target_face

    This is the SINGLE definition that all algorithms must satisfy.

NAMING CONVENTION:
    - target_face: Where content should ARRIVE
    - source_face: Where content COMES FROM
    - target_coord: Position on target where we want content
    - source_coord: Position on source where content originates

================================================================================
SLICE ALGORITHMS (M, E, S) - COMPREHENSIVE REFERENCE
================================================================================

SLICE DEFINITIONS:
    Each slice rotates the middle layer(s) between two opposite faces.
    The rotation direction is defined by a "reference face".

    ┌──────┬────────────┬────────────────┬───────────────────────────────────────┐
    │Slice │   Axis     │ Affects Faces  │ Rotation Direction                    │
    ├──────┼────────────┼────────────────┼───────────────────────────────────────┤
    │  M   │  L ↔ R     │  F, U, B, D    │ Like L (clockwise when viewing L)     │
    │  E   │  U ↔ D     │  F, R, B, L    │ Like D (clockwise when viewing D)     │
    │  S   │  F ↔ B     │  U, R, D, L    │ Like F (clockwise when viewing F)     │
    └──────┴────────────┴────────────────┴───────────────────────────────────────┘

    API: Algs.M.get_face_name() → L, Algs.E.get_face_name() → D, Algs.S.get_face_name() → F

SLICE TRAVERSAL (content movement during rotation):
    M: F → U → B → D → F  (vertical cycle, like L rotation)
    E: R → B → L → F → R  (horizontal cycle, like D rotation)
    S: U → R → D → L → U  (around F/B axis, like F rotation)

SLICE INDEXING (1-based):
    Slice indices are 1-based, ranging from 1 to n_slices (where n_slices = cube_size - 2).

    For an NxN cube:
        - n_slices = N - 2 (number of inner slices)
        - Valid indices: 1, 2, ..., n_slices

    Example for 5x5 cube (n_slices = 3):
        E[1]  - first inner slice (closest to D face)
        E[2]  - middle slice
        E[3]  - last inner slice (closest to U face)
        E     - all slices together

    WHERE SLICE 1 BEGINS (same side as reference face):
        ┌──────┬─────────────────────────────────────────────────────────────────┐
        │Slice │ Slice[1] is closest to...                                       │
        ├──────┼─────────────────────────────────────────────────────────────────┤
        │  M   │ Closest to L face (the reference face for M)                    │
        │  E   │ Closest to D face (the reference face for E)                    │
        │  S   │ Closest to F face (the reference face for S)                    │
        └──────┴─────────────────────────────────────────────────────────────────┘

    Visual for 5x5 cube (E slice example, viewing from front):
                         U face
                    ┌─────────────┐
                    │             │
            E[3] →  ├─────────────┤  ← closest to U
            E[2] →  ├─────────────┤  ← middle
            E[1] →  ├─────────────┤  ← closest to D
                    │             │
                    └─────────────┘
                         D face

RELATIONSHIP TO WHOLE-CUBE ROTATIONS (X, Y, Z):
    ┌──────┬─────────────────┬────────────────────────────────────────────────────┐
    │Whole │ Implementation  │ Rotation Direction                                 │
    ├──────┼─────────────────┼────────────────────────────────────────────────────┤
    │  X   │ M' + R + L'     │ Like R (clockwise facing R) - OPPOSITE of M's L!   │
    │  Y   │ E' + U + D'     │ Like U (clockwise facing U) - OPPOSITE of E's D!   │
    │  Z   │ S + F + B'      │ Like F (clockwise facing F) - SAME as S's F!       │
    └──────┴─────────────────┴────────────────────────────────────────────────────┘

    Direction Relationship (used in _compute_slice_algorithms):
        - M.face (L) is OPPOSITE to X.face (R) → M and X rotate opposite directions
        - E.face (D) is OPPOSITE to Y.face (U) → E and Y rotate opposite directions
        - S.face (F) is SAME as Z.face (F) → S and Z rotate same direction

================================================================================

IMPLEMENTATION:
    Transforms between faces are computed using FUnitRotation (CW0, CW1, CW2, CW3)
    representing 0°, 90°CW, 180°, and 90°CCW rotations respectively.
    The translation is derived from slice traversal geometry using CubeWalkingInfo.

    See: docs/face-coordinate-system/images/right-top-left-coordinates.jpg
    for the face coordinate system diagram (R = column direction, T = row direction).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple

from cube.application.exceptions.ExceptionInternalSWError import InternalSWError
from cube.domain.algs.Alg import Alg
from cube.domain.algs.Algs import Algs
from cube.domain.algs.WholeCubeAlg import WholeCubeAlg
from cube.domain.algs.SliceAlg import SliceAlg
from cube.domain.geometric.types import Point
from cube.domain.model import Cube
from cube.domain.model.Slice import Slice
from cube.domain.model._elements import AxisName
if TYPE_CHECKING:
    from cube.domain.model.Face import Face
    from cube.domain.model.Edge import Edge
    from cube.domain.geometric.cube_layout import CubeLayout

from cube.domain.model.FaceName import FaceName
from cube.domain.model.cube_slice import SliceName


@dataclass(frozen=True)
class FaceTranslationResult:
    """
    Result of translating a coordinate from target face to source face.

    Each result corresponds to ONE whole-cube rotation and its matching slice.
    For opposite faces, translate_source_from_target returns multiple results
    (one per valid rotation axis).

    Attributes:
        whole_cube_base_alg: Base rotation (X, Y, or Z)
        whole_cube_alg: Full algorithm (e.g., X2 for opposite faces)

        slice_algorithm: The slice algorithm (M/E/S) that matches this whole-cube
                        rotation. Contains source_coord for this specific translation.

        shared_edge: Edge connecting target and source faces.
                    - Not None: faces are adjacent (share this edge)
                    - None: faces are opposite (F↔B, U↔D, L↔R)

    USAGE CONTRACT:
        1. Use slice_algorithm.source_coord on source_face
        2. Apply the slice algorithm
        3. Marker appears at target_coord on target_face

    Example::

        # I want content at (1, 2) on Front, coming from Up
        results = translator.translate_source_from_target(cube.front, cube.up, (1, 2))
        result = results[0]  # Pick first (for adjacent faces, there's only one)
        # result.slice_algorithm.source_coord = position on Up face
        # result.whole_cube_alg = X' (brings Up to Front)
    """

    whole_cube_base_alg: WholeCubeAlg
    whole_cube_alg: Alg
    slice_algorithm: SliceAlgorithmResult
    shared_edge: Edge | None

    @property
    def is_adjacent(self) -> bool:
        """True if faces share an edge, False if opposite."""
        return self.shared_edge is not None


@dataclass(frozen=True)
class SliceAlgorithmResult:
    """
    Result of computing a slice algorithm for face-to-face translation.

    Attributes:
        whole_slice_alg: The base slice algorithm (M, E, or S) without indexing
        on_slice: 1-based slice index (see SliceAbleAlg for indexing convention)
        n: Number of rotations (positive = clockwise, negative = counter-clockwise)
        source_coord: Position on source_face where content originates for THIS slice.
                     Each slice may have a different source_coord because it traverses
                     a different path between faces.

    Note on slice indexing:
        Slice indices are 1-based in the public API: E[1], E[2], ..., E[n_slices]
        This matches the convention in SliceAbleAlg where slices are "[1, n]" space.
        See SliceAbleAlg.normalize_slice_index() which converts to 0-based internally.
    """
    whole_slice_alg: SliceAlg  # not sliced

    _on_slice: int  # 0-based slice index
    n: int  # n rotations
    source_coord: tuple[int, int]  # Position on source face for this slice algorithm

    @property
    def on_slice(self) -> int:
        """Return 0-based slice index."""
        return self._on_slice

    def get_alg(self) -> Alg:
        return self.get_slice_alg(self.on_slice)

    def get_whole_slice_alg(self) -> Alg:
        return self.whole_slice_alg * self.n

    def get_slice_alg(self, slice_index: int) -> Alg:
        """

        :param slice_index:  zero based !!!
        :return:
        """
        return self.whole_slice_alg[slice_index + 1] * self.n






# =============================================================================
# ROTATION CYCLES - Empirically derived from whole-cube rotations
# =============================================================================
#
# Each cycle lists faces in the direction content MOVES when applying the base alg.
# After the rotation, content at cycle[i] appears at cycle[i+1].
#
# Empirical observations:
#   X: D→F→U→B→D (D's content moves to F, F's to U, etc.)
#   Y: R→F→L→B→R (R's content moves to F, F's to L, etc.) - NOTE: opposite direction!
#   Z: L→U→R→D→L (L's content moves to U, U's to R, etc.)
class Face2FaceTranslator:
    """
    Utility class for translating coordinates between cube faces.

    This is the ONE place that handles all face-to-face coordinate operations,
    ensuring consistency with the viewer-perspective definition.

    DEFINITION:
        translate(F, R, (row, col)) → (row', col') means:
        If you mark (row, col) on F and (row', col') on R, then apply Y' (R→F),
        both markers appear at the same screen position.

    IMPLEMENTATION:
        Uses rotation cycle analysis to derive whole-cube algorithms dynamically.
    """

    @staticmethod
    def derive_whole_cube_alg(
            layout: "CubeLayout",
            source: FaceName,
            dest: FaceName
    ) -> list[Tuple[WholeCubeAlg, int, Alg]]:
        """
        Derive whole-cube algorithm(s) that bring dest to source's screen position.

        For adjacent faces: returns 1 algorithm (single rotation X/Y/Z)
        For opposite faces: returns 2 algorithms (double rotations like X2, Y2)

        Note: For opposite faces, there are additional solutions using combination
        moves (e.g., X Y), but this method only returns single-axis rotations.

        Examples for opposite faces (single-axis only):
            F↔B: X2, Y2
            U↔D: X2, Z2
            L↔R: Y2, Z2

        Args:
            layout: CubeLayout for deriving rotation cycles
            source: Face to bring content TO
            dest: Face where content comes FROM

        Returns:
            List of (base_alg, steps, full_alg) tuples where:
            - base_alg: The base rotation (X, Y, or Z)
            - steps: Number of rotations (1-3)
            - full_alg: The complete algorithm (e.g., X2)
        """
        results: list[Tuple[WholeCubeAlg, int, Alg]] = []

        whole_cube_alg: WholeCubeAlg
        for whole_cube_alg in [Algs.X, Algs.Y, Algs.Z]:
            # Get the 4 faces around this axis (derived from layout, not hardcoded)
            axis_face = layout.get_axis_face(whole_cube_alg.axis_name)
            cycle = layout.get_face_neighbors_cw_names(axis_face)

            if source in cycle and dest in cycle:
                src_idx = cycle.index(source)
                dst_idx = cycle.index(dest)
                # Steps needed to move dest to source position
                steps = (src_idx - dst_idx) % 4
                if steps == 0:
                    # source == dest (shouldn't happen, but handle gracefully)
                    raise InternalSWError("source == dest")

                results.append((whole_cube_alg, steps, whole_cube_alg * steps))

        if not results:
            raise ValueError(f"No rotation cycle contains both {source} and {dest}")

        return results

    @staticmethod
    def translate_source_from_target(
            target_face: Face,
            source_face: Face,
            target_coord: tuple[int, int]
    ) -> list[FaceTranslationResult]:
        """
        Find the coordinate on source_face that will move to target_coord on target_face.

        Given a position on the target face where we want content to arrive,
        find the corresponding position on the source face where that content
        currently is, and the algorithm to move it.

        Args:
            target_face: Where content should ARRIVE
            source_face: Where content COMES FROM
            target_coord: (row, col) position on target_face where we want content (0-indexed)

        Returns:
            List of FaceTranslationResult, one per valid whole-cube rotation:
            - Adjacent faces: 1 result (single rotation axis)
            - Opposite faces: 2 results (two rotation axes work)

            Each FaceTranslationResult contains:

            whole_cube_alg: Algorithm (X/Y/Z moves) that brings source_face content
                           to target_face position.

            slice_algorithms: Slice algorithms (M/E/S moves) that match this whole-cube
                             rotation. Each SliceAlgorithmResult has its own source_coord.

            shared_edge: Edge connecting target and source faces.
                        - Not None: faces are adjacent (share this edge)
                        - None: faces are opposite (F↔B, U↔D, L↔R)

        Raises:
            ValueError: If target_face == source_face (no translation needed)
            ValueError: If target_coord is out of bounds for cube size

        Example::

            # I want content at (1, 2) on Front face, coming from Right face
            results = Face2FaceTranslator.translate_source_from_target(cube.front, cube.right, (1, 2))
            result = results[0]  # Adjacent faces have 1 result

            # For opposite faces (e.g., Front from Back):
            results = Face2FaceTranslator.translate_source_from_target(cube.front, cube.back, (1, 2))
            # results[0] might use X2, results[1] might use Y2
        """
        if target_face is source_face:
            raise ValueError("Cannot translate from a face to itself")

        # Use center n_slices for coordinate bounds (not cube size)
        # For 3x3 cube, centers are 1x1 (n_slices=1)
        # For 5x5 cube, centers are 3x3 (n_slices=3)
        n_slices = target_face.center.n_slices
        row, col = target_coord
        if not (0 <= row < n_slices and 0 <= col < n_slices):
            raise ValueError(f"Coordinate {target_coord} out of bounds for center grid (n_slices={n_slices})")

        target_name = target_face.name
        source_name = source_face.name

        # Find shared edge (None if faces are opposite)
        shared_edge = Face2FaceTranslator._find_shared_edge(target_face, source_face)

        # Compute all slice algorithms - each has its own source_coord
        layout = target_face.cube.layout
        all_slice_algorithms = Face2FaceTranslator._compute_slice_algorithms(
            target_face.cube,
            target_name, source_name, target_coord, n_slices
        )

        # Derive whole-cube algorithms (1 for adjacent, 2 for opposite faces)
        whole_cube_algs = Face2FaceTranslator.derive_whole_cube_alg(layout, target_name, source_name)

        # Build lookup for whole-cube algs by their axis name
        whole_cube_by_axis: dict[AxisName, tuple[WholeCubeAlg, Alg]] = {}
        for base_alg, _, alg in whole_cube_algs:
            whole_cube_by_axis[base_alg.axis_name] = (base_alg, alg)

        # Each slice algorithm becomes one FaceTranslationResult
        results: list[FaceTranslationResult] = []
        for slice_alg in all_slice_algorithms:
            slice_name = slice_alg.whole_slice_alg.slice_name
            # Get axis for this slice (direction not used here, but documents the relationship)
            axis_name, _same_direction = layout.get_axis_for_slice(slice_name)
            whole_cube_base_alg, whole_cube_alg = whole_cube_by_axis[axis_name]

            results.append(FaceTranslationResult(
                whole_cube_base_alg=whole_cube_base_alg,
                whole_cube_alg=whole_cube_alg,
                slice_algorithm=slice_alg,
                shared_edge=shared_edge,
            ))

        return results

    @staticmethod
    def translate_target_from_source(
            source_face: Face,
            target_face: Face,
            source_coord: tuple[int, int],
            slice_name: SliceName
    ) -> Point:
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

        unit_transform = source_face.cube.layout.translate_target_from_source(
            source_face, target_face, source_coord,
            slice_name)

        return unit_transform.of_cube(source_face.cube)(*source_coord)

    @staticmethod
    def _translate_via_slice_geometry(
            source_face: Face,
            target_face: Face,
            source_coord: tuple[int, int],
            n_slices: int,
            slice_name: SliceName
    ) -> tuple[int, int]:
        """
        Translate coordinates using Slice traversal geometry.

        ================================================================================
        DESIGN: ADJACENT + COMPOSITION
        ================================================================================

        Instead of handling all cases in one complex function, we use composition:

        1. ADJACENT FACES (1 step): Direct edge crossing
           F → U uses _translate_adjacent(F, U, coord)

        2. OPPOSITE FACES (2 steps): Composition of two adjacent transforms
           F → B = _translate_adjacent(intermediate, B, _translate_adjacent(F, intermediate, coord))

        This is cleaner because:
        - Adjacent transform is simpler to understand
        - Opposite is just composition of two adjacent transforms
        - Each transform is independently verifiable

        ================================================================================
        COORDINATE SYSTEM
        ================================================================================

        Each face uses LTR (Left-to-Right) coordinates:
        - (0, 0) at bottom-left when viewing face from outside
        - row increases upward, col increases rightward

                col: 0   1   2
                   ┌───┬───┬───┐
            row 2  │   │   │   │
                   ├───┼───┼───┤
            row 1  │   │   │   │
                   ├───┼───┼───┤
            row 0  │   │   │   │
                   └───┴───┴───┘

        ================================================================================
        """
        cube = source_face.cube

        # Build the slice cycle to find positions
        cycle_faces, cycle_edges = Face2FaceTranslator._build_slice_cycle(cube, slice_name)

        source_idx = cycle_faces.index(source_face)
        target_idx = cycle_faces.index(target_face)
        steps = (target_idx - source_idx) % 4

        if steps == 0:
            # Same face (shouldn't happen, but handle gracefully)
            return source_coord
        elif steps == 1:
            # Adjacent: one step
            source_edge = cycle_edges[source_idx]
            target_edge = cycle_edges[target_idx]
            return Face2FaceTranslator._translate_adjacent(
                source_face, target_face, source_coord, n_slices,
                source_edge, target_edge
            )
        elif steps == 2:
            # Opposite: compose two adjacent transforms
            intermediate_idx = (source_idx + 1) % 4
            intermediate_face = cycle_faces[intermediate_idx]
            intermediate_edge = cycle_edges[intermediate_idx]
            source_edge = cycle_edges[source_idx]
            target_edge = cycle_edges[target_idx]

            # First transform: source → intermediate
            intermediate_coord = Face2FaceTranslator._translate_adjacent(
                source_face, intermediate_face, source_coord, n_slices,
                source_edge, intermediate_edge
            )
            # Second transform: intermediate → target
            return Face2FaceTranslator._translate_adjacent(
                intermediate_face, target_face, intermediate_coord, n_slices,
                intermediate_edge, target_edge
            )
        else:  # steps == 3
            # Going backwards (3 steps forward = 1 step backward)
            # This means target is "before" source in the cycle
            # Compose: source → intermediate1 → intermediate2 → target
            int1_idx = (source_idx + 1) % 4
            int2_idx = (source_idx + 2) % 4

            int1_face = cycle_faces[int1_idx]
            int2_face = cycle_faces[int2_idx]

            source_edge = cycle_edges[source_idx]
            int1_edge = cycle_edges[int1_idx]
            int2_edge = cycle_edges[int2_idx]
            target_edge = cycle_edges[target_idx]

            coord1 = Face2FaceTranslator._translate_adjacent(
                source_face, int1_face, source_coord, n_slices,
                source_edge, int1_edge
            )
            coord2 = Face2FaceTranslator._translate_adjacent(
                int1_face, int2_face, coord1, n_slices,
                int1_edge, int2_edge
            )
            return Face2FaceTranslator._translate_adjacent(
                int2_face, target_face, coord2, n_slices,
                int2_edge, target_edge
            )

    @staticmethod
    def _build_slice_cycle(cube: Cube, slice_name: SliceName) -> tuple[list[Face], list[Edge]]:
        """
        Build the traversal cycle for a slice.

        Uses CubeWalkingInfoUnit which derives the cycle from slice geometry.
        The starting point is intentionally random (in create_walking_info_unit)
        to expose bugs - the caller should not depend on where the cycle starts.

        Returns:
            (cycle_faces, cycle_edges) where:
            - cycle_faces[i] is the i-th face in traversal order
            - cycle_edges[i] is the entry edge for cycle_faces[i]
        """
        walk_info_unit = cube.layout.get_slice(slice_name).create_walking_info_unit()
        return walk_info_unit.resolve_cube_cycle(cube)

    @staticmethod
    def _translate_adjacent(
            source_face: Face,
            target_face: Face,
            source_coord: tuple[int, int],
            n_slices: int,
            source_edge: Edge,
            target_edge: Edge
    ) -> tuple[int, int]:
        """
        Translate coordinates between two ADJACENT faces (one edge crossing).

        ================================================================================
        TWO COORDINATES TO TRACK
        ================================================================================

        When a slice crosses a face, each point has two components:

        1. current_index: WHICH slice (0, 1, 2, ...)
           - Translates through the shared edge
           - Uses edge.get_slice_index_from_ltr_index() and get_ltr_index_from_slice_index()

        2. slot_along: WHERE on the slice (position 0, 1, 2, ...)
           - Physical position along the slice strip
           - PRESERVED across faces (slot 0 stays slot 0)
           - But mapping to (row, col) depends on edge type

        ================================================================================
        SLOT ORDERING (from Slice._get_slices_by_index)
        ================================================================================

        HORIZONTAL EDGES (top/bottom):
        ┌─────────────────────────────┬─────────────────────────────┐
        │  Bottom edge:               │   Top edge:                 │
        │  slot 0 → (row=0, col=idx)  │   slot 0 → (row=n-1, col=idx)
        │  slot 1 → (row=1, col=idx)  │   slot 1 → (row=n-2, col=idx)
        │                             │                             │
        │  current_index = col        │   current_index = col       │
        │  slot = row                 │   slot = inv(row)           │
        └─────────────────────────────┴─────────────────────────────┘

        VERTICAL EDGES (left/right):
        ┌─────────────────────────────┬─────────────────────────────┐
        │  Left edge:                 │   Right edge:               │
        │  slot 0 → (row=idx, col=0)  │   slot 0 → (row=idx, col=n-1)
        │  slot 1 → (row=idx, col=1)  │   slot 1 → (row=idx, col=n-2)
        │                             │                             │
        │  current_index = row        │   current_index = row       │
        │  slot = col                 │   slot = inv(col)           │
        └─────────────────────────────┴─────────────────────────────┘

        ================================================================================
        EXAMPLE: M slice, F(bottom) → U(bottom)
        ================================================================================

        Source F with edge_bottom:
        ┌───────────────┐
        │   0   1   2   │ col
        │ ┌───┬───┬───┐ │
        │ │   │   │   │ │ row 2
        │ ├───┼───┼───┤ │
        │ │   │ X │   │ │ row 1  ← X at (1, 1)
        │ ├───┼───┼───┤ │
        │ │   │   │   │ │ row 0
        │ └───┴───┴───┘ │
        │     ↑ slice 1 │
        └───────────────┘

        Extract: current_index=1, slot_along=1 (bottom edge)
        Translate current_index through F-U edge
        Reconstruct at U with its edge

        ================================================================================
        """

        def inv(x: int) -> int:
            return n_slices - 1 - x

        row, col = source_coord

        # ============================================================
        # STEP 1: Extract current_index and slot_along from source
        # ============================================================
        if source_face.is_bottom_or_top(source_edge):
            # Horizontal edge: col = current_index
            current_index = col
            if source_face.is_top_edge(source_edge):
                slot_along = inv(row)
            else:  # bottom edge
                slot_along = row
        else:
            # Vertical edge: row = current_index
            current_index = row
            if source_face.is_right_edge(source_edge):
                slot_along = inv(col)
            else:  # left edge
                slot_along = col

        # ============================================================
        # STEP 2: Translate current_index through the shared edge
        # ============================================================
        # The shared edge is source_edge.opposite(source_face)
        shared_edge = source_edge.opposite(source_face)
        edge_internal = shared_edge.get_slice_index_from_ltr_index(source_face, current_index)
        new_index = shared_edge.get_ltr_index_from_slice_index(target_face, edge_internal)

        # ============================================================
        # STEP 3: Reconstruct coordinates at target
        # ============================================================
        if target_face.is_bottom_or_top(target_edge):
            # Horizontal edge: col = current_index
            target_col = new_index
            if target_face.is_top_edge(target_edge):
                target_row = inv(slot_along)
            else:  # bottom edge
                target_row = slot_along
        else:
            # Vertical edge: row = current_index
            target_row = new_index
            if target_face.is_right_edge(target_edge):
                target_col = inv(slot_along)
            else:  # left edge
                target_col = slot_along

        return (target_row, target_col)

    @staticmethod
    def _find_shared_edge(face1: Face, face2: Face) -> Edge | None:
        """
        Find the edge shared by two faces, or None if they're opposite.

        Returns:
            The shared Edge if faces are adjacent, None if opposite
        """

        return face1.find_shared_edge(face2)

    @staticmethod
    def _compute_slice_algorithms(
            cube: Cube,
            target_name: FaceName,
            source_name: FaceName,
            target_coord: tuple[int, int],
            n_slices: int,
    ) -> list[SliceAlgorithmResult]:
        """
        Compute slice algorithm(s) that bring content from source to target at target_coord.

        Each slice algorithm has its OWN source_coord derived from CubeWalkingInfo,
        since different slices traverse different paths between faces.

        Returns:
            List of SliceAlgorithmResult (1 for adjacent faces, 2 for opposite faces)
        """
        # Find ALL slices that connect source and target
        connecting_slices = cube.layout.get_all_slices_for_faces(source_name, target_name)

        if not connecting_slices:
            raise InternalSWError(f"No slice connects {source_name} to {target_name}")

        results: list[SliceAlgorithmResult] = []
        source_face = cube.face(source_name)
        target_face = cube.face(target_name)

        # Map slice names to algorithm objects
        slice_name_to_alg: dict[SliceName, SliceAlg] = {
            SliceName.M: Algs.M,
            SliceName.E: Algs.E,
            SliceName.S: Algs.S,
        }

        sized_layout = cube.sized_layout

        for slice_name in connecting_slices:
            slice_alg = slice_name_to_alg[slice_name]

            # Get walking info for this slice
            walk_info = sized_layout.create_walking_info(slice_name)

            # Compute n: how many rotations to move from source to target
            # In the face_infos cycle, content at index i moves to index (i+1) % 4
            faces = walk_info.faces
            face_names = [f.name for f in faces]
            source_idx = face_names.index(source_name)
            target_idx = face_names.index(target_name)
            steps = (target_idx - source_idx) % 4
            # Convert 3 steps to -1 (more efficient)
            n = steps if steps <= 2 else steps - 4

            # Derive source_coord using CubeWalkingInfo
            # To get source_coord from target_coord, translate from target back to source
            source_coord = walk_info.translate_point(target_face, source_face, target_coord)

            # Compute slice index (0-based)
            slice: Slice = sized_layout.get_slice(slice_name)
            slice_index = slice.compute_slice_index(target_name, target_coord, n_slices)

            results.append(SliceAlgorithmResult(slice_alg, slice_index, n, source_coord))

        if not results:
            raise InternalSWError(f"No slice algorithm computed for {source_name} to {target_name}")

        return results
