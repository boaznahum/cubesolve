from abc import abstractmethod, ABCMeta
from typing import TYPE_CHECKING, Any, Optional

from cube.algs import Alg
from cube.app.app_state import ApplicationAndViewState
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver

if TYPE_CHECKING:
    from cube.animation.animation_manager import AnimationManager


class AbstractApp(metaclass=ABCMeta):
    def __init__(self) -> None:
        self._error : str | None = None


    @staticmethod
    def create() -> "AbstractApp":
        return AbstractApp.create_non_default(None)

    @staticmethod
    def create_non_default(cube_size: int | None, animation=True) -> "AbstractApp":
        from .app import _App

        vs = ApplicationAndViewState()
        from cube.animation.animation_manager import AnimationManager
        am: AnimationManager | None = None
        if animation:
            am = AnimationManager(vs)
        app: _App = _App(vs, am, cube_size)

        return app

    @property
    @abstractmethod
    def error(self) -> str|None:
        pass

    @abstractmethod
    def set_error(self, _error: str) -> None:
        self._error = _error


    @property
    @abstractmethod
    def am(self) -> Optional["AnimationManager"]:
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
    def cube(self) -> Cube:
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
                 animation: bool,
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
