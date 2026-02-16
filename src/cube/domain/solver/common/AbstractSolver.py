from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from cube.domain.algs.Alg import Alg
from cube.domain.algs.Algs import Algs
from cube.domain.exceptions import OpAborted
from cube.domain.model import Cube
from cube.domain.solver import Solver
from cube.domain.solver.common.CenterBlockStatistics import CenterBlockStatistics
from cube.domain.solver.common.CommonOp import CommonOp
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.utils.logger_protocol import ILogger, LazyArg

if TYPE_CHECKING:
    pass


class AbstractSolver(Solver, ABC):
    """Abstract base class for all solvers.

    Logger Architecture:
        Every solver receives a parent_logger and creates its own logger via:
            parent_logger.with_prefix(prefix, debug_flag=lambda: self._is_debug_enabled)

        - Root solver: receives cube.sp.logger as parent_logger
        - Child solver: receives parent._logger as parent_logger

        Each solver controls its own debug output via its own _is_debug_enabled.
        Prefix chaining provides context: "LBL:Beginner3x3:L1Cross: message"
    """
    __slots__: list[str] = ["_common", "_op", "_cube", "_debug_override", "__logger"]

    def __init__(
        self,
        op: OperatorProtocol,
        parent_logger: ILogger,
        logger_prefix: str | None = None,
    ) -> None:
        super().__init__()
        # Set _op and _cube BEFORE CommonOp - CommonOp needs self.op
        self._op = op
        self._cube = op.cube
        self._debug_override: bool | None = None

        # Create logger from parent with this solver's own debug_flag
        prefix = logger_prefix or "Solver"
        self.__logger: ILogger = parent_logger.with_prefix(
            prefix,
            debug_flag=lambda: self._is_debug_enabled
        )
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
        4. Statistics are reset before and displayed after solving

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
                    self.reset_block_statistics()
                    count_before = self._op.count
                    result = self._solve_impl(what)
                    count_after = self._op.count
                    self.debug(f"Solve {what.name} used {count_after - count_before} moves (total: {count_after})")
                    self.display_statistics()
                    return result
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

    def reset_block_statistics(self) -> None:
        """Reset block statistics before solving.

        Override in subclasses to reset any statistics counters.
        Called automatically by solve() before _solve_impl().

        Default implementation does nothing.
        """
        pass

    def display_statistics(self) -> None:
        """Display block statistics collected from all sub-helpers.

        Uses get_block_statistics() from the Solver protocol to aggregate
        stats from the entire helper tree. Only the root solver's
        display_statistics() runs (via solve() template method), so
        child solvers don't duplicate output.
        """
        stats: CenterBlockStatistics = self.get_block_statistics()
        if stats.is_empty():
            return
        # Strip solver's own prefix from topic names to avoid redundancy
        my_prefix: str = self._logger.prefix + ":"
        summary = stats.get_summary_stats()
        total_blocks = sum(summary.values())
        total_pieces = sum(size * count for size, count in summary.items())
        self.debug(f"[Center Block Statistics] {total_blocks} blocks, {total_pieces} pieces moved")
        for topic in stats.get_all_topics():
            display_topic = topic.replace(my_prefix, "")
            topic_stats = stats.get_topic_stats(topic)
            if topic_stats:
                parts = [f"{size}x1:{count}" for size, count in sorted(topic_stats.items())]
                total = sum(topic_stats.values())
                self.debug(f"  [{display_topic}] {', '.join(parts)} (total: {total} blocks)")
            else:
                self.debug(f"  [{display_topic}] (no blocks)")
        parts = [f"{size}x1:{count}" for size, count in sorted(summary.items())]
        self.debug(f"  [SUMMARY] {', '.join(parts)} (total: {total_blocks} blocks)")

    def diagnostic(self) -> None:
        """Default no-op diagnostic. Override in subclasses for detailed diagnostics."""
        print(f"No diagnostics available for {self.name}")

    def _run_child_solver(self, child: Solver, what: SolveStep) -> SolverResults:
        """Run a child solver, propagating debug override if set.

        Use this when calling another solver as a helper (e.g., shadow cube solving).
        Propagates the parent's debug override to the child, but only if explicitly set.
        If parent's debug is None (use config), child also uses its own config.
        Animation is set to None to inherit from parent's current animation state.

        Args:
            child: The child solver to run
            what: Which step to solve

        Returns:
            SolverResults from child solver
        """
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
        return self.op.app_state.is_debug(self._is_debug_enabled)

    @property
    def _logger(self) -> ILogger:
        """The logger for this solver, with prefix and debug flag."""
        return self.__logger

    def debug(self, *args: LazyArg) -> None:
        """Output debug information.

        Args:
            *args: Arguments to print. Can be regular values or Callable[[], Any]
                   for lazy evaluation.
        """
        self.__logger.debug(None, *args)

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
