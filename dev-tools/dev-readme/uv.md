# UV - Fast Python Package & Project Manager

**uv** is an extremely fast Python package and project manager written in Rust by
[Astral](https://astral.sh) (the creators of Ruff). It replaces pip, pip-tools, virtualenv,
and even pyenv — all in one tool, 10-100x faster.

- Official docs: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
- PyPI: https://pypi.org/project/uv/

---

## 1. Installing UV

### Recommended: Standalone Installer (no Python needed!)

**Windows (PowerShell):**  boaz:recomended
```powershell
# with taht uv self update works
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

```

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows alternatives:**
```powershell
# Via WinGet (Windows Package Manager)
winget install --id=astral-sh.uv -e

# Via Scoop
scoop install main/uv
```

### Can I install uv via pip? (The Chicken-and-Egg Question)

**Yes, you can** — and there's no real chicken-and-egg problem:

```bash
pip install uv
```

**Why it works:** uv is a standalone Rust binary distributed as a Python wheel.
When you `pip install uv`, you're just downloading a prebuilt binary — uv doesn't
depend on Python at runtime. It's like installing `ruff` via pip.

**However, the standalone installer is preferred because:**
- It doesn't pollute any Python environment
- uv can then manage Python itself (install Python versions!)
- `uv self update` works cleanly
- No dependency on pip being available

**Bottom line:** Use `pip install uv` if you want a quick start. Switch to the
standalone installer when you're ready for uv to fully manage your toolchain.

---

## 2. Updating UV

```bash
# If installed via standalone installer:
uv self update
  error: Self-update is only available for uv binaries installed via the standalone installation scripts.

  If you installed uv with pip, brew, or another package manager, update uv with `pip install --upgrade`, `brew upgrade`,

# If installed via pip:
pip install --upgrade uv

# If installed via WinGet:
winget upgrade --id=astral-sh.uv

# If installed via Scoop:
scoop update uv
```

---

## 3. Core Concepts — How UV Differs from pip

| Concept | pip | uv |
|---------|-----|-----|
| Install packages | `pip install X` | `uv add X` (adds to pyproject.toml) |
| Install from file | `pip install -r requirements.txt` | `uv sync` (uses uv.lock) |
| Create venv | `python -m venv .venv` | `uv venv` (or automatic) |
| Run in venv | `source .venv/bin/activate && python` | `uv run python` (no activation!) |
| Dev dependencies | `pip install -e ".[dev]"` | `uv sync --group dev` |
| Lock versions | `pip freeze > requirements.txt` | `uv lock` (automatic uv.lock) |
| Install Python | External (pyenv, python.org) | `uv python install 3.13` |

### Key Workflow Difference

With **pip**, you manually manage venvs and activate them:
```bash
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
python -m pytest tests/
```

With **uv**, it's all automatic:
```bash
uv sync --group dev       # Creates venv + installs everything
uv run pytest tests/      # Runs in the project venv (no activation!)
```

---

## 4. pyproject.toml Changes

### What Stays the Same

Your `[project]` metadata, dependencies, and tool configs (mypy, pyright, pytest, ruff)
are **standard PEP 621** — they work with both pip and uv unchanged.

### What Changes

#### a) Build System (optional change)

Your current setup:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

**You can keep this as-is.** uv respects any PEP 517 build backend.

If you want to switch to a simpler build backend (optional):
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### b) Dev Dependencies — Use `[dependency-groups]` (PEP 735)

Your current approach (pip-style optional-dependencies):
```toml
[project.optional-dependencies]
dev = [
    "pytest",
    "mypy",
    "ruff",
    ...
]
```

The modern uv approach uses **dependency groups** (PEP 735):
```toml
[dependency-groups]
dev = [
    "pytest",
    "pytest-xdist",
    "mypy",
    "pyright==1.1.408",
    "vulture",
    "ruff",
    "types-colorama",
    "types-keyboard",
    "Pillow",
    "tabulate",
]
```

**Why?** Dependency groups are for development/CI tools that aren't part of the
distributed package. `optional-dependencies` are for optional features that end-users
install (like your `pyglet1`/`pyglet2` extras — those should stay as optional-dependencies).

#### c) Package Discovery (if switching build backend)

With setuptools you have:
```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["cube*"]
```

With hatchling, you'd use:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/cube"]
```

**If you keep setuptools as build backend, no change needed here.**

#### d) uv-Specific Configuration (optional)

```toml
[tool.uv]
# Pin Python version for the project
python = "3.13"

# Override dependency constraints
# override = ["some-package>=2.0"]
```

### Minimal Migration Example

Here's what your pyproject.toml could look like with minimal changes
(keeping setuptools, just adding dependency-groups):

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "cubesolve"
version = "0.1.0"
# ... all your existing metadata stays the same ...

dependencies = [
    "pyglet>=2.0",
    "PyOpenGL",
    "numpy",
    # ... same as before ...
]

[project.optional-dependencies]
# These stay — they're user-facing extras
pyglet1 = ["pyglet>=1.5,<2.0"]
pyglet2 = ["pyglet>=2.0"]

# Move dev from here to [dependency-groups]
# dev = [...]  # REMOVE this

[dependency-groups]
# NEW: dev tools go here
dev = [
    "pytest",
    "pytest-xdist",
    "mypy",
    "pyright==1.1.408",
    "vulture",
    "ruff",
    "types-colorama",
    "types-keyboard",
    "Pillow",
    "tabulate",
]
```

---

## 5. New Files — uv.lock

When you run `uv lock` or `uv sync`, uv creates a **uv.lock** file. This is similar
to `package-lock.json` in Node.js:

- **Exact pinned versions** of all dependencies (including transitive)
- **Cross-platform** — locks for all platforms in one file
- **Deterministic** — same lock file = same install everywhere

**Should you commit uv.lock?**
- **Applications (like this project): YES** — ensures reproducible environments
- **Libraries: Usually no** — let consumers resolve their own versions

Add to `.gitignore` only if you don't want to lock (not recommended for apps).

---

## 6. Day-to-Day Commands

### Project Setup (first time)
```bash
uv sync                        # Install all deps (creates .venv automatically)
uv sync --group dev            # Install deps + dev tools
uv sync --extra pyglet2        # Install deps + pyglet2 extra
uv sync --group dev --extra pyglet2  # Both
```

### Adding/Removing Dependencies
```bash
uv add requests                # Add to [project.dependencies]
uv add --group dev pytest-cov  # Add to [dependency-groups.dev]
uv remove requests             # Remove
```

### Running Commands (no venv activation needed!)
```bash
uv run python -m pytest tests/ -v
uv run python -m mypy -p cube
uv run python -m cube.main_pyglet
```

### Managing Python Versions
```bash
uv python install 3.13         # Install Python 3.13
uv python install 3.14         # Install Python 3.14
uv python list                 # Show available/installed versions
uv python pin 3.13             # Pin project to 3.13 (creates .python-version)
```

### Creating Multiple venvs (for pyglet1 vs pyglet2)
```bash
# Default venv with pyglet2
uv sync --group dev --extra pyglet2

# Separate venv for pyglet1 testing
uv venv .venv_pyglet_legacy --python 3.13
uv pip install -e ".[dev,pyglet1]" --python .venv_pyglet_legacy
```

### Lock File Operations
```bash
uv lock                        # Regenerate uv.lock from pyproject.toml
uv lock --upgrade              # Upgrade all deps to latest compatible
uv lock --upgrade-package numpy # Upgrade just numpy
```

---

## 7. Migration Checklist for This Project

1. [ ] Install uv: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. [ ] Verify: `uv --version`
3. [ ] Move `[project.optional-dependencies].dev` to `[dependency-groups].dev`
4. [ ] Keep `pyglet1`/`pyglet2` in `[project.optional-dependencies]` (user-facing extras)
5. [ ] Run `uv sync --group dev --extra pyglet2` (creates .venv + uv.lock)
6. [ ] Verify: `uv run python -m pytest tests/ -v --ignore=tests/gui -m "not slow"`
7. [ ] Add `uv.lock` to git
8. [ ] Update CLAUDE.md run commands to use `uv run` prefix
9. [ ] (Optional) Set up `.venv_pyglet_legacy` for pyglet1 testing

---

## 8. pip Compatibility Mode

uv provides a **drop-in pip replacement** if you need it:

```bash
uv pip install package-name         # Like pip install
uv pip install -e ".[dev]"          # Like pip install -e
uv pip install -r requirements.txt  # Like pip install -r
uv pip freeze                       # Like pip freeze
uv pip list                         # Like pip list
```

This is useful during migration — you can use `uv pip` as a faster pip
without changing your workflow, then gradually adopt `uv add`/`uv sync`.

---

## 9. PyCharm Integration

**Issue:** PyCharm's "Python Packages" tab may show no packages after setting the
interpreter to uv's `.venv/Scripts/python.exe`.

**Why:** PyCharm uses its own package scanner, which sometimes doesn't detect uv-installed
packages. The packages ARE installed and work fine — it's a PyCharm display issue.

**Workaround:** Use the terminal to verify:
```bash
uv pip list                    # List all installed packages
uv pip list | findstr pytest   # Check if a specific package is installed (Windows)
uv pip list | grep pytest      # Check if a specific package is installed (Linux/macOS)
```

**PyCharm setup:**
1. Settings -> Project -> Python Interpreter
2. Add Interpreter -> Existing -> select `.venv/Scripts/python.exe`
3. Packages will work even if the Packages tab looks empty

---

## 10. Quick Reference Card

```
uv sync              = pip install -e ".[dev]"  (but with lockfile)
uv add X             = pip install X + update pyproject.toml
uv remove X          = pip uninstall X + update pyproject.toml
uv run cmd           = activate venv + run cmd (in one step)
uv lock              = pip freeze (but smarter, cross-platform)
uv python install    = pyenv install (but faster)
uv self update       = pip install --upgrade uv
uv pip install X     = pip install X (compatibility mode)
```
