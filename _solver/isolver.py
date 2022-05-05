from abc import ABC, abstractmethod
from cube import Cube
from cube_operator import Operator


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
