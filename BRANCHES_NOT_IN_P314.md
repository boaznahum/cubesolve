# Branches with Work Not in p314

This document lists all branches (excluding `archive/*`) that contain commits not yet merged into `p314`.

Generated: 2025-12-18

---

## TODO: Actions Required

1. [ ] **cpof-fix2** → Merge into cage-solver, then merge cage-solver into p314
2. [ ] **solvertodo1** → Merge the settings fix into p314
3. [ ] **origin/claude/fix-cage-cfop-solver-9b2IT** → Archive (superseded by cpof-fix2)
4. [ ] **origin/claude/learn-project-structure-*** → Archive (contained in parity-docs-cAG7u)
5. [ ] **origin/claude/parity-docs-cAG7u** → Review docs, cherry-pick useful commits
6. [ ] **origin/claude/parity-docs-orchestrator-cAG7u** → Review test improvements, cherry-pick useful commits

---

## Local Branches

### cage-solver (10+ commits ahead)
Cage method solver implementation - solves edges and corners first, centers last.

```
1c922da Update cage solver tests - Phase 2 now fully implemented
1cb3cc7 Restore CageCenters and Phase 2 integration from PyCharm history
110d900 Remove incorrect assertion that broke even cube tests
38a8273 Merge p314 with AbstractSolver fix into cage-solver
ca34d31 Cage solver: fix instant solve animation + plan Phase 2 centers
1c352fd Fix cage solver: use beginner instead of CFOP for Phase 1b
a5784a3 Cage solver Phase 1b: solve corners via 3x3 solver
90bd1e9 Cage solver: Fresh implementation with edge solving (Phase 1a)
c274740 Merge branch 'p314' into cage-solver
6b568a8 Cage solver Step 2: find edges with target color
```

**Status:** Phase 1 (edges + corners) complete, Phase 2 (centers) implemented with CageCenters.

---

### cpof-fix2 (11+ commits ahead)
Fork of cage-solver with CFOP support fix.

```
5b9325d Add ignore_center_check to F2L for Cage solver CFOP support
1c922da Update cage solver tests - Phase 2 now fully implemented
1cb3cc7 Restore CageCenters and Phase 2 integration from PyCharm history
... (same as cage-solver plus the CFOP fix)
```

**Key change:** Added `ignore_center_check` parameter to F2L, CFOP3x3, and Solvers3x3 so CFOP works when centers aren't solved (needed for Cage method).

---

### solvertodo1 (1 commit ahead)
Minor fix branch.

```
a57dde1 fix .claude corrupted settings
```

---

## Remote-Only Branches

### origin/claude/fix-cage-cfop-solver-9b2IT (4 commits ahead)
Earlier attempt at CFOP fix for Cage solver (superseded by cpof-fix2).

```
11f4e77 Add detailed branch summary for merge handoff
a30904f Add ignore_center_check parameter to F2L for Cage solver
a7c979a Fix F2L to work when centers aren't solved (enables CFOP for Cage)
9a5bcbc Fix AbstractSolver bugs and enable Cage solver
```

**Status:** Superseded by cpof-fix2. Can be archived.

---

### origin/claude/learn-project-structure-01WYYtkueCTRzNjpBziMJtBB (2 commits ahead)
Project structure documentation.

```
378bc87 Document GUI abstraction migration state
e7eae80 Add comprehensive project structure learning documentation
```

**Status:** Documentation only. Contained in parity-docs-cAG7u. Can be archived.

---

### origin/claude/parity-docs-cAG7u (5 commits ahead)
Parity documentation improvements. Contains learn-project-structure commits.

```
12a89d3 Document why corner parity is fixed immediately but edge is not
e761ba5 Rename and improve parity documentation for pre-orchestrator design
9e37d09 Add comprehensive parity error handling documentation
378bc87 Document GUI abstraction migration state
e7eae80 Add comprehensive project structure learning documentation
```

**Status:** Documentation only. Review and merge if useful.

---

### origin/claude/parity-docs-orchestrator-cAG7u (6 commits ahead)
Parity documentation and solver test improvements.

```
b698815 Add GUI scramble seeds 0-9 to solver tests
4ed7cef Decouple solver tests from GUI dependencies
8d7d180 Add detailed odd cube edge parity documentation
064210e Add .venv to gitignore
e00e157 Align orchestrator code comments with old BeginnerSolver design
df45c76 Add comprehensive parity handling documentation for both designs
```

**Status:** Contains useful test improvements. Review for merge.

---

## Branches Already Contained in p314 (Cleaned Up)

These branches were deleted or archived because p314 already contains all their commits:

**Deleted:**
- `fix-even-cube-tests`
- `golden-solver`
- `image-texture-bug`
- `new-opengl`
- `pyglet-native-toolbar` (local + remote)
- `solver-tests-and-docs`
- `gui-controls` (remote)
- `imgui-controls` (local + remote)

**Archived:**
- `before-remove-pyglet1` → `archive/before-remove-pyglet1`

**Kept:**
- `main` (main branch, always keep)
