---
name: loggerdebug
user_invocable: true
description: |
  Fix logger debug/debug_lazy usage to ensure lazy evaluation is used correctly.
  This skill should be used when the user says "fix debug", "fix logger",
  "fix logger debug", "loggerdebug", "fix lazy", "fix log lazy",
  or runs "/loggerdebug".
---

# Fix Logger Debug / Debug Lazy

Fix incorrect usage of `debug()` vs `debug_lazy()` (and `log()` vs `log_lazy()`) across the codebase.

## Rules

**Note:** The logger object may be accessed via different names: `self._logger`, `vs.logger`, `logger`, etc.
All rules apply regardless of the object name — match on the method name (`.debug(`, `.debug_lazy(`, `.log(`, `.log_lazy(`).

1. **Non-lazy with real f-string interpolation -> convert to lazy:**
   - `<obj>.debug(f"text {var}")` -> `<obj>.debug_lazy(lambda: f"text {var}")`
   - `<obj>.log(level, f"text {var}")` -> `<obj>.log_lazy(level, lambda: f"text {var}")`
   - A "real" f-string is one that contains `{...}` interpolation expressions.

2. **Lazy without f-string or without real interpolation -> convert to non-lazy:**
   - `<obj>.debug_lazy(lambda: "plain string")` -> `<obj>.debug("plain string")`
   - `<obj>.debug_lazy(lambda: f"no interpolation")` -> `<obj>.debug("no interpolation")`
   - `<obj>.log_lazy(level, lambda: "plain")` -> `<obj>.log(level, "plain")`
   - `<obj>.log_lazy(level, lambda: f"no interpolation")` -> `<obj>.log(level, "no interpolation")`
   - Remove the `f` prefix when converting from lazy to non-lazy if the string has no interpolation.

3. **Already correct -> leave alone:**
   - `<obj>.debug("plain string")` - non-lazy with plain string (correct)
   - `<obj>.debug_lazy(lambda: f"text {var}")` - lazy with real f-string (correct)
   - `<obj>.debug_lazy(lambda: expensive_func())` - lazy with callable (correct)
   - Multi-arg `debug_lazy` like `<obj>.debug_lazy("prefix:", lambda: f"{x}")` - mixed args (correct)

4. **Edge cases:**
   - `f"text {{literal braces}}"` - doubled braces are NOT interpolation (treat as plain string)
   - Multi-line f-strings (with continuation `\` or parenthesized) count as real if any line has `{...}`
   - `log_lazy` with `verbose_level()` or `cube_level()` as the level arg: same rules apply to the string args

## Triggers

- `/loggerdebug`
- "fix debug", "fix logger", "fix logger debug", "fix lazy", "fix log lazy"

## Step 1: Ask for File Scope

Ask the user which files to scan. Present these options:

1. **Modified files** (preferred) - files modified in the current git branch vs main:
   ```bash
   git diff --name-only main...HEAD -- '*.py'
   ```
   If no modified files, also check uncommitted changes:
   ```bash
   git diff --name-only HEAD -- '*.py'
   ```

2. **Files open in PyCharm** - use MCP tool:
   ```
   mcp__pycharm2__get_all_open_file_paths
   ```
   Filter to `.py` files only. If PyCharm MCP is not available, inform the user and fall back to other options.

3. **A specific package** - ask the user for a path (e.g., `src/cube/domain/solver/`)

4. **Entire src** - scan all of `src/cube/`

5. **User-specified files** - let the user provide specific file paths

## Step 2: Scan Files

For each file in scope, search for these patterns:

### Patterns to Find

The logger may be accessed via different object names (`self._logger`, `vs.logger`, `logger`, etc.).
Use Grep with broad patterns that match ANY object's logger calls:

```
# Non-lazy debug/log calls (check if they use f-strings with interpolation)
\.debug\(
\.log\(

# Lazy debug/log calls (check if they DON'T use f-strings with interpolation)
\.debug_lazy\(
\.log_lazy\(
```

**Filtering:** After grep, read the matching lines and filter to actual CubeLogger calls.
Discard false positives (e.g., `git.log(`, `math.log(`, non-logger `.debug(` calls).
CubeLogger calls typically look like: `<something>.logger.debug(`, `self._logger.debug(`, `logger.debug(`.

**Exclusions:** Skip `src/cube/utils/logging/_logger.py` — this is the CubeLogger implementation itself, not a consumer.

Read each file that has matches and analyze each call site.

### Classification

For each call site, classify it:

| Pattern | Has real `{...}` interpolation? | Current | Should be | Action |
|---------|------|---------|-----------|--------|
| `debug(f"...{x}...")` | Yes | non-lazy | lazy | FIX |
| `debug("plain")` | No | non-lazy | non-lazy | OK |
| `debug(f"no interp")` | No | non-lazy | non-lazy | WARN (unnecessary f-prefix) |
| `debug_lazy(lambda: f"...{x}...")` | Yes | lazy | lazy | OK |
| `debug_lazy(lambda: "plain")` | No | lazy | non-lazy | FIX |
| `debug_lazy(lambda: f"no interp")` | No | lazy | non-lazy | FIX |
| `log(level, f"...{x}...")` | Yes | non-lazy | lazy | FIX |
| `log_lazy(level, lambda: "plain")` | No | lazy | non-lazy | FIX |

## Step 3: Report Findings

Display a summary table of all issues found:

```
## Logger Debug Analysis

### Files scanned: 5
### Issues found: 3

| # | File | Line | Current | Issue | Fix |
|---|------|------|---------|-------|-----|
| 1 | solver/L3Cross.py | 42 | debug(f"...{x}") | non-lazy with f-string | -> debug_lazy(lambda: f"...{x}") |
| 2 | solver/L3Cross.py | 88 | debug_lazy(lambda: "plain") | lazy without interpolation | -> debug("plain") |
| 3 | solver/Cage.py | 156 | log_lazy(level, lambda: f"no interp") | lazy without interpolation | -> log(level, "no interp") |

### Already correct: 12 calls
```

## Step 4: Ask to Fix

Ask the user:
- "Would you like me to fix all N issues?"
- Or "Would you like to fix specific ones? (enter numbers)"

## Step 5: Apply Fixes

Use the Edit tool to fix each issue. Be careful with:

- **Multi-line strings:** The `lambda:` and closing `)` may be on different lines
- **Indentation:** Preserve exact indentation
- **String continuations:** `f"part1 " f"part2"` or `f"part1 "\n f"part2"` - check ALL parts for interpolation
- **Removing `f` prefix:** When converting `debug_lazy(lambda: f"no interp")` to `debug("no interp")`, remove the `f`

### Fix Templates

**Non-lazy -> lazy (debug):**
```python
# Before:
self._logger.debug(f"text {var} more")
# After:
self._logger.debug_lazy(lambda: f"text {var} more")
```

**Non-lazy -> lazy (log):**
```python
# Before:
self._logger.log(level, f"text {var}")
# After:
self._logger.log_lazy(level, lambda: f"text {var}")
```

**Lazy -> non-lazy (debug_lazy):**
```python
# Before:
self._logger.debug_lazy(lambda: "plain string")
# After:
self._logger.debug("plain string")

# Before:
self._logger.debug_lazy(lambda: f"no interpolation")
# After:
self._logger.debug("no interpolation")
```

**Lazy -> non-lazy (log_lazy):**
```python
# Before:
self._logger.log_lazy(logging.DEBUG, lambda: "plain")
# After:
self._logger.log(logging.DEBUG, "plain")

# Before:
self._logger.log_lazy(logging.DEBUG, lambda: f"no interpolation")
# After:
self._logger.log(logging.DEBUG, "no interpolation")
```

## Step 6: Verify

After fixes, re-scan the same files to confirm no issues remain. Report the results.