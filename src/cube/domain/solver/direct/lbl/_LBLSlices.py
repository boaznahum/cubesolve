"""

claude: # in these files row_index is the distance between l1_face, no metter on which orientation
go over all methods and checkit match the definition asked me if you are not sue


LBL Slices Helper - wraps NxNCenters and NxNEdges for layer-by-layer slice solving.

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
from cube.domain.solver.direct.lbl._common import setup_l1, _get_side_face_trackers
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

    # =========================================================================
    # State inspection
    # =========================================================================

    def _is_slice_centers_solved(
            self, slice_index: int, th: FacesTrackerHolder, l1_tracker: FaceTracker
    ) -> bool:
        """Check if all ring centers for a specific slice are solved.

        This method is ORIENTATION-INDEPENDENT: it works regardless of which
        face is Layer 1 (D, U, F, B, L, or R). The geometry layer handles
        the coordinate translation.

        A slice's "ring" consists of 4×(n-2) center pieces forming a horizontal
        band around the cube at a specific height. The ring is solved when every
        center piece has the correct color for its face.

        How it works:
        1. Get the slice sandwiched between L1 face and its opposite
           (e.g., L1=D → E slice, which sits between D and U)
        2. Query that slice for center pieces at the given slice_index
        3. Check each center piece's color against the expected face color

        Args:
            slice_index: 0-based index in the SLICE's coordinate system
                         (not L1-relative). Use distance_from_face_to_slice_index()
                         to convert from L1-relative distance.
            th: FacesTrackerHolder providing face→color mapping for even cubes
            l1_tracker: Layer 1 face tracker (identifies which face is L1)

        Returns:
            True if all 4×(n-2) centers in this slice ring have correct colors
        """
        slice_name = self.cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_tracker.face_name)
        slice_obj: Slice = self.cube.get_slice(slice_name)

        # Get edge wings and center slices at this slice index
        # We only care about center slices (index [1])
        pieces: tuple[Sequence[EdgeWing], Sequence[CenterSlice]] = slice_obj._get_slices_by_index(slice_index)
        center_pieces = pieces[1]

        # Build expected color map from trackers (handles even cube color tracking)
        required_colors: dict[FaceName, Color] = {t.face_name: t.color for t in th.trackers}

        # Check each center piece has the correct color for its face
        for center in center_pieces:
            if center.color != required_colors[center.face.name]:
                return False

        return True

    def count_solved_slice_centers(
            self, th: FacesTrackerHolder, l1_tracker: FaceTracker
    ) -> int:
        """Count consecutive solved slice rings starting from Layer 1.

        ORIENTATION-INDEPENDENT DESIGN
        ==============================
        This method works regardless of which face is Layer 1. The key insight
        is separating "L1-relative distance" from "slice coordinate system":

        - slice_row: L1-relative distance (0 = adjacent to L1, n-1 = farthest)
        - cube_slice_index: Slice's own coordinate (0 = closest to rotation face)

        The geometry layer's distance_from_face_to_slice_index() handles translation.

        Example with 5x5 cube (n_slices=3):
        ===================================
        If L1 = D (white face down):
            - Slice is E (sandwiched between D and U)
            - E's rotation face is D, so E[0] is closest to D
            - slice_row=0 (adjacent to D) → cube_slice_index=0
            - slice_row=2 (adjacent to U) → cube_slice_index=2

        If L1 = U (cube flipped, white face up):
            - Slice is still E (sandwiched between U and D)
            - E's rotation face is still D
            - slice_row=0 (adjacent to U) → cube_slice_index=2 (farthest from D)
            - slice_row=2 (adjacent to D) → cube_slice_index=0

        The geometry layer's distance_from_face_to_slice_index() handles this
        translation automatically based on whether L1 is the slice's rotation
        face or its opposite.

        Args:
            th: FacesTrackerHolder providing face→color mapping
            l1_tracker: Layer 1 face tracker (identifies orientation)

        Returns:
            Number of consecutive solved slice rings (0 to n_slices),
            counting from L1 face upward. Stops at first unsolved slice.
        """
        # Get the slice sandwiched between L1 face and its opposite
        # (e.g., L1=D → E slice, L1=L → M slice, L1=F → S slice)
        slice_name = self.cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_tracker.face_name)
        slice_layout = self.cube.layout.get_slice(slice_name)

        count = 0
        for slice_row in range(self.n_slices):
            # Convert L1-relative distance to slice coordinate system
            cube_slice_index = slice_layout.distance_from_face_to_slice_index(
                l1_tracker.face_name, slice_row, self.n_slices
            )

            if self._is_slice_centers_solved(cube_slice_index, th, l1_tracker):
                count += 1
            else:
                break  # Stop at first unsolved slice

        return count

    # =========================================================================
    # Solving operations
    # =========================================================================

    def _solve_slice_row(
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
        side_trackers: list[FaceTracker] = _get_side_face_trackers(th, l1_white_tracker)

        for target_face in side_trackers:
                self._solve_face_row(l1_white_tracker, target_face, slice_index)

    def _solve_face_row(self, l1_white_tracker: FaceTracker,
                        target_face: FaceTracker,
                        face_row: int
                        ) -> None:
        self._centers.solve_single_center_face_row(l1_white_tracker, target_face, face_row)
        self._edges.solve_single_center_face_row(l1_white_tracker, target_face, face_row)


    def solve_all_faces_all_rows(
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

        # in this files row_index is the distance between l1_face, no metter on which orientation

        # Setup L1 once at the start - positions white face down and will
        # clear all tracking when done. Individual slices accumulate their
        # tracking markers during solving.
        with setup_l1(self, l1_white_tracker):
            for row_index in range(min(NUMBER_OF_SLICES_TO_SOLVE, self.n_slices)):
                with self._logger.tab(f"Solving face row {row_index}"):
                    self._solve_slice_row(row_index, face_trackers, l1_white_tracker)
