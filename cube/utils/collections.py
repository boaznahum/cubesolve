from collections.abc import MutableSet
from typing import Set, TypeVar, Iterable, Iterator, AbstractSet, Any, Generic

#_T = TypeVar("_T")
_T = TypeVar("_T")#, covariant=True)


class OrderedSet(MutableSet[_T], Generic[_T]):

    def __init__(self, __iterable: Iterable[_T] = None) -> None:
        super().__init__()
        self._dict: dict[_T, None]
        if __iterable:
            self._dict = {x: None for x in __iterable}
        else:
            self._dict = {}

    def add(self, value: _T) -> None:
        self._dict[value] = None

    def discard(self, value: _T) -> None:
        self._dict.pop(value)

    def clear(self) -> None:
        self._dict.clear()

    def __contains__(self, __o: object) -> bool:
        return __o in self._dict

    def __iter__(self) -> Iterator[_T]:
        return iter(self._dict.keys())

    def __len__(self) -> int:
        return self._dict.__len__()

    def __sub__(self, __s: AbstractSet[Any]) -> MutableSet[_T]:

        if not __s:
            return self
        else:

            cc: OrderedSet[_T] = OrderedSet(self._dict.keys())

            c = cc._dict
            for x in __s:
                c.pop(x)

            return cc

    def __str__(self) -> str:
        s=""

        for x in self._dict.keys():
            if s:
                s += ", "
            s += str(x)

        s += "}"

        return s


