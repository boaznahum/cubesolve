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
from cube.domain.solver.beginner.NxNCentersV3 import NxNCentersV3
from cube.domain.solver.common.VirtualFaceColor import (
    create_even_cube_face_trackers,
    virtual_face_colors_with_op,
)
from cube.utils.SSCode import SSCode

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
        self._solver_3x3 = Solvers3x3.by_name(solver_name, self._op, ignore_center_check=True)

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
        """Internal solve implementation.

        EVEN CUBE SUPPORT:
        =================
        Even cubes (4x4, 6x6) have no fixed center, so face.center.color
        returns an arbitrary color after scrambling. To solve corners correctly,
        we use virtual_face_colors() to temporarily set face colors based on
        FaceTracker analysis.

        See CageFaceColorMapper.py for detailed documentation.
        """
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
        # PHASE 1b + 2: CORNER AND CENTER SOLVING
        # =====================================================================
        # For ODD cubes (5x5, 7x7):
        #   - face.center.color is correct (fixed middle piece)
        #   - No virtual colors needed
        #
        # For EVEN cubes (4x4, 6x6):
        #   - face.center.color returns arbitrary color (WRONG!)
        #   - Use virtual_face_colors() to set correct face colors
        #   - FaceTracker determines which color each face SHOULD be
        #   - This allows Part.match_faces() to work correctly
        #
        # The context manager saves/restores _virtual_color on exit,
        # so there are no permanent side effects on Face objects.
        # =====================================================================
        is_even_cube = self._cube.n_slices % 2 == 0

        if is_even_cube:
            # -----------------------------------------------------------------
            # EVEN CUBE: Use virtual colors for correct face.color
            # -----------------------------------------------------------------
            # IMPORTANT: Cube rotations (X, Y, Z) move pieces between faces,
            # but Face objects are fixed. Virtual colors are set on Face objects,
            # so they don't move with the pieces!
            #
            # SOLUTION: Rotate cube FIRST to bring "white face" to U position,
            # THEN set virtual colors. This way the 3x3 solver doesn't need to
            # do cube rotations (white is already at U).
            #
            # Step 1: Create trackers (find which face should be which color)
            # Step 2: Find which face should be WHITE
            # Step 3: Rotate cube to bring that face to U
            # Step 4: Re-create trackers (markers moved during rotation!)
            # Step 5: Set virtual colors
            # Step 6: Solve corners and centers
            # -----------------------------------------------------------------
            self._prepare_even_cube_orientation()

            # After rotation, create fresh trackers (old markers moved)
            trackers = create_even_cube_face_trackers(self)

            with virtual_face_colors_with_op(self._cube, trackers, self._op):
                # Inside this block, face.color returns the "correct" color
                # Cube rotations (X, Y, Z) are tracked automatically
                # Virtual colors are updated after each rotation
                self._solve_corners_and_centers()
        else:
            # -----------------------------------------------------------------
            # ODD CUBE: No virtual colors needed
            # -----------------------------------------------------------------
            # face.center.color is correct because odd cubes have a fixed
            # middle piece that defines the face color.
            # -----------------------------------------------------------------
            self._solve_corners_and_centers()

        return sr

    def _prepare_even_cube_orientation(self) -> None:
        """Rotate cube to bring the "white face" to U position for even cubes.

        WHY THIS IS NEEDED:
        ==================
        Virtual colors are set on Face objects, but Face objects don't move
        during cube rotations (X, Y, Z). Only pieces move between faces.

        If we set virtual colors first and then call the 3x3 solver, it will
        rotate the cube to bring white to U. But after rotation, the virtual
        colors are on wrong faces!

        SOLUTION:
        ========
        1. Create temporary trackers to find which face should be WHITE
        2. Rotate cube to bring that face to U
        3. THEN set virtual colors (after rotation is done)
        4. Now the 3x3 solver won't need to rotate (white already at U)

        This method handles steps 1-2. The caller handles steps 3-4.
        """
        from cube.domain.model import Color
        from cube.domain.algs import Algs

        # Create temporary trackers to find face colors
        trackers = create_even_cube_face_trackers(self)

        # Find the tracker for WHITE
        white_tracker = None
        for tracker in trackers:
            if tracker.color == Color.WHITE:
                white_tracker = tracker
                break

        if white_tracker is None:
            # Fallback - shouldn't happen with valid BOY cube
            self.debug("Warning: No WHITE tracker found for even cube")
            return

        # Get the face that should be WHITE (where the marker currently is)
        white_face = white_tracker.face

        self.debug(f"Even cube: WHITE should be on {white_face.name}, bringing to U")

        # Rotate cube to bring this face to U position
        # The FaceTracker markers will move with the pieces
        self.cmn.bring_face_up(white_face)

        self.debug(f"Even cube: Rotation complete, WHITE face now at U")

    def _solve_corners_and_centers(self) -> None:
        """Solve corners (Phase 1b) and centers (Phase 2).

        This is extracted to a separate method so it can be called either:
        - Directly (odd cubes)
        - Inside virtual_face_colors context (even cubes)
        """
        # Phase 1b: Corner solving
        if not self._cube.solved:
            self._solve_corners()

        # Phase 2: Center solving
        if not self._are_centers_solved():
            self._solve_centers()

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
        Solve all centers using NxNCentersV3 with preserve_3x3_state=True.

        When preserve_3x3_state=True, NxNCentersV3 UNDOES all setup moves
        to preserve the cage (paired edges and solved corners).
        """
        self.debug("Starting center solving (using NxNCentersV3 with preserve_3x3_state=True)")

        # SS breakpoint BEFORE - inspect cage state
        self._op.enter_single_step_mode(SSCode.CAGE_CENTERS_START)

        # Log cage state before
        self.debug(f"Before center solving: edges={self._are_edges_solved()}, "
                   f"corners={self._are_corners_solved()}")

        # Use NxNCentersV3 with preserve_3x3_state=True to preserve paired edges
        cage_centers = NxNCentersV3(self, preserve_3x3_state=True)
        cage_centers.solve()

        # Log cage state after
        self.debug(f"After center solving: edges={self._are_edges_solved()}, "
                   f"corners={self._are_corners_solved()}, "
                   f"centers={self._are_centers_solved()}")

        # SS breakpoint AFTER - inspect result
        self._op.enter_single_step_mode(SSCode.CAGE_CENTERS_DONE)
        pass
