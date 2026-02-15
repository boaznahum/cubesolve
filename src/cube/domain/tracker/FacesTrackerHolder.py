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

import sys
from collections.abc import Iterator, Iterable, Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, cast

from typing_extensions import Self

from cube.domain.model import CenterSlice, Color, Face, FaceName
from cube.domain.model.FacesColorsProvider import FacesColorsProvider
from cube.domain.model.PartEdge import PartEdge
from cube.domain.tracker._face_trackers_factory import NxNCentersFaceTrackers
from cube.domain.tracker._face_trackers import FaceTracker

if TYPE_CHECKING:
    from cube.domain.geometric.cube_layout import CubeLayout
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Part import Part
    from cube.domain.solver.protocols import SolverElementsProvider


class FacesTrackerHolder(FacesColorsProvider):
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

    __slots__ = ["_cube", "_trackers", "_is_even", "_face_colors_cache", "_cache_modify_counter",
                 "_holder_id", "_frozen_colors",
                 "_is_for_status_querying"]

    def __init__(
        self,
        slv: SolverElementsProvider,
        trackers: list[FaceTracker] | None = None,
            is_for_status_querying = False
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

        self._is_for_status_querying = is_for_status_querying
        self._cube = slv.cube
        self._is_even = self._cube.n_slices % 2 == 0
        self._face_colors_cache: dict[FaceName, Color] | None = None
        self._cache_modify_counter: int = -1  # Invalid counter to force first rebuild
        self._frozen_colors: dict[FaceName, Color] | None = None

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
            t5, t6 = factory._track_two_last_even_cube(parent_container, [t1, t2, t3, t4])

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

    # noinspection PyUnnecessaryCast  # pycharm is wrong
    def get_face_colors(self) -> dict[FaceName, Color]:
        """Get current face→color mapping from trackers (cached with auto-invalidation).

        When frozen (via frozen_face_colors context), returns the frozen snapshot
        without querying tracker positions. This is essential during L2 slice
        solving where slice rotations displace tracker-marked center slices.

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
        # When frozen, return the frozen snapshot
        if self._frozen_colors is not None:
            return self._frozen_colors

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

        from cube.domain.geometric.cube_layout import CubeLayout
        CubeLayout.sanity_cost_assert_is_boy(
            self.cube.sp,
            # to get rid of the pyright complains it can be null
            lambda: cast(dict[FaceName, Color], self._face_colors_cache)
        )

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

        When frozen (via frozen_face_colors context), returns the pre-computed
        color without querying tracker positions. This is essential during
        query-mode slice rotations where tracker marks may be temporarily
        displaced.

        Args:
            face_name: The face to query.

        Returns:
            The target color for that face.

        Raises:
            KeyError: If no tracker exists for that face.
        """
        if self._frozen_colors is not None:
            color = self._frozen_colors.get(face_name)
            if color is not None:
                return color
            raise KeyError(f"No tracker for face {face_name}")

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

    def get_face_by_color(self, face_color: Color) -> Face:

        return self.get_tracker_by_color(face_color).face



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
        from cube.domain.geometric.cube_layout import CubeLayout
        layout: dict[FaceName, Color] = self.face_colors
        return CubeLayout.create_layout(False, layout, self._cube.sp)


    def cleanup(self) -> None:
        """Remove tracker marks from center slices.

        Calls cleanup() on each tracker polymorphically:
        - MarkedFaceTracker: Removes its specific key from the marked edge
        - FaceTracker (base): No-op (odd, opposite, f5 trackers don't mark)

        This MUST be called when done with the holder (or use context manager).
        """
        for tracker in self._trackers:
            tracker.cleanup(force_remove_visible=self._is_for_status_querying)

    @contextmanager
    def preserve_physical_faces(self) -> Generator[Self, None, None]:
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

        # this will trigger sanity check
        self.get_face_colors()


        try:
            yield self
        finally:
            # Restore each tracker to its saved physical face
            for tracker, saved_face in zip(self._trackers, saved_states):
                tracker.restore_to_physical_face(saved_face)

            # Invalidate cache (tracker->face mappings may have changed)
            self._face_colors_cache = None

            # this will trigger sanity check
            self.get_face_colors()

    def _format_comparison_table(
        self,
        tracker_before: dict[FaceName, Color],
        tracker_after: dict[FaceName, Color],
        cube_before: dict[FaceName, Color] | None,
        cube_after: dict[FaceName, Color] | None,
        op_name: str
    ) -> str:
        """Format before/after comparison as a unified table for stderr output.

        Args:
            tracker_before: Tracker colors before operation.
            tracker_after: Tracker colors after operation.
            cube_before: Cube face colors before operation (or None).
            cube_after: Cube face colors after operation (or None).
            op_name: Name of the operation.

        Returns:
            Formatted string with comparison table.
        """
        lines = [f"\n{'='*80}"]
        lines.append(f"SANITY CHECK FAILED: {op_name}")
        lines.append("")

        # Build color->face mappings from the before/after dicts
        # tracker_before/after are dict[FaceName, Color], we need to invert to dict[Color, FaceName]
        color_to_face_before: dict[Color, FaceName] = {color: face for face, color in tracker_before.items()}
        color_to_face_after: dict[Color, FaceName] = {color: face for face, color in tracker_after.items()}

        # Show tracker state comparison
        lines.append("Tracker State:")
        lines.append("  ┌──────────────┬───────────────┬───────────────┐")
        lines.append("  │ Tracking     │ Face (BEFORE) │ Face (AFTER)  │")
        lines.append("  ├──────────────┼───────────────┼───────────────┤")
        for tracker in self._trackers:
            color = tracker.color
            color_str = str(color)
            face_before : FaceName | str = color_to_face_before.get(color, "???")
            face_after : FaceName | str = color_to_face_after.get(color, "???")
            face_before_str = face_before.name if isinstance(face_before, FaceName) else str(face_before)
            face_after_str = face_after.name if isinstance(face_after, FaceName) else str(face_after)

            # Mark if tracker moved to different face
            mark = " ⚠" if face_before != face_after else ""

            lines.append(f"  │ {color_str:12s} │ {face_before_str:13s} │ {face_after_str:13s} │{mark}")
        lines.append("  └──────────────┴───────────────┴───────────────┘")
        lines.append("")

        if cube_before is not None and cube_after is not None:
            # Full table with both cube and tracker
            lines.append("  ┌──────┬──────────────┬──────────────┬──────────────┬──────────────┐")
            lines.append("  │ Face │ Cube Before  │ Cube After   │ Trkr Before  │ Trkr After   │")
            lines.append("  ├──────┼──────────────┼──────────────┼──────────────┼──────────────┤")

            for face_name in [FaceName.U, FaceName.D, FaceName.F, FaceName.B, FaceName.L, FaceName.R]:
                cb = str(cube_before.get(face_name, "???"))
                ca = str(cube_after.get(face_name, "???"))
                tb = str(tracker_before.get(face_name, "???"))
                ta = str(tracker_after.get(face_name, "???"))

                # Mark mismatches
                cube_changed = cb != ca
                tracker_changed = tb != ta
                mark = ""
                if cube_changed or tracker_changed:
                    mark = " ⚠"

                lines.append(f"  │ {face_name.name:4s} │ {cb:12s} │ {ca:12s} │ {tb:12s} │ {ta:12s} │{mark}")

            lines.append("  └──────┴──────────────┴──────────────┴──────────────┴──────────────┘")
        else:
            # Tracker-only table
            lines.append("  ┌──────┬──────────────┬──────────────┐")
            lines.append("  │ Face │ Trkr Before  │ Trkr After   │")
            lines.append("  ├──────┼──────────────┼──────────────┤")

            for face_name in [FaceName.U, FaceName.D, FaceName.F, FaceName.B, FaceName.L, FaceName.R]:
                tb = str(tracker_before.get(face_name, "???"))
                ta = str(tracker_after.get(face_name, "???"))

                # Mark mismatches
                tracker_changed = tb != ta
                mark = " ⚠" if tracker_changed else ""

                lines.append(f"  │ {face_name.name:4s} │ {tb:12s} │ {ta:12s} │{mark}")

            lines.append("  └──────┴──────────────┴──────────────┘")

        lines.append(f"{'='*80}\n")
        return "\n".join(lines)

    @contextmanager
    def sanity_check_before_after_same_colors(self,op_name: str,
                                              also_assert_cube_faces,
                                              disable: bool =False) -> Generator[Self, None, None]:

        """

        Args:
            disable Pass true if you want to disable the chek , if the changed is expected


        """
        cube = self.cube
        if disable or not cube.sp.config.face_tracker.validate:
            yield self
            return

        before_trackers: dict[FaceName, Color] = dict(self.get_face_colors())

        if also_assert_cube_faces:
            before_cube_colors = dict(cube.faces_colors)
        else:
            before_cube_colors = None

        # why not try / finally becuas ein case of exception like abort or other we just want tht
        # original exception and ont to continue with the checl
        yield self
        after_trackers = self.face_colors

        # Get cube colors if checking
        after_cube: dict[FaceName, Color] | None
        if also_assert_cube_faces:
            after_cube = cube.faces_colors
        else:
            after_cube = None

        # Check for any changes
        tracker_changed = after_trackers != before_trackers
        cube_changed = also_assert_cube_faces and before_cube_colors != after_cube

        # Print unified table to stderr BEFORE any assertions if anything changed
        if tracker_changed or cube_changed:
            table = self._format_comparison_table(
                tracker_before=before_trackers,
                tracker_after=after_trackers,
                cube_before=before_cube_colors,
                cube_after=after_cube,
                op_name=op_name
            )
            print(table, file=sys.stderr)

        # Now do assertions
        assert after_trackers == before_trackers, f"Trackers changed due to {op_name}, before={before_trackers}, after={after_trackers}"

        if also_assert_cube_faces:
            assert before_cube_colors == after_cube, (f"Cube faces changed due to {op_name}:,\n"
                                                      f"   before={before_cube_colors},\n"
                                                      f"   after={after_cube}")

        # this will trigger sanity check
        self.get_face_colors()

    @contextmanager
    def frozen_face_colors(self) -> Generator[dict[FaceName, Color], None, None]:
        """Freeze face-color mapping for the duration of the context.

        During query-mode slice rotations, tracker marks move with center
        pieces, temporarily displacing them to wrong faces. This causes
        get_face_color() to fail with KeyError when two trackers end up
        on the same face.

        This context manager snapshots the current face-color mapping
        and makes get_face_color() return from the snapshot instead of
        doing live tracker searches.

        Usage:
            with holder.frozen_face_colors():
                with op.with_query_restore_state():
                    play(slice_rotation)
                    # match_faces now uses frozen colors — safe!

        Yields:
            The frozen face-color mapping dict.
        """
        frozen = self.get_face_colors().copy()
        self._frozen_colors = frozen
        try:
            yield frozen
        finally:
            self._frozen_colors = None

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

    def get_debug_str_faces(self) -> str:
        faces: dict[FaceName, Color] = { f.face_name:f.color for f in self.trackers}
        s = f"is boy={self._trackers_layout().is_boy()} {faces}"

        return s

    def format_current_state(self, include_cube_faces: bool = True) -> str:
        """Format current tracker and cube state as a human-readable table.

        Shows:
        - Tracker colors (immutable target colors)
        - Current faces where those colors are tracked (dynamic, changes with rotations)
        - Optional: Actual cube face colors

        This is a snapshot of the current state, with no before/after comparison.

        Args:
            include_cube_faces: If True, include actual cube face colors.

        Returns:
            Formatted string with current state table.
        """
        lines: list[str] = []

        # Get current tracker state: face→color mapping
        tracker_current: dict[FaceName, Color] = dict(self.get_face_colors())

        # Invert to get color→face mapping for the tracker state table
        color_to_face: dict[Color, FaceName] = {color: face for face, color in tracker_current.items()}

        # Show tracker state
        lines.append("Tracker State:")
        lines.append("  ┌──────────────┬────────┐")
        lines.append("  │ Tracking     │ Face   │")
        lines.append("  ├──────────────┼────────┤")
        for tracker in self._trackers:
            color = tracker.color
            color_str = str(color)
            face = color_to_face.get(color)
            face_str = face.name if face is not None else "???"
            lines.append(f"  │ {color_str:12s} │ {face_str:6s} │")
        lines.append("  └──────────────┴────────┘")

        if include_cube_faces:
            lines.append("")
            # Get actual cube face colors
            cube_current: dict[FaceName, Color] = dict(self.cube.faces_colors)

            # Full table with both cube and tracker
            lines.append("  ┌──────┬──────────────┬──────────────┐")
            lines.append("  │ Face │ Cube Color   │ Trkr Color   │")
            lines.append("  ├──────┼──────────────┼──────────────┤")

            for face_name in [FaceName.U, FaceName.D, FaceName.F, FaceName.B, FaceName.L, FaceName.R]:
                cube_color = str(cube_current.get(face_name, "???"))
                tracker_color = str(tracker_current.get(face_name, "???"))

                # Mark mismatches
                mark = " ⚠" if cube_color != tracker_color else ""

                lines.append(f"  │ {face_name.name:4s} │ {cube_color:12s} │ {tracker_color:12s} │{mark}")

            lines.append("  └──────┴──────────────┴──────────────┘")

        return "\n".join(lines)

    @staticmethod
    def contain_center_tracker(c: CenterSlice) -> bool:
        """Check if a center slice is tracked by any tracker.

        Args:
            c: CenterSlice to check.

        Returns:
            True if any tracker has marked this center slice.
        """
        return FaceTracker.is_track_slice(c)

