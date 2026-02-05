"""
LBL Slices Helper - wraps NxNCenters and NxNEdges for layer-by-layer slice solving.

Coordinate Convention - row_distance_from_l1:
=============================================
In this module, `row_distance_from_l1` (or similar names like `face_row`) represents
the distance from the L1 (white) face, NOT the row index in the face's LTR system.

- row_distance_from_l1=0: The row/column closest to L1 (touching the shared edge)
- row_distance_from_l1=1: The next row/column away from L1
- row_distance_from_l1=n-1: The row/column furthest from L1

This abstraction is orientation-independent. See cube_layout.py's
get_orthogonal_index_by_distance_from_face() for full documentation with diagrams.

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

from cube.domain.exceptions import InternalSWError
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.tracker.trackers import FaceTracker
from cube.domain.solver.direct.lbl import _lbl_config, _common
from cube.domain.solver.direct.lbl._LBLNxNCenters import NxNCenters2
from cube.domain.solver.direct.lbl._LBLNxNEdges import _LBLNxNEdges
from cube.domain.solver.direct.lbl._common import setup_l1, _get_side_face_trackers, _get_row_pieces

if TYPE_CHECKING:
    from cube.domain.solver.direct.lbl.LayerByLayerNxNSolver import LayerByLayerNxNSolver


class _LBLSlices(SolverHelper):
    """Helper for solving middle slices in layer-by-layer method.

    Wraps NxNCenters and NxNEdges with slice-based operations.

    Attributes:
        centers: NxNCenters helper for center solving
        edges: NxNEdges helper for edge pairing
    """

    __slots__ = ["_slv", "_centers", "_edges"]

    def __init__(self, slv: LayerByLayerNxNSolver) -> None:

        super().__init__(slv, "_LBLSlices")

        """Create LBL slices helper.

        Args:
            slv: LayerByLayerNxNSolver instance (for cube access and operations)
        """
        self._slv: LayerByLayerNxNSolver = slv
        # preserve_cage=True to preserve Layer 1 edges during center solving
        self._centers = NxNCenters2(self, preserve_cage=True)
        self._edges = _LBLNxNEdges(self)

    # =========================================================================
    # Statistics
    # =========================================================================

    def reset_statistics(self) -> None:
        """Reset statistics for all sub-helpers."""
        self._centers.reset_statistics()

    def get_block_statistics(self) -> dict[int, int]:
        """Get block solving statistics from centers helper."""
        return self._centers.get_statistics()

    # =========================================================================
    # State inspection
    # =========================================================================

    def count_solved_slice_centers(
            self, l1_tracker: FaceTracker
    ) -> int:
        """Count consecutive solved slice rings starting from Layer 1.

        claud: most of this description should be moved to _get_row_pieces

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
        count = 0
        for slice_row in range(self.n_slices):
            all_solved = self._row_solved(l1_tracker, slice_row)

            if all_solved:
                count += 1
            else:
                break  # Stop at first unsolved slice

        return count

    def _row_solved(self, l1_tracker: FaceTracker, slice_row: int) -> bool:
        return all(e.match_faces for e in _get_row_pieces(self.cube, l1_tracker, slice_row))

    # =========================================================================
    # Solving operations
    # =========================================================================

    def _solve_slice_row(
            self, face_row: int, th: FacesTrackerHolder, l1_white_tracker: FaceTracker
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
            face_row: Which face row to solve (0 = closest to D)
            th: FacesTrackerHolder for face color tracking
            l1_white_tracker: Layer 1 face tracker
        """
        side_trackers: list[FaceTracker] = _get_side_face_trackers(th, l1_white_tracker)

        # help solver not to touch already solved
        _common.mark_slices_and_v_mark_if_solved(_get_row_pieces(self.cube, l1_white_tracker, face_row))

        # avoid rotations later we will add more in centers and edges
        if self._row_solved(l1_white_tracker, face_row):
            return

        for target_face in side_trackers:
                self._solve_face_row(l1_white_tracker, target_face, face_row)

    def _solve_face_row(self, l1_white_tracker: FaceTracker,
                        target_face: FaceTracker,
                        face_row: int
                        ) -> None:

        MAX_ITERATIONS = 10
        n_iteration = 0
        n_pieces_were_solved = 0
        while True:
            n_iteration += 1
            if n_iteration > MAX_ITERATIONS:
                raise InternalSWError("Maximum number of iterations reached")

            if _lbl_config.BIG_LBL_RESOLVE_CENTER_SLICES:
                self._centers.solve_single_center_face_row(l1_white_tracker, target_face, face_row)

            if _lbl_config.BIG_LBL_RESOLVE_EDGES_SLICES:
                self._edges.solve_single_center_face_row(l1_white_tracker, target_face, face_row)

            if self._row_solved(l1_white_tracker, face_row):
                break

            n_pieces_solved = sum ( e.match_faces for e in _common._get_row_pieces(self.cube, l1_white_tracker, face_row ))

            if n_pieces_solved <=  n_pieces_were_solved:
                break # no progress

            n_pieces_were_solved = n_pieces_solved



        # and still i dont understand why !!!!
        self.debug(lambda : f"Solving row {face_row} took {n_iteration} iterations ‼️‼️‼️")





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

        # in this files row_index is the distance between l1_face, no metter on which orientation

        # Setup L1 once at the start - positions white face down and will
        # clear all tracking when done. Individual slices accumulate their
        # tracking markers during solving.
        with setup_l1(self, l1_white_tracker):
            n_to_solve = min(_lbl_config.NUMBER_OF_SLICES_TO_SOLVE, self.n_slices)

            for row_index in range(n_to_solve):
                with self._logger.tab(f"Solving face row {row_index}"):
                    self._solve_slice_row(row_index, face_trackers, l1_white_tracker)

                    if not self._row_solved(l1_white_tracker, row_index):
                        raise InternalSWError(f"Row {row_index} not solved")
