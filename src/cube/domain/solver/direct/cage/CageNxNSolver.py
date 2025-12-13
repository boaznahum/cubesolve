"""Cage Method NxN Solver - solves big cubes by building a cage first, then filling centers.

This solver uses the Cage method: solve edges and corners FIRST (the "cage"),
then solve centers LAST using commutators.

=============================================================================
CAGE METHOD FOR NxN CUBES
=============================================================================

CONCEPT:
--------
Instead of reducing the cube (solving centers first, then edges),
this method solves the OUTER pieces first, creating a "cage" around the centers.

The centers are then solved last using commutators, which avoids all parity issues.

COMPARISON WITH REDUCTION METHOD:
---------------------------------
  Reduction Method:              Cage Method:
  ----------------               -----------
  1. Solve ALL centers           1. Solve ALL edges (pair wings)
  2. Solve ALL edges             2. Solve ALL corners
  3. Solve as 3x3                3. Solve centers (commutators)

WHY "CAGE"?
-----------
After solving edges and corners, the centers appear "trapped" inside:

    ┌─────────────────┐
    │  E ─── E ─── E  │     E = solved edge/corner
    │  │           │  │
    │  E   [???]   E  │     ??? = unsolved centers (caged!)
    │  │           │  │
    │  E ─── E ─── E  │
    └─────────────────┘

ADVANTAGES:
-----------
1. PARITY-FREE - Centers can always be solved with commutators
2. Simple algorithms - Only need a few commutator patterns
3. Scales to any size - Works on 4x4 through 111x111
4. Predictable - Same approach works consistently

DISADVANTAGES:
--------------
1. Higher move count than reduction (~400-600 vs ~200-300)
2. Edge pairing without center reference can be tricky
3. Less optimized for speedsolving

SOLVING PHASES:
---------------

Phase 1: Build the Cage (Edges + Corners)

  Step 1a: Solve all edges
    - Pair wings together (like reduction, but ignore centers)
    - You have FREEDOM to use any slice moves
    - Place edges in correct positions

  Step 1b: Solve all corners
    - Use standard 3x3 corner methods
    - Corners are identical to 3x3 corners

Phase 2: Fill the Cage (Centers)

  Step 2: Solve centers with commutators
    - For each face, cycle centers into position
    - Use [A, B] = A B A' B' commutator patterns
    - No parity possible - any permutation is solvable

KEY ALGORITHMS:
---------------

Edge pairing (with slice freedom):
  - Standard edge pairing but can use any inner slices
  - No need to preserve centers

Corner solving:
  - Standard 3x3 algorithms (F2L, OLL, PLL for corners)

Center commutators:
  [Rw U Rw', D2] = Rw U Rw' D2 Rw U' Rw' D2
  - 3-cycles centers between faces
  - Doesn't affect edges or corners (already solved)

=============================================================================

References:
- https://www.speedsolving.com/wiki/index.php?title=Cage_Method
- https://www.speedsolving.com/threads/cage-method-for-the-5x5x5.51209/

=============================================================================
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.exceptions import (
    EvenCubeEdgeParityException,
    EvenCubeCornerSwapException,
    InternalSWError,
)
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import Solver, SolveStep, SolverResults
from cube.domain.solver.SolverName import SolverName
from cube.domain.solver.common.BaseSolver import BaseSolver

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube


from contextlib import contextmanager


class _CageSolverFacade(BaseSolver):
    """
    Minimal BaseSolver facade for NxNCenters and NxNEdges.

    Required because NxNCenters and NxNEdges expect a BaseSolver instance.

    Supports cage_mode flag which:
    - Skips center reduction (NxNCenters.solve returns early)
    - Ignores center-related assertions
    """

    __slots__: list[str] = ["_cage_mode"]

    def __init__(self, op: OperatorProtocol) -> None:
        super().__init__(op)
        self._cage_mode = False

    @property
    def cage_mode(self) -> bool:
        """True when building the cage (edges first, skip centers)."""
        return self._cage_mode

    @contextmanager
    def cage_mode_context(self):
        """Context manager to temporarily enable cage mode."""
        old_value = self._cage_mode
        self._cage_mode = True
        try:
            yield
        finally:
            self._cage_mode = old_value

    @property
    def get_code(self) -> SolverName:
        return SolverName.CAGE

    @property
    def status(self) -> str:
        return "Cage"

    def solve(
        self,
        debug: bool | None = None,
        animation: bool | None = True,
        what: SolveStep = SolveStep.ALL
    ) -> SolverResults:
        raise NotImplementedError("Use CageNxNSolver for full solve")


class CageNxNSolver(Solver):
    """
    Solves NxN cubes using the Cage method.

    The Cage method solves edges and corners first (creating a "cage"),
    then solves centers last using commutators. This approach is
    completely parity-free.

    For 3x3 cubes: Delegates to CFOP solver (no inner slices to handle).
    For NxN cubes (N > 3): Uses true Cage method.

    Phases:
        1a. Solve all edges (pair wings, place in position)
        1b. Solve all corners (standard 3x3 methods)
        2.  Solve centers (commutators)

    Attributes:
        _op: Operator for cube manipulation
        _solver_facade: BaseSolver facade for solver elements
        _nxn_edges: Edge solver element
        _nxn_centers: Center solver element
        _solver_3x3: 3x3 solver for skeleton
    """

    __slots__ = [
        "_op", "_solver_facade", "_nxn_edges", "_nxn_centers", "_cage_centers",
        "_l1_cross", "_l1_corners", "_l2", "_l3_cross", "_l3_corners"
    ]

    def __init__(self, op: OperatorProtocol) -> None:
        """
        Create a Cage Method NxN solver.

        Args:
            op: Operator for cube manipulation
        """
        super().__init__()
        self._op = op

        # Create solver facade for NxNCenters/NxNEdges
        self._solver_facade = _CageSolverFacade(op)

        # Import here to avoid circular imports
        from cube.domain.solver.beginner.NxNCenters import NxNCenters
        from cube.domain.solver.beginner.NxNEdges import NxNEdges
        from cube.domain.solver.beginner.L1Cross import L1Cross
        from cube.domain.solver.beginner.L1Corners import L1Corners
        from cube.domain.solver.beginner.L2 import L2
        from cube.domain.solver.beginner.L3Cross import L3Cross
        from cube.domain.solver.beginner.L3Corners import L3Corners
        from cube.domain.solver.direct.cage.CageCenters import CageCenters

        # For even cubes: use standard NxNCenters (reduction order)
        # For odd cubes: use CageCenters (preserves edges with whole-cube rotations)
        self._nxn_centers = NxNCenters(self._solver_facade)
        self._cage_centers = CageCenters(self._solver_facade)
        self._nxn_edges = NxNEdges(self._solver_facade, advanced_edge_parity=True)

        # 3x3 solver elements (used directly, not via delegation)
        self._l1_cross = L1Cross(self._solver_facade)
        self._l1_corners = L1Corners(self._solver_facade)
        self._l2 = L2(self._solver_facade)
        self._l3_cross = L3Cross(self._solver_facade)
        self._l3_corners = L3Corners(self._solver_facade)

    @property
    def get_code(self) -> SolverName:
        """Return solver identifier."""
        return SolverName.CAGE

    @property
    def op(self) -> OperatorProtocol:
        """The operator for cube manipulation."""
        return self._op

    @property
    def _cube(self) -> "Cube":
        """Internal access to the cube."""
        return self._op.cube

    @property
    def is_solved(self) -> bool:
        """Check if cube is solved."""
        return self._cube.solved

    @property
    def is_debug_config_mode(self) -> bool:
        """Whether debug mode is enabled in config."""
        return self._cube.config.solver_debug

    @property
    def status(self) -> str:
        """Human-readable solver status (stateless - inspects cube)."""
        if self.is_solved:
            return "Solved"

        # Stateless status based on cube inspection
        parts: list[str] = []

        if self._cube.is3x3:
            # For 3x3, report layer solving progress
            return self._get_3x3_status()

        # NxN status
        if self._are_edges_solved():
            parts.append("Edges:Done")
        else:
            parts.append("Edges:Pending")

        if self._are_corners_solved():
            parts.append("Corners:Done")
        else:
            parts.append("Corners:Pending")

        if self._are_centers_solved():
            parts.append("Centers:Done")
        else:
            parts.append("Centers:Pending")

        return ", ".join(parts)

    def _get_3x3_status(self) -> str:
        """Get 3x3 solving status (stateless).

        Note: On even cubes, L1/L3 checks rely on color_2_face which isn't set.
        """
        # Even cubes can't use standard L1/L3 status checks
        if self._cube.n_slices % 2 == 0:
            return "3x3 (even cube - status unavailable)"

        cross = self._l1_cross.is_cross()
        corners = self._l1_corners.is_corners()

        if cross and corners:
            s = "L1"
        elif cross:
            s = "L1-Cross"
        elif corners:
            s = "L1-Corners"
        else:
            s = "No-L1"

        if self._l2.solved():
            s += ", L2"
        else:
            s += ", No L2"

        if self._l3_cross.solved() and self._l3_corners.solved():
            s += ", L3"
        elif self._l3_cross.solved():
            s += ", L3-Cross"
        else:
            s += ", No L3"

        return s

    def solve(
        self,
        debug: bool | None = None,
        animation: bool | None = True,
        what: SolveStep = SolveStep.ALL
    ) -> SolverResults:
        """
        Solve the cube using Cage method.

        For 3x3 cubes: Standard layer-by-layer solving.
        For odd NxN cubes: True Cage method (edges+corners first, centers last).
        For even NxN cubes (4x4, 6x6): Reduction order (centers establish face colors).

        Note: Even cubes REQUIRE centers to be solved first because:
        - They have no center piece to define face color
        - The 3x3 solver elements need white_face/color_2_face
        - Face colors are only established after centers are solved

        Parity handling: Even cubes may have edge/corner parity which is
        detected during 3x3 solving and fixed with retry loop.

        Args:
            debug: Enable debug output
            animation: Enable animation
            what: Which step to solve

        Returns:
            SolverResults with solve metadata
        """
        sr = SolverResults()

        if self.is_solved:
            return sr

        cube = self._cube

        # For 3x3 cubes, do standard layer-by-layer solving
        if cube.is3x3:
            self._solve_3x3()
            return sr

        # Odd cubes (5x5, 7x7): TRUE Cage method
        #   - Edges first, then 3x3 skeleton, then centers
        #   - CageCenters uses commutators that preserve edge PAIRING
        #   - Commutators may move edges, so re-solve 3x3 after centers
        #   - PARITY FREE: No edge/corner parity on odd cubes
        #
        # Even cubes (4x4, 6x6): Reduction order
        #   - Centers first (to establish face colors)
        #   - Then edges + 3x3
        #   - Must handle parity

        is_even = cube.n_slices % 2 == 0

        if is_even:
            # Even cubes: reduction order (centers -> edges -> 3x3)
            self._solve_with_reduction_order(sr, is_even)
        else:
            # Odd cubes: TRUE Cage method (edges -> 3x3 -> centers -> re-3x3)
            self._solve_with_cage_order()

        return sr

    def _solve_with_cage_order(self) -> None:
        """Solve using TRUE Cage order (edges -> 3x3 -> centers -> re-3x3).

        For odd cubes only. Uses CageCenters which disables the _swap_slice
        optimization that would break edge pairing.

        The commutators preserve edge PAIRING (wings stay together) but may
        move edges to different positions. So we re-solve 3x3 after centers.

        Advantages:
        - Parity free: odd cubes have no edge/corner parity
        - Uses existing commutator logic (just disables _swap_slice)
        """
        # Phase 1: Solve ALL edges (pair wings)
        if not self._are_edges_solved():
            self._nxn_edges.solve()

        # Phase 2: Solve 3x3 skeleton (establishes correct edge positions)
        # Note: On odd cubes, center piece defines face color
        self._solve_3x3()

        # Phase 3: Fill the cage (solve centers)
        # CageCenters disables _swap_slice which would break edge pairing
        # Commutators preserve pairing but may move edges
        if not self._are_centers_solved():
            self._cage_centers.solve()

        # Phase 4: Re-solve 3x3 skeleton
        # Commutators moved edges, so re-solve to get correct positions
        self._solve_3x3()

    def _solve_with_reduction_order(self, sr: SolverResults, is_even: bool) -> None:
        """Solve using reduction order (centers -> edges -> 3x3).

        For all NxN cubes. Solves centers FIRST, then edges, then 3x3.
        Even cubes need parity handling; odd cubes have no parity issues.
        """
        # Phase 1: Solve centers (establishes face colors)
        if not self._are_centers_solved():
            self._nxn_centers.solve()

        if is_even:
            # Even cubes need parity handling
            self._solve_with_parity_handling(sr)
        else:
            # Odd cubes: no parity issues
            if not self._are_edges_solved():
                self._nxn_edges.solve()
            self._solve_3x3()

    def _solve_with_parity_handling(self, sr: SolverResults) -> None:
        """Solve with parity handling for even cubes (4x4, 6x6).

        Centers should already be solved before calling this method.
        Handles edge and corner parity with retry loop.
        """
        even_edge_parity_detected = False
        corner_swap_detected = False

        # Parity retry loop (max 3 attempts)
        MAX_RETRIES = 3
        for attempt in range(1, MAX_RETRIES + 1):
            if self.is_solved:
                break

            try:
                # Phase 2: Solve edges
                if not self._are_edges_solved():
                    self._nxn_edges.solve()

                # Phase 3: Solve 3x3 skeleton
                self._solve_3x3()

            except EvenCubeEdgeParityException:
                if even_edge_parity_detected:
                    raise InternalSWError("Edge parity already detected")
                even_edge_parity_detected = True
                # Fix edge parity using the proper method for OLL parity
                self._nxn_edges.do_even_full_edge_parity_on_any_edge()
                continue  # retry

            except EvenCubeCornerSwapException:
                if corner_swap_detected:
                    raise InternalSWError("Corner swap already detected")
                corner_swap_detected = True
                continue  # retry (swap was done by l3_corners)

        # Record results
        if even_edge_parity_detected:
            sr._was_even_edge_parity = True
        if corner_swap_detected:
            sr._was_corner_swap = True

    def _solve_3x3(self) -> None:
        """Solve the 3x3 skeleton (cross, corners, edges)."""
        self._l1_cross.solve()
        self._l1_corners.solve()
        self._l2.solve()
        self._l3_cross.solve()
        self._l3_corners.solve()

    # =========================================================================
    # STATE INSPECTION (STATELESS)
    # =========================================================================

    def _are_edges_solved(self) -> bool:
        """Check if all edges are paired and positioned (stateless - inspects cube)."""
        return all(e.is3x3 for e in self._cube.edges)

    def _are_corners_solved(self) -> bool:
        """Check if all corners are positioned and oriented (stateless - inspects cube).

        Note: On even cubes (4x4, 6x6), we can't use L1/L3 corner checks
        because face colors aren't determined until centers are solved.
        For the Cage method, we solve corners BEFORE centers, so we need
        an alternative check.
        """
        # For even cubes, we can't use the standard L1/L3 checks
        # because they rely on color_2_face which isn't set yet
        if self._cube.n_slices % 2 == 0:
            # On even cubes, check if all corners match adjacent edges
            # This is a simplified check - proper implementation would
            # use face tracking
            return self._cube.solved  # Fallback: only true when fully solved
        # For odd cubes, use standard checks
        return self._l1_corners.is_corners() and self._l3_corners.solved()

    def _are_centers_solved(self) -> bool:
        """Check if all centers are solved (stateless - inspects cube)."""
        return all(f.center.is3x3 for f in self._cube.faces)

    def _is_3x3_skeleton_solved(self) -> bool:
        """Check if the 3x3 skeleton (cross, corners, edges) is solved (stateless).

        Note: On even cubes, L1/L3 checks rely on color_2_face which isn't set.
        """
        # For even cubes, can't use standard checks before centers solved
        if self._cube.n_slices % 2 == 0:
            return self._cube.solved  # Fallback
        return (
            self._l1_cross.is_cross()
            and self._l1_corners.is_corners()
            and self._l2.solved()
            and self._l3_cross.solved()
            and self._l3_corners.solved()
        )

    def _is_cage_complete(self) -> bool:
        """Check if the cage (edges + corners) is complete (stateless)."""
        return self._are_edges_solved() and self._is_3x3_skeleton_solved()
