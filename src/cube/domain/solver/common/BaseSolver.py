from abc import ABC
from typing import TypeAlias, TYPE_CHECKING, final

from cube.domain.model.Cube import Cube
from cube.domain.solver.protocols import OperatorProtocol
from cube.domain.algs.Algs import Algs
from .. import Solver

if TYPE_CHECKING:
    from .CommonOp import CommonOp

_Common: TypeAlias = "CommonOp"


class BaseSolver(Solver, ABC):
    __slots__: list[str] = ["_common", "_op", "_cube", "_debug_override"]

    def __init__(self, op) -> None:
        super().__init__()
        self._op = op
        self._cube = op.cube
        from .CommonOp import CommonOp
        self.common: _Common = CommonOp(self)
        self._debug_override: bool | None = None

    @property
    def is_solved(self):
        return self._cube.solved

    @property
    def is_debug_config_mode(self) -> bool:
        return self._cube.config.solver_debug

    @property
    def _is_debug_enabled(self) -> bool:
        if self._debug_override is None:
            return self.is_debug_config_mode
        else:
            return self._debug_override

    def debug(self, *args):
        if self._is_debug_enabled:
            prefix = self.name + ":"
            print("Solver:", prefix, *(str(x) for x in args) )

            self.op.log("Solver:", prefix, *args)


    @property
    @final
    def cube(self) -> Cube:
        return self._cube

    @property
    @final
    def op(self) -> OperatorProtocol:
        return self._op

    @property
    @final
    def cmn(self) -> _Common:
        return self.common

    @property
    def use_original_color(self) -> bool:
        """Whether to use original_color for face mapping (Cage method on even cubes)."""
        return self.common.use_original_color

    @use_original_color.setter
    def use_original_color(self, value: bool) -> None:
        """Set whether to use original_color for face mapping."""
        self.common.use_original_color = value

    def reset_white_face_tracking(self) -> None:
        """Reset the white face tracking state for Cage method."""
        self.common.reset_white_face_tracking()

    def solution(self):
        if self.is_solved:
            return Algs.alg(None)

        n = len(self.op.history())
        solution_algs = []

        with self._op.with_animation(animation=False):

            with self._op.save_history():  # not really needed
                self.solve(debug=False, animation=False)
                while n < len(self.op.history()):
                    step = self.op.undo(animation=False)
                    # s=str(step)
                    if step:
                        solution_algs.insert(0, step)

            return Algs.alg(None, *solution_algs)
