"""Corner swap parity fix — basic and advanced algorithms.

Unlike the basic algorithm which moves edges to new positions,
the advanced algorithm swaps two diagonal U-face corners while returning
all edges to their original positions, eliminating the need for re-reduction.

Basic algorithm: standard PLL parity
Advanced algorithm: Mowla's 17-move diagonal corner swap
    https://www.speedsolving.com/threads/new-two-corner-swap-algorithm-technique-for-big-even-cubes-pll-parity.21725/

Generalized for NxN by mapping:
    r   → R[2:nh+1]   (inner R slices only, no outer layer)
    R   → R            (outer R layer only)
    Rw  → R[1:nh+1]   (outer R + inner slices = wide R half-cube)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.algs import Algs
from cube.domain.solver.common.SolverHelper import SolverHelper

if TYPE_CHECKING:
    from cube.domain.solver.protocols import SolverElementsProvider


class CornerSwapParity(SolverHelper):
    """Fix corner swap parity on even cubes — basic or advanced.

    Basic: swaps diagonal corners, moves edges to new positions (pairing preserved).
    Advanced: swaps diagonal corners, edges return to original positions.
    """

    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver, "CornerSwapParity")

    def fix_corner_parity(self, advanced) -> bool:
        """Fix corner swap parity on even cube.

        Args:
            advanced: If True, request algorithm that preserves edge positions.

        Returns:
            True if edges were preserved (no re-reduce needed),
            False if edges were moved to new positions.
        """
        if advanced:
            self._fix_advanced()
            return True
        self._fix_basic()
        return False

    def _fix_basic(self) -> None:
        """Basic corner swap — swaps diagonal corners, moves edges to new positions.

        Uses the standard PLL parity algorithm:
            2-kRw2 U2 2-kRw2 kUw2 2-kRw2 kUw2

        Where k = n_slices // 2 (half the cube width).

        The algorithm doesn't target specific corners — any diagonal swap
        fixes the parity. Edge pairing is preserved (cube stays in reduced
        3x3 state), but edges move to different positions, so the 3x3
        solve must restart from scratch.
        """
        n_slices = self.cube.n_slices
        assert n_slices % 2 == 0, "Corner parity fix only applies to even cubes"

        self.debug("Doing corner swap (basic — edges move)")

        nh = n_slices // 2

        alg = Algs.alg(None,
                       Algs.R[2:nh + 1] * 2, Algs.U * 2,
                       Algs.R[2:nh + 1] * 2 + Algs.U[1:nh + 1] * 2,
                       Algs.R[2:nh + 1] * 2, Algs.U[1:nh + 1] * 2
                       )

        with self.ann.annotate(h1="Corner swap (PLL Parity)"):
            self.op.play(alg)

    def _fix_advanced(self) -> None:
        """Advanced corner swap — edges return to original positions.

        Uses Mowla's 17-move diagonal corner swap generalized for NxN:
            r2 B2 R' U2 Rw2 U2 B2 R' B2 r2 U2 Rw2 B2 U2 R' U2 Rw2

        Source: https://www.speedsolving.com/threads/new-two-corner-swap-algorithm-technique-for-big-even-cubes-pll-parity.21725/

        Notation mapping for NxN (nh = n_slices // 2):
            r  = R[2:nh+1]  — inner R slices only (4x4: R[2:2], 6x6: R[2:3])
            R  = Algs.R     — outer R layer only
            Rw = R[1:nh+1]  — wide R half-cube (4x4: R[1:2], 6x6: R[1:3])
        """
        n_slices = self.cube.n_slices
        assert n_slices % 2 == 0, "Corner parity fix only applies to even cubes"

        self.debug("Doing corner swap (advanced — edges preserved)")

        nh = n_slices // 2

        r_inner = Algs.R[2:nh + 1]   # inner R slices only
        r_wide = Algs.R[1:nh + 1]    # wide R: outer + inner half
        b2 = Algs.B * 2
        u2 = Algs.U * 2

        # Mowla's 17-move diagonal corner swap:
        # r2 B2 R' U2 Rw2 U2 B2 R' B2 r2 U2 Rw2 B2 U2 R' U2 Rw2
        alg = Algs.alg(None,
                       r_inner * 2, b2, Algs.R.prime, u2,
                       r_wide * 2, u2, b2, Algs.R.prime, b2,
                       r_inner * 2, u2,
                       r_wide * 2, b2, u2, Algs.R.prime, u2,
                       r_wide * 2,
                       )

        with self.ann.annotate(h1="Advanced Corner Swap (edges preserved)"):
            self.op.play(alg)
