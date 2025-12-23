# Dual Operator for Preserving Solver Annotations

**Status**: Planning
**Created**: 2025-12-23
**Branch**: `feature/dual-operator-annotations`

## Problem Statement

When solving an NxN cube using the Cage method, the solver delegates corner solving to a 3x3 solver running on a "shadow cube". The shadow solver has rich annotations (h1, h2, h3 text + visual markers), but these are **completely lost** when we extract the algorithm history and play it on the real cube.

### Current Flow (Problematic)

```
CageNxNSolver._solve_corners()
    │
    ▼
_solve_shadow_3x3()
    │
    ├── 1. Create shadow 3x3 cube
    ├── 2. Create shadow Operator (no animation manager!)
    ├── 3. shadow_solver.solve_3x3()
    │       │
    │       ├── L1Cross.solve()  ← h1="L1 Cross" (LOST)
    │       ├── L1Corners.solve() ← h1="L1 Corners" (LOST)
    │       ├── L2.solve()        ← h1="Layer 2" (LOST)
    │       ├── L3Cross.solve()   ← h1="L3 Cross" (LOST)
    │       └── L3Corners.solve() ← h1="L3 Corners" (LOST)
    │
    ├── 4. history = shadow_op.history()
    └── 5. self._op.play(SeqAlg(*history))  ← Single combined algorithm
                                               No annotations!
```

### What Gets Lost

| Component | Description | Impact |
|-----------|-------------|--------|
| h1 text | Phase name (e.g., "L1 Cross") | User doesn't know which phase is running |
| h2 text | Step description (e.g., "Bringing edge to FR") | User doesn't understand what's happening |
| h3 text | Algorithm notation | User can't learn the algorithms |
| VMarker.C1 | Pink circles tracking moving pieces | User can't follow piece movement |
| VMarker.C2 | Green circles showing destinations | User can't see target positions |

## Proposed Solution: Dual Operator

Create a new `DualOperator` implementation that wraps both a shadow cube and the real operator. When the solver calls `op.play(alg)`, the dual operator:

1. Plays on the shadow cube (for state tracking, query mode)
2. Plays on the real cube (with full animation and annotations)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DualOperator                             │
│                  (implements OperatorProtocol)                  │
│                                                                 │
│   ┌─────────────────────┐       ┌─────────────────────┐        │
│   │    Shadow Cube      │       │    Real Operator    │        │
│   │    (3x3)            │       │    (wraps NxN)      │        │
│   │                     │       │                     │        │
│   │  • Query mode       │       │  • Animation ON     │        │
│   │  • No animation     │       │  • Annotations ON   │        │
│   │  • State tracking   │       │  • History tracked  │        │
│   │  • Solver logic     │       │  • GUI updates      │        │
│   └─────────────────────┘       └─────────────────────┘        │
│             ▲                            ▲                      │
│             │      op.play(alg)          │                      │
│             └────────────┬───────────────┘                      │
│                          │                                      │
│   ┌──────────────────────┴──────────────────────┐              │
│   │              DualAnnotation                  │              │
│   │  • Maps shadow pieces → real pieces          │              │
│   │  • Delegates to real operator's annotation   │              │
│   └─────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                               ▲
                               │
                    ┌──────────┴──────────┐
                    │   3x3 Solver        │
                    │   (BeginnerSolver,  │
                    │    CFOP, etc.)      │
                    └─────────────────────┘
```

### Key Design Decisions

#### D1: Which cube does `op.cube` return?

**Decision**: Return the shadow cube.

**Rationale**: The solver logic (finding pieces, checking positions, etc.) operates on the shadow cube's state. The solver code doesn't need to know about the real cube.

```python
@property
def cube(self) -> Cube:
    return self._shadow_cube  # Solver logic uses this
```

#### D2: How to map shadow pieces to real pieces?

**Decision**: Map by position (accessor name) at annotation start. Markers then travel with pieces.

**Rationale**: In the Cage method, the shadow 3x3 represents the "virtual 3x3" of the NxN cube.
Position is the common language between the two cubes.

```
Shadow 3x3 Cube                Real 5x5 Cube
┌───┬───┬───┐                  ┌───┬───┬───┬───┬───┐
│   │FU │   │                  │   │   │FU │   │   │  (3 slices)
├───┼───┼───┤                  ├───┼───┼───┼───┼───┤
│FL │   │FR │                  │   │   │   │   │   │
├───┼───┼───┤       MAP        ├───┼───┼───┼───┼───┤
│   │FD │   │    ─────────►    │FL │   │   │   │FR │
└───┴───┴───┘                  ├───┼───┼───┼───┼───┤
                               │   │   │   │   │   │
shadow.fu (1 slice)            ├───┼───┼───┼───┼───┤
       │                       │   │   │FD │   │   │
       └──────────────────────►└───┴───┴───┴───┴───┘
                               real.fu (3 slices, all annotated)
```

**Slice handling**: When we map `shadow.fu` (1 slice) → `real.fu` (3 slices on 5x5),
the annotation system iterates ALL slices of the real edge. The entire paired edge
lights up with markers.

**Marker behavior with `AnnWhat.Moved`**:

The position mapping happens **once at annotation start**. After that, markers travel
with the piece via `c_attributes`:

```
1. Annotation starts:
   - Map shadow.fu → real.fu (position-based, ONE TIME)
   - Attach VMarker to real.fu's c_attributes (all slices)

2. Algorithm plays (e.g., R U R'):
   - real.fu piece physically moves to new position
   - VMarker travels WITH it (attached to c_attributes)
   - Pink circles follow the piece around the cube!

3. Annotation ends:
   - Find piece by tracking key (searches all pieces)
   - Remove VMarker from wherever piece ended up
```

**Implementation**:

```python
def _map_piece(self, shadow_piece: Part) -> Part:
    """Map a shadow cube piece to corresponding real cube piece by position."""
    if isinstance(shadow_piece, Edge):
        # Edge.name returns EdgeName enum (e.g., EdgeName.FU)
        accessor = shadow_piece.name.value.lower()  # e.g., "fu"
    elif isinstance(shadow_piece, Corner):
        # Corner.name returns CornerName enum (e.g., CornerName.FLU)
        accessor = shadow_piece.name.value.lower()  # e.g., "flu"
    else:
        raise ValueError(f"Unsupported piece type: {type(shadow_piece)}")

    return getattr(self._real_cube, accessor)
```

#### D3: How to handle annotation context?

**Decision**: Create `DualAnnotation` that wraps real operator's annotation.

**Rationale**: When solver does:
```python
with self.ann.annotate((edge, AnnWhat.Moved), h1="L1 Cross"):
    self.op.play(alg)
```

The `DualAnnotation`:
1. Receives shadow cube pieces
2. Maps them to real cube pieces
3. Delegates to real operator's annotation

#### D4: How to synchronize cube states?

**Decision**: Play algorithm on both cubes in sequence.

```python
def play(self, alg: Alg, inv: bool = False, animation: bool = True) -> None:
    # 1. Play on shadow (query mode, no animation)
    alg.play(self._shadow_cube, inv)

    # 2. Play on real with animation
    self._real_op.play(alg, inv, animation)
```

**Invariant**: Both cubes remain in equivalent states (same piece positions).

#### D5: What about history()?

**Decision**: Delegate to real operator.

**Rationale**: The real operator tracks the actual history. Shadow cube is just for state tracking.

```python
def history(self, *, remove_scramble: bool = False) -> Sequence[Alg]:
    return self._real_op.history(remove_scramble=remove_scramble)
```

#### D6: What about undo()?

**Decision**: Delegate to real operator only. Don't undo on shadow cube.

**Rationale**: When the user presses undo, the solver is already done. The shadow cube
is no longer needed - it was only used during the solve. The real cube's undo is what
matters for the user.

```python
def undo(self, animation: bool = True) -> Alg | None:
    # Shadow cube state becomes stale, but that's OK - solver is done
    return self._real_op.undo(animation)
```

#### D7: How to handle `with_animation(False)` in solver?

**Decision**: Respect the solver's choice - pass through to real operator.

**Rationale**: If a solver explicitly disables animation for certain moves (e.g., boring
setup moves, reorientations), that's intentional. The solver author knows which moves
are interesting to show.

```python
def with_animation(self, animation: bool | None = None) -> ContextManager[None]:
    # Pass through to real operator
    return self._real_op.with_animation(animation)
```

#### D8: How to handle PartColorsID in annotations?

**Decision**: Find piece by colors on the **real** cube, not shadow cube.

**Rationale**: `PartColorsID` is a frozenset of colors (e.g., `{Color.WHITE, Color.GREEN}`).
The annotation system needs to find which piece has those colors. Since we want to
annotate the real cube, we search the real cube.

```python
# In DualAnnotation._map_element():
if isinstance(element, frozenset):  # PartColorsID
    # Find on REAL cube, not shadow
    return self._real_cube.find_part_by_colors(element)
```

Note: For Cage method, shadow 3x3 uses tracked face colors that match the real cube,
so colors_id values are valid for both cubes.

## Class Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                    <<Protocol>>                                │
│                  OperatorProtocol                              │
├───────────────────────────────────────────────────────────────┤
│ + cube: Cube                                                   │
│ + annotation: AnnotationProtocol                               │
│ + animation_enabled: bool                                      │
│ + app_state: ApplicationAndViewState                           │
├───────────────────────────────────────────────────────────────┤
│ + play(alg, inv, animation): None                              │
│ + history(remove_scramble): Sequence[Alg]                      │
│ + undo(animation): Alg | None                                  │
│ + with_animation(animation): ContextManager                    │
│ + with_query_restore_state(): ContextManager                   │
└───────────────────────────────────────────────────────────────┘
                              △
                              │
              ┌───────────────┴───────────────┐
              │                               │
┌─────────────┴─────────────┐   ┌─────────────┴─────────────┐
│         Operator          │   │       DualOperator        │
│   (application layer)     │   │    (application layer)    │
├───────────────────────────┤   ├───────────────────────────┤
│ - _cube: Cube             │   │ - _shadow_cube: Cube      │
│ - _annotation: OpAnnot... │   │ - _real_op: Operator      │
│ - _animation_mgr: ...     │   │ - _annotation: DualAnnot  │
├───────────────────────────┤   ├───────────────────────────┤
│ + play(...)               │   │ + play(...)               │
│ + history(...)            │   │ + history(...)            │
│ + undo(...)               │   │ + undo(...)               │
└───────────────────────────┘   └───────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                    <<Protocol>>                                │
│                 AnnotationProtocol                             │
├───────────────────────────────────────────────────────────────┤
│ + annotate(*elements, h1, h2, h3, animation): ContextManager   │
└───────────────────────────────────────────────────────────────┘
                              △
                              │
              ┌───────────────┴───────────────┐
              │                               │
┌─────────────┴─────────────┐   ┌─────────────┴─────────────┐
│       OpAnnotation        │   │      DualAnnotation       │
├───────────────────────────┤   ├───────────────────────────┤
│ - op: Operator            │   │ - _dual_op: DualOperator  │
│ - cube: Cube              │   │ - _real_op: Operator      │
├───────────────────────────┤   ├───────────────────────────┤
│ + annotate(...)           │   │ + annotate(...)           │
│ - _map_to_real(elements)  │   │ - _map_piece(shadow_piece)│
└───────────────────────────┘   └─────────────────────────────┘
```

## Sequence Diagram

```
┌─────────┐  ┌────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐
│ Cage    │  │ Dual       │  │ Dual         │  │ Real       │  │ Real     │
│ Solver  │  │ Operator   │  │ Annotation   │  │ Operator   │  │ Cube     │
└────┬────┘  └─────┬──────┘  └──────┬───────┘  └─────┬──────┘  └────┬─────┘
     │             │                │                │               │
     │ create(shadow_cube, real_op) │                │               │
     │────────────>│                │                │               │
     │             │                │                │               │
     │ solve_3x3() │                │                │               │
     │────────────>│                │                │               │
     │             │                │                │               │
     │  ┌──────────┴──────────┐     │                │               │
     │  │ L1Cross.solve()     │     │                │               │
     │  └──────────┬──────────┘     │                │               │
     │             │                │                │               │
     │             │ annotate((edge, Moved), h1="L1 Cross")          │
     │             │───────────────>│                │               │
     │             │                │                │               │
     │             │                │ _map_piece(shadow_edge)        │
     │             │                │──────┐         │               │
     │             │                │<─────┘ real_edge               │
     │             │                │                │               │
     │             │                │ real_op.annotation.annotate(   │
     │             │                │   (real_edge, Moved), h1="L1 Cross")
     │             │                │───────────────>│               │
     │             │                │                │               │
     │             │ play(alg)      │                │               │
     │             │<───────────────│                │               │
     │             │                │                │               │
     │             │ alg.play(shadow_cube)           │               │
     │             │──────┐         │                │               │
     │             │<─────┘         │                │               │
     │             │                │                │               │
     │             │                │ real_op.play(alg)              │
     │             │                │───────────────>│               │
     │             │                │                │ play(alg)     │
     │             │                │                │──────────────>│
     │             │                │                │<──────────────│
     │             │<───────────────│                │               │
     │             │                │                │               │
```

## Implementation Plan

### Phase 1: Core Infrastructure

1. **Create `DualOperator` class**
   - Location: `src/cube/application/commands/DualOperator.py`
   - Implements `OperatorProtocol`
   - Wraps shadow cube + real operator

2. **Create `DualAnnotation` class**
   - Location: `src/cube/application/commands/DualAnnotation.py`
   - Implements `AnnotationProtocol`
   - Maps shadow pieces to real pieces

3. **Add piece position mapping utility**
   - Method to get piece by position name
   - Handle corners, edges, centers

### Phase 2: Integration

4. **Modify `CageNxNSolver._solve_shadow_3x3()`**
   - Replace shadow operator with DualOperator
   - Remove post-hoc algorithm application

5. **Test with simple cases**
   - 4x4 cube corner solving
   - 5x5 cube corner solving
   - Verify annotations appear correctly

### Phase 3: Edge Cases

6. **Handle `with_query_restore_state()`**
   - Dual operator must support query mode
   - Shadow cube stays in query mode
   - Real cube may or may not

7. **Handle `undo()`**
   - Undo must work on both cubes
   - Or delegate to real operator only

8. **Handle nested annotations**
   - Annotations can nest (h1 outer, h2 inner)
   - Mapping must preserve nesting

### Phase 4: Validation

9. **Add tests**
   - Unit tests for DualOperator
   - Unit tests for DualAnnotation
   - Integration test: solve with annotations visible

10. **Manual GUI testing**
    - Verify visual markers appear
    - Verify text annotations display
    - Verify animation works correctly

## Piece Mapping Details

### How Piece Names Work

The codebase uses position-based naming:

```python
# Edge: has _name attribute (e.g., "FU", "FR")
edge._name  # "FU" for Front-Up edge

# Corner: uses CornerName enum via name property
corner.name  # CornerName.FLU for Front-Left-Up corner

# Both can be accessed via cube properties
cube.fu   # Edge at Front-Up position
cube.flu  # Corner at Front-Left-Up position
```

### Mapping Implementation

```python
def _map_piece(self, shadow_piece: Part) -> Part:
    """Map a shadow cube piece to corresponding real cube piece."""
    if isinstance(shadow_piece, Edge):
        # Edge._name is lowercase like "fu"
        accessor = shadow_piece._name.lower()
    elif isinstance(shadow_piece, Corner):
        # Corner.name is CornerName enum, value is like "FLU"
        accessor = shadow_piece.name.value.lower()
    else:
        raise ValueError(f"Unsupported piece type: {type(shadow_piece)}")

    return getattr(self._real_cube, accessor)
```

### Corner Mapping

Shadow 3x3 corners map directly to real NxN corners by position:

| Shadow Position | `corner.name` | Accessor |
|-----------------|---------------|----------|
| Front-Left-Up | `CornerName.FLU` | `cube.flu` |
| Front-Right-Up | `CornerName.FRU` | `cube.fru` |
| Back-Left-Up | `CornerName.BLU` | `cube.blu` |
| Back-Right-Up | `CornerName.BRU` | `cube.bru` |
| Front-Left-Down | `CornerName.FLD` | `cube.fld` |
| Front-Right-Down | `CornerName.FRD` | `cube.frd` |
| Back-Left-Down | `CornerName.BLD` | `cube.bld` |
| Back-Right-Down | `CornerName.BRD` | `cube.brd` |

### Edge Mapping

Shadow 3x3 edges map to real NxN edges (which are already paired/reduced):

| Shadow Position | `edge._name` | Accessor |
|-----------------|--------------|----------|
| Front-Up | `"FU"` | `cube.fu` |
| Front-Down | `"FD"` | `cube.fd` |
| Front-Left | `"FL"` | `cube.fl` |
| Front-Right | `"FR"` | `cube.fr` |
| Back-Up | `"BU"` | `cube.bu` |
| Back-Down | `"BD"` | `cube.bd` |
| Back-Left | `"BL"` | `cube.bl` |
| Back-Right | `"BR"` | `cube.br` |
| Left-Up | `"LU"` | `cube.lu` |
| Left-Down | `"LD"` | `cube.ld` |
| Right-Up | `"RU"` | `cube.ru` |
| Right-Down | `"RD"` | `cube.rd` |

### Annotation Element Types

The annotation system accepts various element types. Mapping strategy:

| Element Type | Mapping Strategy |
|--------------|------------------|
| `Part` (Corner/Edge) | Map by position accessor (see above) |
| `PartSlice` | Get parent Part, map, then `mapped_part.get_slice(original_index)` |
| `PartEdge` | Get parent PartSlice, map recursively, get same face edge |
| `PartColorsID` | Find piece by colors on real cube (may differ!) |
| `Iterable[*]` | Map each element recursively |
| `Callable` | Call on shadow cube, then map result |

### Special Case: PartColorsID Mapping

`PartColorsID` is a frozenset of colors. On the shadow cube, these may represent:
- Shadow cube colors (if solver tracks by actual colors)
- Virtual 3x3 colors (derived from face trackers)

For Cage method, the shadow 3x3 uses **tracked face colors**, so mapping by colors_id should work correctly since both cubes use the same color scheme.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Piece mapping fails for some positions | Low | High | Comprehensive unit tests for all positions |
| State desync between cubes | Medium | High | Strict invariant: always play on both |
| Performance impact | Low | Medium | Shadow cube in query mode (no texture updates) |
| Annotation nesting breaks | Medium | Medium | Test nested annotation scenarios |

## Resolved Design Questions

All design questions have been resolved and documented in D1-D8 above:

| Question | Resolution | See |
|----------|------------|-----|
| Which cube does `op.cube` return? | Shadow cube (for solver logic) | D1 |
| How to map shadow → real pieces? | By position, markers travel via c_attributes | D2 |
| How to handle annotation context? | DualAnnotation wraps real annotation | D3 |
| How to sync cube states? | Play on both in sequence | D4 |
| How to handle history()? | Delegate to real operator | D5 |
| How to handle undo()? | Delegate to real operator only | D6 |
| How to handle with_animation(False)? | Respect solver's choice, pass through | D7 |
| How to handle PartColorsID? | Find by colors on real cube | D8 |

**Face-based annotations** (e.g., `cube.front.edges`): Work correctly because we receive
Part objects which we map by position. The recursive element processing handles iterables.

## Files to Create/Modify

### New Files
- `src/cube/application/commands/DualOperator.py`
- `src/cube/application/commands/DualAnnotation.py`
- `tests/application/test_dual_operator.py`

### Modified Files
- `src/cube/domain/solver/direct/cage/CageNxNSolver.py`
- `src/cube/application/commands/__init__.py` (export new classes)

## Success Criteria

1. When solving a 4x4+ cube with Cage method, GUI shows:
   - h1 text for each phase (L1 Cross, L1 Corners, etc.)
   - h2 text for each step
   - Pink circles following moving pieces
   - Green circles showing destinations

2. No change to 3x3 solver code required

3. All existing tests pass

4. No significant performance regression
