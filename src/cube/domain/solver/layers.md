# Solver Package Layer Architecture

## Overview

The solver package follows a strict 4-layer architecture to ensure clean dependencies
and prevent circular imports. Solvers are isolated from each other.

## Package Structure

```
solver/
├── protocols/              # Layer 1: Interfaces
├── common/                 # Layer 2: Shared utilities
│   └── big_cube/           # Layer 2: Big cube (NxN) helpers
├── _3x3/                   # Layer 3a: 3x3 solvers
│   ├── shared/             # Shared 3x3 components
│   ├── beginner/           # Beginner layer-by-layer method
│   ├── cfop/               # CFOP (Fridrich) method
│   └── kociemba/           # Kociemba two-phase algorithm
├── reducers/               # Layer 3b: NxN reducers
│   └── beginner/           # Beginner reduction method
├── direct/                 # Layer 3c: Direct NxN solvers
│   ├── cage/               # Cage solver method
│   └── commutator/         # Commutator-based method
└── [factories]             # Layer 4: Root level factories
    ├── Solvers.py
    ├── Solvers3x3.py
    ├── Reducers.py
    └── NxNSolverOrchestrator.py
```

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: Factories & Orchestrators                              │
│   • Solvers.py                                                  │
│   • Solvers3x3.py                                               │
│   • Reducers.py                                                 │
│   • NxNSolverOrchestrator.py                                    │
│   Can import: All layers                                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    ▼                      ▼                      ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────────┐
│ Layer 3a:      │  │ Layer 3b:      │  │ Layer 3c:          │
│ _3x3/          │  │ reducers/      │  │ direct/            │
│                │  │                │  │                    │
│ beginner/      │  │ beginner/      │  │ cage/              │
│ cfop/          │  │   Beginner-    │  │   CageNxNSolver    │
│ kociemba/      │  │   Reducer.py   │  │                    │
│ shared/        │  │                │  │ commutator/        │
│   L1Cross      │  │                │  │   CommutatorNxN    │
│                │  │                │  │   Solver           │
│                │  │                │  │                    │
│ CANNOT import  │  │ CANNOT import  │  │ CANNOT import      │
│ reducers/,     │  │ _3x3/, direct/ │  │ _3x3/, reducers/   │
│ direct/        │  │                │  │                    │
└───────┬────────┘  └───────┬────────┘  └─────────┬──────────┘
        │                   │                     │
        └───────────────────┼─────────────────────┘
                            ▼
        ┌───────────────────────────────────────────┐
        │ Layer 2: common/                          │
        │   • BaseSolver, AbstractSolver            │
        │   • SolverElement                         │
        │   • CommonOp, Tracker, FaceTracker        │
        │   • big_cube/                             │
        │       NxNCenters, NxNEdges, NxNCorners    │
        │       FaceTrackerHolder                   │
        │       _NxNCentersFaceTracker (private)    │
        │       _NxNCentersHelper (private)         │
        │   Can import: Layer 1 only                │
        └───────────────────┬───────────────────────┘
                            ▼
        ┌───────────────────────────────────────────┐
        │ Layer 1: protocols/                       │
        │   • ReducerProtocol                       │
        │   • Solver3x3Protocol                     │
        │   • SolverElementsProvider                │
        │   • OperatorProtocol                      │
        │   • AnnotationProtocol                    │
        │   Can import: Nothing (base layer)        │
        └───────────────────────────────────────────┘
```

## Layer Rules

| Layer | Packages | Can Import From | Cannot Import From |
|-------|----------|-----------------|-------------------|
| 4 | Root factories (`Solvers`, `Reducers`, etc.) | All layers | - |
| 3a | `_3x3/` | Layers 1-2 | `reducers/`, `direct/` |
| 3b | `reducers/` | Layers 1-2 | `_3x3/`, `direct/` |
| 3c | `direct/` | Layers 1-2 | `_3x3/`, `reducers/` |
| 2 | `common/` | Layer 1 | All Layer 3, Layer 4 |
| 1 | `protocols/` | Nothing | Everything |

## Key Principle: Solver Isolation

**Rule: Solver packages CANNOT import from other solver packages.**

This means:
- `_3x3/beginner/` cannot import from `_3x3/cfop/`
- `reducers/beginner/` cannot import from `_3x3/beginner/`
- `direct/cage/` cannot import from `reducers/`

Shared code must live in `common/` or `_3x3/shared/`.

## Package Details

### Layer 1: protocols/

Protocol definitions (interfaces) that define contracts between components:
- `ReducerProtocol` - Interface for NxN reducers
- `Solver3x3Protocol` - Interface for 3x3 solvers
- `SolverElementsProvider` - Interface for solving step providers
- `OperatorProtocol` - Interface for cube manipulation operations
- `AnnotationProtocol` - Interface for solve annotations

### Layer 2: common/

Shared utilities and base classes:
- `BaseSolver` - Base class for all solvers
- `AbstractSolver` - Abstract solver with common functionality
- `SolverElement` - Building block for solver algorithms
- `CommonOp` - Common cube operations
- `Tracker`, `FaceTracker` - State tracking utilities

#### common/big_cube/

Big cube (NxN) solving utilities shared by reducers and direct solvers:
- `NxNCenters` - Center piece solving for NxN cubes
- `NxNEdges` - Edge pairing for NxN cubes
- `NxNCorners` - Corner parity fix for even NxN cubes
- `FaceTrackerHolder` - Container for face trackers

Private implementation details (prefixed with `_`):
- `_NxNCentersHelper` - Helper methods for center solving
- `_NxNCentersFaceTracker` - Face tracking for center solving

### Layer 3a: _3x3/

Pure 3x3 solving algorithms (work on actual 3x3 or reduced cubes):

#### _3x3/shared/

Components shared between multiple 3x3 solvers:
- `L1Cross` - Layer 1 cross (used by beginner and CFOP)

#### _3x3/beginner/

Beginner layer-by-layer method:
- `BeginnerSolver3x3` - Main solver class

Private implementation details (prefixed with `_`):
- `_L1Corners`, `_L2`, `_L3Cross`, `_L3Corners` - Layer-specific solvers

#### _3x3/cfop/

CFOP (Fridrich) method:
- `CFOP3x3` - Main solver class

Private implementation details (prefixed with `_`):
- `_F2L`, `_OLL`, `_PLL` - Method-specific solvers

#### _3x3/kociemba/

Kociemba two-phase algorithm:
- `Kociemba3x3` - Near-optimal 3x3 solver

### Layer 3b: reducers/

NxN to 3x3 reducers:

#### reducers/beginner/

Standard reduction method:
- `BeginnerReducer` - Reduces NxN to 3x3 using centers + edge pairing

### Layer 3c: direct/

Direct NxN solvers (no 3x3 reduction):

#### direct/cage/

- `CageNxNSolver` - Cage-based solving method

#### direct/commutator/

- `CommutatorNxNSolver` - Commutator-based solving

### Layer 4: Root Factories

Factory classes that wire together components:
- `Solvers` - Main solver factory
- `Solvers3x3` - Factory for 3x3 solvers only
- `Reducers` - Factory for NxN reducers
- `NxNSolverOrchestrator` - Orchestrates reduction + 3x3 solving

## Usage Examples

### Creating a 3x3 Solver

```python
from cube.domain.solver.Solvers3x3 import Solvers3x3

# Beginner method
solver = Solvers3x3.beginner(op)

# CFOP method
solver = Solvers3x3.cfop(op)

# Kociemba (near-optimal)
solver = Solvers3x3.kociemba(op)
```

### Creating an NxN Reducer

```python
from cube.domain.solver.Reducers import Reducers

# Default reducer
reducer = Reducers.default(op)

# Beginner reducer with advanced parity
reducer = Reducers.beginner(op, advanced_edge_parity=True)
```

### Using Big Cube Utilities

```python
from cube.domain.solver.common.big_cube import (
    NxNCenters,
    NxNEdges,
    FaceTrackerHolder
)

# These are used by reducers and direct solvers
centers = NxNCenters(op, face_tracker_holder)
edges = NxNEdges(op)
```

## File Naming Convention

Private implementation files are prefixed with `_` following Python convention:
- Files starting with `_` are internal implementation details
- They should not be imported directly from outside their package
- Only public API classes are exported from `__init__.py`

Examples:
- `common/big_cube/_NxNCentersHelper.py` - internal helper
- `_3x3/beginner/_L1Corners.py` - internal solver component

## Migration Notes

The package was restructured in December 2024 to enforce layer isolation:

| Old Location | New Location |
|--------------|--------------|
| `beginner/NxNCenters.py` | `common/big_cube/NxNCenters.py` |
| `beginner/NxNEdges.py` | `common/big_cube/NxNEdges.py` |
| `beginner/FaceTrackerHolder.py` | `common/big_cube/FaceTrackerHolder.py` |
| `beginner/L1Cross.py` | `_3x3/shared/L1Cross.py` |
| `beginner/L3Corners.py` | `_3x3/beginner/_L3Corners.py` |
| `beginner/BeginnerSolver3x3.py` | `_3x3/beginner/BeginnerSolver3x3.py` |
| `CFOP/CFOP3x3.py` | `_3x3/cfop/CFOP3x3.py` |
| `kociemba/Kociemba3x3.py` | `_3x3/kociemba/Kociemba3x3.py` |
| `reducers/BeginnerReducer.py` | `reducers/beginner/BeginnerReducer.py` |
| (new) | `common/big_cube/NxNCorners.py` |

Note: `_3x3` is prefixed with underscore because Python identifiers cannot start with digits.
