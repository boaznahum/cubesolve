"""Layer 1 solver for 2x2 beginner method.

Solves all 4 first-layer corners so that:
- Each corner is in its correct position
- Each corner is correctly oriented

Since a 2x2 cube has no centers, faces have no inherent color.
This solver delegates directly to ``_2x2L1Corners`` which works
entirely with corner sticker colors — no ``FacesColorsProvider``
is needed.
"""

from __future__ import annotations

from cube.domain.solver._2x2_beginner._2x2L1Corners import _2x2L1Corners
from cube.domain.solver.common.SolverHelper import StepSolver
from cube.domain.solver.protocols import SolverElementsProvider


class L1(StepSolver):
    """First layer corner solver for 2x2.

    Delegates to ``_2x2L1Corners`` which solves using corner sticker
    colors only — no face color provider required.
    """

    __slots__: list[str] = []

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "L1")

    @property
    def is_solved(self) -> bool:
        """Check if all 4 first-layer corners are correctly placed and oriented."""
        l1_corners = _2x2L1Corners(self)
        return l1_corners.is_corners()

    def solve(self) -> None:
        """Solve the first layer (4 corners)."""
        if self.is_solved:
            return

        l1_corners = _2x2L1Corners(self)
        l1_corners.solve()
