from typing import Any, TYPE_CHECKING

from cube.utils.config_protocol import ConfigProtocol
from cube.domain.algs import Alg
from cube.application.AbstractApp import AbstractApp
from cube.application.state import ApplicationAndViewState
from cube.domain.model.Cube import Cube
from cube.application.commands.Operator import Operator
from cube.domain.solver import Solver, Solvers
from cube.domain.solver.SolverName import SolverName

if TYPE_CHECKING:
    from cube.application.animation.AnimationManager import AnimationManager


class _App(AbstractApp):

    def __init__(self,
                 config: ConfigProtocol,
                 vs: ApplicationAndViewState,
                 am: 'AnimationManager | None',
                 cube_size: int | None,
                 solver: SolverName | None = None) -> None:
        self._config = config
        super().__init__()

        self._vs = vs
        self._error = None

        if cube_size is not None:
            vs.cube_size = cube_size

        self._cube = Cube(self.vs.cube_size, sp=self)

        self._am = am

        self._op: Operator = Operator(self.cube,
                                      self._vs,
                                      am,
                                      config.animation_enabled)

        if solver is not None:
            self._slv: Solver = Solvers.by_name(solver, self.op)
        else:
            self._slv = Solvers.default(self.op)

        # pp.alpha_x=0.30000000000000004 app.alpha_y=-0.4 app.alpha_z=0

        self.reset(None)

    def reset(self, cube_size: int | None = None):
        self.cube.reset(cube_size)
        self.op.reset()
        self._error = None

    def set_error(self, _error: str):
        self._error = _error

    @property
    def config(self) -> ConfigProtocol:
        """Get the application configuration."""
        return self._config

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def am(self) -> 'AnimationManager | None':
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
                 animation: Any,
                 verbose=True
                 ) -> Alg:
        from . import _app_tests

        return _app_tests.scramble(self, scramble_key, scramble_size, animation, verbose)
