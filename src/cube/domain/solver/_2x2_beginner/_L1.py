"""Layer 1 solver for 2x2 beginner method.

Solves all 4 bottom-layer corners so that:
- Each corner is in its correct position
- Each corner is correctly oriented (white sticker facing down)

Strategy (human approach):
1. Find a white corner in the top layer (or misplaced in bottom layer)
2. Rotate U to position it above its target slot
3. Use a trigger move (R U R') or variant to insert it
4. Repeat for all 4 corners

If a white corner is stuck in the bottom layer with wrong orientation,
first extract it to the top layer, then re-insert it correctly.
"""

from __future__ import annotations

from cube.domain.solver.common.SolverHelper import StepSolver
from cube.domain.solver.protocols import SolverElementsProvider


class L1(StepSolver):
    """First layer corner solver for 2x2."""

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "L1")

    @property
    def is_solved(self) -> bool:
        """Check if all 4 bottom-layer corners are correctly placed and oriented."""
        # TODO: implement check
        return False

    def solve(self) -> None:
        """Solve the first layer (4 bottom corners)."""
        if self.is_solved:
            return
        # TODO: implement
        raise NotImplementedError("L1 solve not yet implemented")
