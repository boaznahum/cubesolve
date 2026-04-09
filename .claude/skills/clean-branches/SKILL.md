---
name: clean-branches
user_invocable: true
context: conversation
description: |
  Clean up git branches by analyzing merged/unmerged status and archiving completed work.
  Triggered by "/clean-branches" or "/branches".
---

# Branch Cleanup Skill

This skill provides an iterative workflow for cleaning up git branches by analyzing their merge status and organizing them into appropriate namespaces.

**CRITICAL RULES:**
1. **NEVER just delete branches.** Always offer ARCHIVE as the first/recommended option for merged branches.
2. **Follow the FULL workflow** including archive steps — do not shortcut to deletion.
3. **Run the analysis script** — do not do ad-hoc analysis with a separate agent.
4. **PROTECTED BRANCHES — NEVER archive or delete:** `main`, `dev`, `webgl-dev`, 'p314'. Always skip these in analysis and actions regardless of merge status.

## Step 0: Determine Target Branch

**If the user provided a branch name as an argument** (e.g., `/clean-branches webgl-dev`), use that directly — skip the question.

**If no argument was provided**, ask the user which branch to compare against:

1. **Default branch** - Compare against the repository's default branch (usually `main`)
2. **Current branch** - Compare against the currently checked-out branch
3. **Other branch** - Let user specify a different branch name

Show the user the current and default branch names in the question so they know what they're choosing.

To get branch info for the question:
```bash
# Get default branch
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'

# Get current branch
git branch --show-current
```

## Quick Start - Run Analysis Script

After determining the target branch, run the analysis script with the `--target` flag:

```bash
# Compare against default branch (or omit --target)
python .claude/skills/clean-branches/analyze_branches.py

# Compare against a specific branch
python .claude/skills/clean-branches/analyze_branches.py --target <branch-name>

# Compare against current branch
python .claude/skills/clean-branches/analyze_branches.py --target HEAD
```

This script:
- Fetches all branches and analyzes merge/containment status
- Outputs a formatted markdown report showing which branch is being compared against
- Identifies branches needing action with recommendations

After reviewing the output, proceed with user approval for any actions (delete, move, archive).

## Branch Organization Schema

| Namespace | Purpose | Example |
|-----------|---------|---------|
| `zzarchive/completed/<name>` | Merged branches (work completed) | `zzarchive/completed/feature-login` |
| `zzarchive/stopped/<name>` | Unmerged branches (abandoned work) | `zzarchive/stopped/experiment-x` |
| `zzarchive/claudez/<name>` | Archived claude/ branches | `zzarchive/claudez/fix-bug-abc123` |
| `wip/<name>` | Work in progress (active development) | `wip/new-feature` |
| (root) | Keep as-is | `feature-y` |

**Special naming rules:**
- `claude/` branches are archived to `zzarchive/claudez/` (not `zzarchive/claude/`) so searching for `claude/` won't find archived branches
- All archive branches use `zzarchive/` prefix (sorts to bottom of branch list)

## Workflow

### Step 1: Identify Target Branch

The target branch was selected in Step 0. If you need to query the default branch:

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

### Step 4: Analyze Local Branches

For each LOCAL branch (excluding the target branch and already-archived branches):

1. **Check if merged** into target branch:
   ```bash
   git branch --merged <target-branch> | grep -q <branch-name>
   ```

2. **Get last commit info**:
   ```bash
   git log -1 --format="%h %s (%cr by %an)" <branch-name>
   ```

3. **Check if remote exists**:
   ```bash
   git ls-remote --heads origin <branch-name>
   ```

4. **CRITICAL: For local-only branches, check if contained in other branches**:

   If a branch has no remote, check if its commits are already contained in the target branch or any archived branch:

   ```bash
   # Check if branch is ancestor of (contained in) target branch
   git merge-base --is-ancestor <branch> <target-branch> && echo "Contained in target"

   # Check if branch is ancestor of any archived branch
   for archived in $(git branch -r | grep "origin/zzarchive/"); do
     git merge-base --is-ancestor <branch> $archived 2>/dev/null && echo "Contained in $archived"
   done

   # Alternative: show all branches that contain this branch's HEAD
   git branch -a --contains <branch>
   ```

   **Interpretation:**
   - If contained in the target branch → Work was merged, safe to delete local branch
   - If contained in `zzarchive/completed/*` → Work was completed, safe to delete local branch
   - If contained in `zzarchive/stopped/*` → Work was archived, safe to delete local branch
   - If NOT contained anywhere → Work may be lost if deleted, ask user carefully

### Step 5: Analyze Remote-Only Branches (CRITICAL!)

**This step is often missed!** Check remote branches that have NO local copy and are NOT already archived:

```bash
# List remote branches not merged into target branch
git branch -r --no-merged <target-branch> | grep -v HEAD | grep -v "zzarchive/" | grep -v "wip/"
```

For each remote-only branch found:

1. **Get last commit info**:
   ```bash
   git log -1 --format="%h %s (%cr by %an)" origin/<branch-name>
   ```

2. **Check if contained in target branch or other branches**:
   ```bash
   # Check what branches contain this remote branch
   git branch -a --contains origin/<branch-name>
   ```

3. **Check merge status**:
   ```bash
   # Is it merged into the target branch?
   git merge-base --is-ancestor origin/<branch-name> <target-branch> && echo "Merged into target"

   # Is it merged into the current working branch?
   git merge-base --is-ancestor origin/<branch-name> HEAD && echo "Merged into HEAD"
   ```

**Actions for remote-only branches:**
- If contained in target branch → Move to `zzarchive/completed/` (work was merged)
- If contained in current branch but not target → Ask user (might be pending merge)
- If NOT contained anywhere → Ask user: zzarchive/stopped or keep for future work

```bash
# Move remote branch to zzarchive/completed (if merged)
git push origin origin/<branch>:refs/heads/zzarchive/completed/<branch>
git push origin --delete <branch>

# Move remote branch to zzarchive/stopped (if abandoned)
git push origin origin/<branch>:refs/heads/zzarchive/stopped/<branch>
git push origin --delete <branch>
```

### Step 6: Generate Report

Present a summary table to the user:

| Branch | Status | Last Commit | Age | Remote | Contained In | Recommendation |
|--------|--------|-------------|-----|--------|--------------|----------------|
| feature-x | Merged | abc123 Fix bug | 2 weeks | Yes | target | → delete local (work in target) |
| experiment-y | Unmerged | def456 WIP | 3 months | No | zzarchive/stopped/exp-y | → delete local (already archived) |
| new-feature | Unmerged | ghi789 Add X | 1 day | No | (none) | → ask user: WIP/stop/keep |

**Key insight:** If "Contained In" shows the target branch or another branch, the work is NOT lost - it's safe to delete the local branch.

### Step 7: Delete Contained Local-Only Branches

For local branches that have no remote but ARE contained in another branch (target branch or zzarchive/*), the work is already preserved elsewhere. These can be safely deleted:

```bash
# Delete local branch that's already contained in target or archive
git branch -d <branch>
```

**Note:** Use `-d` (not `-D`) which will fail if the branch isn't actually merged/contained - this is a safety check.

### Step 7.5: Handle Branches Checked Out in Worktrees

If `git branch -d` fails with "cannot delete branch used by worktree", the branch is checked out in another worktree. The analysis script detects this and shows the worktree path.

**Options for worktree branches (present all three to user):**

```bash
# Option 1: Detach HEAD + delete branch (Recommended if branch is merged)
# Keeps the worktree intact, just frees the branch
git -C "<worktree-path>" checkout --detach
git branch -D <branch>
git push origin --delete <branch>  # if remote exists

# Option 2: Remove the worktree entirely + delete branch
# Use when the worktree is no longer needed
git worktree remove "<worktree-path>"
git branch -D <branch>
git push origin --delete <branch>  # if remote exists

# Option 3: Keep as-is
# Leave worktree and branch alone
```

**IMPORTANT:** Always ask the user which option they prefer. The worktree may contain uncommitted work. Present "Detach + delete branch" as the recommended option when the branch is merged, since it preserves the worktree directory while cleaning up the branch.

### Step 8: Process Merged Branches (with remotes)

**CRITICAL: ALWAYS archive first, NEVER just delete.** This is the most important step.

For branches that have remotes and are confirmed as merged, offer these options:

**Options (in order of preference):**
1. **Archive remote + delete local** (Recommended — DEFAULT) - Move remote to archive namespace, delete local copy
2. **Delete both** - Delete both local and remote (work already in target branch)
3. **Keep** - Leave as-is

**NEVER skip this step. NEVER just `git push origin --delete` without offering archive first.**

**Archive remote + delete local** (best option - preserves history on remote):
```bash
# Move remote branch to archive
git push origin origin/<branch>:refs/heads/zzarchive/completed/<branch>

# Delete old remote branch
git push origin --delete <branch>

# Delete local branch (if it exists)
git branch -D <branch>

# Prune stale remote-tracking refs
git fetch --prune

# Delete the new zzarchive remote-tracking ref (we don't want to track zzarchive/* locally)
git branch -dr origin/zzarchive/completed/<branch>   # or zzarchive/claudez/ for claude/ branches
```

**IMPORTANT: Clean up archive refs and [gone] branches.**

1. **Delete zzarchive remote-tracking refs** - The push creates a local ref `remotes/origin/zzarchive/*` that we don't need. Delete it with `git branch -dr`. The fetch refspec should exclude `zzarchive/*` so it won't be re-fetched:
   ```bash
   # Ensure zzarchive/* is excluded from fetch (one-time setup)
   git config --get-all remote.origin.fetch | grep -q 'zzarchive' || \
     git config --add remote.origin.fetch '^refs/heads/zzarchive/*'
   ```

2. **Run `/commit-commands:clean_gone`** - Deletes any local branches marked as `[gone]` (including associated worktrees).

`git fetch --prune` only removes refs for deleted remotes, NOT local branches or newly-pushed archive refs.

**Delete both** (when you don't need the branch history):
```bash
# Delete remote
git push origin --delete <branch>

# Delete local
git branch -D <branch>
```

### Step 9: Handle Truly Unmerged Branches

For each unmerged branch, ask the user using AskUserQuestion:

- **Try-merge + test**: Attempt to merge into base via temp branch, run tests, promote if green (see Step 9.5)
- **Keep**: Leave branch as-is
- **WIP**: Move to `wip/<branch-name>`
- **Stop**: Move to `zzarchive/stopped/<branch-name>`

Then execute the chosen action:

```bash
# For WIP
git branch -m <branch> wip/<branch>
git push origin wip/<branch>
git push origin --delete <branch>

# For Stop
git branch -m <branch> zzarchive/stopped/<branch>
git push origin zzarchive/stopped/<branch>
git push origin --delete <branch>
```

### Step 9.5: Try-Merge-And-Test Option

This option attempts to integrate an unmerged branch into the base branch *safely*: merge
into a throwaway temp branch, run the test suite, and only promote to the base branch if
tests pass. If anything fails, the base branch is untouched.

**Preconditions (check before starting):**

```bash
# Working tree MUST be clean — abort if not
git status --porcelain
# If non-empty, stop and tell the user to commit/stash first.

# Remember starting branch so we can return later
START_BRANCH=$(git branch --show-current)
```

**Per-branch workflow:**

```bash
BRANCH=<the-unmerged-branch>
BASE=<base-branch>                 # e.g. main / dev / p314
TMP="tmp/merge-test-$BRANCH"

# 1. Update base branch
git checkout "$BASE"
git pull --ff-only

# 2. Create temp branch from base
git checkout -b "$TMP" "$BASE"

# 3. Capture pre-merge SHA, then attempt the merge
PRE_MERGE_SHA=$(git rev-parse HEAD)
if ! git merge --no-ff "$BRANCH"; then
    git merge --abort
    git checkout "$BASE"
    git branch -D "$TMP"
    echo "MERGE CONFLICT on $BRANCH — falling back to Keep/WIP/Stop question"
    # Fall through to Step 9's Keep/WIP/Stop prompt for this branch
fi
POST_MERGE_SHA=$(git rev-parse HEAD)

# 3b. FAST-PATH: branch already fully contained in base.
#     If the merge produced no new commit (SHA unchanged), $BRANCH is an
#     ancestor of $BASE — its content is already identical to what's in
#     base. There is nothing new to test, no commit to tag, and no change
#     to push. Skip straight to the archive step.
#
#     Detection is SHA-based (not stderr parsing) so it's robust across
#     git versions and locales. --no-ff does NOT create an empty merge
#     commit when the incoming branch is an ancestor, so this check is
#     sound.
if [ "$POST_MERGE_SHA" = "$PRE_MERGE_SHA" ]; then
    echo "Already up to date — $BRANCH is fully contained in $BASE"
    echo "Skipping tests, tag, and push (no new content). Archiving directly."
    git checkout "$BASE"
    git branch -D "$TMP"
    # Skip to the shared archive block below by setting TEST_EXIT=0 and
    # MERGED_NEW=0. The archive block checks MERGED_NEW to decide whether
    # to tag/push; when 0, it only archives.
    TEST_EXIT=0
    MERGED_NEW=0
else
    MERGED_NEW=1

    # 4. Run tests (default: non-GUI, non-slow — matches CLAUDE.md "All Checks" §4)
    #    IMPORTANT: use -m (marker expression), NOT -k (keyword expression).
    #    Allow user to override the default test selector if asked.
    CUBE_QUIET_ALL=1 python -m pytest tests/ -v -m "not gui and not slow"
    TEST_EXIT=$?
fi

if [ "$TEST_EXIT" -eq 0 ]; then
    if [ "$MERGED_NEW" -eq 1 ]; then
        # 5a. Tests PASSED and merge produced a new commit — promote temp into base
        git checkout "$BASE"
        git merge --ff-only "$TMP"

        # Tag the passing commit per CLAUDE.md "Tagging Passing Commits"
        TAG="pass-$(date +%Y%m%d-%H%M%S)"
        git tag "$TAG"

        # AUTOMATIC push on green (user pre-approved via the "Try-merge + test" choice).
        # No per-branch confirmation: green tests = push base + tag.
        git push origin "$BASE"
        git push origin --tags

        # Clean up temp branch
        git branch -D "$TMP"
    fi
    # If MERGED_NEW=0, the temp branch was already deleted in the fast-path
    # above and $BASE is unchanged — skip straight to archiving.

    # Archive the original branch using the SAME workflow as Step 8
    # ("Archive remote + delete local"). Do not invent a new archive path here —
    # reuse the existing archive commands so behavior stays consistent with the
    # rest of the skill (including the zzarchive/* remote-tracking ref cleanup
    # and the [gone] branch cleanup hook in Step 8).
    #
    # Per Step 8, for claude/ branches use zzarchive/claudez/ instead of
    # zzarchive/completed/. Pick the archive prefix accordingly:
    case "$BRANCH" in
        claude/*) ARCHIVE_PREFIX="zzarchive/claudez" ;;
        *)        ARCHIVE_PREFIX="zzarchive/completed" ;;
    esac

    if git ls-remote --heads origin "$BRANCH" | grep -q .; then
        # Move remote branch to archive namespace
        git push origin "origin/$BRANCH:refs/heads/$ARCHIVE_PREFIX/$BRANCH"
        # Delete the old remote branch
        git push origin --delete "$BRANCH"
        # Prune stale remote-tracking refs (per Step 8)
        git fetch --prune
        # Drop the newly-created zzarchive remote-tracking ref — we don't
        # want to track zzarchive/* locally (per Step 8)
        git branch -dr "origin/$ARCHIVE_PREFIX/$BRANCH" 2>/dev/null || true
    fi
    # Delete the local branch copy (work is now in base AND archived on remote)
    git branch -D "$BRANCH" 2>/dev/null || true

    echo "✓ $BRANCH merged into $BASE, tagged $TAG, archived to $ARCHIVE_PREFIX/"
else
    # 5b. Tests FAILED — throw away the merge attempt entirely
    git checkout "$BASE"
    git branch -D "$TMP"
    echo "✗ Tests failed for $BRANCH — base branch untouched"
    # Fall through to Step 9's Keep/WIP/Stop question for this branch
fi

# 6. Return to starting branch before processing the next candidate
git checkout "$START_BRANCH"
```

**Critical safety rules for this option:**

1. **Automatic push on green.** Selecting "Try-merge + test" is itself the user's
   pre-approval for pushing the updated base branch and tags when tests pass. Do NOT
   prompt again per branch — just push. This is the one exception to the skill's
   general "ask before remote-visible actions" rule, because the test gate already
   guards the push.
2. **NEVER force-push** the base branch. Use `--ff-only` merges only. If the ff-only
   merge fails (because base moved during the test run), abort, delete temp, report,
   and fall back to Keep/WIP/Stop.
3. **Abort cleanly on conflict**: `git merge --abort`, delete temp, move on. Do not leave
   the user in a half-merged state.
4. **Honor protected branches** (Rule 4): never run this flow with `main`, `dev`, `webgl-dev`,
   or `p314` as the *candidate* branch — only as the *base*.
5. **Restore starting branch** at the end of each iteration, even on failure.
6. **Continue the loop**: after each branch (pass or fail), move on to the next candidate
   without prompting unless the user chose "Review each".
7. **Test command override**: the default is `-m "not gui and not slow"`. If the user asks
   for a different selector (e.g. include slow tests, or only a subset), use that instead.
8. **Archive via Step 8's workflow.** Do not invent ad-hoc archive commands in this step.
   The post-merge archive uses the same `zzarchive/completed/` (or `zzarchive/claudez/`
   for `claude/*`) pattern, the same fetch-prune, and the same remote-tracking ref
   cleanup as Step 8 so behavior stays consistent.
9. **Already-up-to-date fast-path.** If `git merge --no-ff "$BRANCH"` leaves HEAD
   unchanged (detected by SHA-equality of HEAD before/after the merge), the branch is
   already fully contained in base — its content is *identical* to what's already in
   base. In that case: skip tests (nothing new to validate), skip the `pass-*` tag (base
   didn't move, so any existing tag at that commit is still valid), skip the push, and
   go straight to archiving the original branch. This is the only scenario where Step 9.5
   skips the test run; do not extend the fast-path to other cases.

### Step 10: Clean Up Synced Archive Branches

Local archive branches that are synced with remote are redundant - they're safely backed up. Offer to delete them:

1. **Identify synced archive branches**:
   ```bash
   # Find local zzarchive branches that have matching remote
   for branch in $(git branch --list 'zzarchive/*'); do
     branch_name=$(echo "$branch" | sed 's/^[* ]*//')
     if git ls-remote --heads origin "$branch_name" | grep -q .; then
       echo "$branch_name"  # Has remote backup, safe to delete locally
     fi
   done
   ```

2. **Present to user**:
   | Local Archive Branch | Remote Status | Recommendation |
   |---------------------|---------------|----------------|
   | zzarchive/completed/feature-x | ✅ Synced | Delete local (backed up) |
   | zzarchive/image-bug | ✅ Synced | Delete local (backed up) |

3. **Offer bulk deletion**:
   Ask using AskUserQuestion:
   - **Delete all synced**: Remove all local zzarchive branches that have remote backups
   - **Review each**: Go through them one by one
   - **Keep all**: Leave local copies

4. **Execute deletion**:
   ```bash
   git branch -D <archive-branch>  # Safe - remote copy exists
   ```

### Step 11: Iterate

After processing, show updated branch list and ask if further cleanup is needed. Repeat until the user is satisfied.

## Important Notes

- **CRITICAL: EVERY action with side effects (delete, rename, move, push) MUST be approved by the user BEFORE execution**
- Query/read operations (git log, git branch --list, git branch --contains, etc.) do NOT require approval
- Even if analysis shows a branch is "safe to delete", still ask the user first
- Skip branches that are already in `zzarchive/` or `wip/` namespaces (no action needed)
- **Archive branches**: When analyzing, distinguish between:
  - Local-only archives: May want to push to remote first or delete
  - Synced archives: Safe to delete locally (backed up on remote)
  - Remote-only archives: No action needed (already clean locally)
- Handle branches that only exist locally or only on remote
- If a branch has no remote tracking, note this in the report
- Preserve the current checked-out branch (cannot delete/rename it while on it)

### User Approval Flow — USE AskUserQuestion TOOL

**CRITICAL: Use the `AskUserQuestion` tool for ALL decisions.** This presents a proper
selectable menu in the Claude Code UI where the user can scroll, choose, and press enter.

**Workflow after analysis:**

1. **Print the analysis report** as text output (branch tables, status, etc.)

2. **Use AskUserQuestion for merged branches** (one question):
   - Question: "How to handle N merged branches?" with header "Merged"
   - Options (up to 4):
     - "Archive all (Recommended)" — description: "Move to zzarchive/completed/ + delete local+remote"
     - "Delete all" — description: "Delete without archiving (work is in target)"
     - "Review each" — description: "Decide per branch"
     - "Skip" — description: "Keep all as-is"

3. **Use AskUserQuestion for EACH unmerged branch** (one question per branch):
   - Question: "What to do with `<branch>`? (N unique commits)" with header "<branch>"
   - Options (AskUserQuestion allows max 4 — pick the 4 most relevant; "Try-merge + test"
     should always be included for branches that look like real work):
     - "Try-merge + test" — description: "Merge into base via temp branch, run tests, promote if green (Step 9.5)"
     - "Archive stopped" — description: "Move to zzarchive/stopped/<branch>"
     - "Archive claudez" — description: "Move to zzarchive/claudez/<branch>" (for claude/ branches)
     - "Keep" — description: "Leave as-is"

4. **If "Review each" was selected for merged branches**, use AskUserQuestion per branch:
   - Question: "What to do with `<branch>`?" with header "<branch>"
   - Options:
     - "Archive (Recommended)" — description: "Move to zzarchive/completed/<branch>"
     - "Delete" — description: "Delete without archiving"
     - "Keep" — description: "Leave as-is"

5. **Execute** all chosen actions, then report results.

**You can batch up to 4 questions in a single AskUserQuestion call** using the questions
array. Use this to ask about multiple unmerged branches at once (max 4 per call).
