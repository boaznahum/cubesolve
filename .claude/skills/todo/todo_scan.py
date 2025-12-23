#!/usr/bin/env python3
"""
Todo Scanner - Scans codebase for TODO and CLAUDE comments.

Saves tokens by performing code scanning in Python instead of having Claude read all files.

Usage:
    python .claude/skills/todo/todo_scan.py [--json] [--untracked-only] [--no-github]
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
    issue_id: str | None  # #123 or TC1 or None
    content: str
    context_before: str
    context_after: str


@dataclass
class TodoFile:
    """A file with 'todo' in the name."""
    path: str
    has_new_entries: bool
    in_todo_folder: bool


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

    # Pattern: # TODO [ID]: text  or  # CLAUDE: text
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

                    context_before = '\n'.join(lines[max(0, i-2):i])
                    context_after = '\n'.join(lines[i+1:min(len(lines), i+3)])

                    rel_path = str(file_path.relative_to(project_root))

                    todos.append(TodoItem(
                        file=rel_path,
                        line=i + 1,
                        marker=marker,
                        issue_id=issue_id,
                        content=content,
                        context_before=context_before,
                        context_after=context_after
                    ))

    return todos


def find_todo_files(project_root: Path) -> list[TodoFile]:
    """Find all files with 'todo' in the filename."""
    todo_files: list[TodoFile] = []
    seen: set[str] = set()

    for pattern in ['**/*todo*', '**/*TODO*']:
        for file_path in project_root.glob(pattern):
            if file_path.is_dir():
                continue
            if '__pycache__' in str(file_path) or '.venv' in str(file_path):
                continue
            if '.git' in str(file_path):
                continue
            if '.claude' in str(file_path):
                continue

            rel_path = str(file_path.relative_to(project_root))
            if rel_path in seen:
                continue
            seen.add(rel_path)

            in_todo_folder = rel_path.startswith('todo/') or rel_path.startswith('todo\\')

            has_new_entries = False
            try:
                content = file_path.read_text(encoding='utf-8').lower()
                has_new_entries = 'new entries' in content or 'new entry' in content
            except (UnicodeDecodeError, PermissionError):
                pass

            todo_files.append(TodoFile(
                path=rel_path,
                has_new_entries=has_new_entries,
                in_todo_folder=in_todo_folder
            ))

    return todo_files


def get_github_issues() -> list[dict]:
    """Get list of GitHub issues with 'todo' label."""
    try:
        result = subprocess.run(
            ['gh', 'issue', 'list', '--label', 'todo', '--state', 'all',
             '--limit', '100', '--json', 'number,title,state,labels'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def print_report(
    code_todos: list[TodoItem],
    todo_files: list[TodoFile],
    github_issues: list[dict],
    untracked_only: bool = False
) -> None:
    """Print human-readable report."""
    print("=" * 60)
    print("TODO SCAN REPORT")
    print("=" * 60)
    print()

    with_id = [t for t in code_todos if t.issue_id]
    without_id = [t for t in code_todos if not t.issue_id]

    # Check which IDs are GitHub issue numbers (start with #)
    github_issue_nums = {str(i['number']) for i in github_issues}
    in_github = [t for t in with_id if t.issue_id and t.issue_id.lstrip('#') in github_issue_nums]
    not_in_github = [t for t in with_id if t not in in_github]

    if not untracked_only:
        print(f"Code TODOs: {len(code_todos)}")
        print(f"  - With ID, in GitHub:     {len(in_github)}")
        print(f"  - With ID, NOT in GitHub: {len(not_in_github)}")
        print(f"  - Without ID:             {len(without_id)}")
        print(f"Todo files: {len(todo_files)}")
        print(f"GitHub Issues (todo label): {len(github_issues)}")
        print()

    if without_id:
        print("-" * 60)
        print("CODE TODOs WITHOUT ID (need ID assignment)")
        print("-" * 60)
        for todo in without_id:
            print(f"\n  {todo.file}:{todo.line}")
            print(f"  {todo.marker}: {todo.content}")
        print()

    if not_in_github and not untracked_only:
        print("-" * 60)
        print("CODE TODOs WITH ID BUT NOT IN GITHUB (need migration)")
        print("-" * 60)
        for todo in not_in_github:
            print(f"  [{todo.issue_id}] {todo.file}:{todo.line} - {todo.content[:50]}")
        print()

    if in_github and not untracked_only:
        print("-" * 60)
        print("CODE TODOs IN GITHUB")
        print("-" * 60)
        for todo in in_github:
            print(f"  [{todo.issue_id}] {todo.file}:{todo.line} - {todo.content[:50]}")
        print()

    if todo_files and not untracked_only:
        print("-" * 60)
        print("TODO FILES")
        print("-" * 60)
        not_in_folder = [f for f in todo_files if not f.in_todo_folder]
        with_new = [f for f in todo_files if f.has_new_entries]

        if not_in_folder:
            print("\n  NOT in todo/ folder:")
            for f in not_in_folder:
                print(f"    - {f.path}")

        if with_new:
            print("\n  Have 'new entries' section:")
            for f in with_new:
                print(f"    - {f.path}")

        print(f"\n  All ({len(todo_files)}):")
        for f in todo_files:
            markers = []
            if not f.in_todo_folder:
                markers.append("NOT IN FOLDER")
            if f.has_new_entries:
                markers.append("HAS NEW")
            suffix = f" [{', '.join(markers)}]" if markers else ""
            print(f"    - {f.path}{suffix}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description='Scan codebase for TODOs')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--untracked-only', action='store_true', help='Only show untracked TODOs')
    parser.add_argument('--no-github', action='store_true', help='Skip GitHub API call')
    args = parser.parse_args()

    project_root = find_project_root()
    directories = ['src', 'tests', 'docs']

    code_todos = scan_code_todos(directories, project_root)
    todo_files = find_todo_files(project_root)
    github_issues = [] if args.no_github else get_github_issues()

    if args.json:
        output = {
            'code_todos': [asdict(t) for t in code_todos],
            'todo_files': [asdict(f) for f in todo_files],
            'github_issues': github_issues,
            'summary': {
                'total_code_todos': len(code_todos),
                'tracked': len([t for t in code_todos if t.issue_id]),
                'untracked': len([t for t in code_todos if not t.issue_id]),
                'todo_files': len(todo_files),
                'github_issues': len(github_issues)
            }
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(code_todos, todo_files, github_issues, args.untracked_only)

    return 0


if __name__ == '__main__':
    sys.exit(main())