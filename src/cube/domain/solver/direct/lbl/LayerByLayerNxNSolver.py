"""Layer-by-Layer NxN Solver - solves big cubes one horizontal layer at a time.

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

See docs/design/layer_by_layer_nxn.md for detailed design.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.solver.SolverName import SolverName
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.solver.common.big_cube.NxNCenters import NxNCenters
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges
from cube.domain.solver.common.big_cube.ShadowCubeHelper import ShadowCubeHelper
from cube.domain.solver.common.big_cube._FaceTracker import FaceTracker
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolverResults, SolveStep

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube


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

    __slots__ = ["_nxn_edges", "_shadow_helper", "_tracker_holder"]

    def __init__(self, op: OperatorProtocol) -> None:
        """
        Create a Layer-by-Layer solver.

        Args:
            op: Operator for cube manipulation

        Note:
            Layer 1 color is determined by FIRST_FACE_COLOR config
            (accessed via config.first_face_color and FaceTracker).
        """
        super().__init__(op)

        # Reuse NxNEdges for edge solving
        self._nxn_edges = NxNEdges(self, advanced_edge_parity=False)

        self._shadow_helper = ShadowCubeHelper(self)

        # Persistent tracker holder - created once, reused for all operations
        self._tracker_holder: FacesTrackerHolder | None = None

    # =========================================================================
    # Public properties/methods (Solver protocol order)
    # =========================================================================

    @property
    def tracker_holder(self) -> FacesTrackerHolder:
        """Get or create the persistent tracker holder.

        Creates trackers on first access and reuses them for all operations.
        This ensures consistent face tracking throughout solving and status checks.
        """
        if self._tracker_holder is None:
            self._tracker_holder = FacesTrackerHolder(self)
        return self._tracker_holder

    def cleanup_trackers(self) -> None:
        """Clean up tracker marks from center slices.

        Call this when done with the solver to remove tracking attributes.
        """
        if self._tracker_holder is not None:
            self._tracker_holder.cleanup()
            self._tracker_holder = None

    @property
    def get_code(self) -> SolverName:
        return SolverName.LBL_DIRECT

    @property
    def status(self) -> str:
        """Return current solving status."""
        if self.is_solved:
            return "Solved"

        # Use persistent tracker for status checks
        th = self.tracker_holder
        layer1_done = self._is_layer1_solved(th)

        if layer1_done:
            return "L1:Done"
        else:
            # Check sub-steps
            centers_done = self._is_layer1_centers_solved(th)
            edges_done = self._is_layer1_edges_solved(th)

            if centers_done and edges_done:
                return "L1:Ctr+Edg"
            elif centers_done:
                return "L1:Ctr"
            else:
                return "L1:Pending"

    def supported_steps(self) -> list[SolveStep]:
        """Return list of solve steps this solver supports.

        Note: SolveStep.ALL is implicit for all solvers (not listed here).
        """
        return [
            SolveStep.LBL_L1_Ctr,   # Layer 1 centers only
            SolveStep.L1x,          # Layer 1 cross (centers + edges)
            SolveStep.LBL_L1,       # Layer 1 complete
        ]

    # =========================================================================
    # Protected methods (AbstractSolver)
    # =========================================================================

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        """Solve using Layer-by-Layer method.

        Args:
            what: Which step to solve (ALL, LBL_L1, LBL_L1_Ctr, L1x)
        """
        sr = SolverResults()

        if self.is_solved:
            return sr

        # Use persistent tracker holder (created once, reused for all operations)
        th = self.tracker_holder

        match what:
            case SolveStep.LBL_L1_Ctr:
                # Layer 1 centers only
                self._solve_layer1_centers(th)

            case SolveStep.L1x:
                # Layer 1 cross (centers + edges paired + edges positioned)
                self._solve_layer1_centers(th)
                self._solve_layer1_edges(th)
                self._solve_layer1_cross(th)

            case SolveStep.ALL | SolveStep.LBL_L1:
                # Layer 1 complete (centers + edges + corners)
                self._solve_layer1_centers(th)
                self._solve_layer1_edges(th)
                self._solve_layer1_corners(th)

            case _:
                raise ValueError(f"Unsupported step: {what}")

        return sr

    # =========================================================================
    # Private methods - State inspection (use tracker for even cube support)
    # =========================================================================

    def _get_layer1_tracker(self, th: FacesTrackerHolder) -> FaceTracker:
        """Get the Layer 1 tracker (determined by FIRST_FACE_COLOR config).

        Use this during solving when tracker_holder is available.
        """
        return th.get_tracker_by_color(self.config.first_face_color)

    def _is_layer1_centers_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if Layer 1 face centers are all the same color."""
        l1_face = self._get_layer1_tracker(th).face
        return l1_face.center.is3x3

    def _is_layer1_edges_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if all Layer 1 face edges are paired (reduced to 3x3)."""
        l1_face = self._get_layer1_tracker(th).face
        return all(e.is3x3 for e in l1_face.edges)

    def _is_layer1_cross_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if Layer 1 cross is solved (edges paired AND in correct position).

        Uses tracker's face→color mapping for even cubes where only L1 centers
        are solved (other centers are still scrambled).

        See: EVEN_CUBE_MATCHING.md for why we can't use Part.match_faces here.
        """
        if not self._is_layer1_edges_solved(th):
            return False

        l1_face = self._get_layer1_tracker(th).face
        # Use tracker colors instead of center colors for matching
        return all(th.part_match_faces(e) for e in l1_face.edges)

    def _is_layer1_corners_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if all Layer 1 corners are in correct position with correct orientation.

        Uses tracker's face→color mapping for even cubes where only L1 centers
        are solved (other centers are still scrambled).

        See: EVEN_CUBE_MATCHING.md for why we can't use Part.match_faces here.
        """
        l1_face = self._get_layer1_tracker(th).face
        # Use tracker colors instead of center colors for matching
        return all(th.part_match_faces(c) for c in l1_face.corners)

    def _is_layer1_solved(self, th: FacesTrackerHolder) -> bool:
        """Check if Layer 1 is completely solved (centers + edges + corners)."""
        return (self._is_layer1_centers_solved(th) and
                self._is_layer1_edges_solved(th) and
                self._is_layer1_corners_solved(th))

    # =========================================================================
    # Private methods - Layer 1 solving
    # =========================================================================

    def _solve_layer1(self, sr: SolverResults, th: FacesTrackerHolder) -> None:
        """Solve Layer 1: centers → edges → corners."""

        if self._is_layer1_solved(th):
            self.debug("Layer 1 already solved")
            return

        l1_tracker = self._get_layer1_tracker(th)
        with self.op.annotation.annotate(h1=f"Layer 1 ({l1_tracker.color.name} face)"):
            # Step 1: Solve Layer 1 centers
            if not self._is_layer1_centers_solved(th):
                self._solve_layer1_centers(th)

            # Step 2: Solve Layer 1 edges
            if not self._is_layer1_edges_solved(th):
                self._solve_layer1_edges(th)

            # Step 3: Solve Layer 1 corners using shadow 3x3
            if not self._is_layer1_corners_solved(th):
                self._solve_layer1_corners(th)

    def _solve_layer1_centers(self, th: FacesTrackerHolder) -> None:
        """Solve only the Layer 1 face centers."""
        if self._is_layer1_centers_solved(th):
            return

        l1_tracker = self._get_layer1_tracker(th)
        self.debug(f"Solving Layer 1 centers ({l1_tracker.color.name} face only)")

        with self.op.annotation.annotate(h2=f"L1 centers ({l1_tracker.color.name})"):
            # Use NxNCenters.solve_single_face to solve just the Layer 1 face
            centers = NxNCenters(self, preserve_cage=False)
            centers.solve_single_face(th, l1_tracker)

    def _solve_layer1_edges(self, th: FacesTrackerHolder) -> None:
        """Solve only the Layer 1 face edges."""
        if self._is_layer1_edges_solved(th):
            return

        l1_tracker = self._get_layer1_tracker(th)
        self.debug(f"Solving Layer 1 edges ({l1_tracker.color.name} face only)")

        with self.op.annotation.annotate(h2=f"L1 edges ({l1_tracker.color.name})"):
            # Use solve_face_edges to solve only Layer 1 face edges
            self._nxn_edges.solve_face_edges(l1_tracker)

    def _solve_layer1_cross(self, th: FacesTrackerHolder) -> None:
        """Solve Layer 1 cross (position edges) using shadow 3x3 approach."""
        if self._is_layer1_cross_solved(th):
            return

        l1_tracker = self._get_layer1_tracker(th)
        self.debug(f"Solving Layer 1 cross ({l1_tracker.color.name} layer)")

        with self.op.annotation.annotate(h2=f"L1 cross ({l1_tracker.color.name})"):
            # Solve using shadow cube approach with Solvers3x3
            self._solve_layer1_with_shadow(th, SolveStep.L1x)

    def _solve_layer1_corners(self, th: FacesTrackerHolder) -> None:
        """Solve Layer 1 corners using shadow 3x3 approach."""
        if self._is_layer1_corners_solved(th):
            return

        l1_tracker = self._get_layer1_tracker(th)
        self.debug(f"Solving Layer 1 corners ({l1_tracker.color.name} layer)")

        with self.op.annotation.annotate(h2=f"L1 corners ({l1_tracker.color.name})"):
            # Solve using shadow cube approach with Solvers3x3
            self._solve_layer1_with_shadow(th, SolveStep.L1)

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

        # Check if requested step is already done on shadow
        # claude: we computing costly but maybe using it , any way the
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

        # Use a real 3x3 solver - beginner method for L1
        # claud: use the same configuration as cage used for solver helper
        shadow_solver = Solvers3x3.beginner(dual_op)

        # Solve only L1 (cross + corners)
        shadow_solver.solve_3x3(what=what)

        # Verify shadow cube is still valid after solving
        assert shadow_cube.is_sanity(force_check=True), "Shadow cube invalid after solving"

        # Verify Layer 1 is actually solved on shadow cube
        shadow_l1 = shadow_cube.color_2_face(self.config.first_face_color)
        if what == SolveStep.L1x:
            assert all(e.match_faces for e in shadow_l1.edges), "Shadow cube L1 cross not solved after solve_3x3"
        elif what == SolveStep.L1:
            assert all(e.match_faces for e in shadow_l1.edges), "Shadow cube L1 edges not solved after solve_3x3"
            assert all(c.match_faces for c in shadow_l1.corners), "Shadow cube L1 corners not solved after solve_3x3"

    def _copy_state_to_shadow(self, shadow: "Cube", th: FacesTrackerHolder) -> None:
        """Copy corner/edge state from NxN cube to shadow 3x3."""
        # Get colors from NxN cube as 3x3 snapshot
        colors_3x3 = self._cube.get_3x3_colors()

        # Override centers with face_colors mapping
        modified = colors_3x3.with_centers(th.get_face_colors())

        # Apply to shadow cube
        shadow.set_3x3_colors(modified)
