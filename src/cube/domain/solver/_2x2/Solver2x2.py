"""2x2 Rubik's Cube Solver — IDA* Optimal Method.

Uses precomputed pruning tables and IDA* search to find optimal solutions
(≤11 moves HTM). The state space is only 3,674,160 positions.

We fix the DBL corner and only use U, R, F moves (9 total).
Two coordinates encode the full state: twist (orientation) and permutation.

Before solving, the cube is oriented so the original DBL piece is at
position 7 (back-down-left) with correct orientation (co=0). This is
needed because D/L/B moves on a 2x2 displace the DBL corner, but the
IDA* solver only uses U/R/F.

After solving, the virtual center pieces (which exist in the domain model
even on a 2x2) are reset to match the original face colors, since whole-cube
rotations during pre-orientation may have displaced them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.algs import Alg, Algs
from cube.domain.solver._2x2.cube_to_coordinates import cube_to_coords
from cube.domain.solver._2x2.ida_star_search import solve as ida_solve
from cube.domain.solver._2x2.ida_star_tables import get_tables
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.domain.model.Corner import Corner
    from cube.domain.model.Cube import Cube
    from cube.utils.logger_protocol import ILogger

# Move index → Alg mapping.
# Indices 0–8: U, U2, U', R, R2, R', F, F2, F'
_MOVE_TO_ALG: list[Alg] = [
    Algs.U, Algs.U * 2, Algs.U.prime,
    Algs.R, Algs.R * 2, Algs.R.prime,
    Algs.F, Algs.F * 2, Algs.F.prime,
]

# Pre-orientation table: (slot, co) → rotation sequence.
# For each possible position and orientation of the original DBL piece,
# gives the whole-cube rotations needed to bring it to slot 7 with co=0.
# There are 8 slots × 3 orientations = 24 entries, matching the 24
# possible cube orientations.
_ORIENT_TABLE: dict[tuple[int, int], list[Alg]] = {
    (0, 0): [Algs.Y, Algs.X * 2],
    (0, 1): [Algs.Y * 2, Algs.Z.prime],
    (0, 2): [Algs.Y * 2, Algs.X],
    (1, 0): [Algs.X * 2],
    (1, 1): [Algs.Y, Algs.Z.prime],
    (1, 2): [Algs.Y, Algs.X],
    (2, 0): [Algs.Y.prime, Algs.X * 2],
    (2, 1): [Algs.Z.prime],
    (2, 2): [Algs.X],
    (3, 0): [Algs.Y * 2, Algs.X * 2],
    (3, 1): [Algs.Y.prime, Algs.Z.prime],
    (3, 2): [Algs.Y.prime, Algs.X],
    (4, 0): [Algs.Y * 2],
    (4, 1): [Algs.Y.prime, Algs.Z],
    (4, 2): [Algs.Y, Algs.X.prime],
    (5, 0): [Algs.Y],
    (5, 1): [Algs.Y * 2, Algs.Z],
    (5, 2): [Algs.X.prime],
    (6, 0): [Algs.Y.prime],
    (6, 1): [Algs.Z],
    (6, 2): [Algs.Y * 2, Algs.X.prime],
    (7, 0): [],
    (7, 1): [Algs.Y, Algs.Z],
    (7, 2): [Algs.Y.prime, Algs.X.prime],
}


def _find_dbl_piece_slot_and_co(cube: Cube) -> tuple[int, int]:
    """Find the slot and orientation of the original DBL piece.

    Returns:
        (slot, co) where slot is 0-7 and co is 0-2.
    """
    corners: list[Corner] = [
        cube.fru, cube.flu, cube.blu, cube.bru,
        cube.frd, cube.fld, cube.brd, cube.bld,
    ]

    # Home colors of the DBL slot (the original face colors at back-down-left)
    dbl_home_colors: frozenset[object] = frozenset(
        e.face.original_color for e in cube.bld._slice.edges
    )

    # Twist face pairs for each slot: (CW_face, CCW_face)
    twist_faces: list[tuple[object, object]] = [
        (cube.right, cube.front),   # URF
        (cube.front, cube.left),    # UFL
        (cube.left, cube.back),     # ULB
        (cube.back, cube.right),    # UBR
        (cube.front, cube.right),   # DFR
        (cube.left, cube.front),    # DLF
        (cube.right, cube.back),    # DRB
        (cube.back, cube.left),     # DBL
    ]

    up_color: object = cube.up.original_color
    down_color: object = cube.down.original_color

    for i, corner in enumerate(corners):
        piece_colors: frozenset[object] = frozenset(
            e.color for e in corner._slice.edges
        )
        if piece_colors != dbl_home_colors:
            continue

        # Found the DBL piece at slot i. Determine its orientation.
        for e in corner._slice.edges:
            if e.color == up_color or e.color == down_color:
                if e.face is cube.up or e.face is cube.down:
                    return i, 0
                t1, _t2 = twist_faces[i]
                if e.face is t1:
                    return i, 1
                return i, 2

    raise AssertionError("DBL piece not found in any slot")


class Solver2x2(BaseSolver):
    """Optimal 2x2 cube solver using IDA* with precomputed pruning tables.

    Finds solutions of ≤11 moves (God's number for 2x2).
    Tables are loaded from pre-computed data (~100ms), then cached.
    Subsequent solves complete in sub-millisecond time.
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
        return "Unsolved"

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        _ = what  # All steps do a full optimal solve (only ~9 moves)
        sr = SolverResults()

        if self._cube.solved:
            return sr

        self._solve_optimal()

        return sr

    def supported_steps(self) -> list[SolveStep]:
        return [SolveStep.L1, SolveStep.L3]

    def _orient_dbl(self) -> None:
        """Orient the cube so the original DBL piece is at slot 7 with co=0.

        The IDA* solver only uses U, R, F moves which keep DBL fixed.
        If D/L/B moves were used during scrambling, the DBL piece may
        have been displaced or twisted. This method applies whole-cube
        rotations to restore it (both position and orientation) before solving.
        """
        slot, co = _find_dbl_piece_slot_and_co(self._cube)
        if slot == 7 and co == 0:
            return  # Already in place with correct orientation

        self.debug(f"DBL piece at slot {slot} co={co}, rotating to fix")
        for alg in _ORIENT_TABLE[(slot, co)]:
            self.op.play(alg)

    @staticmethod
    def _fix_centers(cube: Cube) -> None:
        """Reset virtual center pieces to match original face colors.

        On a 2x2, the domain model has virtual center pieces that move with
        whole-cube rotations but not with face moves. After pre-orientation
        (whole-cube rotations) and solving (face moves only), the centers
        may be displaced while corners are correct. This resets them.
        """
        for face in cube.faces:
            face.center._virtual_color = face.original_color  # type: ignore[attr-defined]

    def _solve_optimal(self) -> None:
        """Solve the 2x2 cube optimally using IDA*."""
        # Orient cube so DBL piece is at position 7 with co=0 (required by IDA*)
        self._orient_dbl()

        # Extract coordinates from the physical cube
        perm, twist = cube_to_coords(self._cube)

        # Get precomputed tables (built lazily on first call)
        tables = get_tables()

        # IDA* search returns a list of move indices
        solution: list[int] = ida_solve(perm, twist, tables)

        self.debug(f"IDA* solution: {len(solution)} moves")
        assert len(solution) <= 11, f"IDA* returned {len(solution)} moves (max is 11)"

        # Play each move on the physical cube
        for move_idx in solution:
            self.op.play(_MOVE_TO_ALG[move_idx])

        # Fix virtual center pieces that were displaced by pre-orientation
        self._fix_centers(self._cube)
