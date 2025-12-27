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

**A coordinate (row, col) on Face A translates to (row', col') on Face B if:**

1. Place a marker at (row', col') on Face B
2. Perform whole cube rotation to bring Face B to Face A's position
3. The marker now appears at the **EXACT SAME screen position** as (row, col) on A

**Key Finding:** For this definition, `(row', col') = (row, col)` for ALL face pairs!

The cube model's coordinate system is designed so that (row, col) on any face
corresponds to the same screen position when that face becomes the front.

---

## Visual Example

```
translate(F, U, (1,2)) → dest_coord=(1,2), whole_cube_alg="X'"

BEFORE:                           AFTER X' rotation:

    Front (F)        Up (U)           Front (was U)
   ┌───────┐       ┌───────┐         ┌───────┐
   │       │       │   ●   │         │   ●   │  ← marker at same
   │ (1,2) │       │ (1,2) │   X'    │ (1,2) │    screen position!
   │       │       │       │   →     │       │
   └───────┘       └───────┘         └───────┘

● = marker at (1,2) on U
After X': U comes to front, marker appears at screen position (1,2)
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
            source_face: Face where the original coordinate is defined
            dest_face: Face we want the corresponding coordinate on
            coord: (row, col) position on source_face (0-indexed)

        Returns:
            FaceTranslationResult with destination coordinate and metadata
        """
```

### Result Dataclass

```python
@dataclass(frozen=True)
class FaceTranslationResult:
    dest_coord: tuple[int, int]  # (row, col) on dest_face
    whole_cube_alg: str          # Algorithm to bring dest to source's position
    shared_edge: Edge | None     # Edge connecting faces (None if opposite)

    @property
    def is_adjacent(self) -> bool:
        """True if faces share an edge, False if opposite."""
        return self.shared_edge is not None
```

---

## Whole-Cube Algorithms

The `whole_cube_alg` brings dest_face to source_face's screen position.
Algorithms are **derived dynamically** from rotation cycles:

```python
X_CYCLE = [F, U, B, D]  # X: F→U→B→D→F
Y_CYCLE = [F, R, B, L]  # Y: F→R→B→L→F
Z_CYCLE = [U, R, D, L]  # Z: U→R→D→L→U
```

To find the algorithm for (source, dest):
1. Find which cycle contains both faces
2. Count steps from dest to source in cycle direction
3. steps=1 → axis, steps=2 → axis2, steps=3 → axis'

| Source | Dest | Algorithm | Derivation |
|--------|------|-----------|------------|
| F | U | X' | X_CYCLE: U→F is 3 steps |
| F | R | Y' | Y_CYCLE: R→F is 3 steps |
| F | D | X | X_CYCLE: D→F is 1 step |
| F | L | Y | Y_CYCLE: L→F is 1 step |
| F | B | X2 or Y2 | 2 steps on either cycle |

---

## Test Coverage

### Test Matrix
- **Face pairs:** All 30 (6 sources × 5 destinations)
- **Cube sizes:** 3, 4, 5, 6, 7, 8
- **Positions:** All center slices on each face

### Test Logic
```python
# For each (source_face, dest_face, coord):
result = translator.translate(source_face, dest_face, coord)

# Place marker at dest_coord on dest_face
dest_slice = dest_face.center.get_center_slice(result.dest_coord)
dest_slice.edge.attributes["marker"] = "X"

# Execute whole-cube rotation
cube.x_rotate(-1)  # or y_rotate, z_rotate as per whole_cube_alg

# Verify marker is at original coord on dest_face
check_slice = dest_face.center.get_center_slice(coord)
assert check_slice.edge.attributes.get("marker") == "X"
```

---

## Implementation Notes

1. **Identity Transform:** All 30 face pairs use identity transform because the cube's
   coordinate system is consistent across faces from the viewer's perspective.

2. **Dynamic Algorithm Derivation:** Whole-cube algorithms are computed from rotation
   cycles, not hardcoded. This reduces maintenance and ensures consistency.

3. **Marker Persistence:** Use `edge.attributes` (not `c_attributes`) for markers
   during testing, as `c_attributes` are cleared during rotations.

4. **Face Objects vs Colors:** Whole-cube rotations move colors between faces but
   face objects remain fixed. The `dest_face` object stays the same after rotation.

---

## Related Files

- `Cube.py` - `x_rotate()`, `y_rotate()`, `z_rotate()` for whole-cube rotations
- `Face.py` - Face coordinates and center access
- `Center.py` - `get_center_slice((row, col))` for accessing positions
- `_part_slice.py` - CenterSlice with `edge.attributes` for markers
