# Task Queue

## Priority Order
1. Model documentation
2. Solvers documentation
3. Presentation layer documentation

---

## Phase 1: Model Research & Documentation

### 1.1 Initial Research (COMPLETED)
- [x] Explore model folder structure
- [x] Identify core model classes
- [x] Map class relationships
- [x] Understand Part, Slice, Face concepts
- [x] Understand position IDs
- [x] Understand color IDs
- [x] Understand is3x3 property chain

### 1.2 Document Core Concepts (MOSTLY COMPLETE)
- [x] Create ID system diagram (model-id-system.md)
- [x] Document which methods are phase-dependent
- [x] Document edge coordinate system (edge-coordinate-system.md)
- [x] Understand right_top_left_same_direction flag
- [x] Create 5 visual diagrams for ID system (images/)
- [x] Create 1 visual diagram for edge coordinates (images/)
- [x] **Package layers and dependencies** (layers-and-dependencies.md + 3 diagrams)
- [ ] Create model architecture diagram (class hierarchy visual)
- [ ] Document Slice concept (M, E, S middle layers)
- [ ] Document Face.rotate() mechanics in detail
- [ ] Document Corner class

### 1.3 Validate & Align (PARTIALLY COMPLETE)
- [x] Update Part.py docstrings to match design2 docs
- [x] Update Edge.py docstrings to match design2 docs
- [x] Add `See: design2/xxx.md` references in docstrings
- [x] Fix documentation links to correct source paths
- [ ] Update _part_slice.py docstrings
- [ ] Update Corner.py docstrings
- [ ] Update Face.py docstrings
- [ ] Update Cube.py docstrings

---

## Wrong Direction Dependency Violations - ALL FIXED!

**Architecture now follows bottom-to-top order:**
```
           presentation  (top - UI layer)
                ↓
           application   (middle - orchestration)
                ↓
             domain      (bottom - pure business logic)
                ↓
           utils/resources (foundation)
```

### All Violations Fixed

#### V1: domain → application.exceptions (22 files) - ✅ FIXED

| File                                      | Import                                                                               |
|-------------------------------------------|--------------------------------------------------------------------------------------|
| domain/algs/Algs.py                       | InternalSWError                                                                      |
| domain/algs/SliceAbleAlg.py               | InternalSWError                                                                      |
| domain/algs/WholeCubeAlg.py               | InternalSWError                                                                      |
| domain/algs/_parser.py                    | InternalSWError                                                                      |
| domain/model/Edge.py                      | InternalSWError                                                                      |
| domain/model/CubeSanity.py                | InternalSWError                                                                      |
| domain/model/Cube.py                      | InternalSWError                                                                      |
| domain/model/Corner.py                   | InternalSWError                                                                      |
| domain/model/CubeQueries2.py              | InternalSWError                                                                      |
| domain/model/CubeLayout.py                | InternalSWError                                                                      |
| domain/model/_part.py                     | InternalSWError                                                                      |
| domain/solver/Solvers.py                  | InternalSWError                                                                      |
| domain/solver/CFOP/OLL.py                 | InternalSWError                                                                      |
| domain/solver/CFOP/PLL.py                 | InternalSWError                                                                      |
| domain/solver/CFOP/CFOP.py                | OpAborted                                                                            |
| domain/solver/CFOP/F2L.py                 | InternalSWError                                                                      |
| domain/solver/common/CommonOp.py          | InternalSWError                                                                      |
| domain/solver/beginner/L3Cross.py         | EvenCubeEdgeParityException                                                          |
| domain/solver/beginner/NxNCenters.py      | InternalSWError                                                                      |
| domain/solver/beginner/NxNEdges.py        | InternalSWError                                                                      |
| domain/solver/beginner/BeginnerSolver.py  | OpAborted, EvenCubeEdgeParityException, InternalSWError, EvenCubeCornerSwapException |
| domain/solver/beginner/L3Corners.py       | InternalSWError, EvenCubeCornerSwapException                                         |

#### V2: domain → application.commands (16 files) - ✅ FIXED

| File                                             | Import                                           |
|--------------------------------------------------|--------------------------------------------------|
| domain/solver/Solvers.py                         | Operator                                         |
| domain/solver/solver.py                          | Operator                                         |
| domain/solver/CFOP/CFOP.py                       | Operator                                         |
| domain/solver/CFOP/F2L.py                        | AnnWhat                                          |
| domain/solver/common/SolverElement.py            | Operator, SupportsAnnotation, AnnWhat, OpAnnotation |
| domain/solver/common/BaseSolver.py               | Operator                                         |
| domain/solver/common/CommonOp.py                 | Operator, AnnWhat, SupportsAnnotation, OpAnnotation |
| domain/solver/common/AdvancedEvenOLLBigCubeParity.py | AnnWhat                                      |
| domain/solver/beginner/BeginnerSolver.py         | Operator                                         |
| domain/solver/beginner/L1Corners.py              | AnnWhat                                          |
| domain/solver/beginner/L1Cross.py                | AnnWhat                                          |
| domain/solver/beginner/L2.py                     | AnnWhat                                          |
| domain/solver/beginner/L3Corners.py              | AnnWhat                                          |
| domain/solver/beginner/L3Cross.py                | AnnWhat                                          |
| domain/solver/beginner/NxNCenters.py             | AnnWhat                                          |
| domain/solver/beginner/NxNEdges.py               | AnnWhat                                          |

#### V3: domain → presentation.viewer (2 files) - ✅ FIXED

| File                              | Import                            |
|-----------------------------------|-----------------------------------|
| domain/model/Face.py              | VMarker, viewer_add_view_marker   |
| domain/solver/common/FaceTracker.py | viewer_add_view_marker, VMarker |

### All Tasks Complete

- [x] **V1**: ✅ FIXED (2025-12-07) - Created `domain/exceptions/` with InternalSWError, OpAborted, EvenCubeEdgeParityException, EvenCubeCornerSwapException. Application re-exports for backward compatibility.
- [x] **V2**: ✅ FIXED (2025-12-07) - Created `domain/solver/protocols/` with OperatorProtocol, AnnotationProtocol. Moved AnnWhat to domain. Domain now imports protocols instead of concrete classes.
- [x] **V3**: ✅ FIXED (2025-12-07) - Moved VMarker to `domain/model/VMarker.py`. Presentation re-exports for backward compatibility.

---

## Remaining Questions to Investigate

### High Priority
1. **Slice class (M, E, S)** - How do middle slice rotations work?
2. **Face.rotate() details** - Complete the rotation mechanics documentation

### Medium Priority
1. **Color scheme (BOY)** - How is it defined and used?
2. **Corner class** - Similar to Edge but with 3 faces

### Low Priority
6. **Annotation system** - How does part annotation work?
7. **CubeSanity** - What validations are performed?
8. **CubeQueries2** - What queries are available?

### COMPLETED
- [x] `right_top_left_same_direction` - Documented with diagrams
- [x] ID system (fixed_id, position_id, colors_id) - Full visual documentation
- [x] Two-phase architecture (is3x3 property) - Documented with diagrams
- [x] Parts are FIXED, colors move - Documented with diagrams
- [x] **PartEdge Attribute System** - Three types (attributes, c_attributes, f_attributes) fully documented with diagrams

---

## Phase 2: Solvers Documentation
*(To be detailed after Phase 1)*

### Preliminary Notes
- NxNEdges.py: Uses slice-level colors_id (Phase 1)
- NxNCenters.py: Solves center pieces first
- L1Cross.py: Uses Part-level position_id and colors_id (Phase 2)
- Tracker.py: Tracks parts by colors_id across rotations

---

## Phase 3: Presentation Layer Documentation
*(To be detailed after Phase 2)*

---

## Documentation Created

| Document | Diagrams | Docstrings Updated |
|----------|----------|-------------------|
| model-architecture-overview.md | (text diagrams) | - (overview doc) |
| model-id-system.md | 5 PNGs | Part.py, Edge.py |
| edge-coordinate-system.md | 1 PNG + hand-drawn JPG | Edge.py |
| partedge-attribute-system.md | 3 PNGs | PartEdge.py |
| layers-and-dependencies.md | 3 PNGs | - (architecture doc) |

---

## Consistency Checklist
After any documentation change, verify alignment of:
- [x] Code
- [x] Docstrings (Part.py, Edge.py done)
- [x] design2 documents
- [x] .state insights
