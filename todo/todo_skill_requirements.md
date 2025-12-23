# Todo Skill Requirements

**Created:** 2025-12-23
**Status:** Implementing (GitHub-based approach)

---

## Purpose

Consolidate and organize all TODOs from the codebase into a unified tracking system. Provide quick reports and ensure all TODOs are tracked with proper IDs and status.

---

## Two Sources of TODOs

### 1. Code Comments
- **Markers:** `TODO:` or `CLAUDE:` (case insensitive)
- **Scope:** `src/`, `tests/`, `docs/` directories
- **Example patterns:**
  ```python
  # TODO: fix this bug
  # todo [TC1]: already tracked item
  # CLAUDE: please review this logic
  # claude: check if this is correct
  ```

### 2. Todo Files
- **Definition:** Any file with "todo" in its filename (case insensitive)
- **Examples:** `__todo.md`, `__todo_cage.md`, `__todo_solvers.md`
- **Location:** Should be moved to `todo/` folder if found elsewhere

---

## ID Schema

### Code Comment IDs
- **Format:** `TC#` (e.g., `TC1`, `TC2`, `TC23`)
- **In code:** `# TODO [TC1]: description here`
- **Sequence:** Auto-increment from highest existing TC number

### GitHub Issue IDs (preferred approach)
- **Format:** `#123` (GitHub issue number)
- **In code:** `# TODO [#123]: description here`
- **Labels for categories:**
  - `todo` - All tracked TODOs
  - `todo:code` - From code comments
  - `todo:file` - From todo files
  - `bug`, `architecture`, `gui`, `quality`, `solver`, `docs` - Categories

---

## Workflow

### Code TODOs Workflow

```
┌─────────────────┐
│ Scan code for   │
│ TODO:/CLAUDE:   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Has ID?         │──No─▶│ Assign new ID   │
│ [TC#] or [#123] │      │ Update code     │
└────────┬────────┘      │ Create GH issue │
         │Yes            └────────┬────────┘
         ▼                        │
┌─────────────────┐               │
│ Verify exists   │◀──────────────┘
│ in GH Issues    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check status    │
│ (labels)        │
└─────────────────┘
```

### Status Flow

```
new → analyzed → in_progress → completed
                     │
                     └──────────▶ rejected (wontfix)
```

**Status via GitHub:**
- `new` - Issue exists, no `analyzed` label
- `analyzed` - Has label `analyzed` (Claude reviewed and understands)
- `in_progress` - Has label `in-progress`
- `completed` - Issue is closed
- `rejected` - Issue closed with label `wontfix`

### File TODOs Workflow

1. **Find files:** Search for `*todo*` pattern in filenames
2. **Relocate:** Move files not in `todo/` folder to `todo/`
3. **Parse entries:** Look for "new entries" section (unprocessed items)
4. **Create issues:** Each new entry becomes a GitHub Issue
5. **Update file:** Mark entries as processed with issue number

---

## Analyzed Flag

**Purpose:** Save tokens by analyzing TODOs once, marking them understood.

**What "analyzed" means:**
- Claude has read and understood the TODO
- Context is captured in the GitHub Issue description
- No need to re-read surrounding code each time
- Ready to be worked on when prioritized

**When to analyze:**
- When TODO is first discovered
- When explicitly requested via `/todo analyze`

---

## Quick Report Format

When user runs `/todo`, display:

```
=== TODO Quick Report ===
Last scan: 2025-12-23 14:30

Open Issues: 15 (3 high, 8 medium, 4 low)
In Progress: 2
Needs Analysis: 5

| #   | Pri  | Category | Title                        | Status      |
|-----|------|----------|------------------------------|-------------|
| #45 | HIGH | bug      | GUI Animation Bug            | in-progress |
| #32 | MED  | arch     | Circular imports             | analyzed    |
| #28 | LOW  | quality  | Clean dead code              | new         |
...

Untracked Code TODOs: 2
  src/cube/model/Face.py:246 - TODO: unclear why copies needed
  src/cube/solver/L3Cross.py:45 - CLAUDE: check this logic

Run `/todo scan` to create issues for untracked items.
Run `/todo analyze` to analyze unanalyzed items.
```

---

## Skill Commands

### `/todo` (default)
Quick report showing all open TODOs from GitHub Issues.

### `/todo scan`
Full scan of codebase:
1. Find all `TODO:` and `CLAUDE:` comments
2. Find all todo files
3. Compare with GitHub Issues
4. Report untracked items
5. Optionally create issues for new items

### `/todo analyze [#id]`
Analyze a specific TODO or all unanalyzed TODOs:
1. Read the code context
2. Update GitHub Issue with analysis
3. Add `analyzed` label

### `/todo start #id`
Mark a TODO as in-progress:
1. Add `in-progress` label
2. Update Claude's TodoWrite list

### `/todo done #id`
Mark a TODO as completed:
1. Close the GitHub Issue
2. If code comment, optionally remove it

### `/todo reject #id [reason]`
Reject a TODO:
1. Add `wontfix` label
2. Close the issue with reason

---

## Token-Saving Strategies

### Python Helper Script
Create `scripts/todo_scan.py` to:
- Scan code for TODO/CLAUDE comments (fast, no AI tokens)
- Output JSON with file, line, content, has_id
- Compare with `gh issue list` output
- Report discrepancies

### Cached Queries
- Cache `gh issue list` results for quick report
- Only do full scan when explicitly requested

### Minimal Context
- Quick report: Just query GitHub, no code reading
- Analysis: Read only the specific file/function context

---

## GitHub Labels Setup

```bash
# Create labels for the todo system
gh label create "todo" --color "0E8A16" --description "Tracked TODO item"
gh label create "todo:code" --color "1D76DB" --description "TODO from code comment"
gh label create "todo:file" --color "5319E7" --description "TODO from todo file"
gh label create "analyzed" --color "FBCA04" --description "TODO has been analyzed"
gh label create "in-progress" --color "D93F0B" --description "Currently being worked on"
gh label create "priority:high" --color "B60205" --description "High priority"
gh label create "priority:medium" --color "FBCA04" --description "Medium priority"
gh label create "priority:low" --color "0E8A16" --description "Low priority"
```

---

## File Structure

```
todo/
├── todo_skill_requirements.md    # This file
├── todo_code_comments.md         # Legacy - migrate to GH Issues
├── todo_open.md                  # Legacy - migrate to GH Issues
├── todo_completed.md             # Legacy - reference only
├── __todo_new_entries.md         # Inbox for quick notes
└── ...other todo files...

scripts/
└── todo_scan.py                  # Python helper for scanning

.claude/commands/
└── todo.md                       # The skill definition
```

---

## Migration from Current System

### Current State
- `todo_code_comments.md` - TC1-TC6 tracked
- `todo_open.md` - B1, G2, A7, etc. tracked
- Various `__todo*.md` files scattered

### Migration Steps
1. Create GitHub labels
2. Create GitHub Issues for all items in `todo_open.md`
3. Create GitHub Issues for TC1-TC6 in `todo_code_comments.md`
4. Update code comments with GitHub issue numbers
5. Archive old todo files (keep for reference)

---

## Alternative: File-Based Approach

If GitHub Issues doesn't work out, fall back to file-based:

### Files
- `todo/todo_active.md` - All active TODOs
- `todo/todo_completed.md` - Completed items
- `todo/todo_rejected.md` - Rejected items

### Same workflow, but:
- IDs stay as TC#, B#, G#, etc.
- Status tracked in markdown tables
- Python script updates files instead of GitHub

---

## Implementation Notes

### Phase 1: Setup
- [ ] Create GitHub labels
- [ ] Create `scripts/todo_scan.py`
- [ ] Create `.claude/commands/todo.md` skill

### Phase 2: Migration
- [ ] Migrate `todo_open.md` items to GitHub Issues
- [ ] Migrate `todo_code_comments.md` items to GitHub Issues
- [ ] Update code comments with issue numbers

### Phase 3: Daily Use
- [ ] `/todo` shows quick report
- [ ] `/todo scan` finds new items
- [ ] `/todo analyze` processes unanalyzed items
