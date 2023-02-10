from typing import Any

from cube import config
from cube.algs import Alg
from cube.animation.animation_manager import AnimationManager
from cube.app.abstract_ap import AbstractApp
from cube.app.app_state import ApplicationAndViewState
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver, Solvers


class _App(AbstractApp):

    def __init__(self,
                 vs: ApplicationAndViewState,
                 am: AnimationManager | None,
                 cube_size: int | None) -> None:
        super().__init__()

        self._vs = vs
        self._error = None

        if cube_size is not None:
            vs.cube_size = cube_size

        self._cube = Cube(self.vs.cube_size)

        self._am = am

        self._op: Operator = Operator(self.cube,
                                      self._vs,
                                      am,
                                      config.animation_enabled)

        self._slv: Solver = Solvers.default(self.op)

        # pp.alpha_x=0.30000000000000004 app.alpha_y=-0.4 app.alpha_z=0

        self.reset(None)

    def reset(self, cube_size: int | None = None):
        self.cube.reset(cube_size)
        self.op.reset()
        self._error = None

    def set_error(self, _error: str):
        self._error = _error

    @property
    def error(self) -> str|None:
        return self._error

    @property
    def am(self) -> AnimationManager:
        return self._am

    @property
    def op(self) -> Operator:
        return self._op

    @property
    def vs(self) -> ApplicationAndViewState:
        return self._vs

    @property
    def slv(self) -> Solver:
        return self._slv

    def switch_to_next_solver(self) -> Solver:
        self._slv = Solvers.next_solver(self._slv.get_code, self.op)
        return self._slv

    @property
    def cube(self) -> Cube:
        return self._cube

    def run_tests(self, first_scramble_key, number_of_loops, debug=False):
        from . import _app_tests

        _app_tests.run_tests(self, first_scramble_key, number_of_loops, debug=debug)

    def run_single_test(self, scramble_key,
                        scramble_size: int | None,
                        debug: bool,
                        animation: bool):
        from . import _app_tests

        _app_tests.run_single_test(self, scramble_key, scramble_size, debug, animation)

    def scramble(self,
                 scramble_key: Any,
                 scramble_size: Any,
                 animation: bool,
                 verbose=True
                 ) -> Alg:
        from . import _app_tests

        return _app_tests.scramble(self, scramble_key, scramble_size, animation, verbose)
