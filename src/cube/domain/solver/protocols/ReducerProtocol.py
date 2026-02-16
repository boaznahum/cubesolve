"""Reducer protocol - interface for NxN to 3x3 cube reduction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from cube.domain.solver.common.CenterBlockStatistics import CenterBlockStatistics
    from cube.domain.solver.protocols.OperatorProtocol import OperatorProtocol


class ReductionResults:
    """Results from NxN cube reduction.

    Contains flags indicating what was detected during reduction.
    """

    __slots__ = ["_partial_edge_parity_detected"]

    def __init__(self) -> None:
        self._partial_edge_parity_detected: bool = False

    @property
    def partial_edge_parity_detected(self) -> bool:
        """Whether partial edge parity was detected during reduction."""
        return self._partial_edge_parity_detected

    @partial_edge_parity_detected.setter
    def partial_edge_parity_detected(self, value: bool) -> None:
        self._partial_edge_parity_detected = value


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

    def reduce(self, debug: bool = False) -> ReductionResults:
        """
        Reduce NxN cube to 3x3 virtual state.

        Solves centers and edges so the cube behaves like a 3x3.

        Args:
            debug: Enable debug output

        Returns:
            ReductionResults with flags about what was detected
        """
        ...

    def fix_edge_parity(self) -> None:
        """Fix even cube edge parity (OLL parity).

        Called by orchestrator when 3x3 solver detects edge parity.
        """
        ...

    def fix_corner_parity(self) -> None:
        """Fix even cube corner swap parity (PLL parity).

        Called by orchestrator when 3x3 solver detects corner swap parity.
        Uses inner slice moves to swap two diagonal corners.
        """
        ...

    def solve_centers(self) -> None:
        """Solve only centers (first part of reduction)."""
        ...

    def solve_edges(self) -> bool:
        """Solve only edges (second part of reduction).

        Returns:
            True if edge parity was detected/fixed during reduction.
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

    def get_block_statistics(self) -> "CenterBlockStatistics":
        """Return block statistics from reduction."""
        ...

    def reset_block_statistics(self) -> None:
        """Reset block statistics."""
        ...
