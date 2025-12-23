---
name: todo
user_invocable: true
description: |
  Manage and track all TODOs from code comments and todo files. Provides quick reports
  of open tasks, scans for untracked TODOs, and integrates with GitHub Issues.
  Triggered by "/todo", "show todos", "list todos", or "todo status".
---

# Todo Management Skill

This skill consolidates all TODOs from two sources:
1. **Code comments** - `TODO:` and `CLAUDE:` markers in src/, tests/, docs/
2. **Todo files** - Files with "todo" in the filename

## Quick Start - Run Scan Script First

**ALWAYS run this script first to save tokens:**

```bash
python .claude/skills/todo/todo_scan.py
```

This outputs a complete report showing:
- Tracked vs untracked code TODOs
- Todo files and their status
- GitHub Issues with `todo` label

## Quick Report (Default Action)

When user runs `/todo`, provide a quick summary:

1. Run the scan script
2. Query GitHub Issues: `gh issue list --label todo --state open --json number,title,labels`
3. Present combined report

**Output format:**

```
=== TODO Quick Report ===

Open Issues: X (Y high, Z medium, W low)
In Progress: N
Untracked in code: M

| #   | Pri  | Category | Title                    | Status      |
|-----|------|----------|--------------------------|-------------|
| #45 | HIGH | bug      | GUI Animation Bug        | in-progress |
| #32 | MED  | arch     | Circular imports         | analyzed    |
...

Untracked Code TODOs: M
  src/file.py:123 - TODO: description
  ...

Run `/todo scan` for full scan
Run `/todo track` to create issues for untracked items
```

## Commands

### `/todo` or `/todo report`
Quick report from script output and GitHub Issues.

### `/todo scan`
Full scan with detailed output:
```bash
python .claude/skills/todo/todo_scan.py
```

### `/todo track`
For each untracked code TODO:
1. Assign next available ID (check existing TC# numbers)
2. Create GitHub Issue with `todo` and `todo:code` labels
3. Update code comment with issue number: `# TODO [#123]: text`

### `/todo analyze [#id]`
Read the code context around a TODO, update the GitHub Issue description with analysis, and add `analyzed` label.

### `/todo start #id`
Add `in-progress` label to the GitHub Issue.

### `/todo done #id`
Close the GitHub Issue. Optionally remove or update the code comment.

### `/todo reject #id [reason]`
Add `wontfix` label and close the issue with reason.

## ID Schema

### Code Comments
Format: `# TODO [ID]: description`

Examples:
- `# TODO [TC1]: Move single step mode into operator`
- `# TODO [#45]: Fix animation bug`
- `# CLAUDE [#123]: Review this logic`

### GitHub Labels

| Label | Purpose |
|-------|---------|
| `todo` | All tracked TODOs |
| `todo:code` | From code comments |
| `todo:file` | From todo files |
| `analyzed` | Claude has reviewed and understands |
| `in-progress` | Currently being worked on |
| `priority:high` | High priority |
| `priority:medium` | Medium priority |
| `priority:low` | Low priority |

## Status Flow

```
new → analyzed → in_progress → completed
                     │
                     └──────────▶ rejected (wontfix)
```

## Todo Files

Files with "todo" in filename are tracked:
- Should be moved to `todo/` folder
- Files with "new entries" section need processing
- Each entry should become a GitHub Issue

### Processing New Entries

1. Find files with `has_new_entries: true` in scan output
2. Read the new entries section
3. Create GitHub Issues for each entry
4. Update file to mark entries as processed

## Token-Saving Strategy

1. **Always run Python script first** - It does the file scanning
2. **Use --json flag** for programmatic parsing: `python .claude/skills/todo/todo_scan.py --json`
3. **Only read specific files** when analyzing individual TODOs
4. **Cache GitHub queries** - The script already queries once

## Migration Notes

Existing tracked items use these ID formats:
- `TC1-TC6` - Code TODOs
- `B#, G#, A#, Q#, S#, D#` - Categorized tasks in todo_open.md

These will be migrated to GitHub Issues when `/todo track` is run.

## Important

- **NEVER create issues without user approval** - Show what will be created first
- **Ask before modifying code** - Confirm before updating TODO comments with IDs
- **Preserve existing IDs** - Don't reassign TC1-TC6 to new numbers