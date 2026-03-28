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

import logging
from typing import TYPE_CHECKING

from cube.domain.exceptions import (
    EvenCubeCornerSwapException,
    EvenCubeEdgeParityException,
    InternalSWError, EvenCubeEdgeSwapParityException,
)
from cube.domain.solver._3x3.beginner.BeginnerSolver3x3 import BeginnerSolver3x3
from cube.domain.solver.common.AbstractSolver import AbstractSolver
from cube.domain.solver.common.SolverStatistics import SolverStatistics
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.ReducerProtocol import ReducerProtocol
from cube.domain.solver.protocols.Solver3x3Protocol import Solver3x3Protocol
from cube.domain.solver.solver import ParityFix, Solver, SolverResults, SolveStep
from cube.domain.solver.SolverName import SolverName
from cube.utils.SSCode import SSCode

if TYPE_CHECKING:
    from cube.utils.logging import CubeLogger


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

    __slots__ = ["_op", "_reducer", "_solver_3x3", "_solver_name", "_debug_override",
                 "_advanced_edge_parity", "_advanced_corner_parity"]

    def __init__(
        self,
        op: OperatorProtocol,
        parent_logger: "CubeLogger",
        reducer: ReducerProtocol,
        solver_3x3: Solver3x3Protocol,
        solver_name: SolverName,
        advanced_edge_parity: bool = False,
        advanced_corner_parity: bool = False,
    ) -> None:
        """
        Create an NxN solver orchestrator.

        Args:
            op: Operator for cube manipulation
            parent_logger: Parent logger (cube.sp.logger for root solver)
            reducer: Reducer for NxN -> 3x3 reduction
            solver_3x3: Solver for 3x3 cube
            solver_name: Name identifier for this solver
            advanced_edge_parity: If True, use R/L-slice algorithm that preserves
                                    edge pairing (no re-reduce needed after fix).
                                    If False, use M-slice algorithm that disrupts
                                    edge pairing (re-reduce needed after fix).
            advanced_corner_parity: If True, request corner parity fix that
                                    preserves edge positions.
        """
        super().__init__(op, parent_logger, logger_prefix=f"Solver:{solver_name.display_name}")
        self._op = op
        self._reducer = reducer
        self._solver_3x3 = solver_3x3
        self._solver_name = solver_name
        self._debug_override: bool | None = None
        self._advanced_edge_parity = advanced_edge_parity
        self._advanced_corner_parity = advanced_corner_parity

    @property
    def get_code(self) -> SolverName:
        """Return solver identifier."""
        return self._solver_name

    def _create_2x2_delegate(self) -> Solver:
        """Fast solvers (CFOP, Kociemba) use IDA* for 2x2; others use beginner."""
        from cube.domain.solver.Solvers import Solvers
        if self._solver_name in (SolverName.CFOP, SolverName.KOCIEMBA):
            return Solvers.two_by_two_ida(self._op)
        return Solvers.two_by_two_beginner(self._op)

    @property
    def _status_impl(self) -> str:
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

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        """Solve the cube. Called by AbstractSolver.solve().

        Animation and OpAborted are handled by the template method.

        Args:
            what: Which step to solve

        Returns:
            SolverResults with solve metadata
        """
        return self._solve(what)

    def _solve(self, what: SolveStep) -> SolverResults:
        """
        Internal solve with parity handling.

        This method is a direct refactoring of the original BeginnerSolver._solve()
        from cube/solver/begginer/beginner_solver.py (commit 378bc87).

        ORIGINAL DESIGN (preserved here):
        - Nested functions _reduce(), _l1(), _l2(), _l3() built solve steps
        - Retry loop (max 3) caught parity exceptions and retried
        - Parity flags tracked what was detected

        Args:
            what: Which step to solve

        Returns:
            SolverResults with solve metadata
        """
        sr = SolverResults()

        if self._cube.solved:
            return sr

        # Handle reduction-only steps (equivalent to original _centers() and _edges())
        if what == SolveStep.NxNCenters:
            self._reducer.solve_centers()
            return sr

        if what == SolveStep.NxNEdges:
            results = self._reducer.reduce(self._is_debug_enabled)
            sr.was_partial_edge_parity = results.partial_edge_parity_fix
            return sr

        # Debug state is now handled by AbstractSolver.solve() template method
        debug = self._is_debug_enabled

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
        partial_edge_fix: ParityFix | None = reduction_results.partial_edge_parity_fix

        # =================================================================
        # STEP 2: SOLVE AS 3x3 WITH PARITY HANDLING
        # =================================================================
        # On a reduced cube, even cubes have known face colors as long as no
        # inner slice operation is done without undo before/after querying state.
        # TODO: replace with cube.with_3x3_mode() to prevent inner slice operations
        self._solve_3x3_with_parity(sr, debug, what)

        if partial_edge_fix is not None:
            sr.was_partial_edge_parity = partial_edge_fix

        return sr

    def _solve_3x3_with_parity(
        self,
        sr: SolverResults,
        debug: bool,
        what: SolveStep,
    ) -> None:
        """Solve the reduced cube as a 3x3 with parity detection and retry.

        Called inside with_faces_color_provider context so that
        colors_id/position_id are reliable on even cubes.

        WHY PARITY ONLY AFFECTS EVEN CUBES:
        - Odd cubes have fixed centers → parity resolved during reduction.
        - Even cubes have no fixed centers → parity states look valid but
          are impossible on a 3x3. Detected during L3 solving.

        Retry loop: max 3 iterations.
        - Iteration 1: Normal solve OR edge parity detected
        - Iteration 2: After edge fix → normal solve OR corner parity
        - Iteration 3: After corner fix → should complete
        """
        even_edge_parity_fix: ParityFix | None = None
        even_edge_swap_parity_fix: ParityFix | None = None  # CFOP
        corner_swap_fix: ParityFix | None = None

        is_even_cube = self._cube.n_slices % 2 == 0
        _3x3_can_detect_parity = self._solver_3x3.can_detect_parity
        use_parity_detector = is_even_cube and not _3x3_can_detect_parity

        # For solvers that can't detect parity (Kociemba), use BeginnerSolver3x3
        # as a "parity detector" - it will throw exceptions that we catch
        if use_parity_detector:
            parity_detector: Solver3x3Protocol | None = BeginnerSolver3x3(
                self._op, parent_logger=self._logger
            )
        else:
            parity_detector = None

        max_retries = 3
        for attempt in range(1, max_retries + 1):

            if self._cube.solved:
                break

            self._logger.log_lazy(logging.DEBUG, lambda: f"@@@@ Iteration # {attempt}")

            try:
                if parity_detector is not None:
                    with self._op.with_query_restore_state():
                        parity_detector.solve_3x3(debug, what)
                    self._solver_3x3.solve_3x3(debug, what)
                else:
                    self._solver_3x3.solve_3x3(debug, what)

            except EvenCubeEdgeParityException:
                # =============================================================
                # EDGE PARITY HANDLING
                # =============================================================
                # Detected by L3Cross: 1 or 3 edges flipped (impossible on 3x3)
                # L3Cross throws, orchestrator catches and fixes via reducer.
                # After fix, edges are disturbed -> need to re-reduce
                self._logger.log_lazy(logging.DEBUG, lambda: f"Catch even edge parity in iteration #{attempt}")
                if even_edge_parity_fix is not None:
                    raise InternalSWError("Edge parity detected twice - fix_edge_parity failed")
                self._op.enter_single_step_mode(SSCode.NxN_EDGE_PARITY_FIX)
                even_edge_fix = self._reducer.fix_edge_parity(
                    advanced=self._advanced_edge_parity
                )
                even_edge_parity_fix = even_edge_fix

                # not need in case of advanced
                self._reducer.reduce(debug)
                continue

            except EvenCubeEdgeSwapParityException:
                self._logger.debug_lazy(lambda: f"Catch even edge swap (CFOP) parity in iteration #{attempt}")
                if even_edge_swap_parity_fix is not None:
                    raise InternalSWError("Even Edge swap (CFOP) parity detected twice - fix_edge_parity failed")
                even_edge_swap_fix = self._reducer.fix_edge_parity(
                    advanced=self._advanced_edge_parity
                )
                even_edge_swap_parity_fix = even_edge_swap_fix

                # not need in case of advanced
                self._reducer.reduce(debug)
                continue

            # CFOP handle EvenEdge parity, but it might decide to throw
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
                self._logger.log_lazy(logging.DEBUG, lambda: f"Catch corner swap in iteration #{attempt}")
                if corner_swap_fix is not None:
                    raise InternalSWError("Corner parity detected twice - fix_corner_parity failed")
                self._op.enter_single_step_mode(SSCode.NxN_CORNER_PARITY_FIX)
                # If parity was detected by the parity_detector (not the 3x3 solver
                # itself), the cube is not L1/L2 solved — any two-corner swap suffices
                # and the non-advanced fixer handles it. Only use advanced when the
                # 3x3 solver detected parity itself (cube is L1+L2+L3cross solved).
                corner_fix = self._reducer.fix_corner_parity(
                    advanced=self._advanced_corner_parity and _3x3_can_detect_parity
                )
                corner_swap_fix = ParityFix.of(not corner_fix.need_resolve_3x3)
                if corner_fix.cube_unreduced:
                    self._reducer.reduce(debug)
                continue

            if what == SolveStep.ALL and not self.is_solved:
                raise InternalSWError(
                    f"Not solved after iteration {attempt}, but no parity detected"
                )

        # Record parity results
        if even_edge_parity_fix is not None:
            sr.was_even_edge_parity = even_edge_parity_fix
        if corner_swap_fix is not None:
            sr.was_corner_swap = corner_swap_fix

    # =========================================================================
    # Statistics (override AbstractSolver)
    # =========================================================================

    def reset_block_statistics(self) -> None:
        """Reset statistics in both reducer and 3x3 solver."""
        self._reducer.reset_block_statistics()

    def get_block_statistics(self) -> SolverStatistics:
        """Aggregate block statistics from reducer."""
        return self._reducer.get_block_statistics()

    def _supported_steps_impl(self) -> list[SolveStep]:
        """Return list of solve steps this solver supports.

        Combines NxN reduction steps with the 3x3 solver's steps.
        """
        # Start with NxN reduction steps
        steps: list[SolveStep] = [SolveStep.NxNCenters, SolveStep.NxNEdges]
        # Add 3x3 solver's steps
        steps.extend(self._solver_3x3.supported_steps())
        return steps
