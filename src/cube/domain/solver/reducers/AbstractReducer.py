"""Abstract base class for reducers that implements SolverElementsProvider.

This enables reducers to use solver components (like NxNCenters, NxNEdges)
by providing the minimal interface they need, without being full solvers.

See: src/cube/domain/solver/SOLVER_ARCHITECTURE.md for class hierarchy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol
from cube.domain.solver.protocols.ReducerProtocol import (
    ReducerProtocol,
    ReductionResults,
)
from cube.domain.solver.protocols.SolverElementsProvider import SolverElementsProvider
from cube.utils.logger_protocol import ILogger, LazyArg

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.solver.common.CommonOp import CommonOp


class AbstractReducer(ReducerProtocol, SolverElementsProvider, ABC):
    """
    Abstract base class for reducers that provides SolverElementsProvider interface.

    This class provides the minimal interface that SolverHelper and CommonOp need,
    allowing reducers to use solver components (like NxNCenters, NxNEdges, L3Corners)
    without being full Solver implementations.

    By inheriting from this class, reducers can pass `self` to solver elements
    instead of using a facade class.

    Subclasses must implement:
        - is_reduced() -> bool
        - reduce(debug: bool) -> ReductionResults
        - fix_edge_parity() -> None
        - fix_corner_parity() -> None
        - solve_centers() -> None
        - solve_edges() -> bool
        - centers_solved() -> bool
        - edges_solved() -> bool
        - status: str (property)
    """

    __slots__ = ["_op", "_cube", "_cmn", "_debug_override", "__logger"]

    def __init__(self, op: OperatorProtocol, logger_prefix: str | None = None) -> None:
        """
        Initialize the AbstractReducer.

        Args:
            op: Operator for cube manipulation
            logger_prefix: Prefix for logger output (default: "Reducer")
        """
        self._op = op
        self._cube = op.cube
        self._debug_override: bool | None = None
        # Create logger with prefix (passed explicitly by subclass)
        prefix = logger_prefix or "Reducer"
        self.__logger: ILogger = self._cube.sp.logger.with_prefix(
            prefix,
            debug_flag=lambda: self._is_debug_enabled
        )

        # Create CommonOp passing self (we implement SolverElementsProvider)
        from cube.domain.solver.common.CommonOp import CommonOp
        self._cmn: CommonOp = CommonOp(self)

    # ---- SolverElementsProvider interface ----

    @property
    def op(self) -> OperatorProtocol:
        """The operator for cube manipulation."""
        return self._op

    @property
    def cube(self) -> "Cube":
        """The cube being reduced."""
        return self._cube

    @property
    def cmn(self) -> "CommonOp":
        """Common operations helper."""
        return self._cmn

    def debug(self, *args: LazyArg) -> None:
        """Output debug information.

        Args:
            *args: Arguments to print. Can be regular values or Callable[[], Any]
                   for lazy evaluation.
        """
        self.__logger.debug(None, *args)

    @property
    def _logger(self) -> ILogger:
        """The logger for this reducer, with prefix and debug flag."""
        return self.__logger

    # ---- Debug configuration ----

    @property
    def _is_debug_enabled(self) -> bool:
        """Check if debug output is enabled."""
        if self._debug_override is None:
            return self._cube.config.solver_debug
        else:
            return self._debug_override

    # ---- ReducerProtocol interface (abstract) ----

    @abstractmethod
    def is_reduced(self) -> bool:
        """Check if cube is already reduced to 3x3 state."""
        ...

    @abstractmethod
    def reduce(self, debug: bool = False) -> ReductionResults:
        """Reduce NxN cube to 3x3 virtual state."""
        ...

    @abstractmethod
    def fix_edge_parity(self) -> None:
        """Fix even cube edge parity (OLL parity)."""
        ...

    @abstractmethod
    def fix_corner_parity(self) -> None:
        """Fix even cube corner swap parity (PLL parity)."""
        ...

    @abstractmethod
    def solve_centers(self) -> None:
        """Solve only centers (first part of reduction)."""
        ...

    @abstractmethod
    def solve_edges(self) -> bool:
        """Solve only edges (second part of reduction)."""
        ...

    @abstractmethod
    def centers_solved(self) -> bool:
        """Check if centers are reduced."""
        ...

    @abstractmethod
    def edges_solved(self) -> bool:
        """Check if edges are reduced."""
        ...

    @property
    @abstractmethod
    def status(self) -> str:
        """Human-readable status of reduction state."""
        ...
