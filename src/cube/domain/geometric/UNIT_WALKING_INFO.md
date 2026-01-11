# Unit Walking Info - Size-Independent Geometry

This document explains the **Unit Walking Info** pattern - a key architectural insight that allows computing cube geometry once and applying it to any cube size.

## The Problem

When traversing cube faces along a slice (M, E, or S), we need to know:
1. Which 4 faces the slice passes through
2. The entry edge on each face
3. How coordinates transform between faces
4. Reference points for each face

**The challenge:** These calculations involve coordinate indices that depend on `n_slices` (cube size - 2). For a 3x3 cube, `n_slices=1`. For a 7x7 cube, `n_slices=5`. How can we avoid recomputing everything for each size?

## The Insight

**Key observation:** The TOPOLOGY (which faces, which edges, how coordinates flip) is the same for ALL cube sizes. Only the actual coordinate VALUES change with size.

When we compute walking info:
- The **structure** (faces, edges, inversion flags) is size-independent
- The **coordinate values** scale linearly with `n_slices`

## Solution: Two-Phase Computation

### Phase 1: Create Unit Walking Info (Size-Independent)

Use a **fake n_slices value** (e.g., 1234) to compute the walking info structure:

```python
def _create_walking_info_unit(self, slice_name: SliceName) -> CubeWalkingInfoUnit:
    fake_n_slices = 1234  # Arbitrary placeholder

    # ... traverse faces, compute edge properties ...

    # Store the FUNCTION that computes points, not the points themselves
    face_infos.append(FaceWalkingInfoUnit(
        face=current_face,
        edge=current_edge,
        reference_point=reference_point,  # Using fake_n_slices
        n_slices=fake_n_slices,
        _compute=compute  # Function: (n_slices, row, col) -> Point
    ))
```

The `_compute` function captures the **inversion logic** (is_horizontal, is_slot_inverted, is_index_inverted) but takes `n_slices` as a parameter:

```python
def _compute_h_si_ii(actual_n_slices: int, si: int, sl: int) -> Point:
    return (actual_inv(actual_n_slices, sl), actual_inv(actual_n_slices, si))
```

### Phase 2: Convert to Sized Walking Info

When we need walking info for a specific cube size:

```python
def create_walking_info(self, slice_name: SliceName) -> CubeWalkingInfo:
    # Get the unit (size-independent) walking info
    unit: CubeWalkingInfoUnit = self._create_walking_info_unit(slice_name)

    n_slices = self._cube.n_slices  # Actual cube size

    for uf in unit.face_infos:
        # Scale reference point to actual size
        reference_point: Point = uf.get_reference_point(n_slices)

        # Bind the compute function to actual size
        compute: PointComputer = uf.get_compute(n_slices)

        # Create sized face info
        sized_face_info = FaceWalkingInfo(
            face=cube.face(uf.face.name),
            edge=cube.edge(uf.edge.name),
            reference_point=reference_point,
            n_slices=n_slices,
            _compute=compute
        )
```

## Data Structures

### FaceWalkingInfoUnit (Size-Independent)

```python
@dataclass(frozen=True)
class FaceWalkingInfoUnit:
    face: "Face"           # From internal 3x3 cube
    edge: "Edge"           # Entry edge
    reference_point: Point # Using fake n_slices
    n_slices: int          # The fake n_slices value
    _compute: UnitPointComputer  # (n_slices, row, col) -> Point

    def get_reference_point(self, actual_n_slices: int) -> Point:
        """Scale reference point to actual size."""
        # Reference points are at edges (0 or n_slices-1)
        # If stored as fake_n_slices-1, scale to actual_n_slices-1
        # If stored as 0, stays 0

    def get_compute(self, n_slices_actual: int) -> PointComputer:
        """Bind compute function to actual size."""
        return lambda r, c: self._compute(n_slices_actual, r, c)
```

### FaceWalkingInfo (Size-Specific)

```python
@dataclass(frozen=True)
class FaceWalkingInfo:
    face: "Face"           # From actual cube
    edge: "Edge"           # Entry edge
    reference_point: Point # Actual coordinates
    n_slices: int          # Actual n_slices
    _compute: PointComputer  # (row, col) -> Point (size bound)
```

## Why fake_n_slices=1234 Instead of n_slices=1?

The internal 3x3 cube has `n_slices = 3 - 2 = 1`, so max index = 0.

**Problem:** With n_slices=1, BOTH "start" (0) AND "end" (n_slices-1 = 0) are the SAME value!

```
reference_point = (0, 0) is AMBIGUOUS:
  (a) row at START, col at START  →  scales to (0, 0)
  (b) row at START, col at END    →  scales to (0, n-1)
```

We can't distinguish these cases with n_slices=1!

**Solution:** Use a large fake value (1234) so start and end are distinct:
- "at start" = 0
- "at end" = 1233

Now scaling works correctly for any target size.

## Reference Point Scaling

Reference points are always at face edges (slot=0, slice_index=0). Their coordinates are either:
- `0` (stays 0 for any size)
- `fake_n_slices - 1` (scales to `actual_n_slices - 1`)

```python
def get_reference_point(self, actual_n_slices: int) -> Point:
    r = self.reference_point[0]
    if r > 0:
        assert r == self.n_slices - 1  # Must be at edge
        r_actual = actual_n_slices - 1
    else:
        r_actual = 0

    c = self.reference_point[1]
    if c > 0:
        assert c == self.n_slices - 1  # Must be at edge
        c_actual = actual_n_slices - 1
    else:
        c_actual = 0

    return r_actual, c_actual
```

## Compute Functions

Eight variants based on three boolean flags:
- `is_horizontal`: Edge is top/bottom (vs left/right)
- `is_slot_inverted`: Top/right edges invert slot
- `is_index_inverted`: Current slice index is at max (not 0)

```python
# Horizontal edge, slot inverted, index inverted
def _compute_h_si_ii(n_slices, si, sl): return (inv(n_slices, sl), inv(n_slices, si))

# Horizontal edge, slot inverted, index not inverted
def _compute_h_si(n_slices, si, sl): return (inv(n_slices, sl), si)

# ... 6 more variants ...
```

## Architecture Diagram

```
                    Internal 3x3 Cube
                          │
                          ▼
            ┌─────────────────────────────┐
            │  _create_walking_info_unit  │
            │  (uses fake_n_slices=1234)  │
            └─────────────┬───────────────┘
                          │
                          ▼
            ┌─────────────────────────────┐
            │   CubeWalkingInfoUnit       │
            │   (size-independent)        │
            │   - Face references         │
            │   - Edge references         │
            │   - Compute functions       │
            │   - Reference points (fake) │
            └─────────────┬───────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  3x3     │   │  5x5     │   │  7x7     │
    │ n_slices │   │ n_slices │   │ n_slices │
    │   = 1    │   │   = 3    │   │   = 5    │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         ▼              ▼              ▼
    CubeWalkingInfo  CubeWalkingInfo  CubeWalkingInfo
    (size-specific) (size-specific)  (size-specific)
```

## Why This Matters

1. **Performance:** Compute walking info structure once per slice, reuse for any cube size
2. **Correctness:** All coordinate logic is centralized in compute functions
3. **Testability:** Unit walking info can be validated independently of cube size
4. **Simplicity:** Consumers get `CubeWalkingInfo` with ready-to-use coordinates

## Related Files

- `cube_walking.py` - Data structures (`CubeWalkingInfo`, `CubeWalkingInfoUnit`, etc.)
- `_SizedCubeLayout.py` - Implementation of `create_walking_info()` and `_create_walking_info_unit()`
- `GEOMETRY_LAYERS.md` - Two-layer architecture (Layout vs SizedLayout)
- `CUBELAYOUT_INTERNAL_CUBE.md` - Internal 3x3 cube for geometry queries

## Summary

| Aspect | Unit (Size-Independent) | Sized (Size-Specific) |
|--------|-------------------------|----------------------|
| Class | `CubeWalkingInfoUnit` | `CubeWalkingInfo` |
| n_slices | Fake value (1234) | Actual cube size |
| reference_point | Edge coordinates (0 or fake-1) | Actual coordinates |
| _compute | `(n_slices, r, c) -> Point` | `(r, c) -> Point` |
| Source | Internal 3x3 cube | Actual cube |
| Computed | Once per slice type | On demand per cube size |
