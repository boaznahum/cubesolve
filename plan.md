# Plan: Combine NxNCenters and CageCenters with preserve_3x3_state Parameter

## Overview

Create a unified `NxNCenters` class that combines the functionality of both the original `NxNCenters` (for reduction method) and `CageCenters` (for cage method) using a `preserve_3x3_state` constructor parameter.

## Key Differences Between Current Implementations

| Aspect | NxNCenters (original) | CageCenters |
|--------|----------------------|-------------|
| `_OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES` | From config | **False** (disabled) |
| `_OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS` | From config | **False** (disabled) |
| `__do_center` setup tracking | No tracking | Tracks setup_alg, undoes before return |
| `_bring_face_up_preserve_front` | Returns `None` | Returns the alg played |
| `_block_communicator` source rotation | NOT undone | Undone after commutator |
| `_swap_slice` setup moves | NOT undone | Undone after swap |

## Implementation Plan

### Step 1: Modify NxNCenters Constructor

Add `preserve_3x3_state: bool = False` parameter:

```python
def __init__(self, slv: SolverElementsProvider, preserve_3x3_state: bool = False) -> None:
    super().__init__(slv)
    self._preserve_3x3_state = preserve_3x3_state
    # ...

    if preserve_3x3_state:
        # Disable optimizations that break 3x3 state
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = False
        self._OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = False
    else:
        # Use config values (original behavior)
        self._OPTIMIZE_BIG_CUBE_CENTERS_SEARCH_COMPLETE_SLICES = cfg.optimize_big_cube_centers_search_complete_slices
        self._OPTIMIZE_ODD_CUBE_CENTERS_SWITCH_CENTERS = cfg.optimize_odd_cube_centers_switch_centers
```

### Step 2: Modify `__do_center` Method

Track and undo setup moves when `preserve_3x3_state=True`:

```python
def __do_center(self, face_loc: FaceTracker, minimal_bring_one_color: bool, use_back_too: bool) -> bool:
    # ... existing code ...

    if self._preserve_3x3_state:
        # Track all setup rotations
        setup_alg = Algs.NOOP
        # ... track each _bring_face_up_preserve_front call ...
        # Undo before each return: self.op.play(setup_alg.prime)
    else:
        # Original behavior - no tracking
        pass
```

### Step 3: Modify `_bring_face_up_preserve_front` Method

Return the algorithm played when `preserve_3x3_state=True`:

```python
def _bring_face_up_preserve_front(self, face) -> algs.Alg:
    # ... existing logic ...
    self.op.play(alg_to_play)

    if self._preserve_3x3_state:
        return alg_to_play
    return Algs.NOOP  # Original returns nothing meaningful
```

### Step 4: Modify `_block_communicator` Method

Undo source rotation when `preserve_3x3_state=True`:

```python
def _block_communicator(self, ...) -> bool:
    # ... existing code ...

    # After commutator
    if self._preserve_3x3_state and n_rotate:
        undo_alg = Algs.of_face(source_face.name).prime * n_rotate
        self.op.play(undo_alg)

    return True
```

### Step 5: Modify `_swap_slice` Method

Undo setup moves when `preserve_3x3_state=True`:

```python
def _swap_slice(self, ...):
    # ... existing code ...

    if self._preserve_3x3_state:
        # Undo source face rotation
        if n_rotate:
            op.play(rotate_source_alg.prime * n_rotate)
        # Undo F' setup
        if did_f_prime_setup:
            op.play(Algs.F)
```

### Step 6: Update Callers

#### BeginnerReducer.py (line 48)
```python
# Before:
self._nxn_centers = NxNCenters(self)

# After (no change needed - default is False):
self._nxn_centers = NxNCenters(self)  # preserve_3x3_state=False by default
```

#### CageNxNSolver.py (line 358)
```python
# Before:
from cube.domain.solver.direct.cage.CageCenters import CageCenters
cage_centers = CageCenters(self)

# After:
from cube.domain.solver.beginner.NxNCenters import NxNCenters
cage_centers = NxNCenters(self, preserve_3x3_state=True)
```

### Step 7: Delete CageCenters.py

Remove `src/cube/domain/solver/direct/cage/CageCenters.py` as it's no longer needed.

### Step 8: Update Documentation

Copy the comprehensive documentation from CageCenters into NxNCenters, documenting:
- The `preserve_3x3_state` parameter
- How it affects each method
- When to use `True` vs `False`

## Files to Modify

1. `src/cube/domain/solver/beginner/NxNCenters.py` - Add parameter and conditional logic
2. `src/cube/domain/solver/direct/cage/CageNxNSolver.py` - Update import and usage
3. `src/cube/domain/solver/direct/cage/CageCenters.py` - **DELETE**

## Testing

Run all tests after changes:
```bash
python -m mypy -p cube
python -m pyright src/cube
python -m pytest tests/ -v --ignore=tests/gui -m "not slow"
python -m pytest tests/gui -v --speed-up 5
```

## Risk Analysis

- **Low Risk**: BeginnerReducer uses default parameter (no behavior change)
- **Medium Risk**: CageNxNSolver changes from CageCenters to NxNCenters with parameter
- Tests should verify cage solver still works correctly with the unified class
