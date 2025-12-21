# TODO: Unify Tracker Cleanup Code

## Current State

There are **two separate cleanup mechanisms** for face tracker slices:

### 1. NxNCentersFaceTrackers (used by NxNCenters)

Location: `src/cube/domain/solver/beginner/NxnCentersFaceTracker.py`

```python
class NxNCentersFaceTrackers:
    def _remove_all_track_slices(self) -> None:
        for f in self._cube.faces:
            FaceTracker.remove_face_track_slices(f)
```

Called in `NxNCenters.solve()`:
```python
def solve(self):
    try:
        self._solve()
    finally:
        self._trackers._remove_all_track_slices()  # Always runs
```

### 2. FaceTrackerHolder (used by CageNxNSolver)

Location: `src/cube/domain/solver/beginner/FaceTrackerHolder.py`

```python
class FaceTrackerHolder:
    def cleanup(self) -> None:
        for f in self._cube.faces:
            FaceTracker.remove_face_track_slices(f)
```

Called via context manager in `CageNxNSolver._solve_impl()`:
```python
with FaceTrackerHolder(self) as tracker_holder:
    # ... solve ...
# cleanup() called automatically on exit
```

## The Challenge

### Problem 1: Duplicate Cleanup
When CageNxNSolver passes trackers to NxNCenters:
```python
cage_centers = NxNCenters(self, preserve_cage=True, face_trackers=tracker_holder.trackers)
cage_centers.solve()
```

Cleanup happens **twice**:
1. NxNCenters.solve() → `self._trackers._remove_all_track_slices()`
2. FaceTrackerHolder.__exit__() → `cleanup()`

This works (cleanup is idempotent) but is wasteful and confusing.

### Problem 2: Two Different Tracker Management Classes

| Class | Purpose | Creates Trackers | Manages Cleanup |
|-------|---------|------------------|-----------------|
| `NxNCentersFaceTrackers` | Helper for NxNCenters | Yes (complex logic) | Yes |
| `FaceTrackerHolder` | OOP wrapper for 6 trackers | Yes (delegates) | Yes |

Both do similar things but with different APIs.

### Problem 3: Ownership Confusion

- NxNCenters always creates its own `NxNCentersFaceTrackers` instance
- But it can also receive external trackers via `face_trackers` parameter
- When external trackers are provided, who should clean up?

## Proposed Solution

Unify around `FaceTrackerHolder`:

1. **FaceTrackerHolder** becomes the single source of truth for tracker lifecycle
2. **NxNCentersFaceTrackers** becomes internal implementation detail (tracker creation only)
3. **NxNCenters** accepts `FaceTrackerHolder` instead of `Sequence[FaceTracker]`
4. Cleanup responsibility is clear: whoever creates the holder cleans it up

### New Flow

```python
# BeginnerReducer (reduction method)
with FaceTrackerHolder(self) as holder:
    centers = NxNCenters(self, holder)
    centers.solve()
# cleanup automatic

# CageNxNSolver (cage method)
with FaceTrackerHolder(self) as holder:
    # ... solve edges and corners ...
    centers = NxNCenters(self, holder, preserve_cage=True)
    centers.solve()
# cleanup automatic
```

### Key Insight

The challenge is that NxNCenters was designed to:
1. Create trackers internally (for reduction method)
2. Accept trackers externally (for cage method)

This dual responsibility creates the confusion. By always requiring a holder from outside, the responsibility is clear.

## Files to Modify

- `src/cube/domain/solver/beginner/NxNCenters.py` - Accept holder, remove internal cleanup
- `src/cube/domain/solver/beginner/FaceTrackerHolder.py` - Already good
- `src/cube/domain/solver/reducers/BeginnerReducer.py` - Create holder, pass to NxNCenters
- `src/cube/domain/solver/direct/cage/CageNxNSolver.py` - Already uses holder

## Related: is_boy Checks

There's also duplication in BOY layout validation:
- `NxNCenters._asserts_is_boy()` - inline implementation
- `FaceTrackerHolder.is_boy()` / `assert_is_boy()` - new methods

These should also be unified - NxNCenters should use holder's method.
