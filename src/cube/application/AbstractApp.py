from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

from cube.application.commands.Operator import Operator
from cube.application.Scrambler import Scrambler
from cube.application.state import ApplicationAndViewState
from cube.domain.algs import Alg
from cube.domain.solver import Solver
from cube.domain.solver.SolverName import SolverName
from cube.utils.config_protocol import ConfigProtocol

if TYPE_CHECKING:
    from cube.application.animation.AnimationManager import AnimationManager
    from cube.domain.model.Cube import Cube


class AbstractApp(metaclass=ABCMeta):
    """Abstract base class for the application.

    Implements IServiceProvider protocol - provides config to domain classes
    via dependency injection (passed to Cube constructor).
    """

    def __init__(self) -> None:
        self._error: str | None = None


    @staticmethod
    def create_app(
        cube_size: int | None = None,
        debug_all: bool = False,
        quiet_all: bool = False,
        solver: SolverName | None = None,
    ) -> "AbstractApp":
        """Create app without animation. For tests, scripts, and as first step for GUI.

        The app is always born without animation (Noop markers, no AnimationManager).
        Animation is injected later by the backend via ``enable_animation()``.

        Creation flow::

            Non-GUI (tests/scripts):
                app = AbstractApp.create_app(cube_size=3)
                # app has: NoopMarkerFactory, NoopMarkerManager, NoopAnnotation
                # → ready to use, no animation

            GUI:
                app = AbstractApp.create_app(cube_size=3)
                backend = BackendRegistry.get_backend("pyglet2")
                window = backend.create_app_window(app)
                # Inside create_app_window, backend calls:
                #   am = AnimationManager(app.vs)
                #   app.enable_animation(am)      ← swaps Noop → real objects
                #   am.set_event_loop(event_loop)

            enable_animation(am) injection chain::

                _App.enable_animation(am)
                  ├── _am              = am
                  ├── _marker_factory  = MarkerFactory()        (was Noop)
                  ├── _marker_manager  = MarkerManager()        (was Noop)
                  └── _op.enable_animation(am, animation_enabled)
                        ├── _animation_manager = am
                        ├── _animation_enabled = True
                        └── _annotation        = OpAnnotation   (was Noop)
        """
        from .app import _App
        from .config_impl import AppConfig

        config = AppConfig()
        vs = ApplicationAndViewState(config, debug_all=debug_all, quiet_all=quiet_all)
        app: _App = _App(config, vs, cube_size, solver)

        return app

    @property
    @abstractmethod
    def config(self) -> ConfigProtocol:
        """Get the application configuration."""
        raise NotImplementedError

    @property
    @abstractmethod
    def error(self) -> str | None:
        pass

    @abstractmethod
    def set_error(self, _error: str) -> None:
        self._error = _error


    @property
    @abstractmethod
    def am(self) -> "AnimationManager | None":
        pass

    @abstractmethod
    def enable_animation(self, am: "AnimationManager") -> None:
        """Inject animation support. Called by backend after app creation."""
        raise NotImplementedError

    @property
    @abstractmethod
    def op(self) -> Operator:
        raise NotImplementedError

    @property
    @abstractmethod
    def vs(self) -> ApplicationAndViewState:
        raise NotImplementedError

    @property
    @abstractmethod
    def slv(self) -> Solver:
        raise NotImplementedError

    @abstractmethod
    def switch_to_next_solver(self) -> Solver:
        raise NotImplementedError

    @property
    @abstractmethod
    def cube(self) -> "Cube":
        raise NotImplementedError

    @property
    def scrambler(self) -> Scrambler:
        """Get the scrambler for generating scramble algorithms."""
        return Scrambler(self)

    @abstractmethod
    def reset(self, cube_size: int | None = None):
        """
        Reset cube
        Reset operator
        Reset last error message
        :param cube_size: if None then stay with current size (not config size)
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def run_tests(self, first_scramble_key: int,
                  number_of_loops: int,
                  debug=False):
        pass

    @abstractmethod
    def run_single_test(self, scramble_key,
                        scramble_size: int | None,
                        debug: bool,
                        animation: bool):
        pass

    @abstractmethod
    def scramble(self,
                 scramble_key: Any,
                 scramble_size: Any,
                 animation: Any,
                 verbose=True
                 ) -> Alg:
        """
        reset cube before scramble
        Runs scramble on cube and returns alg
        :param scramble_key:
        :param scramble_size:
        :param animation:
        :param verbose:
        :return:
        """
        pass
