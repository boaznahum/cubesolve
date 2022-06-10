from abc import abstractmethod

import config
from app_state import AppState
from cube_operator import Operator
from model.cube import Cube
from solver import Solver


class AbstractApp:
    def __init__(self):
        pass

    @property
    @abstractmethod
    def op(self) -> Operator:
        raise NotImplementedError

    @property
    @abstractmethod
    def vs(self) -> AppState:
        raise NotImplementedError

    @property
    @abstractmethod
    def slv(self) -> Solver:
        raise NotImplementedError

    @property
    @abstractmethod
    def cube(self) -> Cube:
        raise NotImplementedError

    @abstractmethod
    def reset(self, dont_reset_axis=False):
        raise NotImplementedError


class App(AbstractApp):

    def __init__(self) -> None:
        super().__init__()
        self._error: str | None = None

        self._vs = AppState()

        self._cube = Cube(self.vs.cube_size)

        self._op: Operator = Operator(self.cube, self._vs, config.animation_enabled)

        self._slv: Solver = Solver(self.op)

        # pp.alpha_x=0.30000000000000004 app.alpha_y=-0.4 app.alpha_z=0

        self.reset()

    def reset(self, dont_reset_axis=False):
        self.cube.reset(self.vs.cube_size)
        # can't change instance, it is shared
        if not dont_reset_axis:
            self.vs.reset()
        self._error = None

    def set_error(self, _error: str):
        self._error = _error

    @property
    def error(self):
        return self._error

    @property
    def op(self) -> Operator:
        return self._op

    @property
    def vs(self) -> AppState:
        return self._vs

    @property
    def slv(self) -> Solver:
        return self._slv

    @property
    def cube(self) -> Cube:
        return self._cube
