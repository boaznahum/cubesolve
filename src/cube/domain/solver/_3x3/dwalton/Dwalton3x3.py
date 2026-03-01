"""
Dwalton-style table-based 3x3 solver — Kociemba two-phase algorithm.

Inspired by dwalton76/rubiks-cube-NxNxN-solver which uses precomputed
lookup/pruning tables with IDA* search to solve Rubik's cubes.

This is a pure Python implementation — no external binaries or libraries.
Tables are computed once on first use (~5-15 seconds) and cached in memory.

Credit: Algorithm approach inspired by Daniel Walton's rubiks-cube-NxNxN-solver
(https://github.com/dwalton76/rubiks-cube-NxNxN-solver) and Herbert Kociemba's
two-phase algorithm (http://kociemba.org/cube.htm).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.algs._parser import parse_alg
from cube.domain.exceptions.InternalSWError import InternalSWError
from cube.domain.model.Color import Color
from cube.domain.model.FaceName import FaceName
from cube.domain.solver._3x3.dwalton import search
from cube.domain.solver.common.AbstractSolver import AbstractSolver
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.Solver3x3Protocol import Solver3x3Protocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face
    from cube.utils.logger_protocol import ILogger

# Face order for the 54-char Kociemba string: U R F D L B
_FACE_ORDER: list[FaceName] = [
    FaceName.U, FaceName.R, FaceName.F,
    FaceName.D, FaceName.L, FaceName.B,
]

# URFDLB facelet layout (each face 9 facelets, row-major):
#              0  1  2
#              3  4  5
#              6  7  8
#
# 36 37 38   18 19 20    9 10 11   45 46 47
# 39 40 41   21 22 23   12 13 14   48 49 50
# 42 43 44   24 25 26   15 16 17   51 52 53
#
#             27 28 29
#             30 31 32
#             33 34 35

# Corner facelets: (U/D facelet, side1, side2)
# Order: URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB (matches cubie_defs)
_CORNER_FACELETS: list[tuple[int, int, int]] = [
    (8, 9, 20),    # URF
    (6, 18, 38),   # UFL
    (0, 36, 47),   # ULB
    (2, 45, 11),   # UBR
    (29, 26, 15),  # DFR
    (27, 44, 24),  # DLF
    (33, 53, 42),  # DBL
    (35, 17, 51),  # DRB
]

# Edge facelets: (primary, secondary)
# Order: UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR (matches cubie_defs)
_EDGE_FACELETS: list[tuple[int, int]] = [
    (5, 10),    # UR: U5, R1
    (7, 19),    # UF: U7, F1
    (3, 37),    # UL: U3, L1
    (1, 46),    # UB: U1, B1
    (32, 16),   # DR: D5, R7
    (28, 25),   # DF: D1, F7
    (30, 43),   # DL: D3, L7
    (34, 52),   # DB: D7, B7
    (23, 12),   # FR: F5, R3
    (21, 41),   # FL: F3, L5
    (50, 39),   # BL: B5, L3
    (48, 14),   # BR: B3, R5
]


class Dwalton3x3(AbstractSolver, Solver3x3Protocol):
    """
    Pure Python 3x3 solver using Kociemba two-phase algorithm with lookup tables.

    Inspired by dwalton76/rubiks-cube-NxNxN-solver's table-based approach.
    Tables are computed once on first use (~5-15 seconds).
    Finds solutions of ~20-25 moves.

    Credit: Daniel Walton (dwalton76/rubiks-cube-NxNxN-solver)
    and Herbert Kociemba (kociemba.org).
    """

    __slots__ = ["_op", "_debug_override"]

    def __init__(
        self,
        op: OperatorProtocol,
        parent_logger: "ILogger",
    ) -> None:
        super().__init__(op, parent_logger, logger_prefix="Dwalton3x3")
        self._op = op
        self._debug_override: bool | None = None

    @property
    def get_code(self) -> SolverName:
        return SolverName.DWALTON

    @property
    def status_3x3(self) -> str:
        if self._cube.solved:
            return "Solved"
        return "Unsolved (Dwalton)"

    @property
    def status(self) -> str:
        return self.status_3x3

    @property
    def can_detect_parity(self) -> bool:
        return False

    def solve_3x3(
        self,
        debug: bool = False,
        what: SolveStep | None = None,
    ) -> SolverResults:
        sr = SolverResults()

        if self._cube.solved:
            return sr

        _d = self._debug_override
        try:
            self._debug_override = debug

            # Convert cube to Kociemba facelet string
            facelet_str = self._cube_to_kociemba_string(self._cube)
            if debug:
                self.debug("Facelet string:", facelet_str)

            # Extract cubie state
            cp, co, ep, eo = self._facelets_to_cubies(facelet_str)
            if debug:
                self.debug("CP:", cp, "CO:", co)
                self.debug("EP:", ep, "EO:", eo)

            # Search using cubie arrays
            solution = search.solve(cp, co, ep, eo)

            if solution is None:
                raise InternalSWError("Dwalton solver: no solution found")

            if debug:
                self.debug("Solution:", " ".join(solution))
                self.debug("Move count:", len(solution))

            # Execute solution
            if solution:
                alg = parse_alg(" ".join(solution))
                self._op.play(alg)

        finally:
            self._debug_override = _d

        return sr

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        return self.solve_3x3(self._is_debug_enabled, what)

    def supported_steps(self) -> list[SolveStep]:
        return []

    def _cube_to_kociemba_string(self, cube: Cube) -> str:
        """Convert cube to 54-char URFDLB string using dynamic color mapping."""
        color_to_face: dict[Color, str] = {}
        for face_name in _FACE_ORDER:
            face = cube.face(face_name)
            center_color = face.center.color
            color_to_face[center_color] = face_name.name

        result: list[str] = []
        for face_name in _FACE_ORDER:
            face = cube.face(face_name)
            result.append(self._face_to_string(face, color_to_face))

        return "".join(result)

    @staticmethod
    def _face_to_string(face: Face, color_to_face: dict[Color, str]) -> str:
        """Convert a face to 9 Kociemba chars (row by row, left to right)."""
        colors: list[Color] = []
        colors.append(face.corner_top_left.get_face_edge(face).color)
        colors.append(face.edge_top.get_face_edge(face).color)
        colors.append(face.corner_top_right.get_face_edge(face).color)
        colors.append(face.edge_left.get_face_edge(face).color)
        colors.append(face.center.color)
        colors.append(face.edge_right.get_face_edge(face).color)
        colors.append(face.corner_bottom_left.get_face_edge(face).color)
        colors.append(face.edge_bottom.get_face_edge(face).color)
        colors.append(face.corner_bottom_right.get_face_edge(face).color)
        return "".join(color_to_face[c] for c in colors)

    def _facelets_to_cubies(
        self, s: str
    ) -> tuple[list[int], list[int], list[int], list[int]]:
        """Convert 54-char facelet string to cubie arrays.

        Returns (corner_perm, corner_orient, edge_perm, edge_orient).
        """
        cp = [0] * 8
        co = [0] * 8
        ep = [0] * 12
        eo = [0] * 12

        face_map = {"U": 0, "R": 1, "F": 2, "D": 3, "L": 4, "B": 5}

        # Corners
        for i, (f1, f2, f3) in enumerate(_CORNER_FACELETS):
            colors = (face_map[s[f1]], face_map[s[f2]], face_map[s[f3]])

            found = False
            for j, (g1, g2, g3) in enumerate(_CORNER_FACELETS):
                solved = (g1 // 9, g2 // 9, g3 // 9)

                if colors == solved:
                    cp[i], co[i], found = j, 0, True
                    break
                elif colors == (solved[1], solved[2], solved[0]):
                    # U/D ref sticker (solved[0]) at position 2 → twist 2
                    cp[i], co[i], found = j, 2, True
                    break
                elif colors == (solved[2], solved[0], solved[1]):
                    # U/D ref sticker (solved[0]) at position 1 → twist 1
                    cp[i], co[i], found = j, 1, True
                    break

            if not found:
                raise InternalSWError(
                    f"Dwalton: Cannot identify corner at position {i}, "
                    f"facelets=({s[f1]},{s[f2]},{s[f3]})"
                )

        # Edges
        for i, (f1, f2) in enumerate(_EDGE_FACELETS):
            colors = (face_map[s[f1]], face_map[s[f2]])

            found = False
            for j, (g1, g2) in enumerate(_EDGE_FACELETS):
                solved = (g1 // 9, g2 // 9)

                if colors == solved:
                    ep[i], eo[i], found = j, 0, True
                    break
                elif colors == (solved[1], solved[0]):
                    ep[i], eo[i], found = j, 1, True
                    break

            if not found:
                raise InternalSWError(
                    f"Dwalton: Cannot identify edge at position {i}, "
                    f"facelets=({s[f1]},{s[f2]})"
                )

        return cp, co, ep, eo
