"""Single-entry cache implementations.

Architecture:
- Cache: Protocol for single-entry caches (holds 0 or 1 value)
  - CacheImpl: Actual single-value cache
  - CacheNull: Singleton, no caching, always calls factory
- CacheManager: Protocol for managing multiple Cache instances
  - CacheManagerImpl: Creates/manages CacheImpl instances by key
  - CacheManagerNull: Singleton, always returns CacheNull

The key insight: each Cache holds ONE value. The full cache key is passed
to CacheManager.get(), which returns a single-entry Cache for that key.

Usage::

    # Create CacheManager based on config
    manager = CacheManager.create(config)

    # Full key passed to get(), compute() has no key parameter
    cache = manager.get(("MyClass.method", arg1, arg2), MyType)
    value = cache.compute(lambda: expensive_computation())
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, Hashable, Protocol, TypeVar, runtime_checkable, Tuple

if TYPE_CHECKING:
    from cube.utils.config_protocol import ConfigProtocol

V = TypeVar('V')


@runtime_checkable
class Cache(Protocol[V]):
    """Protocol for single-entry cache implementations.

    A Cache holds at most ONE value. The key is determined when obtaining
    the cache from CacheManager.get(). This simplifies the interface:
    - CacheManager.get(full_key, type) -> returns Cache for that key
    - Cache.compute(factory) -> returns cached value or computes it

    Values cannot be None - the cache assumes all cached values are non-None.
    """

    def clear(self) -> None:
        """Clear the cached value."""
        ...

    def compute(self, factory: Callable[[], V], disable_cache: bool = False) -> V:
        """Get cached value or compute and cache it.

        Args:
            factory: Callable that produces the value if not cached
            disable_cache: If True, always call factory (bypass cache)

        Returns:
            The cached or newly computed value
        """
        ...


@dataclass
class CacheImpl(Cache[V], Generic[V]):
    """Single-entry cache implementation.

    Holds at most ONE cached value. The key is managed by CacheManager.
    Values cannot be None - use _has_value to distinguish "no value" from "cached None".

    Attributes:
        _type: The expected type of cached value (for documentation, not checked)
    """
    _type: type[V]
    _value: V | None = field(default=None, init=False)
    _has_value: bool = field(default=False, init=False)

    def clear(self) -> None:
        """Clear the cached value."""
        self._value = None
        self._has_value = False

    def compute(self, factory: Callable[[], V], disable_cache: bool = False) -> V:
        """Get cached value or compute and cache it.

        Args:
            factory: Callable that produces the value if not cached
            disable_cache: If True, always call factory (bypass cache)

        Returns:
            The cached or newly computed value

        Raises:
            RuntimeError: If cached or computed value is None
        """
        if not disable_cache and self._has_value:
            if self._value is None:
                raise RuntimeError("Cached value is None - cache does not support None values")
            return self._value

        value = factory()
        if value is None:
            raise RuntimeError("Factory returned None - cache does not support None values")
        self._value = value
        self._has_value = True
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

    def compute(self, factory: Callable[[], V], disable_cache: bool = False) -> V:
        """Always call factory and return result (no caching).

        Args:
            factory: Callable that produces the value
            disable_cache: Ignored (always bypasses cache anyway)

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

    def clear(self) -> None:
        """
        Clear the cache
        :return:
        """

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

    def clear(self) -> None:
        for caches in self._caches.values():
            # in case some hold reference to it it is not enough to clear the manager
            caches.clear()

        self._caches.clear()

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

    def clear(self) -> None:
        """No-op since CacheNull never stores anything."""
        pass

    def __getitem__(self, key_and_type: Tuple[Hashable, type[V]]) -> Cache[V]:
        """Always returns the CacheNull singleton.

        Args:
            key_and_type: Ignored

        Returns:
            The CacheNull singleton
        """
        return CacheNull.instance


CacheManagerNull.instance = CacheManagerNull()


# =============================================================================
# Decorator for documenting cached methods
# =============================================================================

F = TypeVar('F', bound=Callable[..., Any])


def cached_result(func: F) -> F:
    """Decorator to indicate that a method's result is cached.

    This is a documentation decorator - it marks methods whose results
    are cached by the CacheManager. The actual caching is done inside
    the method using cache_manager.get().compute().

    The decorator itself does NOT perform caching - it only marks the
    method so callers know the result is cached and they don't need
    to cache it themselves.

    Usage:
        @cached_result
        def get_something(self, arg1, arg2) -> SomeType:
            '''Method docstring.'''
            cache = self.cache_manager.get(("key", arg1, arg2), SomeType)
            return cache.compute(lambda: expensive_computation())
    """
    func._is_cached_result = True  # type: ignore[attr-defined]
    return func
