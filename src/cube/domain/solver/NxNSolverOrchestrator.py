"""
NxN Solver Orchestrator - composes Reducer + 3x3 Solver.

This is a refactoring of the original monolithic BeginnerSolver from:
    Branch: claude/learn-project-structure-01WYYtkueCTRzNjpBziMJtBB
    Commit: 378bc87
    File: cube/solver/begginer/beginner_solver.py

The parity handling logic is preserved from that original design.
See PARITY_HANDLING_BEFORE_ORCHESTRATOR.md for the original analysis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.exceptions import (
    EvenCubeCornerSwapException,
    EvenCubeEdgeParityException,
    InternalSWError,
    OpAborted,
)
from cube.domain.solver._3x3.beginner.BeginnerSolver3x3 import BeginnerSolver3x3
from cube.domain.solver.common.AbstractSolver import AbstractSolver
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.ReducerProtocol import ReducerProtocol
from cube.domain.solver.protocols.Solver3x3Protocol import Solver3x3Protocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.domain.solver.SolverName import SolverName
from cube.utils.SSCode import SSCode

if TYPE_CHECKING:
    pass


class NxNSolverOrchestrator(AbstractSolver):
    """
    Orchestrates NxN cube solving by composing:
    - A Reducer (NxN -> 3x3 reduction)
    - A 3x3 Solver (solves the reduced cube)

    DESIGN ORIGIN:
    This class is a refactoring of the original BeginnerSolver._solve() method.
    The original was a monolithic class handling both reduction and 3x3 solving.
    This version separates concerns while preserving the same parity handling logic.

    PARITY HANDLING (from original BeginnerSolver):
    1. Parity is detected DURING the solve (not before) via exceptions
    2. EvenCubeEdgeParityException: Raised by L3Cross when 1 or 3 edges flipped
    3. EvenCubeCornerSwapException: Raised by L3Corners when 2 corners in position
    4. Recovery uses a RETRY LOOP - fix parity, re-reduce, retry solve

    PARITY FIX PATTERN (unified for both parities):
    1. Detector (L3Cross/L3Corners) raises exception
    2. Orchestrator catches exception
    3. Reducer fixes parity (fix_edge_parity / fix_corner_parity)
    4. Re-reduce and retry solve

    Both algorithms work as long as cube is in 3x3 state (yellow up).
    Corner swap works after Y rotation because any diagonal swap fixes parity.

    See PARITY_HANDLING_ORCHESTRATOR.md for details.
    """

    __slots__ = ["_op", "_reducer", "_solver_3x3", "_solver_name", "_debug_override"]

    def __init__(
        self,
        op: OperatorProtocol,
        reducer: ReducerProtocol,
        solver_3x3: Solver3x3Protocol,
        solver_name: SolverName
    ) -> None:
        """
        Create an NxN solver orchestrator.

        Args:
            op: Operator for cube manipulation
            reducer: Reducer for NxN -> 3x3 reduction
            solver_3x3: Solver for 3x3 cube
            solver_name: Name identifier for this solver
        """
        super().__init__(op)
        self._op = op
        self._reducer = reducer
        self._solver_3x3 = solver_3x3
        self._solver_name = solver_name
        self._debug_override: bool | None = None

    @property
    def get_code(self) -> SolverName:
        """Return solver identifier."""
        return self._solver_name

    @property
    def status(self) -> str:
        """Human-readable solver status."""
        cube = self._cube

        # If not reduced yet, show reduction status
        if not cube.is3x3 and not self._reducer.is_reduced():
            return self._reducer.status + ", Not 3x3"

        # If solved, say so
        if cube.solved:
            return "Solved"

        # Otherwise, show 3x3 solver status
        return self._solver_3x3.status_3x3

    def solve(
        self,
        debug: bool | None = None,
        animation: bool | None = True,
        what: SolveStep = SolveStep.ALL
    ) -> SolverResults:
        """
        Solve the cube.

        Args:
            debug: Enable debug output (None = use config setting)
            animation: Enable animation (None = use current setting)
            what: Which step to solve

        Returns:
            SolverResults with solve metadata
        """
        if debug is None:
            debug = self.is_debug_config_mode

        with self._op.with_animation(animation=animation):
            try:
                return self._solve(debug, what)
            except OpAborted:
                return SolverResults()

    def _solve(self, debug: bool, what: SolveStep) -> SolverResults:
        """
        Internal solve with parity handling.

        This method is a direct refactoring of the original BeginnerSolver._solve()
        from cube/solver/begginer/beginner_solver.py (commit 378bc87).

        ORIGINAL DESIGN (preserved here):
        - Nested functions _reduce(), _l1(), _l2(), _l3() built solve steps
        - Retry loop (max 3) caught parity exceptions and retried
        - Parity flags tracked what was detected

        Args:
            debug: Enable debug output
            what: Which step to solve

        Returns:
            SolverResults with solve metadata
        """
        sr = SolverResults()

        if self._cube.solved:
            return sr

        # Parity tracking flags (same as original BeginnerSolver)
        # These track what parity was detected during the solve
        even_edge_parity_detected = False
        corner_swap_detected = False
        partial_edge_detected = False

        # Handle reduction-only steps (equivalent to original _centers() and _edges())
        if what == SolveStep.NxNCenters:
            self._reducer.solve_centers()
            return sr

        if what == SolveStep.NxNEdges:
            results = self._reducer.reduce(debug)
            sr._was_partial_edge_parity = results.partial_edge_parity_detected
            return sr

        # Store debug state (same pattern as original)
        _d = self._debug_override
        try:
            self._debug_override = debug

            # =================================================================
            # STEP 1: REDUCE NxN TO 3x3
            # =================================================================
            # Equivalent to original: _reduce() which called _centers() + _edges()
            #
            # ODD CUBE EDGE PARITY IS HANDLED HERE (not in the retry loop below):
            # - Odd cubes (5x5, 7x7) have a FIXED CENTER SLICE on each edge
            # - During edge pairing, if 1 edge remains unsolved after 11 are done,
            #   it means parity - but we can SEE which slices are wrong
            # - NxNEdges.solve() fixes it using one of two algorithms:
            #   * Simple (M-slice): Fast but disturbs edges -> re-pairs after
            #   * Advanced (R/L-slice): Preserves pairing -> no re-pair needed
            # - This is handled SILENTLY - no exception, no orchestrator involvement
            # - The return value signals if parity was fixed (for tracking only)
            #
            # EVEN CUBE FULL EDGE PARITY is NOT detected here:
            # - Even cubes (4x4, 6x6) have NO center slice reference
            # - All slices could be flipped the same way -> LOOKS paired
            # - Only detected later in L3Cross when 1 or 3 edges are flipped
            # - Handled by the retry loop below via EvenCubeEdgeParityException
            #
            reduction_results = self._reducer.reduce(debug)
            if reduction_results.partial_edge_parity_detected:
                partial_edge_detected = True

            # =================================================================
            # STEP 2: SOLVE AS 3x3 WITH PARITY HANDLING
            # =================================================================
            #
            # WHY PARITY ONLY AFFECTS EVEN CUBES (from original design):
            # - Odd cubes (3x3, 5x5, 7x7) have a fixed center on each face.
            #   The center slice provides a reference during edge pairing.
            #   When reduced, the virtual 3x3 is always solvable.
            #
            # - Even cubes (4x4, 6x6, 8x8) have no fixed centers.
            #   All edge slices are "wings" with no reference point.
            #   Reduction can create "parity" states that look valid but are
            #   impossible to solve as a normal 3x3:
            #   * Edge parity (OLL): ALL slices of an edge flipped together
            #     - Undetectable during pairing (no reference)
            #     - Detected in L3Cross: 1 or 3 edges flipped (impossible on 3x3)
            #   * Corner parity (PLL): Corner permutation has wrong parity
            #     - Detected in L3Corners: exactly 2 corners in position
            #
            is_even_cube = self._cube.n_slices % 2 == 0
            use_parity_detector = is_even_cube and not self._solver_3x3.can_detect_parity

            # For solvers that can't detect parity (Kociemba), use BeginnerSolver3x3
            # as a "parity detector" - it will throw exceptions that we catch
            if use_parity_detector:
                parity_detector: Solver3x3Protocol | None = BeginnerSolver3x3(self._op)
            else:
                parity_detector = None

            # =================================================================
            # RETRY LOOP (from original BeginnerSolver)
            # =================================================================
            # WHY 3 ITERATIONS?
            # - Iteration 1: Normal solve OR edge parity detected
            # - Iteration 2: After edge fix: normal solve OR corner parity detected
            # - Iteration 3: After corner fix: should complete
            #
            # Each parity type can only occur once. Detecting same parity twice = bug.
            MAX_RETRIES = 3
            for attempt in range(1, MAX_RETRIES + 1):

                if self._cube.solved:
                    break

                self.debug(f"@@@@ Iteration # {attempt}")

                try:
                    if parity_detector is not None:
                        # Use parity detector in QUERY MODE:
                        # - with_query_restore_state(): All moves are rolled back after
                        # - Parity detector raises exceptions, orchestrator catches and fixes
                        with self._op.with_query_restore_state():
                            parity_detector.solve_3x3(debug, what)
                        # No exception = no parity, state restored
                        # Now let actual solver solve
                        self._solver_3x3.solve_3x3(debug, what)
                    else:
                        # Solver can detect parity itself (BeginnerSolver3x3, CFOP)
                        self._solver_3x3.solve_3x3(debug, what)

                except EvenCubeEdgeParityException:
                    # =============================================================
                    # EDGE PARITY HANDLING
                    # =============================================================
                    # Detected by L3Cross: 1 or 3 edges flipped (impossible on 3x3)
                    # L3Cross throws, orchestrator catches and fixes via reducer.
                    # After fix, edges are disturbed -> need to re-reduce
                    self.debug(f"Catch even edge parity in iteration #{attempt}")
                    if even_edge_parity_detected:
                        raise InternalSWError("Edge parity detected twice - fix_edge_parity failed")
                    even_edge_parity_detected = True
                    self._op.enter_single_step_mode(SSCode.NxN_EDGE_PARITY_FIX)
                    self._reducer.fix_edge_parity()  # Flip all inner slices of any edge
                    self._reducer.reduce(debug)       # Re-reduce (fix disturbs pairing)
                    continue  # retry

                except EvenCubeCornerSwapException:
                    # =============================================================
                    # CORNER PARITY HANDLING
                    # =============================================================
                    # Detected by L3Corners: exactly 2 corners in position (impossible)
                    # L3Corners throws, orchestrator catches and fixes via reducer.
                    # Same pattern as edge parity for consistency.
                    #
                    # The corner swap algorithm swaps diagonal corners on U face.
                    # Any diagonal swap fixes parity - only requirement is yellow up.
                    self.debug(f"Catch corner swap in iteration #{attempt}")
                    if corner_swap_detected:
                        raise InternalSWError("Corner parity detected twice - fix_corner_parity failed")
                    corner_swap_detected = True
                    self._op.enter_single_step_mode(SSCode.NxN_CORNER_PARITY_FIX)
                    self._reducer.fix_corner_parity()  # Swap diagonal corners
                    self._reducer.reduce(debug)         # Re-reduce (fix disturbs edges)
                    continue  # retry

                # Verify solved after ALL step (same check as original)
                if what == SolveStep.ALL and not self.is_solved:
                    raise InternalSWError(
                        f"Not solved after iteration {attempt}, but no parity detected"
                    )

        finally:
            self._debug_override = _d

        # Record results (same as original BeginnerSolver)
        if even_edge_parity_detected:
            sr._was_even_edge_parity = True
        if corner_swap_detected:
            sr._was_corner_swap = True
        if partial_edge_detected:
            sr._was_partial_edge_parity = True

        # Report parity results
        if sr.has_parity:
            self.debug(sr.parity_summary())

        return sr

    def supported_steps(self) -> list[SolveStep]:
        """Return list of solve steps this solver supports.

        Combines NxN reduction steps with the 3x3 solver's steps.
        """
        # Start with NxN reduction steps
        steps: list[SolveStep] = [SolveStep.NxNCenters, SolveStep.NxNEdges]
        # Add 3x3 solver's steps
        steps.extend(self._solver_3x3.supported_steps())
        return steps
