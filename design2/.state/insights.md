# Insights - What I've Learned

This file captures key understandings gained during the documentation project.

---

## Project Architecture (from README)

**Source:** README.md (2025-12-06)

Architecture layers:
- **Entry Points** - main_pyglet.py, main_headless.py, main_any_backend.py
- **GUI Layer** - Window, Viewer, Animation Manager
- **Application Core** - App, Cube, Operator, Solver, ViewState
- **Backend Abstraction** - Renderer, EventLoop protocols

**Model package contains:** Cube, Face, Slice, Corner, Edge, Center

**Solvers (order matters - reflects two-phase solving):**
1. `nxn_centers.py` - Big cube centers (Phase 1)
2. `nxn_edges.py` - Big cube edges (Phase 1)
3. `l1_cross.py`, `l1_corners.py` - Layer 1 (Phase 2)
4. `l2.py` - Layer 2
5. `l3_cross.py`, `l3_corners.py` - Layer 3

**Algs:** in algs.py - can be combined, inverted, sliced, multiplied

**Diagrams available:** readme_files/ folder contains architecture diagrams

---

## Two-Phase Cube Architecture

**Source:** Human developer explanation (2025-12-06)

The cube solution operates in two distinct phases:

### Phase 1: Big Cube (e.g., 5x5)
- Focus is on **part slices**
- Some part methods are **meaningless** in this phase
- Example: A part's "color" is NOT defined until all slices are in place
- Asking for a part's color before reduction is invalid

### Phase 2: After Reduction (3x3)
- Cube is reduced to 3x3 structure
- Parts now have **well-defined colors**
- Parts become valid input to the solver

### Implication
When documenting the model, I must:
- Identify which methods are phase-dependent
- Clearly mark when methods are valid vs invalid
- Understand position IDs and color IDs and their role in rotations

---

## Questions to Investigate

1. How exactly does reduction work in the code?
2. What are position IDs vs color IDs?
3. How do color IDs play a role when rotating slices/faces?
4. Which specific part methods are invalid before reduction?

---

*(More insights will be added as research progresses)*
