"""Abstract base class for reducers that implements SolverElementsProvider.

This enables reducers to use solver components (like NxNCenters, NxNEdges)
by providing the minimal interface they need, without being full solvers.

See: src/cube/domain/solver/SOLVER_ARCHITECTURE.md for class hierarchy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from cube.domain.solver.ParityFix import ParityFix
from cube.domain.solver.common.SolverStatistics import SolverStatistics
from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol
from cube.domain.solver.protocols.ReducerProtocol import (
    ReducerProtocol,
    ReductionResults,
)
from cube.domain.solver.protocols.SolverElementsProvider import SolverElementsProvider
from cube.utils.logging import CubeLogger

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.solver.common.CommonOp import CommonOp
    from cube.domain.solver.common.big_cube.CornerSwapParity import CornerFixResults


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
        - fix_edge_parity(advanced: bool) -> bool
        - fix_corner_parity(advanced: bool) -> bool
        - solve_centers() -> None
        - solve_edges() -> bool
        - centers_solved() -> bool
        - edges_solved() -> bool
        - status: str (property)
    """

    __slots__ = ["_op", "_cube", "_cmn", "_debug_override", "__logger"]

    def __init__(self, op: OperatorProtocol, logger_prefix: str | None = None) -> None:
        self._op = op
        self._cube = op.cube
        self._debug_override: bool | None = None
        # Create logger as child of cube root logger.
        prefix = logger_prefix or "Reducer"
        self.__logger: CubeLogger = self._cube.sp.logger.getChild(prefix)  # type: ignore[assignment]

        from cube.domain.solver.common.CommonOp import CommonOp
        self._cmn: CommonOp = CommonOp(self)

    # ---- SolverElementsProvider interface ----

    @property
    def op(self) -> OperatorProtocol:
        return self._op

    @property
    def cube(self) -> "Cube":
        return self._cube

    @property
    def cmn(self) -> "CommonOp":
        return self._cmn

    @property
    def _logger(self) -> CubeLogger:
        return self.__logger

    # ---- Debug configuration ----

    @property
    def _is_debug_enabled(self) -> bool:
        if self._debug_override is None:
            return self._cube.config.solver_debug
        else:
            return self._debug_override

    # ---- Block statistics ----

    def get_block_statistics(self) -> SolverStatistics:
        return SolverStatistics()

    def reset_block_statistics(self) -> None:
        pass

    # ---- ReducerProtocol interface (abstract) ----

    @abstractmethod
    def is_reduced(self) -> bool:
        ...

    @abstractmethod
    def reduce(self, debug: bool = False) -> ReductionResults:
        ...

    @abstractmethod
    def fix_edge_parity(self, advanced: bool) -> ParityFix:
        """Fix even cube edge parity (OLL parity).

        Args:
            advanced: If True, request R/L-slice algorithm.

        Returns:
            ParityFix indicating which algorithm was used.
        """
        ...

    @abstractmethod
    def fix_corner_parity(self, advanced: bool) -> CornerFixResults:
        """Fix even cube corner swap parity (PLL parity).

        Args:
            advanced: If True, use algorithm that preserves edge positions.

        Returns:
            CornerFixResults with fix details.
        """
        ...

    @abstractmethod
    def solve_centers(self) -> None:
        ...

    @abstractmethod
    def solve_edges(self) -> ParityFix | None:
        """Solve only edges (second part of reduction)."""
        ...

    @abstractmethod
    def centers_solved(self) -> bool:
        ...

    @abstractmethod
    def edges_solved(self) -> bool:
        ...

    @property
    @abstractmethod
    def status(self) -> str:
        ...
