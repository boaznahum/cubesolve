# Codebase Concerns

**Analysis Date:** 2026-01-28

## Tech Debt

### GUI Animation - Lazy Cache Initialization Bug (Critical)

**Issue:** GUI tests fail intermittently with animation enabled when lazy cache initialization is incomplete.

**Files:**
- `src/cube/domain/model/Part.py` lines 313-319 (position_id property)
- `src/cube/domain/model/Part.py` lines 357-368 (colors_id property)
- `src/cube/domain/model/PartSlice.py` lines 213-245 (similar lazy caching)
- `src/cube/domain/model/cube_slice.py` line 230 (reset_after_faces_changes)
- `tests/gui/test_gui.py` line 69 (commented skip marker)

**Mechanism:**
1. `Part.colors_id` and `Part.position_id` use lazy initialization with caching
2. Cache is reset via `reset_after_faces_changes()` after cube rotations
3. Without cached values being initialized during animation, cache state becomes inconsistent
4. Pressing speed-up key ('+') forces cache initialization via `cube.is_sanity(force_check=True)`
5. Test passes with `--speed-up 1+` but fails without it

**Impact:**
- GUI tests `test_scramble_and_solve` and `test_multiple_scrambles` are fragile
- Animation timing issues cause non-deterministic failures
- Workaround requires manual speed-up key press during animations

**Fix Approach:**
- Ensure all cache properties are eagerly initialized before animation starts
- Or refactor lazy caching to handle concurrent access safely
- Or use immutable cache strategies that don't require manual resets

---

### Commutator Solver - Incomplete Implementation (High)

**Issue:** Commutator-based solver for NxN cubes is not fully implemented.

**Files:**
- `src/cube/domain/solver/direct/commutator/CommutatorNxNSolver.py` lines 235-276
- `src/cube/domain/solver/Solvers.py` line 105

**Current State:**
- Classes exist but `get_solver_name()` raises `NotImplementedError`
- `solve()` method raises `NotImplementedError`
- Comprehensive design documentation exists but no working implementation

**Blockers:**
- SolverName enum doesn't have COMMUTATOR entry (TODO #7)
- Need commutator algorithms for centers, edges, corners, orientations
- Integration with center placement system incomplete

**Impact:**
- Alternative solving method unavailable
- Large cubes (5x5+) only support LBL/Cage methods
- Feature incomplete but documentation suggests it should be done

**Fix Approach:**
- Implement `get_solver_name()` to return proper SolverName
- Implement phase-based solving: centers → edges → corners
- Use existing commutator/conjugate utilities from CommunicatorHelper
- Start with center commutators (simplest case)

---

### MM Algorithm - Broken for Odd Cubes (High)

**Issue:** MM (Multi-Move) algorithm for edge pairing is broken and blocks odd cube face swaps.

**Files:**
- `src/cube/domain/solver/common/big_cube/NxNCenters.py` line 885

**Problem:**
- Algorithm has implementation issues preventing it from working correctly
- Face swap operations for odd cubes (5x5, 7x7) cannot complete without it
- Edge pairing phase fails when MM is required

**Impact:**
- Odd cubes cannot execute certain solving paths
- Solver must fall back to alternative (likely suboptimal) edge pairing
- Performance degradation on odd cube solving

**Fix Approach:**
- Debug edge pairing logic in MM algorithm
- Verify color assignment consistency
- Add unit tests for edge pairing with odd cubes
- Consider alternative edge pairing if MM cannot be fixed

---

### Cage Solver - Incomplete Edge Parity Handling (Medium)

**Issue:** Advanced edge parity handling not fully implemented for cage method.

**Files:**
- `src/cube/domain/solver/direct/cage/CageNxNSolver.py` lines 81, 113

**Current State:**
- Basic edge parity (single) is handled
- "Full" edge parity for even cubes marked as TODO
- `advanced_edge_parity` parameter exists but may not be used correctly

**Impact:**
- Even cube solving (4x4, 6x6) may not handle all edge parity cases
- Solver might fail or produce suboptimal solutions in rare parity states
- Test coverage may not catch these edge cases

**Fix Approach:**
- Implement full parity detection for even cubes
- Add parameterized tests for all parity combinations
- Document which parity cases are supported per cube size

---

## Known Bugs

### Tracker Majority Algorithm - Ambiguous Color Assignment (Medium)

**Issue:** With even color distribution on even cubes, the majority algorithm may produce ambiguous results.

**Files:**
- `tests_wip/test_tracker_majority_bug.py` (entire file)
- `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py` (tracker creation)

**Scenario:**
When two opposite faces are fully solved (U=YELLOW, D=WHITE) and the remaining 4 side faces have EVEN color distribution (1 each color), the majority algorithm has no clear winner to assign colors.

**Current Status:**
Under investigation (Issue #51). Tests suggest bug may not manifest due to BOY constraints, but exact reproduction is uncertain.

**Potential Impact:**
- Invalid tracker assignment (5 colors instead of 6)
- Solver fails when solving wide even cubes with specific color layouts
- May only affect edge cases, not typical random scrambles

**Workaround:**
None known - avoidable through normal random scrambles.

**Fix Approach:**
- Add deterministic tie-breaking to majority algorithm (e.g., color enum order)
- Or use alternative color assignment strategy that avoids ambiguity
- Add unit tests for pathological color distributions

---

## Performance Bottlenecks

### Large File Complexity (Medium)

**Files with >1000 lines:**
- `src/cube/domain/model/Cube.py` (2064 lines) - Too large, monolithic cube representation
- `src/cube/domain/solver/common/big_cube/NxNCenters.py` (1521 lines) - Complex center solving algorithm
- `src/cube/presentation/gui/backends/pyglet2/ModernGLRenderer.py` (1345 lines) - Large renderer implementation
- `src/cube/presentation/gui/backends/pyglet2/ModernGLCubeViewer.py` (1167 lines) - Complex GL viewer
- `src/cube/presentation/gui/backends/pyglet2/_modern_gl_cell.py` (1150 lines) - Large cell rendering
- `src/cube/domain/solver/_3x3/cfop/_F2L.py` (959 lines) - Complex F2L solving
- `src/cube/presentation/viewer/_cell.py` (725 lines) - Cell rendering logic

**Impact:**
- Hard to understand, test, and maintain
- Increased bug surface area
- Difficult to locate specific functionality
- Refactoring risk (changes affect large code regions)

**Fix Approach:**
- Break large files into focused modules
- Extract helper classes for complex algorithms
- Aim for <500 lines per file maximum
- Start with `Cube.py` - extract geometry and state management into separate modules

---

### Lazy Cache Invalidation (Medium)

**Issue:** Cache invalidation pattern with `reset_after_faces_changes()` is error-prone.

**Files:**
- `src/cube/domain/model/Part.py` lines 326-330
- `src/cube/domain/model/PartSlice.py` (similar pattern)

**Pattern:**
Cache properties (`colors_id`, `position_id`) depend on sticker colors. Manual reset required after rotations. If a rotation forgets to call reset, cache becomes stale without warning.

**Risk:**
- Easy to introduce bugs when adding new rotations
- No automatic invalidation if cache dependency changes
- Silent data corruption (wrong cached values)

**Fix Approach:**
- Use weak references or event-based cache invalidation
- Or make cache computation transparent (always recompute on access)
- Or use dataclass with automatic invalidation hooks

---

## Fragile Areas

### Presentation Layer - Dual-Backend Maintenance (High)

**Files:**
- `src/cube/presentation/gui/backends/pyglet/` - Legacy backend (display lists)
- `src/cube/presentation/gui/backends/pyglet2/` - Modern backend (shaders/VBOs)
- `src/cube/presentation/gui/backends/headless/` - Headless backend
- `src/cube/presentation/gui/backends/console/` - Console backend
- `src/cube/presentation/gui/backends/tkinter/` - Tkinter backend

**Why Fragile:**
- Each backend requires its own implementation of Renderer, EventLoop, AppWindow protocols
- Changes to protocol signatures require updates in 5 different places
- Test infrastructure requires separate virtual environments for pyglet 1.x vs 2.x
- Different OpenGL capabilities (legacy vs modern) require conditional code paths

**Safe Modification:**
- Always update protocols and ALL backend implementations together
- Test with `--backend=all` to catch regressions
- Maintain feature parity across backends
- Document backend-specific limitations (pyglet2: no animation, etc.)

**Test Coverage:**
- GUI tests for each backend exist but may have backend-specific skips
- Animation tests only work with pyglet (legacy)
- Modern GL (pyglet2) doesn't support all animation features

---

### Domain Model - Identity System (Medium)

**Files:**
- `src/cube/domain/model/Part.py` (three ID types: fixed_id, position_id, colors_id)
- `src/cube/domain/model/PartSlice.py` (similar multi-ID pattern)
- `docs/design/domain_model.md` (design reference)

**Why Fragile:**
- Three different ID types used for different purposes
- `colors_id` vs `position_id` distinction critical but easy to confuse
- Methods like `match_faces` have context-dependent behavior (invalid during center solving)
- Lazy initialization with caching makes ID computation non-obvious

**Safe Modification:**
- Always read `domain_model.md` before changing Part/PartSlice behavior
- Understand ID semantics before using them
- Test phase transitions (big cube → 3x3) thoroughly
- Verify ID consistency during center and edge solving phases

**Test Coverage:**
- Domain model tests exist but may not cover all ID consistency cases
- Phase 2 (after reduction) behavior less tested than Phase 1

---

### Solver State Management - Tracker Initialization (Medium)

**Files:**
- `src/cube/domain/tracker/PartSliceTracker.py`
- `src/cube/domain/tracker/FacesTrackerHolder.py`
- `src/cube/domain/solver/direct/lbl/LayerByLayerNxNSolver.py`

**Why Fragile:**
- Trackers depend on cube color state at initialization time
- Majority algorithm for color assignment is ambiguous in edge cases
- Tracker creation must happen before solving begins
- If cube colors change unexpectedly, trackers become invalid

**Safe Modification:**
- Always create trackers fresh at solver startup
- Don't reuse trackers across cube modifications
- Understand majority algorithm behavior before modifying
- Add assertions to verify tracker validity during solving

---

## Scaling Limits

### Cube Size Support (Medium)

**Current Support:**
- 3x3: Full support (all solvers)
- 4x4: Full support
- 5x5+: Limited - LBL and Cage methods only (Commutator not implemented)

**Limits:**
- Even cubes (4x4, 6x6): Can solve via LBL and Cage
- Odd cubes (5x5, 7x7): Limited by MM algorithm bug
- Very large (10x10+): Performance may degrade due to NxNCenters algorithm complexity

**Scaling Path:**
- Fix MM algorithm for odd cubes
- Implement Commutator solver for large cubes (more efficient)
- Profile NxNCenters on 7x7+ to identify bottlenecks

---

### Animation Performance (Low)

**Constraint:** Animation only works with pyglet 1.x (legacy OpenGL).

**Limitation:**
- pyglet 2.x (modern) backend cannot animate
- Tests with animation must use legacy environment
- Separate virtual environment required: `.venv_pyglet_legacy`

**Scaling Path:**
- Implement animation support for pyglet 2.x (use shaders/VBOs)
- Or migrate to alternative graphics library with better animation support
- Current workaround: use `--speed-up` without animation for quick testing

---

## Dependencies at Risk

### Kociemba - External Solver Dependency (Low)

**Package:** `kociemba` (3.x cube solver)

**Risk:**
- External package maintained separately
- License compatibility should be verified
- Package availability on all platforms (requires compilation)

**Current Usage:**
- Used for near-optimal solving (18-22 moves)
- Only used in 3x3 solver fallback

**Mitigation:**
- Already have LBL solver as fallback
- Kociemba is optional enhancement, not required

---

### Pyglet Version Fragmentation (Medium)

**Risk:** Incompatible versions of pyglet (1.x vs 2.x) with different capabilities.

**Current Approach:**
- Two separate environments configured
- Tests can specify backend version
- Leads to maintenance burden

**Better Approach:**
- Standardize on pyglet 2.x (modern) for new work
- Deprecate pyglet 1.x support in roadmap
- Migrate animation system to shader-based approach

---

### TypeGuard Version Override (Low)

**Files:** `pyproject.toml` line 38

**Issue:**
- Overriding signature_dispatch's constraint to support Python 3.14
- Could break compatibility with other packages using signature_dispatch

**Risk:** Low - override is specific and documented

---

## Test Coverage Gaps

### GUI Animation - Intermittent Failures (High)

**What's Not Tested:**
- Animation timing consistency
- Cache state during concurrent animation and cube modifications
- Long animation sequences without speed-up

**Files:**
- `tests/gui/test_gui.py::test_multiple_scrambles` (commented skip)
- `tests/gui/test_gui.py::test_scramble_and_solve` (passes only with speed-up)

**Risk:**
- Production GUI may fail unpredictably with animation
- Bug may only appear under specific timing conditions
- Users cannot rely on animation stability

**Priority:** HIGH - Blocks stable animation feature

---

### Solver Edge Cases - Even Color Distribution (Medium)

**What's Not Tested:**
- Tracker behavior with non-random color layouts
- Majority algorithm with ambiguous color counts
- Edge parity combinations on all cube sizes

**Files:**
- `tests_wip/test_tracker_majority_bug.py` (WIP tests, not in main suite)

**Risk:**
- Solver may fail on adversarially constructed cubes
- Normal random scrambles likely avoid these cases
- Bug may manifest in production with user-created scrambles

**Priority:** MEDIUM - Low probability but high impact if triggered

---

### Center Solving - Odd Cube Phase (Medium)

**What's Not Tested:**
- MM algorithm with various cube sizes
- Face swap operations on odd cubes
- Center parity edge cases

**Files:**
- `src/cube/domain/solver/common/big_cube/NxNCenters.py` (large, complex)
- Limited test coverage for odd cubes

**Risk:**
- Odd cube solving may fail silently or produce wrong results
- Only noticeable when solving 5x5, 7x7, etc.

**Priority:** MEDIUM - Affects large cube support

---

### Commutator Solver - Zero Test Coverage (High)

**What's Not Tested:**
- Commutator solver (unimplemented)
- All commutator types (centers, edges, corners, orientations)
- Commutator composition and simplification

**Files:**
- `src/cube/domain/solver/direct/commutator/CommutatorNxNSolver.py` (stub)

**Risk:**
- Feature cannot be used at all
- Changes to algorithm have no test protection
- Implementation may be incomplete even if written

**Priority:** HIGH - Feature is completely untested

---

## Missing Critical Features

### Commutator-Based Large Cube Solver

**What's Missing:**
- Full implementation of CommutatorNxNSolver
- Commutator algorithms for all piece types
- Integration with solver registry

**Impact:**
- Users cannot choose commutator method for large cubes
- Only LBL and Cage methods available
- Performance suboptimal for very large cubes

**Effort:** Substantial (100+ hours to implement from design docs)

---

### Animation Support for Modern OpenGL (pyglet 2.x)

**What's Missing:**
- Shader-based animation implementation
- VBO updates during animation
- Event loop integration with animation system

**Impact:**
- Users must use legacy pyglet backend for animations
- Two separate test environments required
- Deprecates older graphics technology

**Effort:** Moderate (40-60 hours)

---

## Security Considerations

### No External API Keys or Credentials Detected

**Findings:**
- No hardcoded API keys found in codebase
- Configuration uses environment variables (best practice)
- No obvious credential leaks in test files

**Safe:** No action required.

---

### Type Annotation Coverage

**Findings:**
- Most functions have type annotations
- Some legacy code may lack complete annotations
- Mypy configured in strict mode

**Improvement:**
- Run `python -m mypy -p cube` to identify gaps
- Add type annotations to untyped functions systematically
- Consider using `typeguard` at runtime for dynamic checking

---

## Architecture Violations

### Pyright Exclusion of Direct Solver (Potential Issue)

**Files:** `pyproject.toml` line 151

**Issue:**
```
exclude = ["src/cube/domain/solver/direct"]
```

Type checking is disabled for entire `direct` solver module. This hides potential type errors.

**Impact:**
- DirectSolver implementations (LBL, Cage, Commutator) not type-checked
- Type errors in solver code may go undetected
- Inconsistent with strict typing policy

**Fix Approach:**
- Re-enable Pyright for direct solvers
- Fix type errors as they appear
- Consider solving one method at a time if too many errors

---

## Documentation Gaps

### Lazy Cache System Documentation (Medium)

**Issue:**
Lazy caching with manual reset is not well documented. Developers may not understand when `reset_after_faces_changes()` needs to be called.

**Files:**
- `src/cube/domain/model/Part.py` (could use more detailed docstrings)
- `src/cube/domain/model/PartSlice.py` (similar)

**Fix:**
- Add detailed docstrings explaining cache lifecycle
- Document when cache invalidation is needed
- Provide examples of safe cache usage patterns

---

### Backend-Specific Limitations Not Documented (Medium)

**Issue:**
- Animation limitations on pyglet2 not clearly documented
- Separate environment requirements (pyglet 1.x vs 2.x) not obvious
- Backend feature matrix missing

**Files:**
- README.md could be clearer
- Design docs should include backend capability matrix

**Fix:**
- Create backend compatibility matrix (animation, features per version)
- Document required virtual environment for each backend
- Add troubleshooting guide for backend-specific issues

---

*Concerns audit: 2026-01-28*
