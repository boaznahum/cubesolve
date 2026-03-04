---
name: deploy
description: >
  Deploy the WebGL application to Fly.io. This skill should be used when the user says
  "deploy", "push and deploy", "run automation", "create PR and deploy", or similar.
  Triggered by "/deploy" or when user asks to deploy changes.
---

# Deploy Skill

Deploy current changes to the WebGL dev environment via GitHub Actions + Fly.io.

## Workflow

When deploying, execute these steps in order:

### 1. Version Check

Read `src/cube/resources/version.txt` and compare with the last committed version.
If the version has NOT been bumped since the last commit, bump it:
- Patch (e.g. 1.22.3 -> 1.22.4) for bugfixes/polish
- Minor (e.g. 1.22 -> 1.23) for features

### 2. Commit

If there are uncommitted changes:
- Stage all relevant files (avoid .env, credentials, etc.)
- Write a concise commit message describing the changes
- Include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`

### 3. Push and Run Automation

Push the branch and run the PowerShell deploy script:

```bash
powershell.exe -ExecutionPolicy Bypass -File gh_acreate_pr.ps1
```

This script:
- Displays the version being deployed
- Pushes the current branch
- Pulls `webgl-dev` into current branch (no-op if up to date), then pushes to `webgl-dev`
- Polls for and watches the GitHub Actions deploy run
- Displays the deployed version when done

### 4. Report

After deployment completes, report:
- The deployed version
- Success/failure status
