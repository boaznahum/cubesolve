from abc import ABC
from typing import TypeAlias, TYPE_CHECKING, final

from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from .. import Solver
from ... import config
from ...algs import Algs

if TYPE_CHECKING:
    from .common_op import CommonOp

_Common: TypeAlias = "CommonOp"


class BaseSolver(Solver, ABC):
    __slots__: list[str] = ["_common", "_op", "_cube", "_debug_override"]

    def __init__(self, op) -> None:
        super().__init__()
        self._op = op
        self._cube = op.cube
        from .common_op import CommonOp
        self.common: _Common = CommonOp(self)
        self._debug_override: bool | None = None

    @property
    def is_solved(self):
        return self._cube.solved

    @property
    def is_debug_config_mode(self) -> bool:
        # Check config flag (is_debug also checks debug_all and quiet_all)
        return self._op.app_state.is_debug(config.SOLVER_DEBUG)

    @property
    def _is_debug_enabled(self) -> bool:
        # Truth table (_debug_override, SOLVER_DEBUG) -> result:
        # | override | config | result |  (None means "use config")
        # |----------|--------|--------|
        # | None     | False  | False  |  <- use config
        # | None     | True   | True   |  <- use config
        # | False    | False  | False  |  <- override wins
        # | False    | True   | False  |  <- override wins (can't use OR!)
        # | True     | False  | True   |  <- override wins
        # | True     | True   | True   |  <- override wins
        flag = self._debug_override if self._debug_override is not None else config.SOLVER_DEBUG
        return self._op.app_state.is_debug(flag)

    def debug(self, *args):
        vs = self._op.app_state
        if vs.is_debug(self._debug_override if self._debug_override is not None else config.SOLVER_DEBUG):
            prefix = self.name + ":"
            print(vs.debug_prefix(), "Solver:", prefix, *(str(x) for x in args))
            self.op.log("Solver:", prefix, *args)


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
