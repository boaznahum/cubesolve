"""NxN corner parity fix algorithm.

This module provides the corner swap (PLL parity) fix for even NxN cubes.
Used by reducers and direct solvers when corner parity is detected.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.algs import Algs
from cube.domain.solver.common.SolverElement import SolverElement

if TYPE_CHECKING:
    from cube.domain.solver.protocols import SolverElementsProvider


class NxNCorners(SolverElement):
    """Provides corner parity fix for even NxN cubes.

    This class contains the PLL parity algorithm that swaps two adjacent
    corners on even cubes. It's used by reducers and direct solvers
    to fix corner parity detected during 3x3 solving phase.
    """

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv)

    def fix_corner_parity(self) -> None:
        """Fix corner swap parity on even cube.

        Uses the standard PLL parity algorithm:
        2-kRw2 U2 2-kRw2 kUw2 2-kRw2 kUw2

        Where k = n_slices // 2 (half the cube width).
        """
        n_slices = self.cube.n_slices
        assert n_slices % 2 == 0, "Corner parity fix only applies to even cubes"

        self.debug("Doing corner swap (PLL parity fix)")

        nh = n_slices // 2

        # 2-kRw2 U2
        # 2-kRw2 kUw2  // half cube
        # 2-kRw2 kUw2  // half cube
        alg = Algs.alg(None,
                       Algs.R[2:nh + 1] * 2, Algs.U * 2,
                       Algs.R[2:nh + 1] * 2 + Algs.U[1:nh + 1] * 2,
                       Algs.R[2:nh + 1] * 2, Algs.U[1:nh + 1] * 2
                       )

        with self.ann.annotate(h1="Corner swap (PLL Parity)"):
            self.op.play(alg)
