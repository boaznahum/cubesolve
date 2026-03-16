---
name: todo
user_invocable: true
description: |
  Manage and track all TODOs via GitHub Issues. Provides quick reports,
  scans for untracked code TODOs, and syncs code comments with GitHub.
  Triggered by "/todo", "show todos", "list todos", or "todo status".
---

# Todo Management Skill (GitHub-Only)

All TODOs are tracked as GitHub Issues with the `todo` label. There are no local todo files.

## Quick Start

**ALWAYS run the scan script first to save tokens:**

```bash
python .claude/skills/todo/todo_scan.py
```

## Commands

### `/todo help`
```
/todo              Quick report (open issues, priorities, in-progress)
/todo scan         Scan code for untracked TODOs
/todo sync         Check code<->GitHub consistency
/todo search X     Search issues by keyword or label
/todo track        Create GitHub Issues for untracked code TODOs
/todo analyze #id  Analyze TODO and update its GitHub Issue
/todo start #id    Mark issue as in-progress
/todo done #id     Close the issue
/todo reject #id   Close with wontfix label
```

### `/todo` or `/todo report`
Quick report from scan script + GitHub Issues.

1. Run: `python .claude/skills/todo/todo_scan.py`
2. Present the output as a formatted report

### `/todo scan`
Full scan:
```bash
python .claude/skills/todo/todo_scan.py
```

### `/todo sync`
Find inconsistencies between code comments and GitHub:
```bash
python .claude/skills/todo/todo_scan.py --sync
```

**Checks:**
1. Code TODO has `[#X]` but issue doesn't exist or is closed
2. GitHub Issue with `todo:code` label has no matching code comment
3. Code TODO references a CLOSED issue (stale - should be removed)

**Interactive resolution:** Ask user how to fix each inconsistency.

### `/todo search [query] [--label <label>]`
```bash
gh issue list --label todo --search "query" --state open --json number,title,labels,state
gh issue list --label todo --label "priority:high" --state open --json number,title,labels,state
```

### `/todo track`
For each untracked code TODO:
1. Create GitHub Issue with `todo` and `todo:code` labels
2. Update code comment: `# TODO [#123]: text`

### `/todo analyze [#id]`
Read code context, update GitHub Issue description, add `analyzed` label.

### `/todo start #id`
Add `in-progress` label.

### `/todo done #id`
Close the GitHub Issue. Optionally remove the code comment.

### `/todo reject #id [reason]`
Add `wontfix` label and close with reason.

## Code Comment Format

```python
# TODO [#123]: description
# CLAUDE [#123]: description
```

## GitHub Labels

| Label | Purpose |
|-------|---------|
| `todo` | All tracked TODOs |
| `todo:code` | From code comments |
| `analyzed` | Claude has reviewed and understands |
| `in-progress` | Currently being worked on |
| `priority:high` | High priority |
| `priority:medium` | Medium priority |
| `priority:low` | Low priority |

## Status Flow

```
new -> analyzed -> in_progress -> completed
                       |
                       +-> rejected (wontfix)
```

## Important

- **NEVER create issues without user approval** - Show what will be created first
- **Ask before modifying code** - Confirm before updating TODO comments
