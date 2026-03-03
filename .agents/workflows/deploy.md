---
description: Commit, bump version, push, and create PR to webgl-dev
---
// turbo-all

## Steps

1. Stage all modified files under `src/`:
   ```
   git add -A src/
   ```

2. Read the current version from `src/cube/resources/version.txt` and bump the **patch** number (e.g. `1.22.1` → `1.22.2`). Write the new version back to the file and stage it.

3. Commit with the provided message (include the new version in the commit):
   ```
   git commit -m "<message>"
   ```

4. Run the PR creation script:
   ```
   & .\gh_acreate_pr.ps1
   ```

5. Wait for the script to complete and report the result.
