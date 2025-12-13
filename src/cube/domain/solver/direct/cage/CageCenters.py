"""Cage-aware center solver that preserves edges.

This extends NxNCenters but disables the _swap_slice optimization
which breaks edge pairing. The commutators (_block_communicator)
preserve edges, but _swap_slice does not.

=============================================================================
WHY COMMUTATORS PRESERVE EDGES
=============================================================================

The key insight is that _block_communicator uses TWO DIFFERENT non-overlapping
M-slices (columns), which creates a proper commutator:

    [M1', F, M2', F', M1, F, M2, F']

    where M1 and M2 are different columns (e.g., column 1 and column 2)

This preserves edges because:
1. M1' moves one column of centers
2. F rotates the front face
3. M2' moves a DIFFERENT column
4. F' undoes the F rotation
5. M1 undoes M1'
6. F rotates again
7. M2 undoes M2'
8. F' undoes the final F

The net effect is a 3-cycle of center pieces with NO net movement of edges.

=============================================================================
WHY _swap_slice BREAKS EDGES
=============================================================================

_swap_slice uses: M * mul + U2 + M' * mul

This pattern is NOT a commutator:
- M moves a column of centers AND edges
- U2 swaps pieces on the U face
- M' restores the column but edges have been swapped

This is efficient for reduction (centers first) but breaks the Cage method
where edges are solved first.

=============================================================================
SOLUTION
=============================================================================

By setting _OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = False,
we disable _swap_slice and force the solver to use only _block_communicator,
which preserves edge pairing.

Note: Commutators preserve edge PAIRING (wings stay together) but may MOVE
edges to different positions. The Cage solver handles this by re-solving
the 3x3 skeleton after centers are done.
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
