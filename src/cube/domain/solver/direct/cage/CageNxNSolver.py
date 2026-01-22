"""Cage Method NxN Solver - edges first, then corners, then centers.

The Cage method solves big cubes by:
1. Building the "cage" (edges + corners)
2. Filling the cage (centers using commutators)

Uses FacesTrackerHolder for even cube matching - see:
    solver/common/big_cube/FACE_TRACKER.md

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

from typing import TYPE_CHECKING

from cube.domain.solver.SolverName import SolverName
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.tracker.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.solver.common.big_cube.NxNCenters import NxNCenters
from cube.domain.solver.common.big_cube.NxNCorners import NxNCorners
from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges
from cube.domain.solver.common.big_cube.ShadowCubeHelper import ShadowCubeHelper
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.utils.SSCode import SSCode

if TYPE_CHECKING:
    from cube.utils.logger_protocol import ILogger


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

    def __init__(self, op: OperatorProtocol, parent_logger: "ILogger") -> None:
        """
        Create a Cage method solver.

        Args:
            op: Operator for cube manipulation
            parent_logger: Parent logger (cube.sp.logger for root solver)
        """
        super().__init__(op, parent_logger, logger_prefix="Cage")

        # NxNCorners provides corner swap parity fix algorithm
        self._nxn_corners = NxNCorners(self)

        self._shadow_helper = ShadowCubeHelper(self)

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
        # TODO [#14]: Consider using advanced_edge_parity=True for cage method
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

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        """Solve using Cage method. Called by AbstractSolver.solve().

        Animation and OpAborted are handled by the template method.

        Order: Edges -> Corners -> Centers

        Args:
            what: Which step to solve:
                - SolveStep.ALL: Full solve (edges, corners, centers)
                - SolveStep.NxNEdges: Edges only (pair wings)
                - SolveStep.Cage: Edges + Corners (no centers)
                - SolveStep.NxNCenters: Centers only (assumes cage done)
        """
        sr = SolverResults()

        if self.is_solved:
            return sr

        match what:
            case SolveStep.NxNEdges:
                return self._solve_edges_only(sr)
            case SolveStep.Cage:
                return self._solve_cage_only(sr)
            case SolveStep.NxNCenters:
                return self._solve_centers_only(sr)
            case SolveStep.ALL | _:
                return self._solve_all(sr)

    def _solve_all(self, sr: SolverResults) -> SolverResults:
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
        with FacesTrackerHolder(self) as tracker_holder:
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

    def _solve_edges_only(self, sr: SolverResults) -> SolverResults:
        """Solve edges only (Phase 1a).

        Pairs all wing edges without solving corners or centers.
        """
        if self._are_edges_solved():
            return sr

        had_parity = self._solve_edges()
        if had_parity:
            sr._was_partial_edge_parity = True
        return sr

    def _solve_cage_only(self, sr: SolverResults) -> SolverResults:
        """Solve cage only (Phase 1a + 1b): edges + corners, no centers.

        This is the full _solve_impl without the center-solving step.
        Includes parity detection and retry logic for even cubes.
        """
        from cube.domain.exceptions import (
            EvenCubeCornerSwapException,
            EvenCubeEdgeParityException,
            EvenCubeEdgeSwapParityException,
        )

        # Check if cage is already done
        if (self._are_edges_solved() and self._are_edges_positioned()
                and self._are_corners_solved()):
            return sr

        with FacesTrackerHolder(self) as tracker_holder:
            self.debug(f"Created trackers: {list(tracker_holder)}")

            for attempt in range(5):
                self.debug(f"=== Cage solve attempt {attempt} ===")

                # PHASE 1a: EDGE SOLVING
                if not self._are_edges_solved():
                    had_parity = self._solve_edges()
                    if had_parity:
                        sr._was_partial_edge_parity = True

                # PHASE 1b: CORNER SOLVING
                try:
                    if not (self._are_edges_positioned() and self._are_corners_solved()):
                        self._solve_corners(tracker_holder)
                    break  # Success - exit retry loop

                except EvenCubeEdgeParityException as e:
                    self.debug(f"Caught EvenCubeEdgeParityException on attempt {attempt}: {type(e)}")
                    if attempt >= 4:
                        raise

                    self.debug("Edge parity detected during corner solve, fixing...")
                    self._nxn_edges.do_even_full_edge_parity_on_any_edge()

                except EvenCubeCornerSwapException:
                    if attempt >= 4:
                        raise

                    self.debug("Corner swap parity detected during corner solve, fixing...")
                    self._nxn_corners.fix_corner_parity()

                except EvenCubeEdgeSwapParityException:
                    if attempt >= 4:
                        raise

                    self.debug("Edge swap parity (PLL) detected during corner solve, fixing...")
                    self._nxn_edges.do_even_full_edge_parity_on_any_edge()

        return sr

    def _solve_centers_only(self, sr: SolverResults) -> SolverResults:
        """Solve centers only (Phase 2).

        Assumes cage (edges + corners) is already solved.
        """
        if self._are_centers_solved():
            return sr

        with FacesTrackerHolder(self) as tracker_holder:
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

    def _solve_corners(self, tracker_holder: FacesTrackerHolder) -> None:
        """Solve corners using shadow cube approach with DualOperator.

        Works identically for odd and even cubes:
        - Build shadow 3x3 with face colors from trackers
        - Solve shadow cube using DualOperator
        - DualOperator automatically plays moves on both shadow AND real cube
        - Annotations from 3x3 solver appear on real cube!

        For odd cubes: trackers return fixed center colors
        For even cubes: trackers return majority/tracked colors

        May raise EvenCubeEdgeParityException or EvenCubeCornerSwapException
        which _solve_impl catches to fix parity and retry.

        See docs/design/dual_operator_annotations.md for design details.
        """
        self.debug("Starting corner solving (using DualOperator)")

        # Get face colors from tracker holder
        face_colors = tracker_holder.get_face_colors()
        self.debug(f"Face colors: {face_colors}")

        # Debug: show current edge state
        self.debug("Current edges:")
        for edge in self._cube.edges:
            self.debug(f"  {edge._name}: {edge.e1.color}-{edge.e2.color}, is3x3={edge.is3x3}")

        # Solve using DualOperator - moves are applied to real cube automatically
        self._solve_with_dual_operator(tracker_holder)

    def _solve_with_dual_operator(self, th: FacesTrackerHolder) -> None:
        """Create shadow 3x3 and solve using DualOperator.

        DualOperator wraps both the shadow cube and real operator:
        - Solver logic operates on shadow cube (op.cube returns shadow)
        - Moves are played on BOTH cubes (shadow direct, real via operator)
        - Annotations are mapped from shadow pieces to real pieces
        - User sees full animation with h1/h2/h3 text and visual markers!

        This replaces the old approach of collecting history and playing at once.
        """
        from cube.application.commands.DualOperator import DualOperator
        from cube.domain.solver.Solvers3x3 import Solvers3x3

        # Create shadow 3x3 cube
        shadow_cube = self._shadow_helper.create_shadow_cube_from_faces_and_cube(th)

        # Debug: print all edges on shadow cube
        self.debug("Shadow cube edges:")
        for edge in shadow_cube.edges:
            self.debug(f"  {edge._name}: {edge.e1.color}-{edge.e2.color}")

        if shadow_cube.solved:
            self.debug("Shadow cube is already solved")
            return

        # Create DualOperator: wraps shadow cube + real operator
        # When solver calls op.play(), moves go to BOTH cubes
        # Annotations are mapped from shadow pieces → real pieces
        dual_op = DualOperator(shadow_cube, self._op)

        # For even cubes, use beginner solver to avoid CFOP parity detection issues.
        # CFOP raises exceptions for OLL/PLL parity which causes oscillation when fixing.
        # Beginner solver handles these states without raising exceptions.
        if self._cube.n_slices % 2 == 0:
            solver_name = "beginner"
            self.debug("Using beginner solver for even cube shadow")
        else:
            solver_name = self._cube.config.cage_3x3_solver

        # Create solver with DualOperator
        # Solver sees shadow cube via dual_op.cube
        # But moves and annotations go to real cube too!
        shadow_solver = Solvers3x3.by_name(solver_name, dual_op, self._logger)
        shadow_solver.solve_3x3()

        # No need to apply history - DualOperator already played on real cube!


    # =========================================================================
    # Phase 2: Center solving
    # =========================================================================

    def _solve_centers(self, tracker_holder: FacesTrackerHolder) -> None:
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

    def supported_steps(self) -> list[SolveStep]:
        """Return list of solve steps this solver supports.

        Cage method solves edges first, then corners (via shadow 3x3),
        then centers. Steps are:
        - NxNEdges: Pair all wing edges
        - Cage: Edges + Corners (no centers)
        - NxNCenters: Centers only
        """
        return [SolveStep.NxNEdges, SolveStep.Cage, SolveStep.NxNCenters]
