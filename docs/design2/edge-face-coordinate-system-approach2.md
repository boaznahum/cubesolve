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
