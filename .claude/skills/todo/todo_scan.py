#!/usr/bin/env python3
"""
Todo Scanner - Scans codebase for TODO/CLAUDE comments and checks GitHub Issues.

GitHub-only: no local todo files. All tracking is via GitHub Issues.

Usage:
    python .claude/skills/todo/todo_scan.py [--json] [--sync]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TodoItem:
    """A TODO found in code."""
    file: str
    line: int
    marker: str  # TODO or CLAUDE
    issue_id: str | None  # #123 or None
    content: str


def find_project_root() -> Path:
    """Find project root by looking for .git or .claude folder."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / '.git').exists() or (current / '.claude').exists():
            return current
        current = current.parent
    return Path.cwd()


def scan_code_todos(directories: list[str], project_root: Path) -> list[TodoItem]:
    """Scan directories for TODO: and CLAUDE: comments."""
    todos: list[TodoItem] = []
    pattern = re.compile(
        r'#\s*(TODO|CLAUDE)\s*(?:\[([^\]]+)\])?\s*:?\s*(.*)$',
        re.IGNORECASE
    )

    for directory in directories:
        dir_path = project_root / directory
        if not dir_path.exists():
            continue

        for file_path in dir_path.rglob('*.py'):
            if '__pycache__' in str(file_path) or '.venv' in str(file_path):
                continue

            try:
                lines = file_path.read_text(encoding='utf-8').splitlines()
            except (UnicodeDecodeError, PermissionError):
                continue

            for i, line in enumerate(lines):
                match = pattern.search(line)
                if match:
                    marker = match.group(1).upper()
                    issue_id = match.group(2)
                    content = match.group(3).strip()
                    rel_path = str(file_path.relative_to(project_root))

                    todos.append(TodoItem(
                        file=rel_path,
                        line=i + 1,
                        marker=marker,
                        issue_id=issue_id,
                        content=content,
                    ))

    return todos


def get_github_issues(state: str = "open") -> list[dict]:
    """Get GitHub issues with todo label."""
    try:
        result = subprocess.run(
            ['gh', 'issue', 'list', '--label', 'todo', '--state', state,
             '--limit', '200', '--json', 'number,title,state,labels'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def check_sync(code_todos: list[TodoItem], github_issues: list[dict]) -> dict:
    """Check for inconsistencies between code TODOs and GitHub Issues."""
    github_by_num: dict[str, dict] = {str(i['number']): i for i in github_issues}

    code_with_code_label = {
        str(i['number']): i for i in github_issues
        if any(la.get('name') == 'todo:code' for la in i.get('labels', []))
    }

    stale: list[dict] = []
    missing_in_github: list[dict] = []
    synced = 0
    code_refs: set[str] = set()

    for todo in code_todos:
        if not todo.issue_id:
            continue
        num = todo.issue_id.lstrip('#')
        if not num.isdigit():
            continue
        code_refs.add(num)

        issue = github_by_num.get(num)
        if not issue:
            missing_in_github.append({
                'file': todo.file, 'line': todo.line,
                'issue_id': todo.issue_id, 'reason': 'issue does not exist or is closed'
            })
        elif issue.get('state') == 'CLOSED':
            stale.append({
                'file': todo.file, 'line': todo.line,
                'issue_id': todo.issue_id, 'title': issue.get('title', '')
            })
        else:
            synced += 1

    # GitHub issues with todo:code but no code reference
    missing_in_code: list[dict] = []
    for num, issue in code_with_code_label.items():
        if num not in code_refs and issue.get('state') != 'CLOSED':
            missing_in_code.append({'number': issue['number'], 'title': issue['title']})

    return {
        'stale': stale,
        'missing_in_github': missing_in_github,
        'missing_in_code': missing_in_code,
        'synced': synced,
    }


def print_report(code_todos: list[TodoItem], github_issues: list[dict]) -> None:
    """Print human-readable report."""
    print("=" * 60)
    print("TODO SCAN REPORT")
    print("=" * 60)
    print()

    github_nums = {str(i['number']) for i in github_issues}
    with_id = [t for t in code_todos if t.issue_id]
    without_id = [t for t in code_todos if not t.issue_id]
    in_github = [t for t in with_id if t.issue_id and t.issue_id.lstrip('#') in github_nums]
    not_in_github = [t for t in with_id if t not in in_github]

    # Count priorities
    high = sum(1 for i in github_issues if any(la.get('name') == 'priority:high' for la in i.get('labels', [])))
    med = sum(1 for i in github_issues if any(la.get('name') == 'priority:medium' for la in i.get('labels', [])))
    low = sum(1 for i in github_issues if any(la.get('name') == 'priority:low' for la in i.get('labels', [])))
    in_prog = sum(1 for i in github_issues if any(la.get('name') == 'in-progress' for la in i.get('labels', [])))

    print(f"GitHub Issues (open): {len(github_issues)} ({high} high, {med} medium, {low} low)")
    print(f"In Progress: {in_prog}")
    print(f"Code TODOs: {len(code_todos)} ({len(in_github)} tracked, {len(without_id)} untracked)")
    print()

    if without_id:
        print("-" * 60)
        print("UNTRACKED CODE TODOs (no GitHub issue)")
        print("-" * 60)
        for todo in without_id:
            print(f"  {todo.file}:{todo.line}")
            print(f"    {todo.marker}: {todo.content}")
        print()

    if not_in_github:
        print("-" * 60)
        print("CODE TODOs WITH ID NOT IN GITHUB")
        print("-" * 60)
        for todo in not_in_github:
            print(f"  [{todo.issue_id}] {todo.file}:{todo.line} - {todo.content[:60]}")
        print()

    if in_github:
        print("-" * 60)
        print("TRACKED CODE TODOs")
        print("-" * 60)
        for todo in in_github:
            print(f"  [{todo.issue_id}] {todo.file}:{todo.line} - {todo.content[:60]}")
        print()


def print_sync_report(sync: dict) -> None:
    """Print sync report."""
    print("=" * 60)
    print("SYNC REPORT")
    print("=" * 60)
    print()

    has_issues = False

    if sync['stale']:
        has_issues = True
        print(f"Stale TODOs (reference closed issues) ({len(sync['stale'])}):")
        for item in sync['stale']:
            print(f"  {item['file']}:{item['line']} - [{item['issue_id']}] \"{item['title']}\" - CLOSED")
        print()

    if sync['missing_in_github']:
        has_issues = True
        print(f"Code TODOs missing in GitHub ({len(sync['missing_in_github'])}):")
        for item in sync['missing_in_github']:
            print(f"  {item['file']}:{item['line']} - [{item['issue_id']}] {item['reason']}")
        print()

    if sync['missing_in_code']:
        has_issues = True
        print(f"GitHub issues with todo:code but no code reference ({len(sync['missing_in_code'])}):")
        for item in sync['missing_in_code']:
            print(f"  #{item['number']} \"{item['title']}\"")
        print()

    if not has_issues:
        print("No inconsistencies found!")
        print()

    print(f"Synced: {sync['synced']} code TODOs")


def main() -> int:
    parser = argparse.ArgumentParser(description='Scan codebase for TODOs (GitHub-only)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--sync', action='store_true', help='Check sync between code and GitHub')
    args = parser.parse_args()

    project_root = find_project_root()
    code_todos = scan_code_todos(['src', 'tests', 'docs'], project_root)

    if args.sync:
        # For sync, get both open and closed issues
        all_issues = get_github_issues('all')
        sync = check_sync(code_todos, all_issues)
        if args.json:
            print(json.dumps(sync, indent=2))
        else:
            print_sync_report(sync)
        return 0

    github_issues = get_github_issues('open')

    if args.json:
        output = {
            'code_todos': [asdict(t) for t in code_todos],
            'github_issues_count': len(github_issues),
            'untracked': len([t for t in code_todos if not t.issue_id]),
            'tracked': len([t for t in code_todos if t.issue_id]),
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(code_todos, github_issues)

    return 0


if __name__ == '__main__':
    sys.exit(main())
