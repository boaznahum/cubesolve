#!/usr/bin/env python3
"""Reconstruct cube.iml file for PyCharm/IntelliJ.

Creates a properly configured .iml file with:
- src as source folder
- tests as test source folder
- Python interpreter
- Excluded folders (venvs, cache, etc.)

Usage:
    python scripts/reconstruct_iml.py [--interpreter NAME]

Examples:
    python scripts/reconstruct_iml.py
    python scripts/reconstruct_iml.py --interpreter "Python 3.14 (cubesolve)"
"""

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET


def find_venv_folders(project_root: Path) -> list[str]:
    """Find all virtual environment folders to exclude."""
    exclude_patterns = [
        ".venv*", "venv*", "env", ".env",
        ".mypy_cache", ".pytest_cache", ".ruff_cache",
        "__pycache__", "_archive", "__try", ".tox",
        "build", "dist", "*.egg-info",
    ]

    excludes = []
    for item in project_root.iterdir():
        if not item.is_dir():
            continue
        name = item.name
        # Check exact matches and patterns
        if any(name == pat or (pat.endswith("*") and name.startswith(pat[:-1]))
               for pat in exclude_patterns):
            excludes.append(name)

    return sorted(excludes)


def detect_interpreter(project_root: Path) -> str:
    """Try to detect the Python interpreter name from existing config."""
    # Check misc.xml for SDK
    misc_xml = project_root / ".idea" / "misc.xml"
    if misc_xml.exists():
        try:
            tree = ET.parse(misc_xml)
            for component in tree.findall(".//component[@name='ProjectRootManager']"):
                sdk = component.get("project-jdk-name")
                if sdk:
                    return sdk
        except ET.ParseError:
            pass

    # Check existing iml backup
    backup = project_root / ".idea" / "cube.iml.backup"
    if backup.exists():
        try:
            tree = ET.parse(backup)
            for entry in tree.findall(".//orderEntry[@type='jdk']"):
                name = entry.get("jdkName")
                if name:
                    return name
        except ET.ParseError:
            pass

    # Default
    return "Python 3.14 (cubesolve)"


def create_iml(project_root: Path, interpreter: str) -> str:
    """Create the .iml XML content."""
    excludes = find_venv_folders(project_root)

    # Build XML structure
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<module type="PYTHON_MODULE" version="4">',
        '  <component name="NewModuleRootManager">',
        '    <content url="file://$MODULE_DIR$">',
        '      <sourceFolder url="file://$MODULE_DIR$/src" isTestSource="false" />',
        '      <sourceFolder url="file://$MODULE_DIR$/tests" isTestSource="true" />',
    ]

    # Add excludes
    for folder in excludes:
        lines.append(f'      <excludeFolder url="file://$MODULE_DIR$/{folder}" />')

    lines.extend([
        '    </content>',
        f'    <orderEntry type="jdk" jdkName="{interpreter}" jdkType="Python SDK" />',
        '    <orderEntry type="sourceFolder" forTests="false" />',
        '  </component>',
        '</module>',
    ])

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description="Reconstruct cube.iml for PyCharm")
    parser.add_argument("--interpreter", "-i", help="Python interpreter name")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Print but don't write")
    args = parser.parse_args()

    # Find project root (where .idea folder is)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    if not (project_root / ".idea").exists():
        print(f"Error: .idea folder not found in {project_root}")
        return 1

    # Detect or use provided interpreter
    interpreter = args.interpreter or detect_interpreter(project_root)
    print(f"Using interpreter: {interpreter}")

    # Generate content
    content = create_iml(project_root, interpreter)

    iml_path = project_root / ".idea" / "cube.iml"

    if args.dry_run:
        print(f"\nWould write to: {iml_path}")
        print("\n" + content)
    else:
        # Backup existing if present
        if iml_path.exists():
            backup_path = iml_path.with_suffix(".iml.bak")
            iml_path.rename(backup_path)
            print(f"Backed up existing to: {backup_path}")

        iml_path.write_text(content, encoding="utf-8")
        print(f"Created: {iml_path}")

    return 0


if __name__ == "__main__":
    exit(main())
