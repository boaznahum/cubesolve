# Texture Rotation Bug Analysis

## Bug Description

When rotating a face with textures enabled, the texture appears scrambled after the rotation animation completes. The texture shows correctly during the animation but "snaps" to a broken state at the end.

## Root Cause

The animation system works as follows:
1. **Before rotation**: Geometry is compiled with current UV coordinates baked in
2. **During animation**: The compiled geometry is rotated visually using a matrix transform (no UV changes)
3. **After animation**: The actual cube model rotation happens (`copy_color` moves attributes between pieces)
4. **Then**: Geometry is rebuilt, reading UV values from the model

The attempted fix stored `home_uv` in `PartEdge.c_attributes`, which travels with pieces during rotation via `copy_color()`. This caused the UVs to move with pieces, resulting in a scrambled texture after rebuild.

## The Fundamental Misunderstanding

There are two valid approaches for texture mapping on a rotating cube:

### Approach A: Texture Fixed to Face (Position-based UVs)
- UV is determined by cell POSITION on the face, not which piece is there
- The "B" image stays in place while pieces rotate over it
- After rotation, pieces at new positions show that position's texture region
- **Simple to implement**: `UV = (col/size, row/size)`

### Approach B: Texture Travels with Piece (Piece-based UVs)
- Each piece has a fixed UV that travels with it
- The "B" image appears to rotate 90° when F face rotates
- Requires storing UV that survives rotation
- **Problem**: The animation shows the ORIGINAL UVs during animation (geometry baked before rotation), but after rotation the `c_attributes` have MOVED, causing a mismatch

## Why Approach B Failed

1. Animation compiles geometry with UVs at time T
2. Animation plays (visual rotation only)
3. Cube model rotates (attributes move via `copy_color`)
4. Geometry rebuilds at time T+1
5. At T+1, the piece at position (0,0) has `home_uv` from wherever it came from
6. This creates a discontinuity - animation showed one thing, final state shows another

## Correct Solution

For this codebase, **Approach A (position-based UVs)** is correct because:
- The per-COLOR grouping already ensures each color uses its home face's texture
- Green pieces always use F texture, orange pieces use L texture, etc.
- Position-based UVs mean the texture image stays fixed on the face
- No state needs to travel with pieces

```python
def _get_cell_uv(self, row: int, col: int, size: int) -> tuple:
    """UV based on position, not piece."""
    return (col / size, row / size, (col + 1) / size, (row + 1) / size)
```

## Key Insight

The `c_attributes` mechanism (which copies via `PartEdge.copy_color()`) is designed for attributes that should travel with piece COLORS. However, texture UVs should be tied to POSITION, not color. The animation system's separation of "visual rotation" from "model rotation" makes piece-based UVs particularly problematic.

## Files Involved

- `ModernGLCubeViewer.py` - Main viewer with texture rendering
- `PartEdge.py` - Contains `c_attributes` and `copy_color()`
- `_part_slice.py` - Contains `copy_colors()` which calls `PartEdge.copy_color()`
- `AnimationManager.py` - Orchestrates animation flow

## Lesson Learned

When debugging rendering issues in an animated system, always trace the FULL lifecycle:
1. When is geometry compiled?
2. What data is baked into the geometry?
3. When does the model state change?
4. When is geometry rebuilt?
5. What data is read during rebuild?

The mismatch between "what animation shows" and "what final state shows" often indicates a timing issue between visual updates and model updates.
