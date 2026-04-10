"""Tests that CONFIG_DEFAULTS is deeply frozen and immutable.

Verifies that the freeze mechanism blocks mutations at all levels:
- Top-level field writes
- Nested dataclass field writes
- Dict mutations (MappingProxyType)
- List mutations (converted to tuple)
- Copy returns fully mutable ConfigData
"""
from __future__ import annotations

import pytest

from cube.application._config import CONFIG_DEFAULTS, ConfigData


class TestConfigDefaultsFrozen:
    """CONFIG_DEFAULTS must be immutable at runtime."""

    def test_top_level_field_write_raises(self) -> None:
        """Setting a top-level field on CONFIG_DEFAULTS raises RuntimeError."""
        with pytest.raises(RuntimeError, match="read-only"):
            CONFIG_DEFAULTS.check_cube_sanity = True  # type: ignore[misc]

    def test_nested_dataclass_field_write_raises(self) -> None:
        """Setting a field on a nested dataclass raises RuntimeError."""
        with pytest.raises(RuntimeError, match="read-only"):
            CONFIG_DEFAULTS.arrow_config.enabled = True  # type: ignore[misc]

    def test_dict_field_mutation_raises(self) -> None:
        """Mutating a dict field (MappingProxyType) raises TypeError."""
        keys = list(CONFIG_DEFAULTS.ss_codes.keys())
        assert len(keys) > 0, "ss_codes should have entries"
        with pytest.raises(TypeError):
            CONFIG_DEFAULTS.ss_codes[keys[0]] = True  # type: ignore[index]

    def test_list_field_is_tuple(self) -> None:
        """List fields are converted to tuples (immutable)."""
        assert isinstance(CONFIG_DEFAULTS.celebration_effects, tuple)

    def test_list_field_mutation_raises(self) -> None:
        """Appending to a list field (now tuple) raises AttributeError."""
        with pytest.raises(AttributeError):
            CONFIG_DEFAULTS.celebration_effects.append("x")  # type: ignore[attr-defined]


class TestConfigDefaultsCopy:
    """CONFIG_DEFAULTS.copy() must return a fully mutable ConfigData."""

    def test_copy_returns_config_data(self) -> None:
        """copy() returns a ConfigData instance (not frozen)."""
        c = CONFIG_DEFAULTS.copy()
        assert isinstance(c, ConfigData)

    def test_copy_top_level_mutable(self) -> None:
        """Top-level fields on the copy can be mutated."""
        c = CONFIG_DEFAULTS.copy()
        c.check_cube_sanity = True
        assert c.check_cube_sanity is True

    def test_copy_does_not_affect_original(self) -> None:
        """Mutating the copy does not affect CONFIG_DEFAULTS."""
        c = CONFIG_DEFAULTS.copy()
        original = CONFIG_DEFAULTS.check_cube_sanity
        c.check_cube_sanity = not original
        assert CONFIG_DEFAULTS.check_cube_sanity == original

    def test_copy_nested_dataclass_mutable(self) -> None:
        """Nested dataclass fields on the copy can be mutated."""
        c = CONFIG_DEFAULTS.copy()
        c.arrow_config.enabled = True
        assert c.arrow_config.enabled is True

    def test_copy_dict_mutable(self) -> None:
        """Dict fields on the copy are plain dicts (mutable)."""
        c = CONFIG_DEFAULTS.copy()
        assert isinstance(c.ss_codes, dict)
        keys = list(c.ss_codes.keys())
        c.ss_codes[keys[0]] = True
        assert c.ss_codes[keys[0]] is True

    def test_copy_list_mutable(self) -> None:
        """List fields on the copy are plain lists (mutable)."""
        c = CONFIG_DEFAULTS.copy()
        assert isinstance(c.celebration_effects, list)
        c.celebration_effects.append("test")
        assert "test" in c.celebration_effects

    def test_copy_listeners_empty(self) -> None:
        """Copy has empty listener list (listeners are not shared)."""
        c = CONFIG_DEFAULTS.copy()
        assert c._listeners == []

    def test_copy_listeners_work(self) -> None:
        """Listeners can be added to the copy and fire correctly."""
        c = CONFIG_DEFAULTS.copy()
        events: list[tuple[str, object]] = []
        c.add_listener(lambda f, v: events.append((f, v)))
        c.set_solver_debug(False)
        assert len(events) == 1
        assert events[0] == ("solver_debug", False)
