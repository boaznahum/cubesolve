import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from cube.domain.algs.Alg import Alg
from cube.domain.algs.Algs import Algs
from cube.domain.algs.SeqAlg import SeqAlg
from cube.domain.exceptions import OpAborted
from cube.domain.model import Cube
from cube.domain.solver import Solver
from cube.domain.solver.common.SolverStatistics import (
    MoveCountTopic,
    ParityTopic,
    SolverStatistics,
    TopicKey,
)
from cube.domain.solver.common.CommonOp import CommonOp
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.utils.logging import CubeLogger

if TYPE_CHECKING:
    pass

MOVE_COUNT_KEY = TopicKey("MoveCount", MoveCountTopic)
PARITY_KEY = TopicKey("Parity", ParityTopic)


class AbstractSolver(Solver, ABC):
    """Abstract base class for all solvers.

    Logger Architecture:
        Every solver gets a ``CubeLogger`` child of the root ``cube`` logger.
        Debug is controlled by the logger's level:
        - ``solve(debug=True)`` → temporarily sets logger to DEBUG
        - ``solve(debug=False)`` → temporarily sets logger to INFO
        - ``solve(debug=None)`` → inherits from root (config.solver_debug)
    """
    __slots__: list[str] = ["_common", "_op", "_cube", "_debug_override", "__logger"]

    def __init__(
        self,
        op: OperatorProtocol,
        parent_logger: CubeLogger,
        logger_prefix: str | None = None,
    ) -> None:
        super().__init__()
        self._op = op
        self._cube = op.cube
        self._debug_override: bool | None = None
        self._2x2_delegate_cache: Solver | None = None

        # Create child logger under the parent's namespace.
        prefix = logger_prefix or "Solver"
        self.__logger: CubeLogger = parent_logger.getChild(prefix)  # type: ignore[assignment]
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
        """
        if debug is not None:
            self._debug_override = debug

        # Set logger level based on effective debug state.
        saved_level = self.__logger.level
        if self._is_debug_enabled:
            self.__logger.setLevel(logging.DEBUG)
        elif self._debug_override is not None:
            # Explicitly disabled: set to INFO to override root's level.
            self.__logger.setLevel(logging.INFO)
        # else: debug_override is None → inherit from root (NOTSET)

        try:
            with self._op.with_animation(animation=animation):
                try:
                    if self._cube.size == 2 and not self._is_2x2_solver:
                        return self._delegate_to_2x2(what)

                    self.reset_block_statistics()
                    history_before = len(self._op.history())
                    count_before = self._op.count
                    result = self._solve_impl(what)
                    count_after = self._op.count
                    raw_count = count_after - count_before
                    history_slice = self._op.history()[history_before:]
                    optimized_count = SeqAlg(None, *history_slice).simplify().count() if history_slice else 0

                    stats = self.get_block_statistics()
                    stats.get_topic(MOVE_COUNT_KEY).set_counts(raw_count, optimized_count)
                    stats.get_topic(PARITY_KEY).set_from_results(result)

                    self._display_statistics(stats)
                    return result
                except OpAborted:
                    return SolverResults()
        finally:
            self.__logger.setLevel(saved_level)
            self._debug_override = None

    @property
    def _is_2x2_solver(self) -> bool:
        return False

    @property
    def status(self) -> str:
        if self._cube.size == 2 and not self._is_2x2_solver:
            return self._get_2x2_delegate().status
        return self._status_impl

    @property
    @abstractmethod
    def _status_impl(self) -> str:
        ...

    def supported_steps(self) -> list[SolveStep]:
        if self._cube.size == 2 and not self._is_2x2_solver:
            return self._get_2x2_delegate().supported_steps()
        return self._supported_steps_impl()

    @abstractmethod
    def _supported_steps_impl(self) -> list[SolveStep]:
        ...

    def diagnostic(self) -> None:
        if self._cube.size == 2 and not self._is_2x2_solver:
            self._get_2x2_delegate().diagnostic()
            return
        self._diagnostic_impl()

    def _diagnostic_impl(self) -> None:
        print(f"No diagnostics available for {self.name}")

    def _get_2x2_delegate(self) -> Solver:
        if self._2x2_delegate_cache is None:
            self._2x2_delegate_cache = self._create_2x2_delegate()
        return self._2x2_delegate_cache

    def _create_2x2_delegate(self) -> Solver:
        from cube.domain.solver.Solvers import Solvers
        return Solvers.default_2x2(self._op)

    def _delegate_to_2x2(self, what: SolveStep) -> SolverResults:
        solver_2x2 = self._get_2x2_delegate()
        self._logger.log_lazy(logging.DEBUG, "Delegating to 2x2 solver")
        return solver_2x2.solve(
            debug=self._debug_override,
            animation=None,
            what=what,
        )

    @abstractmethod
    def _solve_impl(self, what: SolveStep) -> SolverResults:
        pass

    def reset_block_statistics(self) -> None:
        pass

    def display_statistics(self) -> None:
        self._display_statistics(self.get_block_statistics())

    def _display_statistics(self, stats: SolverStatistics) -> None:
        if stats.is_empty():
            return
        my_prefix: str = self._logger.name.split(".")[-1] + ":"
        self._logger.log_lazy(logging.DEBUG, "[Solver Statistics]")
        for topic_name, lines in stats.format_all(strip_prefix=my_prefix):
            for line in lines:
                self._logger.log_lazy(logging.DEBUG, lambda: f"  [{topic_name}] {line}")
        self._logger.log_lazy(logging.DEBUG, "==== End of Solver Statistics ===========")


    def _run_child_solver(self, child: Solver, what: SolveStep) -> SolverResults:
        if self._debug_override is not None:
            return child.solve(debug=self._debug_override, animation=None, what=what)
        else:
            return child.solve(animation=None, what=what)

    # =========================================================================

    @final
    @property
    def is_solved(self) -> bool:
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
        return self.__logger.isEnabledFor(logging.DEBUG)

    @property
    def _logger(self) -> CubeLogger:
        """The logger for this solver."""
        return self.__logger

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

            with self._op.save_history():
                self.solve(debug=None, animation=False)
                while n < len(self.op.history()):
                    step = self.op.undo(animation=False)
                    if step:
                        solution_algs.insert(0, step)

            return Algs.alg(None, *solution_algs)

    @property
    @final
    def cmn(self) -> CommonOp:
        return self.common
