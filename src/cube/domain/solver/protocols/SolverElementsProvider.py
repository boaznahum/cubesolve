"""SolverElementsProvider protocol - minimal interface for solver components.

This protocol defines the minimal interface that SolverElement and CommonOp
need from a solver. It allows components like reducers to use solver elements
without being full solvers themselves.

See: src/cube/domain/solver/SOLVER_ARCHITECTURE.md for class hierarchy.
"""

from __future__ import annotations

from abc import ABCMeta
from typing import TYPE_CHECKING, Protocol

from cube.utils.config_protocol import ConfigProtocol
from cube.utils.logger_protocol import ILogger

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.solver.common.CommonOp import CommonOp
    from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol


class SolverElementsProvider(Protocol, metaclass=ABCMeta):
    """
    Minimal protocol for classes that support solver elements.

    This is the minimal interface that SolverElement and CommonOp need.
    Both BaseSolver and AbstractReducer implement this protocol.

    This enables reducers to use solver components (like NxNCenters, NxNEdges)
    without being full solvers themselves, eliminating the need for facade
    classes like the former _ReducerSolverFacade.

    Implementors:
        - BaseSolver (solvers)
        - AbstractReducer (reducers)
    """

    @property
    def op(self) -> "OperatorProtocol":
        """The operator for cube manipulation."""
        ...

    @property
    def cube(self) -> "Cube":
        """The cube being solved."""
        ...

    @property
    def cmn(self) -> "CommonOp":
        """Common operations' helper."""
        ...

    def debug(self, *args) -> None:
        """Output debug information.

        DEPRECATED: Use self._logger.debug(None, ...) instead.
        """
        ...

    @property
    def _logger(self) -> ILogger:
        """The logger for this solver/reducer.

        Created via cube.sp.logger.with_prefix() with debug_flag callback.
        Child elements can chain with: self._logger.with_prefix("ChildName")
        Supports tab() for indented debug sections.
        """
        ...

    @property
    def config(self) -> ConfigProtocol:
        return self.op.app_state.config
