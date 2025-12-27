# Edge-Face Coordinate System: Approach 2

## New Foundational Assumptions

This document presents an alternative interpretation of the edge coordinate system,
based on clearer foundational assumptions.

---

## The Key Insight: Face-Centric Consistency

### Assumption 1: Each Face Has Its Own Consistent LTR System

Every face has its own left-to-right (ltr) coordinate system that is **consistent by definition**:

- `ltr=0` always means the same position on that face
- For horizontal direction: `ltr=0` = leftmost
- For vertical direction: `ltr=0` = bottommost
- This is a property of the **Face**, not of individual edges

```
    Face F's coordinate system:

         ltr=0  ltr=1  ltr=2   (horizontal, for top/bottom edges)
           ↓      ↓      ↓
         ┌─────────────────┐
    ltr=2│                 │
         │                 │
    ltr=1│        F        │   (vertical, for left/right edges)
         │                 │
    ltr=0│                 │
         └─────────────────┘
```

**The face's ltr system is not derived from edges. It IS the definition.**

---

### Assumption 2: Edges Have Internal Slice Ordering

An edge is a physical object with N slices. These slices must be stored in SOME order.
The edge picks an internal indexing: slice[0], slice[1], ..., slice[N-1].

This internal ordering is arbitrary - it just needs to be consistent.

---

### Assumption 3: Edge Arbitrarily Agrees With f1

Since an edge connects two faces, and each face has its own ltr system, the edge
must choose ONE face's perspective as its internal ordering.

**By convention: the edge's internal ordering matches f1's ltr system.**

- f1's `ltr=0` corresponds to edge's `slice[0]`
- f1's `ltr=1` corresponds to edge's `slice[1]`
- etc.

---

### Assumption 4: f2 Must Translate

The second face (f2) may or may not see the slices in the same order as f1.

The `same_direction` flag tells us:

| same_direction | Meaning | f2's translation |
|---------------|---------|------------------|
| `True` | f1 and f2 see slices in same order | f2: `ltr = slice_index` (no change) |
| `False` | f1 and f2 see slices in opposite order | f2: `ltr = N-1 - slice_index` (invert) |

---

## Implications

### Face Consistency is GUARANTEED

With these assumptions, each face's ltr system is consistent **by construction**:

- The ltr system is defined at the Face level
- Edges just provide translation to/from their internal indices
- Different edges of the same face may use different translations, BUT
- They all translate to/from the SAME face-level ltr system

### No "Agreement" Check Needed Between Opposite Edges

The old approach asked: "Do left and right edges agree?"

The new approach says: **This question doesn't make sense.**

- Left and right edges are different physical objects
- They have different internal slice orderings
- They both translate to the SAME face ltr system
- The translations may be different, but the result (face ltr) is the same

### The Critical Insight: Edge-Face LTR = Face LTR

When you access an edge from a face, you're accessing that face's **PartEdge** (edge-face).
The ltr coordinate on that edge-face **IS** the face's ltr coordinate.

This is guaranteed by the translation layer:

```
    Face F asks edge E: "Give me slice at ltr=2"

    Edge E translates:
    - If F is f1: slice_index = 2 (direct)
    - If F is f2 and same_direction=False: slice_index = N-1-2 (inverted)

    The result: F always gets the slice at F's ltr=2 position
```

**This replaces the old insight.** We don't need edges to "agree" - we need each edge
to correctly translate the face's ltr to its internal index. The edge serves the face.

---

## Translation Functions

### Edge → Face LTR

```python
def get_ltr_index_from_slice_index(self, face: Face, slice_i: int) -> int:
    """Convert edge's internal slice index to face's ltr coordinate."""
    if self.same_direction:
        return slice_i  # Both faces see same order
    else:
        if face is self._f1:
            return slice_i  # f1's ltr matches edge's internal order
        else:
            return self.inv_index(slice_i)  # f2 sees inverted order
```

### Face LTR → Edge

```python
def get_slice_index_from_ltr_index(self, face: Face, ltr_i: int) -> int:
    """Convert face's ltr coordinate to edge's internal slice index."""
    if self.same_direction:
        return ltr_i  # Both faces see same order
    else:
        if face is self._f1:
            return ltr_i  # f1's ltr matches edge's internal order
        else:
            return self.inv_index(ltr_i)  # f2 sees inverted order
```

---

## Face Rotation: How It Uses the Translation Layer

When a face rotates clockwise, colors move: LEFT → TOP → RIGHT → BOTTOM → LEFT

### Face's LTR Coordinate System

```
┌─────────────────────────────────────┐
│            TOP (horizontal)         │
│           ltr: 0 → 1 → 2            │
│         ┌─────────────┐             │
│  LEFT   │             │   RIGHT     │
│  (vert) │      F      │   (vert)    │
│  ltr:   │             │   ltr:      │
│   2 ↑   │             │   2 ↑       │
│   1 │   │             │   1 │       │
│   0 ┘   │             │   0 ┘       │
│         └─────────────┘             │
│           ltr: 0 → 1 → 2            │
│           BOTTOM (horizontal)       │
└─────────────────────────────────────┘
```

### Clockwise Rotation Mapping

```
LEFT[ltr=0] ──→ TOP[ltr=0]      (bottom of left → left of top)
LEFT[ltr=2] ──→ TOP[ltr=2]      (top of left → right of top)

TOP[ltr=0]  ──→ RIGHT[ltr=2]    (left of top → TOP of right = INVERTS!)
TOP[ltr=2]  ──→ RIGHT[ltr=0]    (right of top → bottom of right)
```

### The Pattern

```
LEFT[ltr] → TOP[ltr] → RIGHT[inv(ltr)] → BOTTOM[inv(ltr)] → LEFT[ltr]
```

### Why This Is Brilliant

The face rotation code works **entirely in the face's own ltr system**:

```python
for index in range(n_slices):
    top_ltr_index = saved_top.get_ltr_index_from_slice_index(self, index)

    i_left   = e_left.get_slice_index_from_ltr_index(self, top_ltr_index)
    i_right  = e_right.get_slice_index_from_ltr_index(self, inv(top_ltr_index))
    i_bottom = e_bottom.get_slice_index_from_ltr_index(self, inv(top_ltr_index))
```

- The `inv()` handles the rotation geometry (adjacent edges have opposite ltr directions)
- The `get_slice_index_from_ltr_index()` handles f1/f2 translation automatically
- The face never needs to know if it's f1 or f2 in any edge!

---

## Slice Rotation: The Physical Alignment Problem

Slice rotation (M, E, S, or any slice) moves colors around **4 faces**.

### The Problem: Physical Alignment

When a user rotates slice 2, they see a **visual line** going around the cube:

```
         ┌─────────┐
         │  Face U │
         │ slice ? │  ← Must align with F's slice 2!
         └─────────┘
              │
    ┌─────────┼─────────┐
    │ slice ? │ slice 2 │ slice ?
    │ Face L  │ Face F  │ Face R
    └─────────┴─────────┴─────────┘
              │
         ┌─────────┐
         │  Face D │
         │ slice ? │
         └─────────┘
```

**The challenge:** Each face stores slices in its own internal order. Face F's
internal index 2 might be Face U's internal index 0!

But the user expects them to be **physically aligned** - the same visual line.

### The Solution: Edge as Bridge

Two adjacent faces share an edge. The edge translates between their ltr systems:

```python
# We're at ltr=2 on current_face, moving to next_face
# Both faces share next_edge

# Step 1: Convert current_face's ltr to edge's internal index
next_slice_index = next_edge.get_slice_index_from_ltr_index(current_face, current_index)

# Step 2: Convert edge's internal index to next_face's ltr
current_index = next_edge.get_ltr_index_from_slice_index(next_face, next_slice_index)
```

**The edge is the bridge:**

```
current_face ltr=2
       │
       ▼
edge internal index (via translation)
       │
       ▼
next_face ltr=? (physically aligned!)
```

### Why This Works

The ltr coordinate system is designed so that:
- **Same ltr on shared edge = same physical slice**
- The translation layer handles different internal storage orders
- Result: physical alignment is preserved across all 4 faces

This is why the ltr ↔ index translation was invented - to solve the physical
alignment problem for slice rotations.

See: `Slice.py:112-122` for the implementation.

### The Axis Exchange Problem

**The complexity goes deeper:** Not only does the index change, but the
**coordinate axis itself changes** as a slice moves between faces!

#### Real Example: M Slice Rotation (F → U)

The M slice is the middle vertical layer between L and R faces.
It rotates through: F → U → B → D → F

```
    Face F (front view)              Face U (top view, looking down)

         edge_top                         edge_top (U-B)
        ┌─────────┐                      ┌─────────┐
        │ · │ · │ ·│                     │ · · · │
  edge  │───┼───┼──│ edge         edge   │─────────│ edge
  left  │ · │ M │ ·│ right        left   │ · · · │ right
  (F-L) │───┼───┼──│ (F-R)        (L-U)  │─────────│ (U-R)
        │ · │ · │ ·│                     │ M M M │
        └─────────┘                      └─────────┘
         edge_bottom                      edge_bottom (F-U)

    On F: M is a COLUMN              On U: M is a ROW!
    (vertical, along T axis)         (horizontal, along R axis)
    ltr on edge_left                 ltr on edge_bottom
```

**What happened?**
- On Face F: M slice touches edge_left (VERTICAL edge), ltr = bottom→top
- On Face U: M slice touches edge_bottom (HORIZONTAL edge), ltr = left→right
- The slice moved from a VERTICAL edge to a HORIZONTAL edge!

#### How LTR Handles This

The magic: **ltr=2 on F's vertical edge = ltr=2 on U's horizontal edge**

```
    F's edge_left (vertical)         U's edge_bottom (horizontal)

         ltr=2 ─┐                         ┌─────────────┐
         ltr=1 ─┤                         │ 0   1   2   │
         ltr=0 ─┘                         └─ltr─────────┘
              connects to →                 same physical position!
```

The bottom of F's left edge (ltr=0) connects to the left of U's bottom edge (ltr=0).
The top of F's left edge (ltr=2) connects to the right of U's bottom edge (ltr=2).

**Physical alignment is preserved** because ltr values match at the connection point,
even though:
- On F, ltr represents vertical position (T axis, row index)
- On U, ltr represents horizontal position (R axis, column index)

This is handled by `Slice.py:98-108` where the code checks if the edge is
top/bottom (horizontal) vs left/right (vertical) and uses the ltr accordingly:
- Horizontal edge: `current_index` is the column position
- Vertical edge: `current_index` is the row position

---

## What Determines same_direction?

The `same_direction` flag is determined by **geometry**:

- Each face has R (right) and T (top) directions
- An edge is horizontal (along R) or vertical (along T) for each face
- If both faces' relevant directions point the same way along the edge: `True`
- If they point opposite ways: `False`

This is a fixed geometric property - not a choice.

---

## The 12 Edges

```
SAME DIRECTION (True) - 8 edges:
  F-U, F-L, F-R, F-D    (all Front edges)
  L-D, L-B, R-B, U-R

OPPOSITE DIRECTION (False) - 4 edges:
  L-U, U-B, D-R, D-B
```

---

## What Needs to be Verified in Code

With this new understanding, we need to verify that all code using ltr ↔ index
translation is consistent with these assumptions:

1. **Edge.get_ltr_index_from_slice_index** - Does it follow Assumption 3 & 4?
2. **Edge.get_slice_index_from_ltr_index** - Does it follow Assumption 3 & 4?
3. **Face rotation code** - Does it use translations correctly?
4. **Any direct ltr access** - Does it go through proper translation?

---

## Comparison: Old Approach vs New Approach

| Aspect | Old Approach | New Approach |
|--------|--------------|--------------|
| LTR ownership | Ambiguous (edge or face?) | Face owns ltr, edge translates |
| Consistency check | "Do opposite edges agree?" | Not needed - face ltr is consistent by definition |
| f1/f2 meaning | "Which face's view does edge use?" | "Edge uses f1's view, f2 translates" |
| Constraint satisfaction | Impossible (geometric conflicts) | No constraints to satisfy |

---

## Next Steps

1. Review `Edge.py` - verify `get_ltr_*` methods match new interpretation
2. Review `Face.py` - verify rotation code uses translations correctly
3. Review any other code accessing ltr coordinates
4. Remove or simplify the "edge agreement" validation if not needed

---

## If Code Matches This Interpretation

If verification confirms the code follows these assumptions:

1. **Improve this documentation** - make it the authoritative reference
2. **Add references at each usage location** - every place that uses ltr ↔ index
   translation should have a comment referencing this document:
   ```python
   # See: docs/design2/edge-face-coordinate-system-approach2.md
   ```
3. **Remove obsolete validation** - the "edge agreement" check is unnecessary

---

*Document created: 2025-12-27*
*Alternative interpretation for Issue #53*
