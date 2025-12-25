# Tracker Indicators Feature (WIP)

**Status:** Work in Progress - Basic implementation complete, per-holder marker IDs implemented, shadow faces issue pending

## Overview

Small filled circle indicators that appear on center slices marked as tracker anchors (even cubes like 4x4, 6x6). The indicator shows the tracker's **assigned color** (not the current sticker color), helping visualize which center is the reference point for each face.

## Implementation

### Files Modified

1. **`_modern_gl_cell.py`**
   - Added constants:
     - `_TRACKER_INDICATOR_RADIUS_FACTOR = 0.25` (25% of cell size)
     - `_TRACKER_INDICATOR_HEIGHT = 0.10` (height offset)
     - `_TRACKER_INDICATOR_OUTLINE_WIDTH = 0.15` (black outline width)
     - `_TRACKER_INDICATOR_OUTLINE_COLOR = (0.0, 0.0, 0.0)` (black)
     - `_TRACKER_KEY_PREFIX = "_nxn_centers_track:"` (for identifying tracker keys)

   - Added `get_tracker_color() -> Color | None`:
     - Detects if cell is a tracked center by checking `c_attributes` for tracker keys
     - Returns the Color value stored directly in c_attributes (no parsing needed)

   - Added `generate_tracker_indicator_vertices(dest: list[float])`:
     - Generates a small filled circle with black outline
     - Uses tracker's assigned color directly (NOT complementary)
     - Reuses `_generate_3d_ring()` with `inner_radius=0` for filled circle

2. **`_modern_gl_board.py`**
   - Added calls to `cell.generate_tracker_indicator_vertices(marker_verts)` after marker generation
   - Both static and animated paths

### Tracker Class Hierarchy

```
FaceTracker (abstract base)      # Never instantiated directly
    │
    ├── SimpleFaceTracker        # For odd, opposite, f5 (no cleanup needed)
    │   - Stores predicate for face search
    │   - cleanup() is no-op
    │
    └── MarkedFaceTracker        # For marked center slices (needs cleanup)
        - Stores the key used to mark the slice
        - cleanup() searches and removes its specific key
```

**Key Design Points:**
- `face` is an abstract property - each subclass implements face finding
- `cleanup()` is an abstract method - polymorphic cleanup
- Only `MarkedFaceTracker` marks slices and needs cleanup
- `SimpleFaceTracker` is used for odd cube trackers, opposite trackers, and f5 trackers

### Per-Holder Marker IDs

Each `FacesTrackerHolder` instance gets a unique ID. Every tracker created by that
holder uses that holder_id in its marker key. This allows multiple holders
to coexist safely - cleanup only removes markers belonging to THAT holder.

**Key Format:** `"_nxn_centers_track:h{holder_id}:{color}{unique_id}"`
**Value:** The `Color` enum is stored directly as the value (not encoded in key)

Example:
```python
key = "_nxn_centers_track:h42:Color.WHITE1"
edge.c_attributes[key] = Color.WHITE  # Color stored as value
```

### How It Works

1. `FacesTrackerHolder.__init__` generates unique holder ID (class counter)

2. `NxNCentersFaceTrackers._create_tracker_by_center_piece()` creates marker:
   ```python
   key = f"{TRACKER_KEY_PREFIX}h{self._holder_id}:{_slice.color}{unique_id}"
   edge.c_attributes[key] = _slice.color  # Store Color for renderer
   ```

3. `MarkedFaceTracker` stores the key, implements `face` property to find marked slice

4. `FacesTrackerHolder.cleanup()` calls `tracker.cleanup()` polymorphically:
   - `SimpleFaceTracker.cleanup()` - no-op
   - `MarkedFaceTracker.cleanup()` - searches and removes its key

5. Renderer reads color directly from value (no parsing needed)

This design:
- No ambiguity - holder_id is required (not optional)
- Multiple holders coexist safely
- Animation works (status cleanup doesn't break solve holder)
- Renderer doesn't need to parse key format - just reads the Color value

### Static Utility Method

`FaceTracker.is_track_slice(s: CenterSlice) -> bool`

Static method to check if ANY tracker has marked a slice. Used by:
- Debug code (`_debug_print_track_slices`)
- `NxNCenters.py` for checking slice state

## Known Issues

### 1. Shadow Faces Don't Show Indicators

**Status:** Not investigated yet

Shadow faces (L, D, B rendered at offset positions) don't display tracker indicators. Main faces work correctly. The shadow faces use the same `_generate_face_verts()` function, so they should work. Need to investigate why they don't.

### 2. Second Scramble Causes Crash (FIXED)

**Status:** FIXED - Per-holder marker IDs + context managers

See "Second Scramble Crash Bug" section below for details.

## TODO

- [x] Fix second scramble crash bug (blocking) - DONE: Fresh trackers per entry point
- [x] Fix animation crash (cleanup removing other holders' markers) - DONE: Per-holder marker IDs
- [x] Simplify renderer - store Color as value, not encoded in key
- [x] Add tracker class hierarchy with polymorphic cleanup
- [ ] Investigate shadow faces issue
- [ ] Move constants to ConfigProtocol for runtime configurability
- [ ] Add toggle to enable/disable tracker indicators
- [ ] Consider adding indicators for edge trackers too
- [ ] Revisit SimpleFaceTracker design (storing predicate callable feels inelegant)

## Testing

To test the feature:
1. Run GUI with 4x4 cube
2. Scramble once (key 0)
3. Start LBL-Direct solver
4. Look for small colored circles on center pieces (should have black outlines)

---

# Second Scramble Crash Bug

## Symptom

After scrambling and solving once, running a second scramble causes:
```
File ".../LayerByLayerNxNSolver.py", line 118, in status
    layer1_done = self._is_layer1_solved(th)
...
InternalSWError: Can't find face with pred <function ...>
```

## Root Cause

1. First scramble + solve creates trackers with predicates that reference marked center slices
2. Second scramble resets cube and clears all `c_attributes` (including tracker marks)
3. Solver still holds reference to old `FacesTrackerHolder` with old trackers
4. When `status` property is accessed, it tries to use old trackers
5. Tracker predicates can't find their marked centers (keys were cleared)
6. `find_face()` fails because no face matches the predicate

## Solution (IMPLEMENTED)

### Part 1: Context Managers (Second Scramble Fix)

The fix was implemented in `LayerByLayerNxNSolver`:

1. Removed `_tracker_holder` field from `__slots__`
2. Removed `tracker_holder` property and `cleanup_trackers()` method
3. Wrapped `status` property with `with FacesTrackerHolder(self) as th:`
4. Wrapped `_solve_impl` method with `with FacesTrackerHolder(self) as th:`

Key insight: Solvers should NOT hold persistent tracker holders - they become stale on cube reset.
Instead, create fresh trackers at each entry point (`status`, `_solve_impl`) using context managers.

### Part 2: Per-Holder Marker IDs (Animation Fix)

The context manager approach broke with animation because `status` checks would cleanup
while `_solve_impl` was still running (between animated moves).

The fix uses unique holder IDs so each holder only cleans up its own markers.

**Files Modified:**
- `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py`
- `src/cube/domain/solver/common/big_cube/FacesTrackerHolder.py`
- `src/cube/domain/solver/common/big_cube/_FaceTracker.py`
- `src/cube/domain/solver/common/big_cube/_NxNCentersFaceTracker.py`
- `src/cube/presentation/gui/backends/pyglet2/_modern_gl_cell.py`
- `tests/solvers/test_lbl_big_cube_solver.py`
- `tests/solvers/test_tracker_majority_bug.py`

---

# Implementation Reference (For Edge Trackers)

This section documents the complete implementation pattern used for center trackers.
Use this as reference when implementing edge trackers.

## Class Hierarchy Pattern

```
                    ┌─────────────────────────────┐
                    │   FaceTracker (ABC)         │
                    │   _FaceTracker.py           │
                    ├─────────────────────────────┤
                    │ __slots__ = [_cube, _color] │
                    │                             │
                    │ @property @abstractmethod   │
                    │ def face(self) -> Face      │
                    │                             │
                    │ @abstractmethod             │
                    │ def cleanup(self) -> None   │
                    │                             │
                    │ def track_opposite()        │
                    │ @staticmethod is_track_slice│
                    └─────────────┬───────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
┌─────────────────────────────┐     ┌─────────────────────────────┐
│   SimpleFaceTracker         │     │   MarkedFaceTracker         │
│   (no cleanup needed)       │     │   (needs cleanup)           │
├─────────────────────────────┤     ├─────────────────────────────┤
│ __slots__ = [_pred]         │     │ __slots__ = [_key]          │
│                             │     │                             │
│ face: uses stored predicate │     │ face: searches for _key     │
│       _cube.cqr.find_face() │     │       in c_attributes       │
│                             │     │                             │
│ cleanup(): pass (no-op)     │     │ cleanup(): searches all     │
│                             │     │   slices, removes _key      │
└─────────────────────────────┘     └─────────────────────────────┘

Used for:                           Used for:
- Odd cube trackers                 - Even cube marked centers
- Opposite trackers                 - Future: Edge trackers?
- f5/f6 BOY-based trackers
```

## Factory Pattern

The factory (`NxNCentersFaceTrackers`) is the only class that needs `holder_id`:

```python
class NxNCentersFaceTrackers:
    """Factory for creating face trackers."""

    _global_tracer_id: int = 0  # Class variable for unique keys

    def __init__(self, slv: SolverElementsProvider, holder_id: int) -> None:
        self._slv = slv
        self._holder_id = holder_id  # Only factory needs this

    def _create_tracker(self, color: Color, pred: Pred[Face]) -> SimpleFaceTracker:
        """Create a SimpleFaceTracker (no marking)."""
        return SimpleFaceTracker(self.cube, color, pred)

    def _create_tracker_by_center_piece(self, _slice: CenterSlice) -> MarkedFaceTracker:
        """Mark a center slice and create MarkedFaceTracker."""
        # Generate unique key with holder_id
        NxNCentersFaceTrackers._global_tracer_id += 1
        unique_id = NxNCentersFaceTrackers._global_tracer_id
        key = f"{TRACKER_KEY_PREFIX}h{self._holder_id}:{_slice.color}{unique_id}"

        # Store Color as VALUE (renderer reads this directly)
        edge = _slice.edge
        edge.c_attributes[key] = _slice.color

        # Create tracker that stores only the key
        return MarkedFaceTracker(_slice.parent.cube, _slice.color, key)
```

## Key Design Decisions

### 1. Why Abstract Base Class?

**Problem:** Original design had concrete base class used for both marked and unmarked trackers.
This conflated two different behaviors.

**Solution:** Abstract base with two concrete subclasses. Each subclass has single responsibility:
- `SimpleFaceTracker`: Find face via predicate, no cleanup
- `MarkedFaceTracker`: Find face via key search, cleanup removes key

### 2. Why Search Instead of Store Edge Reference?

**Problem:** Initial refactor stored `_marked_edge` reference in `MarkedFaceTracker`.

**Bad:** Edges MOVE during cube rotations! A stored reference becomes stale.

**Solution:** Store only the `_key` string. Search for it during:
- `face` property: Find which face contains the marked slice
- `cleanup()`: Find and remove the key from c_attributes

### 3. Why Store Color as Value?

**Problem:** Original design encoded color in key string. Renderer had to parse:
```python
# Old (ugly)
key = "_nxn_centers_track:h42:WHITE1"
# Renderer had to parse "WHITE" from key string
```

**Solution:** Store Color enum directly as value:
```python
# New (clean)
edge.c_attributes[key] = Color.WHITE
# Renderer just reads: value = c_attributes[key]
```

### 4. Why Per-Holder IDs?

**Problem:** With context managers, `status` property creates its own holder.
When `status` holder cleans up, it was removing markers from `_solve_impl` holder!

**Solution:** Each holder gets unique ID. Keys include holder ID:
```
Key: "_nxn_centers_track:h42:WHITE1"
                        ^^^ holder_id
```

Cleanup only removes keys matching THIS holder's ID.

## Holder Lifecycle

```python
class FacesTrackerHolder:
    _holder_unique_id: int = 0  # Class counter

    def __init__(self, slv, trackers=None):
        # Generate unique ID for this holder instance
        FacesTrackerHolder._holder_unique_id += 1
        self._holder_id = FacesTrackerHolder._holder_unique_id

        if trackers is None:
            # Create trackers via factory (passes holder_id to factory)
            factory = NxNCentersFaceTrackers(slv, self._holder_id)
            self._trackers = [factory.track_no_1(), ...]
        else:
            self._trackers = trackers

    def cleanup(self):
        # Polymorphic cleanup - each tracker knows what to do
        for tracker in self._trackers:
            tracker.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
```

## Renderer Integration

The renderer checks for tracker keys and reads the Color value directly:

```python
# In _modern_gl_cell.py
_TRACKER_KEY_PREFIX = "_nxn_centers_track:"  # Duplicated (acceptable)

def get_tracker_color(self) -> Color | None:
    """Get tracker color if this cell is marked."""
    c_attrs = self._part_edge.c_attributes
    for key, value in c_attrs.items():
        if isinstance(key, str) and key.startswith(_TRACKER_KEY_PREFIX):
            return value  # Value IS the Color enum
    return None
```

## For Edge Trackers (Future)

When implementing edge trackers, follow this pattern:

1. **Create new factory** (or extend existing):
   - `NxNEdgeFaceTrackers` or add methods to existing factory
   - Factory receives `holder_id` from holder
   - Factory creates appropriate tracker type

2. **Decide tracker type**:
   - If edge can be identified by color/position predicate → `SimpleFaceTracker`
   - If edge needs a marker in `c_attributes` → `MarkedFaceTracker` or new subclass

3. **Key format** (if marked):
   ```python
   key = f"_nxn_edges_track:h{holder_id}:{edge_id}{unique_id}"
   edge.c_attributes[key] = identifying_color
   ```

4. **Renderer**:
   - Add `_EDGE_TRACKER_KEY_PREFIX` constant
   - Add `get_edge_tracker_color()` method to cell
   - Generate indicator vertices for edge trackers

5. **Tests**:
   - Test multiple holders coexist
   - Test cleanup only removes own markers
   - Test scramble/solve cycle works
