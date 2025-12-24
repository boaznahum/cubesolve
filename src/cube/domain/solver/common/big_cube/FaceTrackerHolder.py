"""Face tracker holder - encapsulates 6 face trackers for NxN center solving.

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

from collections.abc import Iterator
from typing import TYPE_CHECKING

from cube.domain.model import Color
from cube.domain.model.cube_boy import CubeLayout
from cube.domain.model.FaceName import FaceName
from cube.domain.solver.common.big_cube._FaceTracker import FaceTracker
from cube.domain.solver.common.big_cube._NxNCentersFaceTracker import (
    NxNCentersFaceTrackers,
)

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.solver.protocols import SolverElementsProvider


class FaceTrackerHolder:
    """Holds 6 face trackers and provides operations on them.

    This class encapsulates the tracker lifecycle:
    1. Creates trackers on construction OR accepts existing ones
    2. Provides get_face_colors() to get current face→color mapping
    3. Cleans up tracker marks when done

    The holder tracks which face should have which color, even as the
    cube rotates during solving. This is essential for even cubes where
    there's no fixed center piece.

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

    __slots__ = ["_cube", "_trackers", "_is_even"]

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
        self._cube = slv.cube
        self._is_even = self._cube.n_slices % 2 == 0

        if trackers is not None:
            assert len(trackers) == 6, f"Expected 6 trackers, got {len(trackers)}"
            self._trackers = trackers
        else:
            self._trackers = self._create_trackers(slv)

    def _create_trackers(self, slv: SolverElementsProvider) -> list[FaceTracker]:
        """Create the 6 face trackers."""
        cube = self._cube

        if not self._is_even:
            # ODD CUBE - simple trackers using center color
            # These don't mark any slices, so no cleanup needed
            return [FaceTracker.track_odd(f) for f in cube.faces]
        else:
            # EVEN CUBE - use NxNCentersFaceTrackers to find majority colors
            # These mark center slices - must call cleanup() when done
            trackers_helper = NxNCentersFaceTrackers(slv)

            t1 = trackers_helper.track_no_1()
            t2 = t1.track_opposite()
            t3 = trackers_helper._track_no_3([t1, t2])
            t4 = t3.track_opposite()
            t5, t6 = trackers_helper._track_two_last([t1, t2, t3, t4])

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
        """Get current face→color mapping from trackers.

        Trackers dynamically resolve to the current face, so this always
        returns the correct mapping even after cube rotations.

        Returns:
            Dictionary mapping face names to their target colors.

        Example:
            {FaceName.F: Color.RED, FaceName.U: Color.WHITE, ...}
        """
        face_colors: dict[FaceName, Color] = {}
        for tracker in self._trackers:
            face_colors[tracker.face.name] = tracker.color
        return face_colors

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

        For even cubes:
            Removes the tracking attributes that were added to center slices.

        For odd cubes:
            No-op (odd cube trackers don't mark any slices).

        This MUST be called when done with the holder (or use context manager).
        """
        for f in self._cube.faces:
            FaceTracker.remove_face_track_slices(f)

    def __iter__(self) -> Iterator[FaceTracker]:
        """Iterate over the 6 face trackers."""
        return iter(self._trackers)

    def __len__(self) -> int:
        """Return number of trackers (always 6)."""
        return len(self._trackers)

    def __enter__(self) -> FaceTrackerHolder:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - cleanup trackers."""
        self.cleanup()


