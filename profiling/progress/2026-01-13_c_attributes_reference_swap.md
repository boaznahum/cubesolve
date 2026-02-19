# Rotation c_attributes Optimization

## Summary

Optimized face and slice rotation by swapping `c_attributes` dict references instead of copying dict contents.

**Commit:** `ad5dca4`

## Problem

During rotation, each `PartEdge` has a `c_attributes` dict that must move with the color. The original implementation copied dict contents:

```python
def copy_color(self, source: "PartEdge"):
    self._color = source._color
    self._annotated_by_color = source._annotated_by_color
    self._texture_direction = source._texture_direction
    self.c_attributes.clear()      # O(K)
    self.c_attributes.update(source.c_attributes)  # O(K)
```

This is **O(K)** per sticker where K = number of attributes.

## Solution

Since rotations are always 4-cycles, we can swap dict references instead:

```python
@staticmethod
def rotate_4cycle(p0, p1, p2, p3):
    # Save references (not copies!)
    c_attrs = (p0.c_attributes, p1.c_attributes, p2.c_attributes, p3.c_attributes)

    # Swap references - O(1)
    p0.c_attributes, p1.c_attributes, p2.c_attributes, p3.c_attributes = \
        c_attrs[1], c_attrs[2], c_attrs[3], c_attrs[0]
```

This is **O(1)** per sticker regardless of attribute count.

## Benchmark Results

**Test:** 9x9 cube, 500 face rotations (edges + corners)

| Attributes/Sticker | OLD (copy) | NEW (swap) | Speedup |
|-------------------|------------|------------|---------|
| 0 | 19.9ms | 18.7ms | **1.07x** |
| 5 | 20.9ms | 18.6ms | **1.13x** |
| 10 | 24.7ms | 21.9ms | **1.13x** |
| 20 | 25.5ms | 19.3ms | **1.32x** |
| 50 | 31.6ms | 18.4ms | **1.72x** |

### Key Observations

1. **NEW time stays constant** (~18-19ms) regardless of attribute count
2. **OLD time grows linearly** with K (number of attributes)
3. **Speedup scales with K**: 1.07x at K=0 → 1.72x at K=50

## Files Changed

- `src/cube/domain/model/PartEdge.py` - Added `rotate_4cycle()` static method
- `src/cube/domain/model/Face.py` - Refactored edge, corner, center rotation
- `src/cube/domain/model/Slice.py` - Refactored edge, center rotation

## Practical Impact

When tracking markers, annotations, or other metadata on stickers (via `c_attributes`), rotation performance improves proportionally to the amount of tracked data.

## Reproducing the Benchmark

Run: `PYTHONPATH=src python tests/performance/benchmark_rotation_c_attributes.py`
