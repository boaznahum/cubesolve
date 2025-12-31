"""Face tracker holder - encapsulates 6 face trackers for NxN center solving.

See FACE_TRACKER.md in this directory for detailed documentation on:
- Why trackers are needed for even cubes
- How tracker-based matching works vs center-based matching
- Cache invalidation with modify_counter
- Usage patterns across different solvers

This class provides a clean OOP interface for managing face trackers:
- Creates trackers on construction
- Provides methods to work with trackers (get_face_colors, etc.)
- Handles cleanup when done

USAGE:
======
    with FaceTrackerHolder(solver) as holder:
        face_colors = holder.get_face_colors()
        # ... use face_colors for solving ...
    # cleanup is automatic

Or manually:
    holder = FaceTrackerHolder(solver)
    try:
        face_colors = holder.get_face_colors()
        # ... use face_colors for solving ...
    finally:
        holder.cleanup()
"""

from __future__ import annotations

from collections.abc import Iterator, Iterable
from contextlib import contextmanager
from typing import TYPE_CHECKING

from typing_extensions import Self

from cube.domain.model import CenterSlice, Color
from cube.domain.model.cube_layout.cube_boy import CubeLayout
from cube.domain.model.FaceName import FaceName
from cube.domain.model.PartEdge import PartEdge
from cube.domain.solver.common.tracker._base import FaceTracker
from cube.domain.solver.common.tracker._factory import NxNCentersFaceTrackers

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Part import Part
    from cube.domain.solver.protocols import SolverElementsProvider


class FacesTrackerHolder:
    """Holds 6 face trackers and provides operations on them.

    This class encapsulates the tracker lifecycle:
    1. Creates trackers on construction OR accepts existing ones
    2. Provides get_face_colors() to get current face→color mapping
    3. Cleans up tracker marks when done

    The holder tracks which face should have which color, even as the
    cube rotates during solving. This is essential for even cubes where
    there's no fixed center piece.

    HOLDER-SPECIFIC MARKER IDs:
    ===========================
    Each holder instance gets a unique ID. Tracker keys include this holder ID:

        Key format: "_nxn_centers_track:h{holder_id}:{color}{unique_id}"
        Example: "_nxn_centers_track:h42:WHITE1"

    This allows multiple holders to coexist safely - each cleanup() only
    removes markers belonging to THAT holder, not markers from other holders.

    USAGE PATTERNS:
    ===============

    Pattern 1: Create trackers automatically (e.g., BeginnerReducer)
        with FaceTrackerHolder(solver) as holder:
            centers = NxNCenters(solver, holder)
            centers.solve()
        # cleanup automatic

    Pattern 2: Accept existing trackers (e.g., CageNxNSolver)
        with FaceTrackerHolder(solver, trackers=my_trackers) as holder:
            # holder now manages the existing trackers
            centers = NxNCenters(solver, holder)
            centers.solve()
        # cleanup automatic

    CONTEXT MANAGER:
    ================
    Supports `with` statement for automatic cleanup:

        with FaceTrackerHolder(solver) as holder:
            colors = holder.get_face_colors()
            # ... solve ...
        # cleanup automatic

    ITERATION:
    ==========
    Can iterate over individual trackers if needed:

        for tracker in holder:
            print(f"{tracker.face.name} -> {tracker.color}")
    """

    _holder_unique_id: int = 0  # Class variable for generating unique holder IDs

    __slots__ = ["_cube", "_trackers", "_is_even", "_face_colors_cache", "_cache_modify_counter", "_holder_id"]

    def __init__(
        self,
        slv: SolverElementsProvider,
        trackers: list[FaceTracker] | None = None
    ) -> None:
        """Create or accept face trackers for all 6 faces.

        Args:
            slv: Solver elements provider (access to cube and operator).
            trackers: Optional list of 6 existing FaceTrackers.
                If provided, the holder manages these trackers.
                If None, trackers are created automatically:
                - For odd cubes (5x5, 7x7): Simple trackers using fixed center color.
                - For even cubes (4x4, 6x6): Trackers mark center slices.

        Note:
            MUST call cleanup() when done (or use context manager)!
            Cleanup is needed for even cubes to remove tracking marks.
        """
        # Generate unique holder ID for this instance
        FacesTrackerHolder._holder_unique_id += 1
        self._holder_id = FacesTrackerHolder._holder_unique_id

        self._cube = slv.cube
        self._is_even = self._cube.n_slices % 2 == 0
        self._face_colors_cache: dict[FaceName, Color] | None = None
        self._cache_modify_counter: int = -1  # Invalid counter to force first rebuild

        if trackers is not None:
            assert len(trackers) == 6, f"Expected 6 trackers, got {len(trackers)}"
            self._trackers = trackers
        else:
            self._trackers = self._create_trackers(self, slv)

    def _create_trackers(self, parent_container: FacesTrackerHolder, slv: SolverElementsProvider) -> list[FaceTracker]:
        """Create the 6 face trackers using NxNCentersFaceTrackers factory."""
        cube = self._cube
        factory = NxNCentersFaceTrackers(slv, self._holder_id)

        if not self._is_even:
            # ODD CUBE - simple trackers using fixed center color
            return [factory._create_tracker_odd(self, f) for f in cube.faces]
        else:
            # EVEN CUBE - trackers mark center slices for majority color
            t1 = factory.track_no_1(parent_container)
            t2 = t1._track_opposite()
            t3 = factory._track_no_3(parent_container, [t1, t2])
            t4 = t3._track_opposite()
            t5, t6 = factory._track_two_last(parent_container, [t1, t2, t3, t4])

            return [t1, t2, t3, t4, t5, t6]

    @property
    def cube(self) -> Cube:
        """Get the cube being tracked."""
        return self._cube

    @property
    def is_even_cube(self) -> bool:
        """True if tracking an even cube (requires cleanup)."""
        return self._is_even

    @property
    def trackers(self) -> list[FaceTracker]:
        """Get the list of face trackers (read-only access)."""
        return self._trackers

    def get_face_colors(self) -> dict[FaceName, Color]:
        """Get current face→color mapping from trackers (cached with auto-invalidation).

        Cache Invalidation Pattern:
        ===========================
        Uses cube._modify_counter to detect when cube has changed:

            ┌─────────────────────────────────────────────────────────────┐
            │  cube._modify_counter: 42                                   │
            │  self._cache_modify_counter: 42  ← Same? Use cache ✓        │
            │                                                             │
            │  After cube rotation (Y move):                              │
            │  cube._modify_counter: 43        ← Incremented!             │
            │  self._cache_modify_counter: 42  ← Stale! Rebuild cache     │
            └─────────────────────────────────────────────────────────────┘

        Why Cache Invalidation Is Needed:
        ==================================
        Trackers mark center slices. On whole-cube rotation, slices move:

            Before Y rotation:           After Y rotation:
            ┌───┐                        ┌───┐
            │ U │                        │ U │
            ├───┼───┬───┬───┐            ├───┼───┬───┬───┐
            │ L │[F]│ R │ B │            │ L │ F │[R]│ B │
            ├───┼───┴───┴───┘            ├───┼───┴───┴───┘
            │ D │  ↑                     │ D │      ↑
            └───┘  WHITE tracker here    └───┘      WHITE tracker moved!

            Cache: {F: WHITE}            Cache STALE! Should be {R: WHITE}

        Returns:
            Dictionary mapping face names to their target colors.
        """
        # Check if cache is valid using cube's modification counter
        # noinspection PyProtectedMember
        current_counter = self._cube._modify_counter
        if self._face_colors_cache is not None and self._cache_modify_counter == current_counter:
            return self._face_colors_cache

        # Rebuild cache - trackers may have moved to different faces
        self._face_colors_cache = {}
        for tracker in self._trackers:
            self._face_colors_cache[tracker.face.name] = tracker.color
        self._cache_modify_counter = current_counter
        return self._face_colors_cache

    @property
    def face_colors(self) -> dict[FaceName, Color]:
        """Current face→color mapping (cached property).

        Uses cube._modify_counter for automatic cache invalidation.
        Safe to call repeatedly - returns cached result if cube unchanged.
        """
        return self.get_face_colors()

    def get_face_color(self, face_name: FaceName) -> Color:
        """Get the target color for a specific face.

        Args:
            face_name: The face to query.

        Returns:
            The target color for that face.

        Raises:
            KeyError: If no tracker exists for that face.
        """
        for tracker in self._trackers:
            if tracker.face.name == face_name:
                return tracker.color
        raise KeyError(f"No tracker for face {face_name}")

    def get_tracker(self, face_name: FaceName) -> FaceTracker | None:
        """Get the tracker for a specific face.

        Args:
            face_name: The face to query.

        Returns:
            The FaceTracker for that face, or None if not found.
        """
        for tracker in self._trackers:
            if tracker.face.name == face_name:
                return tracker
        return None

    def get_tracker_by_color(self, color: Color) -> FaceTracker:
        """Get the tracker for a face with the specified color.

        Args:
            color: The target color to find.

        Returns:
            The FaceTracker for the face with that color.

        Raises:
            KeyError: If no tracker exists for that color.
        """
        for tracker in self._trackers:
            if tracker.color == color:
                return tracker
        raise KeyError(f"No tracker for color {color}")

    def part_match_faces(self, part: "Part") -> bool:
        """Check if a part's colors match the tracker-assigned face colors.

        Unlike Part.match_faces which uses actual center colors, this method
        uses the tracker's face→color mapping. This is essential for even
        cubes where only some centers are solved.

        A part matches if every sticker's color equals the tracker's expected
        color for the face that sticker is on.

        Args:
            part: The Part (Edge or Corner) to check.

        Returns:
            True if all part stickers match their face's tracker color.

        Example:
            If tracker says F→ORANGE and U→WHITE, then an edge at F-U
            must have ORANGE sticker on F and WHITE sticker on U.

        See Also:
            FACE_TRACKER.md in this directory for detailed explanation
            with diagrams of why this is needed for even cubes.
        """
        face_colors = self.face_colors  # Get current mapping (not cached)
        for edge in part._3x3_representative_edges:
            expected_color = face_colors.get(edge.face.name)
            if expected_color is None or edge.color != expected_color:
                return False
        return True

    def adjusted_faces(self, of_face: FaceTracker) -> Iterable[FaceTracker]:
        # boaz: improve this

        l1_opposite_face = of_face.face.opposite
        return [t for t in self.trackers
                if t.face is not of_face.face and t.face is not l1_opposite_face]



    def _trackers_layout(self) -> CubeLayout:
        """Get the current tracker mapping as a CubeLayout.

        Builds a CubeLayout from the trackers' face→color mapping.
        Can be used to check is_boy() or compare with other layouts.

        Returns:
            CubeLayout representing current tracker state.
        """
        layout = {tracker.face.name: tracker.color for tracker in self._trackers}
        return CubeLayout(False, layout, self._cube.sp)

    def assert_is_boy(self) -> None:
        """Assert that trackers represent valid BOY layout.

        Raises:
            AssertionError: If layout is not valid BOY.
        """
        cl = self._trackers_layout()
        if not cl.is_boy():
            import sys
            print(cl, file=sys.stderr)
            print(file=sys.stderr)
        assert cl.is_boy(), "Trackers do not represent valid BOY layout"

    def cleanup(self) -> None:
        """Remove tracker marks from center slices.

        Calls cleanup() on each tracker polymorphically:
        - MarkedFaceTracker: Removes its specific key from the marked edge
        - FaceTracker (base): No-op (odd, opposite, f5 trackers don't mark)

        This MUST be called when done with the holder (or use context manager).
        """
        for tracker in self._trackers:
            tracker.cleanup()

    @contextmanager
    def preserve_physical_faces(self) -> Iterator[Self]:
        """Context manager preserving face->color mapping across operations.

        Use when running algorithms (like commutators) that:
        1. Move center pieces (which moves markers)
        2. Preserve the cage (cube orientation unchanged after)

        Each tracker saves/restores according to its own rules:
        - SimpleFaceTracker: no-op (predicates are stable)
        - MarkedFaceTracker: saves face name, restores marker to same physical face

        Usage:
            with holder.preserve_physical_faces():
                commutator.execute()  # Moves centers
            # Markers now restored to original physical faces

        Example:
            # Before: marker on UP tracking WHITE
            with holder.preserve_physical_faces():
                alg.play()  # Commutator moves centers
                # Marker may now be on FRONT (followed the piece)
            # After: marker back on UP (same physical face)

        Yields:
            Self for chaining.
        """
        # Save state for each tracker (physical face name)
        saved_states: list[FaceName] = [
            tracker.save_physical_face() for tracker in self._trackers
        ]

        try:
            yield self
        finally:
            # Restore each tracker to its saved physical face
            for tracker, saved_face in zip(self._trackers, saved_states):
                tracker.restore_to_physical_face(saved_face)

            # Invalidate cache (tracker->face mappings may have changed)
            self._face_colors_cache = None

    def __iter__(self) -> Iterator[FaceTracker]:
        """Iterate over the 6 face trackers."""
        return iter(self._trackers)

    def __len__(self) -> int:
        """Return number of trackers (always 6)."""
        return len(self._trackers)

    def __enter__(self) -> FacesTrackerHolder:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - cleanup trackers."""
        self.cleanup()

    # =========================================================================
    # STATIC METHODS - Holder-agnostic, for display purposes
    # =========================================================================

    @staticmethod
    def is_tracked_slice(s: CenterSlice) -> bool:
        """Check if ANY tracker has marked this slice.

        WARNING: This is HOLDER-AGNOSTIC. Returns True if ANY holder
        has marked this slice, not a specific holder.

        Use for display purposes where holder identity doesn't matter.

        Args:
            s: CenterSlice to check.

        Returns:
            True if any tracker has marked this slice.
        """
        return FaceTracker.is_track_slice(s)

    @staticmethod
    def get_tracked_slice_color(s: CenterSlice) -> Color | None:
        """Get the tracker color for a marked slice.

        WARNING: This is HOLDER-AGNOSTIC. Returns color from ANY holder
        that has marked this slice.

        Use for display purposes (e.g., renderer showing tracker indicators)
        where holder identity doesn't matter.

        Args:
            s: CenterSlice to check.

        Returns:
            The Color enum if tracked, None otherwise.
        """
        return FaceTracker.get_slice_tracker_color(s)

    @staticmethod
    def get_tracked_edge_color(edge: PartEdge) -> Color | None:
        """Get the tracker color for a PartEdge.

        WARNING: This is HOLDER-AGNOSTIC. Returns color from ANY holder
        that has marked this edge.

        Use for display purposes (e.g., renderer showing tracker indicators)
        where holder identity doesn't matter.

        Args:
            edge: PartEdge to check (typically from a center slice).

        Returns:
            The Color enum if tracked, None otherwise.
        """
        return FaceTracker.get_edge_tracker_color(edge)
