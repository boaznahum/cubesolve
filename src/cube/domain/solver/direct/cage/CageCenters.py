"""Cage-aware center solver.

This extends NxNCenters to check the cage_mode flag on the solver facade.
When cage_mode is True, solve() returns early without doing anything.

This allows the Cage solver to:
1. Build the cage (edges + 3x3) with cage_mode=True
2. Solve centers with cage_mode=False
"""

from __future__ import annotations

from cube.domain.solver.beginner.NxNCenters import NxNCenters


class CageCenters(NxNCenters):
    """
    Center solver that respects cage_mode flag.

    When slv.cage_mode is True, solve() returns early.
    This is used during cage building phase to skip center reduction.
    """

    def solve(self):
        """Solve centers, but skip if cage_mode is enabled."""
        # Check for cage_mode on the solver
        if hasattr(self.slv, 'cage_mode') and self.slv.cage_mode:
            # In cage mode: skip center reduction
            return

        # Normal center solving
        super().solve()
