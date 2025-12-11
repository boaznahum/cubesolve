"""
Texture Rotation Config Loader

Loads texture_rotation_config.yaml - decision table for texture_direction updates.
Reloads on file change so you can edit while app runs.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_CONFIG_PATH = Path(__file__).parent / "texture_rotation_config.yaml"
_cached_config: dict[str, Any] | None = None
_cached_mtime: float = 0.0


def _load_config() -> dict[str, Any]:
    """Load config from YAML, using cache if file unchanged."""
    global _cached_config, _cached_mtime

    mtime = os.path.getmtime(_CONFIG_PATH)
    if _cached_config is not None and mtime == _cached_mtime:
        return _cached_config

    with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
        _cached_config = yaml.safe_load(f)
        _cached_mtime = mtime
        return _cached_config


def get_delta(rotating_face: str, target: str) -> int:
    """Get delta to add to texture_direction.

    Args:
        rotating_face: The rotating face ('F', 'R', etc.)
        target: 'self' or adjacent face name ('U', 'R', etc.)

    Returns:
        Delta value (0 = no update, 1/2/3 = add that amount)
    """
    config = _load_config()
    faces = config.get('faces', {})
    face_config = faces.get(rotating_face, {})
    return face_config.get(target, 0)


def reload_config() -> None:
    """Force reload of config file on next access."""
    global _cached_config, _cached_mtime
    _cached_config = None
    _cached_mtime = 0.0
