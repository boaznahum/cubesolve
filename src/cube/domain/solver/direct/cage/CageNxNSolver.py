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
   - "Full" edge parity may appear as OLL/PLL parity on shadow cube
   - Solution: Use beginner solver for even cube shadows (not CFOP)
   - Beginner solver doesn't detect/raise parity exceptions
   - CFOP would cause oscillation: fix parity -> re-pair -> new parity
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from cube.domain.algs import Alg
from cube.domain.algs.SeqAlg import SeqAlg
from cube.domain.model import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.solver.common.big_cube.FaceTrackerHolder import FaceTrackerHolder
from cube.domain.solver.common.big_cube.NxNCenters import NxNCenters
from cube.domain.solver.common.big_cube.NxNCorners import NxNCorners
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.domain.solver.SolverName import SolverName
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

    __slots__ = ["_nxn_edges", "_nxn_corners"]

    def __init__(self, op: OperatorProtocol) -> None:
        """
        Create a Cage method solver.

        Args:
            op: Operator for cube manipulation
        """
        super().__init__(op)

        # NxNCorners provides corner swap parity fix algorithm
        self._nxn_corners = NxNCorners(self)

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

        For even cubes, parity may be detected during corner solving:
        - EvenCubeEdgeParityException: 1 or 3 edges flipped (edge parity)
        - EvenCubeCornerSwapException: 2 corners in position (corner parity)

        When either happens, we fix parity and RE-PAIR edges before retrying.

        Face trackers are created once at start and cleaned up in finally block.
        Trackers work identically for odd/even - only creation method differs.
        """
        from cube.domain.exceptions import (
            EvenCubeCornerSwapException,
            EvenCubeEdgeParityException,
            EvenCubeEdgeSwapParityException,
        )

        # Create face tracker holder - works for both odd and even cubes
        # For odd: simple trackers using fixed center color (no cleanup needed)
        # For even: trackers mark center slices (cleanup on exit)
        # Use context manager for automatic cleanup on exit
        with FaceTrackerHolder(self) as tracker_holder:
            self.debug(f"Created trackers: {list(tracker_holder)}")

            # Main solve loop with parity retry
            # Even cubes may need multiple retries due to OLL and PLL parity interaction
            for attempt in range(5):
                self.debug(f"=== Solve attempt {attempt} ===")

                # PHASE 1a: EDGE SOLVING (pair all edges)
                if not self._are_edges_solved():
                    had_parity = self._solve_edges()
                    if had_parity:
                        sr._was_partial_edge_parity = True

                # PHASE 1b: CORNER SOLVING
                try:
                    if not self._cube.solved:
                        self._solve_corners(tracker_holder)
                    break  # Success - exit retry loop

                except EvenCubeEdgeParityException as e:
                    self.debug(f"Caught EvenCubeEdgeParityException on attempt {attempt}: {type(e)}")
                    if attempt >= 4:
                        raise  # Give up after 5 attempts

                    self.debug("Edge parity detected during corner solve, fixing...")

                    # Fix parity by always applying to FR edge for consistency
                    # This avoids oscillation between different parity states
                    self._nxn_edges.do_even_full_edge_parity_on_any_edge()

                    # Parity fix broke edge pairing - loop will re-pair them

                except EvenCubeCornerSwapException:
                    if attempt >= 4:
                        raise  # Give up after 5 attempts

                    self.debug("Corner swap parity detected during corner solve, fixing...")

                    # Fix corner parity using NxNCorners
                    self._nxn_corners.fix_corner_parity()

                    # Corner swap uses inner slice moves - breaks edge pairing
                    # Loop will re-pair them

                except EvenCubeEdgeSwapParityException:
                    if attempt >= 4:
                        raise  # Give up after 5 attempts

                    self.debug("Edge swap parity (PLL) detected during corner solve, fixing...")

                    # For PLL edge swap parity, use the same edge flip fix as OLL parity.
                    # Both types of parity are caused by the same underlying issue:
                    # edge slices were paired in a way that creates an impossible 3x3 state.
                    # Flipping an edge slice changes both orientation and permutation parity.
                    self._nxn_edges.do_even_full_edge_parity_on_any_edge()

                    # Parity fix uses M-slice moves - breaks edge pairing
                    # Loop will re-pair them

            # PHASE 2: CENTER SOLVING
            if not self._are_centers_solved():
                self._solve_centers(tracker_holder)

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

    def _solve_corners(self, tracker_holder: FaceTrackerHolder) -> None:
        """Solve corners using shadow cube approach.

        Works identically for odd and even cubes:
        - Build shadow 3x3 with face colors from trackers
        - Solve shadow cube
        - Apply algorithm to original cube

        For odd cubes: trackers return fixed center colors
        For even cubes: trackers return majority/tracked colors

        May raise EvenCubeEdgeParityException or EvenCubeCornerSwapException
        which _solve_impl catches to fix parity and retry.
        """
        self.debug("Starting corner solving (using shadow cube)")

        # Get face colors from tracker holder
        face_colors = tracker_holder.get_face_colors()
        self.debug(f"Face colors: {face_colors}")

        # Debug: show current edge state
        self.debug("Current edges:")
        for edge in self._cube.edges:
            self.debug(f"  {edge._name}: {edge.e1.color}-{edge.e2.color}, is3x3={edge.is3x3}")

        # Build and solve shadow cube - may raise parity exceptions
        alg = self._solve_shadow_3x3(face_colors)

        # Apply algorithm to original cube
        if alg:
            self.debug("Applying shadow algorithm to original cube")
            self._op.play(alg)

    def _solve_shadow_3x3(self, face_colors: dict[FaceName, Color]) -> Alg | None:
        """Create shadow 3x3, set state, solve, return algorithm."""
        from cube.application.commands.Operator import Operator
        from cube.application.state import ApplicationAndViewState
        from cube.domain.model.Cube import Cube
        from cube.domain.solver.Solvers3x3 import Solvers3x3

        shadow_cube = Cube(size=3, sp=self._cube.sp)
        shadow_cube.is_even_cube_shadow = True
        self._copy_state_to_shadow(shadow_cube, face_colors)

        assert shadow_cube.is_boy, f"Shadow cube must be valid boy pattern, face_colors={face_colors}"

        # Debug: print all edges on shadow cube
        self.debug("Shadow cube edges:")
        for edge in shadow_cube.edges:
            self.debug(f"  {edge._name}: {edge.e1.color}-{edge.e2.color}")

        if shadow_cube.solved:
            self.debug("Shadow cube is already solved")
            return None

        shadow_app_state = ApplicationAndViewState(self._cube.config)
        shadow_op = Operator(shadow_cube, shadow_app_state, None, False)

        # For even cubes, use beginner solver to avoid CFOP parity detection issues.
        # CFOP raises exceptions for OLL/PLL parity which causes oscillation when fixing.
        # Beginner solver handles these states without raising exceptions.
        if self._cube.n_slices % 2 == 0:
            solver_name = "beginner"
            self.debug("Using beginner solver for even cube shadow")
        else:
            solver_name = self._cube.config.cage_3x3_solver

        shadow_solver = Solvers3x3.by_name(solver_name, shadow_op)
        shadow_solver.solve_3x3()

        history: Sequence[Alg] = shadow_op.history()
        if not history:
            return None

        return SeqAlg(None, *history)

    def _copy_state_to_shadow(self, shadow: Cube, face_colors: dict[FaceName, Color]) -> None:
        """Copy corner/edge state from even cube to shadow 3x3.

        Uses the type-safe Cube3x3Colors mechanism to transfer state.
        The even cube's edge/corner colors are extracted, centers are replaced
        with face_colors, and the result is applied to the shadow cube.
        """
        # Get colors from even cube as 3x3 snapshot
        colors_3x3 = self._cube.get_3x3_colors()

        # Override centers with face_colors mapping
        modified = colors_3x3.with_centers(face_colors)

        # Verify the modified colors represent a valid BOY layout
        assert modified.is_boy(self._cube.sp), \
            "Shadow cube colors must maintain BOY layout"

        # Apply to shadow cube (includes sanity check)
        shadow.set_3x3_colors(modified)

    # =========================================================================
    # Phase 2: Center solving (TODO)
    # =========================================================================

    def _solve_centers(self, tracker_holder: FaceTrackerHolder) -> None:
        """
        Solve all centers using NxNCenters with preserve_cage=True.

        NxNCenters with preserve_cage=True UNDOES setup moves
        to preserve the cage (paired edges and solved corners).

        Args:
            tracker_holder: Holder containing trackers for face colors.
        """
        self.debug("Starting center solving (using NxNCenters with preserve_cage=True)")

        # SS breakpoint BEFORE - inspect cage state
        self._op.enter_single_step_mode(SSCode.CAGE_CENTERS_START)

        # Log cage state before
        self.debug(f"Before centers: edges={self._are_edges_solved()}, "
                   f"corners={self._are_corners_solved()}")

        # Use NxNCenters with preserve_cage=True to preserve paired edges
        # Pass trackers from holder so solver knows which color belongs on each face
        cage_centers = NxNCenters(self, preserve_cage=True)
        cage_centers.solve(tracker_holder)

        # Log cage state after
        self.debug(f"After centers: edges={self._are_edges_solved()}, "
                   f"corners={self._are_corners_solved()}, "
                   f"centers={self._are_centers_solved()}")

        # SS breakpoint AFTER - inspect result
        self._op.enter_single_step_mode(SSCode.CAGE_CENTERS_DONE)
