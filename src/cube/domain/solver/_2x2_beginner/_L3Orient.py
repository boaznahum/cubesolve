"""Layer 3 orientation solver for 2x2 beginner method.

Orients all 4 top-layer corners so that the yellow sticker faces up.
This is the 2x2 equivalent of OLL (Orientation of Last Layer).

Strategy (human approach — Sune algorithm):
1. Hold the cube with unsolved layer on top
2. Count how many corners have yellow on top (0, 1, 2, or 4)
3. If 4: already oriented — done
4. If 0, 1, or 2: position a corner with yellow NOT on top
   at the front-right-up position
5. Apply Sune: R U R' U R U2 R'
6. Repeat until all 4 corners have yellow on top

The Sune algorithm twists the URF corner and cycles orientation
of the other three. At most 3 applications are needed.
"""

from __future__ import annotations

from cube.domain.solver.common.SolverHelper import StepSolver
from cube.domain.solver.protocols import SolverElementsProvider


class L3Orient(StepSolver):
    """Last layer corner orientation solver for 2x2."""

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "L3Orient")

    @property
    def is_solved(self) -> bool:
        """Check if all 4 top-layer corners have yellow facing up."""
        # TODO: implement check
        return False

    def solve(self) -> None:
        """Orient all last-layer corners (yellow face up)."""
        if self.is_solved:
            return
        # TODO: implement
        raise NotImplementedError("L3Orient solve not yet implemented")
