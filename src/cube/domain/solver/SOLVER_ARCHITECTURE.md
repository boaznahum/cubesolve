# Solver Architecture

This document describes the class hierarchy for the solver module, including solvers, reducers, and their supporting components.

## Overview

The solver architecture consists of two parallel hierarchies that share common infrastructure:
1. **Solvers** - Solve 3x3 cubes (BeginnerSolver3x3, CFOP3x3, Kociemba3x3)
2. **Reducers** - Reduce NxN cubes to virtual 3x3 state (BeginnerReducer)

Both hierarchies share solver components (SolverHelper subclasses) through the `SolverElementsProvider` protocol.

## Class Hierarchy Diagram

```
+-----------------------------------------------------------------------------+
|                           PROTOCOLS                                          |
+-----------------------------------------------------------------------------+
|                                                                              |
|  +-----------------------------+     +----------------------------------+    |
|  | <<protocol>>                |     | <<protocol>>                     |    |
|  | SolverElementsProvider      |     | ReducerProtocol                  |    |
|  +-----------------------------+     +----------------------------------+    |
|  | + op: OperatorProtocol      |     | + op: OperatorProtocol           |    |
|  | + cube: Cube                |     | + is_reduced(): bool             |    |
|  | + cmn: CommonOp             |     | + reduce(): ReductionResults     |    |
|  | + debug(*args): None        |     | + fix_edge_parity(): None        |    |
|  +-----------------------------+     | + fix_corner_parity(): None      |    |
|               ^                      +----------------------------------+    |
|               | implements                           ^                       |
|    +----------+-----------+                          | implements            |
|    |                      |                          |                       |
+----+----------------------+--+-----------------------+-----------------------+
     |                      |  |                       |
+----+----------------------+--+-----------------------+-----------------------+
|    |     SOLVERS          |  |                       |      REDUCERS         |
+----+----------------------+--+-----------------------+-----------------------+
|    |                      |  |                       |                       |
|    v                      |  |                       v                       |
| BaseSolver ---------------+  |          AbstractReducer                      |
|    |                         |               |                               |
|    +-- BeginnerSolver3x3     |               +-- BeginnerReducer             |
|    +-- CFOP3x3               |                   (passes SELF to elements)   |
|    +-- Kociemba3x3           |                                               |
|                              |                                               |
+------------------------------+-----------------------------------------------+
                               |
                               | uses
                               v
+-----------------------------------------------------------------------------+
|                           SOLVER ELEMENTS                                    |
+-----------------------------------------------------------------------------+
|                                                                              |
|  SolverHelper(provider: SolverElementsProvider)                             |
|       |                                                                      |
|       +-- NxNCenters         (center reduction for NxN cubes)                |
|       +-- NxNEdges           (edge reduction for NxN cubes)                  |
|       +-- L3Cross            (last layer cross)                              |
|       +-- L3Corners          (last layer corners)                            |
|       +-- OLL                (orientation of last layer)                     |
|       +-- PLL                (permutation of last layer)                     |
|       +-- ...                                                                |
|                                                                              |
|  CommonOp(provider: SolverElementsProvider)                                  |
|       - Shared operations for cube manipulation                              |
|                                                                              |
+-----------------------------------------------------------------------------+
```

## Key Design Decisions

### 1. SolverElementsProvider Protocol

The `SolverElementsProvider` protocol defines the minimal interface that `SolverHelper` and `CommonOp` need from a solver or reducer:

```python
class SolverElementsProvider(Protocol, metaclass=ABCMeta):
    @property
    def op(self) -> OperatorProtocol: ...

    @property
    def cube(self) -> Cube: ...

    @property
    def cmn(self) -> CommonOp: ...

    def debug(self, *args: LazyArg) -> None: ...
```

This protocol allows:
- **Solvers** (`BaseSolver` subclasses) to use solver elements
- **Reducers** (`AbstractReducer` subclasses) to use the same solver elements
- **No facade classes needed** - reducers can pass `self` directly to solver elements

### 2. AbstractReducer Base Class

`AbstractReducer` provides a common implementation of `SolverElementsProvider` for all reducers:

```python
class AbstractReducer(ReducerProtocol, SolverElementsProvider, ABC):
    def __init__(self, op: OperatorProtocol) -> None:
        self._op = op
        self._cube = op.cube
        self._cmn = CommonOp(self)  # Pass self - we implement the protocol!
```

Before this refactoring, `BeginnerReducer` used a `_ReducerSolverFacade` hack to satisfy the `BaseSolver` type requirement of solver elements. Now it simply extends `AbstractReducer` and passes `self`.

### 3. Dependency Flow

```
Orchestrator
    |
    +-- Reducer (AbstractReducer)
    |       |
    |       +-- NxNCenters(self)  -- self implements SolverElementsProvider
    |       +-- NxNEdges(self)
    |       +-- L3Corners(self)
    |
    +-- Solver (BaseSolver)
            |
            +-- L3Cross(self)
            +-- L3Corners(self)
            +-- OLL(self)
            +-- PLL(self)
```

## File Structure

```
solver/
    protocols/
        __init__.py
        OperatorProtocol.py
        AnnotationProtocol.py
        ReducerProtocol.py
        Solver3x3Protocol.py
        SolverElementsProvider.py    <-- NEW: Minimal interface for components

    common/
        BaseSolver.py                <-- Implements SolverElementsProvider
        CommonOp.py                  <-- Uses SolverElementsProvider
        SolverHelper.py             <-- Uses SolverElementsProvider
        ...

    reducers/
        AbstractReducer.py           <-- NEW: Base class implementing SolverElementsProvider
        BeginnerReducer.py           <-- Extends AbstractReducer

    beginner/
        NxNCenters.py                <-- SolverHelper subclass
        NxNEdges.py                  <-- SolverHelper subclass
        L3Cross.py                   <-- SolverHelper subclass
        L3Corners.py                 <-- SolverHelper subclass
        ...

    cfop/
        ...
```

## Related Documentation

- `arch.md` - Main architecture document
- `readme_files/solver.puml` - PlantUML class diagrams
- `PARITY_HANDLING_ORCHESTRATOR.md` - Parity detection and fixing flow
