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

### 1.2 Document Core Concepts (IN PROGRESS)
- [x] Create ID system diagram (model-id-system.md)
- [x] Document which methods are phase-dependent
- [x] Document edge coordinate system (edge-coordinate-system.md)
- [x] Understand right_top_left_same_direction flag
- [ ] Create model architecture diagram (class hierarchy visual)
- [ ] Document Part class and its methods
- [ ] Document Slice concept (M, E, S middle layers)
- [ ] Document Face concept
- [ ] Document rotation/transformation logic

### 1.3 Validate & Align (NOT STARTED)
- [ ] Cross-check documentation with existing docstrings
- [ ] Update any inconsistent docstrings
- [ ] Add links between docs and code

---

## Remaining Questions to Investigate

### High Priority
1. **Face.rotate() mechanics** - Partially understood via edge coordinate analysis
2. **Slice class (M, E, S)** - How do middle slice rotations work?

### Medium Priority
3. **PartEdge class** - What is the role of the smallest unit?
4. **Color scheme (BOY)** - How is it defined and used?
5. **CubeQueries2** - What queries are available?

### Low Priority
6. **Annotation system** - How does part annotation work?
7. **CubeSanity** - What validations are performed?

### COMPLETED
- [x] `right_top_left_same_direction` - Documented in edge-coordinate-system.md

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

## Consistency Checklist
After any documentation change, verify alignment of:
- [ ] Code
- [ ] Docstrings
- [ ] design2 documents
- [ ] .state insights
