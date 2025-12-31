# Physical Face Preserver - Design Document

**Status: IMPLEMENTED**

## Problem Statement

Face trackers mark center slices on even cubes to track "which color belongs on which physical face". When algorithms like commutators move center pieces, the markers move WITH the pieces. For commutators that preserve the cage (cube orientation is preserved after execution), we need a way to restore markers to their original physical faces.

### Example Scenario

1. Marker on UP face tracking WHITE
2. Commutator moves centers (to solve them)
3. Marker now on FRONT face (followed the piece)
4. But we want marker back on UP face (same physical position)

## Solution: Polymorphic Save/Restore

Each tracker type handles its own save/restore logic because different trackers have different rules:

| Tracker Type | Behavior | Save | Restore |
|--------------|----------|------|---------|
| SimpleFaceTracker (odd cube) | Uses fixed center predicate | No-op | No-op |
| SimpleFaceTracker (opposite) | Follows primary tracker | No-op | No-op |
| SimpleFaceTracker (f5_boy) | Uses BOY validation | No-op | No-op |
| MarkedFaceTracker (even cube) | Marks center slice | Save `FaceName` | Cleanup + re-mark on saved face |

## Design

### Base Class Changes (`_base.py`)

```python
class FaceTracker(ABC):
    # ... existing ...

    def save_physical_face(self) -> FaceName:
        """Save current physical face for later restoration."""
        return self.face.name

    def restore_to_physical_face(self, saved_face_name: FaceName) -> None:
        """Restore tracker to the saved physical face.

        Default: no-op (SimpleFaceTracker predicates are stable)
        Override in MarkedFaceTracker.
        """
        pass


class SimpleFaceTracker(FaceTracker):
    # No override needed - predicates remain stable through rotations
    pass


class MarkedFaceTracker(FaceTracker):

    def restore_to_physical_face(self, saved_face_name: FaceName) -> None:
        """Remove current marker, create new marker on saved physical face."""
        # 1. Cleanup existing marker
        self.cleanup()

        # 2. Find face by saved name
        face = self._cube.face(saved_face_name)

        # 3. Find a center slice to mark on that face
        center_slice = self._find_markable_center_slice(face)

        # 4. Mark it with our color (reuse existing key)
        center_slice.edge.c_attributes[self._key] = self._color

    def _find_markable_center_slice(self, face: Face) -> CenterSlice:
        """Find a center slice on the given face to mark.

        Prefers a slice matching our target color if available.
        """
        for s in face.center.all_slices:
            if s.color == self._color:
                return s
        return next(iter(face.center.all_slices))
```

### FacesTrackerHolder Context Manager

```python
from contextlib import contextmanager
from typing import Iterator
from typing_extensions import Self

class FacesTrackerHolder:
    # ... existing ...

    @contextmanager
    def preserve_physical_faces(self) -> Iterator[Self]:
        """Context manager preserving face->color mapping across operations.

        Use when running algorithms (like commutators) that:
        1. Move center pieces (which moves markers)
        2. Preserve the cage (cube orientation unchanged after)

        Each tracker saves/restores according to its own rules:
        - SimpleFaceTracker: no-op (predicates are stable)
        - MarkedFaceTracker: saves face name, restores marker to same face

        Usage:
            with holder.preserve_physical_faces():
                commutator.execute()  # Moves centers
            # Markers now restored to original physical faces
        """
        # Save state for each tracker
        saved_states: list[FaceName] = [
            tracker.save_physical_face() for tracker in self._trackers
        ]

        try:
            yield self
        finally:
            # Restore each tracker to its saved physical face
            for tracker, saved_face in zip(self._trackers, saved_states):
                tracker.restore_to_physical_face(saved_face)

            # Invalidate cache (cube state changed)
            self._cache = None
```

## Usage Example

```python
with FacesTrackerHolder(solver) as holder:
    # Initial state: markers on their detected faces
    print(holder.face_colors)  # {UP: WHITE, FRONT: RED, ...}

    with holder.preserve_physical_faces():
        # Run commutator that moves centers
        alg = commutator.create_algorithm()
        alg.play()
        # Markers may have moved to different physical faces

    # After context: markers restored to original physical faces
    # UP still tracked as WHITE, FRONT still tracked as RED
    print(holder.face_colors)  # {UP: WHITE, FRONT: RED, ...}
```

## Why Polymorphic Design?

1. **SimpleFaceTracker doesn't need restoration** - its predicates (fixed center position, opposite face, BOY validation) remain valid through any rotation

2. **MarkedFaceTracker needs restoration** - the marker physically moves with the piece, so we must remove it and re-mark on the original face

3. **Encapsulation** - each tracker type knows its own rules, FacesTrackerHolder doesn't need to know implementation details

4. **Extensibility** - future tracker types can define their own save/restore behavior

## Implementation Notes

1. **Key reuse**: MarkedFaceTracker reuses its existing `_key` when re-marking, maintaining holder ID and uniqueness

2. **Slice selection**: When re-marking, prefer a slice matching the target color (if available on that face)

3. **Cache invalidation**: Must invalidate FacesTrackerHolder cache after restoration since tracker->face mappings changed

4. **Exception safety**: `finally` block ensures restoration happens even if operation raises
