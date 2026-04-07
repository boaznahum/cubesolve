---
name: fixrun
user_invocable: true
description: |
  Fix PyCharm project structure, interpreter, and run configurations.
  Triggered by "/fixrun", "fix run", "fix pycharm". Use "/fixrun help" for quick reference.
---

# Fix PyCharm Project, Interpreter & Run Configurations

## Subcommand: `/fixrun help`

If the user runs `/fixrun help`, do NOT run the full skill. Instead, display this quick reference:

```
/fixrun help — Quick Reference
═══════════════════════════════

PHANTOM GIT DIFFS on .idea/runConfigurations/*.xml
  Cause: The committed blob was stored before the git clean filter existed,
         or PyCharm changed SDK_NAME/trailing whitespace.
  Fix:
    git rm --cached .idea/runConfigurations/*.xml
    git add .idea/runConfigurations/*.xml
  This re-stages files through the clean filter. No commit needed — diff disappears.

SDK_NAME MISMATCH (PyCharm shows wrong interpreter)
  Fix: Run /fixrun (full skill)

RUN CONFIGS BROKEN (can't run tests, wrong interpreter)
  Fix: Run /fixrun (full skill)

GIT FILTER NOT SET UP (no .git-filters/ directory)
  Fix: Run /fixrun (full skill — Part 4 sets up the filter)

AFTER SWITCHING BRANCHES
  If you see SDK_NAME diffs after checkout, the smudge filter should
  handle it automatically. If not:
    git checkout -- .idea/runConfigurations/
  This re-applies the smudge filter (injects local SDK name).
```

**STOP after displaying the help text.** Do not continue to the full skill.

---

Fix four common PyCharm breakages in this project:
1. Project module (.iml file) — source/test roots
2. Global interpreter (jdk.table.xml) — deduplicate entries, determine active SDK name
3. Git filter — prevent SDK_NAME drift from creating git diffs
4. Run configurations — all configs point to the correct interpreter

## Triggers

Activate on any of:
- `/fixrun`
- "fix run", "fix run config", "fix run configuration", "fix run configurations"
- "fix pycharm", "fix pycharm project", "pycharm broken"
- "no interpreter", "can't run tests", "run tests doesn't appear"
- After switching Python interpreter or recreating venv

## Pre-Check: Detect PyCharm Terminal

**CRITICAL — Do this FIRST before anything else.**

Check if running inside PyCharm's integrated terminal:

```bash
echo "$TERMINAL_EMULATOR"
```

- If the output contains `JetBrains` (e.g., `JetBrains-JediTerm`): **you are inside PyCharm's terminal**.
- Otherwise: you are in an external terminal — proceed normally.

### If Inside PyCharm Terminal

This skill needs to edit `jdk.table.xml`, which PyCharm overwrites on exit. Closing PyCharm kills this terminal session. **You cannot proceed from here.**

Tell the user:

> I'm running inside PyCharm's terminal. This skill needs PyCharm closed to edit `jdk.table.xml`, but closing PyCharm would kill this session.
>
> Please:
> 1. Open **Windows Terminal** (or any terminal outside PyCharm)
> 2. Run these commands:
>    ```
>    cd <PROJECT_DIR>
>    claude
>    ```
> 3. Then type `/fixrun` in the Claude session
> 4. After the skill completes successfully, restart PyCharm

Replace `<PROJECT_DIR>` with the actual absolute project directory path.

**STOP HERE** — do not proceed with any fixes. The external session will handle everything.

### If Outside PyCharm Terminal (or user confirms they are external)

Continue with the rest of the skill. Before editing `jdk.table.xml` (Part 2), ask the user to confirm PyCharm is closed.

## Core Principle: Don't Fight PyCharm's Naming

**CRITICAL:** PyCharm auto-generates interpreter names based on the project directory (e.g., `uv (cubesolve3)`, `uv (cubesolve3) (2)`). If you rename an entry to something PyCharm doesn't expect, it will create a NEW entry on next restart, making things worse.

**Strategy:**
1. **Deduplicate** jdk.table entries for this project (keep one, delete the rest)
2. **Read the active SDK name** from whichever entry survives — do NOT invent a name
3. **Use that name** consistently in .iml, misc.xml, and run configs
4. **Git filter** uses its own canonical name independently (only affects what git stages, not what PyCharm sees)

## Part 0: Determine PyCharm Config Path

```bash
# Glob for all PyCharm versions (both Pro and CE)
ls -d "$APPDATA/JetBrains/PyCharm"*/options/jdk.table.xml \
      "$APPDATA/JetBrains/PyCharmCE"*/options/jdk.table.xml 2>/dev/null | sort
```

- **If exactly one match:** use it.
- **If multiple matches:** Use `AskUserQuestion` with selectable options to let the user pick. Extract version names from paths (e.g., "PyCharm2025.3", "PyCharm2026.1") and pass them as the `options` array parameter. Example:
  ```
  AskUserQuestion:
    question: "Multiple PyCharm versions found. Which one are you using?"
    options: ["PyCharm2025.3", "PyCharm2026.1"]
  ```
- **If no matches:** report error — PyCharm config directory not found.

## Part 1: Analyze Current State (Read Everything First)

Before making ANY changes, read all relevant files to understand the full picture.

### Step 1A: Read All State

1. Read `.idea/modules.xml` → find which `.iml` file is expected
2. Read the `.iml` file → note the `jdkName` it references
3. Read `jdk.table.xml` → identify all entries, especially for this project
4. Read `.idea/misc.xml` → note current `sdkName`
5. Read all `.idea/runConfigurations/*.xml` → note their `SDK_NAME` values
6. Read `.idea/workspace.xml` → find `<component name="RunManager">` section, note `SDK_NAME`/`SDK_HOME`/`IS_MODULE_SDK` for all temporary run configs (`type="PythonConfigurationType"` or `type="tests"`)

### Step 1B: Identify This Project's Entries in jdk.table.xml

Categorize each `<jdk>` entry:
- **This project:** `ASSOCIATED_PROJECT_PATH` matches the current project directory (use forward-slash path comparison)
- **Other projects:** Everything else

### Step 1C: Determine the Active SDK Name

The **active SDK name** is determined by this priority:
1. The `jdkName` in the `.iml` file (if it uses an explicit `jdkName`, not `inheritedJdk`)
2. The `project-jdk-name` in `.idea/misc.xml` (if .iml uses `inheritedJdk`)
3. If neither matches a jdk.table entry → use the name of the first jdk.table entry for this project
4. If no jdk.table entries exist for this project → report error, cannot proceed

**Store this as `ACTIVE_SDK_NAME`** — it will be used everywhere.

### Step 1D: Display State Table

```
ACTIVE_SDK_NAME: uv (cubesolve3) (3)  ← from .iml jdkName

jdk.table.xml entries for this project:
| # | Name                  | SDK_UUID  | Action                    |
|---|-----------------------|-----------|---------------------------|
| 1 | uv (cubesolve3)       | abc-123   | Delete (not active)       |
| 2 | uv (cubesolve3) (2)   | def-456   | Delete (not active)       |
| 3 | uv (cubesolve3) (3)   | ghi-789   | Keep (matches .iml)       |

Other references:
- misc.xml sdkName: "uv (cubesolve2)" → needs update to ACTIVE_SDK_NAME
- Run configs SDK_NAME: "uv (cubesolve2)" → needs update to ACTIVE_SDK_NAME
```

## Part 2: Fix Global Interpreter (jdk.table.xml)

### Step 2A: Warn About PyCharm

**IMPORTANT:** Tell the user: "Close PyCharm before proceeding — it will overwrite jdk.table.xml on exit."

Wait for confirmation before proceeding.

### Step 2B: Deduplicate (Do NOT Rename)

For **this project's entries**:
1. **Keep the entry whose name matches `ACTIVE_SDK_NAME`** (the one .iml references)
2. **Delete all other entries** for this project
3. **Do NOT rename anything** — keep the exact name PyCharm assigned

For **other projects' duplicate entries** (same ASSOCIATED_PROJECT_PATH appearing multiple times):
1. Delete duplicates, keeping only the first entry for each project.

**Never delete the sole entry for another project.**

### Step 2C: Verify the Kept Entry

After deletion, verify:
- The kept entry's `homePath` points to `<project_dir>/.venv/Scripts/python.exe`
- The `ASSOCIATED_PROJECT_PATH` matches the project directory
- If `homePath` is wrong, update it (but keep the name!)

## Part 3: Fix Project Files (.iml and misc.xml)

### Step 3A: Fix .iml Source/Test Roots

Check if the `.iml` file has correct source and test roots. If not, fix ONLY the content/roots — **preserve the `jdkName` reference**.

Required structure:
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
    <orderEntry type="jdk" jdkName="ACTIVE_SDK_NAME" jdkType="Python SDK" />
    <orderEntry type="sourceFolder" forTests="false" />
  </component>
</module>
```

**IMPORTANT:** Replace `ACTIVE_SDK_NAME` with the actual name determined in Step 1C. Do NOT use `inheritedJdk` — use an explicit `jdkName` reference so PyCharm knows exactly which SDK to use.

**IMPORTANT:** If the .iml has `external.system.id="java-source"` in the `<module>` tag, preserve it — PyCharm adds this and expects it.

### Step 3B: Fix misc.xml

Update `.idea/misc.xml` so the `sdkName` matches `ACTIVE_SDK_NAME`:

```xml
<option name="sdkName" value="ACTIVE_SDK_NAME" />
```

Or if using `ProjectRootManager`:
```xml
<component name="ProjectRootManager" version="2" project-jdk-name="ACTIVE_SDK_NAME" project-jdk-type="Python SDK" />
```

**Use whichever format misc.xml already uses** — don't change its structure, just update the SDK name value.

## Part 4: Git Filter for SDK_NAME (Bidirectional)

Prevent PyCharm's SDK_NAME auto-changes from creating git diffs, AND ensure correct SDK_NAME on checkout/branch-switch. Uses a bidirectional git filter:
- **Clean** (working copy → git): normalizes any SDK_NAME to canonical `uv (cubesolve2)`
- **Smudge** (git → working copy): replaces canonical with the local machine's ACTIVE_SDK_NAME

**The canonical name for git is `uv (cubesolve2)`.** This is independent of what PyCharm uses.

**IMPORTANT:** This part MUST run before Part 5 (Fix Run Configurations). Step 4C.4 re-checkouts run config files through the smudge filter. Part 5 then verifies and fixes any remaining issues.

### Step 4A: Check if Filter Already Set Up

1. Check if `.git-filters/normalize-sdk-name.py` exists.
2. Check if `.git-filters/denormalize-sdk-name.py` exists.
3. Check if `.git-filters/local-sdk-name.txt` exists and contains the correct ACTIVE_SDK_NAME.
4. Check if `.gitattributes` contains the filter rule for `runConfigurations/*.xml`.
5. Check if `git config filter.normalize-sdk-name.clean` is set.
6. Check if `git config filter.normalize-sdk-name.smudge` references `denormalize-sdk-name.py` (NOT `cat`).

If all six exist and correct, report "Git filter already configured." and skip to Step 4D.

**Migration note:** If smudge is set to `cat` (old version), update it to use `denormalize-sdk-name.py` and continue with setup.

### Step 4B: Create Filter Scripts

**1. Create `.git-filters/normalize-sdk-name.py`** (clean filter — working copy → git):

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

**2. Create `.git-filters/denormalize-sdk-name.py`** (smudge filter — git → working copy):

```python
"""Git smudge filter: replace canonical SDK_NAME with local machine's SDK name.

Reads the local SDK name from .git-filters/local-sdk-name.txt and replaces
the canonical placeholder with it. This ensures every checkout/branch-switch
gets the correct SDK_NAME for this machine's PyCharm interpreter.
"""
import os
import re
import sys

CANONICAL_SDK_NAME = "uv (cubesolve2)"

# Read local SDK name from sibling file
local_sdk_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local-sdk-name.txt")
try:
    with open(local_sdk_file) as f:
        local_sdk_name = f.read().strip()
except FileNotFoundError:
    local_sdk_name = CANONICAL_SDK_NAME  # fallback if file missing

canonical_escaped = re.escape(CANONICAL_SDK_NAME)

for line in sys.stdin:
    line = re.sub(
        rf'(<option name="SDK_NAME" value="){canonical_escaped}("\s*/>)',
        rf'\g<1>{local_sdk_name}\g<2>',
        line,
    )
    sys.stdout.write(line)
```

**3. Create `.git-filters/local-sdk-name.txt`** with the ACTIVE_SDK_NAME:

```
uv (cubesolve)
```

This file is machine-specific. It must be in `.gitignore`.

**4. Ensure `.git-filters/local-sdk-name.txt` is git-ignored.** Add to `.gitignore` if not already present:
```
.git-filters/local-sdk-name.txt
```

### Step 4C: Configure Git

1. Add to `.gitattributes` (if not already present):
   ```
   # Normalize SDK_NAME in PyCharm run configs so PyCharm's auto-changes don't create git diffs
   .idea/runConfigurations/*.xml filter=normalize-sdk-name
   ```

2. Register the filter in git config:
   ```bash
   git config filter.normalize-sdk-name.clean "python .git-filters/normalize-sdk-name.py"
   git config filter.normalize-sdk-name.smudge "python .git-filters/denormalize-sdk-name.py"
   ```

3. If upgrading from old `cat` smudge, also update:
   ```bash
   git config filter.normalize-sdk-name.smudge "python .git-filters/denormalize-sdk-name.py"
   ```

4. Re-checkout run configs so the smudge filter applies (injects correct SDK_NAME):
   ```bash
   rm .idea/runConfigurations/*.xml
   git checkout -- .idea/runConfigurations/
   ```

### Step 4D: Verify Filter Works

Test both directions:
```bash
# Clean filter: any SDK_NAME → canonical
echo '<option name="SDK_NAME" value="uv (cubesolve3) (4)" />' | python .git-filters/normalize-sdk-name.py
# Expected: <option name="SDK_NAME" value="uv (cubesolve2)" />

# Smudge filter: canonical → local
echo '<option name="SDK_NAME" value="uv (cubesolve2)" />' | python .git-filters/denormalize-sdk-name.py
# Expected: <option name="SDK_NAME" value="ACTIVE_SDK_NAME" /> (whatever is in local-sdk-name.txt)
```

### How It Works

```
PyCharm saves:  SDK_NAME="uv (cubesolve) (4)"
                     ↓ (git clean filter on "git add")
Git stores:     SDK_NAME="uv (cubesolve2)"        ← canonical, same everywhere
                     ↓ (git smudge filter on checkout)
Working copy:   SDK_NAME="uv (cubesolve)"          ← local machine's SDK name
                     → PyCharm finds the right interpreter!
```

- **Clean** runs on `git add` — normalizes to canonical. No diffs from SDK_NAME changes.
- **Smudge** runs on `git checkout` — denormalizes to local. Every checkout gets the right name.
- `local-sdk-name.txt` is git-ignored (machine-specific). Updated by this skill.
- After setup, SDK_NAME is always correct in both git and working copy.

## Part 5: Fix Run Configurations

**NOTE:** This part runs AFTER Part 4 (git filter). The smudge filter should have already injected the correct ACTIVE_SDK_NAME during the re-checkout in Step 4C.4. This part verifies and fixes any remaining issues (e.g., SDK_HOME, IS_MODULE_SDK).

### Step 5A: Scan Run Configs (Shared AND Temporary)

PyCharm stores run configurations in **two** locations:
- **Shared configs:** `.idea/runConfigurations/*.xml` (one file per config, committed to git)
- **Temporary/local configs:** `.idea/workspace.xml` (inside `<component name="RunManager">`, NOT committed)

**Both must be scanned and fixed.**

#### 5A.1: Scan Shared Configs

1. Glob for all `.idea/runConfigurations/*.xml` files.
2. Read each file. Only consider `type="PythonConfigurationType"` or `type="tests"`.
3. For each config, check:
   - `SDK_HOME` should be `$PROJECT_DIR$/.venv/Scripts/python.exe`
   - `SDK_NAME` should match `ACTIVE_SDK_NAME`
   - `IS_MODULE_SDK` should be `false`

#### 5A.2: Scan Temporary Configs in workspace.xml

1. Read `.idea/workspace.xml`.
2. Find the `<component name="RunManager">` section.
3. Within it, find all `<configuration>` elements with `type="PythonConfigurationType"` or `type="tests"`.
4. For each config, check the same three fields: `SDK_HOME`, `SDK_NAME`, `IS_MODULE_SDK`.
5. **Note:** Temporary configs often have `SDK_HOME` set to empty string (`""`) and missing `SDK_NAME` entirely — both need fixing.

#### 5A.3: Display Combined Table

```
| # | Location    | Config Name              | SDK_HOME | SDK_NAME            | IS_MODULE_SDK | Needs Fix |
|---|-------------|--------------------------|----------|---------------------|---------------|-----------|
| 1 | shared      | main_pyglet2             | (set)    | uv (cubesolve3) (3) | false         | No        |
| 2 | shared      | pytest_all_tests         | (empty)  | —                   | true          | Yes       |
| 3 | workspace   | pytest in solvers        | (empty)  | —                   | true          | Yes       |
```

### Step 5B: Apply Fixes (no confirmation needed — fix all automatically)

For each config that needs fixing, apply these XML changes:

**a) Set SDK_HOME:**
```xml
<option name="SDK_HOME" value="$PROJECT_DIR$/.venv/Scripts/python.exe" />
```

**b) Set or add SDK_NAME to ACTIVE_SDK_NAME:**
```xml
<option name="SDK_NAME" value="ACTIVE_SDK_NAME" />
```
If `SDK_NAME` is missing entirely from a config (common in workspace.xml temporary configs), **add it** as a new `<option>` element right after the `SDK_HOME` line.

**c) Set IS_MODULE_SDK to false:**
```xml
<option name="IS_MODULE_SDK" value="false" />
```

**For workspace.xml configs:** Use the Edit tool to fix each broken config in place. Be careful to match the exact `<configuration name="...">` to avoid editing the wrong config.

### Step 5C: Cross-Platform Symlink (Linux only)

If running on Linux (`uname -s` returns "Linux"), create compatibility symlink:

```bash
mkdir -p .venv/Scripts
ln -sf ../bin/python .venv/Scripts/python.exe
```

This ensures `$PROJECT_DIR$/.venv/Scripts/python.exe` resolves on Linux too.

## Part 6: Final Verification

After all changes, verify consistency:

1. **Read the kept jdk.table entry name** → `ACTIVE_SDK_NAME`
2. **Check .iml `jdkName`** → must match `ACTIVE_SDK_NAME`
3. **Check misc.xml `sdkName`** → must match `ACTIVE_SDK_NAME`
4. **Check all shared run configs `SDK_NAME`** (`.idea/runConfigurations/*.xml`) → must match `ACTIVE_SDK_NAME`
5. **Check all temporary run configs `SDK_NAME`** (`.idea/workspace.xml`) → must match `ACTIVE_SDK_NAME`

If any mismatch is found, fix it immediately.

### Report Results

Show summary:
- "Active SDK name: `ACTIVE_SDK_NAME`"
- "Deleted N duplicate interpreter entries from jdk.table.xml"
- "Fixed .iml source/test roots: [yes/no]"
- "Updated misc.xml SDK reference: [yes/no]"
- "Fixed N run configurations"
- "Git filter: [already configured / newly configured]"
- "**Restart PyCharm** for all changes to take effect."
