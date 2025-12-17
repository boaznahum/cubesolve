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

    __slots__ = ["_nxn_edges"]

    def __init__(self, op: OperatorProtocol) -> None:
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

    @property
    def get_code(self) -> SolverName:
        return SolverName.CAGE

    @property
    def status(self) -> str:
        """Return current solving status."""
        if self.is_solved:
            return "Solved"

        # Check phases in order
        edges_done = self._are_edges_solved()
        corners_done = self._are_corners_solved()
        centers_done = self._are_centers_solved()

        parts: list[str] = []
        if edges_done:
            parts.append("E:Done")
        else:
            parts.append("E:Pending")

        if corners_done:
            parts.append("C:Done")
        else:
            parts.append("C:Pending")

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

    def _are_corners_solved(self) -> bool:
        """Check if all corners are in correct position with correct orientation."""
        # For now, we check if the cube would be solved if we ignore centers
        # This is a simplified check - proper implementation needs to verify
        # each corner is in its correct position
        cube = self._cube
        for corner in cube.corners:
            # Check if corner colors match the expected colors for its position
            # For odd cubes, use face center colors
            # For even cubes, need face color mapping (TODO)
            pass
        # Simplified: just check if 3x3 corners would be correct
        return True  # TODO: implement proper check

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

        # TODO: Phase 1b - corners
        # TODO: Phase 2 - centers

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
    # Phase 1b: Corner solving (TODO)
    # =========================================================================

    def _solve_corners(self) -> None:
        """
        Solve all corners using standard 3x3 methods.

        Corners are identical to 3x3 corners on any size cube.
        """
        self.debug("Starting corner solving")
        # TODO: Implement corner solving
        # Can reuse 3x3 corner algorithms
        pass

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
