# Codebase Structure

**Analysis Date:** 2026-01-28

## Directory Layout

```
src/cube/                          # Main package (PascalCase filenames)
├── __init__.py                    # Package marker
├── main_any_backend.py            # Unified entry point (all backends)
├── main_console.py                # Console backend launcher
├── main_headless.py               # Headless backend launcher
├── main_pyglet2.py                # Pyglet2 backend launcher
├── main_tkinter.py                # Tkinter backend launcher
├── main_web.py                    # Web backend launcher
│
├── application/                   # Application orchestration
│   ├── AbstractApp.py             # Abstract app factory + base class
│   ├── app.py                     # _App concrete implementation
│   ├── Scrambler.py               # Cube scrambling
│   ├── Logger.py                  # Logger interface
│   ├── state.py                   # ApplicationAndViewState (view + animation)
│   ├── config_impl.py             # AppConfig implementation
│   ├── _config.py                 # Config constants
│   ├── _app_tests.py              # App unit tests
│   ├── __init__.py
│   │
│   ├── animation/                 # Animation orchestration
│   │   ├── AnimationManager.py     # Animation playback controller
│   │   ├── AnimationText.py        # Animation text rendering
│   │   └── __init__.py
│   │
│   ├── commands/                  # Command handling
│   │   ├── Operator.py            # Cube move executor + history
│   │   ├── op_annotation.py        # Algorithm notation support
│   │   ├── annotation_context.py   # Annotation markers/labels
│   │   └── __init__.py
│   │
│   ├── exceptions/                # Application exceptions
│   │   ├── app_exceptions.py       # OpAborted, AppExit, etc.
│   │   └── __init__.py
│   │
│   ├── markers/                   # Animation notation markers
│   │   ├── ...                     # Marker definitions
│   │   └── __init__.py
│   │
│   └── protocols/                 # Application protocols
│       ├── AnimatableViewer.py     # Viewer protocol
│       ├── EventLoop.py            # Event loop protocol
│       └── __init__.py
│
├── domain/                        # Pure business logic (no dependencies)
│   ├── __init__.py
│   │
│   ├── model/                     # Cube data model
│   │   ├── Cube.py                # Main cube (3x3, NxN support)
│   │   ├── Part.py                # Part base class (colors_id, position_id)
│   │   ├── PartSlice.py           # Part slice (colors_id only, no position_id)
│   │   ├── Edge.py                # Edge piece
│   │   ├── Corner.py              # Corner piece
│   │   ├── Center.py              # Center piece(s)
│   │   ├── Face.py                # Face (6 total)
│   │   ├── Color.py               # Color enum
│   │   ├── FaceName.py            # Face name enum (F, B, L, R, U, D)
│   │   ├── Slice.py               # Middle layer slice
│   │   ├── SliceName.py           # Slice name enum (M, E, S)
│   │   ├── CubeListener.py         # Observer protocol
│   │   ├── CubeSanity.py           # Cube validation
│   │   ├── CubeQueries2.py         # Cube state queries
│   │   ├── cube_slice.py           # Slice view of cube
│   │   ├── PartEdge.py             # Single sticker on part
│   │   └── __init__.py
│   │
│   ├── algs/                      # Algorithm representation
│   │   ├── Alg.py                 # Algorithm base protocol
│   │   ├── SimpleAlg.py            # Single move (R, U', M2, etc.)
│   │   ├── SeqAlg.py              # Move sequence
│   │   ├── AnnotationAlg.py        # Annotated sequence (with labels)
│   │   ├── Algs.py                # Algorithm utilities
│   │   └── __init__.py
│   │
│   ├── geometric/                 # 3D transformations
│   │   ├── cube_boy.py            # Geometry utilities
│   │   └── __init__.py
│   │
│   ├── exceptions/                # Domain exceptions
│   │   ├── cube_exceptions.py      # CubeSanity, AlgError, etc.
│   │   └── __init__.py
│   │
│   ├── solver/                    # Solving algorithms
│   │   ├── solver.py              # Solver base class + SolveStep enum
│   │   ├── Solver.py              # Solver base protocol
│   │   ├── Solvers.py             # Solver registry + orchestrator
│   │   ├── Solvers3x3.py          # 3x3 solver registry
│   │   ├── SolverName.py           # SolverName enum
│   │   ├── NxNSolverOrchestrator.py # Big cube solver selector
│   │   ├── Reducers.py            # Reducer registry
│   │   ├── AnnWhat.py             # Annotation helpers
│   │   │
│   │   ├── protocols/             # Solver protocols
│   │   │   ├── SolverProtocol.py   # Main solver protocol
│   │   │   ├── OperatorProtocol.py # Operator interface
│   │   │   ├── ReducerProtocol.py  # Reducer interface
│   │   │   ├── AnnotationProtocol.py # Notation support
│   │   │   └── __init__.py
│   │   │
│   │   ├── common/                # Shared solver utilities
│   │   │   ├── BaseSolver.py       # Base class
│   │   │   ├── AbstractSolver.py   # Abstract template
│   │   │   ├── SolverHelper.py     # Helper functions
│   │   │   ├── CommonOp.py         # Common operations
│   │   │   ├── AdvancedEvenOLLBigCubeParity.py # Parity handling
│   │   │   └── big_cube/          # Big cube utilities
│   │   │       ├── NxNCenters.py   # Center solving
│   │   │       ├── NxNEdges.py     # Edge solving
│   │   │       ├── NxNCorners.py   # Corner solving
│   │   │       └── ...
│   │   │
│   │   ├── _3x3/                  # 3x3 specific solvers
│   │   │   ├── beginner/          # Beginner method
│   │   │   │   ├── BeginnerSolver3x3.py
│   │   │   │   ├── _L1Cross.py     # Layer 1 cross
│   │   │   │   ├── _L1Corners.py   # Layer 1 corners
│   │   │   │   ├── _L2.py          # Layer 2
│   │   │   │   ├── _L3Cross.py     # Layer 3 cross
│   │   │   │   ├── _L3Corners.py   # Layer 3 corners
│   │   │   │   └── __init__.py
│   │   │   ├── cfop/              # CFOP method
│   │   │   │   ├── CFOP3x3.py      # Main CFOP solver
│   │   │   │   ├── _F2L.py         # First two layers
│   │   │   │   ├── _OLL.py         # Orientation last layer
│   │   │   │   ├── _PLL.py         # Permutation last layer
│   │   │   │   └── __init__.py
│   │   │   ├── kociemba/          # Kociemba algorithm
│   │   │   │   ├── Kociemba3x3.py  # Wrapper for external solver
│   │   │   │   └── __init__.py
│   │   │   ├── shared/            # Shared 3x3 components
│   │   │   │   ├── L1Cross.py      # L1 cross solving
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── direct/                # Direct NxN solvers
│   │   │   ├── cage/              # Cage method
│   │   │   │   ├── CageNxNSolver.py
│   │   │   │   └── __init__.py
│   │   │   ├── lbl/               # Layer-by-layer method
│   │   │   │   ├── LayerByLayerNxNSolver.py # Main LBL solver
│   │   │   │   ├── _LBLSlices.py   # Middle layer solving
│   │   │   │   ├── _LBLNxNCenters.py # Center solving
│   │   │   │   ├── _LBLNxNEdges.py # Edge solving
│   │   │   │   ├── _common.py      # LBL utilities
│   │   │   │   ├── _lbl_config.py  # Configuration
│   │   │   │   └── __init__.py
│   │   │   ├── commutator/        # Commutator method
│   │   │   │   ├── CommutatorNxNSolver.py
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── reducers/              # Reduction methods
│   │   │   ├── beginner/          # Beginner reduction
│   │   │   │   ├── BeginnerReducer.py
│   │   │   │   └── __init__.py
│   │   │   ├── AbstractReducer.py  # Base reducer
│   │   │   └── __init__.py
│   │   │
│   │   └── __init__.py
│   │
│   └── tracker/                   # State tracking (mutation tracking)
│       └── __init__.py
│
├── presentation/                  # GUI abstraction layer
│   ├── __init__.py
│   │
│   ├── gui/                       # GUI framework
│   │   ├── BackendRegistry.py      # Backend registry + get_backend()
│   │   ├── GUIBackendFactory.py    # Factory for backend components
│   │   ├── factory.py              # Public factory exports
│   │   ├── factory.py              # Public factory exports
│   │   ├── key_bindings.py         # Keyboard → Command mapping
│   │   ├── Command.py              # Command enum (~100 commands)
│   │   ├── types.py                # Type aliases (Color4, etc.)
│   │   ├── __init__.py
│   │   │
│   │   ├── protocols/              # GUI protocols
│   │   │   ├── Renderer.py         # Main renderer protocol
│   │   │   ├── EventLoop.py        # Event loop protocol
│   │   │   ├── AppWindow.py        # Application window protocol
│   │   │   ├── Window.py           # Low-level window protocol
│   │   │   ├── ShapeRenderer.py    # Shape rendering protocol
│   │   │   ├── DisplayListManager.py # Display list management
│   │   │   ├── ViewStateManager.py # View transformation protocol
│   │   │   ├── AppWindowBase.py    # Shared AppWindow logic
│   │   │   └── __init__.py
│   │   │
│   │   ├── backends/               # Backend implementations
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── pyglet2/           # Modern OpenGL backend (primary)
│   │   │   │   ├── __init__.py     # create_backend() factory
│   │   │   │   ├── PygletRenderer.py # Modern GL renderer
│   │   │   │   ├── PygletEventLoop.py # Pyglet event loop
│   │   │   │   ├── PygletAppWindow.py # Pyglet app window
│   │   │   │   ├── PygletWindow.py # Pyglet window wrapper
│   │   │   │   ├── ModernGLRenderer.py # Shader-based rendering
│   │   │   │   ├── ModernGLCubeViewer.py # Shader-based viewer
│   │   │   │   ├── PygletAnimation.py # Animation support
│   │   │   │   ├── GUIToolbar.py   # Toolbar/UI
│   │   │   │   ├── matrix.py       # Matrix operations
│   │   │   │   ├── buffers.py      # VBO/VAO management
│   │   │   │   ├── pyglet_utils.py # Utility functions
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── tkinter/           # 2D canvas backend
│   │   │   │   ├── __init__.py     # create_backend() factory
│   │   │   │   ├── TkinterRenderer.py # Canvas renderer
│   │   │   │   ├── TkinterEventLoop.py # Tkinter event loop
│   │   │   │   ├── TkinterAppWindow.py # Tkinter app window
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── console/           # Text-based backend
│   │   │   │   ├── __init__.py     # create_backend() factory
│   │   │   │   ├── ConsoleRenderer.py # Text renderer
│   │   │   │   ├── ConsoleEventLoop.py # Console event loop
│   │   │   │   ├── ConsoleAppWindow.py # Console app window
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── headless/          # Testing backend (no output)
│   │   │   │   ├── __init__.py     # create_backend() factory
│   │   │   │   ├── HeadlessRenderer.py # No-op renderer
│   │   │   │   ├── HeadlessEventLoop.py # No-op event loop
│   │   │   │   ├── HeadlessAppWindow.py # Testing window
│   │   │   │   └── ...
│   │   │   │
│   │   │   └── web/               # WebSocket + browser backend
│   │   │       ├── __init__.py     # create_backend() factory
│   │   │       ├── WebRenderer.py  # WebSocket renderer
│   │   │       ├── WebEventLoop.py # Async event loop
│   │   │       ├── WebAppWindow.py # Web app window
│   │   │       ├── static/        # Web assets
│   │   │       └── ...
│   │   │
│   │   ├── commands/              # GUI command handling
│   │   │   ├── Commands.py         # Command enum
│   │   │   ├── CommandContext.py   # Command execution context
│   │   │   ├── CommandHandler.py   # Command dispatcher
│   │   │   └── __init__.py
│   │   │
│   │   ├── effects/               # Visual effects
│   │   │   ├── CelebrationManager.py # Effect orchestration
│   │   │   ├── effects/           # Effect implementations
│   │   │   │   ├── ConfettiEffect.py
│   │   │   │   ├── VictorySpinEffect.py
│   │   │   │   └── ...
│   │   │   └── __init__.py
│   │   │
│   │   └── __init__.py
│   │
│   ├── viewer/                    # Cube visualization
│   │   ├── GCubeViewer.py          # Legacy OpenGL viewer
│   │   ├── AnimatableViewer.py     # Viewer protocol
│   │   ├── GViewerExt.py           # Extended viewer functionality
│   │   ├── _Board.py              # Board (face) rendering
│   │   ├── _FaceBoard.py          # Face board cell rendering
│   │   ├── _Cell.py               # Individual cell rendering
│   │   ├── res/                   # Resource loading
│   │   │   ├── FaceImages.py       # Face texture management
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── resources/                     # Static resources
│   ├── __init__.py
│   ├── algs/                      # Algorithm databases
│   │   ├── PLL.algs              # PLL algorithms
│   │   ├── OLL.algs              # OLL algorithms
│   │   └── __init__.py
│   └── faces/                     # Face/sticker images
│       ├── family/               # Face image set
│       ├── numbers/              # Numbered face set
│       ├── letters/              # Lettered face set
│       └── ...
│
└── utils/                         # Cross-cutting utilities
    ├── __init__.py
    ├── config_protocol.py         # ConfigProtocol definition
    ├── logger.py                  # Logger implementation
    ├── logger_protocol.py         # LoggerProtocol definition
    ├── service_provider.py         # Dependency injection base
    ├── Cache.py                   # Caching utilities
    ├── markers_config.py           # Animation marker config
    ├── text_cube_viewer.py         # Text-based cube display
    ├── OrderedSet.py              # Ordered set data structure
    ├── SSCode.py                  # Scramble string parsing
    ├── symbols.py                 # Symbol utilities
    └── prof.py                    # Profiling utilities
```

## Directory Purposes

**src/cube/application/:**
- Purpose: Application-level orchestration, state, and command handling
- Contains: AbstractApp, Operator (move executor), AnimationManager, Configuration, State
- Key insight: Bridges domain (Cube, Solver) and presentation (GUI, Renderer)

**src/cube/domain/:**
- Purpose: Pure business logic with zero presentation/framework dependencies
- Contains: Cube model, solving algorithms, geometry, exceptions
- Key insight: Can be used without any GUI (all solvers work headless)

**src/cube/presentation/gui/:**
- Purpose: GUI abstraction layer supporting multiple backends
- Contains: Protocol definitions, backend factories, command handling, effects
- Key insight: All backends implement same protocols, enabling unified entry point

**src/cube/presentation/gui/backends/**:
- Purpose: Backend-specific implementations
- Pattern: Each backend has: create_backend(), Renderer, EventLoop, AppWindow
- Lazy loading: Backends only imported when requested via BackendRegistry

**src/cube/presentation/viewer/:**
- Purpose: 3D cube visualization and animation
- Contains: GCubeViewer (logic), _Board/_FaceBoard/_Cell (rendering), AnimatableViewer protocol
- Handles: Cube state changes, animation queueing, frame updates

**src/cube/domain/solver/:**
- Purpose: Cube solving algorithms organized by method
- Structure:
  - `_3x3/` - 3x3 specific methods (Beginner, CFOP, Kociemba)
  - `direct/` - Direct NxN methods (Cage, LBL, Commutator)
  - `common/` - Shared utilities (SolverHelper, big cube utilities)
  - `reducers/` - Reduction methods (for big cubes)
- Pattern: Each solver inherits from AbstractSolver, implements solve()

**src/cube/domain/model/:**
- Purpose: Cube data model and piece representation
- Key classes:
  - Cube - Main cube (3x3, 4x4, 5x5, NxN)
  - Part/PartSlice - Piece base classes
  - Edge/Corner/Center - Specific piece types
  - Face/Slice - Face/middle-layer views
- Key insight: Fixed positions; colors rotate instead

**src/cube/utils/:**
- Purpose: Cross-cutting utilities (logging, config, caching)
- Used by: All layers via dependency injection
- No dependencies on other cube modules (utilities only)

## Key File Locations

**Entry Points:**
- `src/cube/main_any_backend.py` - Unified entry (all backends)
- `src/cube/main_pyglet2.py` - Pyglet2 specific
- `src/cube/main_tkinter.py` - Tkinter specific
- `src/cube/main_console.py` - Console specific
- `src/cube/main_headless.py` - Headless (testing)
- `src/cube/main_web.py` - Web backend

**Configuration:**
- `src/cube/application/config_impl.py` - AppConfig class (animation_speed, effects, etc.)
- `src/cube/utils/config_protocol.py` - ConfigProtocol interface
- `src/cube/application/_config.py` - Configuration constants

**Core Logic:**
- `src/cube/domain/model/Cube.py` - Main cube model
- `src/cube/application/commands/Operator.py` - Move executor
- `src/cube/domain/solver/solver.py` - Solver base
- `src/cube/presentation/gui/BackendRegistry.py` - Backend loader
- `src/cube/presentation/gui/GUIBackendFactory.py` - Component factory

**Testing:**
- `tests/` - Test suite (not shown in src tree)
- `tests/gui/` - GUI tests
- Run with: `python -m pytest tests/ -v`

**State Management:**
- `src/cube/application/state.py` - ApplicationAndViewState (view, animation, debug state)
- `src/cube/domain/model/Cube.py` - Cube state (pieces, colors)
- `src/cube/application/commands/Operator.py` - Operation history

## Naming Conventions

**Files:**
- PascalCase: `AbstractApp.py`, `Operator.py`, `Cube.py`
- Exception: lowercase for internal/private modules (e.g., `_app_tests.py`, `cube_slice.py`)
- Protocols: `*Protocol.py` suffix (e.g., `OperatorProtocol.py`, `RendererProtocol.py`)
- Implementations: Concrete names (e.g., `ModernGLRenderer.py`, `PygletAppWindow.py`)

**Directories:**
- lowercase: `application/`, `domain/`, `presentation/`, `gui/`, `backends/`
- Underscores for private: `_3x3/` (solver variants), not publicly imported

**Modules:**
- PascalCase classes: `class Cube`, `class Operator`, `class AbstractApp`
- UPPER_CASE constants: `DEFAULT_BACKEND = "pyglet2"`
- lowercase functions: `create_backend()`, `lookup_command()`

## Where to Add New Code

**New Feature (Cube Move/Algorithm):**
- Primary code: `src/cube/domain/solver/direct/` (for NxN) or `src/cube/domain/solver/_3x3/` (for 3x3)
- Base solver: Inherit from `AbstractSolver`
- Test: Create `tests/test_<solver_name>.py`
- Integration: Register in `src/cube/domain/solver/Solvers.py` or `Solvers3x3.py`

**New Backend:**
- Implementation: `src/cube/presentation/gui/backends/<backend_name>/`
- Required files:
  - `__init__.py` with `create_backend()` factory function
  - `<Backend>Renderer.py` implementing Renderer protocol
  - `<Backend>EventLoop.py` implementing EventLoop protocol
  - `<Backend>AppWindow.py` implementing AppWindow protocol
- Registration: Add to `BackendRegistry.get_backend()` in `src/cube/presentation/gui/BackendRegistry.py`

**New Command:**
- Define: Add to `Command` enum in `src/cube/presentation/gui/commands/Commands.py`
- Handler: Add method to `Operator` or `AppWindow`
- Binding: Add key mapping in `src/cube/presentation/gui/key_bindings.py`
- Execution: Implement in `Command.execute()` in `CommandContext`

**New UI Effect:**
- Implementation: `src/cube/presentation/gui/effects/effects/<EffectName>.py`
- Registration: Add to `CelebrationManager.py`
- Trigger: Set `CELEBRATION_EFFECT` in config

**New Component/Module:**
- General: Place in appropriate layer (domain/, application/, presentation/)
- Protocol: Create `*Protocol.py` in `protocols/` subdirectory
- Implementation: Create concrete class in module
- Tests: Create co-located test file (e.g., `test_<module>.py` in same directory)

**Utilities:**
- Shared helpers: `src/cube/utils/<HelperName>.py`
- Cross-cutting: No dependencies on other cube modules
- Exposed via protocols (e.g., `ConfigProtocol`, `LoggerProtocol`)

## Special Directories

**tests/:**
- Purpose: Test suite (separate from src)
- Non-GUI tests: `tests/` (exclude gui)
- GUI tests: `tests/gui/`
- Run: `python -m pytest tests/`
- Generated: No (committed)

**resources/:**
- Purpose: Static data (algorithms, face images)
- Generated: No (committed)
- Used by: GUI (face images), solvers (algorithm databases)

**build/, dist/:**
- Purpose: Package build artifacts
- Generated: Yes (via `python -m build`)
- Committed: No (in .gitignore)

**.planning/:**
- Purpose: GSD planning documents (this analysis)
- Generated: Yes (during planning phase)
- Committed: No (in .gitignore)

**.idea/:**
- Purpose: PyCharm IDE configuration
- Generated: Yes (by PyCharm)
- Committed: Yes (shared IDE settings)

**docs/:**
- Purpose: Design documentation (architecture, migration plans)
- Generated: No (hand-written)
- Key files:
  - `docs/design/gui_abstraction.md` - GUI layer design
  - `docs/design/keyboard_and_commands.md` - Command pattern
  - `docs/design/migration_state.md` - Project history
  - `docs/design/*.puml` - PlantUML diagrams

---

*Structure analysis: 2026-01-28*
