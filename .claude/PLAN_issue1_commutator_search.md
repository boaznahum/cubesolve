# Plan: Integrate Commutator Search Method into _LBLNxNCenters

## Objective
Replace _LBLNxNCenters's target-first block search with an adapted source-first "commutator search method" from NxNCenters, while maintaining LBL's row constraints and marker protection.

## Key Insight
NxNCenters's `search_big_block()` finds blocks ON SOURCE that contain required colors, then maps them to target. This is more comprehensive than the current target-first approach. For LBL, we need to adapt this to:
1. Search source face for blocks with required_color
2. Apply row constraints (only blocks whose mapped target positions fall in current row)
3. Maintain marker protection for s2 validation

## Current Flow vs Proposed Flow

### CURRENT (Target-First)
```
_solve_single_center_piece_from_source_face_impl()
├─ Iterate unsolved positions on TARGET (one row only)
├─ For each position:
│  ├─ _search_blocks_starting_at() → find blocks on target
│  ├─ _source_block_has_color_with_rotation() → search source
│  └─ _try_solve_block() → execute if valid
└─ Return work_done
```

### PROPOSED (Source-First with LBL Constraints)
```
_solve_single_center_piece_from_source_face_impl()
├─ _search_blocks_on_source_lbl() → find blocks with color on source
│  ├─ Iterate source positions
│  ├─ For each: extend into blocks (greedy like NxNCenters)
│  ├─ Filter: block's mapped target row == current_row
│  └─ Return blocks sorted by size (largest first)
├─ For each block:
│  ├─ Map from source to target via CommutatorHelper
│  ├─ Try 4 rotations: _source_block_has_color_no_rotation()
│  ├─ Validate marker protection (s2 check)
│  └─ _try_solve_block() → execute if valid
└─ Return work_done
```

## Changes Required

### 1. New Method: `_search_blocks_on_source_lbl()`
**Location**: _LBLNxNCenters.py

**Purpose**: Adapted version of NxNCenters's `search_big_block()` with LBL row constraints

**Algorithm**:
```python
def _search_blocks_on_source_lbl(
    self,
    source_face: Face,
    required_color: Color,
    current_row: int,  # row index being solved
    l1_tracker: FaceTracker
) -> list[Block]:
    """
    Search for blocks with required_color on source face.

    Only returns blocks whose target mapping falls in current_row.
    Uses CommutatorHelper to map source blocks to target positions.

    Returns blocks sorted by size (largest first).
    """
    blocks = []
    n = self.n_slices

    # Iterate all source positions
    for start_point in all_center_positions(n):
        # Check if this position HAS required_color
        if source_face.center.get_center_slice(start_point).color != required_color:
            continue

        # Start building blocks from this position
        # Try 1x1, then extend horizontally, then vertically (greedy like NxNCenters)

        # 1. Add 1x1 block
        block_1x1 = Block(start_point, start_point)
        if self._block_maps_to_current_row_lbl(block_1x1, source_face, current_row, l1_tracker):
            blocks.append(block_1x1)

        # 2. Try larger blocks (if config allows)
        if LBL_MAX_BLOCK_SIZE > 1:
            # Greedy horizontal extension first
            max_row = start_point[0]  # Track max row reached

            for end_col in range(start_point[1] + 1, n):
                # Extend horizontally
                if all(source_face.center.get_center_slice(Point(start_point[0], c)).color == required_color
                       for c in range(start_point[1], end_col + 1)):
                    block_h = Block(start_point, Point(start_point[0], end_col))
                    if self._block_maps_to_current_row_lbl(block_h, source_face, current_row, l1_tracker):
                        blocks.append(block_h)
                    max_row = start_point[0]
                else:
                    break

            # Then try vertical extension from max_row reached
            # (similar to NxNCenters greedy logic)

    # Sort by size descending
    blocks.sort(key=lambda b: b.size, reverse=True)
    return blocks
```

**Helper: `_block_maps_to_current_row_lbl()`**
```python
def _block_maps_to_current_row_lbl(
    self,
    source_block: Block,
    source_face: Face,
    current_row: int,
    l1_tracker: FaceTracker
) -> bool:
    """
    Check if source block's mapped target position falls in current_row.

    Uses CommutatorHelper.execute_commutator(dry_run=True) to find
    where this block would be placed on target.
    """
    # Dry run to find natural target mapping
    dry_result = self._comm_helper.execute_commutator(
        source_face=source_face,
        target_face=???,  # Need target_face here - see below
        target_block=None,
        source_block=source_block,
        dry_run=True
    )

    target_block = dry_result.???  # Get where this source maps to

    # Check if target block intersects current_row
    target_row_index = ???  # Extract row from target_block
    return target_row_index == current_row
```

**ISSUE**: CommutatorHelper.execute_commutator() requires BOTH source_face AND target_face as separate parameters. In source-first search, we have source_face but need to check all possible target faces. This is a constraint.

### 2. Update: `_solve_single_center_piece_from_source_face_impl()`

**Current implementation**:
- Iterates unsolved positions on target (target-first)
- For each, calls `_search_blocks_starting_at()`

**New implementation**:
- Call `_search_blocks_on_source_lbl()` to find blocks on source
- For each block, check all rotations and target faces
- Execute if valid

```python
def _solve_single_center_piece_from_source_face_impl(self, l1_tracker, target_face, source_face, face_row):
    # OLD: iterate target positions
    # NEW: find blocks on source

    blocks = self._search_blocks_on_source_lbl(source_face, target_face.color, face_row, l1_tracker)

    for block in blocks:
        if self._try_solve_block_from_source_search(...):
            work_done = True
            break  # Move to next block

    return work_done
```

### 3. Refactor: Rotation Search Logic

**Current approach**:
- `_source_block_has_color_with_rotation()` rotates source block on same source face

**New approach for source-first**:
- Source block is already found on source face (no rotation needed)
- Instead, need to try different target faces? Or different rotations of source block position?

**QUESTION**: In source-first search, what varies?
- In NxNCenters: tries different target positions (via `_point_on_source()` mapping)
- In LBL: all target positions on same face, different source face combinations

**Insight**: Actually, rotation is still needed because:
- Source block at position (1,2) when rotated 90° becomes (2, n-1-2)
- This may cause block to match current_row when unrotated version doesn't

### 4. Delete or Deprecate: `_search_blocks_starting_at()`

This method is specific to target-first approach. With source-first search, it's no longer used. Remove it to avoid confusion.

---

## Design Questions

### Q1: How does CommutatorHelper map source blocks to target?
- Current: `execute_commutator()` takes source_face + target_face as separate parameters
- Issue: Source-first search doesn't know target_face in advance
- Solution: Try all 4 target faces in loop? Or extend CommutatorHelper?

### Q2: Does row constraint filtering work geometrically?
- Source block position maps to target via CommutatorHelper
- Need to verify: if source block is in position (1,2)-(1,5), what's its target position?
- Answer: Depends on which source face and which target face

### Q3: Should we search all source faces or just the input source_face?
- Current code: Caller selects target_face, then tries `source_face` (4 adjacent faces)
- New source-first: Should we search all source faces and find blocks there?
- Answer: Probably yes - search all source faces that have the required color

---

## Implementation Strategy

### Option A: Full Source-First (More Comprehensive)
- Implement `_search_blocks_on_source_lbl()`
- Iterate ALL source faces
- For each source face, find all blocks with required_color
- Filter by row constraint
- Best for completeness, may find blocks target-first misses

### Option B: Hybrid (Safer Refactoring)
- Keep iterating target positions (efficient for LBL)
- For each target position, use `_search_blocks_on_source_lbl()` to find source blocks
- Then search source via rotation
- Maintains efficiency, adds source-first search capabilities

### Option C: Rotation-Based Source Search (Simpler)
- Keep current target-first approach
- But enhance block search to include source-first rotation patterns
- Minimal refactoring, but less of a paradigm shift

---

## Recommended Approach: **Option A (Full Source-First)**

**Why**:
1. Truly adopts NxNCenters's commutator search method
2. More comprehensive block finding (may catch blocks target-first misses)
3. Cleaner algorithm (source-first is conceptually simpler)
4. Avoids maintaining two parallel search methods

**Implementation Steps**:
1. Implement `_search_blocks_on_source_lbl()` with row filtering
2. Extend CommutatorHelper if needed to support row filtering
3. Replace `_solve_single_center_piece_from_source_face_impl()` flow
4. Delete `_search_blocks_starting_at()`
5. Update rotation search for source-first context
6. Run full test suite

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| CommutatorHelper API mismatch | HIGH | May need to extend CommutatorHelper interface |
| Row filtering logic incorrect | MEDIUM | Test with simple cases first (2x2, 3x3 mappings) |
| Performance regression | MEDIUM | Profile before/after (source-first searches more positions) |
| Marker protection breaks | HIGH | Keep existing s2 validation logic unchanged |
| Rotation search confusion | MEDIUM | Document rotation semantics clearly |

---

## Validation Plan

1. **Unit tests**: Test `_search_blocks_on_source_lbl()` independently
2. **Integration tests**: Run full solver on 4x4, 5x5 cubes
3. **Regression tests**: Verify all existing tests still pass
4. **Performance test**: Compare old vs new search space sizes
5. **GUI test**: Animate solve on 4x4 to visually inspect block selection

---

## Commit Plan

- Commit 1: Add `_search_blocks_on_source_lbl()` (non-breaking)
- Commit 2: Extend CommutatorHelper if needed
- Commit 3: Refactor `_solve_single_center_piece_from_source_face_impl()`
- Commit 4: Delete `_search_blocks_starting_at()`
- Commit 5: Update tests and documentation

