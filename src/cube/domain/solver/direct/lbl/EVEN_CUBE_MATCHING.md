# Even Cube Matching: Using Tracker Colors Instead of Center Colors

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

## Why Cache Invalidation Matters

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

### Solution: Rebuild Each Time

```python
def get_face_colors(self) -> dict[FaceName, Color]:
    """Always rebuild - trackers follow rotations."""
    return {t.face.name: t.color for t in self._trackers}
```

This ensures we always get the **current** face→color mapping, even after
cube rotations during solving.

## Usage in LBL Solver

```python
# In LayerByLayerNxNSolver

def _is_layer1_cross_solved(self, th: FacesTrackerHolder) -> bool:
    """Uses tracker's face→color mapping for even cubes."""
    l1_face = self._get_layer1_tracker(th).face
    # Use tracker colors instead of center colors
    return all(th.part_match_faces(e) for e in l1_face.edges)

def _is_layer1_corners_solved(self, th: FacesTrackerHolder) -> bool:
    """Uses tracker's face→color mapping for even cubes."""
    l1_face = self._get_layer1_tracker(th).face
    # Use tracker colors instead of center colors
    return all(th.part_match_faces(c) for c in l1_face.corners)
```

## See Also

- `FacesTrackerHolder.part_match_faces()` - The implementation
- `Part.match_faces` - Standard check (uses center colors)
- `FaceTracker` - How individual trackers work
- `STATE.md` - Overall LBL solver state
