# Insights - What I've Learned

This file captures key understandings gained during the documentation project.

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
