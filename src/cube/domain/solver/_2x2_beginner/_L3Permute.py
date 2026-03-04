"""Layer 3 permutation solver for 2x2 beginner method.

Permutes the 4 top-layer corners into their correct positions.
At this point all corners are already oriented (yellow on top).
This is the 2x2 equivalent of PLL (Permutation of Last Layer).

Strategy (human approach):
1. Check if any top-layer corner is already in its correct position
   (correct position = the corner's colors match the adjacent face colors)
2. If one correct corner found: hold it at front-left-up,
   apply the permutation algorithm to cycle the other three
3. If no correct corner found: apply the algorithm once from any angle,
   then one correct corner will appear — repeat step 2
4. If all corners correct: done

The permutation algorithm cycles 3 corners (URF → UBR → ULB)
while keeping UFL fixed:
   R U' L' U R' U' L U  (or equivalent)
"""

from __future__ import annotations

from cube.domain.solver.common.SolverHelper import StepSolver
from cube.domain.solver.protocols import SolverElementsProvider


class L3Permute(StepSolver):
    """Last layer corner permutation solver for 2x2."""

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "L3Permute")

    @property
    def is_solved(self) -> bool:
        """Check if all 4 top-layer corners are in correct positions."""
        # TODO: implement check
        return False

    def solve(self) -> None:
        """Permute last-layer corners into correct positions."""
        if self.is_solved:
            return
        # TODO: implement
        raise NotImplementedError("L3Permute solve not yet implemented")
