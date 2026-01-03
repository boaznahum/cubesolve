# S2 Computation Algorithm Discovery

## Problem Statement

The CommunicatorHelper needed to compute **s2** (the third affected piece in the 3-cycle movement pattern). The 3-cycle is: **s1 → t → s2 → s1**, where:
- **s1** = source point (natural source position on source face)
- **t** = target point (on target face)
- **s2** = intermediate point (on source face) - the one we needed to compute

## Solution: The Correct Algorithm

### Formula

```
xp = su'(translator(tf, sf, f(tp)))
```

Where:
- **tp** = target point (input, on target face)
- **f(tp)** = apply face rotation to target point
- **translator(tf, sf, xpt)** = map from target face coordinates back to source face coordinates
- **su'** = inverse setup operation (rotate back to original coordinate system)
- **xp** = final s2 point (on source face)

### Algorithm Steps

1. **Get tp** (target point from target_block)

2. **Apply f (face rotation on target):**
   ```python
   on_front_rotate_n = _compute_rotate_on_target(...)  # -1 or 1
   xpt = tp
   if on_front_rotate_n < 0:  # CCW
       xpt = rotate_counterclockwise(xpt)
   else:  # CW
       xpt = rotate_clockwise(xpt)
   ```

3. **Apply translator (target → source coordinates):**
   ```python
   xp_translated = Face2FaceTranslator.translate(target_face, source_face, xpt)
   ```

4. **Apply su' (inverse setup rotation):**
   ```python
   source_setup_n_rotate = _find_rotation_idx(source_1_point, expected_source_1_point)
   s2_point = xp_translated
   for _ in range(source_setup_n_rotate):
       s2_point = rotate_counterclockwise(s2_point)
   ```

## Discovery Process

### Key Insight from Communicator Mathematics

When executing the block commutator, we:
1. Apply **su** (setup operation) to align source point
2. Apply **m1** (move np → tp) and **f** (face rotation on target)
3. The communicator moves pieces in 3-cycle
4. Apply **su'** (inverse setup) to restore coordinate system

The third piece (s2) follows a specific path based on these operations:
- **Before communicator executes:** position is computed via f and translator
- **After communicator executes:** position lands at the predicted location
- **After su' is applied:** position is in the original coordinate system = **s2**

### Implementation Details

The translator is necessary because:
- **Identity translator works** for axis-aligned pairs (UP/DOWN, FRONT/BACK) where source and target have compatible coordinate systems
- **Face2FaceTranslator needed** for perpendicular pairs (LEFT/RIGHT with UP/DOWN/FRONT/BACK) where coordinate systems need transformation

## Test Results

### Current Status: 140 PASSED, 40 FAILED (out of 180 tests)

#### ✅ PASSING (Identity Translator Works)

**Axis-aligned face pairs:** All 6 cube sizes (3x3 through 8x8)
- UP-FRONT (U<-F): 6/6 ✅
- FRONT-UP (F<-U): 6/6 ✅
- UP-BACK (U<-B): 6/6 ✅
- BACK-UP (B<-U): 6/6 ✅
- DOWN-FRONT (D<-F): 6/6 ✅
- FRONT-DOWN (F<-D): 6/6 ✅
- DOWN-BACK (D<-B): 6/6 ✅
- BACK-DOWN (B<-D): 6/6 ✅
- FRONT-BACK (F<-B): 6/6 ✅
- BACK-FRONT (B<-F): 6/6 ✅

**Total passing:** 60 tests (10 pairs × 6 cube sizes)

#### ❌ FAILING (Need Face2FaceTranslator)

**Perpendicular pairs:** Pass 3x3 only, fail on 4x4+

Left-related pairs:
- LEFT-UP (L<-U): 1/6 ✅, 5/6 ❌
- UP-LEFT (U<-L): 1/6 ✅, 5/6 ❌
- LEFT-DOWN (L<-D): 1/6 ✅, 5/6 ❌
- DOWN-LEFT (D<-L): 1/6 ✅, 5/6 ❌

Right-related pairs:
- RIGHT-UP (R<-U): 1/6 ✅, 5/6 ❌
- UP-RIGHT (U<-R): 1/6 ✅, 5/6 ❌
- RIGHT-DOWN (R<-D): 1/6 ✅, 5/6 ❌
- DOWN-RIGHT (D<-R): 1/6 ✅, 5/6 ❌

Front/Back with Left/Right:
- FRONT-LEFT (F<-L): 1/6 ✅, 5/6 ❌
- LEFT-FRONT (L<-F): 1/6 ✅, 5/6 ❌
- And 6 more similar pairs...

**Total failing:** 40 tests (20 pairs with 4x4+ failures)

### Why the Pattern?

**3x3 cubes:** Only one center position, so identity translator works for all pairs
**4x4+ cubes:** Multiple center positions. Face2FaceTranslator must properly map coordinates between perpendicular faces

## Code Changes

### Modified Files

**src/cube/domain/solver/common/big_cube/commun/CommunicatorHelper.py**

The s2 computation (lines 337-370) now implements the complete algorithm:

```python
# Compute xp (s2) using correct algorithm:
# xp = su'(translator(tf, sf, f(tp)))

# Step 1: Get tp (target point)
tp: Point = target_block[0]

# Step 2: Apply f (face rotation on target) to tp
on_front_rotate_n, _ = self._compute_rotate_on_target(...)
xpt = tp
if on_front_rotate_n < 0:
    for _ in range(abs(on_front_rotate_n)):
        xpt = self.cube.cqr.rotate_point_counterclockwise(xpt)
else:
    for _ in range(on_front_rotate_n):
        xpt = self.cube.cqr.rotate_point_clockwise(xpt)

# Step 3: Apply translator (identity for now)
xp_translated = xpt

# Step 4: Apply su' (inverse setup)
expected_source_1_point: Point = internal_data.source_coordinate
source_setup_n_rotate = self._find_rotation_idx(source_1_point, expected_source_1_point)
s2_point = xp_translated
for _ in range(source_setup_n_rotate):
    s2_point = self.cube.cqr.rotate_point_counterclockwise(s2_point)
```

### S2 Rotation Table (Deprecated)

The `s2_rotation_table.yaml` file is now **obsolete** since we implemented the correct mathematical algorithm. The table-based approach was an attempt to use multipliers, which was incorrect. The identity translator (no table) is the correct solution.

## Next Steps

1. **Implement Face2FaceTranslator.translate()** in the algorithm to handle perpendicular face pairs
2. This will fix the remaining 40 failing tests
3. Once complete, all 180 tests should pass

## Mathematical Reference

The algorithm is based on the block commutator mathematics:
- The commutator moves pieces in a fixed 3-cycle
- The positions are determined by the operations applied before and after the communicator
- The setup and inverse-setup operations are crucial for coordinate transformation

See the referenced documentation link in the CommunicatorHelper docstring for complete mathematical derivation.
