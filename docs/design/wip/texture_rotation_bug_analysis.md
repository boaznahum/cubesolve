# Texture Rotation Bug Analysis

## Status: IN PROGRESS (2025-12-11)

Face rotations (F, R, U, D, L, B) and slice rotations (M, E, S) work correctly.
Whole-cube rotations (X, Y, Z) need investigation - texture updates may not sum correctly.

## Quick Start for Next Session

1. Run the app: `python -m cube.main_pyglet`
2. Press `i` to enable textures (shows arrows on each sticker)
3. Test face rotations: `f`, `r`, `u`, `d`, `l`, `b` - all should work
4. Test slice rotations: `m`, `e`, `s` - all should work
5. Test X rotation: `x` - **BROKEN** - middle slice on U/D faces shows wrong direction
6. Edit config: `src/cube/presentation/gui/backends/pyglet2/texture_rotation_config.yaml`
   - Changes reload automatically on next rotation

## Current Working Configuration

```yaml
faces:
  F: {self: 1, U: 1, R: 1, D: 1, L: 1}
  R: {self: 1, U: 0, B: 2, D: 2, F: 0}
  U: {self: 1, B: 0, R: 0, F: 0, L: 0}
  D: {self: 1, F: 0, R: 0, B: 0, L: 0}
  L: {self: 1, U: 2, F: 0, D: 0, B: 2}
  B: {self: 1, U: 3, L: 3, D: 3, R: 3}

  M: {F: 0, U: 2, B: 2, D: 0}
  E: {F: 0, R: 0, B: 0, L: 0}
  S: {U: 3, R: 3, D: 3, L: 3}
```

## Files Created/Modified

1. **`texture_rotation_config.yaml`** - Decision table for texture_direction updates
2. **`texture_rotation_loader.py`** - Loads YAML config, caches, reloads on file change
3. **`Face.py`** - `_update_texture_directions_after_rotate()` uses YAML config
4. **`Slice.py`** - `_update_texture_directions_after_rotate()` added for M, E, S

## How It Works

1. Each `PartEdge` has `texture_direction` (0-3): 0=up, 1=90°CW, 2=180°, 3=270°CW
2. When a face/slice rotates, affected stickers get: `direction = (direction + delta) % 4`
3. The YAML config specifies delta values for each rotation type
4. `_modern_gl_cell.py` reads `texture_direction` and applies UV rotation

## Key Insights

- **F, L**: All adjacent faces need update (delta=1 or 2)
- **R**: Only B and D need update (delta=2), not U and F
- **U, D**: No adjacent updates needed (delta=0 for all)
- **B**: All adjacent need update (delta=3)
- **M**: U and B need update (delta=2)
- **E**: No updates needed (delta=0 for all)
- **S**: All affected faces need update (delta=3)

## Whole-Cube Rotations (X, Y, Z) - THE OPEN PROBLEM

These are composed of face + slice rotations:
- X = M(-1) + R(1) + L(-1)
- Y = E(-1) + U(1) + D(-1)
- Z = S(1) + F(1) + B(-1)

### The Problem

When doing X rotation, the middle slice stickers on U and D faces show arrows pointing
in the wrong direction (180° off). M, R, L rotations work correctly individually.

### What Was Tried

1. **Approach 1: Let component updates sum** - Didn't work. The sum of M + R + L
   texture updates doesn't equal correct X rotation update.

2. **Approach 2: Separate X/Y/Z table entries** - Added X, Y, Z entries to YAML config
   with `_skip_texture_updates` flag to skip component updates and do one final update.
   This broke standalone M rotation (M.D=2 was needed for X but broke M alone).

   **Reverted** - X/Y/Z entries removed from YAML, special handling removed from Cube.py.

### Investigation Ideas

1. **Understand the math**: Why doesn't M(-1) + R(1) + L(-1) texture updates sum correctly?
   - M affects: F, U, B, D (middle column)
   - R affects: R face + adjacent edges
   - L affects: L face + adjacent edges
   - The stickers that end up on U after X rotation came from F. What updates did they get?

2. **Track a specific sticker**: Follow one sticker through X rotation and see what
   texture_direction updates it receives vs what it should receive.

3. **Different composition**: Maybe X should be implemented differently for textures?
   Or texture updates need adjustment based on which stickers actually moved where.

## Next Steps

1. ✅ Face rotations working (F, R, U, D, L, B)
2. ✅ Slice rotations working (M, E, S)
3. 🔄 Investigate X, Y, Z whole-cube rotations
4. ⬜ Test with 4x4 cube
5. ⬜ Convert YAML config to hardcoded efficient table
6. ⬜ Remove YAML dependency for production
