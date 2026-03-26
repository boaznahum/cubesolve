"""Corner swap parity fix — basic and advanced algorithms.

Unlike the basic algorithm which moves edges to new positions,
the advanced algorithms swap two U-face corners while returning
all edges to their original positions, eliminating the need for re-reduction.

Basic algorithm: standard PLL parity (any diagonal swap, edges move)
Advanced algorithms (edges preserved, from Mowla/Gallet):
    Diagonal: swaps FRU ↔ BLU (or equivalent diagonal pair)
    Adjacent: swaps FRU ↔ BRU (or equivalent adjacent pair)

Source: https://www.speedsolving.com/threads/new-two-corner-swap-algorithm-technique-for-big-even-cubes-pll-parity.21725/

Generalized for NxN by mapping:
    r   → R[2:nh+1]   (inner R slices only, no outer layer)
    R   → R            (outer R layer only)
    Rw  → R[1:nh+1]   (outer R + inner slices = wide R half-cube)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.algs import Algs
from cube.domain.model.Corner import Corner
from cube.domain.model.Face import Face
from cube.domain.solver.common.SolverHelper import SolverHelper

if TYPE_CHECKING:
    from cube.domain.solver.protocols import SolverElementsProvider


class CornerSwapParity(SolverHelper):
    """Fix corner swap parity on even cubes — basic or advanced.

    Basic: swaps diagonal corners, moves edges to new positions (pairing preserved).
    Advanced: detects diagonal vs adjacent out-of-position corners, applies
    the matching algorithm. Edges return to original positions.
    """

    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver, "CornerSwapParity")

    def fix_corner_parity(self, advanced: bool) -> bool:
        """Fix corner swap parity on even cube.

        Args:
            advanced: If True, detect diagonal vs adjacent and use the
                      matching edge-preserving algorithm.

        Returns:
            True if edges were preserved (no re-reduce needed),
            False if edges were moved to new positions.
        """
        if advanced:
            return self._fix_advanced()
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

    def _fix_advanced(self) -> bool:
        """Advanced corner swap — detect case and apply matching algorithm.

        Examines the U-face to find the 2 out-of-position corners,
        determines if they're diagonal or adjacent, then applies the
        correct edge-preserving algorithm.

        Falls back to basic if the cube state doesn't allow detection
        (e.g. no corner in position, or not exactly 2 in position).

        Returns:
            True if advanced algorithm was used (edges preserved),
            False if fell back to basic (edges moved).
        """
        n_slices = self.cube.n_slices
        assert n_slices % 2 == 0, "Corner parity fix only applies to even cubes"

        # Use U face directly — bring_face_up ensures it's correct.
        # Don't use cmn.white_face which fails on even cubes in Cage solver
        # (face colors may not be standard BOY scheme).
        yf = self.cube.up

        # Find which corners are out of position
        fru = yf.corner_bottom_right
        flu = yf.corner_bottom_left
        blu = yf.corner_top_left
        bru = yf.corner_top_right

        # Ensure one in-position corner is at FRU.
        # Detectors (L3Corners, PLL) normally set this up, but we don't rely on it.
        if not fru.in_position:
            for c, y_alg in [(bru, Algs.Y), (blu, Algs.Y * 2), (flu, Algs.Y.prime)]:
                if c.in_position:
                    self.op.play(y_alg)
                    break
            # Re-read after rotation
            fru = yf.corner_bottom_right
            flu = yf.corner_bottom_left
            blu = yf.corner_top_left
            bru = yf.corner_top_right

        if not fru.in_position:
            # No corner in position — can't determine diagonal vs adjacent.
            self.debug("Advanced: no corner in position, falling back to basic")
            self._fix_basic()
            return False

        # Count how many of the other 3 corners are in position
        others_in_position = sum(c.in_position for c in [flu, blu, bru])

        if others_in_position == 3:
            # All 4 in position — no parity to fix
            assert False, "All corners in position — no parity detected"

        if others_in_position == 0:
            # 3-cycle: none of FLU/BLU/BRU in position.
            # Apply UR 3-corner-cycle to convert to a 2-swap case.
            ur = Algs.alg(None, Algs.U, Algs.R, Algs.U.prime, Algs.L.prime,
                          Algs.U, Algs.R.prime, Algs.U.prime, Algs.L)
            self.debug("Advanced: 3-cycle detected, applying UR to reduce to 2-swap")
            self.op.play(ur)
            flu = yf.corner_bottom_left
            blu = yf.corner_top_left
            bru = yf.corner_top_right
            others_in_position = sum(c.in_position for c in [flu, blu, bru])

            if others_in_position == 3:
                assert False, "All corners in position after UR — no parity"

            if others_in_position == 0:
                # Wrong cycle direction — undo and try UR'
                self.debug("Advanced: still 3-cycle after UR, trying UR'")
                self.op.play(ur.prime)  # undo UR
                self.op.play(ur.prime)  # apply UR' (inverse cycle)
                flu = yf.corner_bottom_left
                blu = yf.corner_top_left
                bru = yf.corner_top_right
                others_in_position = sum(c.in_position for c in [flu, blu, bru])

                if others_in_position == 3:
                    assert False, "All corners in position after UR' — no parity"
                assert others_in_position == 1, (
                    f"Expected 1 in position after UR', got {others_in_position}"
                )

        assert others_in_position == 1, (
            f"Expected exactly 1 of FLU/BLU/BRU in position, got {others_in_position}"
        )

        # Now exactly 2 corners in position (FRU + one other), 2 out of position
        out_of_position: list[Corner] = [c for c in [flu, blu, bru] if not c.in_position]
        assert len(out_of_position) == 2

        c1, c2 = out_of_position

        # Determine diagonal vs adjacent
        diagonal_pairs = [{flu, bru}]  # FRU is in position, so only FLU↔BRU is diagonal
        is_diagonal = {c1, c2} in diagonal_pairs

        if is_diagonal:
            self._fix_diagonal(c1, c2, yf)
        else:
            self._fix_adjacent(c1, c2, yf)

        # Verify all corners are now in position
        from cube.domain.model import Part
        assert Part.all_in_position(yf.corners), "Not all corners in position after advanced swap"
        return True

    def _fix_diagonal(self, c1: Corner, c2: Corner, yf: "Face") -> None:
        """Swap two diagonal corners — edges return to original positions.

        Uses Gallet's 15-move diagonal corner swap generalized for NxN:
            Rw2 f2 U2 Fw2 U' Rw2 U2 Fw2 U Fw2 R2 U2 F2 Rw2 U

        Notation mapping for NxN (nh = n_slices // 2):
            Rw = R[1:nh+1]  — wide R half-cube
            Fw = F[1:nh+1]  — wide F half-cube
            f  = F[2:nh+1]  — inner F slices only
            R  = Algs.R     — outer R layer only
            F  = Algs.F     — outer F layer only
        """
        n_slices = self.cube.n_slices
        nh = n_slices // 2

        self.debug("Doing diagonal corner swap (advanced — edges preserved)")

        r_wide = Algs.R[1:nh + 1]    # Rw
        f_wide = Algs.F[1:nh + 1]    # Fw
        f_inner = Algs.F[2:nh + 1]   # f
        u2 = Algs.U * 2

        # Gallet's 15-move diagonal corner swap:
        # Rw2 f2 U2 Fw2 U' Rw2 U2 Fw2 U Fw2 R2 U2 F2 Rw2 U
        alg = Algs.alg(None,
                       r_wide * 2, f_inner * 2, u2,
                       f_wide * 2, Algs.U.prime,
                       r_wide * 2, u2,
                       f_wide * 2, Algs.U,
                       f_wide * 2, Algs.R * 2, u2,
                       Algs.F * 2, r_wide * 2, Algs.U,
                       )

        with self.ann.annotate(h1="Diagonal Corner Swap (edges preserved)"):
            self.op.play(alg)

    def _fix_adjacent(self, c1: Corner, c2: Corner, yf: "Face") -> None:
        """Swap two adjacent corners — edges return to original positions.

        Uses Mowla's 17-move adjacent corner swap generalized for NxN:
            z r2 U2 R' U2 R' U2 R x U2 Rw2 U2 B2 L U2 L' U2 Rw2 U2 z' y'

        The algorithm swaps FRU ↔ BRU (right-side adjacent pair).
        If the out-of-position pair is not on the right side, we rotate
        with Y to bring them there first.

        Notation mapping for NxN (nh = n_slices // 2):
            r  = R[2:nh+1]  — inner R slices only
            R  = Algs.R     — outer R layer only
            Rw = R[1:nh+1]  — wide R half-cube
        """
        n_slices = self.cube.n_slices
        nh = n_slices // 2

        self.debug("Doing adjacent corner swap (advanced — edges preserved)")

        # The algorithm swaps the two corners on the right side (FRU ↔ BRU).
        # We need to Y-rotate so the out-of-position pair is on the right.
        flu = yf.corner_bottom_left
        blu = yf.corner_top_left
        bru = yf.corner_top_right

        pair = {c1, c2}
        # FRU is always in position, so the adjacent out-of-position pairs are:
        #   FLU+BLU (left side) → Y2 to bring to right
        #   BLU+BRU (back side) → Y to bring to right
        if pair == {flu, blu}:
            setup_alg = Algs.Y * 2
        elif pair == {bru, blu}:
            setup_alg = Algs.Y
        else:
            assert False, f"Unexpected adjacent pair: {c1}, {c2}"

        if setup_alg.count() > 0:
            self.op.play(setup_alg)

        r_inner = Algs.R[2:nh + 1]   # r
        r_wide = Algs.R[1:nh + 1]    # Rw
        u2 = Algs.U * 2
        b2 = Algs.B * 2

        # Mowla's 17-move adjacent corner swap (swaps FRU ↔ BRU):
        # z r2 U2 R' U2 R' U2 R x U2 Rw2 U2 B2 L U2 L' U2 Rw2 U2 z' y'
        #
        # We avoid cube rotations (z, x, y) in the algorithm by translating
        # them into equivalent face moves. Instead, we use the raw face-move
        # form that achieves the same effect:
        alg = Algs.alg(None,
                       Algs.Z,
                       r_inner * 2, u2, Algs.R.prime, u2, Algs.R.prime, u2, Algs.R,
                       Algs.X,
                       u2, r_wide * 2, u2, b2, Algs.L, u2, Algs.L.prime, u2,
                       r_wide * 2, u2,
                       Algs.Z.prime, Algs.Y.prime,
                       )

        with self.ann.annotate(h1="Adjacent Corner Swap (edges preserved)"):
            self.op.play(alg)
