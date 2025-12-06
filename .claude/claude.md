# Project-Specific Instructions for Claude

## Project Overview

This is a Rubik's cube solver with a 3D GUI using pyglet/OpenGL. The codebase uses a renderer abstraction layer supporting multiple backends (pyglet, headless, console, tkinter).

**Status Document:** `docs/design/migration_state.md` (detailed history)
**Todo List:** `__todo.md` (current tasks)

### Architecture
```
main_any_backend.py → BackendRegistry.get_backend("pyglet")
                              ↓
                        GUIBackend
                            ├── renderer → PygletRenderer
                            ├── event_loop → PygletEventLoop
                            └── create_app_window() → PygletAppWindow
                                        ↓
                              GCubeViewer → _Board → _FaceBoard → _Cell

PygletRenderer (implements Renderer protocol)
    ├── shapes: ShapeRenderer (quad, triangle, line, sphere, etc.)
    ├── display_lists: DisplayListManager (gen_list, call_list, delete_list)
    └── view: ViewStateManager (matrix operations, screen_to_world)

Command Pattern (keyboard handling)
    handle_key() → lookup_command() → Command.execute(ctx)
```

### Key Files (PascalCase naming convention)
**Protocols:**
- `src/cube/presentation/gui/protocols/Renderer.py` - Renderer Protocol
- `src/cube/presentation/gui/protocols/EventLoop.py` - EventLoop Protocol
- `src/cube/presentation/gui/protocols/AppWindow.py` - AppWindow Protocol

**Pyglet Backend:**
- `src/cube/presentation/gui/backends/pyglet/PygletRenderer.py`
- `src/cube/presentation/gui/backends/pyglet/PygletEventLoop.py`
- `src/cube/presentation/gui/backends/pyglet/PygletAppWindow.py`

**Other Backends:**
- `src/cube/presentation/gui/backends/headless/` - Headless backend for testing
- `src/cube/presentation/gui/backends/console/` - Console text-based backend
- `src/cube/presentation/gui/backends/tkinter/` - Tkinter 2D canvas backend

**Command System:**
- `src/cube/presentation/gui/Command.py` - Command enum (~100 commands)
- `src/cube/presentation/gui/key_bindings.py` - Key→Command mappings

**Design Docs:**
- `docs/design/migration_state.md` - Migration history
- `docs/design/gui_abstraction.md` - Architecture design
- `docs/design/keyboard_and_commands.md` - Command pattern

### Current Status (2025-12-01)

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Core Abstraction Layer | ✅ Done |
| Phase 2 | Move Pyglet to Backend | ✅ Done |
| Phase 3 | Abstract Window Layer | ✅ Done |
| Phase 4 | PascalCase File Naming | ✅ Done |
| A2.1 | Command Pattern | ✅ Done |
| A2.2 | GUI Tests with Commands | ✅ Done |

**Tests:** 126 non-GUI tests, 2 GUI tests pass (8 skipped)

All pyglet imports now only exist in:
1. `src/cube/presentation/gui/backends/pyglet/` - The pyglet backend

### How to Run
- GUI: `python -m cube.main_pyglet`
- Tests (non-GUI): `python -m pytest tests/ -v --ignore=tests/gui -m "not slow"`
- Tests (GUI): `python -m pytest tests/gui -v --speed-up 5`

### Testing Requirements
**IMPORTANT:** Before committing changes, ALWAYS run BOTH test suites:
1. Non-GUI tests: `python -m pytest tests/ -v --ignore=tests/gui -m "not slow"`
2. GUI tests: `python -m pytest tests/gui -v --speed-up 5`

Both must pass before committing.

### Handling Test Failures
**CRITICAL:** When tests fail, NEVER assume they were "already failing" or "pre-existing issues":
1. **Investigate the failure** - Read the error message, understand what's being tested
2. **Find the root cause** - Check the test code, the code being tested, and any missing configuration
3. **Fix the issue** - Don't skip or ignore failing tests without explicit user approval
4. **Verify the fix** - Run the tests again to confirm they pass

If you need to verify whether a test was failing before your changes, use `git checkout <commit> -- .` to temporarily restore the old code and run the tests, then restore your changes.

**Note:** Use `--speed-up 5` (not 2) to work around the known animation timing bug (see "Known Issues" section below).

### Pyglet Backend Testing - SEPARATE ENVIRONMENTS

**CRITICAL:** The `pyglet` (legacy) and `pyglet2` (modern) backends require DIFFERENT Python environments because they use incompatible pyglet versions.

| Backend | Environment | Pyglet Version | OpenGL |
|---------|-------------|----------------|--------|
| `pyglet` | `.venv_pyglet_legacy` | pyglet 1.x (`<2.0`) | Legacy (display lists) |
| `pyglet2` | `.venv` (default) | pyglet 2.x (`>=2.0`) | Modern (shaders/VBOs) |

**Setup `.venv_pyglet_legacy` environment:**
```bash
python -m venv .venv_pyglet_legacy
.venv_pyglet_legacy/Scripts/pip.exe install -e ".[dev]"
.venv_pyglet_legacy/Scripts/pip.exe install --force-reinstall "pyglet>=1.5,<2.0"
```

**Running tests for each backend:**
```bash
# pyglet2 (modern) - uses default .venv
.venv/Scripts/python.exe -m pytest tests/gui -v --speed-up 5 --backend=pyglet2

# pyglet (legacy) - uses .venv_pyglet_legacy
.venv_pyglet_legacy/Scripts/python.exe -m pytest tests/gui -v --speed-up 5 --backend=pyglet
```

**NEVER mix environments:** Running pyglet (legacy) tests with pyglet 2.x installed will fail with errors like `AttributeError: module 'pyglet.gl' has no attribute 'glGenLists'` because pyglet 2.x removed legacy OpenGL functions.

### Check Pyglet Usage
```bash
grep -r "import pyglet\|from pyglet" src/cube --include="*.py" | grep -v "presentation/gui/backends/pyglet" | grep -v "__pycache__"
```

### Important Notes
- Renderer is REQUIRED - RuntimeError if not configured
- Display lists use internal IDs mapped to GL IDs via `DisplayListManager`
- EventLoop is wired to AnimationManager via `am.set_event_loop(backend.event_loop)`

---

## User Attention Alert

**IMPORTANT:** When you need the user's attention, run the beep script:

```bash
.venv_pyglet2/Scripts/python.exe beep.py
```

**Use this when:**
- Asking a question that requires user input
- Requesting permission (e.g., before committing)
- Task is complete and awaiting review
- Encountered an error or blocker that needs user decision
- Any time you would otherwise wait for user response

The script uses Windows Text-to-Speech to say "Hey Friend! Claude needs your attention!" through the user's speakers.

---

## Git Commit Policy

**IMPORTANT**: Never commit changes without explicit user approval.

### Rules:
1. After making code changes, ALWAYS show the user what was changed
2. WAIT for the user to explicitly say "commit" or "commit the changes"
3. Even if the user asks you to implement a feature, implementation does NOT imply permission to commit
4. The user wants to examine all changes before they are committed

### Workflow:
1. Make requested changes
2. Show the user what was changed
3. Ask: "Would you like me to commit these changes?"
4. Only commit after receiving explicit approval

### Examples:

**Correct:**
- User: "Add feature X"
- Claude: [implements feature] "I've added feature X. Would you like me to commit these changes?"
- User: "Yes, commit"
- Claude: [commits]

**Incorrect:**
- User: "Add feature X"
- Claude: [implements feature and commits without asking]

## Summary
When in doubt, always ask before committing. The user prefers to review changes first.

---

## Test Infrastructure Maintenance

**IMPORTANT**: When making changes to testing infrastructure, ALWAYS update related files.

### When to Update

Whenever you:
- Add new pytest flags or options (e.g., `--animate`)
- Reorganize test files or folders
- Add new test markers
- Change how tests are run
- Add new test categories or fixtures

### What to Update

1. **`tests/TESTING.md`** - Update documentation with:
   - New command-line options
   - New test organization/structure
   - New markers or fixtures
   - Examples of how to run tests

2. **PyCharm run configurations** (`.idea/runConfigurations/*.xml`) - Update paths when:
   - Moving test files to new locations
   - Renaming test files
   - Adding new frequently-used test configurations

3. **`tests/gui/conftest.py`** or root `conftest.py` - When adding:
   - New pytest fixtures
   - New command-line options
   - New pytest hooks

### Example Checklist

When reorganizing tests:
- [ ] Move files with `git mv` (preserves history)
- [ ] Update PyCharm run configurations with new paths
- [ ] Update TESTING.md project structure section
- [ ] Create `__init__.py` in new test packages
- [ ] Verify all tests still pass

---

## Design Documentation Maintenance

**CRITICAL**: When making ANY changes to code or architecture, you MUST update the design documents.
This is NOT optional. Documentation that doesn't match code is worse than no documentation.

### Design Documents

| Document | Purpose |
|----------|---------|
| `docs/design/gui_abstraction.md` | GUI backend abstraction layer |
| `docs/design/keyboard_and_commands.md` | Keyboard handling and command system |
| `docs/design/migration_state.md` | Migration progress tracking |
| `docs/design/phase3_migration_plan.md` | Phase 3 detailed plan |

### PlantUML Diagrams

- `docs/design/gui_abstraction.puml` - Class diagrams and relationships
- `docs/design/gui_components.puml` - Component diagrams
- `docs/design/gui_sequence.puml` - Sequence diagrams

### MANDATORY Update Checklist

After EVERY code change, verify:
- [ ] Design documents reflect the current architecture
- [ ] Code examples in docs match actual implementation
- [ ] API signatures in docs match actual code
- [ ] Status tables are up to date (✅ Done, 🔄 In Progress, etc.)
- [ ] New files/classes are documented

### When to Update

- **ALWAYS** when adding/removing functions, classes, or protocols
- **ALWAYS** when changing API signatures or method names
- **ALWAYS** when adding/removing files or modules
- **ALWAYS** when changing relationships between components
- **ALWAYS** when fixing architectural issues

### How to Update

1. **Read the relevant doc** before making changes
2. **Update the doc** immediately after code changes
3. **Include the doc update** in the same commit as the code change
4. **Show the user** the updated documentation

---

## Architecture Rules

**See:** `docs/design/architecture_rules.md` for comprehensive architecture rules.

Key rules (detailed in architecture_rules.md):
1. **4-Level Hierarchy:** Protocol -> Abstract -> Base -> Concrete
2. **Always inherit from protocols** - no exceptions
3. **No runtime duck typing** with `getattr()`/`hasattr()` for optional features
4. **Type annotations required** on all functions and methods
5. **Initialize attributes in `__init__`** (no lazy initialization with `hasattr`)
6. **Update UML diagrams** with every code change (diagrams must match code)

---

## Type Annotations - MANDATORY

**CRITICAL:** ALL code must have complete type annotations. This catches bugs at write time, not runtime.

### Requirements

1. **All function parameters** must have type hints
2. **All function return types** must be specified
3. **All local variables** should have type hints when the type isn't obvious
4. **Use `from __future__ import annotations`** for forward references

### Example

```python
from __future__ import annotations
from collections.abc import Collection

def process_slices(cube: Cube, label: str = "default") -> None:
    all_slices: Collection[PartSlice] = cube.get_all_parts()
    for slice_ in all_slices:
        colors_cache: PartColorsID | None = slice_._colors_id_by_colors
        # ...
```

### Why This Matters

Without type annotations, bugs like this go unnoticed:
```python
# BUG: get_all_parts() returns PartSlice, not Part
# PartSlice doesn't have position_id - only Part does
all_parts = cube.get_all_parts()  # No type hint = no IDE warning
for part in all_parts:
    pos = part.position_id  # Runtime error!
```

With type annotations, the IDE catches this immediately:
```python
all_slices: Collection[PartSlice] = cube.get_all_parts()
for slice_ in all_slices:
    pos = slice_.position_id  # IDE error: PartSlice has no attribute 'position_id'
```

---

## Domain Model - Understand Before Changing

**CRITICAL:** Before modifying domain model code, read `docs/design/domain_model.md`.

### Key Concepts

```
Cube
 ├── Part (Edge, Corner, Center) - has colors_id AND position_id
 │    └── PartSlice (EdgeWing, CornerSlice, CenterSlice) - has colors_id only
 │         └── PartEdge - single sticker on single face
```

### Important Distinctions

| Class | Has `colors_id` | Has `position_id` | Returned by |
|-------|-----------------|-------------------|-------------|
| Part | Yes | Yes | - |
| PartSlice | Yes | **No** | `cube.get_all_parts()` |
| PartEdge | No | No | - |

### Access Pattern

```python
# cube.get_all_parts() returns PartSlice objects, NOT Part
all_slices: Collection[PartSlice] = cube.get_all_parts()
for slice_ in all_slices:
    slice_.colors_id       # OK - PartSlice has this
    slice_.position_id     # ERROR - only Part has this
    slice_._parent         # Access parent Part
    slice_._parent.position_id  # OK - Part has position_id
```

---

## Known Issues & Fixes

### GUI Animation Solver Bug (Lazy Cache Initialization)

**Status:** Investigating (2025-11-28)

**Symptom:** GUI test `test_scramble_and_solve` fails with `AssertionError` at `l3_cross.py:186` when running with animation at default speed (`--speed-up 0`), but passes when `+` (speed-up) keys are pressed first.

**Root Cause:** Lazy initialization and caching of cube piece properties (`colors_id`, `position_id` in `Part` and `PartSlice` classes) combined with timing issues during animation.

**Mechanism:**
1. `Part.colors_id` and `Part.position_id` are lazily initialized (cached on first access)
2. Cache is reset via `reset_after_faces_changes()` after each cube rotation
3. Pressing `+` triggers `update_gui_elements()` → `cube.is_sanity(force_check=True)`
4. Sanity check accesses `colors_id` for all parts, forcing cache initialization
5. Without this initialization, cache state becomes inconsistent during animation

**Key Files:**
- `src/cube/domain/model/Part.py` lines 221-273 - Lazy cache properties
- `src/cube/domain/model/_part_slice.py` lines 213-245 - Similar lazy caching
- `src/cube/domain/model/cube_slice.py` line 230 - `reset_after_faces_changes()` call
- `src/cube/domain/solver/beginner/L3Cross.py` line 178 - Failing assertion

**Workaround:** Press `+` key before scramble (or use `--speed-up 1+` in tests)
