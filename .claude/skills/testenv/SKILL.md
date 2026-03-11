---
name: testenv
user_invocable: true
description: |
  Set up the Python test environment on Linux/web sessions.
  Installs uv, syncs dependencies (including kociemba with PEP 517 build),
  and verifies the environment by running a kociemba test.
  Triggered by "/testenv".
---

# Test Environment Setup

This skill sets up the Python development environment from scratch on a Linux/web session.
It performs explicit, deterministic steps — no guessing.

## When to Use

Run `/testenv` at the start of every new web session, or whenever the environment is broken/missing.

## Steps — Execute in Order

### Step 1: Install uv (if not already installed)

```bash
# Check if uv is available
which uv
```

If `uv` is not found, install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then verify:

```bash
uv --version
```

### Step 2: Sync the environment with uv

Run from the project root (`/home/user/cubesolve`):

```bash
cd /home/user/cubesolve && uv sync --group dev
```

**Why this works for kociemba:** `uv` uses PEP 517 builds by default (unlike plain `pip` which needs the `--use-pep517` flag). So `uv sync` builds kociemba correctly without any extra flags.

### Step 3: Verify kociemba is installed

```bash
cd /home/user/cubesolve && uv run python -c "import kociemba; print('kociemba OK:', kociemba.solve('DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD'))"
```

Expected output: a solution string like `"D2 R' D' F2 B D R2 D2 R' F2 D' F2 U' B2 L2 U2 D R2 U"`.

If this fails, fall back to explicit pip install:

```bash
cd /home/user/cubesolve && uv run python -m pip install kociemba --use-pep517
```

Then re-verify.

### Step 4: Run a kociemba test to confirm everything works

```bash
cd /home/user/cubesolve && CUBE_QUIET_ALL=1 uv run python -m pytest tests/algs/test_cube.py::test_m_rotation_and_solve_kociemba -v
```

This test scrambles a cube with an M rotation and solves it using the Kociemba solver. It must PASS.

If it fails, investigate and report the error — do NOT skip or ignore it.

## Success Criteria

The skill is complete when ALL of these are true:

1. `uv --version` prints a version
2. `uv sync --group dev` completes without errors
3. `import kociemba` works in the uv-managed Python
4. `test_m_rotation_and_solve_kociemba` PASSES

## Output Format

After running all steps, print a summary:

```
## Test Environment Setup — Complete

| Step                  | Status |
|-----------------------|--------|
| uv installed          | OK     |
| uv sync --group dev   | OK     |
| kociemba importable   | OK     |
| kociemba test passes  | OK     |

Environment is ready. You can run tests with:
  CUBE_QUIET_ALL=1 uv run python -m pytest tests/ --ignore=tests/gui --ignore=tests/console --ignore=tests/webgl --ignore=tests/backends -v
```
