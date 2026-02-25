# Session: web1 — Three.js Web Frontend + Animation

## Goal
1. ~~Rewrite the JS client (`cube.js`) from Canvas 2D to Three.js WebGL for proper 3D rendering.~~ ✅ Done
2. ~~**Get smooth face rotation animation working**~~ ✅ Done — face visually rotates 0°→90° over ~2s

## Commits Made
- `fcd7063d` — Add web animation manager, Three.js lighting, and sticker gaps
- `33e81fe1` — Add web frontend design plan document
- `806e4eb3` — Rewrite web frontend to Three.js WebGL 3D rendering

## Current Status (end of session 4) — ANIMATION WORKS

### What Works
- 3D cube renders correctly in Chrome via Three.js
- Keyboard controls work (R, L, U, D, F, B, scramble, solve, etc.)
- WebSocket communication is solid
- **Smooth face rotation animation** — 22 frames over ~2s, 127 cmds per frame
- rAF render loop with FIFO queue renders frames smoothly
- Debug progress bar shows angle and queue status

### Root Cause Found & Fixed

**Bug:** `inject_command()` called `update_gui_elements()` after `command.execute()`, which
deleted and recreated ALL display lists with new IDs. But the animation's `_draw()` closure
had captured the OLD display list IDs at creation time → animation tried to call deleted lists.

**Why web-only:** In pyglet, `run_animation()` BLOCKS until animation completes, so
`inject_command()` never calls `update_gui_elements()` during animation. In the web backend,
`run_animation()` returns immediately (non-blocking asyncio), and `update_gui_elements()` runs
before the animation async task even starts.

**Fix (1 line):** In `WebAppWindow.inject_command()`:
```python
if not result.no_gui_update and not self.animation_running:
    self.update_gui_elements()
```

### Display List Lifecycle (confirmed via diagnostics)
- INIT COMPLETE: 192 lists total, 96 empty (from `_create_polygon`), 96 nonempty
- 54 cells × ~3.5 lists each for a 4×4 cube
- All display lists fully populated after `GCubeViewer` construction
- Animation captures IDs at creation → must remain valid throughout animation

## Key Files Modified (uncommitted)

| File | Changes |
|------|---------|
| `WebAppWindow.py` | **THE FIX:** skip `update_gui_elements()` when animation running; speed override to 0 |
| `WebAnimationManager.py` | Replaced `schedule_interval`/`_tick` with async coroutine `_animate_async()` |
| `WebRenderer.py` | Cleaned up diagnostics; improved `end_frame` docstring |
| `WebEventLoop.py` | Key mapping fix (`-`→NUM_SUBTRACT, `=`→NUM_ADD), broadcast uses `create_task` |
| `cube.js` | rAF render loop with FIFO queue, debug progress bar, Three.js shapes |
| `index.html` | Added debug progress bar div below canvas |

## Next Steps
- Remove debug progress bar from cube.js/index.html (or keep as optional)
- Run all checks (ruff, mypy, pyright, tests) before committing
- Commit the working animation fix
- Test with scramble + solve sequence
