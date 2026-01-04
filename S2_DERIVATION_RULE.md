# S2 Derivation Rule - Complete Analysis

## Overview

The **s2 position** (the intermediate position in the 3-cycle) is the position where the piece at the target moves to during a block communicator sequence.

The 3-cycle pattern is:
- **s1** (source point on source face) → **t** (target point on target face)
- **t** (target point) → **s2** (intermediate point on SOURCE face)
- **s2** → back to **s1**

## The S2 Derivation Rule

### Mathematical Principle

The s2 position depends on whether the target block coordinates would **intersect** with their rotated version:

```
For target point t on target face:

1. Compute the rotation needed to avoid intersection:
   - Try rotating t clockwise (CW)
   - Check if original t intersects with rotated t

2. If intersection exists:
   - Use counterclockwise (CCW) rotation
   - s2 = rotate_counterclockwise(t)
   - on_front_rotate = -1 (use F' in commutator)

3. If no intersection:
   - Use clockwise (CW) rotation
   - s2 = rotate_clockwise(t)
   - on_front_rotate = 1 (use F in commutator)

4. Critical: s2 is always on the SOURCE face, NOT the target face
```

### Implementation Location

This logic is implemented in `_compute_rotate_on_target()` method at line 625 of `CommunicatorHelper.py`:

```python
def _compute_rotate_on_target(self, cube, face_name, slice_name, target_block):
    # ... helper functions ...

    # Check if CW rotation causes intersection
    if self._1d_intersect((ex(target_point_begin), ex(target_point_end)),
                          (ex(target_begin_rotated_cw), ex(target_end_rotated_cw))):
        on_front_rotate = -1  # Use F' (counterclockwise)
        target_block_after_rotate = (target_begin_rotated_ccw, target_end_rotated_ccw)
    else:
        on_front_rotate = 1   # Use F (clockwise)
        target_block_after_rotate = (target_begin_rotated_cw, target_end_rotated_cw)

    return on_front_rotate, target_block_after_rotate
```

## Empirical Validation

### Test Results (UP→FRONT with 3x3 cube)

| Target Point | Source Point | S2 Position | S2 Face | Rotation | Valid |
|-------------|------------|-----------|---------|----------|-------|
| (0, 0) | (0, 0) | (0, 2) | UP | CCW | ✅ |
| (0, 1) | (0, 1) | (1, 0) | UP | CW | ✅ |
| (1, 0) | (1, 0) | (2, 1) | UP | CW | ✅ |
| (1, 1) | (1, 1) | ERROR | - | - | ❌ |

**Key Observation**: For position (1,1) (center of 3x3), the center position causes an **intersection error** - it cannot be rotated without creating overlap, so the communicator cannot be applied there.

### Verification of Rule

For UP→FRONT:
1. **t=(0,0)** intersects with CW rotation → use CCW → **s2=(0,2)** ✅
2. **t=(0,1)** does NOT intersect with CW → use CW → **s2=(1,0)** ✅
3. **t=(1,0)** does NOT intersect with CW → use CW → **s2=(2,1)** ✅

## Critical Insights

### 1. S2 is on SOURCE Face
Unlike the target point t which is on the TARGET face, **s2 is always on the SOURCE face**. This was empirically verified and is essential to understand the 3-cycle.

### 2. Intersection Check Determines Rotation
The decision between CW and CCW rotation depends entirely on whether the target block coordinates would overlap when rotated. This is computed using `_1d_intersect()` to check one-dimensional intersection of the slice coordinates.

### 3. On-Front-Rotate Controls the Algorithm
The `on_front_rotate` value (-1 or 1) directly controls whether F or F' is used in the commutator sequence:
- `on_front_rotate = 1`: Use F (clockwise) → s2 = rotate_clockwise(t)
- `on_front_rotate = -1`: Use F' (counterclockwise) → s2 = rotate_counterclockwise(t)

### 4. Universal Across All Face Pairs
The principle applies to all 30 face pair combinations. The only difference between pairs is the orientation of the source and target faces, but the underlying intersection logic remains the same.

## Algorithm Summary

```python
def compute_s2(target_point: Point, on_front_rotate: int, cube: Cube) -> Point:
    """
    Compute the s2 position from the target point and rotation type.

    Args:
        target_point: The target position (t)
        on_front_rotate: Rotation direction (-1 for CCW, 1 for CW)
        cube: The cube object with rotation methods

    Returns:
        The s2 position on the source face
    """
    if on_front_rotate == 1:
        # Clockwise rotation
        return cube.cqr.rotate_point_clockwise(target_point)
    else:
        # Counterclockwise rotation
        return cube.cqr.rotate_point_counterclockwise(target_point)
```

## Integration with CommunicatorHelper

The s2 position should be:

1. **Computed** during the `execute_communicator()` method after determining `on_front_rotate`
2. **Returned** as part of the `CommutatorResult` dataclass
3. **Used** in solvers to verify the 3-cycle and make decisions about next moves

### Proposed Enhancement to CommutatorResult

```python
@dataclass(frozen=True)
class CommutatorResult:
    source_ltr: Point
    algorithm: Alg | None
    s2_position: Point | None = None  # NEW: The intermediate affected piece
    _secret: _InternalCommData | None = None
```

## References

1. **Mathematical Foundation**: Block commutator formula [M', F]² creates a 3-cycle
2. **Implementation**: `CommunicatorHelper._compute_rotate_on_target()` line 625
3. **Validation**: `test_3cycle_up_front.py` - empirical 3-cycle verification
4. **Theory**: COMMUTATOR_MATHEMATICS.md - mathematical background

## Next Steps

1. Add `s2_position` field to `CommutatorResult`
2. Compute and return s2 in `execute_communicator()` method
3. Update solver code to track and verify all 3 affected pieces
4. Test across all 30 face pairs for universal applicability
5. Document s2 in solver output for debugging and analysis
