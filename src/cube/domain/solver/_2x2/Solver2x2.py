"""
2x2 Rubik's Cube Solver — Beginner Layer-by-Layer Method.

A 2x2 cube has only 8 corner pieces (no edges, no centers).
The solving strategy is:
  1. Solve bottom layer (4 white corners)
  2. Position top layer corners
  3. Orient top layer corners

This reuses the same algorithmic ideas from the 3x3 beginner solver
but skips all cross/edge/center steps.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.algs import Alg, Algs
from cube.domain.model import Corner, Part, PartColorsID
from cube.domain.model.Face import Face
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.utils.logger_protocol import ILogger


class Solver2x2(BaseSolver):
    """
    Dedicated 2x2 cube solver using beginner corner-only method.

    Steps:
    1. L1 (bottom corners): Position and orient all 4 bottom corners
    2. L3 Corners Position: Permute top corners into correct slots
    3. L3 Corners Orient: Twist top corners so all stickers match
    """

    __slots__: list[str] = ["_display_as"]

    def __init__(
        self,
        op: OperatorProtocol,
        parent_logger: ILogger,
        display_as: SolverName | None = None,
    ) -> None:
        super().__init__(op, parent_logger, logger_prefix="Solver2x2")
        self._display_as: SolverName = display_as or SolverName.TWO_BY_TWO

    @property
    def get_code(self) -> SolverName:
        return self._display_as

    @property
    def status(self) -> str:
        if self._cube.solved:
            return "Solved"

        wf = self.cmn.white_face
        if Part.all_match_faces(wf.corners):
            return "L1, No L3"
        return "No L1"

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        sr = SolverResults()

        if self._cube.solved:
            return sr

        match what:
            case SolveStep.L1:
                self.cmn.bring_face_up(self.cmn.white_face)
                self._solve_bottom_corners()

            case SolveStep.ALL | SolveStep.L3:
                self._solve_2x2()

        return sr

    def supported_steps(self) -> list[SolveStep]:
        return [SolveStep.L1, SolveStep.L3]

    # =========================================================================
    # Core solving logic
    # =========================================================================

    def _solve_2x2(self) -> None:
        """Solve the 2x2 cube."""
        # Bring white face up for bottom-layer solving
        self.cmn.bring_face_up(self.cmn.white_face)

        # Step 1: Solve bottom layer (all 4 white corners)
        self._solve_bottom_corners()

        if self._cube.solved:
            return

        # Step 2: Bring yellow face up for top-layer solving
        self.cmn.bring_face_up(self.cmn.white_face.opposite)

        # Step 3: Position top corners
        self._position_top_corners()

        # Step 4: Orient top corners
        self._orient_top_corners()

    # =========================================================================
    # Bottom layer: Position and orient 4 white corners
    # =========================================================================

    def _solve_bottom_corners(self) -> None:
        """Solve all 4 bottom-layer corners (white face is up)."""
        wf: Face = self.cmn.white_face
        assert wf is self._cube.up

        color_codes = Part.parts_id_by_pos(wf.corners)

        for code in color_codes:
            self._solve_one_bottom_corner(code)

    def _solve_one_bottom_corner(self, corner_id: PartColorsID) -> None:
        """Place one bottom corner into its correct slot with correct orientation."""

        def sc() -> Corner:
            """Source corner: the corner piece with these colors."""
            return self._cube.find_corner_by_colors(corner_id)

        def tc() -> Corner:
            """Target corner: the slot where this corner belongs."""
            return self._cube.find_corner_by_pos_colors(corner_id)

        if sc().match_faces:
            return  # already solved

        wf: Face = self._cube.up

        # Bring target slot to front-right-up position
        self._bring_corner_to_front_right(wf, tc())

        # Get source corner into front-right-down (bottom layer working position)
        if sc().on_face(wf):
            self.debug(f"2x2 L1: source {sc()} on top → bring to bottom")
            self._top_corner_to_front_right_down(wf, sc())
        else:
            self.debug(f"2x2 L1: source {sc()} on bottom → bring to FRD")
            self._bottom_corner_to_front_right_down(sc())

        assert self._cube.front.corner_bottom_right is sc()

        # Now insert: corner is at FRD, target is at FRU
        # Check if white is on the down face
        if sc().f_color(wf.opposite) == wf.color:
            self.debug("2x2 L1: white on bottom, fixing...")
            self.op.play(Algs.R.prime + Algs.D.prime * 2 + Algs.R + Algs.D)
            assert sc().f_color(wf.opposite) != wf.color

        if sc().f_color(self._cube.front) == wf.color:
            self.op.play(Algs.D.prime + Algs.R.prime + Algs.D + Algs.R)
        else:
            self.op.play(Algs.D + Algs.F + Algs.D.prime + Algs.F.prime)

        assert sc().match_faces

    def _bring_corner_to_front_right(self, wf: Face, c: Corner) -> None:
        """Bring corner c on the top face to front-right-up position via Y rotation."""
        assert c.on_face(wf)

        if wf.corner_bottom_right is c:
            return
        if wf.corner_top_right is c:
            self.op.play(Algs.Y)
            return
        if wf.corner_top_left is c:
            self.op.play(Algs.Y * 2)
            return
        if wf.corner_bottom_left is c:
            self.op.play(Algs.Y.prime)
            return
        raise ValueError(f"{c} is not on {wf}")

    def _top_corner_to_front_right_down(self, wf: Face, c: Corner) -> None:
        """Move a top corner to front-right-down position (doesn't preserve top layer)."""
        assert c.on_face(wf)
        saved_id = c.colors_id

        if wf.corner_bottom_right is c:
            self.op.play(Algs.R.prime + Algs.D.prime + Algs.R)
        elif wf.corner_top_right is c:
            self.op.play(Algs.B.prime + Algs.D.prime + Algs.B)
        elif wf.corner_top_left is c:
            self.op.play(Algs.B + Algs.D.prime + Algs.B.prime)
        elif wf.corner_bottom_left is c:
            self.op.play(Algs.F.prime + Algs.D.prime + Algs.F)
        else:
            raise ValueError(f"{c} is not on {wf}")

        c = self._cube.find_corner_by_colors(saved_id)
        self._bottom_corner_to_front_right_down(c)

    def _bottom_corner_to_front_right_down(self, c: Corner) -> None:
        """Rotate D to bring bottom corner to front-right-down."""
        f: Face = self._cube.down
        assert c.on_face(f)

        if f.corner_top_right is c:
            pass  # already there
        elif f.corner_bottom_right is c:
            self.op.play(Algs.D.prime)
        elif f.corner_bottom_left is c:
            self.op.play(Algs.D * 2)
        elif f.corner_top_left is c:
            self.op.play(Algs.D)
        else:
            raise ValueError(f"{c} is not on {f}")

    # =========================================================================
    # Top layer: Position and orient 4 yellow corners
    # =========================================================================

    def _position_top_corners(self) -> None:
        """Permute top corners so each is in its correct slot (ignoring orientation).

        On a 2x2, the top layer permutation can be any element of S_4:
        - Identity: already solved
        - 4-cycle: solved by U rotations (1-3 quarter turns)
        - 3-cycle: solved by A-perm (1-2 applications with Y setup)
        - Double transposition: A-perm converts to 3-cycle, then solve
        - Transposition: U converts to 3-cycle, then solve

        The A-perm (U R U' L' U R' U' L) is a 3-cycle that fixes FRU
        and cycles BRU → BLU → FLU → BRU.
        """
        yf: Face = self._cube.up

        for _attempt in range(12):
            if Part.all_in_position(yf.corners):
                return

            # Try U rotations first — solves 4-cycles in 1-3 moves
            for _ in range(3):
                self.op.play(Algs.U)
                if Part.all_in_position(yf.corners):
                    return
            self.op.play(Algs.U)  # restore to original (4 U = identity)

            # Count corners currently in position
            in_pos = [c for c in yf.corners if c.in_position]
            n_in_pos = len(in_pos)

            if n_in_pos == 0:
                # Double transposition (not a 4-cycle since U didn't solve it).
                # A-perm converts it to a state with 1+ corners in position.
                self.op.play(self._ur_perm)
            elif n_in_pos == 1:
                # 3-cycle: bring the in-position corner to FRU (A-perm's
                # fixed point), then A-perm cycles the other 3.
                self._bring_corner_to_front_right(yf, in_pos[0])
                self.op.play(self._ur_perm)
            elif n_in_pos == 2:
                # Transposition: U converts the structure so that 0 or 1
                # corners are in position, breaking the transposition deadlock.
                self.op.play(Algs.U)
                # Don't apply A-perm yet — let the next iteration handle
                # the new structure (will be 0 or 1 in position).
            else:
                return  # 3 in position implies 4th is too

        assert Part.all_in_position(yf.corners), "Top corner permutation failed"

    def _orient_top_corners(self) -> None:
        """Orient top corners so all stickers match their face.

        Uses the classic R' D' R D algorithm applied to each corner in turn.
        This twists the FRU corner while temporarily disturbing the bottom layer.
        Over all 4 corners, the bottom layer disturbances cancel out (because
        the total corner twist is 0 mod 3 on a valid cube).
        """
        yf: Face = self._cube.up

        for _ in range(4):
            # Twist current front-right corner until its top sticker matches
            while not yf.corner_bottom_right.match_face(yf):
                self.op.play(Algs.alg(None, Algs.R.prime, Algs.D.prime, Algs.R, Algs.D) * 2)

            # Rotate U to bring next corner to front-right
            self.op.play(Algs.U.prime)

        # After orienting all 4 corners, the cube should be solved.
        # The 4 U' moves = identity, and the commutator twists cancel.
        assert self._cube.solved, "2x2 orient failed — cube not solved"

    @property
    def _ur_perm(self) -> Alg:
        """Corner permutation algorithm: U R U' L' U R' U' L."""
        return Algs.alg(None, Algs.U, Algs.R, Algs.U.prime, Algs.L.prime,
                        Algs.U, Algs.R.prime, Algs.U.prime, Algs.L)
