"""Cage-aware center solver that preserves edges.

This extends NxNCenters but disables the _swap_slice optimization
which breaks edge pairing. The commutators (_block_communicator)
preserve edges, but _swap_slice does not.

_swap_slice uses: M * mul + U2 + M' * mul (not a commutator)
This pattern moves edges temporarily and doesn't restore them.

_block_communicator uses: [M1', F, M2', F', M1, F, M2, F']
This is a proper commutator that preserves non-targeted pieces.
"""

from __future__ import annotations

from cube.domain.solver.beginner.NxNCenters import NxNCenters


class CageCenters(NxNCenters):
    """
    Center solver for Cage method that preserves solved edges.

    Inherits all logic from NxNCenters but:
    - Disables _swap_slice optimization (which breaks edges)
    - Only uses _block_communicator (which preserves edges)
    - Respects cage_mode flag if set on solver
    """

    def __init__(self, slv) -> None:
        super().__init__(slv)
        # Disable the complete slice swap optimization
        # This optimization uses M U2 M' which breaks edge pairing
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = False

    def solve(self):
        """Solve centers, but skip if cage_mode is enabled."""
        # Check for cage_mode on the solver facade
        if hasattr(self._solver, 'cage_mode') and self._solver.cage_mode:
            return

        # Normal center solving (without _swap_slice due to disabled config)
        super().solve()
