"""Cage Method NxN Solver - solves big cubes step by step.

Cage method for odd cubes (5x5, 7x7):
1. Solve centers one face at a time (starting face configurable)
2. ... (more steps to come)

For odd cubes, the center piece defines the face color.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.model import Color
from cube.domain.model.Face import Face
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import Solver, SolveStep, SolverResults
from cube.domain.solver.SolverName import SolverName
from cube.domain.solver.common.BaseSolver import BaseSolver
from cube.domain.solver.beginner.NxNCenters import NxNCenters

if TYPE_CHECKING:
    from cube.domain.model.Cube import Cube

# Configuration: which face to start with
START_FACE_COLOR: Color = Color.WHITE


class _FaceLoc:
    """Face locator for _do_center - provides face and color properties."""

    def __init__(self, cube: Cube, color: Color) -> None:
        self._cube = cube
        self._color = color

    @property
    def face(self) -> Face:
        return self._cube.color_2_face(self._color)

    @property
    def color(self) -> Color:
        return self._color


class _CageFacade(BaseSolver):
    """Minimal BaseSolver facade for NxNCenters."""

    def __init__(self, op: OperatorProtocol) -> None:
        super().__init__(op)

    @property
    def get_code(self) -> SolverName:
        return SolverName.CAGE

    @property
    def status(self) -> str:
        return "Cage"

    def solve(
        self,
        debug: bool | None = None,
        animation: bool | None = True,
        what: SolveStep = SolveStep.ALL
    ) -> SolverResults:
        raise NotImplementedError("Use CageNxNSolver.solve()")

#claude: yu can inherit from AbstractSolver no need for all this mess
class CageNxNSolver(Solver):
    """
    Cage method solver for odd NxN cubes.

    Solves step by step:
    - Step 1: White face centers
    - (more steps to come)
    """

    def __init__(self, op: OperatorProtocol) -> None:
        super().__init__()
        self._op = op
        self._facade = _CageFacade(op)
        self._centers = NxNCenters(self._facade)

    @property
    def get_code(self) -> SolverName:
        return SolverName.CAGE

    @property
    def op(self) -> OperatorProtocol:
        return self._op

    @property
    def _cube(self) -> Cube:
        return self._op.cube

    @property
    def is_solved(self) -> bool:
        return self._cube.solved

    @property
    def is_debug_config_mode(self) -> bool:
        return self._cube.config.solver_debug

    @property
    def status(self) -> str:
        """Return current solving status."""
        if self.is_solved:
            return "Solved"

        # Check start face center reduction
        start_face = self._cube.color_2_face(START_FACE_COLOR)
        color_name = START_FACE_COLOR.name.capitalize()
        if start_face.center.is3x3:
            return f"{color_name}:Done"
        else:
            return f"{color_name}:Pending"

    def _is_face_center_solved(self, color: Color) -> bool:
        """Check if a face's centers are reduced to 3x3."""
        face = self._cube.color_2_face(color)
        return self._centers._is_face_solved(face, color)

    def _solve_face_center(self, color: Color) -> None:
        """Solve one face's centers to 3x3.

        Uses NxNCenters._do_center which:
        1. Brings face to front (cmn.bring_face_front)
        2. Pulls matching pieces from adjacent faces
        3. Uses commutators to place them
        """
        if self._is_face_center_solved(color):
            return

        face_loc = _FaceLoc(self._cube, color)
        # _do_center handles bring_face_front internally
        self._centers._do_center(face_loc, minimal_bring_one_color=False, use_back_too=True)  # type: ignore[arg-type]

    def solve(
        self,
        debug: bool | None = None,
        animation: bool | None = True,
        what: SolveStep = SolveStep.ALL
    ) -> SolverResults:
        """Solve using Cage method."""
        sr = SolverResults()

        if self.is_solved:
            return sr

        cube = self._cube

        # Only odd cubes supported
        if cube.size % 2 == 0:
            raise ValueError("Cage method only supports odd cubes (5x5, 7x7, ...)")

        # Step 1: Solve start face centers
        self._solve_face_center(START_FACE_COLOR)

        return sr
