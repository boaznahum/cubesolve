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
- **Location:** `todo/` folder
- **Files:**
  - `todo_open.md` - Active non-code TODOs (table with GitHub links)
  - `todo_code_comments.md` - Active code TODOs (table with GitHub links)
  - `todo_new_entries.md` - Inbox for quick notes
  - `todo_completed.md` - Completed items (reference)

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
Script: `.claude/skills/todo/todo_scan.py`
- Scans code for TODO/CLAUDE comments (fast, no AI tokens)
- Outputs formatted report or JSON (`--json` flag)
- Compares with GitHub Issues
- Reports untracked items

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
├── todo_skill_requirements.md    # This file (requirements doc)
├── todo_open.md                  # Non-code TODOs (table with GH links)
├── todo_code_comments.md         # Code TODOs (table with GH links)
├── todo_new_entries.md           # Inbox for quick notes
├── todo_completed.md             # Completed items (reference)
├── __dead_code.md                # Dead code tracking
└── __next_session.md             # Session notes

.claude/skills/todo/
├── SKILL.md                      # The skill definition
└── todo_scan.py                  # Python helper for scanning
```

---

## Migration Status

**Completed:** 2025-12-24

### What Was Done
1. ✅ Created GitHub labels (todo, todo:code, todo:file, priority:*, etc.)
2. ✅ Created GitHub Issues #3-#15 for code TODOs
3. ✅ Created GitHub Issues #16-#45 for non-code TODOs
4. ✅ Updated code comments with issue numbers `[#N]`
5. ✅ Simplified todo files (detailed descriptions moved to GitHub)
6. ✅ Deleted redundant files (`__todo.md`, `__todo_cage.md`, etc.)

### Current State
- **45 GitHub Issues** with `todo` label
- **Code TODOs:** Tracked in `todo_code_comments.md` with GitHub links
- **Non-code TODOs:** Tracked in `todo_open.md` with GitHub links
- **Detailed descriptions:** In GitHub Issues (not in files)
