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

Fix PyCharm run configurations to use `$PROJECT_DIR$/.venv/Scripts/python.exe` as the interpreter, making them portable across worktrees and machines.

## Background

PyCharm run configurations can reference interpreters in fragile ways:
- `IS_MODULE_SDK=true` — breaks when the module-to-SDK mapping is lost
- `SDK_NAME="uv (cubesolve3) (4)"` — hardcoded name that changes per worktree

The portable solution: set `SDK_HOME=$PROJECT_DIR$/.venv/Scripts/python.exe` and `IS_MODULE_SDK=false`.

## Workflow

### Step 1: Scan and Report

1. Glob for all `.idea/runConfigurations/*.xml` files.
2. Read each XML file. Only consider files with `type="PythonConfigurationType"` or `type="tests"` (skip non-Python configs).
3. For each Python/test config, check whether it needs fixing:
   - `SDK_HOME` is empty or missing
   - `IS_MODULE_SDK` is `true`
   - `SDK_NAME` contains a hardcoded interpreter name
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

### Step 3: Apply Fixes

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

**c) Remove SDK_NAME entirely:**
Remove any line matching `<option name="SDK_NAME" value="..." />`.
PyCharm may re-add it on next run — that is fine, `SDK_HOME` takes priority.

### Step 4: Report Results

Show a summary of what was changed:
- "Fixed N run configurations."
- "Close and reopen run configs in PyCharm for changes to take effect."
- "If PyCharm re-adds SDK_NAME, that's fine — SDK_HOME takes priority."
