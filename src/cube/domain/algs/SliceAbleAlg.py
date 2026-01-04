from abc import ABC
from typing import TYPE_CHECKING, Iterable, Self, Sequence

from cube.domain.algs.SimpleAlg import NSimpleAlg
from cube.domain.exceptions import InternalSWError

if TYPE_CHECKING:
    from cube.domain.algs.SimpleAlg import SimpleAlg


class SliceAbleAlg(NSimpleAlg, ABC):

    def __init__(self, code: str, n: int = 1) -> None:
        super().__init__(code, n)
        # sorted sequence
        self.slices: slice | Sequence[int] | None = None  # [1 n]

    @property
    def _hide_single_slice(self) -> bool:
        """Whether to hide [1] in string representation.

        FaceAlg overrides to True because R = R[1].
        SliceAlg keeps False because M ≠ M[1].
        """
        return False

    def copy(self, other: NSimpleAlg) -> Self:
        assert isinstance(other, SliceAbleAlg)
        super(SliceAbleAlg, self).copy(other)
        self.slices = other.slices
        return self

    def __getitem__(self, items: int | slice | Sequence[int]) -> Self:

        if not items:
            return self

        a_slice: slice | Sequence[int]
        if self.slices is not None:
            raise InternalSWError(f"Already sliced: {self}")
        if isinstance(items, int):
            a_slice = slice(items, items)  # start/stop the same
        elif isinstance(items, slice):
            a_slice = items
        elif isinstance(items, Sequence):
            a_slice = sorted(items)
        else:
            raise InternalSWError(f"Unknown type for slice: {items} {type(items)}")

        clone: SliceAbleAlg = self.clone()
        clone.slices = a_slice

        return clone  # type: ignore

    def _add_to_str(self, s):
        """
                    None -> default = R
                    (None, None) -> default R
                    (1, 1) -> default R
                    (start, None) -> [start:]R
                    (None, stop) -> [:stop] == [1:stop]
                    (start, stop) -> [start:stop]

                :param s:
                :return:
                """

        slices = self.slices

        if slices is None:
            return s

        if isinstance(slices, slice):

            start = slices.start
            stop = slices.stop

            if not start and not stop:
                return s

            # Hide [1:1] for FaceAlg (R = R[1]), but show for SliceAlg (M ≠ M[1])
            if self._hide_single_slice and 1 == start and 1 == stop:
                return s

            if start and not stop:
                return "[" + str(start) + ":" + "]" + s

            if not start and stop:
                return "[1:" + str(stop) + "]" + s

            if start and stop:
                return "[" + str(start) + ":" + str(stop) + "]" + s

            raise InternalSWError(f"Unknown {start} {stop}")
        else:
            return "[" + ",".join(str(i) for i in slices) + "]" + s

    def atomic_str(self) -> str:
        return self._add_to_str(super().atomic_str())

    def normalize_slice_index(self, n_max: int, _default: Iterable[int]) -> Iterable[int]:

        """
        We have no way to no what is max n
        :default in [1,n] space
        :return: below - (1,1)

            [i] -> (i, i)  - by  get_item
            None -> (None, None)

            (None, None) -> default
            (start, None) -> (start, n_max)
            (None, Stop) -> (1, stop)
            (start, stop) -> (1, stop)



        :return: [start, stop] in cube coordinates [0, size-2]
        """

        slices = self.slices

        res: Iterable[int]

        if slices is None:
            res = _default

        elif isinstance(slices, Sequence):
            res = slices

        elif isinstance(slices, slice):

            start = slices.start
            stop = slices.stop

            _stop = None
            _start = None

            if not start and not stop:

                res = _default

            else:
                if start and not stop:
                    _start, _stop = (start, n_max)

                elif not start and stop:
                    _start, _stop = (1, stop)

                else:
                    _start, _stop = (start, stop)

                assert _start
                assert _stop
                res = [*range(_start, _stop + 1)]
        else:
            res = _default

        return [i - 1 for i in res]

    def same_form(self, a: "SimpleAlg") -> bool:

        if not isinstance(a, SliceAbleAlg):
            return False

        my = self.slices
        other = a.slices
        if my is None and other is None:
            return True

        if my is not other:
            return False

        if isinstance(my, slice):
            s1 = my.start
            t1 = my.stop

            assert isinstance(other, slice)  # for my py and pyright
            s2 = other.start
            t2 = other.stop

            return (s1 is None and s2 is None or s1 == s2) and (t1 is None and t2 is None or t1 == t2)
        elif isinstance(my, Sequence):
            assert isinstance(other, Sequence)  # for my py
            # they are sorted
            return my == other
        else:
            raise InternalSWError(f"Unknown type for slices object {my}")
