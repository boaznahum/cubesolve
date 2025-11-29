# Project-Specific Instructions for Claude

## Current Work: GUI Abstraction Layer Migration

**Branch:** `new_gui`
**Status Document:** `docs/design/migration_state.md` (detailed step-by-step progress)

### Project Overview
This is a Rubik's cube solver with a 3D GUI using pyglet/OpenGL. We are migrating from direct OpenGL calls to a renderer abstraction layer to support multiple backends (pyglet, headless for testing, potentially Vulkan).

### Architecture
```
main_g.py → main_pyglet.py → Window → GCubeViewer → _Board → _FaceBoard → _Cell
                ↓
        BackendRegistry.get_backend("pyglet")
                ↓
        GUIBackend
            ├── renderer (lazy singleton) → PygletRenderer
            └── event_loop → PygletEventLoop

PygletRenderer (implements Renderer protocol)
    ├── shapes: ShapeRenderer (quad, triangle, line, sphere, etc.)
    ├── display_lists: DisplayListManager (gen_list, call_list, delete_list)
    └── view: ViewStateManager (matrix operations, screen_to_world)
```

### Key Files
- `src/cube/gui/protocols/renderer.py` - Renderer Protocol definition
- `src/cube/gui/protocols/event_loop.py` - EventLoop Protocol definition
- `src/cube/gui/backends/pyglet/renderer.py` - Pyglet renderer implementation
- `src/cube/gui/backends/pyglet/event_loop.py` - Pyglet event loop implementation
- `src/cube/gui/backends/headless/` - Headless backend for testing
- `src/cube/gui/factory.py` - BackendRegistry and GUIBackend
- `docs/design/migration_state.md` - **Detailed migration status**
- `docs/design/gui_abstraction.md` - Design documentation

### Current Status (2025-11-28)

**PHASE 1 COMPLETED (Steps 1-12):**
- Renderer protocol with ShapeRenderer, DisplayListManager, ViewStateManager
- EventLoop protocol with run(), stop(), schedule_*(), has_exit, idle(), notify()
- PygletRenderer and PygletEventLoop implementations
- AbstractWindow converted to Protocol
- main_pyglet.py uses `backend.event_loop.run()` (no direct pyglet import)
- animation_manager.py uses EventLoop (no direct pyglet import)
- Keyboard/mouse handlers use abstract Keys and MouseButton

**PHASE 2 PENDING (Steps 13-17):**
Files still using pyglet outside the backend:
- `viewer/_cell.py` - `import pyglet`, `from pyglet import gl`
- `viewer/shapes.py` - `from pyglet import gl`, `pyglet.gl.glu`
- `viewer/gl_helper.py` - `from pyglet import gl`
- `viewer/graphic_helper.py` - `from pyglet import gl`
- `main_window/Window.py` - ACCEPTABLE (this is the pyglet window class)

**Goal:** All pyglet imports should only exist in:
1. `src/cube/gui/backends/pyglet/` - The pyglet backend
2. `src/cube/main_window/Window.py` - The pyglet window class

### How to Run
- GUI: `python -m cube.main_pyglet`
- Tests (non-GUI): `python -m pytest tests/ -v --ignore=tests/gui -m "not slow"`
- Tests (GUI): `python -m pytest tests/gui -v --speed-up 5`

### Testing Requirements
**IMPORTANT:** Before committing changes, ALWAYS run BOTH test suites:
1. Non-GUI tests: `python -m pytest tests/ -v --ignore=tests/gui -m "not slow"`
2. GUI tests: `python -m pytest tests/gui -v --speed-up 5`

Both must pass before committing.

**Note:** Use `--speed-up 5` (not 2) to work around the known animation timing bug (see "Known Issues" section below).

### Check Pyglet Usage
```bash
grep -r "import pyglet\|from pyglet" src/cube --include="*.py" | grep -v "gui/backends/pyglet" | grep -v "__pycache__"
```

### Important Notes
- Renderer is REQUIRED - RuntimeError if not configured
- Display lists use internal IDs mapped to GL IDs via `DisplayListManager`
- EventLoop is wired to AnimationManager via `am.set_event_loop(backend.event_loop)`

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

**IMPORTANT**: When making changes to code or architecture, ALWAYS update the design documents.

### Files to Update

1. **`docs/design/gui_abstraction.md`** - Main design document:
   - Architecture descriptions
   - Code examples
   - Status tables
   - API documentation

2. **PlantUML diagrams** in `docs/design/`:
   - `gui_abstraction.puml` - Class diagrams and relationships
   - `gui_components.puml` - Component diagrams
   - `gui_sequence.puml` - Sequence diagrams

### When to Update

- Adding/removing functions, classes, or protocols
- Changing API signatures
- Adding/removing files or modules
- Changing relationships between components
- Updating implementation status

### Checklist

When making code changes:
- [ ] Update `gui_abstraction.md` if architecture changed
- [ ] Update `.puml` diagrams if classes/relationships changed
- [ ] Keep code examples in docs in sync with actual code
- [ ] Update status tables (✅ Done, 🔄 In Progress, etc.)

---

## Protocol Implementation Pattern

**IMPORTANT**: When implementing protocols, always inherit from them for PyCharm visibility.

### Pattern

Implementation classes should inherit from their Protocol classes:

```python
from cube.gui.protocols.renderer import Renderer, ShapeRenderer

class PygletShapeRenderer(ShapeRenderer):
    """Implements ShapeRenderer protocol."""
    ...

class PygletRenderer(Renderer):
    """Implements Renderer protocol."""
    ...
```

### Exception: Metaclass Conflicts

Some classes (like `pyglet.window.Window`) have their own metaclass that conflicts with Protocol.
In these cases, document the protocol in the docstring instead:

```python
class PygletWindow(pyglet.window.Window):
    """Pyglet window implementing Window protocol (WindowProtocol).

    Note: Cannot inherit from WindowProtocol due to metaclass conflict.
    Protocol compliance is verified at runtime via @runtime_checkable.
    """
```

### Implementation Files

- `src/cube/gui/backends/pyglet/renderer.py` - Inherits from Renderer protocols
- `src/cube/gui/backends/pyglet/animation.py` - Inherits from AnimationBackend
- `src/cube/gui/backends/pyglet/event_loop.py` - Inherits from EventLoop
- `src/cube/gui/backends/pyglet/window.py` - PygletTextRenderer inherits TextRenderer, PygletWindow cannot (metaclass)
- `src/cube/gui/backends/headless/*.py` - Same pattern as pyglet

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
- `src/cube/model/Part.py` lines 221-273 - Lazy cache properties
- `src/cube/model/_part_slice.py` lines 213-245 - Similar lazy caching
- `src/cube/model/cube_slice.py` line 230 - `reset_after_faces_changes()` call
- `src/cube/solver/begginer/l3_cross.py` line 186 - Failing assertion

**Workaround:** Press `+` key before scramble (or use `--speed-up 1+` in tests)
