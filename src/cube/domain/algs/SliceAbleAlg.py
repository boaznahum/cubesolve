from abc import ABC, abstractmethod
from typing import Any, Sequence


class SliceAbleAlg(ABC):
    """
    Marker ABC for algorithms that support slice indexing like R[1:3].

    This is a pure marker interface - FaceAlg and SliceAlg inherit from this
    to enable isinstance(alg, SliceAbleAlg) checks at runtime.

    Note: SlicedFaceAlg and SlicedSliceAlg do NOT inherit from this,
    so isinstance(R[1:2], SliceAbleAlg) returns False (can't slice again).
    """

    __slots__ = ()

    @abstractmethod
    def __getitem__(self, items: int | slice | Sequence[int]) -> Any:
        """Slice this algorithm. Returns a sliced variant that cannot be sliced again."""
        ...
