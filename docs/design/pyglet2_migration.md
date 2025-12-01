# Pyglet 2.0 Migration Guide

## Overview

This document describes the migration from pyglet 1.5 to pyglet 2.0, and the path forward to modern OpenGL.

**Status:** 🔄 In Progress - Modern OpenGL Migration

> **Decision (2025-12-01):** Since pyglet 2.0 cannot request compatibility profile on Windows,
> we are proceeding with **modern OpenGL migration** (shaders + VBOs) instead.

## Root Cause: Pyglet 2.0 Limitation

### Why It Doesn't Work

Our code uses legacy OpenGL functions (`glBegin`, `glEnd`, `glVertex`, display lists). These require an **OpenGL Compatibility Profile** context.

Pyglet 2.0's `Win32ARBContext` (in `pyglet/gl/win32.py`) creates contexts using `wglCreateContextAttribsARB`, but it does **not** set:
- `WGL_CONTEXT_PROFILE_MASK_ARB = 0x9126`
- `WGL_CONTEXT_COMPATIBILITY_PROFILE_BIT_ARB = 0x00000002`

Without these attributes, Windows drivers default to **Core Profile** (OpenGL 3.3+), which removes all legacy functions.

### Error Observed

```
pyglet.gl.lib.GLException: (0x1282): Invalid operation. The specified operation is not allowed in the current state.
```

This occurs when calling `glEnd()` because `glBegin()` was a no-op in core profile.

### Verification

```python
# GL Version reported: 3.3.0 NVIDIA 560.94
# This is core profile - legacy GL not available
```

### Options Forward

| Option | Effort | Risk | Notes |
|--------|--------|------|-------|
| **Stay on pyglet 1.5** | None | Low | Use existing `pyglet` backend |
| **Rewrite to modern GL** | High (2-4 weeks) | Medium | Shaders, VBOs, manual matrix math |
| **Patch pyglet** | Medium | High | Add profile constants, may break updates |
| **Report pyglet issue** | Low | N/A | May be fixed in future pyglet versions |

**Recommendation:** Continue using the `pyglet` backend with pyglet 1.5.x for now.

---

## Background

### The Problem

Pyglet 2.0 made breaking changes to OpenGL support:

| Feature | Pyglet 1.5 | Pyglet 2.0 |
|---------|-----------|-----------|
| Default context | OpenGL 2.x compat | OpenGL 3.3 core |
| `pyglet.gl` module | Full legacy GL | Empty (modern only) |
| `pyglet.gl.glu` | Available | **Removed** |
| `glBegin/glEnd` | Works | **Not available** |
| Display lists | Works | **Not available** |
| `Label(bold=True)` | Works | **Changed to `weight='bold'`** |

### Our Codebase

The cube solver uses legacy OpenGL extensively:
- **Immediate mode**: `glBegin/glEnd/glVertex` for cube faces
- **Display lists**: `glGenLists/glNewList/glCallList` for performance
- **GLU quadrics**: `gluSphere/gluCylinder` for annotations
- **Fixed pipeline**: `glColor`, `glPushMatrix`, `glRotate`, etc.

---

## Solution: pyglet2 Backend

We created a new `pyglet2` backend that works with pyglet 2.0 while maintaining legacy OpenGL code.

### Key Changes

#### 1. GL Module Import
```python
# pyglet 1.5 (original)
from pyglet import gl

# pyglet 2.0 (new)
from pyglet.gl import gl_compat as gl
```

The `gl_compat` module provides Python bindings for legacy OpenGL functions.

#### 2. GLU Functions (PyOpenGL)
```python
# pyglet 1.5 - GLU in pyglet.gl
quadric = gl.gluNewQuadric()
gl.gluSphere(quadric, radius, slices, stacks)

# pyglet 2.0 - GLU from PyOpenGL
from OpenGL import GLU as glu
quadric = glu.gluNewQuadric()
glu.gluSphere(quadric, radius, slices, stacks)
```

#### 3. OpenGL Context Configuration
```python
# pyglet 2.0 defaults to 3.3 core profile (no legacy support!)
# Request 2.1 to get compatibility profile:
gl_config = pyglet.gl.Config(major_version=2, minor_version=1)
window = pyglet.window.Window(config=gl_config)
# Driver returns 4.6 compatibility context - legacy GL works!
```

#### 4. Label API Change
```python
# pyglet 1.5
label = pyglet.text.Label("Text", bold=True)

# pyglet 2.0
label = pyglet.text.Label("Text", weight='bold')
```

---

## File Structure

```
src/cube/presentation/gui/backends/
├── pyglet/           # Original (pyglet 1.5, legacy GL)
│   ├── PygletRenderer.py
│   ├── PygletWindow.py
│   └── ...
└── pyglet2/          # New (pyglet 2.0, gl_compat + PyOpenGL)
    ├── PygletRenderer.py    # Uses gl_compat, PyOpenGL GLU
    ├── PygletAppWindow.py   # GL 2.1 config, weight='bold'
    ├── PygletWindow.py      # GL 2.1 config
    └── ...
```

---

## Dependencies

### pyproject.toml
```toml
dependencies = [
    "pyglet>=1.5.0",  # Works with both 1.5 and 2.0
    ...
]

[project.optional-dependencies]
pyglet2 = [
    "PyOpenGL",  # Required for GLU functions in pyglet 2.0
]
```

### Installation
```bash
# For pyglet 2.0 support:
pip install pyglet>=2.0 PyOpenGL
```

---

## Usage

```bash
# Use original pyglet backend (pyglet 1.5)
python -m cube.main_any_backend --backend=pyglet

# Use pyglet2 backend (pyglet 2.0)
python -m cube.main_any_backend --backend=pyglet2
```

---

## Testing

```bash
# Create test environment with pyglet 2.0
python -m venv .venv_pyglet2
.venv_pyglet2/Scripts/pip install pyglet>=2.0 PyOpenGL
.venv_pyglet2/Scripts/pip install -e .[dev]

# Run tests
.venv_pyglet2/Scripts/python -m pytest tests/ -v --ignore=tests/gui
```

---

## Modern OpenGL Migration Plan

Since compatibility profile is not available on Windows, we're migrating to **modern OpenGL 3.3+ core profile**.

### Incremental Migration Strategy

The key insight: migrate **one ShapeRenderer method at a time** while keeping the app working.

#### Phase 1: Infrastructure ✅ COMPLETE
- [x] Verify modern GL symbols work in pyglet 2.0 context
- [x] Create basic shader infrastructure (`shaders.py` - compile, link, error handling)
- [x] Create basic VBO/VAO wrapper classes (`buffers.py`)
- [x] Add matrix math library (`matrix.py` - Mat4, perspective, rotate, translate)

#### Phase 2: Simple Shapes ✅ COMPLETE
- [x] Migrate `line()` - working in ModernGLRenderer
- [x] Migrate `quad()` - working in ModernGLRenderer
- [x] Migrate `triangle()` - working in ModernGLRenderer

#### Phase 3: Cube Rendering ✅ WORKING (partial)
- [x] Create `ModernGLCubeViewer` - generates cube geometry from model
- [x] Per-vertex colors for stickers
- [x] Grid lines for cell borders
- [x] Face rotations work (instant, no animation)
- [x] Scramble/Solve work (instant)
- [x] Mouse drag (camera orbit)
- [x] Mouse scroll (zoom)
- [ ] **Animation** - NOT WORKING (display lists not available)
- [ ] Mouse picking - untested

#### Phase 4: Animation (PENDING)
- [ ] Design VBO-based animation system
- [ ] Per-piece matrix transforms
- [ ] Integration with AnimationManager

### Modern GL Symbols Test

```python
# These should work in pyglet 2.0 core profile context:
from pyglet.gl import gl

# Core profile functions
gl.glGenBuffers        # VBOs
gl.glGenVertexArrays   # VAOs
gl.glCreateShader      # Shaders
gl.glCreateProgram     # Shader programs
gl.glUniform3f         # Shader uniforms
```

**Tested 2025-12-01:** All 22 modern GL symbols available ✅

### Shader + VBO Rendering Test

Verified that full modern GL pipeline works:
- Vertex shader compiles ✅
- Fragment shader compiles ✅
- Program links ✅
- VBO uploads data ✅
- VAO binds attributes ✅
- Triangle renders with vertex colors ✅

```python
# Minimal vertex shader
VERTEX_SHADER = '''
#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aColor;
out vec3 vertexColor;
void main() {
    gl_Position = vec4(aPos, 1.0);
    vertexColor = aColor;
}
'''

# Minimal fragment shader
FRAGMENT_SHADER = '''
#version 330 core
in vec3 vertexColor;
out vec4 FragColor;
void main() {
    FragColor = vec4(vertexColor, 1.0);
}
'''
```

---

## Legacy Reference: Compatibility Mode Attempt

The following documents our **failed attempt** to use legacy GL in pyglet 2.0.
Kept for historical reference.

### Migration Scope

| Component | Current (Legacy) | Modern OpenGL 3.3+ |
|-----------|-----------------|-------------------|
| Rendering | `glBegin/glEnd/glVertex` | VBOs + VAOs |
| Caching | Display lists | Pre-compiled VBOs |
| Colors | `glColor3ub` | Shader uniforms |
| Transforms | `glPushMatrix/glRotate` | Matrix math library |
| Projection | `gluPerspective` | Manual matrix calculation |
| Quadrics | `gluSphere/gluCylinder` | Generate geometry manually |

### Example: Quad Rendering

**Current (Legacy)**:
```python
def quad(self, vertices, color):
    gl.glColor3ub(*color)
    gl.glBegin(gl.GL_QUADS)
    for v in vertices:
        gl.glVertex3f(*v)
    gl.glEnd()
```

**Modern OpenGL**:
```python
def quad(self, vertices, color):
    # Create VBO with vertex data
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices, GL_STATIC_DRAW)

    # Use shader program
    glUseProgram(self.shader)
    glUniform3f(self.color_loc, *[c/255 for c in color])

    # Draw
    glBindVertexArray(self.vao)
    glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
```

### Effort Estimate

| Task | Complexity | Notes |
|------|-----------|-------|
| Shader infrastructure | Medium | Vertex + fragment shaders |
| VBO/VAO management | Medium | Replace display lists |
| Matrix library | Low | Use numpy or pyrr |
| Geometry generation | High | Replace GLU quadrics |
| Text rendering | Low | Pyglet handles this |

**Total estimate**: 2-4 weeks for full migration

### Benefits of Modern OpenGL

1. **Performance**: GPU-optimized rendering
2. **Compatibility**: Works with core profile contexts
3. **Features**: Compute shaders, instancing, etc.
4. **Future-proof**: Core profile is the standard

---

## Decision Record

### A5: Pyglet 2.0 vs 1.5 - OpenGL Compatibility

**Date:** 2024-12-01

**Decision:** Create pyglet2 backend using compatibility profile

**Options Considered:**
1. Stay on pyglet 1.5 - Works but misses 2.x improvements
2. Debug pyglet 2.0 with PyOpenGL - Uncertain outcome
3. Full modern OpenGL refactor - Weeks/months of work

**Chosen:** Option 2 + compatibility profile

**Rationale:**
- Compatibility profile works reliably on modern drivers
- Minimal code changes (import paths, Label API)
- Preserves all existing functionality
- Provides path forward to modern GL if needed

**Outcome:** pyglet2 backend working with pyglet 2.1.11

---

## Current Implementation Status (2025-12-01)

### Files in pyglet2 Backend

```
src/cube/presentation/gui/backends/pyglet2/
├── __init__.py           # Backend registration
├── AbstractWindow.py     # Window protocol
├── AppWindowBase.py      # Shared window logic (copied from pyglet)
├── buffers.py            # VBO/VAO buffer management
├── main_g_mouse.py       # Mouse handling (copied from pyglet)
├── matrix.py             # Mat4, perspective, rotate, multiply
├── ModernGLCubeViewer.py # Shader-based cube rendering (10KB)
├── ModernGLRenderer.py   # Modern GL with GLSL shaders (14KB)
├── PygletAnimation.py    # Animation (currently unused)
├── PygletAppWindow.py    # Main window class (15KB)
├── PygletEventLoop.py    # Event loop (same as pyglet)
├── PygletRenderer.py     # gl_compat wrapper (implements protocol)
├── PygletWindow.py       # Base window
├── shaders.py            # Shader compilation utilities
└── Window.py             # Legacy window (unused)
```

### Architecture Notes

The pyglet2 backend has **two parallel renderer implementations**:

| Renderer | GL Mode | Status | Animation Support |
|----------|---------|--------|-------------------|
| `PygletRenderer.py` | `gl_compat` (legacy) | Working | Possible via display lists |
| `ModernGLRenderer.py` | Modern GL 3.3+ | Working | Needs VBO-based approach |

**Currently using:** `ModernGLRenderer` + `ModernGLCubeViewer`

### How Animation Currently Fails

```python
# In PygletAppWindow.__init__():
self._viewer = None  # GCubeViewer disabled!

# In AnimationManager.run_animation():
try:
    viewer = self._window.viewer  # Property access
except RuntimeError:
    # Viewer not initialized - skip animation
    op(alg, False)  # Execute instantly without animation
    return
```

### Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| Cube rendering | ✅ Working | ModernGLCubeViewer with shaders |
| Face rotations | ✅ Working | R/L/U/D/F/B execute instantly |
| Scramble | ✅ Working | Press 1-9 for scrambles |
| Solve | ✅ Working | Press ? for solve |
| Mouse drag | ✅ Working | Camera orbit via matrix.py |
| Mouse scroll | ✅ Working | Z-axis translation |
| Text labels | ✅ Working | pyglet.text.Label (modern GL) |
| Debug logging | ✅ Working | `--debug-all` shows output |
| **Animation** | ❌ Not working | Display lists not available |
| Mouse picking | ❓ Untested | Needs screen_to_world |

### How to Run

```bash
# Requires .venv_pyglet2 with pyglet 2.x
.venv_pyglet2/Scripts/python.exe -m cube.main_any_backend --backend=pyglet2

# With debug output
.venv_pyglet2/Scripts/python.exe -m cube.main_any_backend --backend=pyglet2 --debug-all
```

### Test Results

```bash
# Run tests with pyglet2 backend
.venv_pyglet2/Scripts/python.exe -m pytest tests/gui/test_gui.py -v --backend=pyglet2

# Results:
# - test_simple_quit: PASSED
# - test_face_rotations: PASSED (without animation)
# - test_scramble_and_solve: SKIPPED (needs GCubeViewer)
# - test_multiple_scrambles: SKIPPED (marked skip)
```

### Recent Commits (new-opengl branch)

```
7028e0b Merge debug fixes from main
b7ec97f Fix pyglet2 mouse rotation and key press debug logging
f2cc9ab Fix pyglet2 animation skip and text rendering
dea6893 Add ModernGLCubeViewer for pyglet2 backend with working cube rendering
1ac0103 Fix pyglet2 on_resize called before renderer initialized
ba42268 Integrate ModernGLRenderer with PygletAppWindow
7a62dbb A5: Document pyglet 2.0 compatibility profile limitation
```

### Next Steps for New Session

**Decision needed:** Which path to pursue for animation?

1. **Option A: Use gl_compat** - Fastest path to full feature parity
   - `PygletRenderer.py` already implements all protocols using `gl_compat`
   - Would allow existing `GCubeViewer` + display lists to work
   - Requires: Verify display lists work in compatibility mode
   - Estimated: 1-2 days

2. **Option B: Implement modern animation** - Future-proof but more work
   - Use `ModernGLCubeViewer` for rendering (already working)
   - Implement VBO-based animation (rotate vertex positions per piece)
   - More complex, requires matrix stack per-piece
   - Estimated: 1-2 weeks

**Recommended:** Try Option A first since `PygletRenderer.py` already exists with gl_compat.

---

## References

- [Pyglet 2.0 Migration Guide](https://pyglet.readthedocs.io/en/latest/programming_guide/migration.html)
- [OpenGL Compatibility Profile](https://www.khronos.org/opengl/wiki/OpenGL_Context#Context_types)
- [PyOpenGL Documentation](http://pyopengl.sourceforge.net/documentation/)
