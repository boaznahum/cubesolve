# Issue: Consistent Framework for Face-to-Face Navigation

## Problem Statement

Currently, navigating between faces during slice rotations involves multiple concepts that are handled separately:
- Edge translation (ltr ↔ slice index)
- Axis exchange (ROW ↔ COLUMN)
- Physical alignment preservation
- `same_direction` flag handling

These are spread across `Edge.py`, `Face.py`, and `Slice.py` without a unified conceptual framework.

## Current Implementation

### Slice.py (lines 63-134)
Each slice type (M, E, S) has hardcoded starting face and edge:
```python
case SliceName.M:
    current_face = self.cube.front
    current_edge = current_face.edge_bottom

case SliceName.E:
    current_face = self.cube.right
    current_edge = current_face.edge_left

case SliceName.S:
    current_face = self.cube.up
    current_edge = current_face.edge_left
```

### Navigation Logic (Slice.py lines 126-134)
```python
next_edge = current_edge.opposite(current_face)
next_face = next_edge.get_other_face(current_face)

# Translate coordinates through edge
next_slice_index = next_edge.get_slice_index_from_ltr_index(current_face, current_index)
current_index = next_edge.get_ltr_index_from_slice_index(next_face, next_slice_index)
```

### Axis Detection (Slice.py lines 98-108)
```python
if current_face.is_bottom_or_top(current_edge):
    # Horizontal edge → ltr selects COLUMN
    _c = [center.get_center_slice((i, current_index)) for i in range(n_slices)]
else:
    # Vertical edge → ltr selects ROW
    _c = [center.get_center_slice((current_index, i)) for i in range(n_slices)]
```

## Proposed Framework

### 1. Navigation Context Object

Create a `FaceNavigationContext` that encapsulates:
```python
@dataclass
class FaceNavigationContext:
    face: Face
    entry_edge: Edge          # Edge we entered through
    exit_edge: Edge           # Edge we'll exit through (opposite)
    axis: Axis                # ROW or COLUMN on this face
    ltr_index: int            # Current position in ltr coordinates

    def navigate_to_next(self) -> 'FaceNavigationContext':
        """Create context for next face in rotation."""
        ...
```

### 2. Axis Determination Rule

Formalize the rule:
- **Horizontal edge** (top/bottom) → slice is a **COLUMN** (ltr selects which column)
- **Vertical edge** (left/right) → slice is a **ROW** (ltr selects which row)

### 3. Slice Path Definition

Define each slice's path declaratively:
```python
SLICE_PATHS = {
    SliceName.M: SlicePath(
        start_face='F',
        start_edge='bottom',
        direction='clockwise',  # F→U→B→D
        edge_type='horizontal'  # Always horizontal → always COLUMN
    ),
    SliceName.S: SlicePath(
        start_face='U',
        start_edge='left',
        direction='clockwise',  # U→R→D→L
        edge_type='alternating'  # vertical→horizontal→vertical→horizontal
    ),
    ...
}
```

### 4. Unified Translation Interface

```python
class FaceToFaceTranslator:
    """Handles all face-to-face coordinate translation."""

    def translate(self,
                  from_face: Face,
                  to_face: Face,
                  through_edge: Edge,
                  ltr_index: int) -> tuple[int, Axis]:
        """
        Returns (new_ltr_index, new_axis) for the destination face.
        """
        ...
```

## Benefits

1. **Single source of truth** for navigation rules
2. **Easier debugging** - can trace navigation step by step
3. **Extensible** - easy to add new slice types or custom rotations
4. **Testable** - can unit test navigation logic independently
5. **Documentation** - framework serves as executable documentation

## Related Files

- `src/cube/domain/model/Slice.py` - Main slice rotation logic
- `src/cube/domain/model/Edge.py` - Edge translation methods
- `src/cube/domain/model/Face.py` - Face edge relationships
- `docs/design2/edge-face-coordinate-system-approach2.md` - Current documentation

## Related Issues

- Issue #53: Two edges may not agree in face coordinate system (CLOSED)

## Tasks

- [ ] Design `FaceNavigationContext` class
- [ ] Design `SlicePath` declarative definition
- [ ] Implement `FaceToFaceTranslator`
- [ ] Refactor `Slice._get_slices_by_index()` to use new framework
- [ ] Add comprehensive unit tests for navigation
- [ ] Update documentation with framework description
