# Even Cube Support Attempt - Summary

## Goal
Add support for even cubes (4x4, 6x6, 8x8) to CageNxNSolver using virtual face colors.

## Problem
Even cubes have no fixed center piece, so face identity is ambiguous. The solver needs to track what color each face SHOULD be.

## Approach - Virtual Face Colors
1. Created `VirtualFaceColor.py` with `VirtualColorManager` class
2. Uses `Face._virtual_color` to override `Face.color` property
3. Uses FaceTrackers (corner pieces) to determine face colors
4. Context manager applies virtual colors during solve

## Implementation

### Files Modified
- **Face.py**: Added `_virtual_color` attribute to `Face` class
- **Cube.py**: Added `_rotation_hook` for X/Y/Z rotation callbacks
- **VirtualFaceColor.py**: New file with `VirtualColorManager` and `virtual_face_colors()` context manager
- **CageNxNSolver.py**: Uses virtual face colors for even cubes
- **F2L.py**: Changed d slice range from `D[1:1+n_slices]` to `D[2:1+n_slices]`
- **FaceAlg.py**: Debug code (cleaned up)
- **NxNEdges.py**: Added `ignore_center_check` for even cubes

### Key Design Decisions
1. Rotation hook on `Cube.rotate_whole()` triggers virtual color updates
2. Virtual colors update when cube rotates (Y_TRANSFORM, X_TRANSFORM, Z_TRANSFORM)
3. FaceTrackers use corner piece positions to determine face identity

## Status: FAILED

### What Works
- Odd cube tests (3x3, 5x5) pass - 17 tests
- Virtual color mechanism works correctly
- Rotation transforms update virtual colors properly

### What Fails
- Even cube test fails in F2L phase
- F2L case 3 algorithm (`R U' R' d R' U R`) places corner at wrong position
- After algorithm, corner ends up at BRD instead of FRD

### Root Cause Analysis (Incomplete)
1. Initially thought rotation updates were the problem - they're not
2. Found d slice range issue: `D[1:1+n]` includes D face (wrong), fixed to `D[2:1+n]`
3. Even with fixed d slice, algorithm still fails
4. Step-by-step tracing shows corner position diverges early in algorithm
5. May be fundamental issue with how F2L works on even cubes

## Next Steps (Not Implemented)
1. Deep investigation into F2L corner tracking on even cubes
2. Check if `Part.position_id` calculation is correct with virtual colors
3. Consider if CFOP F2L can work on even cubes at all
4. May need different approach (beginner solver for even cubes?)

## Tests
- `test_cage_even_cube_full_solve[4]` - FAILS
- `test_cage_odd_cube_full_solve[3-5-7]` - PASS (17 tests)
- Parity tests fail (unrelated feature)
