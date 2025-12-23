# Solver Template Method Refactoring Plan

## Problem Statement

Two concerns must be handled by ALL solvers but are currently inconsistent:

1. **Animation flag**: `with self._op.with_animation(animation=animation)`
2. **OpAborted handling**: `except OpAborted: return SolverResults()`

**Current state:**
- Only `NxNSolverOrchestrator` handles `OpAborted`
- Some solvers forget `with_animation()`, causing bugs
- Each solver re-implements the same boilerplate

**Consequence:**
- `CageNxNSolver` doesn't catch `OpAborted` → red traceback on abort
- Forgetting animation wrapper is a silent bug

## Current Hierarchy

```
Solver (ABC)                         # Abstract solve()
  └── AbstractSolver (ABC)           # Common: _op, _cube, debug()
        └── BaseSolver (ABC)         # Adds solution()
              ├── CageNxNSolver      # solve() - NO OpAborted handling ✗
              ├── CommutatorNxNSolver # solve() - NO OpAborted handling ✗
              ├── CFOP3x3            # solve() - NO OpAborted handling ✗
              ├── BeginnerSolver3x3  # solve() - NO OpAborted handling ✗
              └── NxNSolverOrchestrator # solve() - HAS OpAborted handling ✓
```

## Proposed Solution: Template Method Pattern

### Design

```python
# In Solver (or AbstractSolver):

from typing import final

@final  # Prevent override - subclasses MUST use _solve_impl
def solve(
    self,
    debug: bool | None = None,
    animation: bool | None = True,
    what: SolveStep = SolveStep.ALL
) -> SolverResults:
    """Public entry point. Handles animation and abort - DO NOT OVERRIDE."""

    # Handle debug flag
    if debug is not None:
        self._debug_override = debug

    with self._op.with_animation(animation=animation):
        try:
            return self._solve_impl(what)
        except OpAborted:
            return SolverResults()
        finally:
            self._debug_override = None

@abstractmethod
def _solve_impl(self, what: SolveStep) -> SolverResults:
    """Override in subclass. Called by solve() with animation/abort handled."""
    pass
```

### Benefits

1. **Impossible to forget**: Animation and OpAborted are ALWAYS handled
2. **Single place**: Common concerns in one location
3. **Clean subclasses**: Only implement `_solve_impl()`
4. **@final prevents mistakes**: Can't accidentally override `solve()`

## Implementation Steps

### Step 1: Update AbstractSolver

Add the template method in `AbstractSolver`:

```python
# src/cube/domain/solver/common/AbstractSolver.py

from typing import final
from cube.domain.exceptions import OpAborted

class AbstractSolver(Solver, ABC):

    @final
    def solve(
        self,
        debug: bool | None = None,
        animation: bool | None = True,
        what: SolveStep = SolveStep.ALL
    ) -> SolverResults:
        """Public entry point - handles animation and OpAborted."""
        if debug is not None:
            self._debug_override = debug

        with self._op.with_animation(animation=animation):
            try:
                return self._solve_impl(what)
            except OpAborted:
                return SolverResults()
            finally:
                self._debug_override = None

    @abstractmethod
    def _solve_impl(self, what: SolveStep) -> SolverResults:
        """Implement solver logic here. Animation and abort are handled."""
        pass
```

### Step 2: Update Each Solver

For each solver, rename `solve()` to `_solve_impl()` and remove boilerplate:

**CageNxNSolver:**
```python
# BEFORE:
def solve(self, debug=None, animation=True, what=SolveStep.ALL) -> SolverResults:
    sr = SolverResults()
    if self.is_solved:
        return sr
    with self._op.with_animation(animation=animation):  # REMOVE
        match what:
            ...

# AFTER:
def _solve_impl(self, what: SolveStep) -> SolverResults:
    sr = SolverResults()
    if self.is_solved:
        return sr
    match what:
        ...
```

**NxNSolverOrchestrator:**
```python
# BEFORE:
def solve(self, debug=None, animation=True, what=SolveStep.ALL) -> SolverResults:
    ...
    with self._op.with_animation(animation=animation):
        try:
            return self._solve(debug, what)
        except OpAborted:
            return SolverResults()

# AFTER:
def _solve_impl(self, what: SolveStep) -> SolverResults:
    # No need for with_animation or try/except - handled by base!
    return self._solve(what)
```

### Step 3: Update Solver Interface

Change `Solver.solve()` from `@abstractmethod` to concrete with `@final`:

```python
# src/cube/domain/solver/solver.py

class Solver(SolverElementsProvider, ABC):

    # Remove @abstractmethod from solve - it's now concrete in AbstractSolver
    # Or keep it abstract but document that AbstractSolver provides the template
```

### Step 4: Solvers to Update

| Solver | File | Changes |
|--------|------|---------|
| CageNxNSolver | `direct/cage/CageNxNSolver.py` | Rename solve→_solve_impl, remove with_animation |
| CommutatorNxNSolver | `direct/commutator/CommutatorNxNSolver.py` | Rename solve→_solve_impl, remove with_animation |
| NxNSolverOrchestrator | `NxNSolverOrchestrator.py` | Rename solve→_solve_impl, remove with_animation AND try/except |
| CFOP3x3 | `_3x3/cfop/CFOP3x3.py` | Rename solve→_solve_impl, remove with_animation |
| BeginnerSolver3x3 | `_3x3/beginner/BeginnerSolver3x3.py` | Rename solve→_solve_impl, remove with_animation |

### Step 5: Remove `except Exception` Red Traceback

After this refactoring, `OpAborted` will NEVER reach `inject_command`.
The `except Exception` block will only catch REAL errors.

No change needed in `inject_command` - it will just never see OpAborted anymore.

## Testing

1. Run all existing tests - they should pass unchanged
2. Manual test: scramble → solve → abort mid-solve
   - Should NOT show red traceback
   - Should exit cleanly

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Subclass accidentally overrides solve() | @final decorator prevents this |
| Different signature in some solver | All use same signature: debug, animation, what |
| Break existing code | Tests catch regressions |

## Open Questions

1. Should `debug` flag handling also move to template? (Currently each solver handles it)
2. Should we add logging in the template? (e.g., "Solve started", "Solve aborted")
3. Handle `what` parameter validation in template or leave to subclass?

## Summary

**Before:** Each solver must remember to:
- Wrap with `with_animation()`
- Catch `OpAborted`
- Handle debug flag

**After:** Subclasses only implement `_solve_impl()`:
- Animation wrapper: automatic
- OpAborted handling: automatic
- Debug flag: automatic
- Can't forget because can't override solve()
