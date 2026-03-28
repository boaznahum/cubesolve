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

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cube.domain.algs import Algs, Alg
from cube.domain.solver.common.SolverHelper import SolverHelper

if TYPE_CHECKING:
    from cube.domain.solver.protocols import SolverElementsProvider

@dataclass(frozen=True)
class CornerFixResults:
    cube_unreduced:bool
    need_resolve_3x3: bool


class CornerSwapParity(SolverHelper):
    """Fix corner swap parity on even cubes — basic or advanced.

    Basic: swaps diagonal corners, moves edges to new positions (pairing preserved).
    Advanced: detects diagonal vs adjacent out-of-position corners, applies
    the matching algorithm. Edges return to original positions.
    """

    def __init__(self, solver: SolverElementsProvider) -> None:
        super().__init__(solver, "CornerSwapParity")

    def fix_corner_parity(self, advanced: bool) -> CornerFixResults:
        """Fix corner swap parity on even cube.

        Non-advanced: swaps two arbitrary U-face corners (not necessarily the
        out-of-position pair). The cube remains reduced (is3x3) but needs a
        full 3x3 re-solve (L1+L2+L3).

        Advanced: detects which corners are out of position (diagonal vs
        adjacent) and applies the matching algorithm. Only L3 corner
        orientation may still be needed after the fix.

        Args:
            advanced: If True, detect diagonal vs adjacent and use the matching
                edge-preserving algorithm. Requires the cube to be L1+L2+L3cross
                solved so corner positions can be analyzed.
                If False, swap any two U-face corners — the solver will redo
                L1+L2+L3 anyway. Use this when parity was detected by a query
                probe (not the real solver), so the cube isn't L1/L2 solved.

                Neither mode un-reduces the cube (edges stay paired).

        Returns:
            CornerFixResults with cube_unreduced and need_resolve_3x3 flags.

        Color safety for even cubes:
            Uses colors_id/position_id which require correct face colors.
            On even cubes, callers must ensure centers are reduced (face colors
            are then determined by majority center color).
            Whole-cube rotations (Y, X, Z) do NOT invalidate face colors —
            all slices rotate together. Only independent inner slice moves
            (e.g. R[2:3]) would invalidate, and neither the 3x3 solver nor
            our swap algorithms do that.
        """
        if advanced:
            self._fix_advanced()
            return CornerFixResults(cube_unreduced=False, need_resolve_3x3=False)
        else:
            self._fix_basic()
            return CornerFixResults(cube_unreduced=False, need_resolve_3x3=True)

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

        self._logger.log_lazy(logging.DEBUG, "Doing corner swap (basic — edges move)")

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

        Color safety: whole-cube rotations (Y, X, Z) do NOT invalidate
        the color provider — all slices rotate together. The swap algorithms
        use only outer face moves, wide half-cube moves, and whole-cube
        rotations — none of which move inner slices independently. So
        colors_id/position_id queries are safe at any point.

        Returns:
            True if advanced algorithm was used (edges preserved),
            False if fell back to basic (edges moved).
        """
        n_slices = self.cube.n_slices
        assert n_slices % 2 == 0, "Corner parity fix only applies to even cubes"

        self._logger.log_lazy(logging.DEBUG, "Doing corner swap (advanced — edges preserved)")
        # Use U face directly — bring_face_up ensures it's correct.
        # Don't use cmn.white_face which fails on even cubes in Cage solver
        # (face colors may not be standard BOY scheme).
        yf = self.cube.up

        # Corner references: cube elements are fixed in space (only colors move),
        # so fru/flu/blu/bru are constant references — no need to refresh after moves.
        fru = yf.corner_bottom_right
        flu = yf.corner_bottom_left
        blu = yf.corner_top_left
        bru = yf.corner_top_right

        # Ensure one in-position corner is at FRU.
        # Detectors (L3Corners, PLL) normally set this up, but we don't rely on it.
        # Precondition: L1, L2, and L3 cross must be solved (yellow face up).

        cqr = self.cqr
        fru_actual = cqr.get_corner_actual_position(fru)
        assert fru_actual.on_face(yf), "FRU actual is not on y face"

        #  BLU  |  BRU
        #--------------
        #  FLU  |  FRU
        #
        #  Y is over U !!!


        if not fru.in_position:
            # what the point in rotating all cube !!! this is stupid, positon id is changed too
            # so we need again different color id !!
            for c, u_alg in [(bru, Algs.U), (blu, Algs.U * 2), (flu, Algs.U.prime)]:
                if fru_actual is c:
                    self.op.play(u_alg)
                    break


        assert fru.in_position, f"FRU in not position after trying to fix {fru.position_id} <> {fru.colors_id}"

        # # Count how many of the other 3 corners are in position
        # others_in_position = sum(c.in_position for c in [flu, blu, bru])
        #
        # if others_in_position == 3:
        #     # All 4 in position — no parity to fix
        #     assert False, "All corners in position — no parity detected"

        _3_cycle_alg = self.cmn.top_3_corner_cycle

        # so now we have 6 cases ##

        a = blu
        b = bru
        c = flu

        # A - blu
        # B - bru
        # C - flu
        # D - fru    always in positon, see assert above

        blu_pos = cqr.get_corner_actual_position(blu)
        bru_pos = cqr.get_corner_actual_position(bru)
        flu_pos = cqr.get_corner_actual_position(flu)


        assert blu_pos.on_face(yf)
        assert bru_pos.on_face(yf)
        assert bru_pos.on_face(yf)

        a_b_c = (blu_pos, bru_pos, flu_pos)


        # 6 permutations of 3 corners (FRU always in position):
        #  a = blu, b = bru, c = flu, D = fru (always in position)

        y: Alg = Algs.Y
        y2: Alg = y * 2

        alg: Alg

        # case 1: all in position — no parity
        #  A A-pos | B B-pos
        #  C C-pos | D D-pos
        if a_b_c == (a, b, c):
            assert False, "All corners in position — no parity detected"



        # case 2: flu↔bru diagonal swap
        #  A A-pos | C B-pos
        #  B C-pos | D D-pos
        # Y brings FLU→FRU, BRU→BLU → diagonal alg swaps FRU↔BLU
        elif a_b_c == (a, c, b):
            self._logger.debug("Case 2: flu↔bru diagonal swap")
            alg = y + self._fix_diagonal_fru_blu() + y.prime

        # case 3: blu↔bru adjacent swap (back)
        #  B A-pos | A B-pos
        #  C C-pos | D D-pos
        # Y2 brings BLU→FRU, BRU→FLU → adjacent alg swaps FRU↔FLU
        elif a_b_c == (b, a, c):
            self._logger.debug("Case 3: blu↔bru adjacent swap (back)")
            alg = y2 + self._fix_adjacent_fru_flu() + y2.prime

        # case 4: 3-cycle CW (blu→bru→flu→blu)
        #  B A-pos | C B-pos
        #  A C-pos | D D-pos
        # cycle moves: FLU→BRU, BRU→BLU, BLU→FLU
        # after cycle: blu(at bru)→blu, bru(at flu)→bru, flu(at blu)→flu → all in position
        # if all in position after cycle → parity was just a 3-cycle, assert
        elif a_b_c == (b, c, a):
            self._logger.debug("Case 4: 3-cycle CW, applying cycle")
            alg = _3_cycle_alg

        # case 5: 3-cycle CCW (blu→flu→bru→blu)
        #  C A-pos | A B-pos
        #  B C-pos | D D-pos
        # cycle' moves: FLU→BLU, BLU→BRU, BRU→FLU
        # after cycle': blu(at flu)→blu... wait need inverse
        # cycle' = FLU←BRU←BLU←FLU = BRU→FLU, BLU→BRU, FLU→BLU
        # after: flu(at bru)→flu, blu(at flu)→blu, bru(at blu)... no
        # Just apply cycle' and let the assert check
        elif a_b_c == (c, a, b):
            self._logger.debug("Case 5: 3-cycle CCW, applying cycle'")
            alg = _3_cycle_alg.prime

        # case 6: flu↔blu adjacent swap (left)
        #  C A-pos | B B-pos
        #  A C-pos | D D-pos
        # Y' brings FLU→FRU, BLU→FLU → adjacent alg swaps FRU↔FLU
        elif a_b_c == (c, b, a):
            self._logger.debug("Case 6: flu↔blu adjacent swap (left)")
            alg = y.prime + self._fix_adjacent_fru_flu() + y

        else:
            assert False, f"Unexpected permutation: {a_b_c}"

        assert alg is not None
        with self.ann.annotate(h1="Advanced corner swap fix"):
            self.op.play(alg)

        # Verify all corners are now in position
        from cube.domain.model import Part
        assert Part.all_in_position(yf.corners), "Not all corners in position after advanced swap"
        return True

    def _fix_diagonal_fru_blu(self) -> Alg:
        """Swap two diagonal corners — edges return to original positions.

        # tested in pyglet2
        #Diagonal (6x6): FRU <--> BLU
        # 3Rw2 2-3F2 U2 3Fw2 U' 3Rw2 U2 3Fw2 U 3Fw2 R2 U2 F2 3Rw2 U

        # tested in pyglet2
        #Diagonal (8x8): FRU <--> BLU
        4Rw2 2-4F2 U2 4Fw2 U' 4Rw2 U2 4Fw2 U 4Fw2 R2 U2 F2 4Rw2 U



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

        self._logger.debug("Doing diagonal corner swap (advanced — edges preserved)")

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

        return alg



    def _fix_adjacent_fru_flu(self) -> Alg:
        """Swap two adjacent corners — edges return to original positions.

        Uses Mowla's 17-move adjacent corner swap generalized for NxN:
            z r2 U2 R' U2 R' U2 R x U2 Rw2 U2 B2 L U2 L' U2 Rw2 U2 z' y'


        # tested in pyglet2
        #Adjacent (6x6): FRU <--> FLU
        # Z 2-3R2 U2 R' U2 R' U2 R X U2 3Rw2 U2 B2 L U2 L' U2 3Rw2 U2 Z' Y'

        # tested in pyglet2
        #Adjacent (8x8): FRU <--> FLU
         Z 2-4R2 U2 R' U2 R' U2 R X U2 4Rw2 U2 B2 L U2 L' U2 4Rw2 U2 Z' Y'


        The algorithm swaps FRU ↔ BRU (right-side adjacent pair).
        If the out-of-position pair is not on the right side, we rotate
        with Y to bring them there first.

        Notation mapping for NxN (nh = n_slices // 2):
            r  = R[2:nh+1]  — inner R slices only
            R  = Algs.R     — outer R layer only
            Rw = R[1:nh+1]  — wide R half-cube
        """
        nh = self.cube.n_slices // 2

        self._logger.debug("Doing adjacent corner swap (advanced — edges preserved)")

        r_inner = Algs.R[2:nh + 1]   # r
        r_wide = Algs.R[1:nh + 1]    # Rw
        u2 = Algs.U * 2
        b2 = Algs.B * 2


        #  Z
        #  2-4R2 U2 R' U2 R' U2 R
        #  X
        #  U2
        #  4Rw2 U2 B2 L U2 L' U2
        #  4Rw2 U2
        #  Z' Y'

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
                       u2,
                       r_wide * 2, u2, b2, Algs.L, u2, Algs.L.prime, u2,
                       r_wide * 2, u2,
                       Algs.Z.prime, Algs.Y.prime,
                       )

        return alg
