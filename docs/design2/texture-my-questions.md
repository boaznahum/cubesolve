# Texture Rotation: Adjacent Pieces Geometry

## UV Mapping Overview

UV mapping assigns 2D texture coordinates (U, V) to 3D vertices. For each cell on the cube:
- The texture is mapped to a quad (4 corners)
- UV coordinates (0,0) to (1,1) map the texture to the quad
- Rotating UV coordinates rotates how the texture appears on the quad

## Texture Direction System

Each sticker tracks `texture_direction` (0-3) representing cumulative 90° CW rotations:
- direction=0 → Arrow points UP (no rotation)
- direction=1 → Arrow points RIGHT (90° CW)
- direction=2 → Arrow points DOWN (180°)
- direction=3 → Arrow points LEFT (270° CW)

UV_INDICES = [0, 3, 2, 1] maps direction to UV option for correct visual rotation.

## Adjacent Pieces: The Geometry Problem

When a face rotates, two types of stickers are affected:
1. **Stickers ON the rotating face** - always rotate by `quarter_turns`
2. **Adjacent stickers** - stickers on other faces at the edge of the rotating layer

The key insight: **adjacent stickers only need texture rotation when the rotation axis is perpendicular to their "up" direction**.

### Face Coordinate Systems

```
Face "Up" Directions (when viewing each face straight-on):
- F face: up = Y+ (toward top of screen)
- B face: up = Y+
- R face: up = Y+
- L face: up = Y+
- U face: up = Z- (toward back of cube)
- D face: up = Z+ (toward front of cube)
```

### Rotation Axes

```
- F, B faces rotate around Z axis
- U, D faces rotate around Y axis
- R, L faces rotate around X axis
```

### The Rule

**Adjacent texture rotation is needed when:**
- The rotation axis is **different** from the adjacent faces' "up" direction
- This causes the "up" vector to rotate in the viewing plane

**Adjacent texture rotation is NOT needed when:**
- The rotation axis **matches** the adjacent faces' "up" direction
- The "up" vector is preserved (rotation happens around it)

### Application to Each Face

| Rotating Face | Axis | Adjacent Faces | Adjacent "Up" | Needs Adjacent Update? |
|---------------|------|----------------|---------------|------------------------|
| F | Z | U, R, D, L | Y (R,L,D), Z (U) | YES - Z rotation changes Y |
| B | Z | U, R, D, L | Y (R,L,D), Z (U) | YES - Z rotation changes Y |
| U | Y | F, R, B, L | all Y | NO - Y rotation preserves Y |
| D | Y | F, R, B, L | all Y | NO - Y rotation preserves Y |
| R | X | F, U, B, D | Y (F,B), Z (U,D) | TBD - X rotation changes Y and Z |
| L | X | F, U, B, D | Y (F,B), Z (U,D) | TBD - X rotation changes Y and Z |

## Visual Example: F vs U Rotation

### F Rotation (Z-axis) - Adjacent stickers ROTATE

```
Before F CW:              After F CW:

    U face                   U face
    ↑ arrow                  → arrow (rotated 90° CW!)
    (direction=0)            (direction=1)

The arrow was pointing Y+ (up on U).
Z rotation: Y+ → X+ (right).
On U face, arrow now points right.
```

### U Rotation (Y-axis) - Adjacent stickers DON'T rotate

```
Before U CW:              After U CW:

    F face                   R face (sticker moved here)
    ↑ arrow                  ↑ arrow (same direction!)
    (direction=0)            (direction=0)

The arrow was pointing Y+ (up on F).
Y rotation: Y+ → Y+ (unchanged!).
On R face, arrow still points up.
```

## Code Implementation

In `Face._update_texture_directions_after_rotate()`:

```python
# Only F and B faces need adjacent sticker updates
# because they rotate around Z axis, which changes Y component
from cube.domain.model.cube_layout.cube_boy import FaceName

if self.name in (FaceName.F, FaceName.B):
    # Update adjacent edge and corner stickers
    for edge in [self._edge_top, ...]:
        adjacent_face = edge.get_other_face(self)
        for i in range(n_slices):
            part_edge_adj = edge.get_slice(i).get_face_edge(adjacent_face)
            part_edge_adj.rotate_texture(quarter_turns)
```

## Files Modified

| File | Change |
|------|--------|
| `Face.py` | `_update_texture_directions_after_rotate()` - conditional adjacent updates |
| `_modern_gl_cell.py` | UV_INDICES = [0, 3, 2, 1] for correct visual rotation |

## Empirical Testing Results (2025-12-11)

| Rotating Face | Adjacent Update Rule | Status |
|---------------|---------------------|--------|
| F | ALL adjacent | ✅ WORKS |
| U | NONE | ✅ WORKS |
| D | NONE | ✅ WORKS |
| L | ALL adjacent | ✅ WORKS |
| B | NONE | ✅ WORKS |
| R | F/B only (not U/D) | ❌ PARTIALLY BROKEN |

**Key Insight:** Geometric predictions don't fully match empirical results:
- F and L both need ALL adjacent updates (not matching predicted rule)
- R behaves differently than L despite being on same axis (X)
- B behaves differently than F despite being on same axis (Z)

The pattern suggests the rule depends on more than just rotation axis - possibly related to:
1. Edge coordinate system (`right_top_left_same_direction` flag)
2. How faces are "wired" to each other in cube initialization
3. Something asymmetric about the cube's internal structure

## Remaining Work

- [x] Test F face adjacent - WORKS (all adjacent)
- [x] Test U face adjacent - WORKS (no adjacent)
- [x] Test D face adjacent - WORKS (no adjacent)
- [x] Test L face adjacent - WORKS (all adjacent)
- [x] Test B face adjacent - WORKS (no adjacent)
- [ ] Fix R face adjacent - PARTIALLY BROKEN (needs investigation)
- [ ] Test middle slice movements (M, S, E)
- [ ] Test on larger cubes (5x5)


