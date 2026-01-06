from abc import ABC
from typing import TYPE_CHECKING, ClassVar, Self, Sequence, final

from cube.domain.algs.FaceAlgBase import FaceAlgBase
from cube.domain.algs.SliceAbleAlg import SliceAbleAlg
from cube.domain.exceptions import InternalSWError
from cube.domain.model import FaceName

if TYPE_CHECKING:
    from cube.domain.algs.SlicedFaceAlg import SlicedFaceAlg
    from cube.domain.algs.SimpleAlg import SimpleAlg


class FaceAlg(FaceAlgBase, SliceAbleAlg, ABC):
    """
    Face algorithm that CAN be sliced. R[1:2] returns SlicedFaceAlg.

    This class represents an unsliced face algorithm (R, L, U, D, F, B).
    When sliced via __getitem__, it returns a SlicedFaceAlg which cannot
    be sliced again (type-level enforcement).

    All instances are frozen (immutable) after construction.

    When ALG_CACHE_ENABLED is True, only 4 instances exist per face (n=0,1,2,3).
    The with_n() method returns cached instances instead of creating new ones.
    """

    __slots__ = ()  # No additional slots - _face is in FaceAlgBase

    # Cache: (concrete_class, n % 4) -> instance
    # Shared across all FaceAlg subclasses
    _instance_cache: ClassVar[dict[tuple[type, int], "FaceAlg"]] = {}

    def __init__(self, face: FaceName, n: int = 1) -> None:
        super().__init__(face, n)
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
        """Return slice info. Always None for unsliced FaceAlg."""
        return None

    def with_n(self, n: int) -> Self:
        """
        Return instance with given n value.

        When ALG_CACHE_ENABLED: Returns cached instance (only 4 per face).
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
        """Create a new FaceAlg with the given n value."""
        instance: Self = object.__new__(type(self))
        object.__setattr__(instance, "_frozen", False)
        object.__setattr__(instance, "_code", self._code)
        object.__setattr__(instance, "_n", n)
        object.__setattr__(instance, "_face", self._face)
        object.__setattr__(instance, "_frozen", True)
        return instance

    def __getitem__(self, items: int | slice | Sequence[int]) -> "SlicedFaceAlg":
        """
        Slice this face algorithm, returning a SlicedFaceAlg.

        The returned SlicedFaceAlg cannot be sliced again (no __getitem__).

        Args:
            items: Slice specification (int, slice, or sequence of ints)

        Returns:
            A new SlicedFaceAlg with the slice applied
        """
        from cube.domain.algs.SlicedFaceAlg import SlicedFaceAlg

        if not items:
            # Return a SlicedFaceAlg with default slice
            return SlicedFaceAlg(self._face, self._n, slice(1, 1))

        a_slice: slice | Sequence[int]
        if isinstance(items, int):
            a_slice = slice(items, items)  # start/stop the same
        elif isinstance(items, slice):
            a_slice = items
        elif isinstance(items, Sequence):
            a_slice = sorted(items)
        else:
            raise InternalSWError(f"Unknown type for slice: {items} {type(items)}")

        return SlicedFaceAlg(self._face, self._n, a_slice)

    def same_form(self, a: "SimpleAlg") -> bool:
        """Check if another alg has the same form (both unsliced)."""
        if not isinstance(a, FaceAlg):
            return False
        # Both are unsliced FaceAlg - same form if same face
        return True


@final
class _U(FaceAlg):

    def __init__(self, n: int = 1) -> None:
        super().__init__(FaceName.U, n)
        self._freeze()
        self._register_in_cache()


@final
class _D(FaceAlg):

    def __init__(self, n: int = 1) -> None:
        super().__init__(FaceName.D, n)
        self._freeze()
        self._register_in_cache()


@final
class _F(FaceAlg):

    def __init__(self, n: int = 1) -> None:
        super().__init__(FaceName.F, n)
        self._freeze()
        self._register_in_cache()


@final
class _B(FaceAlg):

    def __init__(self, n: int = 1) -> None:
        super().__init__(FaceName.B, n)
        self._freeze()
        self._register_in_cache()


@final
class _R(FaceAlg):

    def __init__(self, n: int = 1) -> None:
        super().__init__(FaceName.R, n)
        self._freeze()
        self._register_in_cache()


@final
class _L(FaceAlg):

    def __init__(self, n: int = 1) -> None:
        super().__init__(FaceName.L, n)
        self._freeze()
        self._register_in_cache()
