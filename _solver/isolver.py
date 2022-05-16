from abc import ABC, abstractmethod

from algs import Algs
from cube import Cube
from cube_operator import Operator
from elements import Part


class ISolver(ABC):

    __slots__ = []

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

