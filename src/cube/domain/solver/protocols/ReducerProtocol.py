"""Reducer protocol - interface for NxN to 3x3 cube reduction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from cube.domain.solver.common.SolverStatistics import SolverStatistics
    from cube.domain.solver.common.big_cube.CornerSwapParity import CornerFixResults
    from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol
    from cube.domain.solver.solver import SolverResults


class ReducerProtocol(Protocol):
    """
    Protocol for NxN to 3x3 cube reduction.

    A reducer takes an NxN cube (4x4, 5x5, etc.) and reduces it to
    a virtual 3x3 cube by:
    1. Solving centers (grouping center pieces)
    2. Solving edges (pairing edge pieces)

    After reduction, the cube can be solved using any 3x3 solver.

    Implementations should inherit from this protocol.
    """

    @property
    def op(self) -> "OperatorProtocol":
        """The operator for cube manipulation."""
        ...

    def is_reduced(self) -> bool:
        """Check if cube is already reduced to 3x3 state.

        Returns True if:
        - Cube is already 3x3, or
        - All centers and edges are solved (reduced)
        """
        ...

    def reduce(self, debug: bool = False) -> "SolverResults":
        """
        Reduce NxN cube to 3x3 virtual state.

        Solves centers and edges so the cube behaves like a 3x3.

        Args:
            debug: Enable debug output

        Returns:
            SolverResults with PartialEdge parity recorded if detected during reduction.
        """
        ...

    def fix_edge_parity(self, advanced: bool) -> "SolverResults":
        """Fix even cube edge parity (OLL parity).

        Called by orchestrator when 3x3 solver detects edge parity.

        Args:
            advanced: If True, request R/L-slice algorithm.

        Returns:
            SolverResults with EvenEdge parity recorded.
        """
        ...

    def fix_corner_parity(self, advanced: bool) -> "CornerFixResults":
        """Fix even cube corner swap parity (PLL parity).

        Called by orchestrator when 3x3 solver detects corner swap parity.

        Args:
            advanced: If True, use algorithm that preserves edge positions
                      (edges move during execution but return to original positions).
                      If False, use basic algorithm that moves edges to new positions.

        Returns:
            CornerFixResults with fix details (need_resolve_3x3, cube_unreduced flags).
        """
        ...

    def solve_centers(self) -> None:
        """Solve only centers (first part of reduction)."""
        ...

    def solve_edges(self) -> "SolverResults":
        """Solve only edges (second part of reduction).

        Returns:
            SolverResults with PartialEdge parity recorded if detected.
        """
        ...

    def centers_solved(self) -> bool:
        """Check if centers are reduced."""
        ...

    def edges_solved(self) -> bool:
        """Check if edges are reduced."""
        ...

    @property
    def status(self) -> str:
        """Human-readable status of reduction state."""
        ...

    def get_block_statistics(self) -> "SolverStatistics":
        """Return block statistics from reduction."""
        ...

    def reset_block_statistics(self) -> None:
        """Reset block statistics."""
        ...
