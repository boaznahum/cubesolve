"""
Console AppWindow implementation.

Provides a text-based application window for console mode.
Uses text_cube_viewer for NxN cube rendering with rich colors.

Key Handling:
- Console keys are mapped to abstract Keys
- Inverse mode (') sets SHIFT modifier
- All command logic is in handle_key() via lookup_command + command.execute()

Enhanced Features:
- NxN cube support (any size)
- Algorithm parsing: press 'A' to enter algorithm input mode
- Status display: press 'S' to show detailed part status
- Rich colored output when rich library is available
"""
from __future__ import annotations

from collections.abc import Callable

from cube.application.AbstractApp import AbstractApp
from cube.domain.algs import Algs
from cube.presentation.gui.backends.console.ConsoleEventLoop import ConsoleEventLoop
from cube.presentation.gui.backends.console.ConsoleKeys import Keys as ConsoleKeys
from cube.presentation.gui.backends.console.ConsoleRenderer import ConsoleRenderer
from cube.presentation.gui.backends.console.NullViewer import NullViewer
from cube.presentation.gui.factory import GUIBackend
from cube.presentation.gui.protocols import AppWindow
from cube.presentation.gui.protocols.AppWindowBase import AppWindowBase
from cube.presentation.gui.types import Keys, Modifiers
from cube.utils.text_cube_viewer import print_cube_with_info

from rich.console import Console
from rich.prompt import Prompt

_console = Console()

# Mapping from console key characters to abstract Keys
_CONSOLE_TO_KEYS: dict[str, int] = {
    ConsoleKeys.R: Keys.R,
    ConsoleKeys.L: Keys.L,
    ConsoleKeys.U: Keys.U,
    ConsoleKeys.F: Keys.F,
    ConsoleKeys.B: Keys.B,
    ConsoleKeys.D: Keys.D,
    ConsoleKeys.X: Keys.X,
    ConsoleKeys.Y: Keys.Y,
    ConsoleKeys.M: Keys.M,
    ConsoleKeys.CLEAR: Keys.C,
    ConsoleKeys.SCRAMBLE_RANDOM: Keys._0,
    ConsoleKeys.SCRAMBLE_1: Keys._1,
    ConsoleKeys.SCRAMBLE_2: Keys._2,
    ConsoleKeys.SCRAMBLE_3: Keys._3,
    ConsoleKeys.SCRAMBLE_4: Keys._4,
    ConsoleKeys.SCRAMBLE_5: Keys._5,
    ConsoleKeys.SCRAMBLE_6: Keys._6,
    ConsoleKeys.SOLVE: Keys.SLASH,
    ConsoleKeys.UNDO: Keys.COMMA,
    ConsoleKeys.QUIT: Keys.Q,
}

# Keys that are handled specially (not via key mapping)
_SPECIAL_KEYS = {
    ConsoleKeys.ALGS,       # Algorithm input mode
    ConsoleKeys.STATUS,     # Show detailed status
    ConsoleKeys.HELP,       # Show help
    ConsoleKeys.SOLVE_STEP, # Solve step selection
}


class ConsoleAppWindow(AppWindowBase, AppWindow):
    """Console-based AppWindow implementation.

    Inherits from AbstractAppWindow for shared logic and handle_key().
    Inherits from AppWindow protocol for PyCharm visibility.
    Uses console_viewer.plot() for text-based cube display.
    """

    def __init__(
        self,
        app: AbstractApp,
        width: int,
        height: int,
        title: str,
        backend: GUIBackend,
    ):
        """Initialize the Console AppWindow.

        Args:
            app: Application instance (cube, operator, solver)
            width: Ignored in console mode
            height: Ignored in console mode
            title: Window title (printed to console)
            backend: GUI backend for rendering
        """
        # Initialize base class (sets _app, _backend, _animation_manager, etc.)
        super().__init__(app, backend)

        # Console-specific attributes
        self._width = width
        self._height = height
        self._renderer: ConsoleRenderer = backend.renderer  # type: ignore
        self._event_loop: ConsoleEventLoop = backend.event_loop  # type: ignore
        self._title = title
        self._closed = False
        self._inv_mode = False  # Inverse mode toggle
        self._wide_mode = False  # Wide mode toggle (for lowercase moves like r, f, u)
        self._debug = False

        # Set up event loop - pass our on_key_press as the handler
        self._event_loop.set_key_handler(self._on_console_key_event)

        # Create viewer (no-op for console, but required by protocol)
        self._viewer = NullViewer(app.cube)

        # Print title
        print(f"\n=== {title} ===\n")

    @property
    def width(self) -> int:
        """Window width (nominal - console has no real window)."""
        return self._width

    @property
    def height(self) -> int:
        """Window height (nominal - console has no real window)."""
        return self._height

    @property
    def renderer(self) -> ConsoleRenderer:
        """Access the renderer (console-specific type)."""
        return self._renderer

    @property
    def animation_running(self) -> bool:
        """Console mode doesn't support animation."""
        return False

    def run(self) -> None:
        """Run the main event loop."""
        self._draw()
        self._event_loop.run()

    def close(self) -> None:
        """Close the application."""
        self._closed = True
        self._event_loop.stop()

    def update_gui_elements(self) -> None:
        """Update GUI - redraw the cube."""
        self._draw()

    def _draw(self) -> None:
        """Draw the cube using text_cube_viewer (NxN support)."""
        if self._closed:
            return

        print("\n" + "=" * 40)
        print_cube_with_info(self._app.cube)
        print("=" * 40)
        self._print_status()

    def _print_status(self) -> None:
        """Print status information."""
        app = self._app
        cube = app.cube
        slv = app.slv
        op = app.op

        # Line 1: Solver name + status + solved
        solved_str = "[green]SOLVED[/green]" if cube.solved else "[yellow]not solved[/yellow]"
        _console.print(f"Solver: [cyan]{slv.name}[/cyan]  Status: {slv.status}  {solved_str}")

        # Line 2: History (simplified)
        h = Algs.simplify(*op.history(remove_scramble=True))
        hist_str = str(h)[-60:] if h.count() > 0 else "(empty)"
        _console.print(f"History: #{h.count()} {hist_str}")

        # Mode flags
        mode_flags = []
        if self._inv_mode:
            mode_flags.append("INV")
        if self._wide_mode:
            mode_flags.append("WIDE")
        if mode_flags:
            _console.print(f"[magenta][{' + '.join(mode_flags)} MODE][/magenta]")

        if app.error:
            _console.print(f"[red]Error: {app.error}[/red]")

        # Solve steps for current solver
        steps = slv.supported_steps()
        if steps:
            step_strs = [s.short_code for s in steps[:9]]
            _console.print(f"Solve: ? (all)  V: {' '.join(step_strs)}")

        print("\nR L U F B D (faces), X Y M (rot), ' (inv), W (wide), 0-6 (scramble)")
        print("? (solve all), V (solve step), < (undo), A (alg), S (status), C (clear), Q (quit)")

    def _show_help(self) -> None:
        """Show detailed help information."""
        help_text = """
=== Console Cube Solver Help ===

BASIC MOVES
-----------
Face Moves:    R, L, U, D, F, B
               Press the letter to rotate that face clockwise

Inverse:       Press ' (apostrophe) first, then the face key
               Example: ' then R = R' (R counter-clockwise)

Rotations:     X = rotate entire cube on R axis
               Y = rotate entire cube on U axis

Slices:        M = middle slice (between L and R)

WIDE MOVES (for 4x4+ cubes)
---------------------------
Press W first, then R/L/U/D/F/B for wide moves
  W then R = r (rotates R layer + adjacent inner layer)
  W then ' then R = r' (wide R inverse)

USAGE EXAMPLES
--------------
Keyboard mode (press single keys):
  R         → Rotate R face clockwise
  ' R       → Rotate R face counter-clockwise (R')
  W R       → Wide R move (r) - moves R + adjacent slice
  W ' R     → Wide R inverse (r')
  0         → Random scramble
  1-6       → Scramble with fixed seed (reproducible)
  ?         → Solve the cube automatically
  <         → Undo last move

Algorithm mode (press A, then type):
  >>> R U R' U'          Basic algorithm
  >>> r u r' u'          Wide moves (lowercase)
  >>> (R U R' U')6       Repeat 6 times
  >>> [1:2]M             Slice M from index 1 to 2 (4x4+)
  >>> R [1:1]M' R'       Mix standard and slice moves

SLICE NOTATION (for big cubes)
------------------------------
  [1:2]M    = middle slices from 1 to 2
  [0:1]R    = outer + first inner slice of R
  [1:1]F    = just the first inner slice of F

STATUS DISPLAY (press S)
------------------------
Shows whether edges/corners are:
  - is3x3: true if reduced to single piece (like 3x3)
  - match_faces: true if colors match their face

Press any key to continue...
"""
        print(help_text)

    def _show_detailed_status(self) -> None:
        """Show detailed status of cube parts (is3x3, match_faces)."""
        cube = self._app.cube

        # Collect edge status
        edges_3x3: list[str] = []
        edges_not3x3: list[str] = []
        edges_match: list[str] = []
        edges_nomatch: list[str] = []

        for edge in cube.edges:
            name = f"{edge.e1.face.name.value}{edge.e2.face.name.value}"
            if edge.is3x3:
                edges_3x3.append(name)
            else:
                edges_not3x3.append(name)
            if edge.match_faces:
                edges_match.append(name)
            else:
                edges_nomatch.append(name)

        # Collect corner status
        corners_match: list[str] = []
        corners_nomatch: list[str] = []
        for corner in cube.corners:
            edges = corner._slice.edges
            name = "".join(e.face.name.value for e in edges)
            if corner.match_faces:
                corners_match.append(name)
            else:
                corners_nomatch.append(name)

        # Collect center status
        centers_3x3: list[str] = []
        centers_not3x3: list[str] = []
        centers_match: list[str] = []
        centers_nomatch: list[str] = []

        for center in cube.centers:
            name = center.face.name.value
            if center.is3x3:
                centers_3x3.append(name)
            else:
                centers_not3x3.append(name)
            if center.match_faces:
                centers_match.append(name)
            else:
                centers_nomatch.append(name)

        # Print compact status
        def fmt_list(lst: list[str], empty: str = "-") -> str:
            return " ".join(lst) if lst else empty

        solved_str = "SOLVED" if cube.solved else "NOT SOLVED"

        _console.print(f"[cyan]Cube {cube.size}x{cube.size}[/cyan]: {solved_str}")
        _console.print(f"[yellow]Edges[/yellow]  3x3: {fmt_list(edges_3x3)}  not3x3: {fmt_list(edges_not3x3)}")
        _console.print(f"         match: {fmt_list(edges_match)}  nomatch: {fmt_list(edges_nomatch)}")
        _console.print(f"[yellow]Corners[/yellow] match: {fmt_list(corners_match)}  nomatch: {fmt_list(corners_nomatch)}")
        _console.print(f"[yellow]Centers[/yellow] 3x3: {fmt_list(centers_3x3)}  not3x3: {fmt_list(centers_not3x3)}")
        _console.print(f"         match: {fmt_list(centers_match)}  nomatch: {fmt_list(centers_nomatch)}")

    def _prompt_algorithm(self) -> None:
        """Prompt user to enter an algorithm and apply it."""
        _console.print("\n[cyan]Enter algorithm (e.g., R U R' U'):[/cyan]")
        try:
            alg_str = Prompt.ask("[bold cyan]>>>[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            _console.print("[yellow]Cancelled[/yellow]")
            return

        if not alg_str:
            return

        try:
            alg = Algs.parse(alg_str)
            alg.play(self._app.cube)
            _console.print(f"[green]Applied:[/green] {alg}")
        except Exception as e:
            _console.print(f"[red]Parse error:[/red] {e}")

    def _prompt_solve_step(self) -> None:
        """Prompt user to select a solve step."""
        slv = self._app.slv
        steps = slv.supported_steps()

        if not steps:
            _console.print("[yellow]No solve steps available for this solver[/yellow]")
            return

        _console.print(f"\n[cyan]Solver: {slv.name} - Select step (1-{len(steps)}):[/cyan]")
        for i, step in enumerate(steps[:9]):
            _console.print(f"  {i+1}: {step.short_code} - {step.description}")

        try:
            choice = Prompt.ask("[bold cyan]>>>[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            _console.print("[yellow]Cancelled[/yellow]")
            return

        if not choice or not choice.isdigit():
            return

        idx = int(choice) - 1
        if 0 <= idx < len(steps):
            step = steps[idx]
            _console.print(f"[green]Solving: {step.description}...[/green]")
            try:
                result = slv.solve(what=step, animation=False)
                _console.print(f"[green]Done. Result: {result}[/green]")
            except Exception as e:
                import traceback
                _console.print(f"[red]Solve error:[/red] {e}")
                traceback.print_exc()
        else:
            _console.print(f"[yellow]Invalid choice: {choice}[/yellow]")

    # Face keys that support wide mode
    _FACE_KEYS = {ConsoleKeys.R, ConsoleKeys.L, ConsoleKeys.U, ConsoleKeys.D, ConsoleKeys.F, ConsoleKeys.B}

    def _on_console_key_event(self, key: str) -> bool:
        """Native key event handler from ConsoleEventLoop.

        Converts console key to abstract Keys and calls handle_key().

        Args:
            key: The key that was pressed (uppercase).

        Returns:
            True if the application should quit.
        """
        # Handle inverse mode toggle (console-specific state)
        if key == ConsoleKeys.INV:
            self._inv_mode = not self._inv_mode
            return False

        # Handle wide mode toggle
        if key == ConsoleKeys.WIDE:
            self._wide_mode = not self._wide_mode
            return False

        # Handle Ctrl+C as quit
        if key == ConsoleKeys.CTRL_C:
            return True

        # Handle special keys that are not mapped to abstract Keys
        if key == ConsoleKeys.ALGS:
            self._prompt_algorithm()
            self._draw()
            return False

        if key == ConsoleKeys.STATUS:
            self._show_detailed_status()
            return False

        if key == ConsoleKeys.HELP:
            self._show_help()
            return False

        if key == ConsoleKeys.SOLVE_STEP:
            self._prompt_solve_step()
            self._draw()
            return False

        # Handle face moves with wide mode support
        if key in self._FACE_KEYS and self._wide_mode:
            # Build algorithm string: lowercase for wide, with ' for inverse
            move = key.lower()  # Wide move = lowercase
            if self._inv_mode:
                move += "'"
            try:
                alg = Algs.parse(move)
                alg.play(self._app.cube)
            except Exception as e:
                _console.print(f"[red]Error:[/red] {e}")
            # Reset modes after operation
            self._inv_mode = False
            self._wide_mode = False
            self._draw()
            return False

        # Convert console key to abstract key
        abstract_key = _CONSOLE_TO_KEYS.get(key)
        if abstract_key is None:
            return False  # Unknown key, ignore

        # Apply modifiers (inverse mode → SHIFT)
        modifiers = Modifiers.SHIFT if self._inv_mode else 0

        # Call protocol method
        self.handle_key(abstract_key, modifiers)

        # Reset modes after operation
        self._inv_mode = False
        self._wide_mode = False

        # Redraw after command
        self._draw()

        # Check for quit
        return abstract_key == Keys.Q

    # handle_key() inherited from AppWindowBase
    # inject_key() inherited from AppWindowBase

    def set_mouse_visible(self, visible: bool) -> None:
        """No-op for console mode."""
        pass

    def _request_redraw(self) -> None:
        """Request redraw (no-op for console mode - draws immediately)."""
        pass

    def get_opengl_info(self) -> str:
        """Get OpenGL version information (not applicable for console).

        Returns:
            Empty string (console backend has no OpenGL context).
        """
        return ""

    def schedule_once(self, callback: "Callable[[float], None]", delay: float) -> None:
        """Schedule a callback to run after a delay (non-blocking).

        Args:
            callback: Function to call after delay, receives dt (elapsed time)
            delay: Time in seconds to wait before calling
        """
        self._event_loop.schedule_once(callback, delay)

    # adjust_brightness() and get_brightness() inherited from AppWindowBase (return None)
