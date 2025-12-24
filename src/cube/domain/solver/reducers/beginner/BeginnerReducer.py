"""Beginner reducer - standard NxN to 3x3 cube reduction."""

from __future__ import annotations

from cube.domain.solver.common.big_cube.FacesTrackerHolder import FacesTrackerHolder
from cube.domain.solver.common.big_cube.NxNCenters import NxNCenters
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.ReducerProtocol import ReductionResults
from cube.domain.solver.reducers.AbstractReducer import AbstractReducer


class BeginnerReducer(AbstractReducer):
    """
    Standard NxN to 3x3 reducer using beginner method.

    Reduces an NxN cube (4x4, 5x5, etc.) to a virtual 3x3 by:
    1. Solving centers (grouping center pieces by color)
    2. Solving edges (pairing edge pieces)

    Supports both basic and advanced edge parity algorithms.

    Inherits from AbstractReducer which provides the SolverElementsProvider
    interface, allowing this reducer to use solver components (NxNCenters,
    NxNEdges, NxNCorners) directly without needing a facade class.
    """

    __slots__ = ["_nxn_edges", "_nxn_corners"]

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
        super().__init__(op)

        # Import here to avoid circular imports
        from cube.domain.solver.common.big_cube.NxNCorners import NxNCorners
        from cube.domain.solver.common.big_cube.NxNEdges import NxNEdges

        # Pass self (we implement SolverElementsProvider via AbstractReducer)
        self._nxn_edges = NxNEdges(self, advanced_edge_parity)
        self._nxn_corners = NxNCorners(self)

    def is_reduced(self) -> bool:
        """Check if cube is already reduced to 3x3 state.

        Returns True if:
        - Cube is already 3x3, or
        - All centers and edges are solved (reduced)
        """
        if self.cube.is3x3:
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
        with FacesTrackerHolder(self) as holder:
            centers = NxNCenters(self)
            centers.solve(holder)

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

    def fix_corner_parity(self) -> None:
        """Fix even cube corner swap parity (PLL parity).

        Called by orchestrator when 3x3 solver detects corner swap parity.
        Uses inner slice moves to swap two diagonal corners.

        Note:
            After this fix, a re-reduction is typically needed because the
            inner slice moves disturb the reduced edge pairing.
        """
        self._nxn_corners.fix_corner_parity()

    def centers_solved(self) -> bool:
        """Check if centers are reduced."""



        return NxNCenters.is_cube_solved(self.cube)

    def edges_solved(self) -> bool:
        """Check if edges are reduced."""
        return self._nxn_edges.solved()

    @property
    def status(self) -> str:
        """Human-readable status of reduction state."""
        cube = self.cube

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
