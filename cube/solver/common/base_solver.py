from abc import ABC, abstractmethod
from typing import TypeAlias, TYPE_CHECKING, final

from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from .. import Solver
from ...algs import Algs

if TYPE_CHECKING:
    from .common_op import CommonOp

_Common: TypeAlias = "CommonOp"

class BaseSolver(Solver):

    __slots__:list[str] = ["_common", "_op", "_cube"]

    def __init__(self, op) -> None:
        super().__init__()
        self._op = op
        self._cube = op.cube
        from .common_op import CommonOp
        self.common: _Common = CommonOp(self)


    @abstractmethod
    def debug(self, *args): ...

    @property
    @final
    def cube(self) -> Cube:
        return self._cube

    @property
    @final
    def op(self) -> Operator:
        return self._op

    @property
    @final
    def cmn(self) -> _Common:
        return self.common


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
