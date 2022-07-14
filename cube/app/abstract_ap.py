from abc import abstractmethod, ABCMeta
from typing import TYPE_CHECKING

from cube.app.app_state import ApplicationAndViewState
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver

if TYPE_CHECKING:
    from cube.animation.animation_manager import AnimationManager


class AbstractApp(metaclass=ABCMeta):
    def __init__(self):
        pass

    @staticmethod
    def create() -> "AbstractApp":
        return AbstractApp.create_non_default(None)

    @staticmethod
    def create_non_default(cube_size: int | None) -> "AbstractApp":
        from .app import _App

        vs = ApplicationAndViewState()
        from cube.animation.animation_manager import AnimationManager
        am: AnimationManager = AnimationManager(vs)
        app: _App = _App(vs, am, cube_size)

        return app

    @property
    @abstractmethod
    def am(self) -> "AnimationManager":
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

    @property
    @abstractmethod
    def cube(self) -> Cube:
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def run_tests(self, first_scramble_key: int,
                  number_of_loops: int):
        pass

    @abstractmethod
    def run_single_test(self, scramble_key,
                        scramble_size: int | None,
                        debug: bool,
                        animation: bool):
        pass
