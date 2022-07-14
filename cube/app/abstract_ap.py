from abc import abstractmethod

from cube.app.app_state import ApplicationAndViewState
from cube.model.cube import Cube
from cube.operator.cube_operator import Operator
from cube.solver import Solver


class AbstractApp:
    def __init__(self):
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
