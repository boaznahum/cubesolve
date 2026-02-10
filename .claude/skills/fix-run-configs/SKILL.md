---
name: fix-run-configs
user_invocable: true
description: |
  Fix PyCharm run configurations to use portable interpreter paths.
  This skill should be used when the user runs "/fix-run-configs", reports
  "No interpreter" in PyCharm run configs, or after switching Python
  interpreter (e.g., pip to uv). Asks user which configs to fix before
  making changes.
---

# Fix Run Configurations Skill

Fix PyCharm run configurations to use `$PROJECT_DIR$/.venv/Scripts/python.exe` as the interpreter, making them portable across worktrees and machines (Windows AND Linux).

## Background

PyCharm run configurations can reference interpreters in fragile ways:
- `IS_MODULE_SDK=true` — breaks when the module-to-SDK mapping is lost
- `SDK_NAME="uv (cubesolve3) (4)"` — hardcoded name that changes per worktree

The portable solution: set `SDK_HOME=$PROJECT_DIR$/.venv/Scripts/python.exe` and `IS_MODULE_SDK=false`.

## Cross-Platform Compatibility

The canonical path in run configs is always the **Windows-style** path: `$PROJECT_DIR$/.venv/Scripts/python.exe`.
This works natively on Windows. On Linux, we create a symlink so the same path resolves:

```
.venv/Scripts/python.exe -> ../bin/python
```

This way the **same** run configuration XML works on both platforms without modification.

## Workflow

### Step 1: Scan and Report

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

### Step 2: Ask User What to Fix

Use `AskUserQuestion` to ask the user:
- **"Fix all"** — fix all configs that need fixing
- **"Let me pick"** — show the list and let user choose specific ones
- **"Cancel"** — do nothing

If the user picks "Let me pick", use `AskUserQuestion` with `multiSelect: true` listing only the configs that need fixing.

### Step 3: Ensure Cross-Platform Symlink (Linux only)

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

### Step 4: Apply Fixes

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

### Step 5: Report Results

Show a summary of what was changed:
- "Fixed N run configurations."
- On Linux: "Created cross-platform symlink: .venv/Scripts/python.exe -> ../bin/python"
- "Close and reopen run configs in PyCharm for changes to take effect."
- "Note: If you recreate the venv (uv sync), run /fix-run-configs again to restore the Linux symlink."
