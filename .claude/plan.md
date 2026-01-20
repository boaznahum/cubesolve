# Plan: Add PartSliceTracker

## Goal
Create a `PartSliceTracker[PS]` class that tracks a specific `PartSlice` through cube rotations using the existing marker mechanism.

## Usage Pattern
```python
# Via static method
with PartSliceTracker.with_tracker(edge_wing) as t:
    # edge_wing may have moved
    current = t.slice  # finds it by marker

# Via convenience method on PartSlice
with edge_wing.tracker() as t:
    current = t.slice
```

## Design

### Key Pattern (from existing trackers)
- Key format: `_part_slice_track:{unique_id}`
- Store key in `edge.moveable_attributes[key] = True`
- Search by iterating all slices, checking for key in `edge.moveable_attributes`
- Cleanup removes the key

### New File: `src/cube/domain/solver/common/tracker/PartSliceTracker.py`

```python
from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Generic
from contextlib import contextmanager

from cube.domain.model.PartSlice import PartSlice

PS = TypeVar("PS", bound=PartSlice)

_PART_SLICE_TRACKER_PREFIX = "_part_slice_track:"

class PartSliceTracker(Generic[PS]):
    """Tracks a PartSlice through cube rotations using markers."""

    __slots__ = ["_cube", "_key", "_slice_type"]

    _global_id: int = 0

    def __init__(self, part_slice: PS) -> None:
        PartSliceTracker._global_id += 1
        self._key = f"{_PART_SLICE_TRACKER_PREFIX}{PartSliceTracker._global_id}"
        self._cube = part_slice.cube
        self._slice_type = type(part_slice)

        # Mark the first edge
        part_slice.edges[0].moveable_attributes[self._key] = True

    @staticmethod
    def with_tracker(part_slice: PS) -> "PartSliceTracker[PS]":
        """Create a tracker for the given part slice."""
        return PartSliceTracker(part_slice)

    @property
    def slice(self) -> PS:
        """Find and return the tracked slice by searching for the marker."""
        # TODO: add caching later
        for s in self._cube.get_all_parts():
            if isinstance(s, self._slice_type):
                for edge in s.edges:
                    if self._key in edge.moveable_attributes:
                        return s  # type: ignore
        raise RuntimeError(f"Tracked slice not found with key {self._key}")

    def cleanup(self) -> None:
        """Remove the marker from the slice."""
        for s in self._cube.get_all_parts():
            for edge in s.edges:
                if self._key in edge.moveable_attributes:
                    del edge.moveable_attributes[self._key]
                    return

    def __enter__(self) -> "PartSliceTracker[PS]":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()
```

### Modify: `src/cube/domain/model/PartSlice.py`

Add convenience method to `PartSlice`:
```python
def tracker(self: _TPartSlice) -> "PartSliceTracker[_TPartSlice]":
    """Create a tracker context manager for this slice."""
    from cube.domain.solver.common.tracker.PartSliceTracker import PartSliceTracker
    return PartSliceTracker.with_tracker(self)
```

### Export from `__init__.py`
Add `PartSliceTracker` to the tracker package exports.

## Files to Create/Modify
1. **Create**: `src/cube/domain/solver/common/tracker/PartSliceTracker.py` - new tracker class
2. **Modify**: `src/cube/domain/solver/common/tracker/__init__.py` - export PartSliceTracker
3. **Modify**: `src/cube/domain/model/PartSlice.py` - add `.tracker()` convenience method

## Notes
- First phase: no caching in `slice` property (TODO for later)
- Use `edges[0]` for marker storage (simpler than iterating)
- Generic `PS` type preserves the specific slice type (`EdgeWing`, `CenterSlice`, etc.)
