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
- [ ] Create model architecture diagram (class hierarchy visual)
- [ ] Document Part class and its methods
- [ ] Document Slice concept
- [ ] Document Face concept
- [ ] Document rotation/transformation logic

### 1.3 Validate & Align (NOT STARTED)
- [ ] Cross-check documentation with existing docstrings
- [ ] Update any inconsistent docstrings
- [ ] Add links between docs and code

---

## Remaining Questions to Investigate

### High Priority
1. **Face.rotate() mechanics** - How does rotation actually work step by step?
2. **Slice class (M, E, S)** - How do middle slice rotations work?
3. **`right_top_left_same_direction`** - What does this flag mean in Edge class?

### Medium Priority
4. **PartEdge class** - What is the role of the smallest unit?
5. **Color scheme (BOY)** - How is it defined and used?
6. **CubeQueries2** - What queries are available?

### Low Priority
7. **Annotation system** - How does part annotation work?
8. **CubeSanity** - What validations are performed?

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
