# Face Tracker: Tracking Face→Color Mapping for Even Cubes

## Package Structure

```
big_cube/                         # Public package
    FacesTrackerHolder.py         # PUBLIC API - the only class to import
    _FaceTracker.py               # Internal - re-exports from tracker package
    _NxNCentersFaceTracker.py     # Internal - factory implementation
    ...

tracker/                          # Internal package - DO NOT IMPORT DIRECTLY
    _base.py                      # Implementation (FaceTracker classes)
    __init__.py                   # Empty __all__ - no public exports
```

## Public API

**For Solving (holder-specific):**
```python
from cube.domain.solver.common.big_cube import FacesTrackerHolder

with FacesTrackerHolder(solver) as holder:
    face_colors = holder.face_colors
    if holder.part_match_faces(edge):
        # edge is correctly positioned
```

**For Display (holder-agnostic static methods):**
```python
from cube.domain.solver.common.big_cube import FacesTrackerHolder

# Check if a PartEdge is marked by ANY tracker
color = FacesTrackerHolder.get_tracked_edge_color(part_edge)
if color is not None:
    # Display indicator with this color
```

**Type Hints Only:**

```python
from cube.domain.tracker.trackers import FaceTracker


def get_tracker(holder: FacesTrackerHolder) -> FaceTracker:
    return holder.trackers[0]
```

## Static Methods (Holder-Agnostic)

These methods are for **display purposes only**. They detect markers from
ANY holder, not a specific one. Use when holder identity doesn't matter.

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `is_tracked_slice(s)` | CenterSlice | bool | True if ANY holder marked this slice |
| `get_tracked_slice_color(s)` | CenterSlice | Color \| None | Color from ANY holder |
| `get_tracked_edge_color(edge)` | PartEdge | Color \| None | Color from ANY holder |

**WARNING:** Do NOT use these for solver logic - they ignore holder identity!

---

**Internal Classes (don't import directly):**
- `FaceTracker` - Abstract base tracker (`tracker/_base.py`)
- `SimpleFaceTracker` - Tracker with predicate, no cleanup
- `MarkedFaceTracker` - Tracker with marked slice, needs cleanup
- `NxNCentersFaceTrackers` - Factory for creating trackers

**Used By:**
- `LayerByLayerNxNSolver` (`solver/direct/lbl/`) - Layer-by-layer big cube solver
- `CageNxNSolver` (`solver/direct/cage/`) - Cage method solver
- `BeginnerReducer` (`solver/reducers/beginner/`) - Center and edge reduction
- `NxNCenters` (this directory) - Common center solving logic
- `ShadowCubeHelper` (this directory) - Shadow cube creation
- `_modern_gl_cell.py` (renderer) - Display tracker indicators

---

## The Problem

On even cubes (4x4, 6x6), the standard `Part.match_faces` check fails when only
Layer 1 centers are solved.

### Standard match_faces Behavior

`Part.match_faces` checks if a piece's colors match its face's center colors:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Part.match_faces compares:                                         │
│                                                                      │
│  piece.sticker_color  ==  face.center_color                         │
│         ↓                       ↓                                    │
│     (actual)              (from center)                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Works on 3x3 and Fully Reduced NxN

On a 3x3 or fully reduced NxN cube, each face has uniform center color:

```
        3x3 Cube (or fully reduced 4x4)
        ================================

                 U (WHITE)
               ┌───────────┐
               │  W  W  W  │  ← All centers WHITE
               │  W  W  W  │
               │  W  W  W  │
               └───────────┘
       L (BLUE)     F (ORANGE)    R (GREEN)
      ┌─────────┐  ┌─────────┐  ┌─────────┐
      │ B  B  B │  │ O  O  O │  │ G  G  G │
      │ B  B  B │  │ O  O  O │  │ G  G  G │
      │ B  B  B │  │ O  O  O │  │ G  G  G │
      └─────────┘  └─────────┘  └─────────┘

      face.color returns the uniform center color ✓
      match_faces works correctly ✓
```

### Fails on Partially Solved Even Cubes

After LBL Layer 1 solve, only L1 (WHITE) centers are solved. Other faces have
scrambled centers:

```
        4x4 After LBL L1 Centers Solve
        ================================

                 U (WHITE - SOLVED)
               ┌───────────┐
               │  W  W  W  │  ← All WHITE ✓
               │  W  W  W  │
               │  W  W  W  │
               └───────────┘
       L (SCRAMBLED)  F (SCRAMBLED)  R (SCRAMBLED)
      ┌─────────┐    ┌─────────┐    ┌─────────┐
      │ R  B  B │    │ Y  G  Y │    │ Y  G  R │
      │ B  G  G │    │ O  R  R │    │ G  B  B │
      │ Y  B  B │    │ R  G  G │    │ O  Y  Y │
      └─────────┘    └─────────┘    └─────────┘

      face.color returns... what? Majority? First? ✗
      match_faces gives WRONG answers! ✗
```

---

## The Solution: Tracker-Based Matching

Use the tracker's `face→color` dictionary instead of actual center colors.

### How Trackers Work

Trackers mark specific center slices and follow them as the cube rotates:

```
     Tracker Creation (on scrambled cube)
     =====================================

     1. Find which color has majority on each face
     2. Mark a representative center slice
     3. Tracker.face returns current face of marked slice
     4. Tracker.color returns the target color for that face

     ┌──────────────────────────────────────────────────┐
     │  Tracker says: "Face U should have WHITE"        │
     │  Tracker says: "Face F should have ORANGE"       │
     │  ... etc for all 6 faces                         │
     └──────────────────────────────────────────────────┘
```

### Odd vs Even Cube Trackers

| Cube Type | Tracker Method | Cleanup Needed |
|-----------|----------------|----------------|
| Odd (3x3, 5x5, 7x7) | Use fixed center piece color | No |
| Even (4x4, 6x6) | Mark and track center slices | Yes |

For **odd cubes**, the center piece is fixed and unique - its color defines the face.

For **even cubes**, there's no single center - trackers mark a specific slice and
follow it through rotations.

---

## Tracker Class Hierarchy

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
- Opposite trackers                 - (Future: Edge trackers)
- f5/f6 BOY-based trackers
```

### SimpleFaceTracker

Used when face can be found via a predicate (no marking needed):

```python
class SimpleFaceTracker(FaceTracker):
    __slots__ = ["_pred"]

    def __init__(self, cube: Cube, color: Color, pred: Pred[Face]) -> None:
        super().__init__(cube, color)
        self._pred = pred

    @property
    def face(self) -> Face:
        return self._cube.cqr.find_face(self._pred)

    def cleanup(self) -> None:
        pass  # No-op - nothing to clean
```

**Use cases:**
- **Odd cube trackers**: Predicate checks `face.center.color == target_color`
- **Opposite trackers**: Predicate checks `face.opposite is first_tracker.face`
- **f5/f6 trackers**: Predicate uses BOY constraints

### MarkedFaceTracker

Used when a center slice must be marked with a key in `c_attributes`:

```python
class MarkedFaceTracker(FaceTracker):
    __slots__ = ["_key"]

    def __init__(self, cube: Cube, color: Color, key: str) -> None:
        super().__init__(cube, color)
        self._key = key

    @property
    def face(self) -> Face:
        # Search for which face contains the marked slice
        def _slice_pred(s: CenterSlice) -> bool:
            return self._key in s.edge.c_attributes

        def _face_pred(_f: Face) -> bool:
            return _f.cube.cqr.find_slice_in_face_center(_f, _slice_pred) is not None

        return self._cube.cqr.find_face(_face_pred)

    def cleanup(self) -> None:
        # Search and remove the key
        for f in self._cube.faces:
            for s in f.center.all_slices:
                if self._key in s.edge.c_attributes:
                    del s.edge.c_attributes[self._key]
                    return
```

**Key points:**
- Stores only the `_key` string, NOT an edge reference
- Edge references become stale during rotations - must search each time
- `cleanup()` searches all slices to find and remove its specific key

---

## Per-Holder Marker IDs

Each `FacesTrackerHolder` instance gets a unique ID. Tracker keys include this ID
so multiple holders can coexist safely.

### Why Per-Holder IDs?

**Problem:** With context managers, multiple holders exist simultaneously:
- `status` property creates a holder to check solve state
- `_solve_impl` creates a holder for actual solving
- When `status` cleans up, it was removing `_solve_impl` markers!

**Solution:** Each holder only cleans up its OWN markers:

```
Key format: "_nxn_centers_track:h{holder_id}:{color}{unique_id}"
Example:    "_nxn_centers_track:h42:WHITE1"
                                ^^^ holder_id
```

### Implementation

```python
class FacesTrackerHolder:
    _holder_unique_id: int = 0  # Class counter

    def __init__(self, slv, trackers=None):
        # Generate unique ID
        FacesTrackerHolder._holder_unique_id += 1
        self._holder_id = FacesTrackerHolder._holder_unique_id

        if trackers is None:
            # Factory receives holder_id for key creation
            factory = NxNCentersFaceTrackers(slv, self._holder_id)
            self._trackers = self._create_trackers(factory)

    def cleanup(self):
        # Polymorphic - each tracker knows what to clean
        for tracker in self._trackers:
            tracker.cleanup()
```

### Factory Creates Keys

Only the factory (`NxNCentersFaceTrackers`) needs `holder_id`:

```python
class NxNCentersFaceTrackers:
    _global_tracer_id: int = 0  # For unique keys

    def __init__(self, slv, holder_id: int):
        self._holder_id = holder_id

    def _create_tracker_by_center_piece(self, _slice: CenterSlice) -> MarkedFaceTracker:
        NxNCentersFaceTrackers._global_tracer_id += 1
        unique_id = NxNCentersFaceTrackers._global_tracer_id

        # Key includes holder_id for safe multi-holder cleanup
        key = f"{TRACKER_KEY_PREFIX}h{self._holder_id}:{_slice.color}{unique_id}"

        # Store Color as VALUE (renderer reads directly)
        _slice.edge.c_attributes[key] = _slice.color

        return MarkedFaceTracker(_slice.parent.cube, _slice.color, key)
```

---

## Renderer Integration (GUI)

The renderer shows small colored circles on tracked center slices.

### How Renderer Finds Tracked Slices

```python
# In _modern_gl_cell.py
_TRACKER_KEY_PREFIX = "_nxn_centers_track:"

def get_tracker_color(self) -> Color | None:
    """Get tracker color if this cell is marked."""
    c_attrs = self._part_edge.c_attributes
    for key, value in c_attrs.items():
        if isinstance(key, str) and key.startswith(_TRACKER_KEY_PREFIX):
            return value  # Value IS the Color enum
    return None
```

### Color Storage

Color is stored as the VALUE, not encoded in the key:

```python
# In factory:
edge.c_attributes[key] = _slice.color  # Color enum as value

# In renderer:
for key, value in c_attrs.items():
    if key.startswith(_TRACKER_KEY_PREFIX):
        return value  # Just read the Color directly
```

This avoids parsing key strings and keeps the design clean.

---

### part_match_faces Implementation

```python
def part_match_faces(self, part: Part) -> bool:
    """Check if part colors match TRACKER-assigned face colors."""
    face_colors = self.face_colors  # {F: ORANGE, U: WHITE, ...}
    for edge in part._3x3_representative_edges:
        expected_color = face_colors.get(edge.face.name)
        if edge.color != expected_color:
            return False
    return True
```

### Comparison Diagram

```
    Standard match_faces          vs      Tracker-based part_match_faces
    =====================               ================================

    piece.color == face.center_color    piece.color == tracker[face].color
         ↓              ↓                     ↓              ↓
      ORANGE    ==   ???(scrambled)        ORANGE    ==    ORANGE
                         ✗                                    ✓

    ┌─────────────────────────────────────────────────────────────────┐
    │  The tracker KNOWS face F should be ORANGE, even if centers     │
    │  are scrambled. It tracks this through cube rotations.          │
    └─────────────────────────────────────────────────────────────────┘
```

---

## Cache Invalidation

### The Problem with Naive Caching

Initially, we tried to cache the `face_colors` dictionary:

```python
# WRONG - cache becomes stale after rotations!
def get_face_colors(self):
    if self._cache is None:
        self._cache = {t.face.name: t.color for t in self._trackers}
    return self._cache
```

### Cache Staleness After Rotation

```
    Before Y Rotation              After Y Rotation
    ==================             =================

    Tracker marked slice           Marked slice moved!
    on face F                      now on face R

        ┌───┐                          ┌───┐
      ┌─│ U │─┐                      ┌─│ U │─┐
      │ └───┘ │                      │ └───┘ │
    ┌─┴─┐ ┌─┴─┐                    ┌─┴─┐ ┌─┴─┐
    │ L │ │[F]│ ← marked           │ L │ │ F │
    └─┬─┘ └─┬─┘                    └─┬─┘ └─┬─┘
      │ ┌───┐ │          Y           │ ┌───┐ │
      └─│ D │─┘        ─────→        └─│ D │─┘
        └───┘                          └───┘

    Cache: {F: ORANGE}             Cache STILL says {F: ORANGE}
                                   But tracker.face now returns R!
                                   Should be {R: ORANGE}! ✗
```

### Solution: Smart Cache with modify_counter

```python
def get_face_colors(self) -> dict[FaceName, Color]:
    """Get face→color mapping with auto-invalidation."""
    current_counter = self._cube._modify_counter
    if self._cache is not None and self._cache_modify_counter == current_counter:
        return self._cache  # Cache still valid

    # Rebuild - cube was modified
    self._cache = {t.face.name: t.color for t in self._trackers}
    self._cache_modify_counter = current_counter
    return self._cache
```

The `cube._modify_counter` increments on every rotation, allowing automatic
cache invalidation without manual tracking.

---

## Usage Patterns

### Pattern 1: Context Manager (Recommended)

```python
# Automatic cleanup when done
with FacesTrackerHolder(solver) as th:
    face_colors = th.face_colors
    if th.part_match_faces(edge):
        # edge is in correct position
        pass
# cleanup automatic
```

### Pattern 2: Long-Lived Holder

```python
# For solvers that need trackers across multiple operations
class LayerByLayerNxNSolver:
    def __init__(self):
        self._tracker_holder: FacesTrackerHolder | None = None

    @property
    def tracker_holder(self) -> FacesTrackerHolder:
        if self._tracker_holder is None:
            self._tracker_holder = FacesTrackerHolder(self)
        return self._tracker_holder

    def cleanup(self):
        if self._tracker_holder:
            self._tracker_holder.cleanup()
```

### Pattern 3: Passing to Sub-Solvers

```python
# Centers, edges, corners can all use the same tracker holder
with FacesTrackerHolder(solver) as th:
    centers = NxNCenters(solver)
    centers.solve(th)  # Uses th.face_colors for target colors

    edges = NxNEdges(solver)
    edges.solve(th)    # Same face→color mapping
```

---

## Tracker Creation Algorithm

For even cubes, trackers are created in order of confidence:

1. **track_no_1**: Find face with clearest majority color (e.g., U has 4 WHITE)
2. **track_opposite**: Opposite face gets opposite color (D gets YELLOW)
3. **_track_no_3**: Find next best majority from remaining faces
4. **track_opposite**: Its opposite gets opposite color
5. **_track_two_last**: Remaining two faces - use BOY constraints to assign

The BOY (Blue-Orange-Yellow) constraint ensures the final layout is valid:
- If U=WHITE, D must be YELLOW
- If F=ORANGE, B must be RED
- Opposite faces have opposite colors

---

## Known Issues

### Potential Majority Algorithm Bug

**Status:** Under investigation - See GitHub issue #51

When faces have **even color distribution** (no clear majority), the tie-breaking
is arbitrary. This could theoretically assign the same color to multiple faces.

Current investigation shows the BOY constraint check in `_track_two_last` prevents
this, but edge cases may exist.

See: `tests/solvers/test_tracker_majority_bug.py` for test coverage.

---

## See Also

- `FacesTrackerHolder` class - Main interface
- `FaceTracker` class - Individual tracker
- `Part.match_faces` - Standard matching (uses center colors)
- GitHub #51 - Tracker majority algorithm investigation
