# CubeLayout Internal Cube - Problem and Solution

## The Problem

### What is CubeLayout?

CubeLayout (abbreviated "cl") is a **template class** that describes a principle cube
(e.g., BOY - Blue-Orange-Yellow layout). It defines:
- Which color goes on which face
- Face relationships (opposite, adjacent)
- Geometric properties that are independent of cube size

When creating a Cube instance, this template is used via `Cube.__init__(layout=...)`.

### The Gap

CubeLayout needs to answer **template-level geometry questions** - questions whose
answers don't depend on a specific cube instance or size:

- "Does slice M cut rows or columns on face F?"
- "What is the rotation transform from face F to face U via slice M?"
- "What are the 4 faces that slice E passes through?"

**The problem:** When building a Cube, we don't take everything from the CubeLayout.
The Cube builds its own Face objects, Edge relationships, and geometry data
independently. This means CubeLayout is **missing** the data it needs to answer
these questions.

```
CubeLayout (template)          Cube (instance)
─────────────────────          ─────────────────
- face → color mapping         - Face objects with edges
- opposite face pairs          - Edge relationships
- adjacent faces               - Coordinate translations
- (incomplete!)                - Walking logic
                               - etc.
```

### Current Workaround

Currently, geometry methods in `_CubeLayoutGeometry` require a `Cube` instance
as a parameter, even though the answers are template-level (size-independent):

```python
# Current: requires cube instance
def create_walking_info(cube: Cube, slice_name: SliceName) -> CubeWalkingInfo:
    ...

# What we want: CubeLayout should be able to answer this
layout.create_walking_info(slice_name) -> CubeWalkingInfo
```

## The Solution: Lazy Internal Cube

### Approach

Add a lazily-initialized internal 3x3 Cube to CubeLayout. This cube provides
the Face/Edge structure needed to answer geometry questions.

```python
class _CubeLayout(CubeLayout):
    def __init__(self, ...):
        ...
        # Lazy-initialized internal 3x3 cube for geometry queries
        self._internal_cube: Cube | None = None
        self._creating_internal_cube: bool = False

    @property
    def _cube(self) -> Cube:
        """Get internal 3x3 cube (lazy initialization)."""
        if self._internal_cube is not None:
            return self._internal_cube

        # Cycle detection
        if self._creating_internal_cube:
            raise InternalSWError(
                "Circular dependency detected..."
            )

        self._creating_internal_cube = True
        try:
            self._internal_cube = Cube(3, self._sp, layout=self)
        finally:
            self._creating_internal_cube = False

        return self._internal_cube
```

### Breaking the Circular Dependency

There's a chicken-and-egg problem:
1. CubeLayout is used to CREATE a Cube
2. But now CubeLayout CONTAINS a Cube
3. To create that internal Cube, you need... a CubeLayout!

**Solution: Lazy initialization breaks the cycle:**

1. `CubeLayout.__init__()` completes **without** creating the internal Cube
2. The Cube is only created **on first access** (when geometry is queried)
3. At that point, `self` (the CubeLayout) is fully constructed and can be
   passed to `Cube.__init__()`

### Cycle Detection

If a geometry method is called during `Cube.__init__()` (before the internal
cube is ready), we detect this and raise a clear error:

```
InternalSWError: Circular dependency detected: CubeLayout._cube accessed while
creating internal cube. This indicates a geometry method was called during
Cube.__init__() that requires the internal cube.
```

## Usage Pattern

After this change, CubeLayout can answer geometry questions directly:

```python
# Before: needed a cube instance
walk_info = _CubeLayoutGeometry.create_walking_info(some_cube, SliceName.M)

# After: CubeLayout answers using its internal cube
walk_info = layout.create_walking_info(SliceName.M)
```

The internal cube is:
- Created once (on first geometry query)
- Always 3x3 (minimal size, sufficient for geometry)
- Cached for subsequent queries

## Why 3x3?

A 3x3 cube is the minimal size that has:
- All 6 faces with center pieces
- All 12 edges with edge pieces
- All 8 corners
- Exactly 1 slice per axis (M, E, S)

This is sufficient for all template-level geometry queries. The answers
(transforms, cycles, etc.) are the same for any cube size.

## Files Changed

- `_CubeLayout.py` - Added `_internal_cube`, `_creating_internal_cube`, `_cube` property
- `cube_layout.py` - Protocol may be extended with geometry methods

## Related

- Issue #55 - Replace hard-coded lookup tables with mathematical derivation
- `GEOMETRY.md` - Detailed geometry documentation
- `cube_walking.py` - CubeWalkingInfo data structure
