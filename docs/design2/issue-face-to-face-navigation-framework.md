# Issue: Consistent Framework for Face-to-Face Navigation

## Background: Insights from Issue #53

This issue builds on the learnings from Issue #53 "Two edges may not agree in face coordinate system".

### Key Insight: Approach 2

The breakthrough understanding was:

> **Each face's ltr is consistent BY DEFINITION. Edges provide a translation layer.**

- Face ltr coordinates are face-owned, not edge-owned
- The edge's internal storage arbitrarily matches f1's perspective
- f2 translates through the edge (inverts if `same_direction=False`)
- No "agreement check" is needed - consistency is guaranteed by the translation layer

### Critical Discovery: M vs S Slice Behavior

**M Slice: NO Axis Exchange**
- Uses only horizontal edges: `edge_bottom` → `edge_top` on each face
- Stays as **COLUMN** on all 4 faces (F → U → B → D)
- Path: F(edge_bottom) → U(edge_bottom) → B(edge_top) → D(edge_bottom)

**S Slice: HAS Axis Exchange**
- Alternates between vertical and horizontal edges
- Switches between **ROW** and **COLUMN**:
  - U: ROW (vertical edge L-U)
  - R: COLUMN (horizontal edge U-R)
  - D: ROW (vertical edge D-R)
  - L: COLUMN (horizontal edge L-D)

### The Axis Rule

```
Horizontal edge (top/bottom) → ltr selects COLUMN
Vertical edge (left/right)   → ltr selects ROW
```

---

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

### Source Code
- `src/cube/domain/model/Slice.py` - Main slice rotation logic (lines 63-134)
- `src/cube/domain/model/Edge.py` - Edge translation methods (`get_ltr_index_from_slice_index`, `get_slice_index_from_ltr_index`)
- `src/cube/domain/model/Face.py` - Face edge relationships and rotation

### Documentation Created in Issue #53
- `docs/design2/edge-face-coordinate-system-approach2.md` - **Main documentation** for Approach 2
  - Face rotation with ltr coordinates
  - Slice rotation physical alignment
  - Axis exchange explanation (S slice)
  - `same_direction` flag determination

### Diagrams
All diagrams in `docs/design2/images/`:

| Diagram | Description |
|---------|-------------|
| `edge-coordinate-system.png` | Unfolded cube with R/T arrows and **ltr numbering (0→1→2)** on each edge |
| `face-rotation-ltr.png` | Face rotation showing ltr coordinate flow |
| `slice-rotation-axis-exchange.png` | **S slice** ROW↔COLUMN axis exchange (U→R) |
| `slice-physical-alignment.png` | Physical alignment across 4 faces |

### Diagram Generation Scripts
- `coor-system-doc/generate_edge_diagram.py` - Generates edge-coordinate-system.png
- `scripts/generate_ltr_diagrams.py` - Generates face-rotation and slice-rotation diagrams

### Hand-drawn Reference
- `coor-system-doc/right-top-left-coordinates.jpg` - Original hand-drawn R/T coordinate system

## Related Issues

- Issue #53: Two edges may not agree in face coordinate system (**CLOSED**)
  - Proved original approach geometrically impossible
  - Established Approach 2 as correct understanding
  - Removed obsolete `_validate_edge_coordinate_consistency` method
  - Deleted obsolete test `tests/model/test_edge_coordinate_consistency.py`

## Tasks

- [ ] Design `FaceNavigationContext` class
- [ ] Design `SlicePath` declarative definition
- [ ] Implement `FaceToFaceTranslator`
- [ ] Refactor `Slice._get_slices_by_index()` to use new framework
- [ ] Add comprehensive unit tests for navigation
- [ ] Update documentation with framework description

---

## Session Summary (Issue #53 Resolution)

### What Was Done
1. Analyzed original assumption that opposite edges must "agree" - proved **geometrically impossible**
2. Established **Approach 2**: Face ltr is consistent by definition, edges translate
3. Documented 7 usage cases of ltr methods - all match Approach 2
4. Created comprehensive documentation with ASCII and graphical diagrams
5. Fixed axis exchange diagram: changed from M slice (wrong) to S slice (correct)
6. Added ltr numbering (0→1→2) to edge-coordinate-system.png
7. Removed obsolete validation code and tests

### Key Code Locations
- Edge translation: `Edge.py:127-191`
- Slice navigation: `Slice.py:112-134`
- Axis detection: `Slice.py:98-108`
