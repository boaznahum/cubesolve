"""Helper class for NxN center solving - shared tracker creation and cleanup.

This helper consolidates common code used by both:
- CageNxNSolver (cage method - edges/corners first, then centers)
- NxNCenters (reduction method - centers first, then edges)

TRACKER CREATION:
=================
For odd cubes (5x5, 7x7):
    Simple - use fixed center piece color to track each face.

For even cubes (4x4, 6x6):
    Complex - no fixed center, so we find majority colors and mark
    specific center slices to track face positions.

CLEANUP:
========
Even cube trackers mark center slices with tracking attributes.
These must be removed after solving to avoid interfering with
subsequent operations.
"""

from __future__ import annotations

from cube.domain.model.Cube import Cube
from cube.domain.solver.beginner.NxnCentersFaceTracker import NxNCentersFaceTrackers
from cube.domain.solver.common.FaceTracker import FaceTracker
from cube.domain.solver.protocols import SolverElementsProvider


class NxNCentersHelper:
    """Helper for NxN center solving - tracker creation and cleanup.

    Usage:
        # Create trackers
        helper = NxNCentersHelper(solver_elements_provider)
        trackers = helper.create_trackers()

        # ... use trackers for solving ...

        # Cleanup (in finally block)
        helper.cleanup_trackers()
    """

    def __init__(self, slv: SolverElementsProvider) -> None:
        """Initialize helper with solver elements provider.

        Args:
            slv: Provides access to cube and operator.
        """
        self._cube = slv.cube
        self._trackers = NxNCentersFaceTrackers(slv)

    @property
    def cube(self) -> Cube:
        """Get the cube being solved."""
        return self._cube

    def create_trackers(self) -> list[FaceTracker]:
        """Create face trackers for all 6 faces.

        For odd cubes:
            Simple trackers using fixed center piece color.
            No cleanup needed (no slices are marked).

        For even cubes:
            Trackers mark center slices to track face positions.
            MUST call cleanup_trackers() when done!

        Returns:
            List of 6 FaceTrackers, one per face.
        """
        cube = self._cube

        if cube.n_slices % 2:
            # ODD CUBE - simple trackers using center color
            # These don't mark any slices, so no cleanup needed
            return [FaceTracker.track_odd(f) for f in cube.faces]
        else:
            # EVEN CUBE - use NxNCentersFaceTrackers to find majority colors
            # These mark center slices - must call cleanup_trackers() when done
            t1 = self._trackers.track_no_1()
            t2 = t1.track_opposite()
            t3 = self._trackers._track_no_3([t1, t2])
            t4 = t3.track_opposite()
            t5, t6 = self._trackers._track_two_last([t1, t2, t3, t4])

            return [t1, t2, t3, t4, t5, t6]

    def cleanup_trackers(self) -> None:
        """Remove tracker markers from center slices.

        For even cubes:
            Removes the tracking attributes that were added to center slices
            during create_trackers().

        For odd cubes:
            No-op (odd cube trackers don't mark any slices).

        This should be called in a finally block after solving is complete.
        """
        for f in self._cube.faces:
            FaceTracker.remove_face_track_slices(f)

    @staticmethod
    def cleanup_trackers_static(cube: Cube) -> None:
        """Static version of cleanup - removes tracker markers from all faces.

        Useful when you have the cube but not the helper instance.

        Args:
            cube: The cube to cleanup.
        """
        for f in cube.faces:
            FaceTracker.remove_face_track_slices(f)
