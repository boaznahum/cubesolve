"""
Root test configuration.

Auto-applies the 'gui' marker to tests under directories that require
a display or browser (tests/gui/, tests/webgl/, tests/backends/).

Run non-GUI tests:  pytest tests/ -m "not gui and not slow"
Run GUI tests:      pytest tests/gui -v --speed-up 5
Run WebGL tests:    pytest tests/webgl -v
"""
from __future__ import annotations

from pathlib import Path

import pytest

# Directories whose tests should be marked as 'gui'
_GUI_DIRS = {"gui", "webgl"}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:  # noqa: ARG001
    """Auto-mark tests under gui/webgl/backends directories with the 'gui' marker."""
    tests_root = Path(__file__).parent
    gui_marker = pytest.mark.gui

    for item in items:
        # Check if any parent directory (relative to tests/) is a gui dir
        try:
            rel = item.path.relative_to(tests_root)
        except ValueError:
            continue
        if rel.parts and rel.parts[0] in _GUI_DIRS:
            item.add_marker(gui_marker)
