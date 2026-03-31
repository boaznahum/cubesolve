"""Layer 3 permutation solver for 2x2 beginner method.

Permutes the 4 top-layer corners into their correct positions.
Orientation is ignored — L3Orient runs after this step.

IMPORTANT — No face colors:
    Like all 2x2 solvers, this works entirely with corner sticker colors.
    Never accesses Face.color, self.white_face, match_faces, in_position,
    or any API that reads face colors from centers.

Strategy (only uses the 3-cycle + U moves):
A) U-rotate until FRU is in position (always exactly one such rotation).
B) Apply 3-cycle (fixes FRU, cycles FLU/BRU/BLU) until BRU is in position.
   At most 2 applications.
C) Now either all 4 are in position (done) or FLU↔BLU are swapped.
   To break the swap: 3-cycle, U2, 3-cycle — then restart from A.
"""

from __future__ import annotations

from cube.domain.algs import Algs, Alg
from cube.domain.model import Color, Corner
from cube.domain.model.Face import Face
from cube.domain.solver._2x2_beginner._l3_utils import find_yellow_color, find_white_face, bring_white_to_down
from cube.domain.solver.AnnWhat import AnnWhat
from cube.domain.solver.common.SolverHelper import StepSolver
from cube.domain.solver.protocols import SolverElementsProvider


class L3Permute(StepSolver):
    """Last layer corner permutation solver for 2x2.

    Works purely with corner sticker colors — no face colors.
    """

    __slots__: list[str] = ["_swap_detected", "_advance_swap"]


    # R' F R' B2
    # R F' R' B2
    # R2 U' — adjacent corner swap
    # https://cdn.prod.website-files.com/6595ca03bcd68f311fd41872/65afebcae0a3534d92a9b921_Rubiks_SolutionGuide_2x2-Mini.pdf
    # and simpler in my drive
    _ADVANCED_SWAP: Alg = Algs.parse("""
                                        R' F R' B2
                                        R F' R' B2
                                        R2 U'

                                        """)

    def __init__(self, slv: SolverElementsProvider) -> None:
        super().__init__(slv, "L3Permute")
        self._advance_swap = False
        self._swap_detected: bool = False

    @property
    def swap_detected(self) -> bool:
        """Whether a FLU↔BLU corner swap was detected during the last solve."""
        return self._swap_detected

    @property
    def is_solved(self) -> bool:
        """Check using default white color."""
        return self.is_solved_with(self.cmn.white)

    def is_solved_with(self, white_color: Color) -> bool:
        """Check if all 4 top-layer corners are in correct positions.

        Ignores orientation — only checks that each top corner's
        non-yellow colors match the bottom corner below it.
        Uses query mode so no moves are visible.
        """
        yellow_color: Color = find_yellow_color(self.cube, white_color)

        white_face: Face | None = find_white_face(self.cube, white_color)
        if white_face is None:
            return False

        yellow_face: Face = white_face.opposite

        return self._is_u_aligned(yellow_face, white_face, white_color, yellow_color) >= 0

    def solve(self, white_color: Color | None = None) -> None:
        """Permute last-layer corners into correct positions."""
        self._swap_detected = False
        wc: Color = white_color or self.cmn.white
        if self.is_solved_with(wc):
            self._align_u_layer(wc)
            return

        with self._logger.tab("Doing L3 Permute"):
            with self.ann.annotate(h1="Doing L3 Permute"):
                self._solve(wc)

    def _align_u_layer(self, white_color: Color) -> None:
        """Align top layer with bottom using U rotations."""
        yellow_color: Color = find_yellow_color(self.cube, white_color)
        white_face: Face | None = find_white_face(self.cube, white_color)

        assert white_face is not None  # we must reach here after L1 is solved

        yellow_face: Face = white_face.opposite
        self._try_u_alignment(yellow_face, white_face, white_color, yellow_color)

    def _solve(self, white_color: Color) -> None:
        yellow_color: Color = find_yellow_color(self.cube, white_color)

        bring_white_to_down(self, white_color)

        up: Face = self.cube.up
        down: Face = self.cube.down

        self._do_permute(up, down, white_color, yellow_color)

    def _do_permute(self, up: Face, down: Face, white_color: Color,
                    yellow_color: Color) -> None:
        """Place all 4 top-layer corners using the 3-cycle + U moves.

        Algorithm:
        A) U-rotate until FRU is in position.
        B) Apply 3-cycle until BRU is in position (max 2).
        C) If FLU↔BLU still swapped: 3-cycle, U2, 3-cycle → restart from A.
        """

        #U R U' L' U R' U' L — 3-corner cycle, fixes FRU, cycles FLU/BRU/BLU
        c3c = self.cmn.top_3_corner_cycle

        for attempt in range(3):
            # Step A: U-rotate until FRU is in position
            self._bring_fru_to_position(up, down, white_color, yellow_color)

            # Step B: Cycle until BRU is in position (max 2 applications)
            with self.ann.annotate(
                    (up.corner_top_right, AnnWhat.Moved),
                    (up.corner_top_left, AnnWhat.Moved),
                    (up.corner_bottom_left, AnnWhat.Moved),
                    h2="Cycling corners",
            ):
                for _ in range(2):
                    if self._corner_in_position(up.corner_top_right, down.corner_bottom_right,
                                                white_color, yellow_color):
                        break
                    self.op.play(c3c)

            assert self._corner_in_position(up.corner_top_right, down.corner_bottom_right,
                                            white_color, yellow_color), \
                "BRU not in position after cycling"

            # Step C: Check if all in position

            # Now all in position, or FLU and BLU swapped
            if self._all_in_position(up, down, white_color, yellow_color):
                self._logger.debug_lazy(lambda: f"solved on iteration {attempt + 1}")
                return  # done!

            # FLU↔BLU are swapped — break the swap with cycle, U2, cycle
            self._swap_detected = True

            self._logger.debug_lazy(lambda: f"FLU↔BLU corner swap detected on iteration {attempt + 1}")

            if self._advance_swap:

                self._logger.debug_lazy(lambda: f"FLU↔BLU swap on iteration {attempt + 1}, "
                           f"fixing with advanced algorithm")

                # Step 3: If FRU and BRU are swapped, do U' swap U to bring them to front
                # the algorithm swap FRU<-->BRU
                if not self._all_in_position(up, down, white_color, yellow_color):
                    with self.ann.annotate(
                            (up.corner_bottom_right, AnnWhat.Moved),
                            (up.corner_top_right, AnnWhat.Moved),
                            h2="Advanced swapping corners",
                    ):
                        self.op.play(Algs.U.prime)
                        self.op.play(self._ADVANCED_SWAP)
                        self.op.play(Algs.U)

                # Step 4: U-align
                assert self._try_u_alignment(up, down, white_color, yellow_color), (
                    "L3 Permute failed"
                )
            else:

                self._logger.debug_lazy(lambda: f"FLU↔BLU swap on iteration {attempt + 1}, "
                           f"fixing with 3-cycle U2 3-cycle")
                with self.ann.annotate(
                        (up.corner_bottom_left, AnnWhat.Moved),
                        (up.corner_top_left, AnnWhat.Moved),
                        h2="Simple swapping corners",
                ):
                    self.op.play(c3c)
                    self.op.play((Algs.U * 2).simplify())
                    self.op.play(c3c)

            self._logger.debug("retrying from step A")

        raise AssertionError("L3 Permute failed after 3 attempts")

    def _bring_fru_to_position(self, up: Face, down: Face,
                               white_color: Color, yellow_color: Color) -> None:
        """U-rotate until FRU corner matches the bottom corner below it."""
        for _ in range(4):
            if self._corner_in_position(up.corner_bottom_right, down.corner_top_right,
                                        white_color, yellow_color):
                return
            self.op.play(Algs.U)

        raise AssertionError("No U rotation puts FRU in position")

    def _is_u_aligned(self, up: Face, down: Face,
                      white_color: Color, yellow_color: Color) -> int:
        """Check if any U rotation aligns top with bottom. No moves made.

        :return >= 0 if is aligned the number o required rotations to align
        """

        n = 0
        with self.op.with_query_restore_state():
            for _ in range(4):
                if self._all_in_position(up, down, white_color, yellow_color):
                    return n
                self.op.play(Algs.U)
                n += 1

            return -1

    def _try_u_alignment(self, up: Face, down: Face,
                         white_color: Color, yellow_color: Color) -> bool:
        """Apply U rotations to align top layer with bottom. Returns True if aligned."""

        # After 4 U rotations we're back to the original state
        n = self._is_u_aligned(up, down, white_color, yellow_color)
        if n < 0:
            return False
        else:
            self.op.play( (Algs.U * n).simplify())
            return True


    def _corner_in_position(self, top_corner: Corner, bottom_corner: Corner,
                            white_color: Color, yellow_color: Color) -> bool:
        """Check if a single top corner matches the bottom corner below it."""
        tc_colors: frozenset[Color] = top_corner.colors_id - {yellow_color}
        bc_colors: frozenset[Color] = bottom_corner.colors_id - {white_color}
        return tc_colors == bc_colors

    def _all_in_position(
        self, up: Face, down: Face,
        white_color: Color, yellow_color: Color,
    ) -> bool:
        """Check if all 4 top corners match their bottom counterparts."""
        pairs = [
            (up.corner_bottom_right, down.corner_top_right),   # FRU / FRD
            (up.corner_bottom_left, down.corner_top_left),     # FLU / FLD
            (up.corner_top_right, down.corner_bottom_right),   # BRU / BRD
            (up.corner_top_left, down.corner_bottom_left),     # BLU / BLD
        ]
        return all(
            self._corner_in_position(tc, bc, white_color, yellow_color)
            for tc, bc in pairs
        )
