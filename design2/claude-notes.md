# Claude Notes - OpenGL Model Documentation Project

This file contains my working notes and instructions to myself during this documentation project.

---

## ⚠️ CRITICAL RULE: Consistency Across Four Areas

**EVERY documentation change MUST update ALL FOUR areas:**

```
┌─────────────────────────────────────────────────────────────────┐
│  1. CODE         → Implementation changes (if needed)          │
│  2. DOCSTRINGS   → Python docstrings in src/cube/domain/model/ │
│  3. DESIGN2/*.MD → Visual documentation with diagrams          │
│  4. INSIGHTS     → .state/insights.md                          │
└─────────────────────────────────────────────────────────────────┘
```

**Docstrings MUST include:**
- `See: design2/model-id-system.md` (or relevant doc)
- Clear explanation matching the design2 document
- Correct understanding of the concept

**NEVER create/update design2 docs without updating docstrings!**

---

## Priority Instructions

1. **FIRST**: Read `human-notes.md` carefully before doing any documentation work
2. The human developer has expressed that I don't fully understand the model - take this seriously
3. Ask clarifying questions when uncertain rather than making assumptions
4. **ALWAYS update docstrings when creating documentation**

## Current Status

- Architecture overview moved from model/ (design2/model-architecture-overview.md)
- ID system fully documented (design2/model-id-system.md + docstrings)
- Edge coordinate system documented (design2/edge-coordinate-system.md + docstrings)
- PartEdge attribute system documented (design2/partedge-attribute-system.md + docstrings)
- Generated visual diagrams in design2/images/

## Source File Locations

All model files are under: `src/cube/domain/model/`
- Part.py, Edge.py, Corner.py, Center.py
- Face.py, Cube.py
- _part_slice.py (EdgeWing, CornerSlice, CenterSlice)
- PartEdge.py

All solver files are under: `src/cube/domain/solver/`
- beginner/NxNEdges.py, L1Cross.py, etc.
- common/Tracker.py

## Documentation Progress

| Topic | design2/*.md | Docstrings | Diagrams |
|-------|--------------|------------|----------|
| Architecture Overview | ✓ (moved) | - | text diagrams |
| ID System | ✓ | ✓ | ✓ 5 diagrams |
| Edge Coordinates | ✓ | ✓ | ✓ 1 diagram |
| PartEdge Attributes | ✓ | ✓ | ✓ 3 diagrams |
| Slice (M,E,S) | TODO | TODO | TODO |
| Class Hierarchy | (in overview) | TODO | TODO |

## Questions for Human

(List questions that arise during documentation)

---

*This file is maintained by Claude to track progress and understanding.*
