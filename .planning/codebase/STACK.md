# Technology Stack

**Analysis Date:** 2026-01-28

## Languages

**Primary:**
- Python 3.10+ - Main application language, required by `pyproject.toml`
- Python 3.14 - Supported version (tested against in CI)

**Secondary:**
- JavaScript - Web frontend for browser-based backend (`src/cube/presentation/gui/backends/web/static/`)
- HTML/CSS - Web UI components for web backend

## Runtime

**Environment:**
- Python 3.10, 3.11, 3.12, 3.13, 3.14 - All supported (see `pyproject.toml` classifiers)

**Package Manager:**
- pip - Standard Python package manager
- setuptools>=61.0 - Build system
- wheel - Distribution format
- Lockfile: Not present (uses `pyproject.toml` for dependency management)

## Frameworks

**Core:**
- pyglet 2.0+ (primary) - OpenGL 3D graphics rendering, modern backend
- PyOpenGL - OpenGL bindings, used for GLU functions not in pyglet 2.0
- numpy - Numerical computing, matrix operations for graphics

**Alternative/Legacy:**
- pyglet 1.5.x (optional) - Legacy OpenGL support, can be installed via `[pyglet1]` extra
- tkinter - Built-in Python GUI (alternative backend at `src/cube/presentation/gui/backends/tkinter/`)
- aiohttp>=3.9.0 - Async HTTP/WebSocket server for web backend

**Testing:**
- pytest - Test runner and framework
- pytest-xdist - Parallel test execution
- mypy - Static type checker
- pyright==1.1.408 - Strict type checker (standard mode)
- ruff - Linter and code formatter
- vulture - Dead code detector

**Development:**
- Pillow - Image generation for test textures (`resources/faces/generate_images.py`)
- tabulate - Test output formatting

## Key Dependencies

**Critical:**
- kociemba - Near-optimal Rubik's cube solver (two-phase algorithm, 18-22 moves)
  - Used in `src/cube/domain/solver/_3x3/kociemba/Kociemba3x3.py`
  - Provides 3x3 solving via `kociemba.solve(cube_string)`

**Infrastructure:**
- keyboard - Global keyboard event capture for GUI input handling
- colorama - Cross-platform colored terminal output
- rich - Advanced terminal formatting and colors (console viewer)
- PyYAML - Configuration file parsing
- vecrec - Vector and record handling
- typeguard>=4.4.0 - Runtime type checking validation
- typing_extensions>=4.14.0 - Backported Python 3.13+ typing features (for `@deprecated` decorator)

## Configuration

**Environment:**
- Environment variables for runtime control:
  - `CUBE_DISABLE_CACHE` - Disable cube state caching (set to "1", "true", or "yes")
  - `CUBE_QUIET_ALL` - Suppress debug output during testing
  - Backend-specific configs in `src/cube/application/_config.py`

**Build:**
- `pyproject.toml` - Single source of truth for dependencies, build config, and tool settings
  - Contains setuptools package discovery configuration
  - Pytest, mypy, pyright configurations inline
- Package data includes:
  - `src/cube/resources/faces/**/*.png` - Cube face textures
  - `src/cube/resources/algs/*.txt` - Algorithm definitions

## Platform Requirements

**Development:**
- Windows/Linux/macOS compatible (platform-independent Python)
- Virtual environments: `.venv` (default for pyglet2) and `.venv_pyglet_legacy` (for pyglet 1.5.x)
- Separate venv for legacy pyglet due to incompatible pyglet versions

**Production:**
- Deployment target: Desktop (pyglet backend) or browser (web backend via aiohttp)
- No external cloud dependencies
- No database required (standalone application)
- OpenGL 3.0+ capable GPU recommended for pyglet backend
- Modern browser required for web backend (WebSocket support)

## Solver Dependencies

**Bundled Algorithms:**
- Beginner Solver - Custom LBL (Layer-By-Layer) implementation
- CFOP Solver - Fridrich method for speedcubing
- Kociemba Solver - Two-phase algorithm via `kociemba` package (NxN support via reduction)
- Layer-By-Layer (Direct) Solver - Custom LBL for NxN cubes
- Cage Solver - Specialized solver for big cubes

---

*Stack analysis: 2026-01-28*
