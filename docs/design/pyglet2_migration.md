# Pyglet 2.0 Migration Guide

## Overview

This document describes the migration from pyglet 1.5 to pyglet 2.0, and the path forward to modern OpenGL.

**Status:** ❌ Blocked - Pyglet 2.0 lacks compatibility profile support on Windows

> **Important:** The pyglet2 backend does NOT work with our legacy OpenGL code. See [Root Cause](#root-cause-pyglet-20-limitation) below.

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

## Future: Modern OpenGL Migration (A5.c)

The current solution uses **legacy OpenGL in compatibility mode**. A full modern OpenGL migration would provide better performance and future-proofing.

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

## References

- [Pyglet 2.0 Migration Guide](https://pyglet.readthedocs.io/en/latest/programming_guide/migration.html)
- [OpenGL Compatibility Profile](https://www.khronos.org/opengl/wiki/OpenGL_Context#Context_types)
- [PyOpenGL Documentation](http://pyopengl.sourceforge.net/documentation/)
