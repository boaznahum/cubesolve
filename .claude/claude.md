# Project-Specific Instructions for Claude

## Current Work: GUI Abstraction Layer Migration

**Branch:** `new_gui`

### Project Overview
This is a Rubik's cube solver with a 3D GUI using pyglet/OpenGL. We are migrating from direct OpenGL calls to a renderer abstraction layer to support multiple backends (pyglet, headless for testing, potentially Vulkan).

### Architecture
```
main_g.py → main_pyglet.py → Window → GCubeViewer → _Board → _FaceBoard → _Cell
                ↓
        BackendRegistry.create_renderer(backend="pyglet")
                ↓
        PygletRenderer (implements Renderer protocol)
            ├── ShapeRenderer (quad, triangle, line, sphere, etc.)
            ├── DisplayListManager (gen_list, call_list, delete_list)
            └── ViewStateManager (matrix operations)
```

### Key Files
- `src/cube/gui/protocols/renderer.py` - Renderer Protocol definition
- `src/cube/gui/backends/pyglet/renderer.py` - Pyglet implementation
- `src/cube/gui/backends/headless/` - Headless backend for testing
- `src/cube/gui/backends/__init__.py` - BackendRegistry
- `src/cube/viewer/_cell.py` - Cell rendering (uses renderer)
- `src/cube/viewer/_board.py` - Board rendering (uses renderer)
- `src/cube/animation/animation_manager.py` - Animation (uses renderer)
- `docs/design/gui_abstraction.md` - Design documentation

### Current Status (2025-11-28)
**COMPLETED:**
- Renderer protocol with ShapeRenderer, DisplayListManager, ViewStateManager
- PygletRenderer implementation
- Migrated _cell.py, _board.py, animation_manager.py to use renderer
- Removed ALL fallback code - renderer is now REQUIRED everywhere
- GUITestRunner updated to use BackendRegistry

**REMAINING WORK:**
1. Migrate remaining direct GL calls in:
   - `viewer_g_ext.py` - draw_axis()
   - `texture.py` - TextureData texture loading
   - `app_state.py` - matrix operations (prepare_objects_view/restore_objects_view)
   - `Window.py` - draw_text() orthographic projection
2. Complete headless backend for testing
3. Update design documentation

### How to Run
- GUI: `python main_g.py`
- Tests: `python -m pytest tests/ -v --ignore=tests/gui -m "not slow"`

### Important Notes
- All code now throws `RuntimeError` if renderer is None - no fallbacks
- Display lists use internal IDs mapped to GL IDs via `DisplayListManager`
- TextureData uploads texture inside a display list - must call that list before drawing

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
