from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

from cube.application.commands.Operator import Operator
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
    def create() -> "AbstractApp":
        return AbstractApp.create_non_default(None)

    @staticmethod
    def create_non_default(
        cube_size: int | None,
        animation: bool = True,
        debug_all: bool = False,
        quiet_all: bool = False,
        solver: SolverName | None = None,
    ) -> "AbstractApp":
        from .app import _App
        from .config_impl import AppConfig

        # Create config first - it provides values to everything else
        config = AppConfig()
        vs = ApplicationAndViewState(config, debug_all=debug_all, quiet_all=quiet_all)
        am: "AnimationManager | None" = None
        if animation:
            from cube.application.animation.AnimationManager import AnimationManager
            am = AnimationManager(vs)
        app: _App = _App(config, vs, am, cube_size, solver)

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
