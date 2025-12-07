# Package Layers and Dependencies

This document describes the package structure of `src/cube/` and the dependencies between packages.

---

## Complete Overview

![Package Layers and Dependencies](images/combined-layers-dependencies.png)

---

## First Level Packages (bottom-to-top order)

| Layer | Package | Purpose |
|-------|---------|---------|
| Foundation | `utils/` | Utility functions (OrderedSet, etc.) |
| Foundation | `resources/` | Static resources (face images) |
| Bottom | `domain/` | Core business logic (cube model, solvers, algorithms) |
| Middle | `application/` | Application logic, state management, commands |
| Top | `presentation/` | GUI, viewers, rendering backends |

**Ideal dependency flow:** `presentation -> application -> domain -> utils/resources`

---

## Second Level Packages

### application/
| Package | Purpose |
|---------|---------|
| `animation/` | Animation management and timing |
| `commands/` | Operator/command system for cube operations |
| `exceptions/` | Custom exception types |

### domain/
| Package | Purpose |
|---------|---------|
| `algs/` | Algorithm definitions (Alg, SimpleAlg, SliceAbleAlg) |
| `model/` | Cube model classes (Cube, Part, Face, Edge, Corner, etc.) |
| `solver/` | Solving algorithms |
| `solver/beginner/` | Layer-by-layer beginner method |
| `solver/CFOP/` | CFOP speedcubing method |
| `solver/common/` | Shared solver utilities (Tracker, CommonOp) |
| `solver/protocols/` | Protocol interfaces for dependency inversion |
| `exceptions/` | Domain-specific exceptions |

### presentation/
| Package | Purpose |
|---------|---------|
| `gui/` | GUI framework and window management |
| `gui/backends/` | Backend implementations (pyglet2, tkinter, console, headless, web) |
| `gui/commands/` | GUI command pattern implementations |
| `gui/effects/` | Visual effects (confetti, sparkle) |
| `gui/protocols/` | Protocol definitions for GUI abstraction |
| `viewer/` | Cube viewer logic (_cell, _Board, etc.) |

---

## Dependencies

### Normal Dependencies (green arrows)
- `application` -> `domain` (uses cube model and algorithms)
- `presentation` -> `domain` (displays cube state)
- `presentation` -> `application` (uses operators and animation)
- `domain` -> `utils` (OrderedSet usage)
- `presentation` -> `resources` (face images)

---

## All Violations Fixed!

| ID  | From      | To             | Status  | Fix Applied |
|-----|-----------|----------------|---------|-------------|
| V1  | `domain`  | `application`  | FIXED | Created `domain/exceptions/` |
| V2  | `domain`  | `application`  | FIXED | Created `domain/solver/protocols/` |
| V3  | `domain`  | `presentation` | FIXED | Moved `VMarker` to `domain/model/` |

### V1: Exceptions (FIXED)
- Created `domain/exceptions/` with InternalSWError, OpAborted, etc.
- Application re-exports for backward compatibility

### V2: Commands/Protocols (FIXED)
- Created `domain/solver/protocols/` with OperatorProtocol, AnnotationProtocol
- Moved AnnWhat enum to `domain/solver/AnnWhat.py`
- Domain imports protocols instead of concrete application classes
- Application implements protocols and re-exports for backward compatibility

### V3: Viewer/VMarker (FIXED)
- Moved `VMarker.py` to `domain/model/VMarker.py`
- Presentation re-exports for backward compatibility
- No more domain -> presentation imports

---

## Clean Architecture Achieved

```
presentation -> application -> domain -> (nothing external)
                  |
               utils/resources
```

The architecture now follows clean dependency rules:
- Higher layers depend on lower layers only
- No circular or wrong-direction dependencies
- Backward compatibility maintained via re-exports

---

## Source Files

- Generator script: `design2/images/generate_layers_diagrams.py`

To regenerate diagram:
```bash
cd design2/images
python generate_layers_diagrams.py
```

---

*Last updated: 2025-12-07*
