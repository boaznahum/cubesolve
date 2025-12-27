# Face2FaceTranslator - Implementation Documentation

## Location
`src/cube/domain/model/Face2FaceTranslator.py`

Replaces scattered methods:
- `Edge.get_slice_index_from_ltr_index()`
- `Edge.get_ltr_index_from_slice_index()`
- `Face.is_bottom_or_top()` for axis detection
- `Slice.py` navigation logic

---

## Definition (Viewer Perspective)

**A coordinate (x, y) on Face A translates to (x', y') on Face B if:**

1. Place a marker at (x, y) on Face A - note where it appears on screen
2. Place a marker at (x', y') on Face B
3. Perform whole cube rotation to bring Face B to Face A's position
4. The marker at (x', y') now appears at the **EXACT SAME screen position** as (x, y) was originally

**The translated coordinate preserves VISUAL POSITION from the viewer's perspective.**

---

## Visual Example

```
BEFORE:                           AFTER Y' rotation:

    Front (F)       Right (R)         Front (was R)
   ┌───────┐       ┌───────┐         ┌───────┐
   │       │       │       │         │       │
   │   ●   │       │   ○   │   Y'    │   ○   │  ← marker at same
   │ (1,2) │       │(x',y')│   →     │       │    screen position!
   └───────┘       └───────┘         └───────┘

● = original marker at (1,2) on F
○ = translated marker at (x',y') on R
After Y': R comes to front, ○ appears where ● was
```

---

## API

### Main Class

```python
class Face2FaceTranslator:
    def __init__(self, cube: Cube) -> None:
        """Initialize with a cube instance."""

    def translate(
        self,
        source_face: Face,
        dest_face: Face,
        coord: tuple[int, int]
    ) -> FaceTranslationResult:
        """
        Translate a coordinate from source_face to dest_face.

        Args:
            source_face: The face where the coordinate is defined
            dest_face: The face we want the corresponding coordinate on
            coord: (row, col) position on source_face (0-indexed)

        Returns:
            FaceTranslationResult with destination coordinate and metadata
        """
```

### Result Dataclass

```python
@dataclass(frozen=True)
class FaceTranslationResult:
    dest_coord: tuple[int, int]     # (row, col) on dest_face
    shared_edge: Edge | None        # None if opposite faces
    is_adjacent: bool               # True if faces share an edge
    verification_rotation: str      # Whole-cube rotation for testing
    source_axis: Axis               # ROW or COLUMN on source
    dest_axis: Axis                 # ROW or COLUMN on dest
    axis_exchanged: bool            # True if ROW↔COLUMN swap
```

---

## Face Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                    FACE RELATIONSHIP MATRIX                      │
├─────────┬───────┬───────┬───────┬───────┬───────┬───────────────┤
│ From\To │   F   │   U   │   R   │   B   │   D   │       L       │
├─────────┼───────┼───────┼───────┼───────┼───────┼───────────────┤
│    F    │   -   │  adj  │  adj  │  opp  │  adj  │      adj      │
│    U    │  adj  │   -   │  adj  │  adj  │  opp  │      adj      │
│    R    │  adj  │  adj  │   -   │  adj  │  adj  │      opp      │
│    B    │  opp  │  adj  │  adj  │   -   │  adj  │      adj      │
│    D    │  adj  │  opp  │  adj  │  adj  │   -   │      adj      │
│    L    │  adj  │  adj  │  opp  │  adj  │  adj  │       -       │
└─────────┴───────┴───────┴───────┴───────┴───────┴───────────────┘

adj = adjacent (share edge, 1 whole-cube rotation to verify)
opp = opposite (no shared edge, 2 rotations through intermediate)
```

---

## Verification Rotations

The whole-cube rotation that brings `dest` to `source`'s position:

| Source | Dest | Verification Rotation |
|--------|------|----------------------|
| F | U | X |
| F | R | Y' |
| F | D | X' |
| F | L | Y |
| F | B | Y2 (or X2) |
| U | F | X' |
| U | R | Z' |
| U | B | X |
| U | L | Z |
| U | D | X2 (or Z2) |
| R | F | Y |
| R | U | Z |
| R | B | Y' |
| R | D | Z' |
| R | L | Y2 (or Z2) |
| ... | ... | ... |

---

## Test Strategy

### Test Matrix

| Dimension | Values | Count |
|-----------|--------|-------|
| Source faces | F, U, R, B, D, L | 6 |
| Dest faces | All except source (adjacent + opposite) | 5 per source |
| Face pairs | 6 × 5 | **30** |
| Cube sizes | 3, 4, 5, 6, 7, 8 | 6 |
| Positions per face | n² | 9, 16, 25, 36, 49, 64 |

**Total tests:** 30 pairs × (9+16+25+36+49+64) = 30 × 199 = **5,970 tests**

### Core Test: Viewer Perspective Verification

```python
def test_translation_viewer_perspective(cube, source_face, dest_face, coord):
    """
    THE DEFINITIVE TEST:

    1. Get translated coordinate AND whole-cube algorithm
    2. Put marker (c_attribute) at dest_coord on dest_face
    3. Execute whole-cube algorithm (brings dest to source position)
    4. Assert: marker appears at original coord on source face
    """
    translator = Face2FaceTranslator(cube)
    result = translator.translate(source_face, dest_face, coord)

    # Put marker at translated position on dest face
    dest_cell = dest_face.get_cell(result.dest_coord)
    dest_cell.c_attributes["marker"] = "HERE"

    # Execute whole-cube rotation (brings dest face to source position)
    cube.execute_alg(result.verification_rotation)

    # After rotation, check the face now at source's position
    # The marker should be at the original coord
    face_now_at_source_position = get_face_at_position(cube, source_face.name)
    cell = face_now_at_source_position.get_cell(coord)

    assert cell.c_attributes.get("marker") == "HERE"
```

### Test Cases

1. **All 30 face pairs** (24 adjacent + 6 opposite)
2. **All cube sizes:** 3, 4, 5, 6, 7, 8
3. **All positions** on each face (n² positions)
4. **Round-trip verification:** A→B→A returns original coord

---

## Implementation Status

- [x] Class structure created
- [x] Definition documented
- [ ] `_find_shared_edge()` - implemented (trivial)
- [ ] `_get_edge_position()` - implemented (trivial)
- [ ] `_translate_adjacent()` - TODO
- [ ] `_translate_opposite()` - TODO
- [ ] `_get_verification_rotation()` - TODO
- [ ] Unit tests - TODO (define with user)

---

## Related Files

- `Edge.py` - `get_slice_index_from_ltr_index()`, `get_ltr_index_from_slice_index()`
- `Face.py` - Edge accessors, coordinate methods
- `Slice.py` - Current navigation logic (to be refactored)
