"""Beginner 2x2 solver — human layer-by-layer method.

Solves a 2x2 cube the way a human would, using the beginner method:

  Layer 1 (L1): Solve the first layer (4 corners on bottom)
  Layer 3 (L3): Solve the last layer (4 corners on top)

This mirrors the 3x3 beginner approach but without edges or cross steps
(a 2x2 has only corners). The goal is educational — showing how a human
would reason through the solve step by step.

Steps:
  L1 — Solve first layer: place all 4 bottom-layer corners with correct
        position and orientation (white face down).
  L3 — Solve last layer in two sub-steps:
        1. Orient last-layer corners (all yellow stickers facing up)
        2. Permute last-layer corners (swap into correct positions)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cube.domain.solver.common.Solver2x2Base import Solver2x2Base
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.solver.solver import SolverResults, SolveStep
from cube.domain.solver.SolverName import SolverName
from ...model import Color, Face

if TYPE_CHECKING:
    from cube.utils.logger_protocol import ILogger

from ._L1 import L1
from ._L3Orient import L3Orient
from ._L3Permute import L3Permute


class Solver2x2Beginner(Solver2x2Base):
    """Beginner 2x2 cube solver using human layer-by-layer method.

    Solves in 3 phases:
    1. L1 — First layer corners (white face down)
    2. L3 Orient — Orient last-layer corners (yellow on top)
    3. L3 Permute — Permute last-layer corners into final positions
    """

    __slots__: list[str] = ["_l1", "_l3_orient", "_l3_permute"]

    def __init__(
        self,
        op: OperatorProtocol,
        parent_logger: ILogger,
    ) -> None:
        super().__init__(op, parent_logger, logger_prefix="Beginner2x2")

        self._l1 = L1(self)
        self._l3_orient = L3Orient(self)
        self._l3_permute = L3Permute(self)

    @property
    def get_code(self) -> SolverName:
        return SolverName.TWO_BY_TWO_BEGINNER

    @property
    def _status_impl(self) -> str:
        if self._cube.solved:
            return "Solved"

        l1_result = self._l1.solved_face_and_color()
        if not l1_result:
            return "Unsolved"

        l1_face, l1_color = l1_result

        with self.op.with_query_restore_state():
            self.cmn.bring_face_down(l1_face)

            l3o_done = self._l3_orient.is_solved_with(l1_color)
            l3p_done = self._l3_permute.is_solved_with(l1_color)

            if l3o_done and l3p_done:
                return "L1, L3"
            elif l3o_done:
                return "L1, L3-Orient"
            else:
                return "L1"

    def _solve_impl(self, what: SolveStep) -> SolverResults:
        sr = SolverResults()

        if self._cube.solved:
            return sr

        match what:
            case SolveStep.L1:
                self._l1.solve()

            case SolveStep.ALL | SolveStep.L3:
                self._l1.solve()
                l1_result = self._l1.solved_face_and_color()
                assert l1_result
                l1_face, l1_color = l1_result
                self._solve_l3(l1_face, l1_color)

        return sr

    def _solve_l3(self, l1_face: Face, l1_color: Color) -> None:
        """Solve L3: permute then orient."""
        with self._logger.tab("Solve L3"):
            self.cmn.bring_face_down(l1_face)
            self._l3_permute.solve(l1_color)
            self._l3_orient.solve(l1_color)

    def _supported_steps_impl(self) -> list[SolveStep]:
        return [SolveStep.L1, SolveStep.L3]
