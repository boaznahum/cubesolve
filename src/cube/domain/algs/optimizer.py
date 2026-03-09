from collections.abc import Iterator, MutableSequence
from typing import Sequence

from cube.domain.algs.Alg import Alg
from cube.domain.algs.SeqAlg import SeqSimpleAlg
from cube.domain.algs.SimpleAlg import SimpleAlg


def simplify(self: Alg) -> SeqSimpleAlg:
    from cube.domain.algs.SeqAlg import SeqSimpleAlg
    from cube.domain.algs.SimpleAlg import SimpleAlg
    flat_algs: MutableSequence[SimpleAlg] = []

    algs: Iterator[SimpleAlg] = self.flatten()

    for a in algs:
        flat_algs.append(a)

    combined = _combine(flat_algs)
    return SeqSimpleAlg(None, *combined)


def _resolve_slices_to_set(slices: "slice | Sequence[int]") -> frozenset[int] | None:
    """Resolve a slice spec to an explicit set of indices.

    Returns None if the slices can't be fully resolved (e.g., open-ended slice).
    """
    if isinstance(slices, Sequence):
        return frozenset(slices)
    if isinstance(slices, slice):
        start, stop = slices.start, slices.stop
        if start is not None and stop is not None:
            return frozenset(range(start, stop + 1))
        if start is None and stop is not None:
            return frozenset(range(1, stop + 1))
    return None


def _try_merge_disjoint(prev: "NSimpleAlg", a: "NSimpleAlg") -> "NSimpleAlg | None":
    """Try to merge two sliced algs with same face, disjoint slices, and same n (mod 4).

    When two consecutive sliced algorithms operate on the same face/slice-name,
    have disjoint slice sets, and the same rotation count mod 4, they can be
    merged into a single algorithm operating on the union of their slices.

    For example: R[1,2]*1 + R[3,4]*1 -> R[1,2,3,4]*1

    Returns the merged alg, or None if merge is not possible.
    """
    from cube.domain.algs.SlicedFaceAlg import SlicedFaceAlg
    from cube.domain.algs.SlicedSliceAlg import SlicedSliceAlg

    if isinstance(prev, SlicedFaceAlg) and isinstance(a, SlicedFaceAlg):
        if prev._face != a._face:
            return None
    elif isinstance(prev, SlicedSliceAlg) and isinstance(a, SlicedSliceAlg):
        if prev._slice_name != a._slice_name:
            return None
    else:
        return None

    # Must have same rotation mod 4
    if prev.n % 4 != a.n % 4:
        return None

    s1 = _resolve_slices_to_set(prev._slices)
    s2 = _resolve_slices_to_set(a._slices)
    if s1 is None or s2 is None:
        return None

    # Must be disjoint (overlapping slices would get double rotation)
    if s1 & s2:
        return None

    union = sorted(s1 | s2)

    if isinstance(prev, SlicedFaceAlg):
        return SlicedFaceAlg(prev._face, prev.n, union)
    else:
        assert isinstance(prev, SlicedSliceAlg)
        return SlicedSliceAlg(prev._slice_name, prev.n, union)


def _combine(algs: Sequence[SimpleAlg]) -> Sequence[SimpleAlg]:

    from cube.domain.algs.SimpleAlg import NSimpleAlg, SimpleAlg

    work_to_do = bool(algs)
    while work_to_do:
        work_to_do = False
        new_algs: list[NSimpleAlg] = []
        prev: NSimpleAlg | None = None
        for a in algs:
            if not isinstance(a, NSimpleAlg):
                raise TypeError("Unexpected type", type(a))

            if not a.n % 4:  # get rid of R4
                continue

            if prev:
                if type(prev) is type(a) and prev.same_form(a):

                    assert isinstance(prev, SimpleAlg)

                    # Use with_n() to create new instance with combined n value
                    combined_n = prev.n + a.n
                    if combined_n % 4:
                        prev = a.with_n(combined_n)
                    else:
                        prev = None  # R0 is a None
                    work_to_do = True  # really ?
                else:
                    # Try merging disjoint slices of same face
                    merged = _try_merge_disjoint(prev, a)
                    if merged is not None:
                        prev = merged
                        work_to_do = True
                    else:
                        new_algs.append(prev)
                        prev = a

            else:
                prev = a

        if prev:
            new_algs.append(prev)

        algs = new_algs

    return algs
