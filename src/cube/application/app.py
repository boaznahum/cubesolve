from typing import TYPE_CHECKING, Any

from cube.application.AbstractApp import AbstractApp
from cube.application.commands.Operator import Operator
from cube.application.markers import (
    IMarkerFactory,
    IMarkerManager,
    MarkerFactory,
    MarkerManager,
    NoopMarkerFactory,
    NoopMarkerManager,
)
from cube.application.state import ApplicationAndViewState
from cube.utils.logger_protocol import ILogger
from cube.domain.algs import Alg
from cube.domain.model.Cube import Cube
from cube.domain.solver import Solver, Solvers
from cube.domain.solver.SolverName import SolverName
from cube.utils.config_protocol import ConfigProtocol
from cube.utils.service_provider import IServiceProvider

if TYPE_CHECKING:
    from cube.application.animation.AnimationManager import AnimationManager


class _App(AbstractApp, IServiceProvider):

    def __init__(self,
                 config: ConfigProtocol,
                 vs: ApplicationAndViewState,
                 cube_size: int | None,
                 solver: SolverName | None = None) -> None:
        self._config = config
        # Always start with Noop markers; enable_animation() swaps them
        self._marker_factory: IMarkerFactory = NoopMarkerFactory()
        self._marker_manager: IMarkerManager = NoopMarkerManager()
        super().__init__()

        self._vs = vs
        # Use the logger from ApplicationAndViewState (has env var override)
        self._logger = vs.logger
        self._error = None

        if cube_size is not None:
            vs.cube_size = cube_size

        self._cube = Cube(self.vs.cube_size, sp=self)

        self._am: AnimationManager | None = None

        self._op: Operator = Operator(self.cube, self._vs)

        if solver is not None:
            self._slv: Solver = Solvers.by_name(solver, self.op)
        else:
            self._slv = Solvers.default(self.op)

        self.reset(None)

    def enable_animation(self, am: 'AnimationManager') -> None:
        """Inject animation support. Called by backend after app creation."""
        assert self._am is None, "enable_animation() called twice"
        self._am = am
        self._marker_factory = MarkerFactory()
        self._marker_manager = MarkerManager()
        self._op.enable_animation(am, self._config.animation_enabled)

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
    def marker_factory(self) -> IMarkerFactory:
        """Get the marker factory for creating marker configurations."""
        return self._marker_factory

    @property
    def marker_manager(self) -> IMarkerManager:
        """Get the marker manager for adding/retrieving markers on cube stickers."""
        return self._marker_manager

    @property
    def logger(self) -> ILogger:
        """Get the logger for debug output control."""
        return self._logger

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

    def switch_to_solver(self, name: SolverName) -> Solver:
        """Switch to a specific solver by name."""
        self._slv = Solvers.by_name(name, self.op)
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
