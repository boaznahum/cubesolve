#!/usr/bin/env python3
"""
Branch analysis script for clean-branches skill.
Analyzes git branches and generates a cleanup report.

Usage:
    python analyze_branches.py                    # Compare against default branch
    python analyze_branches.py --target main      # Compare against 'main'
    python analyze_branches.py --target HEAD      # Compare against current branch
    python analyze_branches.py --list-branches    # List available branches for selection
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class BranchInfo:
    name: str
    is_local: bool
    is_remote: bool
    last_commit_hash: str
    last_commit_msg: str
    last_commit_age: str
    contained_in: list[str]
    is_archived: bool
    namespace: str  # 'zzarchive/completed', 'zzarchive/stopped', 'zzarchive/claudez', 'wip', 'feature', or ''
    ff_relation: str  # 'same', 'behind' (contained in target), 'ahead' (target FF to branch), 'diverged'
    ahead_behind: str  # e.g. "3 ahead, 2 behind" relative to target
    worktree_path: str  # path if checked out in a worktree, else ''


def run_git(args: list[str], check: bool = True) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=check,
    )
    return result.stdout.strip()


def get_default_branch() -> str:
    """Get the default branch name."""
    try:
        # Try gh first
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to git remote show
        output = run_git(["remote", "show", "origin"])
        for line in output.splitlines():
            if "HEAD branch:" in line:
                return line.split(":")[-1].strip()
    return "main"


def get_local_branches() -> list[str]:
    """Get list of local branch names."""
    output = run_git(["branch", "--list", "--format=%(refname:short)"])
    return [b for b in output.splitlines() if b]


def get_remote_branches() -> list[str]:
    """Get list of remote branch names (without origin/ prefix)."""
    output = run_git(["branch", "-r", "--format=%(refname:short)"])
    branches = []
    for b in output.splitlines():
        if b and not b.endswith("/HEAD"):
            # Remove 'origin/' prefix
            if b.startswith("origin/"):
                branches.append(b[7:])
    return branches


def get_current_branch() -> str:
    """Get the current branch name."""
    return run_git(["branch", "--show-current"])


def get_commit_info(ref: str) -> tuple[str, str, str]:
    """Get (hash, message, age) for a ref."""
    try:
        output = run_git(["log", "-1", "--format=%h|%s|%cr", ref])
        parts = output.split("|", 2)
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
    except subprocess.CalledProcessError:
        pass
    return "", "", ""


def is_ancestor(branch: str, target: str) -> bool:
    """Check if branch is an ancestor of (contained in) target."""
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", branch, target],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_ff_relation(ref: str, target: str) -> tuple[str, str]:
    """Determine fast-forward relationship between ref and target.

    Returns (relation, ahead_behind) where relation is one of:
    - 'same': ref and target point to the same commit
    - 'behind': ref is ancestor of target (contained in target)
    - 'ahead': target is ancestor of ref (target can FF to ref)
    - 'diverged': neither is ancestor of the other
    """
    # Check if same commit
    try:
        ref_sha = run_git(["rev-parse", ref])
        target_sha = run_git(["rev-parse", target])
        if ref_sha == target_sha:
            return "same", "0 ahead, 0 behind"
    except subprocess.CalledProcessError:
        return "diverged", "unknown"

    # Get ahead/behind counts
    try:
        output = run_git(["rev-list", "--left-right", "--count", f"{target}...{ref}"])
        parts = output.split()
        if len(parts) == 2:
            behind = int(parts[0])  # commits in target not in ref
            ahead = int(parts[1])   # commits in ref not in target
            ahead_behind = f"{ahead} ahead, {behind} behind"

            if ahead == 0 and behind == 0:
                return "same", ahead_behind
            elif ahead == 0:
                return "behind", ahead_behind
            elif behind == 0:
                return "ahead", ahead_behind
            else:
                return "diverged", ahead_behind
    except subprocess.CalledProcessError:
        pass

    # Fallback to merge-base checks
    branch_in_target = is_ancestor(ref, target)
    target_in_branch = is_ancestor(target, ref)

    if branch_in_target and target_in_branch:
        return "same", "0 ahead, 0 behind"
    elif branch_in_target:
        return "behind", "unknown"
    elif target_in_branch:
        return "ahead", "unknown"
    else:
        return "diverged", "unknown"


def get_worktree_branches() -> dict[str, str]:
    """Return a mapping of branch name -> worktree path for branches checked out in worktrees."""
    try:
        output = run_git(["worktree", "list", "--porcelain"])
    except subprocess.CalledProcessError:
        return {}

    result: dict[str, str] = {}
    current_path = ""
    for line in output.splitlines():
        if line.startswith("worktree "):
            current_path = line[len("worktree "):]
        elif line.startswith("branch refs/heads/"):
            branch_name = line[len("branch refs/heads/"):]
            result[branch_name] = current_path
    return result


def _archive_name(branch_name: str, category: str = "completed") -> str:
    """Build the archive destination for a branch.

    claude/ branches go to zzarchive/claudez/ (so searching 'claude/' won't find them).
    All other branches go to zzarchive/<category>/<name>.
    """
    if branch_name.startswith("claude/"):
        # claude/foo-bar -> zzarchive/claudez/foo-bar
        return f"zzarchive/claudez/{branch_name[len('claude/'):]}"
    return f"zzarchive/{category}/{branch_name}"


def get_namespace(branch: str) -> str:
    """Extract namespace from branch name."""
    if branch.startswith("zzarchive/completed/"):
        return "zzarchive/completed"
    if branch.startswith("zzarchive/stopped/"):
        return "zzarchive/stopped"
    if branch.startswith("zzarchive/claudez/"):
        return "zzarchive/claudez"
    if branch.startswith("zzarchive/"):
        return "zzarchive"
    if branch.startswith("wip/"):
        return "wip"
    if branch.startswith("feature/"):
        return "feature"
    return ""


def find_contained_in(branch: str, ref: str, all_branches: list[str], default_branch: str) -> list[str]:
    """Find which branches contain this branch."""
    contained = []

    # Check default branch first
    if is_ancestor(ref, default_branch):
        contained.append(default_branch)

    # Check other important branches
    for target in all_branches:
        if target == branch:
            continue
        if target == default_branch:
            continue
        # Check archived branches
        if target.startswith("zzarchive/"):
            target_ref = f"origin/{target}"
            if is_ancestor(ref, target_ref):
                contained.append(target)

    return contained


def _update_compare_branch(compare_branch: str, current_branch: str, local_branches: list[str]) -> str:
    """Update the compare branch to match its remote tracking branch.

    Returns a status message describing what happened.
    """
    # Check if remote exists for compare branch
    try:
        run_git(["ls-remote", "--heads", "origin", compare_branch])
    except subprocess.CalledProcessError:
        return f"WARNING: No remote for {compare_branch}, using local state"

    remote_ref = f"origin/{compare_branch}"

    # Check if remote ref exists locally (was fetched)
    try:
        run_git(["rev-parse", "--verify", remote_ref])
    except subprocess.CalledProcessError:
        return f"WARNING: Remote ref {remote_ref} not found locally"

    if compare_branch not in local_branches:
        # No local branch - we'll compare against origin/compare_branch
        # Nothing to update, but we need to use the remote ref for comparison
        return f"Using remote {remote_ref} (no local branch)"

    # Check if local is behind remote
    try:
        local_sha = run_git(["rev-parse", compare_branch])
        remote_sha = run_git(["rev-parse", remote_ref])
    except subprocess.CalledProcessError:
        return f"WARNING: Could not resolve refs for {compare_branch}"

    if local_sha == remote_sha:
        return f"{compare_branch} is up to date with remote"

    # Local differs from remote - try to fast-forward
    if compare_branch == current_branch:
        # Currently on this branch - try git pull --ff-only
        try:
            run_git(["merge", "--ff-only", remote_ref])
            return f"Fast-forwarded {compare_branch} to match remote"
        except subprocess.CalledProcessError:
            # Can't FF - local has diverged
            return (f"WARNING: {compare_branch} has diverged from remote! "
                    f"Using local state (may give incorrect results). "
                    f"Consider: git pull --rebase")
    else:
        # Not on this branch - update the ref directly
        if is_ancestor(compare_branch, remote_ref):
            # Local is behind remote - safe to fast-forward
            try:
                run_git(["update-ref", f"refs/heads/{compare_branch}", remote_sha])
                return f"Updated {compare_branch} to match remote (was behind)"
            except subprocess.CalledProcessError:
                return f"WARNING: Could not update {compare_branch} ref"
        elif is_ancestor(remote_ref, compare_branch):
            # Local is ahead of remote - unusual but not an error
            return f"WARNING: Local {compare_branch} is ahead of remote"
        else:
            # Diverged
            return (f"WARNING: {compare_branch} has diverged from remote! "
                    f"Using local state (may give incorrect results)")


def analyze_branches(target_branch: str | None = None) -> dict:
    """Analyze all branches and return report data.

    Args:
        target_branch: Branch to compare against. If None, uses the default branch.
    """
    print("Fetching branches...", file=sys.stderr)
    run_git(["fetch", "--all", "--prune"])

    default_branch = get_default_branch()
    current_branch = get_current_branch()
    local_branches = get_local_branches()
    remote_branches = get_remote_branches()

    # Use target_branch if specified, otherwise use default branch
    compare_branch = target_branch if target_branch else default_branch

    # Update the compare branch to match remote before analysis
    update_status = _update_compare_branch(compare_branch, current_branch, local_branches)
    if update_status:
        print(update_status, file=sys.stderr)

    all_branch_names = set(local_branches) | set(remote_branches)
    worktree_map = get_worktree_branches()

    branches: list[BranchInfo] = []

    print(f"Analyzing {len(all_branch_names)} branches...", file=sys.stderr)

    for name in sorted(all_branch_names):
        is_local = name in local_branches
        is_remote = name in remote_branches
        namespace = get_namespace(name)
        is_archived = namespace.startswith("zzarchive")

        # Get ref to use for analysis
        if is_local:
            ref = name
        else:
            ref = f"origin/{name}"

        commit_hash, commit_msg, commit_age = get_commit_info(ref)

        # Only check containment for non-archived branches
        if is_archived:
            contained_in = []
        else:
            contained_in = find_contained_in(name, ref, remote_branches, compare_branch)

        # Get fast-forward relationship to compare branch
        if name == compare_branch:
            ff_relation, ahead_behind = "same", "0 ahead, 0 behind"
        elif is_archived:
            ff_relation, ahead_behind = "", ""
        else:
            ff_relation, ahead_behind = get_ff_relation(ref, compare_branch)

        branches.append(BranchInfo(
            name=name,
            is_local=is_local,
            is_remote=is_remote,
            last_commit_hash=commit_hash,
            last_commit_msg=commit_msg[:50] + "..." if len(commit_msg) > 50 else commit_msg,
            last_commit_age=commit_age,
            contained_in=contained_in,
            is_archived=is_archived,
            namespace=namespace,
            ff_relation=ff_relation,
            ahead_behind=ahead_behind,
            worktree_path=worktree_map.get(name, ""),
        ))

    return {
        "default_branch": default_branch,
        "current_branch": current_branch,
        "compare_branch": compare_branch,
        "branches": branches,
    }


def print_report(data: dict) -> None:
    """Print the branch analysis report."""
    default_branch = data["default_branch"]
    current_branch = data["current_branch"]
    compare_branch = data["compare_branch"]
    branches = data["branches"]

    print(f"\n## Branch Analysis Report\n")
    print(f"**Default branch:** `{default_branch}`")
    print(f"**Current branch:** `{current_branch}`")
    print(f"**Comparing against:** `{compare_branch}`")

    # Separate by category
    active = [b for b in branches if not b.is_archived and b.namespace not in ("wip",)]
    wip = [b for b in branches if b.namespace == "wip"]
    archived = [b for b in branches if b.is_archived]

    # Standard branches that should always be kept
    standard_branches = {"main", "master", "develop", "dev"}

    # Active branches
    print(f"\n### Active Branches ({len(active)})\n")
    print(f"Comparing against `{compare_branch}`\n")
    if active:
        print("| Branch | Local | Remote | Last Commit | Age | Status | Action |")
        print("|--------|-------|--------|-------------|-----|--------|--------|")

        for b in active:
            local = "Yes" if b.is_local else "No"
            remote = "Yes" if b.is_remote else "No"

            # Status: clear human-readable description of relationship to target
            if b.ff_relation == "same":
                status = "= identical to target"
            elif b.ff_relation == "behind":
                status = "ALL work in target"
            elif b.ff_relation == "ahead":
                # Parse ahead count for clarity
                ahead_count = ""
                if b.ahead_behind and b.ahead_behind != "unknown":
                    parts = b.ahead_behind.split(", ")
                    if len(parts) == 2:
                        ahead_count = parts[0].split()[0]
                status = f"NOT in target ({ahead_count} unique commits)"
            elif b.ff_relation == "diverged":
                # Parse counts
                ahead_count = ""
                behind_count = ""
                if b.ahead_behind and b.ahead_behind != "unknown":
                    parts = b.ahead_behind.split(", ")
                    if len(parts) == 2:
                        ahead_count = parts[0].split()[0]
                        behind_count = parts[1].split()[0]
                status = f"NOT in target ({ahead_count} unique, {behind_count} missing)"
            else:
                status = "-"

            # Determine recommended action
            wt_note = f" WORKTREE: {b.worktree_path}" if b.worktree_path else ""
            if b.name == compare_branch:
                action = "Keep (target)"
            elif b.name == default_branch:
                action = "Keep (default)"
            elif b.name == current_branch:
                action = "Keep (current)"
            elif b.name in standard_branches:
                action = "Keep (standard)"
            elif b.ff_relation in ("behind", "same"):
                # All work is in the target - safe to delete
                if b.is_local and not b.is_remote:
                    action = "Delete local (work in target)" + wt_note
                elif b.is_local and b.is_remote:
                    action = "Delete both (work in target)" + wt_note
                else:
                    action = "Delete remote (work in target)"
            elif b.contained_in:
                if b.is_local and not b.is_remote:
                    action = "Delete local (in " + b.contained_in[0] + ")" + wt_note
                else:
                    action = "Archive? (in " + b.contained_in[0] + ")"
            else:
                action = "Review (work NOT in target)"

            print(f"| `{b.name}` | {local} | {remote} | {b.last_commit_hash} {b.last_commit_msg} | {b.last_commit_age} | {status} | {action} |")
    else:
        print("*No active branches*")

    # WIP branches
    print(f"\n### Work in Progress ({len(wip)})\n")
    if wip:
        print("| Branch | Last Commit | Age | Contained In | Action |")
        print("|--------|-------------|-----|--------------|--------|")
        for b in wip:
            contained = ", ".join(b.contained_in) if b.contained_in else "-"
            if compare_branch in b.contained_in:
                action = f"-> zzarchive/completed (merged to {compare_branch})"
            elif b.contained_in:
                action = f"Review (in {b.contained_in[0]})"
            else:
                action = "Keep (active)"
            print(f"| `{b.name}` | {b.last_commit_hash} {b.last_commit_msg} | {b.last_commit_age} | {contained} | {action} |")
    else:
        print("*No WIP branches*")

    # Archived summary
    print(f"\n### Archived ({len(archived)})\n")
    completed = [b for b in archived if b.namespace == "zzarchive/completed"]
    stopped = [b for b in archived if b.namespace == "zzarchive/stopped"]
    other = [b for b in archived if b.namespace == "zzarchive"]

    print(f"- **Completed:** {len(completed)}")
    print(f"- **Stopped:** {len(stopped)}")
    print(f"- **Other:** {len(other)}")

    # Recommendations
    skip_branches = {default_branch, current_branch, compare_branch}
    needs_action = [b for b in active if b.name not in skip_branches and b.name not in standard_branches]

    # WIP branches that are merged to compare branch need action
    wip_needs_action = [b for b in wip if compare_branch in b.contained_in]

    if needs_action or wip_needs_action:
        print(f"\n### Recommendations\n")

        # WIP branches merged to compare branch
        for b in wip_needs_action:
            short_name = b.name.replace("wip/", "")
            archive_name = _archive_name(short_name)
            print(f"- `{b.name}`: **Merged to {compare_branch}** -> move to `{archive_name}`")

        # Active branches
        for b in needs_action:
            work_in_target = b.ff_relation in ("behind", "same")
            if work_in_target:
                loc = "local-only" if (b.is_local and not b.is_remote) else ("remote-only" if (not b.is_local) else "local+remote")
                print(f"- `{b.name}`: [{loc}] Work IS in `{compare_branch}` - **safe to delete**")
            elif b.contained_in:
                loc = "local-only" if (b.is_local and not b.is_remote) else ("remote-only" if (not b.is_local) else "local+remote")
                print(f"- `{b.name}`: [{loc}] Work IS in `{b.contained_in[0]}` - **safe to delete**")
            else:
                loc = "local-only" if (b.is_local and not b.is_remote) else ("remote-only" if (not b.is_local) else "local+remote")
                print(f"- `{b.name}`: [{loc}] Work NOT in `{compare_branch}` - keep, move to wip/, or archive")

    # Worktree warnings
    worktree_branches = [b for b in branches if b.worktree_path and b.name != current_branch]
    if worktree_branches:
        print(f"\n### Branches Checked Out in Worktrees (cannot delete)\n")
        print("These branches cannot be deleted until detached from their worktree.\n")
        print("**To detach, run:**\n")
        print("```bash")
        for b in worktree_branches:
            print(f"git -C \"{b.worktree_path}\" checkout --detach")
        print("```\n")
        print("After detaching, you can delete the branches normally, or remove the worktree entirely:\n")
        print("```bash")
        for b in worktree_branches:
            print(f"git worktree remove \"{b.worktree_path}\"  # removes worktree + detaches branch")
        print("```")


def list_branches_for_selection() -> None:
    """List branches available for selection as target."""
    print("Fetching branches...", file=sys.stderr)
    run_git(["fetch", "--all", "--prune"])

    default_branch = get_default_branch()
    current_branch = get_current_branch()
    local_branches = get_local_branches()
    remote_branches = get_remote_branches()

    print("\n## Available Target Branches\n")
    print(f"**Default branch:** `{default_branch}`")
    print(f"**Current branch:** `{current_branch}`")

    print("\n### Local Branches")
    for b in sorted(local_branches):
        marker = ""
        if b == default_branch:
            marker = " (default)"
        elif b == current_branch:
            marker = " (current)"
        print(f"  - `{b}`{marker}")

    # Show remote-only branches
    remote_only = set(remote_branches) - set(local_branches)
    if remote_only:
        print("\n### Remote-Only Branches")
        for b in sorted(remote_only):
            if not b.startswith("zzarchive/"):
                print(f"  - `origin/{b}`")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze git branches for cleanup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_branches.py                    # Compare against default branch
  python analyze_branches.py --target main      # Compare against 'main'
  python analyze_branches.py --target HEAD      # Compare against current branch
  python analyze_branches.py --list-branches    # List available branches
        """,
    )
    parser.add_argument(
        "--target", "-t",
        help="Branch to compare against (use HEAD for current branch)",
    )
    parser.add_argument(
        "--list-branches", "-l",
        action="store_true",
        help="List available branches for selection",
    )
    args = parser.parse_args()

    if args.list_branches:
        list_branches_for_selection()
        return

    # Resolve target branch
    target_branch: str | None = args.target
    if target_branch == "HEAD":
        target_branch = get_current_branch()

    data = analyze_branches(target_branch)
    print_report(data)


if __name__ == "__main__":
    main()
