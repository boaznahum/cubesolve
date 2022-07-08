from abc import ABC, abstractmethod

from cube.model.cube import Cube
from cube.operator.cube_operator import Operator


class BaseSolver(ABC):

    __slots__:list[str] = []

    @abstractmethod
    def debug(self, *args): ...

    @property
    @abstractmethod
    def cube(self) -> Cube: ...

    @property
    @abstractmethod
    def op(self) -> Operator: ...

    @property
    @abstractmethod
    def cmn(self): ...

    @property
    @abstractmethod
    def running_solution(self):
        pass

