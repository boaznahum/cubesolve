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

from collections.abc import Sequence
from typing import TYPE_CHECKING

from cube.domain.algs import Alg
from cube.domain.algs.SeqAlg import SeqAlg
from cube.domain.model import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.solver.SolverName import SolverName
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.solver import SolveStep, SolverResults
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.beginner.NxNEdges import NxNEdges
from cube.domain.solver.beginner.NxnCentersFaceTracker import NxNCentersFaceTrackers
from cube.domain.solver.direct.cage.CageCenters import CageCenters
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

    def _is_even_cube(self) -> bool:
        """Check if this is an even cube (4x4, 6x6, etc.)."""
        return self._cube.n_slices % 2 == 0

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

        # =====================================================================
        # PHASE 2: CENTER SOLVING
        # =====================================================================
        # Use NxNCenters to solve centers.
        # WARNING: NxNCenters may break edges/corners - testing with SS mode.
        # =====================================================================
        if not self._are_centers_solved():
            self._solve_centers()

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
        """Solve corners. ODD: direct 3x3. EVEN: shadow cube approach."""
        if self._is_even_cube():
            self._solve_corners_even()
        else:
            self._solve_corners_odd()

    def _solve_corners_odd(self) -> None:
        """Solve corners on ODD cubes using 3x3 solver directly."""
        self.debug("Starting corner solving (ODD cube - using 3x3 solver)")
        self._solver_3x3.solve_3x3()

    def _solve_corners_even(self) -> None:
        """Solve corners on EVEN cubes using shadow cube approach."""
        from cube.domain.exceptions import InternalSWError
        from cube.domain.exceptions import EvenCubeEdgeParityException

        self.debug("Starting corner solving (EVEN cube - using shadow cube)")

        # Step 1: Determine face colors and fix any flipped edges FIRST
        face_colors = self._get_even_cube_face_colors()
        self.debug(f"Initial face colors: {face_colors}")

        # Fix ALL flipped edges before building shadow cube
        for attempt in range(3):
            flipped = self._find_flipped_edges(face_colors)
            if not flipped:
                break
            self.debug(f"Pre-fix: Found {len(flipped)} flipped edges, fixing first one")
            self._nxn_edges._do_edge_parity_on_edge(flipped[0])
            # Recalculate face colors after each fix since cube orientation may change
            face_colors = self._get_even_cube_face_colors()
            self.debug(f"Recalculated face colors: {face_colors}")

        self.debug(f"Final face colors: {face_colors}")

        # Now build and solve shadow cube - should work without parity issues
        alg: Alg | None = None
        try:
            alg = self._solve_shadow_3x3(face_colors)
        except EvenCubeEdgeParityException as e:
            # This shouldn't happen if we fixed all flipped edges above
            self.debug(f"Unexpected parity after pre-fix: {e}")
            raise

        # Apply algorithm to original cube
        if alg:
            self.debug("Applying shadow algorithm to original cube")
            self._op.play(alg)

    def _fix_all_flipped_edges(self, face_colors: dict[FaceName, Color]) -> None:
        """Find and fix all edges that are flipped relative to face colors."""
        flipped = self._find_flipped_edges(face_colors)
        self.debug(f"Found {len(flipped)} flipped edges")
        for edge in flipped:
            self.debug(f"Fixing flipped edge: {edge._name}")
            self._nxn_edges._do_edge_parity_on_edge(edge)

    def _find_flipped_edges(self, face_colors: dict[FaceName, Color]) -> list:
        """Find edges that are flipped relative to expected face colors."""
        from cube.domain.model.Edge import Edge
        flipped: list[Edge] = []
        for edge in self._cube.edges:
            f1, f2 = edge.e1.face, edge.e2.face
            exp1 = face_colors.get(f1.name)
            exp2 = face_colors.get(f2.name)
            if edge.e1.color == exp2 and edge.e2.color == exp1:
                flipped.append(edge)
        return flipped

    def _get_even_cube_face_colors(self) -> dict[FaceName, Color]:
        """Determine face colors for even cube using FaceTrackers."""
        trackers = NxNCentersFaceTrackers(self)

        t1 = trackers.track_no_1()
        t2 = t1.track_opposite()
        t3 = trackers._track_no_3([t1, t2])
        t4 = t3.track_opposite()
        t5, t6 = trackers._track_two_last([t1, t2, t3, t4])

        face_colors: dict[FaceName, Color] = {}
        for tracker in [t1, t2, t3, t4, t5, t6]:
            face_colors[tracker.face.name] = tracker.color
        return face_colors

    def _solve_shadow_3x3(self, face_colors: dict[FaceName, Color]) -> Alg | None:
        """Create shadow 3x3, set state, solve, return algorithm."""
        from cube.domain.model.Cube import Cube
        from cube.application.commands.Operator import Operator
        from cube.application.state import ApplicationAndViewState
        from cube.domain.solver.Solvers3x3 import Solvers3x3

        shadow_cube = Cube(size=3, sp=self._cube.sp)
        shadow_cube.is_even_cube_shadow = True
        self._copy_state_to_shadow(shadow_cube, face_colors)

        assert shadow_cube.is_boy, f"Shadow cube must be valid boy pattern, face_colors={face_colors}"

        # Debug: print all edges on shadow cube
        self.debug(f"Shadow cube edges:")
        for edge in shadow_cube.edges:
            self.debug(f"  {edge._name}: {edge.e1.color}-{edge.e2.color}")

        if shadow_cube.solved:
            self.debug("Shadow cube is already solved")
            return None

        shadow_app_state = ApplicationAndViewState(self._cube.config)
        shadow_op = Operator(shadow_cube, shadow_app_state, None, False)

        solver_name = self._cube.config.cage_3x3_solver
        shadow_solver = Solvers3x3.by_name(solver_name, shadow_op, ignore_center_check=True)
        shadow_solver.solve_3x3()

        history: Sequence[Alg] = shadow_op.history()
        if not history:
            return None

        return SeqAlg(None, *history)

    def _copy_state_to_shadow(self, shadow: "Cube", face_colors: dict[FaceName, Color]) -> None:
        """Copy corner/edge state from even cube to shadow 3x3.

        IMPORTANT: This translates edge colors to match face_colors mapping.
        The 4x4's edge stickers have arbitrary colors from pairing.
        We translate them to represent edge positions relative to face_colors.
        """
        even_cube = self._cube

        # Build inverse mapping: color -> face
        color_to_face: dict[Color, FaceName] = {c: f for f, c in face_colors.items()}

        # Copy corner colors - iterate in parallel (same position order)
        for shadow_corner, even_corner in zip(shadow.corners, even_cube.corners):
            for shadow_pe, even_pe in zip(shadow_corner.slice.edges, even_corner.slice.edges):
                shadow_pe._color = even_pe.color

        # Copy edge colors with translation
        # For each edge, determine its "home" position based on face_colors
        edge_colors_seen: dict[frozenset, str] = {}
        for shadow_edge, even_edge in zip(shadow.edges, even_cube.edges):
            c1 = even_edge.e1.color
            c2 = even_edge.e2.color
            color_pair = frozenset([c1, c2])

            # Check for duplicates
            if color_pair in edge_colors_seen:
                self.debug(f"DUPLICATE edge colors: {c1}-{c2} at {even_edge._name}, "
                          f"first seen at {edge_colors_seen[color_pair]}")
            else:
                edge_colors_seen[color_pair] = even_edge._name

            shadow_edge.e1._color = c1
            shadow_edge.e2._color = c2

        # Set center colors
        for face_name, color in face_colors.items():
            shadow_face = shadow.face(face_name)
            shadow_face.center.get_slice((0, 0)).edges[0]._color = color

        # Verify edge colors form valid 3x3 combinations
        self._verify_shadow_edges(shadow, face_colors)

    def _verify_shadow_edges(self, shadow: "Cube", face_colors: dict[FaceName, Color]) -> None:
        """Verify that shadow cube edges form valid 3x3 color combinations."""
        # Build set of expected edge color pairs (from adjacent faces)
        adjacent_pairs = [
            (FaceName.F, FaceName.U), (FaceName.F, FaceName.D),
            (FaceName.F, FaceName.L), (FaceName.F, FaceName.R),
            (FaceName.B, FaceName.U), (FaceName.B, FaceName.D),
            (FaceName.B, FaceName.L), (FaceName.B, FaceName.R),
            (FaceName.U, FaceName.L), (FaceName.U, FaceName.R),
            (FaceName.D, FaceName.L), (FaceName.D, FaceName.R),
        ]
        expected_color_pairs: set[frozenset] = set()
        for f1, f2 in adjacent_pairs:
            c1, c2 = face_colors[f1], face_colors[f2]
            expected_color_pairs.add(frozenset([c1, c2]))

        # Check which edge color pairs we have
        actual_color_pairs: dict[frozenset, list] = {}
        for edge in shadow.edges:
            c1, c2 = edge.e1.color, edge.e2.color
            pair = frozenset([c1, c2])
            if pair not in actual_color_pairs:
                actual_color_pairs[pair] = []
            actual_color_pairs[pair].append(edge._name)

        # Find missing and duplicate pairs
        missing = expected_color_pairs - set(actual_color_pairs.keys())
        duplicates = {p: edges for p, edges in actual_color_pairs.items() if len(edges) > 1}
        invalid = set(actual_color_pairs.keys()) - expected_color_pairs

        if missing or duplicates or invalid:
            self.debug(f"Shadow edge validation:")
            if missing:
                self.debug(f"  Missing pairs: {[tuple(p) for p in missing]}")
            if duplicates:
                self.debug(f"  Duplicate pairs: {[(tuple(p), e) for p, e in duplicates.items()]}")
            if invalid:
                self.debug(f"  Invalid pairs (non-adjacent): {[tuple(p) for p in invalid]}")

    # =========================================================================
    # Phase 2: Center solving (TODO)
    # =========================================================================

    def _solve_centers(self) -> None:
        """
        Solve all centers using CageCenters.

        CageCenters is a modified NxNCenters that UNDOES setup moves
        to preserve the cage (paired edges and solved corners).
        """
        self.debug("Starting center solving (using CageCenters)")

        # SS breakpoint BEFORE - inspect cage state
        self._op.enter_single_step_mode(SSCode.CAGE_CENTERS_START)

        # Log cage state before
        self.debug(f"Before CageCenters: edges={self._are_edges_solved()}, "
                   f"corners={self._are_corners_solved()}")

        # Use CageCenters which preserves paired edges
        cage_centers = CageCenters(self)
        cage_centers.solve()

        # Log cage state after
        self.debug(f"After CageCenters: edges={self._are_edges_solved()}, "
                   f"corners={self._are_corners_solved()}, "
                   f"centers={self._are_centers_solved()}")

        # SS breakpoint AFTER - inspect result
        self._op.enter_single_step_mode(SSCode.CAGE_CENTERS_DONE)
        pass
