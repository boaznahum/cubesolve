---
name: fix-run-configs
user_invocable: true
description: |
  Fix PyCharm project structure and run configurations.
  This skill should be used when the user says "fix pycharm", "fix pycharm project",
  "pycharm broken", "run tests doesn't appear", "no interpreter", "can't run tests",
  or runs "/fix-run-configs". Repairs .iml file (source/test roots) and run config
  interpreter paths.
---

# Fix PyCharm Project & Run Configurations Skill

Fix PyCharm project structure (`.iml` file, source roots) and run configurations (interpreter paths). Covers the two most common PyCharm breakages in this project.

## Triggers

Activate this skill on any of these user requests:
- `/fix-run-configs`
- "fix pycharm", "fix pycharm project", "pycharm broken"
- "no interpreter" in PyCharm
- "run tests doesn't appear", "can't run tests in PyCharm"
- "mark directory as" not working
- After switching Python interpreter (pip → uv, venv recreated)

## Part 1: Fix Project Module (.iml file)

The `.iml` file defines source roots, test roots, and excluded directories. Without it, PyCharm can't:
- Show "Run tests" on right-click
- Recognize `src/` as sources or `tests/` as test sources
- Properly resolve imports

### Step 1A: Check .iml Health

1. Read `.idea/modules.xml` to find which `.iml` file is expected.
2. Check if that `.iml` file exists.
3. If it exists, verify it contains these critical entries:
   - `<sourceFolder url="file://$MODULE_DIR$/src" isTestSource="false" />`
   - `<sourceFolder url="file://$MODULE_DIR$/tests" isTestSource="true" />`

### Step 1B: Repair .iml if Missing or Broken

If the `.iml` file is missing or doesn't have the correct source/test roots, **create or overwrite it** with:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<module type="PYTHON_MODULE" version="4">
  <component name="NewModuleRootManager">
    <content url="file://$MODULE_DIR$">
      <sourceFolder url="file://$MODULE_DIR$/src" isTestSource="false" />
      <sourceFolder url="file://$MODULE_DIR$/tests" isTestSource="true" />
      <excludeFolder url="file://$MODULE_DIR$/.venv" />
      <excludeFolder url="file://$MODULE_DIR$/.venv_pyglet_legacy" />
      <excludeFolder url="file://$MODULE_DIR$/.venv_pyglet2" />
      <excludeFolder url="file://$MODULE_DIR$/.pytest_cache" />
      <excludeFolder url="file://$MODULE_DIR$/dist" />
      <excludeFolder url="file://$MODULE_DIR$/build" />
      <excludeFolder url="file://$MODULE_DIR$/src/cube.egg-info" />
    </content>
    <orderEntry type="inheritedJdk" />
    <orderEntry type="sourceFolder" forTests="false" />
  </component>
</module>
```

Also verify `.idea/modules.xml` points to the correct `.iml` path. If `modules.xml` is missing, create it:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="ProjectModuleManager">
    <modules>
      <module fileurl="file://$PROJECT_DIR$/.idea/cubesolve.iml" filepath="$PROJECT_DIR$/.idea/cubesolve.iml" />
    </modules>
  </component>
</project>
```

### Step 1C: Report

- If repaired: "Restored .iml file — `src/` marked as Sources Root, `tests/` as Test Sources Root. **Restart PyCharm** to pick up the change."
- If already healthy: "Project module file (.iml) is OK."

## Part 2: Fix Run Configurations (Interpreter Paths)

Fix PyCharm run configurations to use `$PROJECT_DIR$/.venv/Scripts/python.exe` as the interpreter, making them portable across worktrees and machines (Windows AND Linux).

### Background

PyCharm run configurations can reference interpreters in fragile ways:
- `IS_MODULE_SDK=true` — breaks when the module-to-SDK mapping is lost
- `SDK_NAME="uv (cubesolve3) (4)"` — hardcoded name that changes per worktree

The portable solution: set `SDK_HOME=$PROJECT_DIR$/.venv/Scripts/python.exe` and `IS_MODULE_SDK=false`.

### Cross-Platform Compatibility

The canonical path in run configs is always the **Windows-style** path: `$PROJECT_DIR$/.venv/Scripts/python.exe`.
This works natively on Windows. On Linux, we create a symlink so the same path resolves:

```
.venv/Scripts/python.exe -> ../bin/python
```

This way the **same** run configuration XML works on both platforms without modification.

### Step 2A: Scan and Report

1. Glob for all `.idea/runConfigurations/*.xml` files.
2. Read each XML file. Only consider files with `type="PythonConfigurationType"` or `type="tests"` (skip non-Python configs).
3. For each Python/test config, check whether it needs fixing:
   - `SDK_HOME` is empty, missing, or doesn't contain `.venv/Scripts/python.exe`
   - `IS_MODULE_SDK` is `true`
4. Display a table showing ALL configs and their current status:

```
| # | Config Name              | Type   | SDK_HOME | IS_MODULE_SDK | SDK_NAME            | Needs Fix |
|---|--------------------------|--------|----------|---------------|---------------------|-----------|
| 1 | main_pyglet2             | Python | (empty)  | true          | —                   | Yes       |
| 2 | pytest_all_tests         | pytest | (set)    | false         | uv (cubesolve3) (2) | Yes       |
| 3 | main_web                 | Python | (set)    | false         | —                   | No        |
```

### Step 2B: Ask User What to Fix

Use `AskUserQuestion` to ask the user:
- **"Fix all"** — fix all configs that need fixing
- **"Let me pick"** — show the list and let user choose specific ones
- **"Cancel"** — do nothing

If the user picks "Let me pick", use `AskUserQuestion` with `multiSelect: true` listing only the configs that need fixing.

### Step 2C: Ensure Cross-Platform Symlink (Linux only)

If running on Linux (check with `uname -s`), ensure the compatibility symlink exists:

1. Check if `.venv/Scripts/python.exe` exists and is a valid symlink.
2. If not, create it:
   ```bash
   mkdir -p .venv/Scripts
   ln -sf ../bin/python .venv/Scripts/python.exe
   ```
3. Verify the symlink works by running `.venv/Scripts/python.exe --version`.
4. Report: "Created cross-platform symlink: .venv/Scripts/python.exe -> ../bin/python"

**Note:** This symlink is lost when the venv is recreated (e.g., `uv sync`). This skill re-creates it each time.

### Step 2D: Apply Fixes

For each selected config, apply these three XML transformations:

**a) Set SDK_HOME to venv path:**
```xml
<!-- Before -->
<option name="SDK_HOME" value="" />
<!-- After -->
<option name="SDK_HOME" value="$PROJECT_DIR$/.venv/Scripts/python.exe" />
```

**b) Set IS_MODULE_SDK to false:**
```xml
<!-- Before -->
<option name="IS_MODULE_SDK" value="true" />
<!-- After -->
<option name="IS_MODULE_SDK" value="false" />
```

**c) Leave SDK_NAME alone:**
Do NOT remove `SDK_NAME`. PyCharm auto-regenerates it on every save, so removing it just creates git noise.
`SDK_HOME` takes priority over `SDK_NAME` for interpreter resolution, so `SDK_NAME` is harmless.

### Step 2E: Report Results

Show a summary of what was changed:
- "Fixed N run configurations."
- On Linux: "Created cross-platform symlink: .venv/Scripts/python.exe -> ../bin/python"
- "Close and reopen run configs in PyCharm for changes to take effect."
- "Note: If you recreate the venv (uv sync), run /fix-run-configs again to restore the Linux symlink."
