# Face Tracker: Tracking Face→Color Mapping for Even Cubes

**Related Classes:**
- `FacesTrackerHolder` - Main interface (this directory)
- `FaceTracker` - Individual face tracker (`_FaceTracker.py`)
- `NxNCentersFaceTrackers` - Tracker creation for even cubes (`_NxNCentersFaceTracker.py`)

**Used By:**
- `LayerByLayerNxNSolver` (`solver/direct/lbl/`) - Layer-by-layer big cube solver
- `CageNxNSolver` (`solver/direct/cage/`) - Cage method solver
- `BeginnerReducer` (`solver/reducers/beginner/`) - Center and edge reduction
- `NxNCenters` (this directory) - Common center solving logic
- `ShadowCubeHelper` (this directory) - Shadow cube creation

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
