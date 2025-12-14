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
        Internal solve with parity handling.

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
            self._reducer.solve_centers()
            return sr

        if what == SolveStep.NxNEdges:
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

            # Step 2: Solve as 3x3 with parity handling
            #
            # WHY PARITY ONLY AFFECTS EVEN CUBES?
            # - Odd cubes (3x3, 5x5, 7x7) have a fixed center on each face.
            #   When reduced, the virtual 3x3 is always solvable.
            # - Even cubes (4x4, 6x6, 8x8) have no fixed centers.
            #   Reduction can create "parity" states that look valid but are
            #   impossible to solve as a normal 3x3:
            #   * Edge parity (OLL): Odd number of edges flipped
            #   * Corner parity (PLL): Corner permutation has wrong parity
            #
            # For solvers that can detect parity (LBL, CFOP): they throw exceptions.
            # For solvers that can't (Kociemba): use CFOP as helper to throw.
            #
            is_even_cube = self._cube.n_slices % 2 == 0
            use_cfop_for_parity = is_even_cube and not self._solver_3x3.can_detect_parity

            if use_cfop_for_parity:
                from cube.domain.solver.CFOP.CFOP3x3 import CFOP3x3
                parity_detector: CFOP3x3 | None = CFOP3x3(self._op)
            else:
                parity_detector = None

            MAX_RETRIES = 3
            for attempt in range(1, MAX_RETRIES + 1):

                if self._cube.solved:
                    break

                self._debug(f"@@@@ Iteration # {attempt}")

                try:
                    if parity_detector is not None:
                        # Use CFOP to detect parity (in query mode - state restored)
                        # please note it use smae slef._op
                        with self._op.with_query_restore_state():
                            parity_detector.solve_3x3(debug, what)
                        # No exception - no parity, state restored
                        # Now let actual solver solve
                        self._solver_3x3.solve_3x3(debug, what)
                    else:
                        # Solver can detect parity itself
                        self._solver_3x3.solve_3x3(debug, what)

                except EvenCubeEdgeParityException:
                    self._debug(f"Catch even edge parity in iteration #{attempt}")
                    if even_edge_parity_detected:
                        # Already fixed edge parity - this might be corner parity
                        # that Kociemba can't distinguish. Let CFOP handle it.
                        if parity_detector is not None:
                            self._debug("Falling back to CFOP for remaining parity")
                            parity_detector.solve_3x3(debug, what)
                            break
                        raise InternalSWError("already even_edge_parity_was_detected")
                    even_edge_parity_detected = True
                    self._reducer.fix_edge_parity()
                    self._reducer.reduce(debug)
                    continue  # retry

                except EvenCubeCornerSwapException:
                    self._debug(f"Catch corner swap in iteration #{attempt}")
                    if corner_swap_detected:
                        raise InternalSWError("already even_corner_swap_was_detected")
                    corner_swap_detected = True
                    self._reducer.reduce(debug)
                    continue  # retry

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
