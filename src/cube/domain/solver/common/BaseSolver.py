from abc import ABC
from typing import TYPE_CHECKING, TypeAlias

from cube.domain.algs.Alg import Alg
from cube.domain.algs.Algs import Algs

from .AbstractSolver import AbstractSolver

if TYPE_CHECKING:
    from .CommonOp import CommonOp

_Common: TypeAlias = "CommonOp"


class BaseSolver(AbstractSolver, ABC):
    __slots__: list[str] = ["_op", "_cube", "_debug_override"]

    def __init__(self, op) -> None:
        super().__init__(op)

    def solution(self) -> Alg:
        if self.is_solved:
            return Algs.alg(None)

        n = len(self.op.history())
        solution_algs: list[Alg] = []

        with self._op.with_animation(animation=False):

            with self._op.save_history():  # not really needed
                self.solve(debug=False, animation=False)
                while n < len(self.op.history()):
                    step = self.op.undo(animation=False)
                    # s=str(step)
                    if step:
                        solution_algs.insert(0, step)

            return Algs.alg(None, *solution_algs)
