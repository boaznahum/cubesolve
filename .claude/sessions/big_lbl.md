# Session: big_lbl Branch - Edge Parity Implementation

## Goal
Implement even cube edge parity detection in LBL solver for middle slice solving.

## Key Files Modified
- `src/cube/domain/solver/direct/lbl/_LBLSlices.py` - Parity detection and fix methods
- `src/cube/domain/solver/direct/lbl/_common.py` - Converted `setup_l1` to class with `realign()`
- `src/cube/domain/solver/direct/lbl/_lbl_config.py` - Added `ADVANCED_EDGE_PARITY` flag
- `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py` - Minor comment

## Current Implementation Status

### What's Implemented
1. `_get_orthogonal_edges(l1_tracker)` - Gets 4 edges orthogonal to L1
2. `_get_l1_edges(l1_tracker)` - Gets 4 edges on L1 (white) face
3. `_check_and_fix_edge_parity(l1_tracker)` - Detects and applies parity fix
4. `ADVANCED_EDGE_PARITY=True` flag in `_lbl_config.py`
5. `setup_l1` class with `realign()` method
6. Retry loop in `solve_all_faces_all_rows()` with parity handling

### Current Problem
**Both advanced and non-advanced parity algorithms destroy L1 edges**

The parity algorithm (`NxNEdges._do_edge_parity_on_edge()`) disturbs the already-solved L1 edges, regardless of which mode is used. Attempting to fix this at the `_LBLSlices` level is too complicated.

## Plan: Move Parity Loop to Solver Level

Like `BeginnerReducer`, move the parity retry loop to `LayerByLayerNxNSolver._solve_impl()` so we can repeat the ENTIRE solving process after parity.

### How BeginnerReducer Does It
```python
# In BeginnerReducer.reduce():
self.solve_centers()
if self.solve_edges():  # Returns True if parity was detected/fixed
    results.partial_edge_parity_detected = True
```

The `NxNEdges.solve()` method has internal loop:
```python
self._do_first_11()  # Solve 11 edges
if not solved:
    self._do_last_edge_parity()  # Apply parity
    self._do_first_11()  # Repeat - solve the remaining edge
```

### Proposed Change for LBL Solver

1. **Remove loop from `_LBLSlices.solve_all_faces_all_rows()`** - Just solve slices once
2. **Keep parity check** - `_check_and_fix_edge_parity()` returns True if parity detected
3. **Move loop to `LayerByLayerNxNSolver._solve_impl()`**:
   ```python
   def _solve_impl(self, what):
       parity_detected = False
       while True:
           # Solve Layer 1
           self._solve_layer1(th)

           # Solve middle slices
           if self._lbl_slices.solve_all_faces_all_rows(...):
               # Parity was detected and fixed
               if parity_detected:
                   raise AssertionError("Parity twice")
               parity_detected = True
               continue  # Repeat entire process

           break

       # Continue with Layer 3...
   ```

### Benefits
- Simpler logic at slice level
- L1 gets re-solved after parity (no need to preserve it)
- Follows same pattern as BeginnerReducer
- Easier to debug and maintain

## Known Issues (Handle Later)
- Bug in `tab()` method of the logger - needs investigation

## Files to Check
- `src/cube/domain/solver/reducers/beginner/BeginnerReducer.py` - Reference implementation
- `src/cube/domain/solver/common/big_cube/NxNEdges.py` - Parity algorithm

## Next Steps
1. Commit current changes (WIP)
2. Simplify `_LBLSlices.solve_all_faces_all_rows()` - remove loop, return parity status
3. Add loop to `LayerByLayerNxNSolver._solve_impl()`
4. Test with both advanced and non-advanced modes
