"""Beginner reducer - standard NxN to 3x3 cube reduction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.ReducerProtocol import ReducerProtocol, ReductionResults
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.SolverName import SolverName
from cube.domain.solver.solver import SolverResults, SolveStep

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube


class _ReducerSolverFacade(BaseSolver):
    """
    Minimal BaseSolver facade for NxNCenters and NxNEdges.

    NxNCenters and NxNEdges require a BaseSolver instance, but we don't
    want BeginnerReducer to be a full solver. This facade provides the
    minimum interface needed.
    """

    __slots__: list[str] = []

    def __init__(self, op: OperatorProtocol) -> None:
        super().__init__(op)

    @property
    def get_code(self) -> SolverName:
        return SolverName.LBL

    @property
    def status(self) -> str:
        return "Reducer"

    def solve(
        self,
        debug: bool | None = None,
        animation: bool | None = True,
        what: SolveStep = SolveStep.ALL
    ) -> SolverResults:
        raise NotImplementedError("Use orchestrator for full solve")


class BeginnerReducer(ReducerProtocol):
    """
    Standard NxN to 3x3 reducer using beginner method.

    Reduces an NxN cube (4x4, 5x5, etc.) to a virtual 3x3 by:
    1. Solving centers (grouping center pieces by color)
    2. Solving edges (pairing edge pieces)

    Supports both basic and advanced edge parity algorithms.

    Inherits from ReducerProtocol to satisfy the project's convention
    of implementations inheriting from protocols.
    """

    __slots__ = ["_op", "_solver_facade", "_nxn_centers", "_nxn_edges"]

    def __init__(
        self,
        op: OperatorProtocol,
        advanced_edge_parity: bool = False
    ) -> None:
        """
        Create a BeginnerReducer.

        Args:
            op: Operator for cube manipulation
            advanced_edge_parity: If True, use advanced R/L-slice parity algorithm.
                                  If False, use simple M-slice parity algorithm.
        """
        self._op = op

        # Create minimal solver facade for NxNCenters/NxNEdges
        self._solver_facade = _ReducerSolverFacade(op)

        # Import here to avoid circular imports
        from cube.domain.solver.beginner.NxNCenters import NxNCenters
        from cube.domain.solver.beginner.NxNEdges import NxNEdges

        self._nxn_centers = NxNCenters(self._solver_facade)
        self._nxn_edges = NxNEdges(self._solver_facade, advanced_edge_parity)

    @property
    def op(self) -> OperatorProtocol:
        """The operator for cube manipulation."""
        return self._op

    @property
    def _cube(self) -> "Cube":
        """Internal access to the cube."""
        return self._op.cube

    def is_reduced(self) -> bool:
        """Check if cube is already reduced to 3x3 state.

        Returns True if:
        - Cube is already 3x3, or
        - All centers and edges are solved (reduced)
        """
        if self._cube.is3x3:
            return True
        return self.centers_solved() and self.edges_solved()

    def reduce(self, debug: bool = False) -> ReductionResults:
        """
        Reduce NxN cube to 3x3 virtual state.

        Solves centers first, then edges.

        Args:
            debug: Enable debug output

        Returns:
            ReductionResults with flags about what was detected
        """
        results = ReductionResults()

        if self.is_reduced():
            return results

        # Solve centers
        self.solve_centers()

        # Solve edges (returns True if parity was detected/fixed)
        if self.solve_edges():
            results.partial_edge_parity_detected = True

        return results

    def solve_centers(self) -> None:
        """Solve only centers (first part of reduction)."""
        self._nxn_centers.solve()

    def solve_edges(self) -> bool:
        """Solve only edges (second part of reduction).

        Returns:
            True if edge parity was detected/fixed during reduction.
        """
        return self._nxn_edges.solve()

    def fix_edge_parity(self) -> None:
        """Fix even cube edge parity (OLL parity).

        Called by orchestrator when 3x3 solver detects edge parity
        during L3 solving.
        """
        self._nxn_edges.do_even_full_edge_parity_on_any_edge()

    def centers_solved(self) -> bool:
        """Check if centers are reduced."""
        return self._nxn_centers.solved()

    def edges_solved(self) -> bool:
        """Check if edges are reduced."""
        return self._nxn_edges.solved()

    @property
    def status(self) -> str:
        """Human-readable status of reduction state."""
        cube = self._cube

        if cube.is3x3:
            return "3x3"

        parts: list[str] = []

        if cube.is_boy:
            parts.append("Boy:True")
        else:
            parts.append("Boy:False")

        if self.centers_solved():
            parts.append("Centers")
        else:
            parts.append("No Centers")

        if self.edges_solved():
            parts.append("Edges")
        else:
            parts.append("No Edges")

        return ", ".join(parts)
