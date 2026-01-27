# Plan: Add Custom Marker Support to Annotation Context Manager

## Problem
In `CommunicatorHelper.execute_communicator()`, we manually create and manage the `at_risk` marker outside of the annotation context manager:

```python
# Current code - marker created separately, even if animation disabled
mf = self.cube.sp.marker_factory
at_risk_marker = mf.at_risk()  # Called even when animation is off!
mm.add_marker(s2_edge, "at_risk", at_risk_marker, moveable=True)
try:
    with self.ann.annotate(...):
        ...
finally:
    mm.remove_all("at_risk", ...)
```

## Goal
Allow passing additional markers to `annotate()` that are:
- **Lazily created** - factory method only called if animation is enabled
- Automatically added when entering context
- Automatically removed when exiting context

## Proposed API

### New parameter: `additional_markers`

A list of tuples with:
1. `element` - The PartEdge to mark
2. `what` - `AnnWhat.Moved` or `AnnWhat.FixedPosition` (consistent with existing API)
3. `marker_factory_method` - Callable that returns MarkerConfig (lazy!)

```python
AdditionalMarker = Tuple[PartEdge, AnnWhat, Callable[[], MarkerConfig]]
```

- `AnnWhat.Moved` → marker follows the piece (moveable=True)
- `AnnWhat.FixedPosition` → marker stays at position (moveable=False)
- Marker name is auto-generated internally (like existing annotation system)

### Updated annotate() signature

```python
def annotate(
    self,
    *elements: Tuple[SupportsAnnotation, AnnWhat],
    additional_markers: list[Tuple[PartEdge, AnnWhat, Callable[[], MarkerConfig]]] | None = None,
    h1: _HEAD = None,
    h2: _HEAD = None,
    h3: _HEAD = None,
    animation: bool = True
) -> ContextManager[None]:
```

### Usage in CommunicatorHelper

```python
# After change - factory method is NOT called if animation disabled
s2_edge = source_face.center.get_center_slice(xpt_on_source_after_un_setup).edge
mf = self.cube.sp.marker_factory

with self.ann.annotate(
    (_ann_source, AnnWhat.Moved),
    (_ann_target, AnnWhat.FixedPosition),
    additional_markers=[
        (s2_edge, AnnWhat.Moved, mf.at_risk)  # Pass method, not result!
    ],
    h2=_h2
):
    if source_setup_n_rotate:
        self.op.play(source_setup_alg)
    self.op.play(cum)
# Markers automatically removed on exit
```

**Key benefit**: `mf.at_risk` is passed as a method reference. It's only called inside `_annotate()` when animation is enabled.

## Files to Modify

1. **`src/cube/domain/solver/protocols/AnnotationProtocol.py`**
   - Add type alias for `AdditionalMarker`
   - Update `annotate()` signature

2. **`src/cube/application/commands/OpAnnotation.py`**
   - Update `annotate()` signature
   - Update `_annotate()` to process `additional_markers`
   - Call factory methods lazily inside `_w_slice_edges_annotate()`
   - Track additional markers for cleanup

3. **`src/cube/application/commands/DualAnnotation.py`** (if implements protocol)
   - Update signature to match

4. **`src/cube/domain/solver/common/big_cube/commun/CommunicatorHelper.py`**
   - Use new `additional_markers` parameter

## Implementation Details

### In `_annotate()`:
```python
# Process additional_markers - call factory methods lazily here
if additional_markers:
    for element, what, factory_method in additional_markers:
        marker = factory_method()  # Lazy creation!
        moveable = (what == AnnWhat.Moved)  # Convert AnnWhat to bool
        edges.append((element, not moveable, marker))  # Reuse existing edges list
```

### In `_w_slice_edges_annotate()`:
- No changes needed! Additional markers are just added to the existing `edges` list
- They get auto-generated names like regular annotations
- Cleanup happens automatically in the existing finally block

## Benefits

1. **Lazy creation** - Marker factory only called when animation enabled
2. **Clean lifecycle** - Markers managed by annotation context
3. **Custom names** - Caller specifies marker name (e.g., "at_risk")
4. **Backward compatible** - `additional_markers=None` by default
