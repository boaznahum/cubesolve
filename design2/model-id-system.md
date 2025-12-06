# Model ID System - Visual Documentation

This document provides visual diagrams explaining the three ID types in the cube model.

---

## Overview: Three Types of IDs

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ID SYSTEM SUMMARY                                  │
├─────────────────┬───────────────────────┬───────────────────────────────────┤
│ ID Type         │ Based On              │ Changes When                      │
├─────────────────┼───────────────────────┼───────────────────────────────────┤
│ fixed_id        │ Face NAMES (F,R,U...) │ NEVER                             │
│ position_id     │ Face CENTER colors    │ Slice/cube rotation (M,E,S,x,y,z) │
│ colors_id       │ Actual part colors    │ ANY rotation                      │
└─────────────────┴───────────────────────┴───────────────────────────────────┘
```

---

## 1. fixed_id - Structural Identity

**Definition:** Based on face NAMES (enum values), never changes.

**Purpose:** Identifies the physical SLOT in the cube structure.

```
                    ┌───────────┐
                    │     U     │
                    │  (Yellow) │
                    └─────┬─────┘
          ┌───────────┐   │   ┌───────────┐
          │     L     │───┼───│     R     │
          │  (Orange) │   │   │   (Red)   │
          └───────────┘   │   └───────────┘
                    ┌─────┴─────┐
                    │     F     │
                    │  (Blue)   │
                    └───────────┘

    Edge at Front-Up position:

    fixed_id = frozenset({FaceName.F, FaceName.U})
                         ▲           ▲
                         │           │
                    Face NAME   Face NAME
                    (not color!)

    This NEVER changes, even if you rotate the whole cube!
```

**Code location:** `Part.fixed_id`, `PartSlice.fixed_id`

**Formula:**
```python
# For PartSlice:
fixed_id = frozenset(tuple([index]) + tuple(edge.face.name for edge in edges))

# For Part:
fixed_id = frozenset(slice.fixed_id for slice in all_slices)
```

---

## 2. position_id - Target Position by Face Colors

**Definition:** Colors of the FACES the part is currently ON.

**Purpose:** Tells you where a part SHOULD go (based on face center colors).

```
    SOLVED CUBE (BOY orientation):

                    ┌───────────┐
                    │  YELLOW   │  ← Face U center color
                    │     U     │
                    └─────┬─────┘
                          │
                    ┌─────┴─────┐
                    │   BLUE    │  ← Face F center color
                    │     F     │
                    └───────────┘

    Edge at Front-Up slot:

    position_id = frozenset({Color.BLUE, Color.YELLOW})
                            ▲              ▲
                            │              │
                    Face F's center   Face U's center
                         color            color
```

**When does position_id change?**

```
    BEFORE y rotation:           AFTER y rotation (cube rotates):

         U(Yellow)                    U(Yellow)
            │                            │
    L(Orange)─┼─R(Red)           L(Red)──┼──R(Orange)
            │                            │
         F(Blue)                      F(Green)

    Edge at F-U slot:
    position_id = {BLUE, YELLOW}     position_id = {GREEN, YELLOW}

    ⚠️ CHANGED! Because face F now has GREEN center (was back face)
```

**Code location:** `Part.position_id`

**Formula:**
```python
position_id = frozenset(edge.face.color for edge in _3x3_representative_edges)
#                              ▲
#                     Face's CENTER color (not the part's color!)
```

---

## 3. colors_id - Actual Part Colors

**Definition:** The ACTUAL colors currently visible on the part.

**Purpose:** Identifies WHICH piece this is (by its sticker colors).

```
    SCRAMBLED STATE EXAMPLE:

                    ┌───────────┐
                    │  YELLOW   │  ← Face U center
                    │    ┌─┐    │
                    │    │R│    │  ← But this edge has RED sticker!
                    └────┴─┴────┘
                          │
                    ┌─────┴─────┐
                    │    ┌─┐    │
                    │    │W│    │  ← And WHITE sticker on F side!
                    │   BLUE    │  ← Face F center
                    └───────────┘

    This edge (White-Red piece) is in the F-U slot:

    position_id = {BLUE, YELLOW}     ← Where it IS (slot identity)
    colors_id   = {WHITE, RED}       ← What it IS (piece identity)

    in_position = (position_id == colors_id) = FALSE!

    The White-Red edge SHOULD be at the Down-Right slot
    (where White and Red faces meet)
```

**Code location:** `Part.colors_id`, `PartSlice.colors_id`

**Formula:**
```python
colors_id = frozenset(edge.color for edge in _3x3_representative_edges)
#                          ▲
#                  The sticker's ACTUAL color
```

---

## Visual: How IDs Change During Rotation

### Face Rotation (F move)

```
    BEFORE F rotation:                AFTER F rotation:

           U                                U
        ┌──┴──┐                          ┌──┴──┐
        │Y │Y │                          │O │Y │
        ├──┼──┤                          ├──┼──┤
      L │O │B │ R                      L │Y │B │ R
        ├──┼──┤                          ├──┼──┤
        │O │B │                          │O │B │
        └──┬──┘                          └──┬──┘
           F                                F

    Edge at F-U position:

    fixed_id:    {F, U}              {F, U}         ← SAME (structure)
    position_id: {BLUE, YELLOW}      {BLUE, YELLOW} ← SAME (faces unchanged)
    colors_id:   {YELLOW, BLUE}      {ORANGE, BLUE} ← CHANGED! (colors moved)
```

### Slice Rotation (M move)

```
    BEFORE M rotation:                AFTER M rotation:

    Face centers move!

           U(Y)                            U(B)  ← Was Front's color!
        ┌──┴──┐                          ┌──┴──┐
        │  │  │                          │  │  │
      L │  │  │ R                      L │  │  │ R
        │  │  │                          │  │  │
        └──┬──┘                          └──┬──┘
           F(B)                            F(W)  ← Was Down's color!

    Edge at F-U position:

    fixed_id:    {F, U}              {F, U}         ← SAME
    position_id: {BLUE, YELLOW}      {WHITE, BLUE}  ← CHANGED! (face colors moved)
    colors_id:   changes...          changes...     ← Also changes
```

---

## Phase 1 vs Phase 2: Which IDs Matter?

### Phase 1: Big Cube (before reduction)

```
    5x5 EDGE (not reduced):

    ┌───┬───┬───┐
    │ R │ O │ R │  ← 3 different slices with DIFFERENT colors!
    ├───┼───┼───┤
    │ B │ G │ B │
    └───┴───┴───┘

    Slice 0: colors_id = {RED, BLUE}
    Slice 1: colors_id = {ORANGE, GREEN}  ← Different!
    Slice 2: colors_id = {RED, BLUE}

    Edge.colors_id = uses MIDDLE slice = {ORANGE, GREEN}

    ⚠️ Edge.colors_id is MEANINGLESS here!
    ⚠️ Edge.is3x3 = FALSE

    Solver uses: slice.colors_id (individual slices)
```

### Phase 2: After Reduction (3x3 mode)

```
    5x5 EDGE (after reduction):

    ┌───┬───┬───┐
    │ R │ R │ R │  ← All slices have SAME colors!
    ├───┼───┼───┤
    │ B │ B │ B │
    └───┴───┴───┘

    Slice 0: colors_id = {RED, BLUE}
    Slice 1: colors_id = {RED, BLUE}  ← Same!
    Slice 2: colors_id = {RED, BLUE}  ← Same!

    Edge.colors_id = {RED, BLUE}  ← NOW MEANINGFUL!
    Edge.is3x3 = TRUE

    Solver uses: edge.colors_id, edge.in_position, edge.match_faces
```

---

## Solver Usage Patterns

### NxNEdges.py (Phase 1 - Big Cube)

```python
# Works with SLICES, not Parts
for i in range(n_slices):
    a_slice = edge.get_slice(i)
    a_slice_id = a_slice.colors_id  # ← Slice-level colors_id
    if a_slice_id != target_color:
        # fix this slice
```

### L1Cross.py (Phase 2 - 3x3)

```python
# Works with PARTS
color_codes = Part.parts_id_by_pos(wf.edges)  # ← position_id
for color_id in color_codes:
    source_edge = cube.find_edge_by_color(color_id)  # ← colors_id
    if source_edge.match_faces:  # ← Only valid in 3x3!
        continue
```

### Tracker.py (Phase 2 - Part tracking)

```python
class PartTracker:
    def __init__(self, color_id):
        self._color_id = color_id  # Track by colors_id

    @property
    def position(self):
        # Find where this color SHOULD be (by position_id)
        return find_part_by_position(self._color_id)

    @property
    def actual(self):
        # Find where this color IS (by colors_id)
        return find_part_by_color(self._color_id)
```

---

## Key Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                     PART STATE CHECKS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  in_position = (position_id == colors_id)                       │
│                                                                 │
│      TRUE  → Part is in correct SLOT (but maybe wrong orient)   │
│      FALSE → Part needs to move to different slot               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  match_faces = all(edge.color == edge.face.color)               │
│                                                                 │
│      TRUE  → Part is SOLVED (correct slot AND orientation)      │
│      FALSE → Part needs adjustment                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  is3x3 = all slices have same colors                            │
│                                                                 │
│      TRUE  → Part-level methods (colors_id, etc.) are valid     │
│      FALSE → Use slice-level methods only!                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Code References

| Property | File | Line | Description |
|----------|------|------|-------------|
| `Part.fixed_id` | Part.py | ~89 | Structure-based ID |
| `Part.position_id` | Part.py | ~217 | Face-color-based target |
| `Part.colors_id` | Part.py | ~252 | Actual sticker colors |
| `Part.in_position` | Part.py | ~203 | position_id == colors_id |
| `Part.match_faces` | Part.py | ~191 | All colors match faces |
| `Edge.is3x3` | Edge.py | ~59 | All slices aligned |
| `PartSlice.colors_id` | _part_slice.py | ~226 | Slice-level colors |

---

*Document created: 2025-12-06*
*Source: Deep analysis of model/ package*
