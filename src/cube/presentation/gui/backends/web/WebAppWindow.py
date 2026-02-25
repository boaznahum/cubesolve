"""
Web application window implementation.

High-level window combining GUI and application logic.
"""

from __future__ import annotations

import json
import traceback
from collections.abc import Callable
from typing import TYPE_CHECKING

from cube.application.exceptions.ExceptionAppExit import AppExit
from cube.presentation.gui.backends.web.WebEventLoop import WebEventLoop
from cube.presentation.gui.backends.web.WebRenderer import WebRenderer
from cube.presentation.gui.backends.web.WebWindow import WebWindow
from cube.presentation.gui.commands import Command, CommandContext
from cube.presentation.gui.protocols.AppWindow import AppWindow

if TYPE_CHECKING:
    from cube.application.AbstractApp import AbstractApp
    from cube.presentation.gui.commands import CommandSequence
    from cube.presentation.gui.GUIBackendFactory import GUIBackendFactory
    from cube.presentation.viewer.GCubeViewer import GCubeViewer


class WebAppWindow(AppWindow):
    """Web application window implementing AppWindow protocol.

    Combines WebWindow, WebRenderer, and WebEventLoop with
    application logic (cube, solver, animation).
    """

    def __init__(
        self,
        app: "AbstractApp",
        width: int,
        height: int,
        title: str,
        backend: "GUIBackendFactory",
    ):
        self._app = app
        self._backend = backend
        self._width = width
        self._height = height
        self._title = title

        # State for edge solve tracking (used by SOLVE_EDGES command)
        self._last_edge_solve_count: int = 0

        # Get components from backend (singletons)
        self._renderer: WebRenderer = backend.renderer  # type: ignore[assignment]
        self._event_loop: WebEventLoop = backend.event_loop  # type: ignore[assignment]
        self._window: WebWindow = WebWindow(width, height, title)

        # Configure event loop with test mode from app config
        # (Must be done before run() is called so port selection works correctly)
        self._event_loop.gui_test_mode = app.config.gui_test_mode

        # Wire renderer to event loop for WebSocket communication
        self._renderer.set_event_loop(self._event_loop)

        # Wire key handler to event loop (receives keys from browser)
        self._event_loop.set_key_handler(self._handle_browser_key)

        # Wire speed handler to event loop (receives speed from browser slider)
        self._event_loop.set_speed_handler(self._handle_browser_speed)

        # Wire command handler to event loop (receives toolbar button clicks)
        self._event_loop.set_command_handler(self._handle_browser_command)

        # Wire size handler to event loop (receives size from browser slider)
        self._event_loop.set_size_handler(self._handle_browser_size)

        # Wire client connected callback for initial draw
        self._event_loop.set_client_connected_handler(self._on_client_connected)

        # Create viewer
        from cube.presentation.viewer.GCubeViewer import GCubeViewer
        self._viewer = GCubeViewer(app.cube, app.vs, self._renderer)

        # Create non-blocking animation manager for web backend.
        # The standard AnimationManager blocks in a while loop, which would
        # freeze the asyncio event loop. WebAnimationManager queues moves
        # and processes them via scheduled callbacks.
        from .WebAnimationManager import WebAnimationManager

        am = WebAnimationManager(app.vs, app.op)
        app.enable_animation(am)
        am.set_event_loop(self._event_loop)
        am.set_window(self)  # type: ignore[arg-type]
        am.set_web_window(self)
        self._animation_manager: WebAnimationManager = am

        # Use speed from config (user can adjust via slider)

        # Set up event handlers
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up window event handlers."""
        self._window.set_draw_handler(self._on_draw)
        self._window.set_resize_handler(self._on_resize)
        self._window.set_key_press_handler(self._on_key_press)
        self._window.set_close_handler(self._on_close)

    def _on_draw(self) -> None:
        """Handle draw event."""
        import math

        self._renderer.begin_frame()
        self._renderer.clear((217, 217, 217, 255))  # Light gray background

        # Set up view
        vs = self._app.vs
        self._renderer.view.set_projection(self._width, self._height)
        self._renderer.view.load_identity()

        # Camera distance
        offset = vs.offset
        self._renderer.view.translate(float(offset[0]), float(offset[1]), float(offset[2]))

        # Base orientation
        self._renderer.view.rotate(math.degrees(vs.alpha_x_0), 1, 0, 0)
        self._renderer.view.rotate(math.degrees(vs.alpha_y_0), 0, 1, 0)
        self._renderer.view.rotate(math.degrees(vs.alpha_z_0), 0, 0, 1)

        # User-controlled rotation (X/Y/Z keys)
        self._renderer.view.rotate(math.degrees(vs.alpha_x), 1, 0, 0)
        self._renderer.view.rotate(math.degrees(vs.alpha_y), 0, 1, 0)
        self._renderer.view.rotate(math.degrees(vs.alpha_z), 0, 0, 1)

        # Draw cube (static parts; animated parts are hidden during animation)
        self._viewer.draw()

        # Draw animation overlay (rotating parts during face rotation)
        if self._animation_manager:
            self._animation_manager.draw()

        self._renderer.end_frame()

        # Send text overlays to browser
        self._broadcast_text()

    def _on_resize(self, width: int, height: int) -> None:
        """Handle resize event."""
        self._width = width
        self._height = height
        self._renderer.view.set_projection(width, height)

    def _on_key_press(self, event) -> None:
        """Handle key press event."""
        from cube.presentation.gui.key_bindings import lookup_command

        command = lookup_command(event.symbol, event.modifiers, self.animation_running)
        if command:
            self.inject_command(command)

    def _handle_browser_key(self, symbol: int, modifiers: int) -> None:
        """Handle key event from browser via WebSocket."""
        from cube.presentation.gui.Keys import Keys

        # Escape during animation: discard remaining queued moves
        if symbol == Keys.ESCAPE and self.animation_running:
            self._animation_manager.cancel_animation()
            return

        from cube.presentation.gui.key_bindings import lookup_command

        command = lookup_command(symbol, modifiers, self.animation_running)
        if command:
            self.inject_command(command)

    def _handle_browser_speed(self, speed_index: int) -> None:
        """Handle speed change from browser slider."""
        from cube.application.state import speeds
        clamped = max(0, min(len(speeds) - 1, speed_index))
        self._app.vs._speed = clamped
        # No need to broadcast back — the slider already shows the value

    def _handle_browser_size(self, size: int) -> None:
        """Handle cube size change from browser slider."""
        clamped = max(2, min(7, size))
        vs = self._app.vs
        if clamped != vs.cube_size:
            vs.cube_size = clamped
            self._app.cube.reset(clamped)
            self._app.op.reset()
            self.update_gui_elements()

    def _handle_browser_command(self, command_name: str) -> None:
        """Handle command from browser toolbar button."""
        from cube.presentation.gui.commands import Commands

        # "solve" uses two-phase approach: compute solution, then replay with animation.
        # This avoids blocking the asyncio event loop during solver computation.
        if command_name == "solve":
            self._two_phase_solve()
            return

        command_map: dict[str, Command] = {
            "solve_instant": Commands.SOLVE_ALL_NO_ANIMATION,
            "scramble": Commands.SCRAMBLE_1,
            "reset": Commands.RESET_CUBE,
            "toggle_debug": Commands.TOGGLE_DEBUG,
            "toggle_animation": Commands.TOGGLE_ANIMATION,
        }

        command = command_map.get(command_name)
        if command:
            self.inject_command(command)
            self._broadcast_toolbar_state()

    def _two_phase_solve(self) -> None:
        """Solve using two-phase approach: compute solution, then replay.

        Phase 1: slv.solution() computes the full solution with animation OFF.
                 The cube is left unchanged (solver undoes its moves internally).
        Phase 2: op.play(solution_alg) replays the solution with animation ON.
                 Each move is queued in WebAnimationManager and played visually
                 one at a time, with model changes applied after each animation.
        """
        try:
            app = self._app
            slv = app.slv

            # Phase 1: Compute solution (instant, no animation, cube unchanged)
            solution_alg = slv.solution()

            if solution_alg.count() == 0:
                return  # Already solved

            # Phase 2: Replay solution with animation
            app.op.play(solution_alg)

            self._broadcast_toolbar_state()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._app.set_error(f"Solve error: {e}")
            self.update_gui_elements()

    def _broadcast_speed(self) -> None:
        """Send current speed index to browser to sync the slider."""
        speed_index = self._app.vs.get_speed_index
        msg = json.dumps({"type": "speed_update", "value": speed_index})
        self._event_loop.broadcast(msg)

    def _broadcast_text(self) -> None:
        """Send animation text and status info to browser."""
        vs = self._app.vs
        app = self._app
        at = vs.animation_text

        # Animation text (3 lines: solver phase, step detail, current move)
        anim_lines: list[dict[str, object]] = []
        animation_text_props = app.config.animation_text
        for i in range(3):
            line = at.get_line(i)
            if line:
                prop = animation_text_props[i]
                color: tuple[int, int, int, int] = prop[3]
                anim_lines.append({
                    "text": line,
                    "size": prop[2],
                    "color": f"rgba({color[0]},{color[1]},{color[2]},{color[3] / 255:.2f})",
                    "bold": prop[4],
                })

        # Status line (compact)
        slv = app.slv
        status = slv.status
        solver_name = slv.name

        msg = json.dumps({
            "type": "text_update",
            "animation": anim_lines,
            "status": status,
            "solver": solver_name,
        })
        self._event_loop.broadcast(msg)

    def _broadcast_toolbar_state(self) -> None:
        """Send current toggle states to browser for button labels."""
        app = self._app
        msg = json.dumps({
            "type": "toolbar_state",
            "debug": app.config.solver_debug,
            "animation": app.op.animation_enabled,
        })
        self._event_loop.broadcast(msg)

    def _broadcast_size(self) -> None:
        """Send current cube size to browser to sync the slider."""
        size = self._app.vs.cube_size
        msg = json.dumps({"type": "size_update", "value": size})
        self._event_loop.broadcast(msg)

    def _on_client_connected(self) -> None:
        """Handle browser client connection - trigger initial draw."""
        print("Client connected - sending initial frame", flush=True)
        self._broadcast_speed()
        self._broadcast_size()
        self._broadcast_toolbar_state()
        self._on_draw()

    def _on_close(self) -> bool:
        """Handle close event."""
        self._event_loop.stop()
        return True

    @property
    def width(self) -> int:
        """Window width in pixels."""
        return self._width

    @property
    def height(self) -> int:
        """Window height in pixels."""
        return self._height

    @property
    def app(self) -> "AbstractApp":
        """Access the application instance."""
        return self._app

    @property
    def backend(self) -> "GUIBackendFactory":
        """Access the GUI backend."""
        return self._backend

    @property
    def viewer(self) -> "GCubeViewer":
        """Access the cube viewer."""
        return self._viewer

    @property
    def renderer(self) -> WebRenderer:
        """Access the renderer."""
        return self._renderer

    @property
    def animation_running(self) -> bool:
        """Check if animation is currently running."""
        return bool(self._animation_manager and self._animation_manager.animation_running())

    def run(self) -> None:
        """Run the main event loop."""
        # Initial draw is triggered by _on_client_connected callback
        # when browser connects (via set_client_connected_handler)

        # Run event loop (blocking)
        self._event_loop.run()

    def close(self) -> None:
        """Close the window and stop the event loop."""
        self._viewer.cleanup()
        self._renderer.cleanup()
        self._event_loop.stop()

    def update_gui_elements(self) -> None:
        """Update all GUI elements."""
        # Update viewer to regenerate display lists with new colors
        if self._viewer:
            self._viewer.update()

        # Update animation manager
        if self._animation_manager:
            self._animation_manager.update_gui_elements()

        # Redraw
        self._on_draw()

    def inject_key(self, key: int, modifiers: int = 0) -> None:
        """Inject a key press event."""
        self._window.simulate_key_press(key, modifiers)

    def inject_command(self, command: Command) -> None:
        """Inject a command directly."""
        from cube.presentation.gui.commands import Commands

        # Intercept solve commands — use two-phase approach for web backend
        if command is Commands.SOLVE_ALL:
            self._two_phase_solve()
            return

        try:
            speed_before = self._app.vs.get_speed_index
            size_before = self._app.vs.cube_size
            ctx = CommandContext.from_window(self)  # type: ignore[arg-type]
            result = command.execute(ctx)
            # Sync browser controls after command
            if self._app.vs.get_speed_index != speed_before:
                self._broadcast_speed()
            if self._app.vs.cube_size != size_before:
                self._broadcast_size()
            self._broadcast_toolbar_state()
            if not result.no_gui_update and not self.animation_running:
                # Skip GUI update when animation just started — the async
                # animation loop handles its own frames via _on_draw(), and
                # rebuilding display lists here would invalidate the IDs
                # captured by the animation's _draw() closure.
                # (In the blocking pyglet backend this isn't an issue because
                # run_animation() blocks until animation completes.)
                self.update_gui_elements()
        except AppExit:
            # For web backend, always close on AppExit (Q key)
            print("Closing web backend...", flush=True)
            self.close()
        except Exception as e:
            cfg = self._app.config
            if cfg.gui_test_mode and cfg.quit_on_error_in_test_mode:
                self.close()
                raise
            else:
                traceback.print_exc()
                msg = str(e)
                error_text = "Some error occurred:"
                if msg:
                    error_text += msg
                self._app.set_error(error_text)
                self.update_gui_elements()

    def set_mouse_visible(self, visible: bool) -> None:
        """Set mouse visibility."""
        self._window.set_mouse_visible(visible)

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._viewer:
            self._viewer.cleanup()
        self._renderer.cleanup()

    def get_opengl_info(self) -> str:
        """Get OpenGL info string (not applicable for web backend)."""
        return "Web Backend (WebGL in browser)"

    def adjust_brightness(self, delta: float) -> float | None:
        """Adjust lighting brightness (not supported in web backend)."""
        return None

    def get_brightness(self) -> float | None:
        """Get current brightness level (not supported in web backend)."""
        return None

    def adjust_background(self, delta: float) -> float | None:
        """Adjust background gray level (not supported in web backend)."""
        return None

    def get_background(self) -> float | None:
        """Get current background gray level (not supported in web backend)."""
        return None

    def next_texture_set(self) -> str | None:
        """Cycle to the next texture set (not supported in web backend)."""
        return None

    def prev_texture_set(self) -> str | None:
        """Cycle to the previous texture set (not supported in web backend)."""
        return None

    def toggle_texture(self) -> bool:
        """Toggle texture mode on/off (not supported in web backend)."""
        return False

    def load_texture_set(self, directory: str) -> int:
        """Load all face textures from a directory (not supported in web backend)."""
        return 0

    def schedule_once(self, callback: "Callable[[float], None]", delay: float) -> None:
        """Schedule a callback to run after a delay (non-blocking).

        Args:
            callback: Function to call after delay, receives dt (elapsed time)
            delay: Time in seconds to wait before calling
        """
        self._event_loop.schedule_once(callback, delay)

    def inject_command_sequence(
        self,
        commands: "CommandSequence | list[Command]",
        on_complete: "Callable[[], None] | None" = None,
    ) -> None:
        """Inject a sequence of commands, handling delays from SleepCommand.

        Commands are executed in order. If a command returns delay_next_command > 0,
        the remaining commands are scheduled to run after that delay.
        The GUI remains responsive during delays.

        Args:
            commands: Sequence of commands to execute
            on_complete: Optional callback when all commands complete
        """

        # Convert list to CommandSequence if needed
        if isinstance(commands, list):
            cmd_list = commands
        else:
            cmd_list = list(commands)

        if not cmd_list:
            if on_complete:
                on_complete()
            return

        def execute_next(index: int) -> None:
            if index >= len(cmd_list):
                if on_complete:
                    on_complete()
                return

            cmd = cmd_list[index]
            result = cmd.execute(CommandContext.from_window(self))  # type: ignore[arg-type]

            if not result.no_gui_update:
                self.update_gui_elements()

            # If delay requested, schedule next command after delay
            if result.delay_next_command > 0:
                def continue_sequence(_dt: float) -> None:
                    execute_next(index + 1)
                self.schedule_once(continue_sequence, result.delay_next_command)
            else:
                # No delay, execute next command immediately
                execute_next(index + 1)

        execute_next(0)

    def show_popup(self, title: str, lines: list[str],
                   line_colors: list[tuple[int, int, int, int]] | None = None) -> None:
        """Show a modal text popup overlay (no-op for web backend)."""
        pass
