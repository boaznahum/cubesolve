from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Self, Sequence, final

from cube.domain.algs.SliceAbleAlg import SliceAbleAlg
from cube.domain.algs.SliceAlgBase import SliceAlgBase
from cube.domain.exceptions import InternalSWError
from cube.domain.model.cube_slice import SliceName

if TYPE_CHECKING:
    from cube.domain.algs.SlicedSliceAlg import SlicedSliceAlg
    from cube.domain.algs.SimpleAlg import SimpleAlg


class SliceAlg(SliceAlgBase, SliceAbleAlg, ABC):
    """
    Slice algorithm that CAN be sliced. M[1:2] returns SlicedSliceAlg.

    This class represents an unsliced slice algorithm (M, E, S).
    When sliced via __getitem__, it returns a SlicedSliceAlg which cannot
    be sliced again (type-level enforcement).

    All instances are frozen (immutable) after construction.

    When ALG_CACHE_ENABLED is True, only 4 instances exist per slice (n=0,1,2,3).
    The with_n() method returns cached instances instead of creating new ones.

    See SliceAlgBase for documentation on slice indexing conventions.
    """

    __slots__ = ()  # No additional slots - _slice_name is in SliceAlgBase

    # Cache: (concrete_class, n % 4) -> instance
    # Shared across all SliceAlg subclasses
    _instance_cache: ClassVar[dict[tuple[type, int], "SliceAlg"]] = {}

    def __init__(self, slice_name: SliceName, n: int = 1) -> None:
        super().__init__(slice_name, n)
        # Note: _freeze() is called by concrete subclasses

    def _register_in_cache(self) -> None:
        """Register this instance in the cache. Called after _freeze()."""
        from cube.application import _config as config
        if config.ALG_CACHE_ENABLED:
            key = (type(self), self._n % 4)
            if key not in self._instance_cache:
                self._instance_cache[key] = self

    @property
    def slices(self) -> None:
        """Return slice info. Always None for unsliced SliceAlg."""
        return None

    def with_n(self, n: int) -> Self:
        """
        Return instance with given n value.

        When ALG_CACHE_ENABLED: Returns cached instance (only 4 per slice).
        When disabled: Creates new instance each time.
        """
        from cube.application import _config as config

        n_norm = n % 4

        if config.ALG_CACHE_ENABLED:
            key = (type(self), n_norm)
            cached = self._instance_cache.get(key)
            if cached is not None:
                return cached  # type: ignore[return-value]
            # Create, cache, and return
            instance = self._create_with_n(n_norm)
            self._instance_cache[key] = instance
            return instance
        else:
            # Original behavior
            if n == self._n:
                return self
            return self._create_with_n(n)

    def _create_with_n(self, n: int) -> Self:
        """Create a new SliceAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_slice_name", self._slice_name)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def __getitem__(self, items: int | slice | Sequence[int]) -> "SlicedSliceAlg":
        """
        Slice this slice algorithm, returning a SlicedSliceAlg.

        The returned SlicedSliceAlg cannot be sliced again (no __getitem__).

        Args:
            items: Slice specification (int, slice, or sequence of ints)

        Returns:
            A new SlicedSliceAlg with the slice applied
        """
        from cube.domain.algs.SlicedSliceAlg import SlicedSliceAlg

        if not items:
            # Return self unchanged for empty slice? Or default?
            # Original behavior returned self, but we need to return SlicedSliceAlg
            # For empty items, return with default all slices
            return SlicedSliceAlg(self._slice_name, self._n, slice(None, None))

        a_slice: slice | Sequence[int]
        if isinstance(items, int):
            a_slice = slice(items, items)  # start/stop the same
        elif isinstance(items, slice):
            a_slice = items
        elif isinstance(items, Sequence):
            a_slice = sorted(items)
        else:
            raise InternalSWError(f"Unknown type for slice: {items} {type(items)}")

        return SlicedSliceAlg(self._slice_name, self._n, a_slice)

    @abstractmethod
    def get_base_alg(self) -> "SliceAlgBase":
        """Return whole slice alg that is not yet sliced."""
        pass

    def same_form(self, a: "SimpleAlg") -> bool:
        """Check if another alg has the same form (both unsliced)."""
        if not isinstance(a, SliceAlg):
            return False
        # Both are unsliced SliceAlg - same form
        return True


@final
class _M(SliceAlg):

    def __init__(self, n: int = 1) -> None:
        super().__init__(SliceName.M, n)
        self._freeze()
        self._register_in_cache()

    def get_base_alg(self) -> SliceAlgBase:
        from cube.domain.algs.Algs import Algs
        return Algs.M


@final
class _E(SliceAlg):
    """
    Middle slice over D
    """

    def __init__(self, n: int = 1) -> None:
        super().__init__(SliceName.E, n)
        self._freeze()
        self._register_in_cache()

    def get_base_alg(self) -> SliceAlgBase:
        from cube.domain.algs.Algs import Algs
        return Algs.E


@final
class _S(SliceAlg):
    """
    Middle slice over F
    """

    def __init__(self, n: int = 1) -> None:
        super().__init__(SliceName.S, n)
        self._freeze()
        self._register_in_cache()

    def get_base_alg(self) -> SliceAlgBase:
        from cube.domain.algs.Algs import Algs
        return Algs.S
