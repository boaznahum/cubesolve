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

from cube.domain.model import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.common.big_cube.FaceTrackerHolder import FaceTrackerHolder
from cube.domain.solver.common.big_cube.NxNCenters import NxNCenters
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face


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

    __slots__ = ["_nxn_edges"]

    def __init__(self, op: OperatorProtocol) -> None:
        """
        Create a Layer-by-Layer solver.

        Args:
            op: Operator for cube manipulation

        Note:
            Layer 1 color is determined by FIRST_FACE_COLOR config
            (accessed via cmn.white_face).
        """
        super().__init__(op)

        # Reuse NxNEdges for edge solving
        self._nxn_edges = NxNEdges(self, advanced_edge_parity=False)

    # =========================================================================
    # Public properties/methods (Solver protocol order)
    # =========================================================================

    @property
    def get_code(self) -> SolverName:
        return SolverName.LBL_DIRECT

    @property
    def status(self) -> str:
        """Return current solving status."""
        if self.is_solved:
            return "Solved"

        # Check layer-by-layer status
        layer1_done = self._is_layer1_solved()

        if layer1_done:
            return "L1:Done"
        else:
            # Check sub-steps
            centers_done = self._is_layer1_centers_solved()
            edges_done = self._is_layer1_edges_solved()

            if centers_done and edges_done:
                return "L1:Ctr+Edg"
            elif centers_done:
                return "L1:Ctr"
            else:
                return "L1:Pending"

    def supported_steps(self) -> list[SolveStep]:
        """Return list of solve steps this solver supports."""
        return [
            SolveStep.ALL,
            SolveStep.LBL_L1_Ctr,   # Layer 1 centers only
            SolveStep.LBL_L1_Edg,   # Layer 1 edges only
            SolveStep.LBL_L1,       # Layer 1 complete
        ]

    # =========================================================================
    # Protected methods (AbstractSolver)
    # =========================================================================

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        """Solve using Layer-by-Layer method.

        Args:
            what: Which step to solve (ALL, LBL_L1, LBL_L1_Ctr, LBL_L1_Edg)
        """
        sr = SolverResults()

        if self.is_solved:
            return sr

        # Create face tracker holder for center solving
        with FaceTrackerHolder(self) as tracker_holder:
            match what:
                case SolveStep.ALL:
                    # Full solve - Layer 1 for now
                    self._solve_layer1(sr, tracker_holder)

                case SolveStep.LBL_L1:
                    # Layer 1 complete
                    self._solve_layer1(sr, tracker_holder)

                case SolveStep.LBL_L1_Ctr:
                    # Layer 1 centers only
                    if not self._is_layer1_centers_solved():
                        self._solve_layer1_centers(tracker_holder)

                case SolveStep.LBL_L1_Edg:
                    # Layer 1 edges only (requires centers to be solved first)
                    if not self._is_layer1_edges_solved():
                        self._solve_layer1_edges()

                case _:
                    raise ValueError(f"Unsupported step: {what}")

        return sr

    # =========================================================================
    # Private methods - State inspection
    # =========================================================================

    def _get_layer1_face(self) -> "Face":
        """Get the Layer 1 face (determined by FIRST_FACE_COLOR config)."""
        return self.cmn.white_face

    def _is_layer1_centers_solved(self) -> bool:
        """Check if Layer 1 face centers are all the same color."""
        l1_face = self._get_layer1_face()
        return l1_face.center.is3x3

    def _is_layer1_edges_solved(self) -> bool:
        """Check if all Layer 1 face edges are paired (reduced to 3x3)."""
        l1_face = self._get_layer1_face()
        return all(e.is3x3 for e in l1_face.edges)

    def _is_layer1_corners_solved(self) -> bool:
        """Check if all Layer 1 corners are in correct position with correct orientation."""
        l1_face = self._get_layer1_face()
        return all(c.match_faces for c in l1_face.corners)

    def _is_layer1_solved(self) -> bool:
        """Check if Layer 1 is completely solved (centers + edges + corners)."""
        return (self._is_layer1_centers_solved() and
                self._is_layer1_edges_solved() and
                self._is_layer1_corners_solved())

    # =========================================================================
    # Private methods - Layer 1 solving
    # =========================================================================

    def _solve_layer1(self, sr: SolverResults, tracker_holder: FaceTrackerHolder) -> None:
        """Solve Layer 1: centers → edges → corners."""

        if self._is_layer1_solved():
            self.debug("Layer 1 already solved")
            return

        l1_face = self._get_layer1_face()
        with self.op.annotation.annotate(h1=f"Layer 1 ({l1_face.name.name} face)"):
            # Step 1: Solve Layer 1 centers
            if not self._is_layer1_centers_solved():
                self._solve_layer1_centers(tracker_holder)

            # Step 2: Solve Layer 1 edges
            if not self._is_layer1_edges_solved():
                self._solve_layer1_edges()

            # Step 3: Solve Layer 1 corners using shadow 3x3
            if not self._is_layer1_corners_solved():
                self._solve_layer1_corners(tracker_holder)

    def _solve_layer1_centers(self, tracker_holder: FaceTrackerHolder) -> None:
        """Solve only the Layer 1 face centers."""
        l1_face = self._get_layer1_face()
        self.debug(f"Solving Layer 1 centers ({l1_face.name.name} face only)")

        with self.op.annotation.annotate(h2="L1 centers"):
            # Use NxNCenters.solve_single_face to solve just the Layer 1 face
            centers = NxNCenters(self, preserve_cage=False)
            centers.solve_single_face(tracker_holder, l1_face)

    def _solve_layer1_edges(self) -> None:
        """Solve only the Layer 1 face edges."""
        l1_face = self._get_layer1_face()
        self.debug(f"Solving Layer 1 edges ({l1_face.name.name} face only)")

        with self.op.annotation.annotate(h2="L1 edges"):
            # Use solve_face_edges to solve only Layer 1 face edges
            self._nxn_edges.solve_face_edges(l1_face)

    def _solve_layer1_corners(self, tracker_holder: FaceTrackerHolder) -> None:
        """Solve Layer 1 corners using shadow 3x3 approach."""
        l1_face = self._get_layer1_face()
        self.debug(f"Solving Layer 1 corners ({l1_face.name.name} layer)")

        with self.op.annotation.annotate(h2="L1 corners"):
            # Get face colors from tracker holder
            face_colors = tracker_holder.get_face_colors()

            # Solve using shadow cube approach with Solvers3x3
            self._solve_layer1_with_shadow(face_colors)

    def _solve_layer1_with_shadow(self, face_colors: dict[FaceName, Color]) -> None:
        """Create shadow 3x3 and solve Layer 1 using beginner method.

        Uses the proper pattern from CageNxNSolver:
        1. Create shadow 3x3 cube
        2. Create DualOperator (wraps shadow + real operator)
        3. Use Solvers3x3.beginner() - a real 3x3 solver
        4. Solve with SolveStep.L1 to only do cross + corners
        """
        from cube.application.commands.DualOperator import DualOperator
        from cube.domain.model.Cube import Cube
        from cube.domain.solver.Solvers3x3 import Solvers3x3

        # Create shadow 3x3 cube
        shadow_cube = Cube(size=3, sp=self._cube.sp)
        shadow_cube.is_even_cube_shadow = True
        self._copy_state_to_shadow(shadow_cube, face_colors)

        if shadow_cube.solved:
            self.debug("Shadow cube already solved")
            return

        # Check if Layer 1 is already done on shadow
        # Use cmn.white_face to get the L1 face on shadow cube
        # (DualOperator will sync this with the real cube)
        shadow_l1_face = shadow_cube.color_2_face(self.cmn.white)
        if (all(c.match_faces for c in shadow_l1_face.corners) and
                all(e.match_faces for e in shadow_l1_face.edges)):
            self.debug("Shadow cube Layer 1 already solved")
            return

        # Create DualOperator: wraps shadow cube + real operator
        dual_op = DualOperator(shadow_cube, self._op)

        # Use a real 3x3 solver - beginner method for L1
        shadow_solver = Solvers3x3.beginner(dual_op)

        # Solve only L1 (cross + corners)
        shadow_solver.solve_3x3(what=SolveStep.L1)

    def _copy_state_to_shadow(self, shadow: "Cube", face_colors: dict[FaceName, Color]) -> None:
        """Copy corner/edge state from NxN cube to shadow 3x3."""
        # Get colors from NxN cube as 3x3 snapshot
        colors_3x3 = self._cube.get_3x3_colors()

        # Override centers with face_colors mapping
        modified = colors_3x3.with_centers(face_colors)

        # Apply to shadow cube
        shadow.set_3x3_colors(modified)
