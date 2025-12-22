# Dead Code Cleanup

Generated: 2025-12-22

This file documents dead code identified in `src/cube/` that should be cleaned up.

## Instructions for Next Session

Run through each section below and remove the dead code. After each removal:
1. Run `/check` to verify no regressions
2. Mark the item as done with ~~strikethrough~~

---

## 1. Unused Class - `Misc` (HIGH)

**File:** `src/cube/utils/Misc.py`

**Action:** Delete the entire file if only contains this class, or remove the class.

```python
class Misc:
    @staticmethod
    def assert_pyglet_not_imported():
        assert not _is_module_imported('pyglet'), 'Pyglet imported'
```

**Reason:** Never imported or called anywhere in the codebase.

---

## 2. Remove `use(_)` Stub Functions (HIGH)

These files define a no-op `use(_)` function used to suppress "unused variable" warnings. This is a code smell - either use the variables or remove them.

**Files to clean:**

| File | Line |
|------|------|
| `src/cube/domain/solver/_3x3/shared/L1Cross.py` | 14 |
| `src/cube/domain/solver/_3x3/beginner/_L1Corners.py` | 11 |
| `src/cube/domain/solver/_3x3/beginner/_L2.py` | 11 |
| `src/cube/domain/solver/_3x3/beginner/_L3Corners.py` | 13 |
| `src/cube/domain/solver/_3x3/beginner/_L3Cross.py` | 13 |
| `src/cube/domain/solver/_3x3/cfop/_F2L.py` | 27 |
| `src/cube/domain/solver/_3x3/cfop/_OLL.py` | 11 |
| `src/cube/domain/solver/_3x3/cfop/_PLL.py` | 11 |
| `src/cube/domain/solver/common/big_cube/NxNEdges.py` | 16 |
| `src/cube/domain/solver/common/big_cube/NxNCenters.py` | 19 |

**Action:** In each file:
1. Remove the `use(_)` function definition
2. Find all `use(variable)` calls and either:
   - Remove the variable if truly unused
   - Prefix with `_` if intentionally unused (e.g., `_unused_var = ...`)

---

## 3. Remove Unused `_status` Module Variables (HIGH)

These module-level variables are initialized to `None` and never read.

**Files to clean:**

| File | Line |
|------|------|
| `src/cube/domain/solver/_3x3/shared/L1Cross.py` | 16 |
| `src/cube/domain/solver/_3x3/beginner/_L3Corners.py` | 15 |
| `src/cube/domain/solver/_3x3/beginner/_L3Cross.py` | 15 |
| `src/cube/domain/solver/_3x3/cfop/_OLL.py` | 15 |
| `src/cube/domain/solver/_3x3/cfop/_PLL.py` | 13 |
| `src/cube/domain/solver/common/big_cube/NxNCenters.py` | 26 |
| `src/cube/domain/solver/common/big_cube/NxNEdges.py` | 20 |

**Action:** Remove the `_status = None` line and any `global _status` references.

---

## 4. Remove Unreachable Code in `__print_cross_status` (HIGH)

**File:** `src/cube/domain/solver/_3x3/shared/L1Cross.py` (lines 64-78)

```python
def __print_cross_status(self):
    return  # <-- Early return makes everything below unreachable

    # noinspection PyUnreachableCode
    wf = self.white_face
    es: Sequence[Edge] = wf.edges
    # ... more unreachable code
```

**Action:** Either:
- Remove the entire method if not needed
- Or remove just the unreachable code after `return`

---

## 5. Remove Unused Local Variables in `_L2.py` (HIGH)

**File:** `src/cube/domain/solver/_3x3/beginner/_L2.py` (lines 118-121)

```python
_te = st.position       # don't track
_se = st.actual         # don't track
_te_id = _te.colors_id
_se_id = _se.colors_id
```

**Action:** Remove these 4 lines - variables assigned but never used.

---

## 6. Unused Function Parameters (MEDIUM)

**File:** `src/cube/presentation/gui/backends/console/ConsoleViewer.py` (line 234)

```python
def _plot_face(b: _Board, f: Face, fy: int, fx: int, flip_v=False, flip_h=False):
```

**Action:** Either:
- Implement the `flip_v`/`flip_h` logic if needed
- Or remove the parameters and update all callers

---

## Summary

| Category | Count | Priority |
|----------|-------|----------|
| Unused class (`Misc`) | 1 | HIGH |
| `use(_)` stub pattern | 10 files | HIGH |
| `_status` variables | 7 files | HIGH |
| Unreachable code | 1 | HIGH |
| Unused local vars | 1 | HIGH |
| Unused parameters | 1 | MEDIUM |
| **Total** | **21 items** | |

---

## After Cleanup

Once all items are cleaned:
1. Run full checks: `/check`
2. Run tests: `python -m pytest tests/ -v --ignore=tests/gui -m "not slow"`
3. Delete this file
