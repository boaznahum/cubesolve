# Performance: Cache Face and Slice Rotation Cycles

**Date:** 2026-01-19
**Branch:** profiling_no_2
**Status:** Complete

## Change Description

Cache precomputed rotation cycles at Face and Slice level to eliminate repeated `get_face_edge()`, `single_shared_face()`, and `get_other_face()` calls during rotations.

### Problem Identified

Profiling showed `get_face_edge()` called ~26,730 times during a solve:
- Each call iterates through edges list to find match - O(n)
- Called 8 times per edge wing + 12 times for corners per rotation
- Significant overhead for repetitive lookups

### Solution

Use CacheManager pattern (consistent with Slice.py) to precompute all 4-tuples needed for rotation:
- PartEdge cycles for `PartEdge.rotate_4cycle()`
- PartSlice cycles for `PartSlice.rotate_4cycle_slice_data()`

Cache is automatically invalidated on cube reset (new Face objects created).

### Implementation

```python
# In Face.py
def _get_rotation_cycles(self) -> tuple[...]:
    """Get cached rotation cycles for this face."""
    def compute_cycles() -> ...:
        # Build all edge_cycles and slice_cycles
        return edge_cycles, slice_cycles

    cache_key = ("Face._get_rotation_cycles", self._name)
    cache = self._cache_manager.get(cache_key, tuple)
    return cache.compute(compute_cycles)

def rotate(self, n_rotations=1) -> None:
    edge_cycles, slice_cycles = self._get_rotation_cycles()

    def _rotate() -> None:
        for edge_cycle in edge_cycles:
            PartEdge.rotate_4cycle(*edge_cycle)
        for slice_cycle in slice_cycles:
            PartSlice.rotate_4cycle_slice_data(*slice_cycle)
    # ...
```

## Files Modified

1. `src/cube/domain/model/Face.py`
   - Added `_cache_manager` to `__slots__`
   - Initialize CacheManager in `__init__`
   - Added `_get_rotation_cycles()` method with cache
   - Simplified `rotate()` method to use cached cycles

2. `src/cube/domain/model/Slice.py`
   - Added `_get_rotation_cycles()` method with cache
   - Simplified `_rotate()` method to use cached cycles

## Performance Results

Comparison before/after caching (has_visible_presentation=False):

| Solver | Size | Original | After Face | After Slice | Total Improvement |
|--------|------|----------|------------|-------------|-------------------|
| LBL | 3x3 | 8.4ms | 5.8ms | 5.5ms | **35% faster** |
| LBL | 5x5 | 46.5ms | 34.0ms | 29.9ms | **36% faster** |
| CFOP | 3x3 | 8.1ms | 6.0ms | 5.7ms | **30% faster** |
| CFOP | 5x5 | 44.9ms | 33.5ms | 29.5ms | **34% faster** |

## Key Findings

1. `get_face_edge()` no longer appears in profile hot path
2. `single_shared_face()` calls eliminated from rotation hot path
3. Face rotation tottime reduced from ~21ms to ~7.6ms (5x5)
4. Main overhead now is `_update_texture_directions_after_rotate` (expected for visible mode)

## Verification

All checks passed:
- ruff: no issues
- mypy: no issues
- pyright: 0 errors
- pytest (non-GUI): 1920 passed, 8 skipped
- pytest (GUI): 24 passed
