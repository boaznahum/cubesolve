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

from itertools import chain
from typing import TYPE_CHECKING, Sequence, Any, Iterable, Generator

from cube.domain.model import CenterSlice, EdgeWing, PartSlice
from cube.domain.model.Edge import Edge
from cube.domain.model.Slice import Slice
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges
from cube.domain.solver.common.SolverHelper import SolverHelper
from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.tracker.trackers import FaceTracker
from cube.domain.solver.direct.lbl import _lbl_config, _common
from cube.domain.solver.direct.lbl._LBLNxNCenters import NxNCenters2
from cube.domain.solver.direct.lbl._LBLNxNEdges import _LBLNxNEdges
from cube.domain.solver.direct.lbl._common import setup_l1, _get_side_face_trackers
from cube.utils.text_cube_viewer import print_cube

if TYPE_CHECKING:
    from cube.domain.solver.protocols.SolverElementsProvider import SolverElementsProvider


class _LBLSlices(SolverHelper):
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
        self._centers = NxNCenters2(self, preserve_cage=True)
        self._edges = _LBLNxNEdges(self, advanced_edge_parity=False)



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

    def _is_slice_centers_and_edges_solved(
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
        pieces: tuple[Sequence[EdgeWing], Sequence[CenterSlice]] = slice_obj.get_slices_by_index(slice_index)

        pieces_to_test: list[Iterable[PartSlice[Any]]] = []
        if _lbl_config.BIG_LBL_RESOLVE_CENTER_SLICES:
            pieces_to_test.append(pieces[1])
        if _lbl_config.BIG_LBL_RESOLVE_EDGES_SLICES:
            pieces_to_test.append(pieces[0])

        # todo:even: works for odd only, in odd the actual color is from the tracker
        return all ( slice_piece.match_faces  for slice_piece in chain(*pieces_to_test) )
        # # Check each center piece has the correct color for its face
        # for center in center_pieces:
        #     if center.color != required_colors[center.face.name]:
        #         return False
        #
        # return True

    def count_solved_slice_centers(
            self, th: FacesTrackerHolder, l1_tracker: FaceTracker
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
            all_solved = all(e.match_faces for e in self._get_row_pieces(l1_tracker, slice_row))

            if all_solved:
                count += 1
            else:
                break  # Stop at first unsolved slice

        return count


    def _get_row_pieces(
            self, l1_tracker: FaceTracker, slice_row: int
    ) -> Generator[PartSlice]:
        """Get all pieces (center slices and/or edge wings) at a given slice row.

        Args:
            l1_tracker: Face tracker for Layer 1 face
            slice_row: Distance from L1 face (0 = closest to L1)

        Yields:
            PartSlice objects at the given row based on config flags
            (BIG_LBL_RESOLVE_CENTER_SLICES and BIG_LBL_RESOLVE_EDGES_SLICES)
        """

        # Get the slice sandwiched between L1 face and its opposite
        # (e.g., L1=D → E slice, L1=L → M slice, L1=F → S slice)
        slice_name = self.cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_tracker.face_name)
        slice_layout = self.cube.layout.get_slice(slice_name)

        # Convert L1-relative distance to slice coordinate system
        cube_slice_index = slice_layout.distance_from_face_to_slice_index(
            l1_tracker.face_name, slice_row, self.n_slices
        )

        slice_name = self.cube.layout.get_slice_sandwiched_between_face_and_opposite(l1_tracker.face_name)
        slice_obj: Slice = self.cube.get_slice(slice_name)

        # Get edge wings and center slices at this slice index
        # We only care about center slices (index [1])
        pieces: tuple[Sequence[EdgeWing], Sequence[CenterSlice]] = slice_obj.get_slices_by_index(cube_slice_index)

        pieces_to_test: list[Iterable[PartSlice[Any]]] = []
        if _lbl_config.BIG_LBL_RESOLVE_CENTER_SLICES:
            pieces_to_test.append(pieces[1])
        if _lbl_config.BIG_LBL_RESOLVE_EDGES_SLICES:
            pieces_to_test.append(pieces[0])

        yield from chain(*pieces_to_test)



    # =========================================================================
    # Edge parity detection for even cubes
    # =========================================================================

    def _get_orthogonal_edges(self, l1_tracker: FaceTracker) -> list[Edge]:
        """Get the 4 edges orthogonal to Layer 1 (don't touch L1 or L3).

        These are the only edges affected by middle slice solving in LBL method.
        Dynamically determined based on which face is Layer 1.

        In LBL method:
        - Layer 1 (D face): edges DF, DR, DB, DL - solved first
        - Middle slices: only affect orthogonal edges FL, FR, BL, BR
        - Layer n (U face): edges UF, UR, UB, UL - solved last

        Args:
            l1_tracker: Face tracker for Layer 1 (determines orientation)

        Returns:
            List of 4 edges that don't touch L1 face or its opposite.
        """
        l1_face = l1_tracker.face
        l3_face = l1_face.opposite

        # Orthogonal edges don't touch L1 or L3
        return [e for e in self.cube.edges
                if e._f1 not in (l1_face, l3_face)
                and e._f2 not in (l1_face, l3_face)]

    def _check_and_fix_edge_parity(self, l1_tracker: FaceTracker) -> bool:
        """Check for and fix edge parity in orthogonal edges after solving all slices.

        Only checks the 4 orthogonal edges since those are the only ones
        solved during middle slice solving in LBL method.

        Edge parity occurs when exactly one edge cannot be fully paired
        (its wings have mixed colors). This is a mathematical property
        of even cubes - when it happens, a parity algorithm must be applied.

        Behavior depends on _lbl_config.ADVANCED_EDGE_PARITY:
        - Non-advanced (False): Parity algorithm scrambles edges, caller must repeat
        - Advanced (True): Parity algorithm fixes edges completely, we assert after

        Args:
            l1_tracker: Face tracker for Layer 1 (determines which edges are orthogonal)

        Returns:
            True if parity was detected and fixed, False otherwise.
            Caller should repeat edge solving if True and non-advanced mode.
        """
        orthogonal_edges = self._get_orthogonal_edges(l1_tracker)
        unsolved = [e for e in orthogonal_edges if not e.is3x3]

        if len(unsolved) == 1:
            # Edge parity - exactly one orthogonal edge cannot be paired
            self.debug(f"Edge parity detected on {unsolved[0]}")

            # Use original NxNEdges class with configured parity mode
            nxn_edges = NxNEdges(self, advanced_edge_parity=_lbl_config.ADVANCED_EDGE_PARITY)

            print_cube(self.cube, "Before parity")
            nxn_edges._do_edge_parity_on_edge(unsolved[0])
            print_cube(self.cube, "After parity")

            if _lbl_config.ADVANCED_EDGE_PARITY:
                # Advanced mode: parity algorithm should have fixed all edges
                # Verify orthogonal edges are all fixed
                assert all(e.is3x3 for e in orthogonal_edges), \
                    "Advanced parity should fix all orthogonal edges"
                # Also verify L1 edges are still fixed
                l1_edges = self._get_l1_edges(l1_tracker)
                assert all(e.is3x3 for e in l1_edges), \
                    "Advanced parity should not disturb L1 edges"

            return True

        return False

    def _get_l1_edges(self, l1_tracker: FaceTracker) -> list[Edge]:
        """Get the 4 edges on Layer 1 face (touch L1 but not L3).

        Args:
            l1_tracker: Face tracker for Layer 1

        Returns:
            List of 4 edges that touch L1 face.
        """
        l1_face = l1_tracker.face
        return [e for e in self.cube.edges
                if e._f1 is l1_face or e._f2 is l1_face]

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


        # help solver not to touch already solved
        _common.mark_slices_and_v_mark_if_solved(self._get_row_pieces(l1_white_tracker, face_row))

        if _lbl_config.BIG_LBL_RESOLVE_CENTER_SLICES:
            self._centers.solve_single_center_face_row(l1_white_tracker, target_face, face_row)

        if _lbl_config.BIG_LBL_RESOLVE_EDGES_SLICES:
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

        # in this files row_index is the distance between l1_face, no metter on which orientation

        # Setup L1 once at the start - positions white face down and will
        # clear all tracking when done. Individual slices accumulate their
        # tracking markers during solving.
        with setup_l1(self, l1_white_tracker) as l1_setup:
            n_to_solve = min(_lbl_config.NUMBER_OF_SLICES_TO_SOLVE, self.n_slices)

            parity_detected = False
            while True:

                if parity_detected:
                    self._slv._solve_layer3_corners(face_trackers)

                for row_index in range(n_to_solve):
                    with self._logger.tab(f"Solving face row {row_index}"):
                        self._solve_slice_row(row_index, face_trackers, l1_white_tracker)

                if False and not (n_to_solve < self.n_slices):
                    # Check for edge parity in orthogonal edges (can occur in even cubes)
                    if self._check_and_fix_edge_parity(l1_white_tracker):
                        if parity_detected:
                            # Parity detected twice - this is a bug
                            raise AssertionError("Edge parity detected twice - this should not happen")
                        parity_detected = True
                        # Parity algorithm changes cube orientation - realign L1
                        l1_setup.realign()

                        # becuase we start over, actaully we need tochnage to clean aonly slices pieces
                        _common.clear_all_type_of_markers(self.cube)
                        if not _lbl_config.ADVANCED_EDGE_PARITY:
                            # Non-advanced mode: parity scrambled edges, need to re-solve
                            self.debug("Non-advanced parity applied, re-solving edges")
                            continue  # Repeat the edge solving loop
                # No parity or advanced mode handled it - we're done
                break

            # Final verification: all orthogonal and L1 edges must be solved
            if False and  not (n_to_solve < self.n_slices):
                orthogonal_edges = self._get_orthogonal_edges(l1_white_tracker)
                l1_edges = self._get_l1_edges(l1_white_tracker)
                assert all(e.is3x3 for e in orthogonal_edges), \
                    f"Not all orthogonal edges solved: {[e for e in orthogonal_edges if not e.is3x3]}"
                assert all(e.is3x3 for e in l1_edges), \
                    f"Not all L1 (white) edges solved: {[e for e in l1_edges if not e.is3x3]}"
