"""Cage Method NxN Solver - edges first, then corners, then centers.

The Cage method solves big cubes by:
1. Building the "cage" (edges + corners)
2. Filling the cage (centers using commutators)

See DESIGN.md for detailed algorithm description.

EDGE PARITY HANDLING:
====================
Edge parity is handled INSIDE NxNEdges.solve() - NOT by this orchestrator.
This is simpler than the reduction method because:

1. NxNEdges.solve() determines edge colors from the EDGE ITSELF:
   - For odd cubes (5x5, 7x7): Uses middle slice colors
   - For even cubes (4x4, 6x6): Uses majority color on edge
   - NO dependency on centers - works whether centers are solved or not!

2. Parity detection and fix happens inside NxNEdges.solve():
   - Solves first 11 edges using _do_first_11()
   - If 1 edge remains unsolved -> parity situation
   - Calls _do_last_edge_parity() to fix it
   - Re-solves remaining edges
   - Returns True if parity was detected/fixed

3. For ODD cubes (5x5, 7x7):
   - Parity is fully handled inside NxNEdges.solve()
   - The fixed center slice provides reference for each edge
   - No additional parity detection needed

4. For EVEN cubes (4x4, 6x6):
   - "Partial" edge parity (detectable during pairing) is handled
   - "Full" edge parity (all slices flipped same way) may remain
   - Full parity would be detected later during L3Cross solving
   - TODO: Decide if/how to handle this in cage method
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.solver.SolverName import SolverName
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.solver import SolveStep, SolverResults
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.beginner.NxNEdges import NxNEdges

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube


class CageNxNSolver(BaseSolver):
    """
    Cage method solver for NxN cubes.

    Solves in this order (per DESIGN.md):
    - Phase 1: Build the cage
        - Step 1a: Solve all EDGES (pair wings, place correctly)
        - Step 1b: Solve all CORNERS
    - Phase 2: Fill the cage
        - Step 2: Solve CENTERS using commutators

    Key insight: We can use ANY slice moves freely because centers are solved LAST.

    PARITY HANDLING:
    ================
    Edge parity is handled INSIDE NxNEdges.solve() automatically.
    See module docstring for details.

    - NxNEdges.solve() returns True if parity was detected and fixed
    - We track this in SolverResults._was_partial_edge_parity
    - For even cubes, additional "full" edge parity may exist (TODO)
    """

    __slots__ = ["_nxn_edges", "_solver_3x3"]

    def __init__(self, op: OperatorProtocol) -> None:
        """
        Create a Cage method solver.

        Args:
            op: Operator for cube manipulation
        """
        super().__init__(op)
        # =====================================================================
        # EDGE SOLVER SETUP
        # =====================================================================
        # Reuse NxNEdges for edge solving - it doesn't depend on centers.
        # NxNEdges determines edge colors from the edge itself:
        # - Odd cubes: middle slice defines edge color
        # - Even cubes: majority color on edge
        #
        # advanced_edge_parity flag controls parity algorithm:
        # - False: Simple M-slice algorithm (fast, disturbs edges slightly)
        # - True: Advanced R/L-slice algorithm (preserves edges better)
        #
        # TODO: Consider using advanced_edge_parity=True for cage method
        # since we want to preserve edge pairing as much as possible.
        # =====================================================================
        self._nxn_edges = NxNEdges(self, advanced_edge_parity=False)

        # =====================================================================
        # 3x3 SOLVER FOR CORNERS (Phase 1b)
        # =====================================================================
        # After edges are paired, use standard 3x3 solver for corners.
        # The 3x3 solver will solve L1, L2, L3 - treating the cube as a
        # virtual 3x3.
        #
        # WHY THIS WORKS (ODD CUBES ONLY):
        # - Face center IS fixed for odd cubes (5x5, 7x7)
        # - 3x3 solver uses face.center.color to determine face colors
        # - Scrambled inner center pieces don't affect corner placement
        #
        # WHY 3x3 SOLVER DOESN'T COMPLAIN:
        # - It never checks cube.is3x3
        # - Corners are identical on all cube sizes
        # - After Phase 1a, edges are paired (is3x3) - look like 3x3 edges
        # - It uses face.center.color which works for odd cubes
        #
        # EVEN CUBES NOT SUPPORTED:
        # - Even cubes have NO fixed center → face color undefined
        # - Would need FaceTracker to establish color mapping first
        # - See __todo_cage.md for future work
        # =====================================================================
        from cube.domain.solver.Solvers3x3 import Solvers3x3
        solver_name = self._cube.config.cage_3x3_solver
        self._solver_3x3 = Solvers3x3.by_name(solver_name, self._op)

    @property
    def get_code(self) -> SolverName:
        return SolverName.CAGE

    @property
    def status(self) -> str:
        """Return current solving status.

        Shows cage (edges + corners) status and center status separately.
        """
        if self.is_solved:
            return "Solved"

        # Check cage status (edges paired + corners positioned)
        edges_paired = self._are_edges_solved()
        edges_positioned = self._are_edges_positioned()
        corners_done = self._are_corners_solved()
        centers_done = self._are_centers_solved()

        # Cage = edges + corners
        cage_done = edges_paired and edges_positioned and corners_done

        parts: list[str] = []

        if cage_done:
            parts.append("Cage:Done")
        elif edges_paired:
            parts.append("Cage:Edges")  # Edges paired, corners pending
        else:
            parts.append("Cage:Pending")

        if centers_done:
            parts.append("Ctr:Done")
        else:
            parts.append("Ctr:Pending")

        return " ".join(parts)

    # =========================================================================
    # State inspection methods (STATELESS - inspect cube only)
    # =========================================================================

    def _are_edges_solved(self) -> bool:
        """Check if all edges are reduced to 3x3 (all wings paired)."""
        return all(e.is3x3 for e in self._cube.edges)

    def _are_edges_positioned(self) -> bool:
        """Check if all edges are in correct position (matching face colors).

        This is stronger than _are_edges_solved() which only checks pairing.
        After the 3x3 solver runs, edges should be both paired AND positioned.
        """
        return all(e.match_faces for e in self._cube.edges)

    def _are_corners_solved(self) -> bool:
        """Check if all corners are in correct position with correct orientation.

        A corner is "solved" when all its stickers match the face center colors.
        Uses Part.match_faces which checks each sticker against its face's center.

        NOTE: Only works for ODD cubes where face center is fixed.
        """
        # Part.match_faces checks if all stickers match their face colors
        return all(corner.match_faces for corner in self._cube.corners)

    def _are_centers_solved(self) -> bool:
        """Check if all centers are reduced to 3x3 (uniform color per face)."""
        return all(f.center.is3x3 for f in self._cube.faces)

    # =========================================================================
    # Main solve method
    # =========================================================================

    def solve(
        self,
        debug: bool | None = None,
        animation: bool | None = True,
        what: SolveStep = SolveStep.ALL
    ) -> SolverResults:
        """Solve using Cage method.

        Order: Edges -> Corners -> Centers
        """
        sr = SolverResults()

        if self.is_solved:
            return sr

        with self._op.with_animation(animation=animation):
            return self._solve_impl(sr)

    def _solve_impl(self, sr: SolverResults) -> SolverResults:
        """Internal solve implementation."""
        # =====================================================================
        # PHASE 1a: EDGE SOLVING
        # =====================================================================
        # Edge parity is handled INSIDE NxNEdges.solve():
        # - Solves 11 edges first
        # - If 1 edge left unsolved -> parity
        # - Fixes parity using M-slice or R/L-slice algorithm
        # - Re-solves remaining edges
        # - Returns True if parity was detected/fixed
        #
        # See module docstring and NxNEdges.solve() for details.
        # =====================================================================
        if not self._are_edges_solved():
            had_parity = self._solve_edges()
            if had_parity:
                sr._was_partial_edge_parity = True

        # =====================================================================
        # PHASE 1b: CORNER SOLVING (via 3x3 solver)
        # =====================================================================
        # After edges are paired, the cube is a "virtual 3x3".
        # Use standard 3x3 solver to solve L1, L2, L3.
        #
        # After this phase:
        # - Corners: SOLVED (correct position and orientation)
        # - Edges: SOLVED (paired and in correct position)
        # - Centers: SCRAMBLED (inner center pieces still mixed)
        #
        # NOTE: Only works for ODD cubes (5x5, 7x7) where face center
        # defines the face color. Even cubes need FaceTracker first.
        # =====================================================================
        if not self._cube.solved:
            self._solve_corners()

        # TODO: Phase 2 - centers (commutators)
        # Centers remain scrambled after Phase 1b.
        # Need commutators that preserve edges/corners.

        return sr

    # =========================================================================
    # Phase 1a: Edge solving (reuses NxNEdges)
    # =========================================================================

    def _solve_edges(self) -> bool:
        """
        Solve all edges - pair wings and place correctly.

        IMPLEMENTATION:
        ==============
        Reuses NxNEdges which handles everything:

        1. COLOR DETERMINATION (doesn't need centers):
           - Odd cubes: middle slice defines edge color
           - Even cubes: majority color on edge

        2. EDGE SOLVING:
           - Brings edge to front-left position
           - Fixes slices on same edge that are flipped
           - Finds matching slices from other edges
           - Uses E-slice moves to swap wings

        3. PARITY HANDLING (inside NxNEdges.solve()):
           - Solves 11 edges via _do_first_11()
           - If 1 edge left: parity detected
           - Calls _do_last_edge_parity() to fix
           - Re-solves remaining edges

        Returns:
            True if edge parity was detected and fixed
        """
        self.debug("Starting edge solving (using NxNEdges)")
        # NxNEdges.solve() returns True if parity was detected/fixed
        return self._nxn_edges.solve()

    # =========================================================================
    # Phase 1b: Corner solving (uses 3x3 solver)
    # =========================================================================

    def _solve_corners(self) -> None:
        """
        Solve corners using standard 3x3 solver.

        IMPLEMENTATION:
        ==============
        After edges are paired (Phase 1a), the cube is a "virtual 3x3".
        We use BeginnerSolver3x3.solve_3x3() which solves:
        - L1: White cross + white corners
        - L2: Middle layer edges
        - L3: Yellow cross, yellow corners (OLL + PLL)

        WHY THIS WORKS (ODD CUBES):
        - Face center IS fixed (defines face color)
        - 3x3 solver uses face.center.color correctly
        - Corners are identical on all cube sizes

        AFTER THIS METHOD:
        - Corners: SOLVED
        - Edges: SOLVED (were already paired)
        - Centers: SCRAMBLED (inner pieces still mixed)

        NOTE: Even cubes not supported - face color undefined.
        """
        self.debug("Starting corner solving (using 3x3 solver)")
        # solve_3x3() solves the cube as if it were a 3x3
        # Since edges are already paired, this effectively solves corners
        self._solver_3x3.solve_3x3()

    # =========================================================================
    # Phase 2: Center solving (TODO)
    # =========================================================================

    def _solve_centers(self) -> None:
        """
        Solve all centers using commutators.

        Since edges/corners are fixed, commutators only affect centers.
        """
        self.debug("Starting center solving")
        # TODO: Implement center solving with commutators
        # Key: Must use only commutators that preserve edges
        pass
