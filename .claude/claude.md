# Project-Specific Instructions for Claude

## Project Overview

This is a Rubik's cube solver with a 3D GUI using pyglet/OpenGL. The codebase uses a renderer abstraction layer supporting multiple backends (pyglet, headless, console, tkinter).

**Status Document:** `docs/design/migration_state.md` (detailed history)
**Todo List:** `__todo.md` (current tasks)

### Architecture
```
App Creation (backend owns animation):
    app = AbstractApp.create_app()          ← always Noop markers, no AM
    backend.create_app_window(app)          ← backend injects animation:
        if supports_animation:
            am = AnimationManager(app.vs)
            app.enable_animation(am)        ← swaps Noop → real markers
            am.set_event_loop(event_loop)
        AppWindow(app, ...)

Backend Components:
    GUIBackendFactory
        ├── renderer → PygletRenderer (lazy singleton)
        ├── event_loop → PygletEventLoop (lazy singleton)
        └── create_app_window() → PygletAppWindow

Renderer (implements Renderer protocol):
    ├── shapes: ShapeRenderer (quad, triangle, line, sphere, etc.)
    ├── display_lists: DisplayListManager (gen_list, call_list, delete_list)
    └── view: ViewStateManager (matrix operations, screen_to_world)

Viewer Hierarchy:
    GCubeViewer → _Board → _FaceBoard → _Cell

Command Pattern (keyboard handling):
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

**Migration:** All 6 phases complete (see `docs/design/migration_state.md`). All pyglet imports isolated to `src/cube/presentation/gui/backends/pyglet/`.

### How to Run
- GUI: `python -m cube.main_pyglet`
- Tests (non-GUI, non-slow): `python -m pytest tests/ -v -m "not gui and not slow"`
- Tests (GUI): `python -m pytest tests/gui -v --speed-up 5`

### Environment Setup (Headless / Claude Code on Web)
- **Python 3.13+** required. On Linux use `python3.13`. Install kociemba with `--use-pep517`.

### All Checks (run before committing)

**CRITICAL:** When user says "run all checks", run ALL FIVE of these:

```bash
# 1. Ruff linter (fast - run first)
python -m ruff check src/cube

# 2. Mypy type checker
python -m mypy -p cube

# 3. Pyright type checker
python -m pyright src/cube

# 4. Non-GUI, non-slow tests (ALWAYS use CUBE_QUIET_ALL=1 to suppress debug output)
# Bash/Linux:
CUBE_QUIET_ALL=1 python -m pytest tests/ -v -m "not gui and not slow"
# PowerShell/Windows:
# $env:CUBE_QUIET_ALL="1"; python -m pytest tests/ -v -m "not gui and not slow"

# 5. GUI tests (ALWAYS use CUBE_QUIET_ALL=1 to suppress debug output)
# Bash/Linux:
CUBE_QUIET_ALL=1 python -m pytest tests/gui -v --speed-up 5
# PowerShell/Windows:
# $env:CUBE_QUIET_ALL="1"; python -m pytest tests/gui -v --speed-up 5
```

**ALL FIVE must pass before committing.** Ruff is fastest so run it first. Use `ruff check --fix` to auto-fix issues.

**ALWAYS FIX ALL ERRORS:** When running checks, fix ALL errors you encounter - even if they are pre-existing or unrelated to your current changes. Never say "this error was pre-existing" or "not caused by my change" as an excuse to skip fixing it. Just fix it.

### Tagging Passing Commits

**IMPORTANT:** When a commit passes ALL checks (all 5 checkers + all tests under tests/), create a git tag and push it:

```bash
# Create tag with timestamp (format: pass-YYYYMMDD-HHMMSS)
git tag pass-$(date +%Y%m%d-%H%M%S)

# Push the tag
git push origin --tags
```

This helps identify known-good commits for easy rollback if needed.

**Note:** Pyright uses `typeCheckingMode = "standard"` (configured in `pyproject.toml`), which is stricter than mypy. It catches:
- Undefined variables that mypy misses
- Method override issues (incompatible parameter types/names)
- `__all__` declarations that don't match actual exports

### Handling Test Failures
**CRITICAL:** When tests fail, NEVER assume they were "already failing" or "pre-existing issues":
1. **Investigate the failure** - Read the error message, understand what's being tested
2. **Find the root cause** - Check the test code, the code being tested, and any missing configuration
3. **Fix the issue** - Don't skip or ignore failing tests without explicit user approval
4. **Verify the fix** - Run the tests again to confirm they pass

If you need to verify whether a test was failing before your changes, use `git checkout <commit> -- .` to temporarily restore the old code and run the tests, then restore your changes.

### Test Skipping Policy - NEVER SKIP TESTS
**CRITICAL:** Do NOT add `pytest.skip()` or `@pytest.mark.skip`. Always fix the underlying issue instead. If a backend lacks a feature, add a stub/no-op. Discuss with user before any skip. Use `--speed-up 5` for GUI tests (animation timing workaround).

### Pyglet Backend Testing - SEPARATE ENVIRONMENTS
`pyglet` (legacy, pyglet 1.x) uses `.venv_pyglet_legacy`; `pyglet2` (modern, pyglet 2.x) uses `.venv`. **NEVER mix** — pyglet 2.x removed legacy GL functions. See `tests/TESTING.md` for setup details.

### Important Notes
- Renderer is REQUIRED - RuntimeError if not configured
- Display lists use internal IDs mapped to GL IDs via `DisplayListManager`
- **Backend owns animation:** App always starts without AM. Backend calls `app.enable_animation(am)` + `am.set_event_loop(event_loop)` if it supports animation. No circular dependency.

---

## PyCharm MCP Server - Token Optimization

**Use PyCharm MCP tools when possible to save tokens, but not at the cost of quality.**

**Prefer PyCharm MCP for:**
- `get_file_problems` - Code inspections (finds issues without reading whole file)
- `search_in_files_by_text/regex` - Searching code
- `find_files_by_name_keyword` - Finding files by name
- `list_directory_tree` - Directory structure
- `rename_refactoring` - Safe symbol renaming across project
- `get_symbol_info` - Understanding symbols at a position
- `execute_run_configuration` - Running tests/apps

**Use regular tools when:**
- Need precise line-by-line file reading
- PyCharm results are incomplete or insufficient
- Need Claude's own analysis/judgment
- Quality would suffer

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

## WebGL Backend — Server Restart Notifications

**CRITICAL:** When working on the WebGL backend, ALWAYS tell the user when they need to restart the Python server.

- **Python changes** (anything under `src/cube/`): **Server restart required.** Always tell the user: "You need to restart the Python server to pick up these changes."
- **JS/HTML/CSS changes** (anything under `static/`): **Browser refresh only.** Tell the user: "Just refresh the browser — no server restart needed."
- **Mixed changes** (both Python and JS): Tell the user: "Restart the server and refresh the browser."

Never assume the user knows which changes require a restart. Always be explicit.

---

## Version Management - MANDATORY

**CRITICAL:** On ANY code change, increment the version number before committing.

- **Version file:** `src/cube/resources/version.txt` (single line, e.g. `1.0`)
- **Version reader:** `src/cube/version.py` → `get_version()`
- **Displayed in:** Web backend status bar ("Connected v1.0")
- **Rule:** Bump version in `version.txt` with every commit:
  - Patch (`1.0` → `1.0.1`) for bugfixes
  - Minor (`1.0` → `1.1`) for features
  - Major (`1.0` → `2.0`) for breaking changes

---

## Git Commit Policy

**IMPORTANT**: Never commit without explicit user approval. Implementation does NOT imply permission to commit.

### Workflow:
1. Make changes, self-review the diff, fix issues
2. Show user what changed, ask "Would you like me to commit?"
3. Only commit after explicit approval

### Pre-Commit Checklist:
1. `git diff --name-only` — list modified files
2. `grep -i "claude"` in all modified files — find embedded instructions, ask user about each
3. Never undo user code or `git checkout` without permission
4. Review new methods — add docstrings if missing, ask user if purpose unclear

---

## Test Infrastructure Maintenance

When changing test infrastructure (new flags, markers, fixtures, file moves), update: `tests/TESTING.md`, PyCharm run configs (`.idea/runConfigurations/`), and `conftest.py`. Use `git mv` for moves.

---

## Design Documentation Maintenance

**CRITICAL**: When changing code/architecture, update the matching design docs in the same commit.
- Docs: `docs/design/gui_abstraction.md`, `keyboard_and_commands.md`, `migration_state.md`, `phase3_migration_plan.md`
- Diagrams: `docs/design/*.puml` (class, component, sequence)
- Update whenever adding/removing/renaming functions, classes, protocols, files, or APIs

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

ALL code must have complete type annotations: function parameters, return types, non-obvious locals. Use `from __future__ import annotations` for forward references.

---

## Domain Model - Understand Before Changing

Read `docs/design/domain_model.md` before modifying domain code. Key: `cube.get_all_parts()` returns `PartSlice` (has `colors_id`, no `position_id`). Access `position_id` via `slice_._parent`.

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
- Do NOT run tests after modification without asking — user must review the solution first

---

## Model Routing for Subagents

Default subagents to cheaper models when possible:
- **Haiku**: Explore agents, file search/counting, data gathering, grep-heavy tasks
- **Sonnet**: Code analysis, synthesis, judgment calls, implementation
- **Opus**: Complex multi-step reasoning, architecture decisions (main thread only)

Use the `model` parameter on Agent tool calls. Haiku is 60x cheaper than Opus for input tokens.

---

## Session Notes - MANDATORY

**CRITICAL:** For every session, maintain a session notes file to persist progress across sessions.

### Location & Naming

```
.claude/sessions/<branch-name>.md
```

Example: For branch `claude/create-transforms-8ecXU`, the file is:
```
.claude/sessions/claude-create-transforms-8ecXU.md
```

### Requirements

1. **Create on first session** if it doesn't exist
2. **Update on any progress** - document what was done, what works, what fails
3. **Make it ready to continue** - another session should be able to pick up where you left off
4. **Include**:
   - Overview of the task/goal
   - Key files modified
   - Current status (what works, what's broken)
   - Next steps
   - Commits made
   - Any debugging notes or insights

### Purpose

This ensures continuity across Claude sessions. When starting work on a branch:
1. Check if `.claude/sessions/<branch-name>.md` exists
2. Read it to understand current state
3. Continue from where the previous session left off
4. Update the file with your progress before ending