"""
claude: # in these files row_index is the distance between l1_face, no metter on which orientation
go over all methods and checkit match the definition asked me if you are not sue

Layer-by-Layer NxN Solver - solves big cubes one horizontal layer at a time.

Unlike the reduction method (centers → edges → 3x3), this solver:
1. Solves Layer 1 (white face): centers → edges → corners
2. Solves Layer 2 to n-1 (middle slices): centers → edge wings
3. Solves Layer n (yellow face): centers → edges → corners

Layer 1 is determined by FIRST_FACE_COLOR config (default: WHITE), not by
assuming D face. This allows solving from any orientation.

For Layer 1, we:
1. Solve white-face centers using NxNCenters
2. Solve white-face edges using NxNEdges (only edges on white face)
3. Create a shadow 3x3 cube and solve Layer 1 (cross + corners) using Solvers3x3

Uses FacesTrackerHolder for even cube matching - see:
    solver/common/big_cube/FACE_TRACKER.md

See docs/design/layer_by_layer_nxn.md for detailed design.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from typing_extensions import deprecated

from cube.domain.algs import Algs
from cube.domain.exceptions import InternalSWError
from cube.domain.model import Corner, Part, Color
from cube.domain.solver.SolverName import SolverName
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.common.big_cube.NxNCenters import NxNCenters
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges
from cube.domain.solver.common.big_cube.ShadowCubeHelper import ShadowCubeHelper
from cube.domain.solver.direct.lbl import _common
from cube.domain.solver.direct.lbl._LBLL3Edges import _LBLL3Edges
from cube.domain.solver.direct.lbl._LBLSlices import _LBLSlices
from cube.domain.solver.exceptions import SolverFaceColorsChangedNeedRestartException
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import Solver, SolverResults, SolveStep
from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.tracker.trackers import FaceTracker

if TYPE_CHECKING:
    from cube.utils.logger_protocol import ILogger

class LayerByLayerNxNSolver(BaseSolver):
    """
    Layer-by-Layer solver for NxN cubes.

    Solves the cube one horizontal layer at a time.

    Layer 1 (white face - determined by FIRST_FACE_COLOR config):
    - Solve centers: (n-2)² center pieces
    - Solve edges: 4 edges × (n-2) wings each
    - Solve corners: 4 corners via shadow 3x3

    Layer 2 to n-1 (middle slices):
    - Solve centers: 4×(n-2) center pieces (ring on side faces)
    - Solve edge wings: 4 wings (one from each middle edge)

    Layer n (opposite face):
    - Like Layer 1 but with restricted moves
    """

    __slots__ = ["_nxn_edges", "_shadow_helper", "_lbl_slices"]

    def __init__(self, op: OperatorProtocol, parent_logger: "ILogger") -> None:
        """
        Create a Layer-by-Layer solver.

        Args:
            op: Operator for cube manipulation
            parent_logger: Parent logger (cube.sp.logger for root solver)

        Note:
            Layer 1 color is determined by FIRST_FACE_COLOR config
            (accessed via config.first_face_color and FaceTracker).
        """
        super().__init__(op, parent_logger, logger_prefix="Big-LBL")

        # Reuse NxNEdges for edge solving
        self._nxn_edges = NxNEdges(self, advanced_edge_parity=False)

        self._shadow_helper = ShadowCubeHelper(self)

        # LBL slices helper - wraps NxNCenters and NxNEdges for slice operations
        self._lbl_slices = _LBLSlices(self)

        # L3 edges helper - solves L3 edges without disturbing L1/middle
        self._l3_edges = _LBLL3Edges(self)

    # =========================================================================
    # Public properties/methods (Solver protocol order)
    # =========================================================================

    @property
    def get_code(self) -> SolverName:
        return SolverName.LBL_BIG

    @property
    def status(self) -> str:
        """Return current solving status."""
        if self.is_solved:
            return "Solved"

        # Create fresh tracker holder for status check
        # Note: We rely on tracker majority algorithm being deterministic.
        # If issue #51 (tracker majority bug) is real, trackers might not be
        # reproducible across calls, causing inconsistent status reports.
        with FacesTrackerHolder(self) as th:
          with self.cube.with_faces_color_provider(th):
            layer1_done = self._is_layer1_solved(th)

            if not layer1_done:
                # Check Layer 1 sub-steps
                centers_done = self._is_layer1_centers_solved(th)
                l1_edges=self._is_layer1_edges_solved(th)
                l1_cross = self._is_layer1_edges_and_cross_solved(th)

                if centers_done and l1_cross:
                    return "L1:Cross"
                elif centers_done and l1_edges:
                    return "L1:Edges"
                elif centers_done:
                    return "L1:Center"
                else:
                    return "L1:Pending"

            # Layer 1 done - check middle slices
            n_slices = self.cube.n_slices
            l1_tracker = self._get_layer1_tracker(th)
            solved_slices = self._lbl_slices.count_solved_slice_centers(l1_tracker)

            return f"L1:Done|Sl:{solved_slices}/{n_slices}"

    def _is_l2_slices_solved(self) -> bool:

        """
        Take to account L1 orientation
        :return:
        """
        with FacesTrackerHolder(self) as th:
          with self.cube.with_faces_color_provider(th):

            if not self._is_layer1_solved(th):
                return False

            if not self._is_l2_slices_solved_ignore_rotation():
                return False


            # l1 solved, L2 slices solved

            # so now make sure l1 edges are on faces

            return all(e.match_faces for e in self._get_layer1_tracker(th).face.edges)

    def _is_l2_slices_solved_ignore_rotation(self) -> bool:
        with FacesTrackerHolder(self) as th:
          with self.cube.with_faces_color_provider(th):

            l1_tracker = self._get_layer1_tracker(th)
            solved_slices = self._lbl_slices.count_solved_slice_centers(l1_tracker)

            return solved_slices == self.cube.n_slices

    def is_solved_phase(self, what: SolveStep) -> bool:
        with FacesTrackerHolder(self) as th:
          with self.cube.with_faces_color_provider(th):
            return self.is_solved_phase_with_tracker(th, what)

    def is_solved_phase_with_tracker(self, th:FacesTrackerHolder, what: SolveStep) -> bool:
        """Check if a specific solving phase is complete.

        Args:
            what: The solve step to check.

        Returns:
            True if the phase is solved, False otherwise.

        Note:
            This will be made abstract in a future refactor.
            :param what:
            :param th:
        """
        match what:
            case SolveStep.LBL_L1_Ctr:
                return self._is_layer1_centers_solved(th)

            case SolveStep.LBL_L1_EDGES:
                return self._is_layer1_edges_solved(th)

            case SolveStep.L1x:
                return self._is_layer1_cross_solved(th)

            case SolveStep.LBL_L1:
                return self._is_layer1_solved(th)

            case SolveStep.LBL_L2_SLICES:
                if not self._is_layer1_solved(th):
                    return False
                l1_tracker = self._get_layer1_tracker(th)
                return self._lbl_slices.count_solved_slice_centers(l1_tracker) == self.cube.n_slices

            case SolveStep.LBL_L3_CENTER:
                if not self._is_layer1_solved(th):
                    return False
                l1_tracker = self._get_layer1_tracker(th)
                if self._lbl_slices.count_solved_slice_centers(l1_tracker) != self.cube.n_slices:
                    return False
                return self._is_layer3_centers_solved(th)

            case SolveStep.LBL_L3_CROSS:
                if not self._is_layer1_solved(th):
                    return False
                l1_tracker = self._get_layer1_tracker(th)
                if self._lbl_slices.count_solved_slice_centers(l1_tracker) != self.cube.n_slices:
                    return False
                if not self._is_layer3_centers_solved(th):
                    return False
                return self._is_layer3_cross_solved(th)

            case SolveStep.ALL:
                return self.is_solved

            case _:
                raise ValueError(f"Unsupported step for is_solved_phase: {what}")

    def supported_steps(self) -> list[SolveStep]:
        """Return list of solve steps this solver supports.

        Note: SolveStep.ALL is implicit for all solvers (not listed here).
        Slice steps are dynamically added based on cube size.
        """
        steps = [
            SolveStep.LBL_L1_Ctr,     # Layer 1 centers only
            SolveStep.LBL_L1_EDGES,            # Layer 1 cross (centers + edges)
            SolveStep.L1x,            # Layer 1 cross (centers + edges)
            SolveStep.LBL_L1,         # Layer 1 complete
            SolveStep.LBL_L2_SLICES, # All middle slices centers
            SolveStep.LBL_L3_CENTER,
            SolveStep.LBL_L3_EDGES,
            SolveStep.LBL_L3_CROSS

        ]

        return steps

    # =========================================================================
    # Protected methods (AbstractSolver)
    # =========================================================================

    def _solve_impl(self, what: SolveStep) -> SolverResults:

        max_iterations = 3
        iterations = 0


        while True:
            # 1. first iteration
            # 2. Retry after face changed
            # 3 Error
            iterations += 1
            if iterations >= max_iterations:
                raise InternalSWError("Too many iterations for solver")

            try:
                return self._solve_impl2(what)
            except SolverFaceColorsChangedNeedRestartException as _:
                self.debug("Retrying after face colors changed")
                continue

        assert False # to satisfy pyCharm we not really can reach here


    def _solve_impl2(self, what: SolveStep) -> SolverResults:
        """Solve using Layer-by-Layer method.

        Args:
            what: Which step to solve (ALL, LBL_L1, LBL_L1_Ctr, L1x)
        """
        sr = SolverResults()

        if self.is_solved:
            return sr


        # it i wll be called again in the loop in case of parity detection
        _common.clear_all_type_of_markers(self.cube)

        # Create fresh tracker holder for this solve operation
        # Note: We rely on tracker majority algorithm being deterministic.
        # If issue #51 (tracker majority bug) is real, trackers might not be
        # reproducible across calls, causing solving to fail.
        with FacesTrackerHolder(self) as th:
          with self.cube.with_faces_color_provider(th):
            match what:
                case SolveStep.LBL_L1_Ctr:
                    # Layer 1 centers only
                    self._solve_layer1_centers(th)

                case SolveStep.LBL_L1_EDGES:
                    # Layer 1 cross (centers + edges paired + edges positioned)
                    self._solve_layer1_centers(th)
                    self._solve_layer1_edges(th)

                case SolveStep.L1x:
                    # Layer 1 cross (centers + edges paired + edges positioned)
                    self._solve_layer1_centers(th)
                    self._solve_layer1_edges(th)
                    self._solve_layer1_cross(th)

                case SolveStep.LBL_L1:
                    # Layer 1 complete (centers + edges + corners)
                    self._solve_layer1_centers(th)
                    self._solve_layer1_edges(th)
                    self._solve_layer1_corners(th)

                case SolveStep.LBL_L2_SLICES:
                    # Layer 1 + middle slices centers only (for debugging)
                    self._solve_layer1_centers(th)
                    self._solve_layer1_edges(th)
                    self._solve_layer1_corners(th)
                    self._solve_l2_slices(th)

                case SolveStep.LBL_L3_CENTER:
                    self._solve_layer1_centers(th)
                    self._solve_layer1_edges(th)
                    self._solve_layer1_corners(th)
                    self._solve_l2_slices(th)
                    self._solve_layer3_centers(th)


                case SolveStep.LBL_L3_EDGES:
                    self._solve_layer1_centers(th)
                    self._solve_layer1_edges(th)
                    self._solve_layer1_corners(th)
                    self._solve_l2_slices(th)
                    self._solve_layer3_centers(th)
                    self._solve_layer3_edges(th)

                case SolveStep.LBL_L3_CROSS:
                    self._solve_layer1_centers(th)
                    self._solve_layer1_edges(th)
                    self._solve_layer1_corners(th)
                    self._solve_l2_slices(th)
                    self._solve_layer3_centers(th)
                    self._solve_layer3_edges(th)
                    self._solve_layer3_cross(th)

                case SolveStep.ALL:
                    # Full solve (currently only up to Layer 1 + slices centers)
                    self._solve_layer1_centers(th)
                    self._solve_layer1_edges(th)
                    self._solve_layer1_corners(th)
                    self._solve_l2_slices(th)

                    self._solve_layer3_centers(th)
                    self._solve_layer3_edges(th)
                    self._solve_layer3_cross(th)
                    self._solve_layer3_corners(th)

                case _:
                    raise ValueError(f"Unsupported step: {what}")

        return sr

    # =========================================================================
    # Private methods - State inspection (use tracker for even cube support)
    # =========================================================================

    def _get_layer1_tracker(self, th: FacesTrackerHolder) -> FaceTracker:
        """Get the Layer 1 tracker (determined by FIRST_FACE_COLOR config)."""
        return th.get_tracker_by_color(self.config.first_face_color)

    def _is_layer1_centers_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if Layer 1 face centers are all the same color."""
        l1_face = self._get_layer1_tracker(th).face
        return l1_face.center.is3x3

    def _is_layer3_centers_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if Layer 1 face centers are all the same color."""
        l3_face = self._get_layer1_tracker(th).face.opposite
        return l3_face.center.is3x3

    def _is_layer1_edges_solved(self, th: FacesTrackerHolder) -> bool:
        l1_tracker = self._get_layer1_tracker(th)
        l1_face = l1_tracker.face

        # they are not necessarily on face
        l1_color: Color = self.config.first_face_color
        white_edges = []
        for e in self.cube.edges:
            if e.is3x3 and l1_color in e.colors_id:
                white_edges.append(e)

        return len(white_edges) == 4


        # find all wing with l1 color

        # First check: all edges on L1 face must be paired (reduced to 3x3)
        return all(e.is3x3 for e in l1_edges)

    @deprecated("Use _is_layer1_edges_and_cross_solved")
    def _is_layer1_cross_solved(self, th: FacesTrackerHolder) -> bool:

        return self._is_layer1_edges_and_cross_solved(th)


    def _is_layer1_edges_and_cross_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if L1 edges are paired AND in position (allowing L1 face rotation).

        This method checks two conditions:
        1. All 4 edges on L1 face are paired (is3x3 = reduced to 3x3 state)
        2. The edges are in correct positions, possibly with L1 face rotated

        The "rotate and check" pattern handles the case where L1 face is rotated:
        ```
        Example: Cross solved but D rotated 90°
        ┌───┐       ┌───┐
        │ G │       │ R │   ← Green edge on Red face (wrong!)
        └───┘       └───┘
        But rotating D by 90° CCW fixes it → edges ARE in position,
        just the whole L1 face needs alignment.
        ```

        Uses cube.cqr.rotate_face_and_check() which:
        - Tries 0, 1, 2, 3 rotations of L1 face
        - Checks Part.all_match_faces() at each rotation
        - Returns rotation count (>=0) if found, -1 if none work
        - Restores cube state (query only, no side effects)

        Returns:
            True if edges are paired and can be aligned by rotating L1 face
        """
        l1_tracker = self._get_layer1_tracker(th)
        l1_face = l1_tracker.face

        if not self._is_layer1_edges_solved(th):
            return False


        # Second check: edges can be aligned by rotating L1 face
        def _is_cross() -> bool:
            return Part.all_match_faces(l1_face.edges)

        return self.cube.cqr.rotate_face_and_check(l1_face, _is_cross) >= 0

    def _is_layer3_edges_solved(self, th: FacesTrackerHolder) -> bool:

        l3_tracker = self._get_layer1_tracker(th).opposite
        l3_face = l3_tracker.face
        l3_edges = l3_face.edges

        # First check: all edges on L1 face must be paired (reduced to 3x3)
        return all(e.is3x3 for e in l3_edges)




    def _is_layer3_cross_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if Layer 1 cross is solved (edges paired AND in correct position).

        Uses tracker's face→color mapping for even cubes where only L1 centers
        are solved (other centers are still scrambled).

        See: EVEN_CUBE_MATCHING.md for why we can't use Part.match_faces here.
        """
        if not self._is_layer3_edges_solved(th):
            return False

        l3_face = self._get_layer1_tracker(th).face.opposite
        # Use tracker colors instead of center colors for matching
        return all(th.part_match_faces(e) for e in l3_face.edges)

    def _is_layer1_corners_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if all Layer 1 corners are correctly positioned and oriented.

        For each corner on L1 face, verifies:
        1. The corner's sticker on L1 face has L1's color (correct orientation)
        2. The corner's stickers on adjacent side faces match the corresponding
           edge's stickers on those faces (correct position relative to solved edges)

        Why compare to EDGES instead of FACES?
        L1 face might be rotated (e.g., D rotated 90°). If we used Part.match_faces,
        corners would fail even though they're correctly positioned relative to edges.
        By comparing corner stickers to adjacent edge stickers, we check relative
        consistency - corners and edges should have the same colors on each side face.

        Uses Face.edges_of_corner() to find the two edges adjacent to each corner.

        See: EVEN_CUBE_MATCHING.md for why we can't use Part.match_faces here.
        """
        l1_face = self._get_layer1_tracker(th).face
        l1_face_color = l1_face.color
        # todo: Use tracker colors instead of center colors for matching
        c: Corner

        for c in l1_face.corners:
            if c.get_face_edge(l1_face).color != l1_face_color:
                return False

            edges = l1_face.edges_of_corner(c)

            for e in edges:
                other_face = e.get_other_face(l1_face)
                if c.get_face_edge(other_face).color != e.get_face_edge(other_face).color:
                    return False


        return True

    def _is_layer3_corners_solved(self, th: FacesTrackerHolder) -> bool:

        l3_face = self._get_layer1_tracker(th).face.opposite
        l3_face_color = l3_face.color
        # todo: Use tracker colors instead of center colors for matching
        c: Corner

        for c in l3_face.corners:
            if c.get_face_edge(l3_face).color != l3_face_color:
                return False

            edges = l3_face.edges_of_corner(c)

            for e in edges:
                other_face = e.get_other_face(l3_face)
                if c.get_face_edge(other_face).color != e.get_face_edge(other_face).color:
                    return False


        return True

    def _is_layer1_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if Layer 1 is completely solved (centers + edges + corners)."""
        return (self._is_layer1_centers_solved(th) and
                self._is_layer1_edges_and_cross_solved(th) and
                self._is_layer1_corners_solved(th))

    # =========================================================================
    # Private methods - Layer 1 solving
    # =========================================================================

    def _solve_layer1_centers(self, th: FacesTrackerHolder) -> None:
        """Solve only the Layer 1 face centers."""
        if self._is_layer1_centers_solved(th):
            return

        l1_tracker = self._get_layer1_tracker(th)
        self.debug(f"Solving Layer 1 centers ({l1_tracker.color.name} face only)")

        with self.op.annotation.annotate(h2=f"L1 centers ({l1_tracker.color.name})"):
            centers = NxNCenters(self, preserve_cage=False, tracker_holder=th)
            centers.solve_single_face(th, l1_tracker)

    def _solve_layer3_centers(self, th: FacesTrackerHolder) -> None:
        """Solve only the Layer 3 face centers."""
        if self._is_layer3_centers_solved(th):
            return

        l3_tracker = self._get_layer1_tracker(th).opposite
        self.debug(f"Solving Layer 3 centers ({l3_tracker.color.name} face only)")

        with self.op.annotation.annotate(h2=f"L3 centers ({l3_tracker.color.name})"):
            centers = NxNCenters(self, preserve_cage=False, tracker_holder=th)
            centers.solve_single_face(th, l3_tracker)

    def _solve_layer1_edges(self, th: FacesTrackerHolder) -> None:
        """Solve only the Layer 1 face edges."""
        if self._is_layer1_edges_solved(th):
            return

        l1_tracker = self._get_layer1_tracker(th)
        self.debug(f"Solving Layer 1 edges ({l1_tracker.color.name} face only)")

        with self.op.annotation.annotate(h2=f"L1 edges ({l1_tracker.color.name})"):
            # Use solve_face_edges to solve only Layer 1 face edges
            self._nxn_edges.solve_face_edges(l1_tracker)

    def _solve_layer3_edges(self, th: FacesTrackerHolder) -> None:
        """Solve only the Layer 3 face edges using safe algorithms.

        Uses _LBLL3Edges helper which uses commutator-based algorithms
        that preserve L1 and middle layer edges.
        """
        if self._is_layer3_edges_solved(th):
            return

        l3_tracker = self._get_layer1_tracker(th).opposite
        self.debug(f"Solving Layer 3 edges ({l3_tracker.color.name} face only)")

        with self.op.annotation.annotate(h2=f"L3 edges ({l3_tracker.color.name})"):
            self._l3_edges.do_l3_edges(l3_tracker)

    def _solve_layer1_cross(self, th: FacesTrackerHolder) -> None:
        """Solve Layer 1 cross (position edges) using shadow 3x3 approach."""
        if self._is_layer1_edges_and_cross_solved(th):
            return

        l1_tracker = self._get_layer1_tracker(th)
        self.debug(f"Solving Layer 1 cross ({l1_tracker.color.name} layer)")

        with self.op.annotation.annotate(h2=f"L1 cross ({l1_tracker.color.name})"):
            # Solve using shadow cube approach with Solvers3x3
            self._solve_layer1_with_shadow(th, SolveStep.L1x)

    def _solve_layer3_cross(self, th: FacesTrackerHolder) -> None:
        """Solve Layer 1 cross (position edges) using shadow 3x3 approach."""

        assert self._is_layer3_edges_solved(th)

        if self._is_layer3_cross_solved(th):
            return

        l1_tracker = self._get_layer1_tracker(th).opposite
        self.debug(f"Solving Layer 3 cross ({l1_tracker.color.name} layer)")

        with self.op.annotation.annotate(h2=f"L3 cross ({l1_tracker.color.name})"):
            # Solve using shadow cube approach with Solvers3x3
            self._solve_layer1_with_shadow(th, SolveStep.L3x)

    def _solve_layer1_corners(self, th: FacesTrackerHolder) -> None:
        """Solve Layer 1 corners using shadow 3x3 approach."""
        if self._is_layer1_corners_solved(th):
            return

        l1_tracker = self._get_layer1_tracker(th)
        self.debug(f"Solving Layer 1 corners ({l1_tracker.color.name} layer)")

        with self.op.annotation.annotate(h2=f"L1 corners ({l1_tracker.color.name})"):
            # Solve using shadow cube approach with Solvers3x3
            self._solve_layer1_with_shadow(th, SolveStep.L1)

    def _solve_layer3_corners(self, th: FacesTrackerHolder) -> None:
        """Solve Layer 1 corners using shadow 3x3 approach."""
        if self._is_layer3_corners_solved(th):
            return

        l3_tracker = self._get_layer1_tracker(th).opposite
        self.debug(f"Solving Layer 3 corners ({l3_tracker.color.name} layer)")

        with self.op.annotation.annotate(h2=f"L3 corners ({l3_tracker.color.name})"):
            # Solve using shadow cube approach with Solvers3x3
            self._solve_layer1_with_shadow(th, SolveStep.L3)

    def _solve_layer1_with_shadow(self, th: FacesTrackerHolder, what: SolveStep) -> None:
        """Create shadow 3x3 and solve Layer 1 using beginner method.

        Uses the proper pattern from CageNxNSolver:
        1. Create shadow 3x3 cube
        2. Create DualOperator (wraps shadow + real operator)
        3. Use Solvers3x3.beginner() - a real 3x3 solver
        4. Solve with SolveStep.L1 to only do cross + corners
        :param th:
        """
        from cube.application.commands.DualOperator import DualOperator
        from cube.domain.solver.Solvers3x3 import Solvers3x3

        # Verify source cube is valid before creating shadow
        assert self.cube.is_sanity(force_check=True), "Source NxN cube invalid before shadow creation"

        # this is a copy of cage is doing, why not add an helper for shadow operations !!!
        # Create shadow 3x3 cube (includes sanity check via set_3x3_colors)
        shadow_cube = self._shadow_helper.create_shadow_cube_from_faces_and_cube(th)
        assert shadow_cube.is_sanity(force_check=True), "Shadow cube invalid before solving"

        if shadow_cube.solved:
            self.debug("Shadow cube already solved")
            return

        # Early-exit optimization: Check if requested step is already done on shadow.
        # This avoids creating DualOperator and solver when not needed.
        # Cost: O(4) to check edges, O(4) to check corners - trivial vs full solve.
        shadow_l1_face = shadow_cube.color_2_face(self.config.first_face_color)
        edges_solved = all(e.match_faces for e in shadow_l1_face.edges)
        corners_solved = all(c.match_faces for c in shadow_l1_face.corners)

        if what == SolveStep.L1x and edges_solved:
            self.debug("Shadow cube L1 cross already solved")
            return
        if what == SolveStep.L1 and edges_solved and corners_solved:
            self.debug("Shadow cube Layer 1 already solved")
            return

        # Create DualOperator: wraps shadow cube + real operator
        dual_op = DualOperator(shadow_cube, self._op)

        # Use beginner method for L1 solving (same approach as CageNxNSolver)
        # we cannot use kochima becuase it konw to solve only valid cube and only whole cube
        shadow_solver = Solvers3x3.beginner(dual_op, self._logger)

        # Solve only L1 (cross + corners)
        # Cast: BeginnerSolver3x3 is both Solver3x3Protocol AND Solver (via BaseSolver)
        self._run_child_solver(cast(Solver, shadow_solver), what)

        # Verify shadow cube is still valid after solving
        assert shadow_cube.is_sanity(force_check=True), "Shadow cube invalid after solving"

        # Verify Layer 1 is actually solved on shadow cube
        shadow_l1 = shadow_cube.color_2_face(self.config.first_face_color)
        if what == SolveStep.L1x:
            assert all(e.match_faces for e in shadow_l1.edges), "Shadow cube L1 cross not solved after solve_3x3"
        elif what == SolveStep.L1:
            assert all(e.match_faces for e in shadow_l1.edges), "Shadow cube L1 edges not solved after solve_3x3"
            assert all(c.match_faces for c in shadow_l1.corners), "Shadow cube L1 corners not solved after solve_3x3"

    # =========================================================================
    # Private methods - Middle slices solving
    # =========================================================================

    def _solve_l2_slices(self, face_trackers: FacesTrackerHolder) -> None:
        """Solve all middle slice ring centers + edges (bottom to top).

        Delegates to _LBLSlices helper which wraps NxNCenters and NxNEdges.
        """
        l1_tracker = self._get_layer1_tracker(face_trackers)

        # bug here, maybe need rotation
        if self._is_l2_slices_solved():
            return

        # this should be done in the helper, not here:
        if self._is_l2_slices_solved_ignore_rotation():
            for _ in range(3):
                self.op.play(Algs.of_face(l1_tracker.face.name))
                if self._is_l2_slices_solved():
                    return

            raise InternalSWError("How di we reach here?")

        else:
            self._lbl_slices.solve_all_faces_all_rows(face_trackers, l1_tracker)

        # After solving, L1 edges may not match equatorial face colors
        # (e.g. if global prealign changed face colors). Fix with D rotation.
        if not self._is_l2_slices_solved():
            if self._is_l2_slices_solved_ignore_rotation():
                with FacesTrackerHolder(self) as fix_th:
                    fix_l1 = self._get_layer1_tracker(fix_th)
                    for _ in range(3):
                        self.op.play(Algs.of_face(fix_l1.face.name))
                        if self._is_l2_slices_solved():
                            return

    # =========================================================================
    # Statistics (override AbstractSolver)
    # =========================================================================

    def reset_statistics(self) -> None:
        """Reset solver statistics before solving."""
        self._lbl_slices.reset_statistics()

    def get_statistics(self) -> dict[int, int]:
        """Return block solving statistics."""
        return self._lbl_slices.get_statistics()

    def display_statistics(self) -> None:
        """Display solver statistics after solving."""
        self._lbl_slices.display_statistics()
