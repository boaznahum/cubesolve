# Performance Analysis and Optimization Opportunities

**Date:** 2026-01-19
**Profiling Scripts:**
- `tests/performance/profile_solvers.py` - Comprehensive solver profiling
- `tests/performance/profile_face_rotate.py` - Detailed Face.rotate analysis

## Benchmark Summary (5x5 Cube)

| Solver | Avg Time | Moves | Moves/sec |
|--------|----------|-------|-----------|
| LBL | 349ms | 523 | 1,499 |
| CFOP | 328ms | 455 | 1,390 |
| Kociemba | 257ms | 397 | 1,545 |
| Cage | 390ms | 485 | 1,242 |

## Top Bottlenecks (by tottime - actual CPU time)

### 1. Texture Direction Updates (18% of solve time)

**Files:**
- `Face.py:554:_update_texture_directions_after_rotate` - 53ms (13.4%)
- `Slice.py:493:_update_texture_directions_after_rotate` - 20ms (5%)

**Issue:** After every face/slice rotation, the code updates texture directions for all affected stickers. This is only needed for GUI rendering.

**Call Pattern:**
```
rotate() -> _rotate() -> _update_texture_directions_after_rotate()
                          - Iterates all edges (n_slices iterations)
                          - Iterates all corners (4 iterations)
                          - Iterates all center cells (n^2 iterations)
                          - Makes ~100+ method calls per rotation
```

**Optimization Opportunities:**
1. **Skip in headless mode** - Add flag to skip texture updates when not rendering
2. **Batch updates** - Defer texture updates until rendering is needed
3. **Pre-computed tables** - Store texture deltas as direct lookup tables

### 2. Property/Method Call Overhead (15% of solve time)

**Hot methods (by call count):**
| Method | Calls | Time | Issue |
|--------|-------|------|-------|
| `PartEdge.face` | 231,099 | 18ms | Simple property, called too often |
| `PartSlice.get_face_edge` | 70,752 | 22ms | Dictionary lookup per call |
| `Edge.get_slice` | 39,200 | 9ms | List access + validation |

**Optimization Opportunities:**
1. **Direct attribute access** - Replace `obj.property` with `obj._attr` in hot paths
2. **Inline small functions** - Manually inline tiny getter functions
3. **Cache results** - Cache `get_face_edge()` results during rotation

### 3. Enum Operations (3% of solve time)

**Issue:** `enum.py:186(__get__)` called 36,277 times

**Cause:** Using `FaceName.F.name` triggers enum descriptor protocol

**Optimization:**
```python
# Slow (triggers __get__ every time)
face_name = self.name.name

# Fast (pre-cache enum name)
self._face_name_str = self.name.name  # Cache once at init
```

### 4. Dictionary Lookups in Inner Loops

**File:** `texture_rotation_loader.py:29:get_delta` - 34k calls, 14ms

```python
# Current (2 dict lookups per call)
def get_delta(rotating_face: str, target: str) -> int:
    face_config = _TEXTURE_DELTAS.get(rotating_face, {})
    return face_config.get(target, 0)
```

**Optimization:**
```python
# Flatten to single lookup with tuple key
_FLAT_DELTAS = {
    ('F', 'self'): 1, ('F', 'U'): 1, ...
}
def get_delta(rotating_face: str, target: str) -> int:
    return _FLAT_DELTAS.get((rotating_face, target), 0)
```

### 5. Core Rotation Logic (7% of solve time)

**File:** `Face.py:395:_rotate` - 28ms

This is already well-optimized with O(1) reference swapping. Further optimization would require:
- C extension for rotation
- NumPy-based cube representation
- Pre-computed rotation permutations

## Optimization Priority Matrix

| Optimization | Impact | Effort | Risk |
|--------------|--------|--------|------|
| Skip texture updates in headless | **High** | Low | Low |
| Pre-cache enum names | Medium | Low | Low |
| Flatten texture delta lookup | Medium | Low | Low |
| Direct attribute access in hot paths | Medium | Medium | Medium |
| Batch texture updates | Medium | Medium | Medium |
| C extension for rotation | **High** | **High** | Medium |

## Quick Wins (Low Effort, Low Risk)

### 1. Add query mode for texture updates
```python
# In Face.rotate
if not self.cube._in_query_mode:
    self._update_texture_directions_after_rotate(1)
```
Already partially implemented - need to ensure it's used in solver paths.

### 2. Pre-cache enum string names
```python
class Face:
    def __init__(self, ...):
        self._name_str = self.name.name  # Cache once
```

### 3. Flatten texture delta table
See optimization above.

## Performance Testing Commands

```bash
# Full profiling with all solvers
python -m tests.performance.profile_solvers --sizes 3,4,5 --solves 3

# Quick benchmark (no cProfile)
python -m tests.performance.profile_solvers --quick --solver LBL --size 5

# Detailed Face.rotate analysis
python -m tests.performance.profile_face_rotate --mode solve --size 5

# Compare with/without cache
python -m tests.performance.profile_solvers --compare-cache --sizes 3,4,5

# Save JSON report
python -m tests.performance.profile_solvers --output report.json
```

## Next Steps

1. **Implement quick wins** - Low risk, immediate benefit
2. **Add `--headless` mode** - Skip all GUI-related computations
3. **Profile after optimizations** - Measure actual improvement
4. **Consider C extension** - For production/competition use
