"""
Kociemba 3x3 Solver - implements Solver3x3Protocol
===================================================

Uses Herbert Kociemba's two-phase algorithm to find near-optimal solutions
(typically 18-22 moves) for any 3x3 Rubik's cube position.

This solver wraps the `kociemba` Python package which provides:
- Sub-second solve times
- Solutions within 2-3 moves of optimal (God's Number = 20)
- Automatic pruning table generation on first use

For NxN cubes, use via NxNSolverOrchestrator which handles reduction first.


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

from cube.domain.exceptions.InternalSWError import InternalSWError
from cube.domain.algs._parser import parse_alg
from cube.domain.model.geometric.cube_boy import Color, FaceName
from cube.domain.solver.common.AbstractSolver import AbstractSolver
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.protocols.Solver3x3Protocol import Solver3x3Protocol
from cube.domain.solver.solver import SolverResults, SolveStep
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


class Kociemba3x3(AbstractSolver, Solver3x3Protocol):
    """
    Pure 3x3 solver using Kociemba's two-phase algorithm.

    Finds solutions of 18-22 moves (God's Number is 20) in under 1 second.

    This solver implements Solver3x3Protocol and only handles 3x3 solving.
    For NxN cubes, use via NxNSolverOrchestrator which:
    1. Reduces NxN to virtual 3x3
    2. Calls this solver for the 3x3 phase

    Note: Works on actual 3x3 cubes OR reduced NxN cubes (treated as virtual 3x3).
    """



    __slots__ = ["_op", "_debug_override"]

    def __init__(self, op: OperatorProtocol) -> None:
        super().__init__(op)
        self._op = op
        self._op = op
        self._debug_override: bool | None = None

    @property
    def get_code(self) -> SolverName:
        """Return solver identifier."""
        return SolverName.KOCIEMBA


    @property
    def status_3x3(self) -> str:
        """Human-readable 3x3 solving status."""
        if self._cube.solved:
            return "Solved"
        return "Unsolved (Kociemba)"

    @property
    def status(self) -> str:
        return self.status_3x3

    @property
    def can_detect_parity(self) -> bool:
        """Kociemba cannot detect parity - it just fails with invalid cube state."""
        return False

    def solve_3x3(
        self,
        debug: bool = False,
        what: SolveStep | None = None
    ) -> SolverResults:
        """
        Solve using Kociemba's two-phase algorithm.

        Args:
            debug: Enable debug output
            what: Which step to solve (ignored - Kociemba always solves ALL)

        Returns:
            SolverResults with solve metadata

        Note:
            - Kociemba always solves completely (partial solving not supported)
            - Works on 3x3 cubes OR reduced NxN cubes (reads outer layer only)
        """
        sr = SolverResults()

        if self._cube.solved:
            return sr

        # Store debug state
        _d = self._debug_override
        try:
            self._debug_override = debug

            # Convert cube state to Kociemba's 54-char format
            # This works for both 3x3 and reduced NxN (reads outer layer)
            cube_string = self._cube_to_kociemba_string(self._cube)

            if debug:
                self.debug("Cube state:", cube_string)

            # Get solution from Kociemba
            try:
                solution = kociemba.solve(cube_string)
            except ValueError as e:
                # Invalid cube string usually means edge parity on even cubes
                # The orchestrator will catch this, fix parity, and retry
                if debug:
                    self.debug("Invalid cube state (likely parity):", str(e))
                    #it is a bug we must not reach here orchstrator must handle it
                raise InternalSWError(
                    "Kociemba: Invalid cube state - orchstrator must handle it"
                ) from e

            if self.is_debug_enabled:
                self.debug("Solution:", solution)
                move_count = len(solution.split())
                self.debug("Move count:", move_count)

            # Parse and execute the solution
            if solution:
                alg = parse_alg(solution)
                self._op.play(alg)

        finally:
            self._debug_override = _d

        return sr

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        """Solve the cube. Called by AbstractSolver.solve().

        Animation and OpAborted are handled by the template method.

        Args:
            what: Which step to solve

        Returns:
            SolverResults with solve metadata
        """
        return self.solve_3x3(self._is_debug_enabled, what)

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

        Note: For NxN cubes, this reads the outer layer (corners/edges/centers)
        which represent the virtual 3x3 after reduction.
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

    def supported_steps(self) -> list[SolveStep]:
        """Return list of solve steps this solver supports.

        Kociemba always solves the entire cube at once - no partial solving.
        """
        return []
