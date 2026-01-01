"""LBL Slices Helper - wraps NxNCenters and NxNEdges for layer-by-layer slice solving.

This helper provides slice-based operations for middle layer solving:
- Ring center solving (one row on 4 side faces per slice)
- Edge wing pairing (4 wings per slice)

Slice indexing: 0 to n_slices-1 (0 = closest to D, n_slices-1 = closest to U)
Row mapping: row = n_slices - 1 - slice_index

Algorithm for ring center solving:
1. For each side face (F, R, B, L), bring it to front position
2. For each position in target row that needs the correct color:
   - Find source center with correct color on U face (or other side face rows)
   - Use block commutator to bring it into position
3. Move to next side face
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.model.cube_layout.cube_boy import Color
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.common.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.solver.common.tracker._base import FaceTracker
from cube.domain.solver.common.big_cube.NxNCenters2 import NxNCenters2
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges

if TYPE_CHECKING:
    from cube.domain.model.Face import Face
    from cube.domain.solver.protocols.SolverElementsProvider import SolverElementsProvider


class _LBLSlices(SolverElement):
    """Helper for solving middle slices in layer-by-layer method.

    Wraps NxNCenters and NxNEdges with slice-based operations.

    Attributes:
        centers: NxNCenters helper for center solving
        edges: NxNEdges helper for edge pairing
    """

    __slots__ = ["_slv", "_centers", "_edges"]

    def __init__(self, slv: SolverElementsProvider) -> None:

        super().__init__(slv)

        """Create LBL slices helper.

        Args:
            slv: Solver elements provider (for cube access and operations)
        """
        self._slv = slv
        # preserve_cage=True to preserve Layer 1 edges during center solving
        self._centers = NxNCenters2(slv, preserve_cage=True)
        self._edges = NxNEdges(slv, advanced_edge_parity=False)

    @property
    def centers(self) -> NxNCenters2:
        """Access to NxNCenters helper."""
        return self._centers

    @property
    def edges(self) -> NxNEdges:
        """Access to NxNEdges helper."""
        return self._edges

    # =========================================================================
    # Coordinate conversion
    # =========================================================================

    def slice_to_row(self, slice_index: int) -> int:
        """Convert slice index (0=bottom) to row index on side faces.

        Formula: row = n_slices - 1 - slice_index

        Example for 5x5 (n_slices=3):
            slice 0 → row 2 (bottom row, closest to D)
            slice 1 → row 1 (middle row)
            slice 2 → row 0 (top row, closest to U)
        """
        return self.n_slices - 1 - slice_index

    def row_to_slice(self, row_index: int) -> int:
        """Convert row index on side faces to slice index.

        Inverse of slice_to_row.
        """
        return self.n_slices - 1 - row_index

    # =========================================================================
    # Face helpers
    # =========================================================================

    def get_side_face_trackers(
            self, th: FacesTrackerHolder, l1_tracker: FaceTracker
    ) -> list[FaceTracker]:
        """Get trackers for side faces (not Layer 1 or its opposite).

        Args:
            th: FacesTrackerHolder with all 6 face trackers
            l1_tracker: The Layer 1 face tracker (to exclude with its opposite)

        Returns:
            List of 4 side face trackers
        """
        l1_opposite_face = l1_tracker.face.opposite
        return [t for t in th.trackers
                if t.face is not l1_tracker.face and t.face is not l1_opposite_face]

    # =========================================================================
    # State inspection
    # =========================================================================

    def is_slice_centers_solved(
            self, slice_index: int, th: FacesTrackerHolder, l1_tracker: FaceTracker
    ) -> bool:
        """Check if all ring centers for a specific slice are solved.

        A slice's ring centers are solved when every center in the corresponding
        row on all 4 side faces has the correct color for that face.

        Args:
            slice_index: 0 to n_slices-1 (0 = closest to D)
            th: FacesTrackerHolder for face color tracking
            l1_tracker: Layer 1 face tracker (to identify side faces)
        """
        row = self.slice_to_row(slice_index)

        for face_tracker in self.get_side_face_trackers(th, l1_tracker):
            target_color = face_tracker.color
            face = face_tracker.face

            for col in range(self.n_slices):
                center = face.center.get_center_slice((row, col))
                if center.color != target_color:
                    return False

        return True

    def count_solved_slice_centers(
            self, th: FacesTrackerHolder, l1_tracker: FaceTracker
    ) -> int:
        """Count how many slices have their ring centers solved (from bottom up).

        Counts consecutive solved slices starting from slice 0 (bottom).
        Once an unsolved slice is found, stops counting.
        """
        count = 0
        for slice_index in range(self.n_slices):
            if self.is_slice_centers_solved(slice_index, th, l1_tracker):
                count += 1
            else:
                break
        return count

    # =========================================================================
    # Solving operations
    # =========================================================================

    def solve_slice_centers(
            self, slice_index: int, th: FacesTrackerHolder, l1_white_tracker: FaceTracker
    ) -> None:
        """Solve ring centers for a single slice.

        Simple approach (no optimization):
        1. For each side face, bring to front
        2. For each piece in row that needs fixing:
           - Search on UP (rotate adjacent faces to UP)
           - Search on BACK
           - If still missing, move from same face to adjacent, then bring from there
        3. Repeat until all 4 faces are solved (may need multiple iterations
           because solving one face can disturb others)

        Args:
            slice_index: Which slice to solve (0 = closest to D)
            th: FacesTrackerHolder for face color tracking
            l1_white_tracker: Layer 1 face tracker
        """
        row = self.slice_to_row(slice_index)

        #boaz: it may related to cube orinatation
        if self.is_slice_centers_solved(slice_index, th, l1_white_tracker):
            return

        # Get side face trackers (excluding L1 and opposite)
        side_trackers = self.get_side_face_trackers(th, l1_white_tracker)

        if self.is_slice_centers_solved(slice_index, th, l1_white_tracker):
            return

        for face_tracker in side_trackers:
            self._solve_face_row_simple(l1_white_tracker, face_tracker, slice_index)

        # Verify solved
        # boaz: currently we cant do it, because our index system is wrong, slice_index is depends on cube orientation
        if False and not self.is_slice_centers_solved(slice_index, th, l1_white_tracker):
            self._report_stuck(slice_index, row, side_trackers)

    def _solve_face_row_simple(
            self, l1_white_tracker: FaceTracker, face_tracker: FaceTracker, slice_index: int
    ) -> None:
        row = self.slice_to_row(slice_index)
        self._centers.solve_single_center_row_slice(l1_white_tracker, face_tracker, row)

    def _is_face_row_solved(self, face: Face, row: int, target_color: Color) -> bool:
        """Check if a specific row on a face has all correct colors."""
        for col in range(self.n_slices):
            if face.center.get_center_slice((row, col)).color != target_color:
                return False
        return True

    def _report_stuck(
            self, slice_index: int, row: int, side_trackers: list[FaceTracker]
    ) -> None:
        """Report which face is stuck and show state."""
        for face_tracker in side_trackers:
            if not self._is_face_row_solved(face_tracker.face, row, face_tracker.color):
                needed = face_tracker.color.name
                print(f"\n=== STUCK: Need {needed} on row {row} ===")
                cube = self.cube
                for face in [cube.front, cube.right, cube.back, cube.left, cube.up, cube.down]:
                    positions = []
                    for r in range(self.n_slices):
                        for c in range(self.n_slices):
                            center = face.center.get_center_slice((r, c))
                            if center.color.name == needed:
                                positions.append(f"({r},{c})")
                    if positions:
                        print(f"  {face.name}: {needed} at {positions}")
                raise RuntimeError(
                    f"Failed to solve slice {slice_index} (row {row}) on face {face_tracker.color.name}"
                )

    def solve_all_slice_centers(
            self, th: FacesTrackerHolder, l1_white_tracker: FaceTracker
    ) -> None:
        """Solve all middle slice ring centers (bottom to top).

        Solves slices in order: 0, 1, 2, ... n_slices-1
        Each slice = one row on each of the 4 side faces.

        IMPORTANT: Layer 1 must be on DOWN for the commutator to work correctly.
        The commutator uses UP as source, so if Layer 1 is on UP, we'll mess it up.
        """

        # Ensure Layer 1 is on DOWN (commutator uses UP as source)
        l1_face = l1_white_tracker.face
        cube = self.cube
        op = self._slv.op

        # Solve all slices from bottom to top
        if True:  # WIP: Only solve first slice for now
            r = range(1)
        else:
            r = range(self.n_slices)
        for slice_index in r:
            self.solve_slice_centers(slice_index, th, l1_white_tracker)
