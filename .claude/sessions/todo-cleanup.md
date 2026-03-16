# Session: todo-cleanup

**Branch:** `todo-cleanup`
**Base:** `imporove-geometry`
**Started:** 2026-03-16

## Goal
Migrate all TODO tracking from local files to GitHub Issues only, clean up stale issues.

## What Was Done

### 1. Created GitHub Issues for all untracked items (#120-#136)
- 9 from untracked code TODOs (no issue number)
- 1 from untracked todo_open.md entry (_BRING_TO_UP)
- 3 from todo_new_entries.md (A1, A2, A4)
- 1 from _2x2_ida_optimal/_todo.md
- 3 from lbl/wip/___todo.md

### 2. Updated code comments with issue numbers
All 11 previously-untracked code TODOs now have `[#NNN]` references.

### 3. Deleted 8 local todo files
- `todo/todo_open.md`, `todo/todo_code_comments.md`, `todo/todo_new_entries.md`
- `todo/todo_completed.md`, `todo/todo_skill_requirements.md`
- `src/cube/domain/geometric/boaz-geo-todo.md`
- `src/cube/domain/solver/_2x2_ida_optimal/_todo.md`
- `src/cube/domain/solver/direct/lbl/wip/___todo.md`

### 4. Rewrote todo skill to GitHub-only
- `.claude/skills/todo/SKILL.md` — simplified, no local file references
- `.claude/skills/todo/todo_scan.py` — scans code + GitHub only

### 5. Scanned all 63 open issues against codebase
Closed 15 confirmed-done issues.

## Issue Scan Results

| Category | Count | Issues |
|----------|-------|--------|
| **Closed as DONE** | 15 | #5, #13, #29, #32, #37, #38, #43, #45, #48, #49, #51, #55, #61, #131, #133 |
| **Probably done** | 9 | #6, #9, #17, #22, #23, #27, #40, #50, #129 |
| **Not done** | 28 | #3, #4, #7, #8, #11, #14, #15, #16, #18, #20, #21, #28, #33, #34, #36, #47, #120-#128, #134-#136 |
| **Unclear** | 11 | #10, #12, #19, #25, #30, #31, #35, #39, #41, #130, #132 |

## Current Status
- 48 open GitHub issues with `todo` label remain
- 0 untracked code TODOs
- No local todo files (GitHub is single source of truth)
- Awaiting user review of "probably done" and "unclear" issues

## Files Modified
- `.claude/skills/todo/SKILL.md` — rewritten
- `.claude/skills/todo/todo_scan.py` — rewritten
- 8 source files — code comments updated with issue numbers
- 8 todo files — deleted

## Next Steps
- User to review "probably done" issues and decide which to close
- User to review "unclear" issues
- Commit changes
