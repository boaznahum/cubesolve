# Plan: Type-Safe Sliced Alg Hierarchy

## Goal
Make slicing a **type-level** distinction. After slicing, return a different type that **cannot be sliced again** (compile-time enforcement instead of runtime).

## Current State

```
SliceAbleAlg(NSimpleAlg, ABC)
├── _slices: slice | Sequence[int] | None
├── __getitem__(items) -> Self  # raises at RUNTIME if already sliced
└── normalize_slice_index(), same_form(), ...

FaceAlg(SliceAbleAlg, AnimationAbleAlg, ABC)
├── _face: FaceName
└── _R, _L, _U, _D, _F, _B (concrete)

SliceAlg(SliceAbleAlg, AnimationAbleAlg, ABC)
├── _slice_name: SliceName
└── _M, _E, _S (concrete)
```

**Problem:** `R[1:2]` returns `_R` (same type). Re-slicing only fails at runtime.

## Proposed New Hierarchy

```
                    NSimpleAlg
                        │
          ┌─────────────┴─────────────┐
          │                           │
    FaceAlgBase                 SliceAlgBase
    (AnimationAbleAlg)          (AnimationAbleAlg)
    ├── _face                   ├── _slice_name
    ├── face_name               ├── slice_name
    ├── play()                  ├── play()
    └── get_animation_objects() └── get_animation_objects()
          │                           │
    ┌─────┴─────┐               ┌─────┴─────┐
    │           │               │           │
 FaceAlg    SlicedFaceAlg    SliceAlg   SlicedSliceAlg
 (sliceable) (NOT sliceable) (sliceable) (NOT sliceable)
    │           │               │           │
 _R,_L,...   (generic)       _M,_E,_S    (generic)
```

## Detailed Design

### 1. FaceAlgBase (NEW - Abstract Base)

```python
class FaceAlgBase(NSimpleAlg, AnimationAbleAlg, ABC):
    """Base class for all face-related algorithms (sliced and unsliced)."""

    __slots__ = ("_face",)

    def __init__(self, face: FaceName, n: int = 1):
        super().__init__(str(face.value), n)
        self._face = face

    @property
    def face_name(self) -> FaceName:
        return self._face

    @property
    @abstractmethod
    def slices(self) -> slice | Sequence[int] | None:
        """Return slice info. None for unsliced FaceAlg."""
        ...

    # play() and get_animation_objects() - shared implementation
    # that uses self.slices (None means default [1])
```

### 2. FaceAlg (Sliceable - keeps current name)

```python
class FaceAlg(FaceAlgBase, ABC):
    """Face algorithm that CAN be sliced. R[1:2] returns SlicedFaceAlg."""

    __slots__ = ()  # No _slices - unsliced by definition

    @property
    def slices(self) -> None:
        return None  # Always None for unsliced

    def __getitem__(self, items: int | slice | Sequence[int]) -> "SlicedFaceAlg":
        # Returns SlicedFaceAlg, NOT Self
        ...
```

### 3. SlicedFaceAlg (NOT Sliceable - NEW)

```python
class SlicedFaceAlg(FaceAlgBase):
    """A sliced face algorithm. CANNOT be sliced again (no __getitem__)."""

    __slots__ = ("_slices",)

    def __init__(self, face: FaceName, n: int, slices: slice | Sequence[int]):
        super().__init__(face, n)
        self._slices = slices
        self._freeze()

    @property
    def slices(self) -> slice | Sequence[int]:
        return self._slices  # Always set

    # NO __getitem__ method - prevents re-slicing at type level
```

### 4. Same Pattern for SliceAlg

- `SliceAlgBase` - common base
- `SliceAlg` - sliceable (M, E, S)
- `SlicedSliceAlg` - not sliceable

## Files to Modify

1. **NEW: `FaceAlgBase.py`** - new base class
2. **MODIFY: `FaceAlg.py`** - inherit from FaceAlgBase, change `__getitem__` return type
3. **NEW: `SlicedFaceAlg.py`** - new class
4. **NEW: `SliceAlgBase.py`** - new base class
5. **MODIFY: `SliceAlg.py`** - inherit from SliceAlgBase, change `__getitem__` return type
6. **NEW: `SlicedSliceAlg.py`** - new class
7. **MODIFY: `SliceAbleAlg.py`** - may be removed or simplified
8. **MODIFY: `__init__.py`** - export new types
9. **MODIFY: `Algs.py`** - type hints
10. **MODIFY: `state.py`** - type hints for `slice_alg()` return
11. **MODIFY: `Scramble.py`** - isinstance checks
12. **MODIFY: `Face2FaceTranslator.py`** - type hints

## Type Checking After Changes

All existing `isinstance(x, FaceAlg)` checks:
- Will be `True` for unsliced `FaceAlg` only
- Will be `False` for `SlicedFaceAlg`
- Use `isinstance(x, FaceAlgBase)` to check for any face-related alg

## Migration Notes

- `R[1:2]` now returns `SlicedFaceAlg` instead of `_R`
- Code checking `isinstance(x, SliceAbleAlg)` may need update
- `SlicedFaceAlg` has same `play()` behavior, just different type

## Baseline (before changes)

- mypy algs/: 0 errors
- pyright algs/: 0 errors
- ruff algs/: 2 errors (unused imports, pre-existing)
- Tests: 320 passed, 148 skipped
