"""
Kociemba Near-Optimal Solver
============================

Uses Herbert Kociemba's two-phase algorithm to find near-optimal solutions
(typically 18-22 moves) for any 3x3 Rubik's cube position.

This solver wraps the `kociemba` Python package which provides:
- Sub-second solve times
- Solutions within 2-3 moves of optimal (God's Number = 20)
- Automatic pruning table generation on first use

Note: Only works for 3x3 cubes. For NxN cubes, falls back to beginner solver.


Kociemba String Format
======================

The kociemba library expects a 54-character string representing the cube state.

Cube Layout (Unfolded)
----------------------
::

            +-------+
            | U U U |
            | U U U |
            | U U U |
    +-------+-------+-------+-------+
    | L L L | F F F | R R R | B B B |
    | L L L | F F F | R R R | B B B |
    | L L L | F F F | R R R | B B B |
    +-------+-------+-------+-------+
            | D D D |
            | D D D |
            | D D D |
            +-------+

String Order: U R F D L B
-----------------------------
The 54-character string is built by reading faces in order: U, R, F, D, L, B.
Each face contributes 9 characters (positions 0-8, 9-17, 18-26, 27-35, 36-44, 45-53).

::

    String position:  0         9        18        27        36        45
                      |         |         |         |         |         |
                      v         v         v         v         v         v
    String:          [UUUUUUUUU|RRRRRRRRR|FFFFFFFFF|DDDDDDDDD|LLLLLLLLL|BBBBBBBBB]
                      └── U ───┘└── R ───┘└── F ───┘└── D ───┘└── L ───┘└── B ───┘


Facelet Reading Order (per face)
--------------------------------
Each face's 9 facelets are read left-to-right, top-to-bottom:

::

    Looking at a face:       Indices:        Example for U face:
    +-------+               +-------+        +-------+
    | 0 1 2 |               | 0 1 2 |        | 0 1 2 |  → string[0:3]
    | 3 4 5 |               | 3 4 5 |        | 3 4 5 |  → string[3:6]
    | 6 7 8 |               | 6 7 8 |        | 6 7 8 |  → string[6:9]
    +-------+               +-------+        +-------+

    Mapped to cube parts:
    +---------------------+
    | corner  edge corner |
    | edge   center edge  |
    | corner  edge corner |
    +---------------------+


Character Meaning
-----------------
Each character (U/R/F/D/L/B) indicates which face's CENTER COLOR that
facelet currently shows:

- 'U' = facelet shows the color of Up face's center
- 'R' = facelet shows the color of Right face's center
- 'F' = facelet shows the color of Front face's center
- 'D' = facelet shows the color of Down face's center
- 'L' = facelet shows the color of Left face's center
- 'B' = facelet shows the color of Back face's center

Example - Solved Cube:
::

    "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
     └─ U ──┘└─ R ──┘└─ F ──┘└─ D ──┘└─ L ──┘└─ B ──┘


Dynamic Color Mapping
---------------------
Our cube model may move center colors during slice moves (M, E, S).
Unlike a physical 3x3 cube where centers are fixed, our model allows
center pieces to move.

Example after M rotation:
::

    Physical cube:     Our model:
    U center = Yellow  U center = Blue (moved from F)
    F center = Blue    F center = Yellow (moved from D)

To handle this, we build a dynamic mapping at solve time:

1. Check what color is currently on each face's center
2. Map that color → face name

::

    After M rotation:
    U face center = Blue   →  Blue  maps to 'U'
    F face center = Yellow →  Yellow maps to 'F'
    ... etc

3. Use this mapping to convert all facelets to Kociemba characters

This ensures the string is always valid for Kociemba regardless of how
our internal model represents the cube state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import kociemba  # type: ignore[import-not-found]

from cube.domain.algs._parser import parse_alg
from cube.domain.exceptions import OpAborted
from cube.domain.model.cube_boy import Color, FaceName
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolveStep, SolverResults
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube
    from cube.domain.model.Face import Face


# Face order for Kociemba's 54-char string: U R F D L B
_FACE_ORDER: list[FaceName] = [
    FaceName.U,
    FaceName.R,
    FaceName.F,
    FaceName.D,
    FaceName.L,
    FaceName.B,
]


class KociembaSolver(BaseSolver):
    """
    Near-optimal solver using Kociemba's two-phase algorithm.

    Finds solutions of 18-22 moves (God's Number is 20) in under 1 second.
    Only supports 3x3 cubes - larger cubes need reduction first.
    """

    __slots__: list[str] = []

    def __init__(self, op: OperatorProtocol) -> None:
        super().__init__(op)

    @property
    def get_code(self) -> SolverName:
        return SolverName.KOCIEMBA

    @property
    def status(self) -> str:
        if self._cube.solved:
            return "Solved"
        if self._cube.size != 3:
            return f"Kociemba: {self._cube.size}x{self._cube.size} not supported (3x3 only)"
        return "Unsolved"

    def solve(
        self,
        debug: bool | None = None,
        animation: bool | None = True,
        what: SolveStep = SolveStep.ALL,
    ) -> SolverResults:
        """
        Solve the cube using Kociemba's algorithm.

        Args:
            debug: Enable debug output (None = use config)
            animation: Control animation (None = use config)
            what: Which step to solve (only ALL is supported for Kociemba)

        Returns:
            SolverResults with solve information
        """
        if debug is None:
            debug = self._is_debug_enabled

        with self._op.with_animation(animation=animation):
            try:
                return self._solve(debug, what)
            except OpAborted:
                return SolverResults()

    def _solve(self, debug: bool, what: SolveStep) -> SolverResults:
        sr = SolverResults()

        if self._cube.solved:
            return sr

        # Kociemba only supports 3x3 - fall back to beginner solver for other sizes
        if self._cube.size != 3:
            from cube.domain.solver.beginner.BeginnerSolver import BeginnerSolver
            fallback = BeginnerSolver(self._op)
            if debug:
                self.debug(f"Kociemba: falling back to beginner solver for {self._cube.size}x{self._cube.size} cube")
            return fallback.solve(debug=debug, animation=False, what=what)

        # Convert cube state to Kociemba's 54-char format
        cube_string = self._cube_to_kociemba_string(self._cube)

        if debug:
            self.debug("Cube state:", cube_string)

        # Get solution from Kociemba
        solution = kociemba.solve(cube_string)

        if debug:
            self.debug("Solution:", solution)
            move_count = len(solution.split())
            self.debug("Move count:", move_count)

        # Parse and execute the solution
        if solution:
            alg = parse_alg(solution)
            self._op.play(alg)

        return sr

    def _cube_to_kociemba_string(self, cube: Cube) -> str:
        """
        Convert cube state to Kociemba's 54-character string format.

        Format: 54 characters representing facelets in order U R F D L B.
        Each face has 9 facelets read left-to-right, top-to-bottom:
            0 1 2
            3 4 5
            6 7 8

        Each character is U/R/F/D/L/B indicating which face's center
        color that facelet currently shows.

        Note: We build a dynamic color→face mapping based on current center colors,
        so this works even when the cube model moves centers (e.g., after M rotation).
        """
        # Build dynamic mapping: current center color → face name
        color_to_face: dict[Color, str] = {}
        for face_name in _FACE_ORDER:
            face = cube.face(face_name)
            center_color = face.center.color
            color_to_face[center_color] = face_name.name

        result: list[str] = []
        for face_name in _FACE_ORDER:
            face = cube.face(face_name)
            face_string = self._face_to_kociemba_string(face, color_to_face)
            result.append(face_string)

        return "".join(result)

    def _face_to_kociemba_string(self, face: Face, color_to_face: dict[Color, str]) -> str:
        """
        Convert a single face to 9 Kociemba characters.

        Reading order (looking at face):
            0 1 2   = corner_top_left, edge_top, corner_top_right
            3 4 5   = edge_left, center, edge_right
            6 7 8   = corner_bottom_left, edge_bottom, corner_bottom_right

        Args:
            face: The face to convert
            color_to_face: Dynamic mapping from color to face letter (U/R/F/D/L/B)
        """
        colors: list[Color] = []

        # Row 0: corner_top_left, edge_top, corner_top_right
        colors.append(face.corner_top_left.get_face_edge(face).color)
        colors.append(face.edge_top.get_face_edge(face).color)
        colors.append(face.corner_top_right.get_face_edge(face).color)

        # Row 1: edge_left, center, edge_right
        colors.append(face.edge_left.get_face_edge(face).color)
        colors.append(face.center.color)
        colors.append(face.edge_right.get_face_edge(face).color)

        # Row 2: corner_bottom_left, edge_bottom, corner_bottom_right
        colors.append(face.corner_bottom_left.get_face_edge(face).color)
        colors.append(face.edge_bottom.get_face_edge(face).color)
        colors.append(face.corner_bottom_right.get_face_edge(face).color)

        # Convert colors to Kociemba characters using dynamic mapping
        return "".join(color_to_face[c] for c in colors)
