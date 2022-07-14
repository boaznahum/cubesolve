from cube import config
from cube.animation.animation_manager import AnimationManager
from cube.app.abstract_ap import AbstractApp
from cube.app.app_state import ApplicationAndViewState
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver, Solvers


class App(AbstractApp):

    def __init__(self,
                 vs: ApplicationAndViewState,
                 am: AnimationManager) -> None:
        super().__init__()

        self._vs = vs
        self._error: str | None = None

        self._cube = Cube(self.vs.cube_size)

        self._op: Operator = Operator(self.cube,
                                      self._vs,
                                      am,
                                      config.animation_enabled)

        self._slv: Solver = Solvers.default(self.op)

        # pp.alpha_x=0.30000000000000004 app.alpha_y=-0.4 app.alpha_z=0

        self.reset()

    def reset(self):
        self.cube.reset(self.vs.cube_size)
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
    def vs(self) -> ApplicationAndViewState:
        return self._vs

    @property
    def slv(self) -> Solver:
        return self._slv

    @property
    def cube(self) -> Cube:
        return self._cube
