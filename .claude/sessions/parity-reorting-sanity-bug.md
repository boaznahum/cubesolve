# Session: Sanity Check Bug Investigation

**Branch:** `parity-reorting`
**Date:** 2026-04-06 / 2026-04-07
**Commits:** `f9f63667`

## Task

User reported tests failing with `-n auto` (pytest-xdist parallel execution) after commit `75ff8e13` (identified via `git bisect`). The failing test was a Cage solver test with `ValueError: Cube doesn't contain part frozenset({BLUE})`.

## Investigation

### Step 1: Reproducing the failure

- The bad commit `75ff8e13` ("Fix SlicedSliceAlg index mirroring and add randomized theorem tests") only changed `alg_transform.py` and its test file.
- `alg_transform` has **no callers** in production code — it's a new feature.
- The failing tests were in `tests/solvers/test_all_solvers.py` (Cage solver on even cubes).
- Failure only occurred with `-n auto` (parallel), never with `-n0` (serial).
- Different seed/color failed each run (non-deterministic which test, but always the same error pattern).

### Step 2: Isolating the cause

- Running only solver tests with `-n auto`: **PASS**
- Running solver + transform tests together: **PASS**
- Running full suite with old transform tests but new production code: **PASS**
- Running full suite with new transform tests: **FAIL**
- **Key experiment:** Replaced 237 new transform tests with 237 dummy `assert True` tests: **FAIL** (same error!)

**Conclusion:** The production code change was innocent. Adding ANY 237 tests changed xdist's worker distribution, causing previously non-co-located tests to share a worker.

### Step 3: Finding the state leak

Searched for tests that modify `CONFIG_DEFAULTS` without restoring:

- `tests/algs/bug_sanity_on.py:12` — sets `CONFIG_DEFAULTS.check_cube_sanity = True` and **NEVER restores it**.
- When this test lands on the same xdist worker as Cage solver tests, the solver runs with sanity checking enabled.

### Step 4: Finding the real bug

With `check_cube_sanity=True`, the Cage solver on 8x8 fails at `CubeSanity.do_sanity()` Step 4:

```
CubeSanity.py:112: cube.find_part_by_colors(frozenset([c]))
ValueError: Cube doesn't contain part frozenset({BLUE})
```

Debug output at crash time:
```
is3x3: True
Face U: color=RED, center.is3x3=True, provider=True, center_3x3_mode=True
Face D: color=ORANGE, center.is3x3=True, provider=True, center_3x3_mode=True
Face F: color=BLUE, center.is3x3=True, provider=True, center_3x3_mode=True
...
```

All centers have `provider=True` and `center_3x3_mode=True`. The Cage solver uses face color providers during its 3x3 phase to make the 8x8 appear as a 3x3.

**Root cause:** `Center` class did NOT override `colors_id`. The inheritance chain:

- `Center.is3x3` → `True` (via `_center_3x3_mode` shortcut — respects provider)
- `Center.color` → provider color (overridden — respects provider)
- `Center.colors_id` → inherited from `Part.colors_id` → reads `PartEdge.color` (raw sticker — **IGNORES provider**)

Meanwhile, `Edge` already had this override:
```python
def colors_id(self):
    if self._edges_provider is not None:
        return self._edges_provider.get_edge_colors(self)
    return super().colors_id
```

Center was missing the equivalent override.

### Deeper issue

The fundamental problem is that `PartEdge.color` (the lowest level) has no provider concept. Every Part subclass must individually override `colors_id`, `face_color`, `match_face` to bypass the raw sticker and query its provider. This is fragile — tracked in issue #161.

## Changes Made

### Code fixes
1. **`src/cube/domain/model/Center.py`** — Added `colors_id` override using `_color_provider` (matches Edge pattern)
2. **`src/cube/domain/model/Edge.py`** — Added CRITICAL warning comments on `colors_id`, `face_color`, `match_face` referencing issue #161
3. **`tests/algs/bug_sanity_on.py`** — Wrapped in try/finally to restore `check_cube_sanity`
4. **`src/cube/resources/version.txt`** — Bumped to 1.82.1

### GitHub issues
- **#161** — CRITICAL: PartEdge.color ignores color providers (the deeper fix)
- **#162** — (pending) Tests must not mutate global CONFIG_DEFAULTS

## Key Files
- `src/cube/domain/model/Center.py` — Center.colors_id override
- `src/cube/domain/model/Edge.py` — Edge.colors_id workaround (existing)
- `src/cube/domain/model/Part.py:380` — Part.colors_id base (reads PartEdge.color)
- `src/cube/domain/model/PartEdge.py:94` — PartEdge.color (raw sticker, no provider)
- `src/cube/domain/model/CubeSanity.py:112` — Sanity check Step 4 (where it crashed)
- `src/cube/domain/solver/direct/cage/CageNxNSolver.py:454` — Cage solver 3x3 phase
- `tests/algs/bug_sanity_on.py` — The leaking test

## Status
- Phase 1 fix committed (Center.colors_id override + test leak fix)
- Phase 2 (PartEdge.color provider-aware) tracked in issue #161
- Issue #162: Tests must not mutate global CONFIG_DEFAULTS
