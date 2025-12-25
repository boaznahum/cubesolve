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

from cube.domain.model.cube_boy import Color
from cube.domain.solver.common.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.solver.common.tracker._base import FaceTracker
from cube.domain.solver.common.big_cube.NxNCenters import NxNCenters
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face
    from cube.domain.solver.protocols.SolverElementsProvider import SolverElementsProvider


class _LBLSlices:
    """Helper for solving middle slices in layer-by-layer method.

    Wraps NxNCenters and NxNEdges with slice-based operations.

    Attributes:
        centers: NxNCenters helper for center solving
        edges: NxNEdges helper for edge pairing
    """

    __slots__ = ["_slv", "_centers", "_edges"]

    def __init__(self, slv: SolverElementsProvider) -> None:
        """Create LBL slices helper.

        Args:
            slv: Solver elements provider (for cube access and operations)
        """
        self._slv = slv
        # preserve_cage=True to preserve Layer 1 edges during center solving
        self._centers = NxNCenters(slv, preserve_cage=True)
        self._edges = NxNEdges(slv, advanced_edge_parity=False)

    @property
    def cube(self) -> Cube:
        return self._slv.cube

    @property
    def centers(self) -> NxNCenters:
        """Access to NxNCenters helper."""
        return self._centers

    @property
    def edges(self) -> NxNEdges:
        """Access to NxNEdges helper."""
        return self._edges

    @property
    def n_slices(self) -> int:
        """Number of middle slices (n-2 for NxN cube)."""
        return self.cube.n_slices

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
        self, slice_index: int, th: FacesTrackerHolder, l1_tracker: FaceTracker
    ) -> None:
        """Solve ring centers for a single slice.

        Algorithm:
        1. For each side face, bring it to front
        2. Use NxNCenters to fix centers in the target row only
        3. Repeat until row is solved

        Args:
            slice_index: Which slice to solve (0 = closest to D)
            th: FacesTrackerHolder for face color tracking
            l1_tracker: Layer 1 face tracker
        """
        if self.is_slice_centers_solved(slice_index, th, l1_tracker):
            return

        row = self.slice_to_row(slice_index)

        # Get side face trackers (excluding L1 and opposite)
        side_trackers = self.get_side_face_trackers(th, l1_tracker)

        # Keep iterating until slice is solved (may need multiple passes)
        max_iterations = 20  # Safety limit
        for iteration in range(max_iterations):
            if self.is_slice_centers_solved(slice_index, th, l1_tracker):
                return

            work_done = False
            for face_tracker in side_trackers:
                if self._solve_face_row(face_tracker, row, th, l1_tracker):
                    work_done = True
                    # Check if fully solved after each face
                    if self.is_slice_centers_solved(slice_index, th, l1_tracker):
                        return

            if not work_done:
                # No progress made - might need different strategy
                break

        # If we get here, slice might not be fully solved
        if not self.is_slice_centers_solved(slice_index, th, l1_tracker):
            raise RuntimeError(
                f"Failed to solve slice {slice_index} (row {row}) after {max_iterations} iterations"
            )

    def _solve_face_row(
        self,
        face_tracker: FaceTracker,
        row: int,
        th: FacesTrackerHolder,
        l1_tracker: FaceTracker
    ) -> bool:
        """Solve a single row on a single face.

        Brings the face to front, then tries sources in this order:
        1. UP face (already in position)
        2. BACK face (commutator supports this directly)
        3. LEFT face (brought to UP)
        4. RIGHT face (brought to UP)
        5. Same face different row (move piece out first)

        Note: D face is Layer 1 (solved) - we skip it.

        Returns True if any work was done.
        """
        from cube.domain.algs import Algs

        target_color = face_tracker.color
        face = face_tracker.face

        # Check if this row is already solved
        if self._is_face_row_solved(face, row, target_color):
            return False

        # Bring target face to front
        self._centers.cmn.bring_face_front(face)

        # Now work on the row (face is now at front position)
        cube = self.cube
        front = cube.front
        op = self._slv.op

        work_done = False

        # First try UP and BACK as sources (no rotation needed)
        for source in [cube.up, cube.back]:
            if self._is_face_row_solved(front, row, target_color):
                return work_done
            if self._try_source_for_row(front, row, target_color, source):
                work_done = True

        # Try L and R by bringing to UP (track and undo rotations)
        setup_alg = Algs.NOOP
        for adj_face in [cube.left, cube.right]:
            if self._is_face_row_solved(front, row, target_color):
                break

            # Bring adjacent face to UP
            rotate_alg = self._centers._bring_face_up_preserve_front(adj_face)
            setup_alg = setup_alg + rotate_alg

            # Now cube.up has our source
            if self._try_source_for_row(front, row, target_color, cube.up):
                work_done = True

        # Undo all setup rotations
        if setup_alg != Algs.NOOP:
            op.play(setup_alg.prime)

        return work_done

    def _try_source_for_row(
        self,
        front: Face,
        row: int,
        target_color: Color,
        source_face: Face
    ) -> bool:
        """Try to fix centers in row using pieces from source_face.

        Returns True if any work was done.
        """
        work_done = False
        for col in range(self.n_slices):
            center = front.center.get_center_slice((row, col))
            if center.color == target_color:
                continue  # Already correct

            if self._fix_single_center(front, row, col, target_color, source_face):
                work_done = True

        return work_done

    def _fix_single_center(
        self,
        target_face: Face,
        row: int,
        col: int,
        target_color: Color,
        source_face: Face
    ) -> bool:
        """Fix a single center position using block commutator.

        Uses NxNCenters._block_communicator internally.

        Returns True if successful.
        """
        # Check if source face has the color we need
        if not self._has_color_on_face(source_face, target_color):
            return False

        # Use a 1x1 block commutator targeting (row, col)
        from cube.domain.solver.common.big_cube.NxNCenters import _SearchBlockMode

        # The block is just the single position
        rc1 = (row, col)
        rc2 = (row, col)

        # Try the commutator - it will search for matching source
        return self._centers._block_communicator(
            target_color,
            target_face,
            source_face,
            rc1, rc2,
            _SearchBlockMode.BigThanSource
        )

    def _is_face_row_solved(self, face: Face, row: int, target_color: Color) -> bool:
        """Check if a specific row on a face has all correct colors."""
        for col in range(self.n_slices):
            if face.center.get_center_slice((row, col)).color != target_color:
                return False
        return True

    def _has_color_on_face(self, face: Face, color: Color) -> bool:
        """Check if face has at least one center of the given color."""
        for row in range(self.n_slices):
            for col in range(self.n_slices):
                if face.center.get_center_slice((row, col)).color == color:
                    return True
        return False

    def solve_all_slice_centers(
        self, th: FacesTrackerHolder, l1_tracker: FaceTracker
    ) -> None:
        """Solve all middle slice ring centers.

        Uses NxNCenters.solve_single_face for each side face.
        The commutator affects multiple rows, so we solve entire faces
        rather than row by row.
        """
        # Get all side face trackers (not L1 or its opposite)
        side_trackers = self.get_side_face_trackers(th, l1_tracker)

        # Solve each side face completely
        for face_tracker in side_trackers:
            self._centers.solve_single_face(th, face_tracker)
