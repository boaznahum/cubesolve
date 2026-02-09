# Dead Code Analysis - Modified Files
**Date:** 2025-02-09
**Commit:** efa01cda
**Branch:** big-lbl-even-opus_2

## Overview
Analysis of dead/unused code found in modified solver files after refactoring.

---

## NxNCenters.py

### 1. Unused Method: `is_cube_solved()` (lines 168-170)
**Confidence:** HIGH
**Lines of Code:** 3

```python
@staticmethod
def is_cube_solved(cube: Cube):
    return cube.is_solved()
```

**Analysis:**
- Static method that simply delegates to `cube.is_solved()`
- Never called anywhere in the codebase
- Duplicates functionality available directly on Cube object
- **Recommendation:** Safe to remove

---

### 2. Unused Method: `count_missing()` (lines 1001-1008)
**Confidence:** HIGH
**Lines of Code:** 8

```python
@staticmethod
def count_missing(face: Face, color: Color) -> int:
    """
    Count how many center pieces don't match the required color
    """
    n = face.cube.n_slices
    total = n * n
    matching = face.center.count_color(color)
    return total - matching
```

**Analysis:**
- Static method for counting mismatched pieces
- Well-documented but never called
- **Recommendation:** Safe to remove unless planned for future use

---

### 3. Unused Method: `_has_color_on_face()` (lines 1013-1018)
**Confidence:** HIGH
**Lines of Code:** 6

```python
@staticmethod
def _has_color_on_face(face: Face, color: Color) -> int:
    for s in face.center.all_slices:
        if s.color == color:
            return True
    return False
```

**Analysis:**
- Static method to check if color exists on face
- **Bug:** Return type annotation says `int` but returns `bool`
- Never called anywhere
- **Recommendation:** Safe to remove

---

### 4. Unused Method: `_count_colors_on_block()` (lines 1020-1064)
**Confidence:** MEDIUM-HIGH
**Lines of Code:** 45

**NOTE:** This was the OLD `_count_colors_on_block_and_tracker` method before refactoring.
After recent refactoring, we:
- Renamed this method to `_count_colors_on_block`
- Removed tracker counting logic
- It IS now used (called from `_search_slices_on_face`)

**Analysis:**
- This entry is OUTDATED - the method is now actively used
- **Recommendation:** IGNORE THIS ENTRY - method is in use

---

### 5. Unused Method: `_swap_entire_face_odd_cube()` (lines 854-903)
**Confidence:** HIGH
**Lines of Code:** 50 (with 26 lines unreachable)

```python
def _swap_entire_face_odd_cube(self, tracker_holder: "FacesTrackerHolder", color, face, back, faces):
    """
    When face is fully solved but back face has many pieces of that color,
    swap entire face with back

    Only works for ODD cubes (center piece exists)
    """
    # ... some setup code ...

    # Line 876: RAISES ERROR - ALL CODE BELOW IS UNREACHABLE
    raise InternalSWError("Need to fix MM")

    # Lines 878-903: UNREACHABLE CODE (26 lines)
    swap_faces = [...]
    op.op(Algs.seq_alg(None, *swap_faces))

    with self.ann.annotate(...):
        self._block_commutator(...)  # 4 commutator calls
```

**Analysis:**
- Method never called anywhere
- Raises `InternalSWError("Need to fix MM")` on line 876
- All code after line 876 is unreachable (26 lines)
- Appears to be incomplete/broken implementation
- **Recommendation:** Remove entire method (50 lines) OR fix the implementation if needed in future

**Unreachable Code Details:**
- Lines 878-882: Face swap algorithm setup
- Lines 885-903: Four commutator executions that will never run

---

### 6. Commented-Out Debug Code
**Confidence:** HIGH
**Lines:** 251, 255, 299-303, 594-620

**Examples:**
```python
# Line 251: #self._faces = faces
# Line 255: #self._trackers._debug_print_track_slices()
# Lines 299-303: Multiple commented print statements
# Lines 594-620: Large block of commented diagnostic code
```

**Analysis:**
- Extensive debug/diagnostic code commented out
- Likely used during development/debugging
- **Recommendation:** Safe to remove if no longer needed for debugging

---

## _LBLNxNCenters.py

### 1. Unused Method: `_source_block_has_color_no_rotation()` (lines 619-695)
**Confidence:** HIGH
**Lines of Code:** 77

```python
def _source_block_has_color_no_rotation(
    self,
    required_color: Color,
    source_face: Face,
    source_block: Block,
    second_block: Block,
    target_face: Face,
    target_block: Block,
) -> bool:
    """
    Check if source block has required color WITHOUT rotation search.

    THE 3-CYCLE COMMUTATOR:
    =======================
    ... [extensive documentation] ...
    """
    # 77 lines of implementation
```

**Analysis:**
- Complex method with extensive documentation
- Never called anywhere in the codebase
- Appears to be superseded by `_source_block_has_color_with_rotation()`
- **Recommendation:** Review if this logic is covered by the rotation version, then remove

---

### 2. Unused Method: `_block_iter()` (lines 612-616)
**Confidence:** HIGH
**Lines of Code:** 5

```python
@staticmethod
def _block_iter(block: Block) -> Iterator[Point]:
    """Iterate over all cells in a block."""
    return block.cells
```

**Analysis:**
- Simple wrapper that just returns `block.cells`
- Never called anywhere
- Could be replaced with direct `block.cells` access
- **Recommendation:** Safe to remove

---

### 3. Unused Parameter: `target_face` (line 160)
**Confidence:** HIGH

```python
def _slice_on_target_face_solved(self, l1_white_tracker: FaceTracker, target_face: FaceTracker, face_row: int) -> bool:
    #del _target_face  # Unused - checks all faces, not just target

    # ... function body never uses target_face parameter ...
```

**Analysis:**
- Parameter `target_face` is passed but never used in function body
- Comment acknowledges it's unused
- Function checks ALL faces, not just target
- **Recommendation:** Remove parameter from signature and update all call sites

---

## _LBLSlices.py

### 1. Unreachable Code (lines 410-412)
**Confidence:** HIGH
**Lines of Code:** 3

```python
# Line 408:
raise SolverFaceColorsChangedNeedRestartException()

# Lines 410-412: UNREACHABLE
with FacesTrackerHolder(self) as new_th:
    new_l1 = self._get_layer1_tracker(new_th)
    self._lbl_slices.solve_all_faces_all_rows(new_th, new_l1)
```

**Analysis:**
- Code after `raise` statement on line 408 will never execute
- Additionally, references non-existent methods (`_get_layer1_tracker()`, `_lbl_slices`)
- Appears to be leftover code from refactoring
- **Recommendation:** Remove lines 410-412

---

### 2. Unused Variable: `n_iteration` (line 357)
**Confidence:** MEDIUM
**Lines of Code:** 1

```python
n_iteration = 0
# ...
n_iteration += 1
if n_iteration > MAX_ITERATIONS:
    raise InternalSWError("Maximum iterations reached")
```

**Analysis:**
- Variable is incremented and checked against MAX_ITERATIONS
- But the actual value is never used elsewhere (only the error condition matters)
- **Recommendation:** Low priority - keep for iteration tracking even if value isn't used

---

## _common.py

**No significant dead code found.**

The file contains utility functions that are actively used by other modules.

---

# USER'S MODIFIED FILES

## _config.py

### 1. Unused Config Values (lines 89, 91)
**Confidence:** HIGH

```python
# Line 89:
validate: bool = True  # no longer used

# Line 91:
use_simple_f5_tracker: bool = True  # no longer used
```

**Analysis:**
- Config fields in `FaceTrackerConfig` dataclass
- Marked as "no longer used" in comments
- Grep search returns zero usages in codebase
- **Recommendation:** Remove both fields from config

---

## FacesTrackerHolder.py

### 1. Unused Method: `get_face_color()` (lines 247-262)
**Confidence:** HIGH

### 2. Unused Method: `get_tracker()` (lines 264-276)
**Confidence:** HIGH

### 3. Unused Method: `get_tracker_by_color()` (lines 278-293)
**Confidence:** HIGH
- Only called by `get_face_by_color()` which is also unused

### 4. Unused Method: `get_face_by_color()` (lines 295-297)
**Confidence:** HIGH
- Creates dead code chain with `get_tracker_by_color()`

### 5. Unused Method: `adjusted_faces()` (lines 332-337)
**Confidence:** HIGH
- Only `Face.adjusted_faces()` is used, not this version

### 6. Unused Method: `get_debug_str_faces()` (lines 535-539)
**Confidence:** MEDIUM
- Debug-only method, never called

### 7. Unused Static Method: `preserve_physical_faces_static()` (lines 368-411)
**Confidence:** HIGH
- Instance method `preserve_physical_faces()` is used instead
- Static version never called

**Analysis:**
- 7 public/static methods that are never called
- Some form dead code chains (method calls another unused method)
- **Recommendation:** Remove all 7 methods unless planned for future API

---

## _factory.py

### 1. CRITICAL: Unreachable Code (line 433)
**Confidence:** CRITICAL

```python
def _track_two_last_simple(self, ...):
    # ...
    return f5_track, f6_track  # Line 431

    return False  # Line 433 - UNREACHABLE!
```

**Analysis:**
- `return False` on line 433 comes AFTER `return` on line 431
- Will never execute
- **Recommendation:** Remove line 433 immediately

### 2. Unused Method: `_create_f5_pred()` (lines 437-506)
**Confidence:** MEDIUM
- 70 lines of code
- Comment says "used by FaceTracker.by_pred()" but that method doesn't exist
- Never called anywhere

### 3. Unused Debug Method: `_debug_print_track_slices()` (lines 520-531)
**Confidence:** MEDIUM
- Has `_SKIP_DEBUG = True` flag to disable it
- Never called

### 4. Unused Static Method: `_is_track_slice()` (lines 509-511)
**Confidence:** MEDIUM
- Just delegates to `FaceTracker.is_track_slice()`
- Never called

---

## _helper.py

**No dead code found.**

All functions are actively used.

---

## trackers.py

### 1. Unused Method: `other_faces()` (lines 217-221)
**Confidence:** MEDIUM

```python
def other_faces(self) -> Iterable["FaceTracker"]:
    """boaz: improve this"""
    return [t for t in self._holder if t is not self]
```

**Analysis:**
- Similar to `adjusted_faces()` but less restrictive
- Has "boaz: improve this" comment (incomplete)
- Never called anywhere
- **Recommendation:** Remove or implement properly

### 2. Unused Method: `adjusted_faces()` (lines 223-227)
**Confidence:** MEDIUM

```python
def adjusted_faces(self) -> Iterable["FaceTracker"]:
    """boaz: improve this"""
    return [t for t in self._holder if t is not self and t is not self.opposite]
```

**Analysis:**
- Has "boaz: improve this" comment (incomplete)
- Called from `Face.adjusted_faces()` but not directly
- **Recommendation:** Keep (used indirectly) but review the implementation

---

## Summary Statistics

### Claude's Changes (Solver Files)
| File | Dead Methods | Dead Lines | Unreachable Lines | Priority |
|------|-------------|-----------|-------------------|----------|
| NxNCenters.py | 4 | ~62 | 26 | HIGH |
| _LBLNxNCenters.py | 2 + 1 param | ~82 | 0 | MEDIUM |
| _LBLSlices.py | 0 | 0 | 3 | LOW |
| **Subtotal** | **6** | **~144** | **29** | |

### User's Changes (Tracker/Config Files)
| File | Dead Methods | Dead Config | Unreachable Lines | Priority |
|------|-------------|------------|-------------------|----------|
| _config.py | 0 | 2 | 0 | HIGH |
| FacesTrackerHolder.py | 7 | 0 | 0 | HIGH |
| _factory.py | 3 | 0 | 1 | CRITICAL |
| _helper.py | 0 | 0 | 0 | - |
| trackers.py | 2 | 0 | 0 | MEDIUM |
| **Subtotal** | **12** | **2** | **1** | |

### Grand Total
| Category | Count |
|----------|-------|
| Dead Methods | 18 |
| Dead Config Fields | 2 |
| Unreachable Lines | 30 |
| **Total Issues** | **50+** |

---

## Recommendations by Priority

### CRITICAL Priority (Fix Immediately):
1. **_factory.py line 433** - Remove unreachable `return False` statement

### HIGH Priority (Remove First):
2. **NxNCenters.py** - `_swap_entire_face_odd_cube()` (50 lines) - Broken, raises error, has unreachable code
3. **_LBLNxNCenters.py** - `_source_block_has_color_no_rotation()` (77 lines) - Large unused method
4. **FacesTrackerHolder.py** - 7 unused public methods (~115 lines total)
5. **_config.py** - Remove 2 unused config fields (`validate`, `use_simple_f5_tracker`)

### MEDIUM Priority:
6. **NxNCenters.py** - `is_cube_solved()`, `count_missing()`, `_has_color_on_face()` (~17 lines)
7. **_LBLNxNCenters.py** - `_block_iter()` (5 lines)
8. **_LBLNxNCenters.py** - Remove unused `target_face` parameter
9. **_factory.py** - `_create_f5_pred()` (70 lines), `_debug_print_track_slices()`, `_is_track_slice()`
10. **trackers.py** - `other_faces()` method (never used)

### LOW Priority:
11. **_LBLSlices.py** - Remove unreachable code after raise (3 lines)
12. **NxNCenters.py** - Clean up commented debug code

---

## Notes

### Overall Statistics:
- **Total removable code:** ~360+ lines across all files
- **Critical issues:** 1 (unreachable return statement)
- **High priority removals:** ~260 lines (large unused methods)
- **Medium priority:** ~100 lines (smaller utility methods)

### Safety Analysis:
- All identified code appears safe to remove
- No evidence of dynamic usage (getattr, reflection, etc.)
- No references found in test files
- Methods not in `__all__` exports (private methods)
- Some methods form "dead chains" (unused method calls another unused method)

### Special Notes:
- **_factory.py line 433**: CRITICAL bug - unreachable code that should be removed immediately
- **FacesTrackerHolder.py**: 7 public methods unused - may indicate over-engineered API
- **_create_f5_pred()**: 70 lines referencing non-existent `FaceTracker.by_pred()` method
- **Config fields**: Marked "no longer used" but still present in dataclass

---

## Action Items

### Immediate Actions:
- [ ] **CRITICAL:** Remove unreachable `return False` at `_factory.py:433`

### Phase 1 - High Priority Cleanup:
- [ ] Remove `_swap_entire_face_odd_cube()` from NxNCenters.py (50 lines)
- [ ] Remove `_source_block_has_color_no_rotation()` from _LBLNxNCenters.py (77 lines)
- [ ] Review and remove 7 unused methods from FacesTrackerHolder.py (~115 lines)
- [ ] Remove unused config fields from _config.py

### Phase 2 - Medium Priority Cleanup:
- [ ] Remove smaller unused methods from NxNCenters.py
- [ ] Remove unused methods from _factory.py including `_create_f5_pred()` (70 lines)
- [ ] Clean up _LBLNxNCenters.py unused parameter and method
- [ ] Remove `other_faces()` from trackers.py

### Phase 3 - Code Hygiene:
- [ ] Remove unreachable code in _LBLSlices.py
- [ ] Clean up commented debug code in NxNCenters.py

### Testing:
- [ ] Run full test suite after each phase
- [ ] Check git history to understand why methods were added
- [ ] Verify no dynamic usage patterns were missed
- [ ] Update documentation if any removed methods were documented
