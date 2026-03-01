# 2x2 Rubik's Cube Implementation

This document describes the full implementation of 2x2 Rubik's cube support,
covering domain model changes, the dedicated solver, scrambler fixes, GUI
backend adaptations, and the new size-selection UI across all backends.

---

## Table of Contents

1. [Overview](#overview)
2. [Domain Model Changes](#domain-model-changes)
   - [What a 2x2 Cube Lacks](#what-a-2x2-cube-lacks)
   - [Virtual Center Colors](#virtual-center-colors)
   - [Why Virtual Colors Need Slice Move Mappings](#why-virtual-colors-need-slice-move-mappings)
   - [Part Model Guards](#part-model-guards)
3. [Solver](#solver)
   - [Algorithm Overview](#algorithm-overview)
   - [S4 Permutation Handling](#s4-permutation-handling)
   - [Solver Routing](#solver-routing)
4. [Scrambler Fix](#scrambler-fix)
5. [Application Layer](#application-layer)
6. [GUI Backend Fixes](#gui-backend-fixes)
   - [Legacy Viewer Pipeline](#legacy-viewer-pipeline)
   - [Modern GL Pipeline (pyglet2)](#modern-gl-pipeline-pyglet2)
   - [Console Viewer](#console-viewer)
   - [Web/WebGL Backend](#webwebgl-backend)
7. [Size Selection UI](#size-selection-ui)
   - [SetSizeCommand](#setsizecommand)
   - [Pyglet2 Toolbar](#pyglet2-toolbar)
   - [Web Toolbar](#web-toolbar)
8. [File Change Summary](#file-change-summary)
9. [Testing](#testing)

---

## Overview

A 2x2 Rubik's cube has **only 8 corner pieces**. There are no edges and no
centers. This means `n_slices = cube_size - 2 = 0`. Every subsystem that
assumed at least one slice (edges, centers, slice moves) had to be guarded.

The implementation was done across 3 commits:

| Commit   | Description                                                  |
|----------|--------------------------------------------------------------|
| e2bdbd0  | Full 2x2 domain model + solver + scrambler + app integration |
| 01128dc  | GUI backend fixes (headless, console, web/WebGL rendering)   |
| eaa9737  | Size selection buttons in pyglet2 and web backends           |

---

## Domain Model Changes

### What a 2x2 Cube Lacks

| Property        | 3x3          | 2x2       |
|-----------------|--------------|-----------|
| Corners         | 8            | 8         |
| Edges           | 12           | 0         |
| Centers         | 6            | 0 (virtual) |
| `n_slices`      | 1            | 0         |
| Slice moves (M/E/S) | Physical | Virtual   |

On a 3x3, `face.color` is derived from the physical center sticker on that
face. On a 2x2, there is no center sticker, yet the system still needs
`face.color` to determine which color "belongs" to each face — this is required
for `match_face`, `in_position`, `position_id`, `color_2_face`, and the
solver's concept of "white face" / "yellow face".

### Virtual Center Colors

**File:** `src/cube/domain/model/Center.py`

Each `Center` object gains a `_virtual_color` attribute. On construction, if
the center has no slices (2x2), it stores the face's `original_color`:

```python
class Center(Part):
    __slots__ = ("_slices", "_face_ref", "_virtual_color")

    def __init__(self, center_slices, face=None):
        self._virtual_color: "Color | None" = None
        if not center_slices or not center_slices[0]:
            if face is not None:
                self._virtual_color = face.original_color
```

The `color` property returns `_virtual_color` when there are no slices:

```python
@property
def color(self):
    if not self._slices:
        return self._virtual_color
    return self.edg().color
```

### Why Virtual Colors Need Slice Move Mappings

This is the key insight of the 2x2 model support.

On a 3x3, a whole-cube rotation like **X** is decomposed into face moves:

```
X = R + M' + L'
```

The M slice move physically moves the center sticker from U to F (for example),
so `face.color` updates automatically because the sticker moved.

On a 2x2, `n_slices = 0`, so the M slice has **nothing to move**. After a
whole-cube X rotation, the corners rotate correctly (via R and L'), but the
virtual center colors are never updated — `face.color` becomes stale.

The fix is in `Slice.rotate()`:

**File:** `src/cube/domain/model/Slice.py`

```python
# For 2x2 cubes, rotate virtual center colors to track whole-cube rotations
if self.n_slices == 0:
    self._rotate_virtual_center_colors(n)
    return
```

The mapping table defines which faces each slice axis cycles:

```python
_VIRTUAL_COLOR_CYCLES: dict[SliceName, tuple[FaceName, ...]] = {
    SliceName.M: (FaceName.U, FaceName.F, FaceName.D, FaceName.B),
    SliceName.E: (FaceName.F, FaceName.R, FaceName.B, FaceName.L),
    SliceName.S: (FaceName.L, FaceName.U, FaceName.R, FaceName.D),
}
```

When M rotates by 1 quarter turn: U's virtual color goes to F, F's to D,
D's to B, B's to U. This exactly mirrors what the physical M slice would do
on a 3x3 — keeping `face.color` consistent after whole-cube rotations.

### Part Model Guards

**File:** `src/cube/domain/model/Part.py`

Several fixes were needed:

1. **`fixed_id` assertion**: Changed from `assert self._fixed_id` to
   `assert self._fixed_id is not None` — because an empty `frozenset` is
   falsy, causing assertion failures for 2x2 edges/centers.

2. **`has_slices` property**: New property to distinguish real parts (corners
   on 2x2) from empty-slice parts (edges/centers on 2x2):

   ```python
   @property
   def has_slices(self) -> bool:
       return next(self.all_slices, None) is not None
   ```

3. **Empty-edge guards**: `position_id`, `in_position`, `match_face`, and
   `colors_id_by_color` all check for empty `_edges` before accessing them.

**File:** `src/cube/domain/model/Edge.py` — Graceful empty-slice handling in
`color`, `get_slice_by_ltr_index`, `n_slices`.

**File:** `src/cube/domain/model/Face.py` — Support for 0 center slices, skip
marker setup for 2x2.

**File:** `src/cube/domain/model/Cube.py` — Tolerate `n_slices=0` in
construction.

**File:** `src/cube/domain/model/CubeSanity.py` — Skip center-based sanity
checks for 2x2.

---

## Solver

### Algorithm Overview

**File:** `src/cube/domain/solver/_2x2/Solver2x2.py` (290 lines)

The solver uses a beginner layer-by-layer method adapted for corner-only cubes:

1. **Bottom layer** (4 white corners): Position and orient each corner into its
   slot using the classic `D' R' D R` and `D F D' F'` insertion algorithms.

2. **Top layer positioning**: Permute the 4 yellow-face corners into their
   correct slots (ignoring orientation) using the A-perm algorithm:
   `U R U' L' U R' U' L` (a 3-cycle).

3. **Top layer orientation**: Twist each corner in-place using the commutator
   `(R' D' R D) * 2`, rotating U between corners. The total twist cancels out
   over all 4 corners.

### S4 Permutation Handling

The top layer has 4 corners that can be in any of the 24 permutations of S_4.
The solver handles all permutation types:

| Type                  | Count | Strategy                                |
|-----------------------|-------|-----------------------------------------|
| Identity              | 1     | Already solved                          |
| 4-cycle               | 6     | U rotations (1-3 quarter turns)         |
| 3-cycle (even)        | 8     | A-perm (1-2 applications with Y setup)  |
| Double transposition  | 3     | A-perm converts to 3-cycle, then solve  |
| Transposition (odd)   | 6     | U converts to 3-cycle, then solve       |

The A-perm fixes the FRU corner and cycles BRU -> BLU -> FLU -> BRU. By
rotating the in-position corner to FRU first, any 3-cycle is solvable in one
application. The loop runs up to 12 iterations to handle cascading conversions.

### Solver Routing

**File:** `src/cube/domain/solver/Solvers.py`

The `default()` factory routes based on cube size:

- Size 2: `Solver2x2`
- Size 3+: `LayerByLayerNxNSolver`

**File:** `src/cube/domain/solver/SolverName.py`

Added `TWO_BY_TWO` with `min_size=2`, `max_size=2`.

---

## Scrambler Fix

**File:** `src/cube/domain/algs/Scramble.py`

The scrambler called `randint(1, max_slice)` where `max_slice = cube_size - 2`.
For 2x2, this becomes `randint(1, 0)` which raises `ValueError`.

Fix: guard slice randomization behind `if max_slice >= 1:`.

---

## Application Layer

**File:** `src/cube/application/app.py`

When the cube size changes via `app.reset(cube_size)`, the solver must be
re-created (a 3x3 solver cannot solve a 2x2 cube). Added:

```python
def reset(self, cube_size: int | None = None):
    self.cube.reset(cube_size)
    self.op.reset()
    self._slv = Solvers.default(self.op)
    self._error = None
```

---

## GUI Backend Fixes

### Legacy Viewer Pipeline

The legacy viewer pipeline is shared by headless, web, and legacy pyglet
backends:

```
GCubeViewer -> _Board -> _FaceBoard -> _Cell
```

**File:** `src/cube/presentation/viewer/_faceboard.py`

Three fixes:

1. **Filter parts by `has_slices`**: The cell dictionary only includes parts
   that have actual slices, preventing KeyError when looking up 2x2 edge/center
   parts.

2. **2x2 geometry branch**: `prepare_gui_geometry` creates only 4 corner cells
   (instead of the 9-cell 3x3 grid):

   ```python
   if f.cube.n_slices == 0:
       _create_cell(1, 0, f.corner_top_left)
       _create_cell(1, 1, f.corner_top_right)
       _create_cell(0, 0, f.corner_bottom_left)
       _create_cell(0, 1, f.corner_bottom_right)
   ```

3. **2x2 coordinate calculation**: Each corner occupies half the face width/height
   (instead of one-third on 3x3).

**File:** `src/cube/presentation/viewer/_board.py`

Skip parts without slices in `finish_faces`:

```python
if not p.has_slices:
    continue
```

### Modern GL Pipeline (pyglet2)

The modern GL pipeline (`ModernGLCubeViewer -> ModernGLBoard -> ModernGLFace ->
ModernGLCell`) is already size-agnostic — it iterates over whatever parts exist.
No changes were needed.

### Console Viewer

**File:** `src/cube/presentation/gui/backends/console/ConsoleViewer.py`

Skip `edge.plot_cell` and `center.plot_cell` for 2x2 cubes (these parts have no
slices and no meaningful visual representation).

### Web/WebGL Backend

The web backend uses `WebAppWindow -> GCubeViewer` (same legacy pipeline), so
all `_FaceBoard`/`_Board` fixes apply automatically. The JavaScript `cube.js`
rendering is size-agnostic (draws quads and lines from server data). No
backend-specific rendering changes were needed.

---

## Size Selection UI

### SetSizeCommand

**File:** `src/cube/presentation/gui/commands/concrete.py`

New command that sets the cube to a specific size:

```python
@dataclass(frozen=True)
class SetSizeCommand(Command):
    size: int

    def execute(self, ctx: CommandContext) -> CommandResult:
        if ctx.vs.cube_size != self.size:
            ctx.vs.cube_size = self.size
            ctx.app.reset(ctx.vs.cube_size)
        return CommandResult()
```

**File:** `src/cube/presentation/gui/commands/registry.py`

Registered as `SIZE_2`, `SIZE_3`, `SIZE_4`, `SIZE_5`.

### Pyglet2 Toolbar

**File:** `src/cube/presentation/gui/backends/pyglet2/GUIToolbar.py`

Added size buttons "2", "3", "4", "5" alongside existing "-" and "+" buttons:

```python
toolbar.add_button("2", Commands.SIZE_2)
toolbar.add_button("3", Commands.SIZE_3)
toolbar.add_button("4", Commands.SIZE_4)
toolbar.add_button("5", Commands.SIZE_5)
toolbar.add_button("-", Commands.SIZE_DEC)
toolbar.add_button("+", Commands.SIZE_INC)
```

### Web Toolbar

The web backend previously had no toolbar — just a bare canvas. A full toolbar
was added with size, scramble, and solve controls.

**File:** `src/cube/presentation/gui/backends/web/static/index.html`

HTML toolbar with grouped buttons:

```html
<div id="toolbar">
    <div class="group">
        <span class="group-label">Size:</span>
        <button data-command="SIZE_2">2</button>
        <button data-command="SIZE_3">3</button>
        <button data-command="SIZE_4">4</button>
        <button data-command="SIZE_5">5</button>
        <button data-command="SIZE_DEC">-</button>
        <button data-command="SIZE_INC">+</button>
    </div>
    ...
</div>
```

**File:** `src/cube/presentation/gui/backends/web/static/cube.js`

Click handler sends commands via WebSocket:

```javascript
document.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-command]');
    if (button && window.cubeClient && window.cubeClient.connected) {
        window.cubeClient.send({
            type: 'command',
            name: button.dataset.command
        });
    }
});
```

**File:** `src/cube/presentation/gui/backends/web/WebEventLoop.py`

New `command` message type handler:

```python
elif msg_type == "command":
    command_name = data.get("name", "")
    if self._command_handler:
        self._command_handler(command_name)
```

**File:** `src/cube/presentation/gui/backends/web/WebAppWindow.py`

Command handler dispatches by name:

```python
def _handle_browser_command(self, command_name: str) -> None:
    command = Commands.get_by_name(command_name)
    self.inject_command(command)
```

This is more general than key bindings — digit keys 2-5 are already bound to
scramble commands, so toolbar buttons bypass key bindings entirely and dispatch
commands by name.

---

## File Change Summary

### Domain Model (Commit 1)

| File | Change |
|------|--------|
| `Center.py` | `_virtual_color` attribute, virtual color property |
| `Slice.py` | `_VIRTUAL_COLOR_CYCLES` table, `_rotate_virtual_center_colors()` |
| `Part.py` | `has_slices` property, `fixed_id` assert fix, empty-edge guards |
| `Edge.py` | Empty-slice handling in `color`, `get_slice_by_ltr_index` |
| `Face.py` | 0 center slices support, skip marker setup |
| `Cube.py` | `n_slices=0` tolerance |
| `CubeSanity.py` | Skip center checks for 2x2 |

### Solver (Commit 1)

| File | Change |
|------|--------|
| `_2x2/Solver2x2.py` | **NEW** — 290-line beginner corner-only solver |
| `_2x2/__init__.py` | **NEW** — package init |
| `SolverName.py` | `TWO_BY_TWO` enum member |
| `Solvers.py` | Routes size 2 to `Solver2x2` |

### Application (Commit 1)

| File | Change |
|------|--------|
| `app.py` | Re-create solver in `reset()` |
| `Scramble.py` | `max_slice < 1` guard |

### GUI Backends (Commit 2)

| File | Change |
|------|--------|
| `_faceboard.py` | 2x2 cell grid, coordinate calc, `has_slices` filter |
| `_board.py` | Skip parts without slices in `finish_faces` |
| `ConsoleViewer.py` | Skip edge/center `plot_cell` for 2x2 |

### Size Selection UI (Commit 3)

| File | Change |
|------|--------|
| `concrete.py` | `SetSizeCommand` |
| `registry.py` | `SIZE_2/3/4/5` constants |
| `GUIToolbar.py` | Size buttons in pyglet2 toolbar |
| `index.html` | Full toolbar with size/scramble/solve buttons |
| `cube.js` | Toolbar click handler sending command messages |
| `WebEventLoop.py` | `command` message type + handler callback |
| `WebAppWindow.py` | `_handle_browser_command()` dispatcher |

---

## Testing

All tests pass with zero regressions:

- **6711+ non-GUI tests** pass (only pre-existing Kociemba module failures excluded)
- **9 GUI tests** pass (headless backend), including:
  - `test_scramble_and_solve[headless-2]` — 2x2 scramble+solve
  - `test_size_dec_to_2x2_and_solve[headless]` — size transition 4->3->2, scramble, solve
- **500/500 stress test** (2x2 scramble+solve with random seeds) passed during development
