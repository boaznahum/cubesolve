"""NxN Solver Orchestrator - composes Reducer + 3x3 Solver."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.exceptions import (
    OpAborted,
    EvenCubeEdgeParityException,
    EvenCubeCornerSwapException,
    InternalSWError,
)
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.ReducerProtocol import ReducerProtocol
from cube.domain.solver.protocols.Solver3x3Protocol import Solver3x3Protocol
from cube.domain.solver.solver import Solver, SolveStep, SolverResults
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube


class NxNSolverOrchestrator(Solver):
    """
    Orchestrates NxN cube solving by composing:
    - A Reducer (NxN -> 3x3 reduction)
    - A 3x3 Solver (solves the reduced cube)

    Handles parity exceptions by:
    1. Catching EvenCubeEdgeParityException and calling reducer.fix_edge_parity()
    2. Catching EvenCubeCornerSwapException and retrying (swap done by solver)
    3. Retrying the solve after fixing parity

    This design allows:
    - Any reducer to work with any 3x3 solver
    - Parity handling in one place (not duplicated in each solver)
    - Easy testing of reducers and 3x3 solvers independently
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
        super().__init__()
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
    def _is_debug_enabled(self) -> bool:
        """Check if debug is currently enabled."""
        if self._debug_override is None:
            return self.is_debug_config_mode
        else:
            return self._debug_override

    def _debug(self, *args) -> None:
        """Print debug output if enabled."""
        if self._is_debug_enabled:
            prefix = f"Orchestrator[{self._solver_name.value}]:"
            print("Solver:", prefix, *(str(x) for x in args))
            self._op.log("Solver:", prefix, *args)

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
        Internal solve with parity retry loop.

        Args:
            debug: Enable debug output
            what: Which step to solve

        Returns:
            SolverResults with solve metadata
        """
        sr = SolverResults()

        if self._cube.solved:
            return sr

        even_edge_parity_detected = False
        corner_swap_detected = False
        partial_edge_detected = False

        # Handle reduction-only steps
        if what == SolveStep.NxNCenters:
            # Just solve centers
            self._reducer.solve_centers()
            return sr

        if what == SolveStep.NxNEdges:
            # Solve centers + edges (full reduction)
            results = self._reducer.reduce(debug)
            sr._was_partial_edge_parity = results.partial_edge_parity_detected
            return sr

        # Store debug state
        _d = self._debug_override
        try:
            self._debug_override = debug

            # Step 1: Reduce NxN to 3x3 (if needed)
            reduction_results = self._reducer.reduce(debug)
            if reduction_results.partial_edge_parity_detected:
                partial_edge_detected = True

            # Step 2: Pre-detect parity if solver can't handle it
            # Some solvers (like Kociemba) can't detect parity - they just fail.
            # For these, we detect and fix parity BEFORE calling solve_3x3.
            if self._cube.n_slices % 2 == 0:  # Only even cubes have parity
                parity_result = self._detect_and_fix_parity_if_needed(debug)
                if parity_result.edge_parity_fixed:
                    even_edge_parity_detected = True
                if parity_result.corner_parity_fixed:
                    corner_swap_detected = True

            # Step 3: Solve as 3x3 with retry loop for any remaining parity
            MAX_RETRIES = 3
            for attempt in range(1, MAX_RETRIES + 1):

                if self._cube.solved:
                    break

                self._debug(f"@@@@ Iteration # {attempt}")

                try:
                    self._solver_3x3.solve_3x3(debug, what)

                except EvenCubeEdgeParityException:
                    self._debug(f"Catch even edge parity in iteration #{attempt}")
                    if even_edge_parity_detected:
                        raise InternalSWError("already even_edge_parity_was_detected")
                    else:
                        even_edge_parity_detected = True
                        self._reducer.fix_edge_parity()
                        continue  # retry

                except EvenCubeCornerSwapException:
                    self._debug(f"Catch corner swap in iteration #{attempt}")
                    if corner_swap_detected:
                        raise InternalSWError("already even_corner_swap_was_detected")
                    else:
                        corner_swap_detected = True
                        continue  # retry (swap was already done by l3_corners)

                # Check if we should be solved after ALL step
                if what == SolveStep.ALL and not self.is_solved:
                    raise InternalSWError(
                        f"Not solved after iteration {attempt}, but no parity detected"
                    )

        finally:
            self._debug_override = _d

        # Record results
        if even_edge_parity_detected:
            sr._was_even_edge_parity = True

        if corner_swap_detected:
            sr._was_corner_swap = True

        if partial_edge_detected:
            sr._was_partial_edge_parity = True

        return sr

    def _detect_and_fix_parity_if_needed(self, debug: bool) -> "_ParityResult":
        """
        Detect and fix parity BEFORE calling solve_3x3.

        This is called for all solvers to ensure parity is handled uniformly.
        The solver's detect_edge_parity() is used if it returns True/False,
        otherwise a helper solver is used.

        Pre-fixing parity (instead of exception-retry) ensures solve_3x3()
        starts with a valid cube state, which is required for solvers like
        BeginnerSolver3x3 that can't resume from an arbitrary state.

        Returns:
            _ParityResult with flags indicating what was fixed
        """
        result = _ParityResult()

        # Try to detect edge parity using the solver's own method
        edge_parity: bool | None = self._solver_3x3.detect_edge_parity()

        if edge_parity is None:
            # Solver can't detect parity - use helper solver
            self._debug("Solver can't detect parity, using helper for detection")
            from cube.domain.solver.beginner.BeginnerSolver3x3 import BeginnerSolver3x3
            helper: BeginnerSolver3x3 = BeginnerSolver3x3(self._op)
            edge_parity = helper.detect_edge_parity()
        else:
            self._debug(f"Solver detected edge parity: {edge_parity}")

        # Fix edge parity if detected
        if edge_parity:
            self._debug("Edge parity detected, fixing BEFORE solve_3x3...")
            self._reducer.fix_edge_parity()
            # IMPORTANT: Re-reduce after parity fix - the fix may have affected edges
            self._debug("Re-reducing after edge parity fix...")
            self._reducer.reduce()
            result.edge_parity_fixed = True

        # Detect corner parity (only after edge parity is fixed)
        corner_parity: bool | None = self._solver_3x3.detect_corner_parity()

        if corner_parity is None:
            # Solver can't detect - use helper
            from cube.domain.solver.beginner.BeginnerSolver3x3 import BeginnerSolver3x3
            helper_corner: BeginnerSolver3x3 = BeginnerSolver3x3(self._op)
            corner_parity = helper_corner.detect_corner_parity()

        if corner_parity:
            self._debug("Corner parity detected, fixing BEFORE solve_3x3...")
            # Corner parity fix: Use helper to solve through L3Corners
            from cube.domain.solver.beginner.BeginnerSolver3x3 import BeginnerSolver3x3
            helper_fix: BeginnerSolver3x3 = BeginnerSolver3x3(self._op)
            self._fix_corner_parity_via_helper(helper_fix)
            result.corner_parity_fixed = True

        return result

    def _fix_corner_parity_via_helper(self, helper: "Solver3x3Protocol") -> None:
        """
        Fix corner parity by solving through L3Corners with the helper solver.

        L3Corners detects corner parity, does the swap fix, then raises
        EvenCubeCornerSwapException. We catch the exception and continue.
        """
        from cube.domain.solver.beginner.BeginnerSolver3x3 import BeginnerSolver3x3

        if not isinstance(helper, BeginnerSolver3x3):
            raise InternalSWError("Helper must be BeginnerSolver3x3 for corner parity fix")

        try:
            # Solve L1, L2, L3Cross, then L3Corners (which will fix and raise)
            helper.l1_cross.solve()
            helper.l1_corners.solve()
            helper.l2.solve()
            helper.l3_cross.solve()
            helper.l3_corners.solve()  # This will do the swap and raise
        except EvenCubeCornerSwapException:
            # Expected - the swap was done, cube is now in valid state
            pass


class _ParityResult:
    """Result of parity detection and fixing."""

    __slots__ = ["edge_parity_fixed", "corner_parity_fixed"]

    def __init__(self) -> None:
        self.edge_parity_fixed = False
        self.corner_parity_fixed = False
