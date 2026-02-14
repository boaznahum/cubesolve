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

from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator, Tuple

from cube.domain.algs import SlicedSliceAlg
from cube.domain.algs.Algs import Algs
from cube.domain.exceptions import InternalSWError
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.tracker.face_trackers import FaceTracker
from cube.domain.solver.direct.lbl import _lbl_config, _common
from cube.domain.solver.direct.lbl._LBLNxNCenters import _LBLNxNCenters
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

    __slots__ = ["_slv", "_last_centers", "_edges", "_sanity_check"]

    def __init__(self, slv: LayerByLayerNxNSolver) -> None:

        super().__init__(slv, "_LBLSlices")

        """Create LBL slices helper.

        Args:
            slv: LayerByLayerNxNSolver instance (for cube access and operations)
        """
        self._slv: LayerByLayerNxNSolver = slv
        self._last_centers: _LBLNxNCenters | None = None
        self._edges = _LBLNxNEdges(self)
        self._sanity_check: bool = slv.config.lbl_sanity_check

    def _create_centers(self, th: FacesTrackerHolder) -> _LBLNxNCenters:
        """Create fresh _LBLNxNCenters with the given tracker holder."""
        centers = _LBLNxNCenters(self, tracker_holder=th, preserve_cage=True)
        self._last_centers = centers
        return centers

    # =========================================================================
    # Statistics
    # =========================================================================

    def reset_statistics(self) -> None:
        """Reset statistics for all sub-helpers."""
        if self._last_centers is not None:
            self._last_centers.reset_statistics()

    def get_statistics(self) -> dict[int, int]:
        """Return block solving statistics (empty dict if no centers created)."""
        if self._last_centers is None:
            return {}
        return self._last_centers.get_statistics()

    def display_statistics(self) -> None:
        """Display block solving statistics."""
        if self._last_centers is None:
            return
        stats = self._last_centers.get_statistics()

        if not stats:
            return  # No blocks solved

        # Build display string (sorted by block size)
        parts = [f"{size}x1:{count}" for size, count in sorted(stats.items())]
        total = sum(stats.values())

        self.debug(f"Block statistics: {', '.join(parts)} (total: {total} blocks)")

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
    # Pre-alignment
    # =========================================================================

    def count_all_rows_solved(self, l1_tracker: FaceTracker, n_rows: int) -> int:
        """Count solved rows.
        stop on first not solved roe
        """

        count = 0
        for slice_row in range(n_rows):
            all_solved = self._row_solved(l1_tracker, slice_row)

            if all_solved:
                count += 1
            else:
                break  # Stop at first unsolved slice

        return count


    def sanity_check_previous_are_solved(self, l1_tracker: FaceTracker, row_index: int, op_name: str) -> None:
        if self._sanity_check:
            for prev_row_index in range(row_index):
                assert self._row_solved(l1_tracker,
                                        prev_row_index), f"op name: {op_name} @ row={row_index}, found previous not solved {prev_row_index}"

    @contextmanager
    def with_sanity_check_previous_are_solved(
        self,
        l1_tracker: FaceTracker,
        row_index: int,
        operation_name: str
    ) -> Generator[None, None, None]:
        """Context manager that performs before/after sanity checks.

        Checks that previous rows are solved before and after the operation.
        If an exception occurs during the operation, the after check is skipped.

        IMPORTANT PATTERN - Exception-aware context manager:
        =====================================================
        This context manager uses a subtle but powerful Python pattern:
        Code AFTER yield only runs if the with-block completes normally.

        Execution flow:
        1. Code BEFORE yield: Always runs (setup/before-check)
        2. yield: Transfers control to the with-block
        3. Code AFTER yield: Only runs if with-block completes WITHOUT exception

        If an exception is raised in the with-block:
        - Execution does NOT continue after yield
        - Exception propagates immediately
        - After-check is skipped (preventing cascading errors)

        Why this matters here:
        - User presses abort button → exception raised
        - Without this pattern: after-check would also fail, creating second error
        - With this pattern: after-check is skipped, only original exception shown

        Note: If you need cleanup that ALWAYS runs (even on exception), use
        try-finally around yield. Here we intentionally want to skip the
        after-check on exceptions.

        Args:
            l1_tracker: Layer 1 face tracker
            row_index: Current row index being worked on
            operation_name: Description of the operation (e.g., "removing piece from face")

        Usage:
            with self.with_sanity_check_previous_are_solved(tracker, row, "operation"):
                # Your code here
                pass
        """
        # Before check - always runs
        self.sanity_check_previous_are_solved(l1_tracker, row_index, f"before {operation_name}")

        yield

        # After check - only runs if no exception occurred during yield
        # (If user pressed abort, execution never reaches here)
        self.sanity_check_previous_are_solved(l1_tracker, row_index, f"after {operation_name}")

    def _global_center_slice_prealign(self, l1_white_tracker: FaceTracker) -> bool:
        """Try rotating the center E-slice for global alignment.

        The center E-slice contains the face center pieces that determine
        face.color. Rotating it changes which face has which color. If the
        cube's equatorial faces are misaligned by 1-3 rotations, this fixes
        ALL rows at once.

        Must be called BEFORE solve_all_faces_all_rows. If this returns True,
        face colors changed and the caller must rebuild FacesTrackerHolder.

        Only applies to odd cubes (even cubes have no fixed center piece).

        Returns:
            True if the center slice was rotated (face colors changed).
        """
        n_slices = self.n_slices

        # Only odd cubes have a center slice
        if n_slices % 2 == 0:
            return False

        # Position L1 on D for correct row indexing
        from cube.domain.solver.direct.lbl._common import position_l1
        position_l1(self, l1_white_tracker)

        center_row = n_slices // 2

        cube = self.cube
        slice_name = cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_white_tracker.face_name)
        slice_layout = cube.layout.get_slice(slice_name)
        cube_slice_index = slice_layout.distance_from_face_to_slice_index(
            l1_white_tracker.face_name, center_row, n_slices
        )
        center_slice_alg = Algs.of_slice(slice_name)[cube_slice_index + 1]

        n_to_solve = min(_lbl_config.NUMBER_OF_SLICES_TO_SOLVE, n_slices)

        # Count total solved pieces across all rows (rotation 0)
        best_count = self.count_all_rows_solved(l1_white_tracker, n_to_solve)
        best_rot = 0

        with self.op.with_query_restore_state():
            for n_rot in range(1, 4):
                    self.play(center_slice_alg)
                    count = self.count_all_rows_solved(l1_white_tracker, n_to_solve)
                    if count > best_count:
                        best_count = count
                        best_rot = n_rot

        if best_rot > 0:
            self.debug(lambda : f"Global center-slice pre-align: {best_rot}x rotation "
                       f"({best_count} total pieces aligned)")
            self.debug(lambda :f"[LBL] Global center-slice pre-align: {best_rot}x rotation "
                  f"({best_count} total pieces aligned)")
            # Rotate the center E-slice to change equatorial face colors

            self.play(center_slice_alg * best_rot)

            # caller will raise exception to restart solver
            return True

        return False

    def _get_slice_alg_for_slice_optimization(self, face_row: int, l1_white_tracker: FaceTracker) -> SlicedSliceAlg | None:
        """Get the slice algorithm for a given row.

        Returns None for center slice on odd cubes (rotating it would move
        face center pieces, changing face.color and breaking tracker mapping).
        """
        cube = self.cube
        n_slices = self.n_slices

        # Skip center slice on odd cubes
        middle = n_slices // 2
        if n_slices % 2 == 1:
            # 5: middle=2:  0 1 [2] 3 4
            if face_row == middle:
                return None
        else:
            # 6: middle=3:  0 1 [2] [3] 4 5
            if face_row == middle or face_row == middle - 1:
                return None

        slice_name = cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_white_tracker.face_name)
        slice_layout = cube.layout.get_slice(slice_name)
        cube_slice_index = slice_layout.distance_from_face_to_slice_index(
            l1_white_tracker.face_name, face_row, n_slices
        )
        return Algs.of_slice(slice_name)[cube_slice_index + 1]  # 1-based

    def _find_row_best_pre_alignment(self, face_row: int, l1_white_tracker: FaceTracker) -> Tuple[SlicedSliceAlg, int] | None:
        """Find the best slice pre-alignment rotation count (0-3).

        Uses with_query_restore_state() to test each rotation without
        affecting the cube. Returns the number of rotations that maximizes
        already-correct pieces, or 0 if no rotation helps.

        Face colors are frozen during the query to prevent tracker displacement:
        slice rotations move center pieces (and their tracker marks), which can
        cause two trackers to temporarily point to the same face.
        """

        # boaz: patch
        if False:
            return 0

        slice_alg: SlicedSliceAlg | None = self._get_slice_alg_for_slice_optimization(face_row, l1_white_tracker)
        # Also None for odd middle slice
        if slice_alg is None:
            return None

        cube = self.cube

        parent: FacesTrackerHolder = l1_white_tracker.parent

        contains_center_tracer = any(1 for e in _common.get_center_row_pieces(cube, l1_white_tracker, None, face_row) if parent.contain_center_tracker(e))
        if contains_center_tracer:
            self.debug(lambda : f"☑️☑️☑️☑️☑️☑️☑️☑️☑️ Protecting row {face_row} it contains center tracker ☑️☑️☑️☑️☑️☑️☑️☑️☑️ ")
            return None

        # Count currently solved pieces (rotation 0) #claude: skip if it is the max available
        best_count = sum(1 for e in _get_row_pieces(cube, l1_white_tracker, face_row) if e.match_faces)
        if best_count == _common.get_expected_number_of_row_pieces(cube):
            return None  # already solved

        best_rotations = 0

        if True:
            with self.op.with_query_restore_state():
                for n_rotations in range(1, 4):
                    self.play(slice_alg)
                    count = sum(1 for e in _get_row_pieces(cube, l1_white_tracker, face_row) if e.match_faces)
                    if count > best_count:
                        best_count = count
                        best_rotations = n_rotations
        else:
            for n_rotations in range(1, 4):
                self.play(slice_alg)
                count = sum(1 for e in _get_row_pieces(cube, l1_white_tracker, face_row) if e.match_faces)
                if count > best_count:
                    best_count = count
                    best_rotations = n_rotations
            #undo all
            self.play((slice_alg*3).prime)

        if best_rotations == 0:
            return None
        else:
            return slice_alg, best_rotations

    # =========================================================================
    # Solving operations
    # =========================================================================

    def _solve_row_core(
            self, face_row: int, th: FacesTrackerHolder, l1_white_tracker: FaceTracker
    ) -> None:
        """Core solve logic for a single row (no pre-alignment)."""
        side_trackers: list[FaceTracker] = _get_side_face_trackers(th, l1_white_tracker)

        # help solver not to touch already solved
        _common.mark_slices_and_v_mark_if_solved(_get_row_pieces(self.cube, l1_white_tracker, face_row))

        # avoid rotations later we will add more in centers and edges
        if self._row_solved(l1_white_tracker, face_row):
            return

        for target_face in side_trackers:
            self._solve_face_row(l1_white_tracker, target_face, face_row, th)

    def _solve_slice_row(
            self, face_row: int, th: FacesTrackerHolder, l1_white_tracker: FaceTracker
    ) -> None:
        """Solve ring centers for a single slice with optional pre-alignment.

        Strategy:
        1. Find the best pre-alignment rotation (0-3) using query mode
        2. If improvement found: apply pre-alignment rotation
        3. Run the core solver (which handles the rest regardless)

        Note: _find_best_pre_alignment returns 0 for center slices on odd cubes
        (rotating them would change face.color and break tracker mapping).

        Args:
            face_row: Which face row to solve (0 = closest to D)
            th: FacesTrackerHolder for face color tracking
            l1_white_tracker: Layer 1 face tracker
        """

        with self.with_sanity_check_previous_are_solved(l1_white_tracker, face_row, "optimization"):
            with l1_white_tracker.parent.sanity_check_before_after_same_colors("slice optimization", also_assert_cube_faces=True):
                alg_best_rotations: tuple[SlicedSliceAlg, int] | None = self._find_row_best_pre_alignment(face_row, l1_white_tracker)

                if alg_best_rotations is not None:
                    slice_alg = alg_best_rotations[0]
                    best_rotations = alg_best_rotations[1]
                    self.debug(f"Pre-align row {face_row}: rotating slice {best_rotations}x")
                    # Preserve tracker positions across the slice rotation.
                    # The rotation moves center pieces (and their tracker marks) between
                    # faces. We want the pieces to move, but tracker marks must stay on
                    # their original faces so face-color mapping remains valid.
                    with th.preserve_physical_faces():
                        self.play(slice_alg * best_rotations)

                    # Pre-alignment rotation moved pieces in this row — clear stale
                    # solved markers so the solver doesn't skip unsolved pieces.
                    # Only the current row is affected (slice rotation is per-row).
                    # Boaz: Is till dont understand it, how row that we first reach can have solved markers ? maybe we
                    # we have some outer loop ? or moving center pieces move a solved pieces to other place ?
                    _common.clear_pieces_solved_flags_and_markers(_get_row_pieces(self.cube, l1_white_tracker, face_row))

        with self.with_sanity_check_previous_are_solved(l1_white_tracker, face_row, "_solve_row_core"):
            self._solve_row_core(face_row, th, l1_white_tracker)

    def _solve_face_row(self, l1_white_tracker: FaceTracker,
                        target_face: FaceTracker,
                        face_row: int,
                        th: FacesTrackerHolder,
                        ) -> None:

        MAX_ITERATIONS = 10
        n_iteration = 0
        n_pieces_were_solved = 0
        while True:
            n_iteration += 1
            if n_iteration > MAX_ITERATIONS:
                raise InternalSWError("Maximum number of iterations reached")

            if _lbl_config.BIG_LBL_RESOLVE_CENTER_SLICES:
                self._create_centers(th).solve_single_center_face_row(l1_white_tracker, target_face, face_row)

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

        # Global center-slice pre-alignment: rotate the center E-slice
        # to maximize total solved pieces across all rows.
        # This changes face.color, so trackers must be rebuilt.
        self._global_center_slice_prealign(l1_white_tracker)

        # if rotated:
        #     raise SolverFaceColorsChangedNeedRestartException()
        #     # Face colors changed — rebuild trackers with new face colors
        #     with FacesTrackerHolder(self) as new_th:
        #         new_l1 = self._get_layer1_tracker(new_th)
        #         self._lbl_slices.solve_all_faces_all_rows(new_th, new_l1)


        # in this files row_index is the distance between l1_face, no metter on which orientation

        # Setup L1 once at the start - positions white face down and will
        # clear all tracking when done. Individual slices accumulate their
        # tracking markers during solving.
        n_to_solve = min(_lbl_config.NUMBER_OF_SLICES_TO_SOLVE, self.n_slices)

        with setup_l1(self, l1_white_tracker):

            for row_index in range(n_to_solve):
                with self._logger.tab(f"Solving face row {row_index}"):

                    with self.with_sanity_check_previous_are_solved(l1_white_tracker, row_index, "solving row"):
                        self._solve_slice_row(row_index, face_trackers, l1_white_tracker)

                        if not self._row_solved(l1_white_tracker, row_index):
                            raise InternalSWError(f"Row {row_index} not solved")


            assert self.count_all_rows_solved(l1_white_tracker, n_to_solve) == n_to_solve, f"Solved={self.count_all_rows_solved(l1_white_tracker, n_to_solve)} / {n_to_solve}"
