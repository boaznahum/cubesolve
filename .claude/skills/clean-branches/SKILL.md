---
name: clean-branches
user_invocable: true
description: |
  Clean up git branches by analyzing merged/unmerged status, archiving completed work,
  and organizing active branches. This skill should be used when the user wants to clean
  up branches, organize their git repository, or review branch status.
  Triggered by "/clean-branches", "/branches", "clean branches", or "check branches".
---

# Branch Cleanup Skill

This skill provides an iterative workflow for cleaning up git branches by analyzing their merge status and organizing them into appropriate namespaces.

## Branch Organization Schema

| Namespace | Purpose | Example |
|-----------|---------|---------|
| `archive/completed/<name>` | Merged branches (work completed) | `archive/completed/feature-login` |
| `archive/stopped/<name>` | Unmerged branches (abandoned work) | `archive/stopped/experiment-x` |
| `wip/<name>` | Work in progress (active development) | `wip/new-feature` |
| (root) | Keep as-is | `feature-y` |

## Workflow

### Step 1: Identify Default Branch

Query GitHub to determine the default branch:

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

### Step 2: Fetch All Remote Branches

```bash
git fetch --all --prune
```

### Step 3: List All Branches

Get all local and remote branches:

```bash
# Local branches
git branch --list

# Remote branches (excluding HEAD)
git branch -r | grep -v HEAD
```

### Step 4: Analyze Each Branch

For each branch (excluding the default branch and already-archived branches):

1. **Check if merged** into default branch:
   ```bash
   git branch --merged <default-branch> | grep -q <branch-name>
   ```

2. **Get last commit info**:
   ```bash
   git log -1 --format="%h %s (%cr by %an)" <branch-name>
   ```

3. **Check if remote exists**:
   ```bash
   git ls-remote --heads origin <branch-name>
   ```

### Step 5: Generate Report

Present a summary table to the user:

| Branch | Status | Last Commit | Author | Age | Recommendation |
|--------|--------|-------------|--------|-----|----------------|
| feature-x | Merged | abc123 Fix bug | John | 2 weeks ago | → archive/completed |
| experiment-y | Unmerged | def456 WIP | Jane | 3 months ago | → archive/stopped? |

### Step 6: Process Merged Branches

For branches confirmed as merged, move to `archive/completed/`:

```bash
# Rename local branch
git branch -m <branch> archive/completed/<branch>

# Push new branch name
git push origin archive/completed/<branch>

# Delete old remote branch
git push origin --delete <branch>
```

### Step 7: Handle Unmerged Branches

For each unmerged branch, ask the user using AskUserQuestion:

- **Keep**: Leave branch as-is
- **WIP**: Move to `wip/<branch-name>`
- **Stop**: Move to `archive/stopped/<branch-name>`

Then execute the chosen action:

```bash
# For WIP
git branch -m <branch> wip/<branch>
git push origin wip/<branch>
git push origin --delete <branch>

# For Stop
git branch -m <branch> archive/stopped/<branch>
git push origin archive/stopped/<branch>
git push origin --delete <branch>
```

### Step 8: Iterate

After processing, show updated branch list and ask if further cleanup is needed. Repeat until the user is satisfied.

## Important Notes

- Always confirm destructive operations (remote deletions) with the user
- Skip branches that are already in `archive/` or `wip/` namespaces
- Handle branches that only exist locally or only on remote
- If a branch has no remote tracking, note this in the report
- Preserve the current checked-out branch (cannot delete/rename it while on it)
