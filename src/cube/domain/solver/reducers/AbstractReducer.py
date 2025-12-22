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

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.solver.common.CommonOp import CommonOp


class AbstractReducer(ReducerProtocol, SolverElementsProvider, ABC):
    """
    Abstract base class for reducers that provides SolverElementsProvider interface.

    This class provides the minimal interface that SolverElement and CommonOp need,
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

    __slots__ = ["_op", "_cube", "_cmn", "_debug_override", "_debug_prefix"]

    def __init__(self, op: OperatorProtocol) -> None:
        """
        Initialize the AbstractReducer.

        Args:
            op: Operator for cube manipulation
        """
        self._op = op
        self._cube = op.cube
        self._debug_override: bool | None = None
        self._debug_prefix: str = "Reducer"

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

    def debug(self, *args) -> None:
        """Output debug information."""
        if self._is_debug_enabled:
            prefix = self._debug_prefix + ":"
            print("Reducer:", prefix, *(str(x) for x in args))
            self.op.log("Reducer:", prefix, *args)

    # ---- Debug configuration ----

    @property
    def _is_debug_enabled(self) -> bool:
        """Check if debug output is enabled."""
        if self._debug_override is None:
            return self._cube.config.solver_debug
        else:
            return self._debug_override

    def _set_debug_prefix(self, prefix: str) -> None:
        """Set the debug output prefix."""
        self._debug_prefix = prefix

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
