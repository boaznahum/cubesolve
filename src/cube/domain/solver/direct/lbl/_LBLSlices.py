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

from typing import TYPE_CHECKING, Sequence

from cube.domain.model import CenterSlice, EdgeWing, FaceName, Color
from cube.domain.model.Slice import Slice
from cube.domain.solver.common.SolverElement import SolverElement
from cube.domain.solver.common.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.solver.common.tracker.trackers import FaceTracker
from cube.domain.solver.direct.lbl.NxNCenters2 import NxNCenters2
from cube.domain.solver.direct.lbl._LBLNxNEdges import _LBLNxNEdges

if TYPE_CHECKING:
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
        self._edges = _LBLNxNEdges(slv, advanced_edge_parity=False)

    @property
    def centers(self) -> NxNCenters2:
        """Access to NxNCenters helper."""
        return self._centers

    @property
    def edges(self) -> _LBLNxNEdges:
        """Access to NxNEdges helper."""
        return self._edges

    # =========================================================================
    # Coordinate conversion
    # =========================================================================

    def _slice_to_row(self, slice_index: int) -> int:
        """Convert slice index (0=bottom) to row index on side faces.

        Formula: row = n_slices - 1 - slice_index

        Example for 5x5 (n_slices=3):
            slice 0 → row 2 (bottom row, closest to D)
            slice 1 → row 1 (middle row)
            slice 2 → row 0 (top row, closest to U)
        """
        return self.n_slices - 1 - slice_index

    # =========================================================================
    # Face helpers
    # =========================================================================

    def _get_side_face_trackers(
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

    def _is_slice_centers_solved(
            self, slice_index: int, th: FacesTrackerHolder, l1_tracker: FaceTracker
    ) -> bool:
        """Check if all ring centers for a specific slice are solved.

        A slice's ring centers are solved when every center in the corresponding
        row on all 4 side faces has the correct color for that face.

        Args:
            slice_index: 0 to n_slices-1 in slice coordinates not relative to L1
            th: FacesTrackerHolder for face color tracking
            l1_tracker: Layer 1 face tracker (to identify side faces)
        """

        slice_name = self.cube.layout.get_slice_name_parallel_to_face(l1_tracker.face_name)

        slice: Slice = self.cube.get_slice(slice_name)

        pieces: tuple[Sequence[EdgeWing], Sequence[CenterSlice]] = slice._get_slices_by_index(slice_index)

        center_pieces = pieces[1]

        # it is waste of time becuase ecnters are groupd:
        required_colors: dict[FaceName, Color] = {f.face_name : f.color for f in th.trackers}

        c: CenterSlice
        for c in center_pieces:
            if c.color != required_colors[c.face.name]:
                    return False

        return True

    def count_solved_slice_centers(
            self, th: FacesTrackerHolder, l1_tracker: FaceTracker
    ) -> int:
        """Count how many slices have their ring centers solved (from bottom up).

        Correctly handle cube orientation

        Counts consecutive solved slices starting from row 0 (relative to L1)
        Once an unsolved slice is found, stops counting.

        Claud: Im trying to do it independ on orientation, if it works we need to document it
        """

        # Find the slice sandwiched between L1 face and its opposite
        slice_name = self.cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_tracker.face_name)

        slice_layout = self.cube.layout.get_slice(slice_name)

        count = 0
        # slice_row as begin from L1
        for slice_row in range(self.n_slices):

            cube_slice_index = slice_layout.distance_from_face_to_slice_index(
                l1_tracker.face_name, slice_row, self.n_slices
            )

            if self._is_slice_centers_solved(cube_slice_index, th, l1_tracker):
                count += 1
            else:
                break
        return count

    # =========================================================================
    # Solving operations
    # =========================================================================

    def _solve_slice_centers(
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
        with self._centers._setup_l1(l1_white_tracker, slice_index):
            # Setup L1 once at the start - positions white face down and will
            # clear all tracking when done. Individual slices accumulate their
            # tracking markers during solving.
            side_trackers = self._get_side_face_trackers(th, l1_white_tracker)

            for target_face in side_trackers:
                self._solve_face_index(l1_white_tracker, target_face, slice_index)

    def _solve_face_index(
            self, l1_white_tracker: FaceTracker, target_face: FaceTracker, slice_index: int
    ) -> None:
        self._centers.solve_single_center_row_slice(l1_white_tracker, target_face, slice_index)

    def solve_all_slice_centers(
            self, face_trackers: FacesTrackerHolder, l1_white_tracker: FaceTracker
    ) -> None:
        """Solve all middle slice ring centers (bottom to top).

        Solves slices in order: 0, 1, 2, ... n_slices-1
        Each slice = one row on each of the 4 side faces.

        IMPORTANT: Layer 1 must be on DOWN for the commutator to work correctly.
        The commutator uses UP as source, so if Layer 1 is on UP, we'll mess it up.
        """
        # Solve all slices from bottom to top
        from cube.domain.solver.direct.lbl._lbl_config import NUMBER_OF_SLICES_TO_SOLVE
        for slice_index in range(min(NUMBER_OF_SLICES_TO_SOLVE, self.n_slices)):
            self._solve_slice_centers(slice_index, face_trackers, l1_white_tracker)
