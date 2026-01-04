"""Generic cache implementations with type safety.

Provides a Cache protocol and two implementations:
- CacheImpl: Actual caching with type validation
- CacheNull: No caching, always calls factory (useful for testing/debugging)

Usage::

    # Create a cache for strings
    cache: Cache[str] = CacheImpl(str)

    # Compute or retrieve cached value
    value = cache.compute("key1", lambda: expensive_computation())

    # Clear all cached values
    cache.clear()

    # Use null cache to disable caching
    null_cache: Cache[str] = CacheNull(str)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Generic, Hashable, Protocol, TypeVar, runtime_checkable

V = TypeVar('V')


@runtime_checkable
class Cache(Protocol[V]):
    """Protocol for cache implementations.

    Generic cache that stores values of type V, keyed by hashable keys.
    Implementations must provide clear() and compute() methods.
    """

    def clear(self) -> None:
        """Clear all cached values."""
        ...

    def compute(self, key: Hashable, factory: Callable[[], V]) -> V:
        """Get cached value or compute and cache it.

        Args:
            key: Hashable key to look up or store the value
            factory: Callable that produces the value if not cached

        Returns:
            The cached or newly computed value

        Raises:
            TypeError: If cached or computed value is not of expected type
        """
        ...


@dataclass
class CacheImpl(Cache[V], Generic[V]):
    """Actual cache implementation with type checking.

    Caches values and validates their types on retrieval and storage.

    Attributes:
        _type: The expected type of cached values
    """
    _type: type[V]
    _cache: dict[Hashable, V] = field(default_factory=dict, init=False)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def compute(self, key: Hashable, factory: Callable[[], V]) -> V:
        """Get cached value or compute and cache it.

        Args:
            key: Hashable key to look up or store the value
            factory: Callable that produces the value if not cached

        Returns:
            The cached or newly computed value

        Raises:
            TypeError: If cached or computed value is not of expected type
        """
        if key in self._cache:
            value = self._cache[key]
            if not isinstance(value, self._type):
                raise TypeError(
                    f"Cached value has wrong type: expected {self._type.__name__}, "
                    f"got {type(value).__name__}"
                )
            return value

        value = factory()
        if not isinstance(value, self._type):
            raise TypeError(
                f"Factory returned wrong type: expected {self._type.__name__}, "
                f"got {type(value).__name__}"
            )
        self._cache[key] = value
        return value


@dataclass
class CacheNull(Cache[V], Generic[V]):
    """Null cache - always calls factory, never caches.

    Useful for testing or when caching should be disabled.
    Still performs type validation on factory results.

    Attributes:
        _type: The expected type of values
    """
    _type: type[V]

    def clear(self) -> None:
        """No-op since nothing is cached."""
        pass

    def compute(self, key: Hashable, factory: Callable[[], V]) -> V:
        """Always call factory and return result (no caching).

        Args:
            key: Ignored (no caching)
            factory: Callable that produces the value

        Returns:
            The newly computed value

        Raises:
            TypeError: If computed value is not of expected type
        """
        value = factory()
        if not isinstance(value, self._type):
            raise TypeError(
                f"Factory returned wrong type: expected {self._type.__name__}, "
                f"got {type(value).__name__}"
            )
        return value
