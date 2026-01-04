"""Generic cache implementations with type safety.

Provides Cache and CacheManager protocols with implementations:
- Cache: Protocol for individual caches
  - CacheImpl: Actual caching with type validation
  - CacheNull: Singleton, no caching, always calls factory
- CacheManager: Protocol for cache of caches
  - CacheManagerImpl: Creates/manages CacheImpl instances
  - CacheManagerNull: Singleton, always returns CacheNull

Usage::

    # Create CacheManager based on config
    manager = CacheManager.create(config)
    cache = manager.get("my_cache", str)

    value = cache.compute("key1", lambda: expensive_computation())
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, Hashable, Protocol, TypeVar, runtime_checkable, Tuple

if TYPE_CHECKING:
    from cube.utils.config_protocol import ConfigProtocol

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


class CacheNull(Cache[V]):
    """Null cache singleton - always calls factory, never caches.

    Useful for testing or when caching should be disabled.
    Since nothing is stored, a single instance works for all types.

    Usage::
        cache: Cache[str] = CacheNull.instance
    """
    instance: ClassVar[CacheNull[Any]]

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
        """
        return factory()


CacheNull.instance = CacheNull()


@runtime_checkable
class CacheManager(Protocol):
    """Protocol for cache manager - a cache of caches.

    Manages multiple Cache instances, each identified by a key.
    Use CacheManager.create(config) to get appropriate implementation.
    """

    @staticmethod
    def create(config: "ConfigProtocol") -> "CacheManager":
        """Factory: create appropriate CacheManager based on config.

        Args:
            config: Configuration protocol with enable_cube_cache flag

        Returns:
            CacheManagerImpl if caching enabled, CacheManagerNull otherwise
        """
        if config.enable_cube_cache:
            return CacheManagerImpl()
        return CacheManagerNull.instance

    def get(self, key: Hashable, value_type: type[V]) -> Cache[V]:
        """Get or create a cache for the given key and value type.

        Args:
            key: Hashable key identifying the cache
            value_type: The type of values the cache will store

        Returns:
            A Cache instance for the given key
        """
        ...

    def __getitem__(self, key_and_type: Tuple[Hashable, type[V]]) -> Cache[V]:
        """Bracket access: manager[key, MyType].

        Args:
            key_and_type: Tuple of (key, value_type)

        Returns:
            A Cache instance for the given key
        """
        ...


@dataclass
class CacheManagerImpl(CacheManager):
    """Actual cache manager - creates/returns CacheImpl instances.

    Maintains a dictionary of caches, creating new ones as needed.
    """
    _caches: dict[Hashable, Cache[Any]] = field(default_factory=dict, init=False)

    def get(self, key: Hashable, value_type: type[V]) -> Cache[V]:
        """Get or create a cache for the given key and value type.

        Args:
            key: Hashable key identifying the cache
            value_type: The type of values the cache will store

        Returns:
            A CacheImpl instance for the given key
        """
        if key not in self._caches:
            self._caches[key] = CacheImpl(value_type)
        return self._caches[key]  # type: ignore[return-value]

    def __getitem__(self, key_and_type: Tuple[Hashable, type[V]]) -> Cache[V]:
        """Bracket access: manager[key, MyType].

        Args:
            key_and_type: Tuple of (key, value_type)

        Returns:
            A CacheImpl instance for the given key
        """
        return self.get(key_and_type[0], key_and_type[1])


class CacheManagerNull(CacheManager):
    """Null cache manager singleton - always returns CacheNull.

    Useful for testing or when caching should be disabled globally.

    Usage::
        manager: CacheManager = CacheManagerNull.instance
    """
    instance: ClassVar[CacheManagerNull]

    def get(self, key: Hashable, value_type: type[V]) -> Cache[V]:
        """Always returns the CacheNull singleton.

        Args:
            key: Ignored
            value_type: Ignored

        Returns:
            The CacheNull singleton
        """
        return CacheNull.instance

    def __getitem__(self, key_and_type: Tuple[Hashable, type[V]]) -> Cache[V]:
        """Always returns the CacheNull singleton.

        Args:
            key_and_type: Ignored

        Returns:
            The CacheNull singleton
        """
        return CacheNull.instance


CacheManagerNull.instance = CacheManagerNull()
