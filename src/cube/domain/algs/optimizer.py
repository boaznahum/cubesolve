from collections.abc import Iterator, MutableSequence
from typing import Sequence

from cube.domain.algs.Alg import Alg
from cube.domain.algs.SeqAlg import SeqSimpleAlg
from cube.domain.algs.SimpleAlg import NSimpleAlg, SimpleAlg


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


def _create_sliced_alg(template: "NSimpleAlg", slices: list[int], n: int) -> "NSimpleAlg":
    """Create a new sliced alg with the given slices and n, preserving face/slice-name from template."""
    from cube.domain.algs.SlicedFaceAlg import SlicedFaceAlg
    from cube.domain.algs.SlicedSliceAlg import SlicedSliceAlg

    if isinstance(template, SlicedFaceAlg):
        return SlicedFaceAlg(template._face, n, slices)
    else:
        assert isinstance(template, SlicedSliceAlg)
        return SlicedSliceAlg(template._slice_name, n, slices)


def _try_merge_disjoint(prev: "NSimpleAlg", a: "NSimpleAlg") -> "tuple[NSimpleAlg, NSimpleAlg | None] | None":
    """Try to merge two sliced algs with same face and disjoint slices.

    When two consecutive sliced algorithms operate on the same face/slice-name
    and have disjoint slice sets, they can be merged by extracting the common
    minimum rotation:

        S1*N1 & S2*N2 -> (S1∪S2)*N & S_larger*(N_larger - N)
        where N = min(N1, N2)

    When N1 ≡ N2 (mod 4), the remainder vanishes: 2 algs -> 1 alg.
    When N1 ≢ N2 (mod 4), we get union + remainder: 2 algs -> 2 algs,
    but the rearranged slices enable cascading merges with subsequent algs.

    Returns (union_alg, remainder_alg_or_None), or None if merge is not possible.
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

    s1 = _resolve_slices_to_set(prev._slices)
    s2 = _resolve_slices_to_set(a._slices)
    if s1 is None or s2 is None:
        return None

    # Must be disjoint (overlapping slices would get double rotation)
    if s1 & s2:
        return None

    n1, n2 = prev.n, a.n
    n_min = min(n1, n2)
    union = sorted(s1 | s2)

    # Union alg with the minimum n (always valid since both n1,n2 are non-zero mod 4)
    union_alg = _create_sliced_alg(prev, union, n_min)

    # Remainder: the set with larger n keeps the difference
    n_remainder = max(n1, n2) - n_min
    remainder_alg: NSimpleAlg | None = None
    if n_remainder % 4:
        remainder_slices = sorted(s1 if n1 > n2 else s2)
        remainder_alg = _create_sliced_alg(prev, remainder_slices, n_remainder)

    return union_alg, remainder_alg


def _combine(algs: Sequence[SimpleAlg]) -> Sequence[SimpleAlg]:

    from cube.domain.algs.SimpleAlg import NSimpleAlg, SimpleAlg

    work_to_do = bool(algs)
    while work_to_do:
        work_to_do = False
        new_algs: list[SimpleAlg] = []
        prev: NSimpleAlg | None = None
        for a in algs:
            if not isinstance(a, NSimpleAlg):
                # Non-combinable alg (e.g. HeadingAlg) — flush prev, pass through
                if prev:
                    new_algs.append(prev)
                    prev = None
                new_algs.append(a)
                continue

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
                    result = _try_merge_disjoint(prev, a)
                    if result is not None:
                        union_alg, remainder_alg = result
                        new_algs.append(union_alg)
                        prev = remainder_alg  # None if no remainder
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
