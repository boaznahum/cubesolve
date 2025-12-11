# Texture Rotation Bug Analysis

## Status: IN PROGRESS (2025-12-11)

Face rotations (F, R, U, D, L, B) and slice rotations (M, E, S) work correctly.
Whole-cube rotations (X, Y, Z) need investigation - texture updates may not sum correctly.

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

## Whole-Cube Rotations (X, Y, Z)

These are composed of face + slice rotations:
- X = M(-1) + R(1) + L(-1)
- Y = E(-1) + U(1) + D(-1)
- Z = S(1) + F(1) + B(-1)

**Issue:** The texture updates from component rotations may not sum correctly.
X rotation was observed to have incorrect texture on the middle slice on U and D faces.

**Investigation needed:** Determine why the sum of M + R + L texture updates doesn't
equal the correct X rotation texture update.

## Next Steps

1. ✅ Face rotations working (F, R, U, D, L, B)
2. ✅ Slice rotations working (M, E, S)
3. 🔄 Investigate X, Y, Z whole-cube rotations
4. ⬜ Test with 4x4 cube
5. ⬜ Convert YAML config to hardcoded efficient table
6. ⬜ Remove YAML dependency for production
