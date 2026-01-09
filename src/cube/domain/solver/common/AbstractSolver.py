from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from cube.domain.algs.Alg import Alg
from cube.domain.algs.Algs import Algs
from cube.domain.exceptions import OpAborted
from cube.domain.model import Cube
from cube.domain.solver import Solver
from cube.domain.solver.common.CommonOp import CommonOp
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolverResults, SolveStep

if TYPE_CHECKING:
    pass


class AbstractSolver(Solver, ABC):
    """Abstract base class for all solvers."""
    __slots__: list[str] = ["_common", "_op", "_cube", "_debug_override"]

    def __init__(self, op: OperatorProtocol) -> None:
        super().__init__()
        # Set _op and _cube BEFORE CommonOp - CommonOp needs self.op
        self._op = op
        self._cube = op.cube
        self._debug_override: bool | None = None
        self.common: CommonOp = CommonOp(self)

    # =========================================================================
    # Template Method Pattern: solve() + _solve_impl()
    # =========================================================================

    @final
    def solve(
        self,
        debug: bool | None = None,
        animation: bool | None = True,
        what: SolveStep = SolveStep.ALL
    ) -> SolverResults:
        """Public entry point for solving - handles animation and OpAborted.

        DO NOT OVERRIDE. Implement _solve_impl() instead.

        This template method ensures:
        1. Animation flag is properly applied via with_animation()
        2. OpAborted is caught and handled cleanly (no red traceback)
        3. Debug flag is managed

        Args:
            debug: Override debug mode (None = use config)
            animation: Override animation (None = use config, True/False = force)
            what: Which step to solve (ALL, L1x, etc.)

        Returns:
            SolverResults with parity information
        """
        if debug is not None:
            self._debug_override = debug

        try:
            with self._op.with_animation(animation=animation):
                try:
                    return self._solve_impl(what)
                except OpAborted:
                    # User aborted - this is normal, not an error
                    return SolverResults()
        finally:
            self._debug_override = None

    @abstractmethod
    def _solve_impl(self, what: SolveStep) -> SolverResults:
        """Implement solver logic here. Called by solve().

        Animation and OpAborted are handled by the template method solve().
        Just implement the solving logic.

        Args:
            what: Which step to solve

        Returns:
            SolverResults with parity information
        """
        pass

    # =========================================================================

    @final
    @property
    def is_solved(self):
        return self._cube.solved

    @property
    def is_debug_config_mode(self) -> bool:
        return self._cube.config.solver_debug


    @property
    def _is_debug_enabled(self) -> bool:
        if self._debug_override is None:
            return self.is_debug_config_mode
        else:
            return self._debug_override

    @property
    def is_debug_enabled(self):
        return self.op.app_state.is_debug(self._is_debug_enabled)

    def debug(self, *args):
        logger = self.cube.sp.logger
        if logger.is_debug(self._is_debug_enabled):
            prefix = self.name + ":"
            print("Solver:", prefix, *(str(x) for x in args))
            self.op.log("Solver:", prefix, *args)

    @property
    @final
    def cube(self) -> Cube:
        return self._cube

    @property
    @final
    def op(self) -> OperatorProtocol:
        return self._op

    def solution(self) -> Alg:
        if self.is_solved:
            return Algs.alg(None)

        n = len(self.op.history())
        solution_algs: list[Alg] = []

        with self._op.with_animation(animation=False):

            with self._op.save_history():  # not really needed
                self.solve(debug=False, animation=False)
                while n < len(self.op.history()):
                    step = self.op.undo(animation=False)
                    # s=str(step)
                    if step:
                        solution_algs.insert(0, step)

            return Algs.alg(None, *solution_algs)

    @property
    @final
    def cmn(self) -> CommonOp:
        return self.common
