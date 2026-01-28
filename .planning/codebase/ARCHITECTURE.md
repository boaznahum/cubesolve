# Architecture

**Analysis Date:** 2026-01-28

## Pattern Overview

**Overall:** Layered hexagonal architecture with clear separation between:
1. **Domain Layer** - Pure business logic (cube model, solving algorithms)
2. **Application Layer** - Application orchestration (command handling, animation, state management)
3. **Presentation Layer** - GUI abstraction with pluggable backends

**Key Characteristics:**
- Dependency injection from application → domain
- Protocol-driven design for renderer/window/event-loop abstraction
- Lazy singleton pattern for backend components (renderer, event_loop)
- Command pattern for keyboard/input handling
- Observer pattern for cube state changes via CubeListener protocol

## Layers

**Domain Layer:**
- Purpose: Pure cube model, solving algorithms, geometric operations
- Location: `src/cube/domain/`
- Contains:
  - Cube model (pieces, faces, colors)
  - Solving algorithms (Beginner, CFOP, Layer-by-Layer, Cage, etc.)
  - Geometric operations (rotations, transformations)
  - Algorithm representation (Alg, SimpleAlg, SeqAlg, AnnotationAlg)
- Depends on: Nothing (zero dependencies on application/presentation)
- Used by: Application layer via Operator and Solver interfaces

**Application Layer:**
- Purpose: Application orchestration, state management, animation, command dispatch
- Location: `src/cube/application/`
- Contains:
  - AbstractApp/app.py - Application factory and container
  - Operator - Command handler (rotations, solves, animations)
  - ApplicationAndViewState - Shared state (view angles, animation speed, debug settings)
  - AnimationManager - Animation orchestration
  - Scrambler - Cube scrambling
  - Commands - Command enums and context
  - Markers - Animation markers for notation
- Depends on: Domain layer
- Used by: Presentation layer (GUI backends)

**Presentation Layer:**
- Purpose: GUI rendering and windowing abstraction
- Location: `src/cube/presentation/`
- Contains:
  - GUI Protocols - Renderer, EventLoop, AppWindow, Window
  - Backend Registry - Dynamic backend loading
  - GUI Backend Factory - Component assembly
  - Backend Implementations:
    - `pyglet2/` - Modern OpenGL with shaders (primary)
    - `tkinter/` - 2D canvas rendering
    - `console/` - Text-based output
    - `headless/` - Testing backend
    - `web/` - WebSocket + browser rendering
  - Cube Viewer - 3D visualization (GCubeViewer, ModernGLCubeViewer)
  - Commands - Keyboard to command mapping
- Depends on: Application layer
- Used by: Entry points (main_*.py scripts)

**Utils Layer:**
- Purpose: Cross-cutting concerns
- Location: `src/cube/utils/`
- Contains: Logger, Config protocols, Service provider, Caching

## Data Flow

**Initialization Flow:**

1. `main_any_backend.py:create_app_window()`
2. `AbstractApp.create_non_default()` creates:
   - AppConfig (configuration)
   - ApplicationAndViewState (shared state)
   - AnimationManager (optional, if animation enabled)
   - _App instance (wraps all three)
3. `BackendRegistry.get_backend(backend_name)` creates:
   - GUIBackendFactory via `<backend>/create_backend()`
   - Lazily instantiates: Renderer, EventLoop
4. `GUIBackendFactory.create_app_window()` wires:
   - AnimationManager → EventLoop
   - AppWindow → Viewer → Renderer
   - Returns AppWindow instance
5. `AppWindow.run()` starts event loop

**User Input Flow:**

1. User presses key
2. EventLoop captures key event
3. Backend calls AppWindow.handle_key(key, modifiers)
4. AppWindow → `lookup_command(key)` → Command enum
5. Command → `CommandContext` → Operator method
6. Operator modifies Cube
7. Cube notifies CubeListener (usually Viewer)
8. Viewer schedules animation
9. AnimationManager animates over N frames
10. Each frame calls Viewer.update_gui_elements()
11. Viewer updates 3D model, renders via Renderer

**Animation Flow:**

1. Operator.do(alg) called
2. If animation_enabled:
   - Operator creates Animation object with callbacks
   - AnimationManager.animate(animation_callable)
   - Waits for animation complete
   - Calls Operator callback when done
3. If not animated:
   - Direct execution, no Animation object

**State Management:**

```
ApplicationAndViewState
├── View state (rotation angles, FOV, zoom)
├── Animation speed settings
├── Logger (debug/quiet flags)
├── Config reference
└── Cube state reference (via parent app)
```

## Key Abstractions

**Cube Model:**
- Purpose: Virtual Rubik's cube with fixed positions, rotated colors
- Examples: `src/cube/domain/model/Cube.py`, Part, Edge, Corner, Face
- Pattern: Shared piece references (Edge in 2 Faces, Corner in 3 Faces)
- Key insight: All parts at fixed positions; only colors rotate

**Operator:**
- Purpose: Executes cube moves (rotations, solves) with animation support
- Examples: `src/cube/application/commands/Operator.py`
- Pattern: Wraps cube moves, records history, triggers animation
- Key interface: `do(alg: Alg)` → rotates cube and/or animates

**Solver:**
- Purpose: Algorithm selection and execution
- Examples: BeginnerSolver3x3, CFOP3x3, LayerByLayerNxNSolver
- Pattern: Each solver implements solving for specific cube type
- Key interface: `solve(cube) → List[Alg]` → returns solving moves

**Renderer Protocol:**
- Purpose: Abstract rendering backend
- Examples: ModernGLRenderer (pyglet2), CanvasRenderer (tkinter), HeadlessRenderer
- Pattern: Protocol defines shapes, display_lists, view transformations
- Key methods: `clear()`, `begin_frame()`, `end_frame()`, `shapes.quad()`, `display_lists.gen_list()`

**EventLoop Protocol:**
- Purpose: Abstract event handling
- Examples: PygletEventLoop, TkinterEventLoop, HeadlessEventLoop
- Pattern: Polls/dispatches keyboard and mouse events
- Key methods: `start()`, `stop()`, `is_running()`, callbacks for key/mouse

**AppWindow Protocol:**
- Purpose: High-level window interface combining GUI + app logic
- Examples: PygletAppWindow, TkinterAppWindow, HeadlessAppWindow
- Pattern: Wraps backend window, coordinates Operator/Viewer/Animation
- Key methods: `run()`, `handle_key()`, `inject_command()`, `update_gui_elements()`

**Viewer/AnimatableViewer Protocol:**
- Purpose: 3D cube visualization and animation
- Examples: ModernGLCubeViewer (modern), GCubeViewer (legacy)
- Pattern: Listens to Cube changes, orchestrates animations, calls Renderer
- Key methods: `draw()`, `update_gui_elements()`, `queue_rotate()`, `animate_rotation()`

**AnimationManager:**
- Purpose: Orchestrate animation playback
- Examples: `src/cube/application/animation/AnimationManager.py`
- Pattern: Manages current animation frame/progress, calls update/draw callbacks
- Key flow: Animation object → manager updates frame → calls callbacks → renderer draws

## Entry Points

**main_any_backend.py:**
- Location: `src/cube/main_any_backend.py`
- Triggers: `python -m cube.main_any_backend [--backend=pyglet2]`
- Responsibilities:
  - Parse command-line arguments
  - Create AbstractApp via factory
  - Create AppWindow via GUIBackendFactory
  - Inject startup commands (scramble, solve sequence)
  - Run event loop
  - Cleanup resources

**Backend-Specific Entry Points:**
- `main_pyglet2.py` - Direct pyglet2 backend
- `main_tkinter.py` - Direct tkinter backend
- `main_console.py` - Direct console backend
- `main_headless.py` - Direct headless backend
- `main_web.py` - Direct web backend
- All delegate to `run_with_backend()` from main_any_backend

**Create App Window Flow:**
```python
app = AbstractApp.create_non_default(...)
backend = BackendRegistry.get_backend("pyglet2")
window = backend.create_app_window(app, width, height, title)
window.run()
```

## Error Handling

**Strategy:** Layered with exception propagation

**Patterns:**

1. **Domain Layer** - Raises domain exceptions (CubeSanity, AlgError, SolveError)
   - `src/cube/domain/exceptions/`

2. **Application Layer** - Catches domain errors, wraps in ApplicationError
   - Records in ApplicationAndViewState.error
   - Operator logs and re-raises or handles gracefully
   - `src/cube/application/exceptions/app_exceptions.py`

3. **Presentation Layer** - Catches application errors
   - AppWindow.handle_key() catches and logs
   - Displays error in UI (toolbar error label)
   - Continues running (doesn't crash)

4. **Top Level** - KeyboardInterrupt handled
   - main_any_backend.py catches KeyboardInterrupt
   - Returns 0 (clean exit)

## Cross-Cutting Concerns

**Logging:**
- Framework: `ApplicationAndViewState.debug(condition, msg)`
- Levels: debug (verbose), normal (warnings/errors)
- Flags: `debug_all=True` enables all, `quiet_all=True` suppresses all
- Env override: `CUBE_QUIET_ALL=1` env var forces quiet mode
- Output: stdout/file via Logger in `src/cube/utils/logger.py`

**Configuration:**
- Protocol: `ConfigProtocol` in `src/cube/utils/config_protocol.py`
- Implementation: `AppConfig` in `src/cube/application/config_impl.py`
- Injected: Into AbstractApp, passed to domain classes needing config
- Properties: animation_speed, celebration_effect, log paths, etc.

**Animation:**
- Manager: AnimationManager in application layer
- Framework: Animation object with update/draw/cleanup callbacks
- Speed: ApplicationAndViewState._speed (8 preset speeds)
- Integration: Viewer queues animations, AnimationManager plays them

**Dependency Injection:**
- Pattern: Factory methods (AbstractApp.create(), GUIBackendFactory.create_app_window())
- Wiring: AppWindow receives app, renderer, event_loop, viewer
- Protocols: All components expose protocol interfaces
- Lazy: Singleton patterns for renderer/event_loop (created once, reused)

---

*Architecture analysis: 2026-01-28*
