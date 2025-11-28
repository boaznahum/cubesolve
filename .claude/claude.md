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
