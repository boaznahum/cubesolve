# Session: generic-bring-face-to

## Goal
Create a generic `bring_face_to(target_face, source_face)` method in `CommonOp` that replaces the specific methods like `bring_face_down`, `bring_face_up`, `bring_face_front`.

## Approach
TDD - Tests first, then implementation.

## Design Decisions

### Exception Design
Single `GeometryError` exception class with error codes (instead of many exception classes):

```python
class GeometryErrorCode(Enum):
    SAME_FACE = auto()      # bring_face_to(F, F) - same face
    INVALID_FACE = auto()   # unknown face

class GeometryError(Exception):
    def __init__(self, code: GeometryErrorCode, message: str):
        self.code = code
        super().__init__(f"{code.name}: {message}")
```

Location: `src/cube/domain/exceptions/GeometryError.py`

### Test Coverage
- 30 valid face pairs (6 faces x 5 other faces)
- 6 same-face cases (should raise `GeometryError` with `SAME_FACE` code)
- Parameterized tests like `test_face_pair` in `test_face2face_translator.py`

### Test Location
`tests/geometry/test_bring_face_to.py`

## Files to Create/Modify

1. `src/cube/domain/exceptions/GeometryError.py` - New exception + error codes
2. `src/cube/domain/exceptions/__init__.py` - Export new exception
3. `tests/geometry/test_bring_face_to.py` - New test file
4. `src/cube/domain/solver/common/CommonOp.py` - Add `bring_face_to` stub

## Current Status
- [x] Planning complete
- [x] Create `GeometryError` exception with codes
- [x] Create tests for `bring_face_to` (72 tests total)
- [x] Create empty `bring_face_to` stub
- [x] Implement `bring_face_to` using `derive_whole_cube_alg`
- [ ] Replace `bring_face_down`, `bring_face_up`, `bring_face_front` with `bring_face_to`

## Test Results
- **All 72 tests PASS**
  - 60 valid face-pair tests (30 pairs × 2 cube sizes)
  - 12 same-face exception tests (6 faces × 2 cube sizes)

## Implementation Details
- Made `_derive_whole_cube_alg` public as `derive_whole_cube_alg`
- Uses existing geometry infrastructure (no new hardcoded values)
- Algorithm computed dynamically from `_X_CYCLE`, `_Y_CYCLE`, `_Z_CYCLE` tables

## Next Steps
Replace `bring_face_down`, `bring_face_up`, `bring_face_front` with calls to `bring_face_to`.

## Notes
- `CommonOp.bring_face_down` has comment "# NEVER TESTED !!" at line 198
- Similar to `test_face_pair` pattern in `tests/geometry/test_face2face_translator.py`