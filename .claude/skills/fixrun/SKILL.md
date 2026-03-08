---
name: fixrun
user_invocable: true
description: |
  Fix PyCharm project structure, interpreter, and run configurations.
  This skill should be used when the user says "fix run", "fixrun", "fix run config",
  "fix run configuration", "fix run configurations", "run configurations",
  "fix pycharm", "fix pycharm project", "pycharm broken", "run tests doesn't appear",
  "no interpreter", "can't run tests", or runs "/fixrun". Repairs .iml file
  (source/test roots), ensures correct interpreter, sets up git filter, and fixes run configs.
---

# Fix PyCharm Project, Interpreter & Run Configurations

Fix four common PyCharm breakages in this project:
1. Project module (.iml file) — source/test roots
2. Global interpreter (jdk.table.xml) — ensure "uv (cubesolve2)" exists, clean up stale entries
3. Run configurations — all configs point to the correct interpreter
4. Git filter — prevent SDK_NAME drift from creating git diffs

## Triggers

Activate on any of:
- `/fixrun`
- "fix run", "fix run config", "fix run configuration", "fix run configurations"
- "fix pycharm", "fix pycharm project", "pycharm broken"
- "no interpreter", "can't run tests", "run tests doesn't appear"
- After switching Python interpreter or recreating venv

## Part 1: Fix Project Module (.iml file)

The `.iml` file defines source roots, test roots, and excluded directories.

### Step 1A: Check .iml Health

1. Read `.idea/modules.xml` to find which `.iml` file is expected.
2. Check if that `.iml` file exists.
3. If it exists, verify it contains:
   - `<sourceFolder url="file://$MODULE_DIR$/src" isTestSource="false" />`
   - `<sourceFolder url="file://$MODULE_DIR$/tests" isTestSource="true" />`

### Step 1B: Repair .iml if Missing or Broken

If missing or incorrect, create/overwrite with:

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

Also verify `.idea/modules.xml` points to the correct `.iml` path.

### Step 1C: Report

- If repaired: "Restored .iml — **restart PyCharm** to pick up the change."
- If healthy: "Project module file (.iml) is OK."

## Part 2: Fix Global Interpreter (jdk.table.xml)

The global interpreter table lives in the PyCharm config directory. To find it:

```bash
# Glob for all PyCharm versions (both Pro and CE)
ls -d C:/Users/boaz2/AppData/Roaming/JetBrains/PyCharm*/options/jdk.table.xml \
      C:/Users/boaz2/AppData/Roaming/JetBrains/PyCharmCE*/options/jdk.table.xml 2>/dev/null | sort
```

- **If exactly one match:** use it.
- **If multiple matches:** ask the user which PyCharm version they are using (use `AskUserQuestion` with the list of found versions as options).
- **If no matches:** report error — PyCharm config directory not found.

### Goal

Ensure exactly ONE interpreter named `"uv (cubesolve2)"` exists for this project, pointing to the current project's `.venv/Scripts/python.exe`. Delete all stale/duplicate entries.

### Step 2A: Read and Analyze jdk.table.xml

1. Read `jdk.table.xml`.
2. Identify all `<jdk>` entries. Categorize each:
   - **This project:** `ASSOCIATED_PROJECT_PATH` contains `cubesolve2` (the current project dir)
   - **Other projects:** Everything else (Supplement, cubesolve, cubesolve3, etc.)

### Step 2B: Report Current State

Display a table:

```
| # | Name                  | Home Path                                    | Associated Project | Action     |
|---|-----------------------|----------------------------------------------|--------------------|------------|
| 1 | uv (cubesolve)        | E:/.../cubesolve/.venv/Scripts/python.exe     | cubesolve          | Keep (other project) |
| 2 | uv (cubesolve2)       | E:/.../cubesolve2/.venv/Scripts/python.exe    | cubesolve2         | → Rename to "uv (cubesolve2)" |
| 3 | uv (cubesolve3)       | E:/.../cubesolve3/.venv/Scripts/python.exe    | cubesolve3         | Keep (other project) |
| 4 | uv (cubesolve3) (2)   | E:/.../cubesolve3/.venv/Scripts/python.exe    | cubesolve3         | Delete (duplicate) |
| 5 | uv (Supplement)       | E:/.../Supplement/.venv/Scripts/python.exe    | Supplement         | Keep (other project) |
```

### Step 2C: Apply Fixes

**IMPORTANT:** Close PyCharm before editing `jdk.table.xml`. Warn the user: "Close PyCharm before proceeding — it will overwrite jdk.table.xml on exit."

For **this project's** entries (ASSOCIATED_PROJECT_PATH contains current project dir):
1. Keep exactly one entry. Rename it to `"uv (cubesolve2)"`.
2. Set `homePath` to the current project's `.venv/Scripts/python.exe` (absolute path).
3. Set `ASSOCIATED_PROJECT_PATH` to the current project's absolute path.
4. Update `UV_WORKING_DIR` and `UV_VENV_PATH` to match.
5. Delete any duplicate entries for this project.

For **other projects' duplicate entries** (same ASSOCIATED_PROJECT_PATH appearing multiple times):
1. Delete duplicates, keeping only the first entry for each project.

**Never delete the sole entry for another project** (e.g., Supplement, cubesolve3) — those belong to other PyCharm projects.

### Step 2D: Fix misc.xml Project SDK Reference

Update `.idea/misc.xml` to reference the correct interpreter name:

```xml
<component name="ProjectRootManager" version="2" project-jdk-name="uv (cubesolve2)" project-jdk-type="Python SDK" />
```

## Part 3: Fix Run Configurations

### Step 3A: Scan Run Configs

1. Glob for all `.idea/runConfigurations/*.xml` files.
2. Read each file. Only consider `type="PythonConfigurationType"` or `type="tests"`.
3. For each config, check:
   - `SDK_HOME` should be `$PROJECT_DIR$/.venv/Scripts/python.exe`
   - `SDK_NAME` should be `uv (cubesolve)`
   - `IS_MODULE_SDK` should be `false`

4. Display a table:

```
| # | Config Name              | SDK_HOME | SDK_NAME            | IS_MODULE_SDK | Needs Fix |
|---|--------------------------|----------|---------------------|---------------|-----------|
| 1 | main_pyglet2             | (set)    | uv (cubesolve3)     | false         | Yes       |
| 2 | pytest_all_tests         | (empty)  | —                   | true          | Yes       |
| 3 | main_any_backend         | (set)    | uv (cubesolve)      | false         | No        |
```

### Step 3B: Apply Fixes (no confirmation needed — fix all automatically)

For each config that needs fixing, apply these XML changes:

**a) Set SDK_HOME:**
```xml
<option name="SDK_HOME" value="$PROJECT_DIR$/.venv/Scripts/python.exe" />
```

**b) Set SDK_NAME:**
```xml
<option name="SDK_NAME" value="uv (cubesolve2)" />
```

**c) Set IS_MODULE_SDK to false:**
```xml
<option name="IS_MODULE_SDK" value="false" />
```

### Step 3C: Cross-Platform Symlink (Linux only)

If running on Linux (`uname -s` returns "Linux"), create compatibility symlink:

```bash
mkdir -p .venv/Scripts
ln -sf ../bin/python .venv/Scripts/python.exe
```

This ensures `$PROJECT_DIR$/.venv/Scripts/python.exe` resolves on Linux too.

### Step 3D: Report Results

Show summary:
- "Fixed N run configurations."
- "Updated interpreter name to 'uv (cubesolve)' in jdk.table.xml."
- "Deleted N stale interpreter entries."
- "**Restart PyCharm** for all changes to take effect."

## Part 4: Git Filter for SDK_NAME

Prevent PyCharm's SDK_NAME auto-changes from creating git diffs. This uses a git clean filter that normalizes SDK_NAME to a canonical value before staging.

### Step 4A: Check if Filter Already Set Up

1. Check if `.git-filters/normalize-sdk-name.py` exists.
2. Check if `.gitattributes` contains the filter rule for `runConfigurations/*.xml`.
3. Check if `git config filter.normalize-sdk-name.clean` is set.

If all three exist, report "Git filter already configured." and skip to Step 4D.

### Step 4B: Create Filter Script

Create `.git-filters/normalize-sdk-name.py`:

```python
"""Git clean filter: normalize SDK_NAME in PyCharm run configurations.

Replaces any SDK_NAME value with a canonical placeholder so that
PyCharm's auto-generated SDK_NAME changes don't show up in git diffs.
"""
import re
import sys

CANONICAL_SDK_NAME = "uv (cubesolve2)"

for line in sys.stdin:
    line = re.sub(
        r'(<option name="SDK_NAME" value=")([^"]*)("\s*/>)',
        rf'\g<1>{CANONICAL_SDK_NAME}\g<3>',
        line,
    )
    sys.stdout.write(line)
```

### Step 4C: Configure Git

1. Add to `.gitattributes`:
   ```
   # Normalize SDK_NAME in PyCharm run configs so PyCharm's auto-changes don't create git diffs
   .idea/runConfigurations/*.xml filter=normalize-sdk-name
   ```

2. Register the filter in git config:
   ```bash
   git config filter.normalize-sdk-name.clean "python .git-filters/normalize-sdk-name.py"
   git config filter.normalize-sdk-name.smudge "cat"
   ```

3. Re-checkout run configs so the filter applies to the index:
   ```bash
   rm .idea/runConfigurations/*.xml
   git checkout -- .idea/runConfigurations/
   ```

### Step 4D: Verify Filter Works

Test the filter:
```bash
echo '<option name="SDK_NAME" value="uv (cubesolve3) (4)" />' | python .git-filters/normalize-sdk-name.py
```

Expected output: `<option name="SDK_NAME" value="uv (cubesolve2)" />`

### How It Works

```
PyCharm saves:  SDK_NAME="uv (cubesolve3) (4)"
                     ↓ (git clean filter runs on "git add")
Git sees:       SDK_NAME="uv (cubesolve2)"
                     → no diff!
```

- The filter runs automatically on `git add` — no manual steps needed.
- The working copy keeps whatever PyCharm writes — the filter only affects what git stages.
- After the one-time setup, SDK_NAME changes never appear in `git diff` again.
