# Rubik's Cube Solver - Architecture Documentation

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Layers](#architecture-layers)
4. [Component Details](#component-details)
5. [Design Patterns](#design-patterns)
6. [Data Flow](#data-flow)
7. [Key Design Decisions](#key-design-decisions)
8. [Extension Points](#extension-points)
9. [Strengths and Improvements](#strengths-and-improvements)
10. [File Structure Reference](#file-structure-reference)

---

## Executive Summary

This is a Python-based 3D Rubik's Cube solver with **~13,143 lines of code** organized into a sophisticated layered architecture. The system supports both 3x3 and NxN cubes with multiple solving strategies (Beginner Layer-By-Layer and CFOP), smooth 3D animation using OpenGL/Pyglet, and a rich keyboard/mouse control interface.

**Key Highlights:**
- ✅ Clean separation into 8 major layers
- ✅ Extensive use of design patterns (Composite, Strategy, Command, Observer)
- ✅ Highly extensible architecture (pluggable solvers, algorithms, viewers)
- ✅ Domain-driven design with rich domain model
- ✅ Support for cubes from 3x3 to NxN

**Architecture Score: 8.5/10**

---

## System Overview

### Technology Stack

```
┌─────────────────────────────────────────────┐
│  Language: Python 3.10+                     │
│  Graphics: Pyglet + OpenGL 1.x             │
│  Math: NumPy                                │
│  Type System: Extensive type hints          │
└─────────────────────────────────────────────┘
```

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Entry Point                             │
│                      main_g.py                               │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   Presentation Layer                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Window (main_window/)                                 │ │
│  │  - Pyglet Window                                       │ │
│  │  - Keyboard Handler                                    │ │
│  │  - Mouse Handler                                       │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   Application Layer                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  App (app/)                                            │ │
│  │  - Component Orchestration                             │ │
│  │  - ApplicationAndViewState                             │ │
│  │  - Testing Framework                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└──────┬───────────────────┬────────────────────┬──────────────┘
       │                   │                    │
       │                   │                    │
┌──────▼──────┐   ┌───────▼────────┐   ┌──────▼──────────────┐
│   Solver    │   │   Operator     │   │   AnimationMgr      │
│  (solver/)  │   │  (operator/)   │   │   (animation/)      │
│             │   │                │   │                     │
│  Strategy   │   │   Mediator     │   │   Observer          │
│  Pattern    │   │   + History    │   │   Pattern           │
└──────┬──────┘   └───────┬────────┘   └──────┬──────────────┘
       │                   │                    │
       │                   │                    │
       └──────────┬────────┴────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                  Core Domain Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Algorithms  │  │    Model     │  │     Viewer       │ │
│  │   (algs/)    │  │   (model/)   │  │    (viewer/)     │ │
│  │              │  │              │  │                  │ │
│  │  Composite   │  │  Cube/Parts  │  │  OpenGL/Pyglet   │ │
│  │  Pattern     │  │  Faces/Slices│  │  3D Rendering    │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Layers

### Layer Dependency Rules

```
Presentation ──────> Application ──────> Domain
     ↓                    ↓                  ↓
 No down deps      Depends on Domain    Independent
```

**Key Principles:**
- ✅ Clean downward flow: Upper layers depend on lower layers
- ✅ No upward dependencies: Lower layers don't know about upper layers
- ✅ Interface-based coupling: Layers use protocols/ABCs

### Layer Details

#### 1. Presentation Layer (`main_window/`)

**Responsibility:** Handle user input and display

**Components:**
- `Window`: Pyglet window managing events
- `main_g_keyboard_input.py`: All keyboard event handling
- `main_g_mouse.py`: Mouse event handling

**Key Classes:**
```python
class Window(AbstractWindow, AnimationWindow):
    def on_draw()
    def on_resize(width, height)
    def on_key_press(symbol, modifiers)
    def on_mouse_press(x, y, button, modifiers)
```

#### 2. Application Layer (`app/`)

**Responsibility:** Orchestrate components and manage state

**Components:**
- `_App`: Main application orchestrator (Facade pattern)
- `ApplicationAndViewState`: Centralized state management
- `_app_tests.py`: Testing framework

**Key Interface:**
```python
class AbstractApp(ABC):
    @property
    def cube() -> Cube
    @property
    def op() -> Operator
    @property
    def slv() -> Solver
    @property
    def am() -> AnimationManager
```

#### 3. Domain Layer

##### a. Algorithms Layer (`algs/`)

**Responsibility:** Define cube moves and sequences

**Hierarchy:**
```
Alg (Abstract Base)
├── SimpleAlg (Atomic moves)
│   └── NSimpleAlg
│       └── AnimationAbleAlg
│           ├── FaceAlgBase (common face properties)
│           │   ├── FaceAlg (R, L, U, D, F, B) - also inherits SliceAbleAlg
│           │   └── SlicedFaceAlg - result of R[1:2], NOT SliceAbleAlg
│           ├── SliceAlgBase (common slice properties)
│           │   ├── SliceAlg (M, E, S) - also inherits SliceAbleAlg
│           │   └── SlicedSliceAlg - result of M[1:2], NOT SliceAbleAlg
│           ├── WholeCubeAlg (x, y, z)
│           └── DoubleLayerAlg (Wide moves: Rw, Lw, etc.)
├── SliceAbleAlg (Marker ABC - for isinstance checks)
├── SeqAlg (Composite - sequences)
├── Inv (Decorator - inverse)
└── Mul (Decorator - repetition)
```

**Key Features:**
```python
# Operator overloading enables DSL-like syntax
alg = R + U + R.prime + U.prime  # Sequence
alg = R * 3                       # Repetition
alg = -R                          # Inverse
alg = R[1:3]                      # Slicing (layers)
```

##### b. Model Layer (`model/`)

**Responsibility:** Represent the physical cube structure

**Core Components:**

```
Cube
├── 6 x Face (F, B, L, R, U, D)
│   └── Each Face contains:
│       ├── 4 x Corner (3 colors)
│       ├── 4 x Edge (2 colors)
│       └── 1 x Center (1 color)
│
└── 3 x Slice (M, E, S)
    └── Each Slice contains:
        ├── 4 x Edge
        └── 4 x Center
```

**Part Hierarchy:**
```
Part (Abstract Base)
├── Edge (2-color piece)
│   └── EdgeWing (for NxN cubes)
├── Corner (3-color piece)
│   └── CornerSlice
└── Center (1-color piece)
    └── CenterSlice (i, j position)
```

**Key Design:**
- **Shared Edges:** Adjacent faces share `PartEdge` objects
- **Fixed IDs:** Parts have immutable IDs for tracking
- **NxN Support:** Parts contain multiple slices

##### c. Solver Layer (`solver/`)

**Responsibility:** Implement solving algorithms

**Architecture:**
```
SolverElementsProvider (Protocol)    <- Minimal interface for solver components
├── BaseSolver                       <- Base class for 3x3 solvers
│   ├── BeginnerSolver3x3
│   ├── CFOP3x3
│   └── Kociemba3x3
│
└── AbstractReducer                  <- Base class for NxN reducers
    └── BeginnerReducer

SolverHelper(provider: SolverElementsProvider)  <- All step solvers
├── L1Cross, L1Corners, L2           (Layer 1-2)
├── L3Cross, L3Corners               (Layer 3)
├── OLL, PLL                         (CFOP steps)
└── NxNCenters, NxNEdges             (Big cube reduction)
```

**Key Design:** `SolverElementsProvider` protocol allows both solvers and reducers
to use the same solver elements (NxNCenters, NxNEdges, etc.) without facade classes.

See: `src/cube/domain/solver/SOLVER_ARCHITECTURE.md` for detailed class hierarchy.

##### d. Operator Layer (`operator/`)

**Responsibility:** Execute algorithms and manage history

**Command Pattern Implementation:**
```python
class Operator:
    # Execute commands
    def play(alg: Alg, inv: bool, animation: bool)

    # Undo/Redo
    def undo(animation: bool) -> Alg | None
    def history() -> Sequence[Alg]

    # Recording
    @contextmanager
    def record() -> Sequence[Alg]

    # Animation control
    @contextmanager
    def with_animation(enabled: bool)
```

##### e. Viewer Layer (`viewer/`)

**Responsibility:** 3D rendering using OpenGL

**Composite Pattern:**
```
GCubeViewer
└── _Board
    └── 6 x _FaceBoard (one per face)
        └── N² x _Cell (individual stickers)
```

**Rendering Pipeline:**
```
GCubeViewer.update()
  └─> _Board.update()
      └─> _FaceBoard.update()
          └─> _Cell.update()

GCubeViewer.draw()
  └─> Batch.draw() [OpenGL]
```

##### f. Animation Layer (`animation/`)

**Responsibility:** Smooth animation of cube moves

**Observer Pattern:**
```
AnimationManager
├─> run_animation(cube, op, alg)
├─> Create Animation with closures
├─> Pyglet event loop calls update/draw
└─> Cleanup and apply to cube state
```

---

## Component Details

### Model Layer Deep Dive

#### Cube Structure

```python
class Cube:
    # Properties
    size: int                    # 3 for 3x3, 4 for 4x4, etc.
    n_slices: int                # Number of middle slices

    # Faces
    front, back: Face
    left, right: Face
    up, down: Face

    # Slices
    m_slice: Slice  # Middle (between L and R)
    e_slice: Slice  # Equatorial (between U and D)
    s_slice: Slice  # Standing (between F and B)

    # Operations
    def rotate_face_and_slice(n, face_name, slices)
    def sanity() -> bool  # Validate cube state
    @property
    def solved() -> bool
```

#### Part System

```
┌─────────────────────────────────────────────┐
│                   Part                      │
│  ┌──────────────────────────────────────┐  │
│  │  fixed_id: PartFixedID (immutable)   │  │
│  │  all_slices: list[PartSlice]         │  │
│  └──────────────────────────────────────┘  │
└───────────┬─────────────────────────────────┘
            │
    ┌───────┴───────┬──────────┐
    │               │          │
┌───▼────┐   ┌─────▼─────┐   ┌▼───────┐
│  Edge  │   │  Corner   │   │ Center │
│        │   │           │   │        │
│ 2 faces│   │  3 faces  │   │ 1 face │
└────────┘   └───────────┘   └────────┘
```

**Key Insight:** Parts share edges with adjacent faces:
```python
# Front-right edge is shared by both faces
f._edge_right = r._edge_left = _create_edge(edges, f, r, True)
```

### Algorithm Layer Deep Dive

#### Composite Pattern Implementation

```
                         Alg
                          │
          ┌───────────────┼───────────────┬──────────────┐
          │               │               │              │
     SimpleAlg         SeqAlg         Decorator    SliceAbleAlg
          │               │               │          (marker ABC)
     NSimpleAlg      [Alg, ...]      ┌───┴───┐
          │                          │       │
  AnimationAbleAlg                  Inv     Mul
          │                         (')    (*n)
    ┌─────┼─────┬─────────────┐
    │     │     │             │
FaceAlgBase SliceAlgBase WholeCubeAlg DoubleLayerAlg
    │     │                   (x,y,z)    (Rw,Lw,...)
 ┌──┴──┐  ┌──┴──┐
 │     │  │     │
FaceAlg SlicedFaceAlg SliceAlg SlicedSliceAlg
(R,L,..)  (R[1:2])    (M,E,S)   (M[1:2])
   ↑                     ↑
   └── SliceAbleAlg ─────┘  (FaceAlg & SliceAlg inherit SliceAbleAlg)
```

**Type-Safe Slicing:** `FaceAlg.__getitem__()` returns `SlicedFaceAlg` (not `Self`).
`SlicedFaceAlg` has no `__getitem__` - compile-time prevention of re-slicing.
`isinstance(R, SliceAbleAlg)` is True, but `isinstance(R[1:2], SliceAbleAlg)` is False.

**Example Composition:**
```python
# Define sexy move
sexy_move = R + U + R.prime + U.prime

# T-perm algorithm
t_perm = (R + U + R.prime + U.prime +
          R.prime + F + R*2 + U.prime + R.prime +
          U.prime + R + U + R.prime + F.prime)

# Repeat 3 times
alg = t_perm * 3

# Inverse
alg_inverse = -t_perm
```

**Algorithm Simplification:**
```python
alg = R + R + R + R  # Four R's
alg.simplify()       # → Empty (R⁴ = identity)

alg = R + R.prime    # R and R'
alg.simplify()       # → Empty (cancels)

alg = R*2 + R.prime  # R² and R'
alg.simplify()       # → R
```

### Solver Layer Deep Dive

#### Beginner Solver Flow

```
BeginnerSolver.solve()
    │
    ├─> L1Cross.solve()
    │   └─> Orient 4 edge pieces
    │       └─> Position 4 edge pieces
    │
    ├─> L1Corners.solve()
    │   └─> For each corner:
    │       ├─> Move to top layer
    │       ├─> Orient correctly
    │       └─> Insert into position
    │
    ├─> L2.solve()
    │   └─> For each middle edge:
    │       ├─> Move to top
    │       └─> Apply algorithm (UR or UL)
    │
    ├─> L3Cross.solve()
    │   └─> Orient top edges (cross pattern)
    │       └─> Permute top edges
    │
    └─> L3Corners.solve()
        ├─> Permute corners (T-perm)
        └─> Orient corners (Sune)
```

#### CFOP Solver Flow

```
CFOP.solve()
    │
    ├─> L1Cross (same as beginner)
    │
    ├─> F2L.solve()
    │   └─> For each of 4 corner-edge pairs:
    │       └─> Insert together (1-look)
    │
    ├─> OLL.solve()
    │   └─> Orient all last layer pieces
    │       └─> Apply one of 57 OLL algorithms
    │
    └─> PLL.solve()
        └─> Permute last layer
            └─> Apply one of 21 PLL algorithms
```

### Operator Layer Deep Dive

#### Command Pattern with History

```
┌─────────────────────────────────────────┐
│            Operator                     │
│                                         │
│  _history: [Alg₁, Alg₂, ..., Algₙ]    │
│  _recording: Optional[List[Alg]]       │
│                                         │
│  play(alg) ──────> Execute + Save      │
│  undo() ─────────> Pop + Execute inv   │
│  record() ───────> Start recording     │
└─────────────────────────────────────────┘
```

**History Management:**
```python
# Execute sequence
op.play(R)
op.play(U)
op.play(R.prime)

# History now: [R, U, R']

# Undo
op.undo()  # Executes R (inverse of R')
# History now: [R, U]

op.undo()  # Executes U'
# History now: [R]
```

**Recording:**
```python
with op.record() as recording:
    op.play(R)
    op.play(U)
    op.play(R.prime)

# recording = [R, U, R']
# Can replay later: op.play_seq(recording)
```

### Animation Layer Deep Dive

#### Animation Lifecycle

```
┌──────────────────────────────────────────────────────┐
│  1. Operator.play(R, animation=True)                 │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  2. AnimationManager.run_animation(cube, op, R)      │
│     ├─> Get animation objects from viewer            │
│     ├─> Calculate rotation axis and increments       │
│     └─> Create Animation with closures               │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  3. Pyglet Event Loop                                │
│     ├─> update() [called periodically]               │
│     │   ├─> Increment rotation angle                 │
│     │   └─> Update viewer geometry                   │
│     │                                                 │
│     └─> draw() [called every frame]                  │
│         └─> Render updated geometry                  │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  4. Animation Complete                               │
│     ├─> Operator.play(R, animation=False)            │
│     │   └─> Update cube model                        │
│     └─> Cleanup animation                            │
└──────────────────────────────────────────────────────┘
```

**Key Design:** Animation modifies geometry (visual), not model (logical). Model updates only at end.

---

## Design Patterns

### 1. Composite Pattern (Algorithms)

**Intent:** Allow treating individual algorithms and compositions uniformly

**Structure:**
```
<<interface>> Alg
  + play(cube, inv)
  + count()
  + inv()
       ▲
       │
   ┌───┴────┐
   │        │
SimpleAlg  SeqAlg
           ├─> List<Alg>
           └─> Recursively calls play()
```

**Implementation:**
```python
# Location: cube/algs/

class Alg(ABC):
    @abstractmethod
    def play(self, cube: Cube, inv: bool = False):
        pass

class SeqAlg(Alg):
    def __init__(self, *algs: Alg):
        self._algs = [*algs]

    def play(self, cube: Cube, inv: bool = False):
        if inv:
            for a in reversed(self._algs):
                a.play(cube, True)
        else:
            for a in self._algs:
                a.play(cube, False)
```

**Benefits:**
- ✅ Uniform interface for simple and complex algorithms
- ✅ Recursive composition: `SeqAlg(R, SeqAlg(U, R.prime), U.prime)`
- ✅ Easy to extend with new algorithm types

### 2. Strategy Pattern (Solvers)

**Intent:** Encapsulate solving algorithms and make them interchangeable

**Structure:**
```
┌──────────────┐
│   Context    │
│   (App)      │
│ ┌──────────┐ │
│ │  solver  │ │
│ └────┬─────┘ │
└──────┼───────┘
       │ uses
       ▼
<<interface>> Solver
  + solve()
  + is_solved
       ▲
       │
   ┌───┴────┬────────┐
   │        │        │
Beginner  CFOP   Kociemba
```

**Implementation:**
```python
# Location: cube/solver/

class Solver(ABC):
    @abstractmethod
    def solve(self, debug: bool | None,
              animation: bool | None,
              what: SolveStep) -> SolverResults:
        pass

# Factory for creating solvers
class Solvers:
    @staticmethod
    def default(op: Operator) -> Solver:
        return BeginnerSolver(op) if config.SOLVER_LBL else CFOP(op)

    @staticmethod
    def by_name(name: SolverName, op: Operator) -> Solver:
        # Factory method
        pass
```

**Benefits:**
- ✅ Solvers can be swapped at runtime
- ✅ Easy to add new solving algorithms
- ✅ Each solver has independent implementation

### 3. Command Pattern (Operator)

**Intent:** Encapsulate operations as objects to support undo/redo

**Structure:**
```
┌─────────────┐
│  Invoker    │
│ (Operator)  │      ┌──────────────┐
│ ┌─────────┐ │      │   Command    │
│ │ history │─┼─────>│    (Alg)     │
│ └─────────┘ │      │ + play()     │
│             │      │ + inv()      │
│ + play()    │      └──────────────┘
│ + undo()    │              │
└─────────────┘              │ operates on
                             ▼
                      ┌──────────────┐
                      │   Receiver   │
                      │    (Cube)    │
                      └──────────────┘
```

**Implementation:**
```python
# Location: cube/operator/cube_operator.py

class Operator:
    def __init__(self, cube: Cube, ...):
        self._cube = cube
        self._history: list[Alg] = []

    def play(self, alg: Alg, inv: bool = False):
        alg.play(self._cube, inv)
        self._history.append(alg if not inv else alg.inv())

    def undo(self) -> Alg | None:
        if self._history:
            alg = self._history.pop()
            alg.inv().play(self._cube, False)
            return alg
```

**Benefits:**
- ✅ Undo is trivial (execute inverse)
- ✅ History tracking built-in
- ✅ Recording macros is natural

### 4. Observer Pattern (Animation)

**Intent:** Notify window when animation updates are needed

**Structure:**
```
┌──────────────────┐      observes     ┌─────────────┐
│ AnimationManager │◄──────────────────│   Window    │
│                  │                    │ (Observer)  │
│ + notify()       │─────notifies──────>│ + update()  │
└──────────────────┘                    │ + draw()    │
                                        └─────────────┘
```

**Implementation:**
```python
# Location: cube/animation/animation_manager.py

class AnimationManager:
    def run_animation(self, cube, op, alg):
        # Create animation with callbacks
        def update_callback():
            self._window.update_gui_elements()
            return animation_complete

        def draw_callback():
            # Draw animation frame
            pass

        animation = Animation(update_callback, draw_callback)
        self._current_animation = animation
```

**Benefits:**
- ✅ Decouples animation from cube logic
- ✅ Window doesn't need to poll for changes
- ✅ Clean integration with Pyglet event loop

### 5. Facade Pattern (App)

**Intent:** Provide simplified interface to complex subsystem

**Structure:**
```
┌────────────────────────────────────────┐
│          App (Facade)                  │
│                                        │
│  + cube: Cube                          │
│  + op: Operator                        │
│  + slv: Solver                         │
│  + am: AnimationManager                │
│  + vs: ApplicationAndViewState         │
└────────────┬───────────────────────────┘
             │ simplifies access to
             ▼
┌────────────────────────────────────────┐
│      Complex Subsystems                │
│  ┌──────┐ ┌────────┐ ┌──────────────┐ │
│  │ Cube │ │Operator│ │    Solver    │ │
│  └──────┘ └────────┘ └──────────────┘ │
└────────────────────────────────────────┘
```

**Implementation:**
```python
# Location: cube/app/app.py

class _App(AbstractApp):
    def __init__(self, vs, am, cube_size):
        self._cube = Cube(cube_size)
        self._op = Operator(self._cube, vs, am, ...)
        self._slv = Solvers.default(self._op)
        self._am = am
        self._vs = vs

    # Facade methods
    @property
    def cube(self) -> Cube:
        return self._cube

    @property
    def op(self) -> Operator:
        return self._op
```

**Benefits:**
- ✅ Single initialization point
- ✅ Hides wiring complexity
- ✅ Provides cohesive interface

### 6. Template Method Pattern (BaseSolver)

**Intent:** Define skeleton of algorithm, let subclasses override steps

**Structure:**
```
┌────────────────────────────────────┐
│   SolverElementsProvider (Proto)   │
│  + op: OperatorProtocol            │
│  + cube: Cube                      │
│  + cmn: CommonOp                   │
│  + debug(*args): None              │
└────────────▲───────────────────────┘
             │ implements
    ┌────────┴─────────┐
    │                  │
┌───┴──────────────┐ ┌─┴──────────────┐
│   BaseSolver     │ │ AbstractReducer│
│ (3x3 solvers)    │ │ (NxN reducers) │
└───────▲──────────┘ └───────▲────────┘
        │                    │
   ┌────┴────┐          ┌────┴────┐
   │         │          │         │
Beginner   CFOP    BeginnerReducer
```

**Implementation:**
```python
# Location: cube/solver/common/base_solver.py

class BaseSolver(SolverElementsProvider, ABC):
    def solution(self):
        """Template method"""
        with self._op.save_history():
            self.solve(debug=False, animation=False)  # Hook
            # Extract solution from history
        return solution_alg

    @abstractmethod
    def solve(self, ...):
        """Hook method - implemented by subclasses"""
        pass
```

**Benefits:**
- ✅ Common functionality in base class
- ✅ Subclasses only override what's needed
- ✅ Enforces structure
- ✅ Both solvers and reducers can use SolverHelper subclasses

### 7. Flyweight Pattern (Part IDs)

**Intent:** Share intrinsic state to reduce memory usage

**Structure:**
```
┌─────────────────────────────────┐
│           Part                  │
│  _fixed_id: frozenset (shared)  │
│  all_slices: list (unique)      │
└─────────────────────────────────┘
```

**Implementation:**
```python
# Location: cube/model/Part.py

class Part(ABC):
    def finish_init(self):
        # Create immutable ID (Flyweight)
        _id = frozenset(s.fixed_id for s in self.all_slices)
        self._fixed_id = _id

    @property
    def fixed_id(self) -> PartFixedID:
        return self._fixed_id  # Shared across instances
```

**Benefits:**
- ✅ Parts identified by immutable IDs
- ✅ IDs don't change when colors rotate
- ✅ Memory efficient (frozensets are interned)

---

## Data Flow

### User Input → Cube Rotation

```
┌──────────────────────────────────────────────────────┐
│ 1. User presses 'R' key                              │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ 2. Window.on_key_press(key.R)                        │
│    └─> handle_keyboard_input(window, key.R, mods)   │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ 3. Identify algorithm: Algs.R                        │
│    └─> Apply slicing if needed: R[1:3]              │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ 4. app.op.play(Algs.R, inv=False, animation=True)   │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ 5. Operator._play()                                  │
│    ├─> Flatten: SeqAlg → [SimpleAlg, ...]           │
│    └─> For each SimpleAlg:                           │
│        ├─> IF animation enabled:                     │
│        │   └─> AnimationManager.run_animation()      │
│        │       ├─> Animate geometry rotation         │
│        │       ├─> Window.update_gui_elements()      │
│        │       └─> Window.draw()                     │
│        │                                              │
│        └─> SimpleAlg.play(cube, inv=False)           │
│            └─> Cube.rotate_face_and_slice()          │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ 6. Update cube model                                 │
│    ├─> Rotate part colors in place                  │
│    ├─> Increment modify counter                     │
│    └─> Add to history                                │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ 7. Window.on_draw() [Pyglet event]                  │
│    ├─> Check if cube modified                       │
│    ├─> Viewer.update() [regenerate geometry]        │
│    └─> Viewer.draw() [render batch]                 │
└──────────────────────────────────────────────────────┘
```

### Solving Flow

```
┌──────────────────────────────────────────────────────┐
│ 1. User presses '/' (solve key)                      │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ 2. Window.on_key_press(key.SLASH)                    │
│    └─> app.slv.solve(what=SolveStep.ALL)            │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ 3. BeginnerSolver.solve()                            │
│    ├─> For each stage:                               │
│    │   ├─> Analyze cube state                        │
│    │   ├─> Generate solving algorithm                │
│    │   └─> app.op.play(solving_alg)                  │
│    │                                                  │
│    ├─> L1Cross.solve()                               │
│    ├─> L1Corners.solve()                             │
│    ├─> L2.solve()                                    │
│    ├─> L3Cross.solve()                               │
│    └─> L3Corners.solve()                             │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ 4. Each stage uses Operator to execute moves         │
│    └─> Animations play if enabled                    │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ 5. Return SolverResults                              │
│    └─> Contains parity error flags                   │
└──────────────────────────────────────────────────────┘
```

### Animation Detailed Flow

```
┌──────────────────────────────────────────────────────┐
│ AnimationManager.run_animation(cube, op, alg)        │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ _op_and_play_animation(window, cube, ...)           │
│                                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │ Setup Phase                                  │   │
│ │ ├─> Get animation objects from alg           │   │
│ │ ├─> face_name, parts_to_animate             │   │
│ │ ├─> Get geometry from viewer                │   │
│ │ └─> Calculate rotation axis & increments    │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │ Animation Loop                               │   │
│ │ For each frame:                              │   │
│ │   ├─> Increment rotation angle               │   │
│ │   ├─> Update viewer geometry (rotate)        │   │
│ │   ├─> window.update_gui_elements()           │   │
│ │   │   └─> viewer.update()                    │   │
│ │   ├─> window.on_draw()                       │   │
│ │   │   └─> viewer.draw() [OpenGL]            │   │
│ │   └─> sleep(animation_delay)                 │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │ Completion Phase                             │   │
│ │ ├─> op.play(alg, animation=False)            │   │
│ │ │   └─> Update cube model (logical state)   │   │
│ │ └─> Cleanup animation state                  │   │
│ └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Algorithm Representation: Composite Objects

**Decision:** Algorithms are objects forming a tree structure (Composite pattern)

**Rationale:**
- Supports both simple (R, U) and complex ((R U R') * 3) moves uniformly
- Enables algebraic manipulation (simplification, inversion)
- Allows animation of individual steps
- Type-safe (compile-time checking)

**Alternative Considered:** String-based notation (e.g., "R U R' U'")
- ❌ No type safety
- ❌ Harder to compose programmatically
- ❌ No algebraic operations

**Trade-off:** More complex implementation, but far more powerful and maintainable.

### 2. Cube Model: Shared Part Edges

**Decision:** Adjacent faces share `PartEdge` objects

**Example:**
```python
# Front-right edge is same object as right-left edge
f._edge_right = r._edge_left = _create_edge(edges, f, r, True)
```

**Rationale:**
- Single source of truth for each edge color
- Color changes automatically visible from both faces
- Rotations naturally update all affected parts
- No need to synchronize colors between faces

**Trade-off:** Complex initialization logic, but elegant manipulation.

### 3. Animation: Separate from Model Updates

**Decision:** Animation modifies viewer geometry, not cube model. Cube model updates only at animation end.

**Rationale:**
- Clean separation of concerns
- Cube model stays consistent (always valid state)
- Animation can be skipped without affecting logic
- Easier to test (model logic independent of animation)

**Animation Flow:**
```
┌────────────┐    ┌──────────────┐    ┌────────────┐
│   Start    │ -> │   Animate    │ -> │   Apply    │
│   State    │    │   Geometry   │    │  To Model  │
│  (Cube)    │    │  (Viewer)    │    │   (Cube)   │
└────────────┘    └──────────────┘    └────────────┘
  Consistent        Visual only         Consistent
```

**Trade-off:** More complex animation code, but better separation.

### 4. Undo via Inverse Execution

**Decision:** Undo executes algorithm inverse rather than storing cube snapshots (Memento pattern)

**Rationale:**
- Algorithms are inherently reversible (R' undoes R)
- No need to snapshot entire cube state (memory efficient)
- History is compact (just algorithm list)
- Can generate solution by inverting/reversing history

**Alternative Considered:** Memento pattern (store cube snapshots)
- ❌ Memory intensive (O(n) space per operation)
- ❌ Slower for large cubes (copying state)

**Trade-off:** Undo is slower (executes moves), but memory efficient and simpler.

### 5. NxN Support via Reduction

**Decision:** Larger cubes (4x4, 5x5) reduced to 3x3 via `NxNCenters` and `NxNEdges` solvers

**Process:**
```
NxN Cube
  ↓
Solve Centers (NxNCenters)
  ↓
Solve Edges (NxNEdges)
  ↓
Now looks like 3x3
  ↓
Use 3x3 solver (LBL or CFOP)
```

**Rationale:**
- Reuses 3x3 solving logic
- Centers and edges can be solved independently
- Handles parity errors (special cases for even cubes)
- Conceptually simple

**Alternative Considered:** Dedicated solvers for each size
- ❌ More code duplication
- ❌ Harder to maintain

**Trade-off:** Not the fastest for larger cubes, but maintainable and extensible.

### 6. Operator as Mediator

**Decision:** Operator mediates between Algorithms and Cube (doesn't let algorithms directly modify cube)

**Structure:**
```
Window ──> Operator ──> Algorithm ──> Cube
                ├─> History
                ├─> Recording
                └─> Animation
```

**Rationale:**
- Single point to add cross-cutting concerns (history, recording, animation)
- Algorithms stay pure (no side effects beyond cube modification)
- Easier to add features (e.g., move validation, logging)

**Trade-off:** Extra layer of indirection, but cleaner architecture.

### 7. Fixed Part IDs

**Decision:** Parts have immutable `fixed_id` that doesn't change when colors rotate

**Example:**
```python
# Part ID is frozenset of edge identifiers
edge.fixed_id = frozenset([edge_id_1, edge_id_2])
# This never changes, even when colors rotate
```

**Rationale:**
- Track physical pieces independent of color
- Essential for solver algorithms (know where pieces are)
- Simplifies part identification

**Trade-off:** More complex initialization, but essential for solving.

---

## Extension Points

### How to Add a New Solver Algorithm

**Example:** Adding Roux method solver

**Steps:**

1. **Create solver class** in `cube/solver/roux/roux.py`:
```python
from cube.solver.common.base_solver import BaseSolver
from cube.solver.solver import Solver, SolveStep, SolverResults

class RouxSolver(BaseSolver):
    def __init__(self, op: Operator):
        super().__init__(op)

    def solve(self, debug=None, animation=None, what=SolveStep.ALL):
        # Roux stages:
        # 1. First block (FB)
        # 2. Second block (SB)
        # 3. CMLL (corners of last layer)
        # 4. LSE (last six edges)

        self._solve_first_block()
        self._solve_second_block()
        self._solve_cmll()
        self._solve_lse()

        return SolverResults()

    def _solve_first_block(self):
        # Implementation...
        pass
```

2. **Register in factory** (`cube/solver/solvers.py`):
```python
class SolverName(Enum):
    LBL = "LBL"
    CFOP = "CFOP"
    ROUX = "ROUX"  # Add new enum

class Solvers:
    @staticmethod
    def by_name(name: SolverName, op: Operator) -> Solver:
        match name:
            case SolverName.LBL:
                return BeginnerSolver(op)
            case SolverName.CFOP:
                return CFOP(op)
            case SolverName.ROUX:
                return RouxSolver(op)  # Add case
```

3. **That's it!** The rest works automatically:
   - Solver switching (backslash key)
   - Animation integration
   - History tracking
   - Testing framework

### How to Add New Cube Notation

**Example:** Adding Singmaster notation parser

**Option A: String Parser**

Create in `cube/algs/_parser.py`:
```python
def parse_singmaster(notation: str) -> Alg:
    """Parse Singmaster notation: R U R' U'"""
    tokens = notation.split()
    algs = []
    for token in tokens:
        if token.endswith("'"):
            algs.append(get_move(token[:-1]).prime)
        elif token.endswith("2"):
            algs.append(get_move(token[:-1]) * 2)
        else:
            algs.append(get_move(token))
    return SeqAlg(*algs)
```

**Option B: New Algorithm Type**

```python
class SingmasterNotationAlg(Alg):
    def __init__(self, notation: str):
        self._notation = notation
        self._parsed = parse_singmaster(notation)

    def play(self, cube: Cube, inv: bool = False):
        self._parsed.play(cube, inv)

    def flatten(self):
        return self._parsed.flatten()
```

**Integration:** Operator doesn't care about algorithm type, just calls `play()`.

### How to Change Rendering

**Example:** Using Vulkan instead of OpenGL

**Steps:**

1. **Implement `AnimationWindow` protocol**:
```python
from cube.animation.animation_manager import AnimationWindow

class VulkanWindow(AnimationWindow):
    def __init__(self, app, width, height):
        self._app = app
        self._vulkan_viewer = VulkanCubeViewer(app.cube)

    @property
    def viewer(self) -> CubeViewer:
        return self._vulkan_viewer

    def update_gui_elements(self):
        # Update Vulkan buffers
        pass

    def on_draw(self):
        # Render with Vulkan
        pass
```

2. **Replace in entry point** (`main_g.py`):
```python
def main():
    app = _App(...)
    window = VulkanWindow(app, 800, 600)  # Instead of Window
    # Rest unchanged
```

**No changes needed** in:
- Cube model
- Solver logic
- Operator
- Animation manager (uses protocol)

### How to Add Custom Algorithm Macros

**Example:** Adding custom combo moves

```python
# In cube/algs/Algs.py

class Algs:
    # ... existing moves ...

    # Custom algorithms
    @staticmethod
    def sexy_move() -> Alg:
        """R U R' U'"""
        return R + U + R.prime + U.prime

    @staticmethod
    def t_perm() -> Alg:
        """T permutation"""
        return (R + U + R.prime + U.prime + R.prime + F +
                R*2 + U.prime + R.prime + U.prime + R + U +
                R.prime + F.prime)

    @staticmethod
    def sune() -> Alg:
        """Sune OLL algorithm"""
        return R + U + R.prime + U + R + U*2 + R.prime
```

**Usage:**
```python
op.play(Algs.sexy_move() * 6)  # Repeat 6 times
op.play(Algs.t_perm())          # Execute T-perm
```

---

## Strengths and Improvements

### Architectural Strengths

#### 1. ✅ Excellent Separation of Concerns

```
Model     ─ Pure domain logic, no UI dependencies
Algorithms ─ Self-contained, composable, testable
Operator  ─ Clean mediator with single responsibility
Solver    ─ Pluggable strategies independent of model
Viewer    ─ Completely decoupled from business logic
```

#### 2. ✅ Strong Abstraction Boundaries

- Extensive use of Abstract Base Classes (ABC)
- Protocol types for loose coupling (`AnimationWindow`, `OpProtocol`)
- Type hints throughout (Python 3.10+ features)

#### 3. ✅ Domain-Driven Design

- **Ubiquitous Language:** Face names (F/B/L/R/U/D), part types (Edge, Corner, Center)
- **Value Objects:** `PartColorsID`, `FaceName` (immutable)
- **Entities:** `Cube`, `Part` with identity
- **Aggregates:** `Cube` is root aggregate

#### 4. ✅ Extensibility

Easy to add:
- New solving algorithms (implement `Solver`)
- New algorithms (extend `Alg`)
- New views (implement `AnimationWindow`)
- New cube sizes (already supported generically)

#### 5. ✅ Algebraic Algorithm System

```python
# Composable
alg = R + U + R.prime

# Invertible
alg_inv = -alg

# Repeatable
alg = (R + U + R.prime + U.prime) * 6

# Sliceable
alg = R[1:3]  # Specific layers
```

#### 6. ✅ Testing Support

- Built-in testing framework (`_app_tests.py`)
- Scramble generation
- Solution verification
- Parity error detection

### Areas for Improvement

#### 1. ⚠️ Circular Dependencies

**Issue:** Some imports use `TYPE_CHECKING` guards

```python
if TYPE_CHECKING:
    from cube.operator.op_annotation import OpAnnotation
```

**Recommendation:** Apply Dependency Inversion Principle
- Create abstract interface for annotations
- Have both Operator and OpAnnotation depend on interface

#### 2. ⚠️ Global Configuration State

**Issue:** `config.CHECK_CUBE_SANITY`, `config.SOLVER_DEBUG` are global mutable state

**Problems:**
- Hard to test with different configurations
- Hidden dependencies
- Not thread-safe

**Recommendation:**
```python
# Instead of global config
@dataclass(frozen=True)
class AppConfig:
    cube_size: int = 3
    solver_debug: bool = False
    check_sanity: bool = True
    animation_enabled: bool = True

# Inject via constructor
class _App:
    def __init__(self, config: AppConfig, ...):
        self._config = config
```

#### 3. ⚠️ Animation Manager Bidirectional Dependency

**Issue:** Window and AnimationManager have circular dependency

```python
# Workaround in Window.py
if self._animation_manager:
    self._animation_manager.set_window(self)  # Patch!
```

**Recommendation:**
- Pass window as parameter to `run_animation()`
- Or use event bus/mediator
- Or invert: Window depends on AnimationManager, not vice versa

#### 4. ⚠️ Operator Complexity

**Responsibilities:**
1. Execute algorithms ✓
2. Manage history/undo ✓
3. Control animation ✓
4. Handle recording ✓
5. Abort signaling ✓
6. Logging ✓

**Recommendation:** Apply Single Responsibility Principle
```python
# Split into:
AlgorithmExecutor     # Execute on cube
HistoryManager        # Track and undo
AnimationCoordinator  # Delegate to AnimationManager
OperationRecorder     # Macro recording
```

#### 5. ⚠️ Type Safety

Some areas use `Any`:
```python
def play(self, alg: Alg, inv: Any = False, animation: Any = True)
#                            ^^^                      ^^^
```

**Recommendation:** Use proper types (`bool`)

#### 6. ⚠️ Error Handling Strategy

Inconsistent exception handling:
```python
# Some places
except:
    return False
```

**Recommendation:**
- Define exception hierarchy
- Avoid bare `except:`
- Log exceptions appropriately
- Consider Result/Either types

#### 7. ⚠️ Model Mutation Tracking

Relies on manual `modified()` calls:
```python
def rotate_face_and_slice(self, ...):
    # ... modify state ...
    self.modified()  # Easy to forget!
```

**Recommendation:**
- Use property setters to auto-track
- Or immutable data structures (copy-on-write)
- Or event sourcing

### Summary Assessment

| Aspect | Score | Notes |
|--------|-------|-------|
| **Architecture** | 8.5/10 | Clean layered design, minor coupling issues |
| **Maintainability** | 8/10 | Well-organized, some complex areas |
| **Extensibility** | 9/10 | Easy to add solvers/algorithms |
| **Testability** | 7/10 | Good test support, some global state |
| **Performance** | 6/10 | Not optimized, but adequate for purpose |
| **Documentation** | 7/10 | Good code structure, needs more docs |

**Overall: Strong Architecture** - This is a mature, well-architected codebase demonstrating professional software engineering practices.

---

## File Structure Reference

### Complete Directory Tree

```
cubesolve/
├── main_g.py                          # Entry point
│
├── cube/
│   ├── algs/                          # Algorithm layer (18 files)
│   │   ├── __init__.py
│   │   ├── Alg.py                     # Abstract base
│   │   ├── SimpleAlg.py               # Atomic moves
│   │   ├── FaceAlg.py                 # R, L, U, D, F, B
│   │   ├── SliceAlg.py                # M, E, S
│   │   ├── WholeCubeAlg.py            # x, y, z
│   │   ├── SeqAlg.py                  # Sequences (Composite)
│   │   ├── Inv.py                     # Inverse (Decorator)
│   │   ├── Mul.py                     # Multiplication (Decorator)
│   │   ├── DoubleLayerAlg.py          # Wide moves (Rw, Lw, etc.)
│   │   ├── Algs.py                    # Pre-defined algorithms
│   │   ├── SliceAbleAlg.py            # Slicing support
│   │   ├── AnimationAbleAlg.py        # Animation interface
│   │   ├── AnnoationAlg.py            # Annotation support
│   │   ├── optimizer.py               # Simplification logic
│   │   ├── _parser.py                 # Algorithm parsing
│   │   └── _internal_utils.py         # Utilities
│   │
│   ├── model/                         # Model layer (20 files)
│   │   ├── __init__.py
│   │   ├── cube.py                    # Main Cube class
│   │   ├── cube_face.py               # Face representation
│   │   ├── cube_slice.py              # Slice representation
│   │   ├── cube_queries2.py           # Cube queries
│   │   ├── cube_sanity.py             # Validation
│   │   ├── cube_boy.py                # FaceName enum
│   │   ├── Part.py                    # Part abstract base
│   │   ├── Edge.py                    # Edge pieces
│   │   ├── Corner.py                  # Corner pieces
│   │   ├── Center.py                  # Center pieces
│   │   ├── _part.py                   # Part implementation
│   │   ├── _PartEdge.py               # Part edge
│   │   ├── _part_slice.py             # Part slicing
│   │   ├── _elements.py               # Element types
│   │   ├── _super_element.py          # Super element
│   │   └── misc.py                    # Utilities
│   │
│   ├── operator/                      # Operator layer (2 files)
│   │   ├── __init__.py
│   │   ├── cube_operator.py           # Main operator
│   │   └── op_annotation.py           # Annotations
│   │
│   ├── solver/                        # Solver layer (25 files)
│   │   ├── __init__.py
│   │   ├── solver.py                  # Solver interface
│   │   ├── solvers.py                 # Solver factory
│   │   ├── solver_name.py             # Solver enum
│   │   │
│   │   ├── common/                    # Common solver code
│   │   │   ├── __init__.py
│   │   │   ├── base_solver.py         # Base class
│   │   │   ├── common_op.py           # Common operations
│   │   │   ├── solver_element.py      # Solver elements
│   │   │   ├── tracker.py             # State tracking
│   │   │   ├── face_tracker.py        # Face tracking
│   │   │   └── advanced_even_oll_big_cube_parity.py
│   │   │
│   │   ├── begginer/                  # Layer-by-layer solver
│   │   │   ├── __init__.py
│   │   │   ├── beginner_solver.py     # Main solver
│   │   │   ├── l1_cross.py            # L1 cross
│   │   │   ├── l1_corners.py          # L1 corners
│   │   │   ├── l2.py                  # L2 edges
│   │   │   ├── l3_cross.py            # L3 cross
│   │   │   ├── l3_corners.py          # L3 corners
│   │   │   ├── nxn_centers.py         # Big cube centers
│   │   │   ├── nxn_edges.py           # Big cube edges
│   │   │   └── _nxn_centers_face_tracker.py
│   │   │
│   │   └── CFOP/                      # CFOP solver
│   │       ├── __init__.py
│   │       ├── cfop.py                # Main solver
│   │       ├── f2l.py                 # First two layers
│   │       ├── OLL.py                 # Orient last layer
│   │       └── PLL.py                 # Permute last layer
│   │
│   ├── viewer/                        # Viewer layer (10 files)
│   │   ├── __init__.py
│   │   ├── viewer_g.py                # Main viewer
│   │   ├── viewer_g_ext.py            # Viewer extensions
│   │   ├── viewer_markers.py          # Debug markers
│   │   ├── _board.py                  # Board manager
│   │   ├── _faceboard.py              # Face rendering
│   │   ├── _cell.py                   # Cell rendering
│   │   ├── gl_helper.py               # OpenGL utilities
│   │   ├── graphic_helper.py          # Graphics helpers
│   │   └── res/                       # Resources
│   │       └── __init__.py
│   │
│   ├── animation/                     # Animation layer (2 files)
│   │   ├── __init__.py
│   │   ├── animation_manager.py       # Animation orchestration
│   │   └── main_g_animation_text.py   # Animation text
│   │
│   ├── app/                           # Application layer (6 files)
│   │   ├── __init__.py
│   │   ├── abstract_ap.py             # App interface
│   │   ├── app.py                     # App implementation
│   │   ├── app_state.py               # State management
│   │   ├── app_exceptions.py          # Custom exceptions
│   │   └── _app_tests.py              # Testing framework
│   │
│   ├── main_window/                   # Window layer (3 files)
│   │   ├── __init__.py
│   │   ├── Window.py                  # Main window
│   │   ├── main_g_abstract.py         # Abstract window
│   │   ├── main_g_keyboard_input.py   # Keyboard handling
│   │   └── main_g_mouse.py            # Mouse handling
│   │
│   ├── main_console/                  # Console interface (2 files)
│   │   ├── __init__.py
│   │   └── viewer.py                  # Console viewer
│   │
│   ├── config/                        # Configuration (1 file)
│   │   ├── __init__.py
│   │   └── config.py                  # Global config
│   │
│   ├── utils/                         # Utilities (4 files)
│   │   ├── __init__.py
│   │   ├── prof.py                    # Profiling
│   │   └── geometry.py                # Geometry utilities
│   │
│   ├── ai/                            # AI (minimal)
│   │   └── __init__.py
│   │
│   └── tests/                         # Tests (8 files)
│       ├── __init__.py
│       └── test_perf.py               # Performance tests
│
├── __try/                             # Experimental code
│
├── _archive/                          # Archived code
│
├── .claude/                           # Claude Code config
│   ├── settings.local.json
│   ├── claude.md
│   └── agents/
│       └── code-guide.md
│
├── README.md                          # User documentation
├── arch.md                            # This file
└── requirements.txt                   # Dependencies
```

### File Statistics

```
Total Lines of Code: ~13,143

By Component:
├── algs/        ~2,500 lines  (19%)
├── model/       ~3,000 lines  (23%)
├── solver/      ~4,000 lines  (30%)
├── viewer/      ~1,500 lines  (11%)
├── animation/     ~300 lines   (2%)
├── operator/      ~400 lines   (3%)
├── app/           ~500 lines   (4%)
├── main_window/   ~800 lines   (6%)
└── other/         ~143 lines   (1%)
```

### Key File Locations

| Component | Main File | Description |
|-----------|-----------|-------------|
| Entry Point | `main_g.py` | Application entry point |
| Model | `cube/model/cube.py` | Cube representation |
| Algorithms | `cube/algs/Alg.py` | Algorithm interface |
| Algorithms | `cube/algs/Algs.py` | Pre-defined algorithms |
| Operator | `cube/operator/cube_operator.py` | Execution engine |
| Solver | `cube/solver/solver.py` | Solver interface |
| Beginner Solver | `cube/solver/begginer/beginner_solver.py` | LBL solver |
| CFOP Solver | `cube/solver/CFOP/cfop.py` | CFOP solver |
| Viewer | `cube/viewer/viewer_g.py` | OpenGL viewer |
| Animation | `cube/animation/animation_manager.py` | Animation system |
| App | `cube/app/app.py` | Application facade |
| Window | `cube/main_window/Window.py` | Pyglet window |
| Keyboard | `cube/main_window/main_g_keyboard_input.py` | Input handling |
| Config | `cube/config/config.py` | Configuration |

---

## Appendix: Class Diagram

### Core Classes Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                          Window                                 │
│  + on_key_press()                                               │
│  + on_mouse_press()                                             │
│  + on_draw()                                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │ owns
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                          App                                    │
│  + cube: Cube                                                   │
│  + op: Operator                                                 │
│  + slv: Solver                                                  │
│  + am: AnimationManager                                         │
│  + vs: ApplicationAndViewState                                  │
└──┬──────────┬──────────┬──────────┬──────────┬─────────────────┘
   │          │          │          │          │
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌─────┐  ┌────────┐  ┌─────┐  ┌─────┐  ┌────────────────┐
│Cube │  │Operator│  │Solver│  │Viewer│  │AnimationManager│
└──┬──┘  └───┬────┘  └──┬──┘  └──┬──┘  └────────┬───────┘
   │         │          │        │              │
   │         │          │        │              │
   ▼         ▼          ▼        ▼              ▼
┌─────┐  ┌─────┐   ┌────────┐ ┌──────┐  ┌──────────┐
│Face │  │ Alg │   │ Common │ │_Board│  │Animation │
│Edge │  │     │   │   Op   │ │      │  └──────────┘
│Corner│ │     │   └────────┘ └──────┘
│Center│ │     │
└─────┘  └─────┘
```

---

**Document Version:** 1.0
**Last Updated:** 2025-01-21
**Total Pages:** Architecture documentation complete

---

