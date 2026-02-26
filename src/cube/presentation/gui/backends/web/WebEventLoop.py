"""
Web event loop implementation.

Runs asyncio event loop with HTTP + WebSocket server for browser communication.
Routes each WebSocket connection to its own ClientSession via SessionManager.
"""

from __future__ import annotations

import asyncio
import json
import time
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from cube.presentation.gui.protocols import EventLoop

if TYPE_CHECKING:
    from aiohttp.web import WebSocketResponse

    from cube.presentation.gui.backends.web.SessionManager import SessionManager


class WebEventLoop(EventLoop):
    """Event loop using asyncio with HTTP + WebSocket server.

    Serves static files and maintains WebSocket connections to browsers.
    Uses aiohttp for both HTTP and WebSocket on the same port.

    Each WebSocket connection is routed to its own ClientSession via
    SessionManager. The event loop no longer stores handler callbacks —
    all message handling is delegated to individual sessions.
    """

    def __init__(self, port: int | None = None, gui_test_mode: bool = False):
        self._running = False
        self._has_exit = False
        self._gui_test_mode = gui_test_mode
        self._loop: asyncio.AbstractEventLoop | None = None
        self._session_manager: SessionManager | None = None
        self._scheduled: list[tuple[float, Callable[[float], None], float | None]] = []
        self._start_time = time.monotonic()
        self._explicit_port = port  # Store for lazy port resolution
        self._port: int | None = None  # Resolved lazily in run()
        self._port_resolved = False

        # Callbacks for call_soon
        self._pending_callbacks: list[Callable[[], None]] = []

    def set_session_manager(self, manager: "SessionManager") -> None:
        """Set the session manager for routing WebSocket connections."""
        self._session_manager = manager

    @staticmethod
    def _find_free_port() -> int:
        """Find an available port for the server."""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    @property
    def gui_test_mode(self) -> bool:
        """Whether running in GUI test mode."""
        return self._gui_test_mode

    @gui_test_mode.setter
    def gui_test_mode(self, value: bool) -> None:
        """Set GUI test mode. Must be called before run()."""
        if self._port_resolved:
            raise RuntimeError("Cannot change gui_test_mode after port has been resolved")
        self._gui_test_mode = value

    def _resolve_port(self) -> int:
        """Resolve the port to use (lazy, called before server starts)."""
        if not self._port_resolved:
            if self._gui_test_mode:
                self._port = self._find_free_port()
            else:
                self._port = self._explicit_port if self._explicit_port is not None else 8765
            self._port_resolved = True
        assert self._port is not None
        return self._port

    @property
    def running(self) -> bool:
        """Whether the event loop is currently running."""
        return self._running

    @property
    def has_exit(self) -> bool:
        """Whether the event loop has been signaled to exit."""
        return self._has_exit

    def run(self) -> None:
        """Start the event loop (blocking)."""
        self._running = True
        self._has_exit = False
        self._start_time = time.monotonic()

        try:
            asyncio.run(self._async_run())
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False

    async def _async_run(self) -> None:
        """Main async entry point."""
        try:
            from aiohttp import web
        except ImportError as e:
            raise ImportError(
                "aiohttp package required for web backend. Install with: pip install aiohttp"
            ) from e

        self._loop = asyncio.get_running_loop()

        # Create aiohttp app
        app = web.Application()
        static_dir = Path(__file__).parent / "static"

        # WebSocket handler — routes each connection to its own ClientSession
        async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
            ws = web.WebSocketResponse()
            await ws.prepare(request)

            if self._session_manager:
                await self._session_manager.create_session(ws, request)

            try:
                async for msg in ws:
                    if msg.type == web.WSMsgType.TEXT:
                        await self._handle_message(ws, msg.data)
                    elif msg.type == web.WSMsgType.ERROR:
                        print(f"WebSocket error: {ws.exception()}", flush=True)
            finally:
                if self._session_manager:
                    self._session_manager.remove_session(ws)

            return ws

        # Static file handlers
        async def index_handler(request: web.Request) -> web.StreamResponse:
            return web.FileResponse(static_dir / "index.html")

        async def static_handler(request: web.Request) -> web.StreamResponse:
            filename = request.match_info.get('filename', 'index.html')
            filepath = static_dir / filename
            if filepath.exists():
                return web.FileResponse(filepath)
            return web.Response(status=404, text="Not found")

        # Routes
        app.router.add_get('/ws', websocket_handler)
        app.router.add_get('/', index_handler)
        app.router.add_get('/{filename}', static_handler)

        # Resolve port (lazy - uses gui_test_mode to decide)
        port = self._resolve_port()

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        host = 'localhost' if self._gui_test_mode else '0.0.0.0'
        site = web.TCPSite(runner, host, port, reuse_address=True)
        await site.start()

        from cube.version import get_version
        print(f"Web backend v{get_version()} running at http://localhost:{port}", flush=True)
        if not self._gui_test_mode:
            import socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                print(f"LAN access: http://{local_ip}:{port}", flush=True)
            except Exception:
                pass
        print("Press Ctrl+C to stop", flush=True)

        # Open browser (skip in test mode)
        if not self._gui_test_mode:
            webbrowser.open(f"http://localhost:{port}")

        # Start periodic client logging task
        logging_task: asyncio.Task[None] | None = None
        if not self._gui_test_mode:
            logging_task = asyncio.create_task(self._log_clients_periodically())

        # Main loop
        try:
            while not self._has_exit:
                await self._process_scheduled()
                await self._process_pending()
                await asyncio.sleep(0.016)  # ~60fps
        finally:
            if logging_task:
                logging_task.cancel()
            await runner.cleanup()

    async def _handle_message(self, websocket: "WebSocketResponse", message: str) -> None:
        """Handle incoming message — delegate to the session."""
        if not self._session_manager:
            return

        session = self._session_manager.get_session(websocket)
        if session is None:
            return

        try:
            data = json.loads(message)
            session.handle_message(data)
        except json.JSONDecodeError:
            print(f"Invalid JSON: {message}", flush=True)

    async def _log_clients_periodically(self) -> None:
        """Log connected clients every 60 seconds."""
        try:
            while True:
                await asyncio.sleep(60)
                if self._session_manager and self._session_manager.session_count > 0:
                    print(f"Connected clients: {self._session_manager.session_count}", flush=True)
                    self._session_manager._log_all_clients()
        except asyncio.CancelledError:
            pass

    async def _process_scheduled(self) -> None:
        """Process scheduled callbacks."""
        now = time.monotonic()
        to_run = []
        remaining = []

        for scheduled_time, callback, interval in self._scheduled:
            if now >= scheduled_time:
                to_run.append((callback, interval))
            else:
                remaining.append((scheduled_time, callback, interval))

        self._scheduled = remaining

        for callback, interval in to_run:
            try:
                dt = now - self._start_time
                callback(dt)
                # Reschedule if interval callback
                if interval is not None:
                    self._scheduled.append((now + interval, callback, interval))
            except Exception as e:
                print(f"Callback error: {e}", flush=True)
                import traceback
                traceback.print_exc()

    async def _process_pending(self) -> None:
        """Process pending call_soon callbacks."""
        callbacks = self._pending_callbacks[:]
        self._pending_callbacks.clear()

        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Callback error: {e}", flush=True)

    def stop(self) -> None:
        """Request the event loop to stop."""
        print("Stopping event loop...", flush=True)
        self._has_exit = True
        # Close all WebSocket clients
        if self._loop and self._session_manager:
            for session in self._session_manager.all_sessions:
                try:
                    asyncio.run_coroutine_threadsafe(session._ws.close(), self._loop)
                except Exception:
                    pass

    def step(self, timeout: float = 0.0) -> bool:
        """Process pending events (limited support in async context)."""
        return False

    def schedule_once(self, callback: Callable[[float], None], delay: float) -> None:
        """Schedule a callback to run once after delay."""
        scheduled_time = time.monotonic() + delay
        self._scheduled.append((scheduled_time, callback, None))

    def schedule_interval(self, callback: Callable[[float], None], interval: float) -> None:
        """Schedule a callback to run repeatedly."""
        scheduled_time = time.monotonic() + interval
        self._scheduled.append((scheduled_time, callback, interval))

    def unschedule(self, callback: Callable[[float], None]) -> None:
        """Remove a scheduled callback."""
        self._scheduled = [
            (t, cb, i) for t, cb, i in self._scheduled
            if cb != callback
        ]

    def call_soon(self, callback: Callable[[], None]) -> None:
        """Schedule a callback to run as soon as possible."""
        self._pending_callbacks.append(callback)

    def get_time(self) -> float:
        """Get current time in seconds."""
        return time.monotonic() - self._start_time

    def idle(self) -> float:
        """Process pending callbacks and return timeout until next."""
        now = time.monotonic()

        if not self._scheduled:
            return 1.0

        next_time = min(t for t, _, _ in self._scheduled)
        return max(0.0, next_time - now)

    def notify(self) -> None:
        """Wake up the event loop."""
        pass

    def send_to(self, ws: "WebSocketResponse", message: str) -> None:
        """Send a message to a specific WebSocket client (unicast)."""
        if self._loop and not ws.closed:
            self._loop.create_task(self._safe_send(ws, message))

    def broadcast(self, message: str) -> None:
        """Send message to all connected clients (rare — e.g., server shutdown)."""
        if self._session_manager and self._loop:
            for session in self._session_manager.all_sessions:
                ws = session._ws
                if not ws.closed:
                    self._loop.create_task(self._safe_send(ws, message))

    @staticmethod
    async def _safe_send(ws: "WebSocketResponse", message: str) -> None:
        """Send a WebSocket message, silently ignoring disconnected clients."""
        try:
            await ws.send_str(message)
        except (ConnectionResetError, ConnectionError, OSError):
            pass  # Client disconnected — nothing to do

    def _js_keycode_to_symbol(self, keycode: int, key: str) -> int:
        """Convert JavaScript keyCode to our Keys symbol.

        JavaScript keyCode values mostly match ASCII for letters/numbers,
        but special keys need mapping.
        """
        from cube.presentation.gui.Keys import Keys

        # Map JavaScript special keyCodes to our Keys constants
        # JavaScript keyCode reference: https://keycode.info/
        JS_TO_KEYS = {
            27: Keys.ESCAPE,      # Escape
            13: Keys.RETURN,      # Enter
            32: Keys.SPACE,       # Space
            9: Keys.TAB,          # Tab
            8: Keys.BACKSPACE,    # Backspace
            46: Keys.DELETE,      # Delete
            45: Keys.INSERT,      # Insert
            37: Keys.LEFT,        # ArrowLeft
            39: Keys.RIGHT,       # ArrowRight
            38: Keys.UP,          # ArrowUp
            40: Keys.DOWN,        # ArrowDown
            36: Keys.HOME,        # Home
            35: Keys.END,         # End
            33: Keys.PAGE_UP,     # PageUp
            34: Keys.PAGE_DOWN,   # PageDown
            # Function keys
            112: Keys.F1, 113: Keys.F2, 114: Keys.F3, 115: Keys.F4,
            116: Keys.F5, 117: Keys.F6, 118: Keys.F7, 119: Keys.F8,
            120: Keys.F9, 121: Keys.F10, 122: Keys.F11, 123: Keys.F12,
            # Punctuation — regular -/= control CUBE SIZE (Keys.MINUS/EQUAL),
            # while numpad +/- control SPEED (Keys.NUM_ADD/NUM_SUBTRACT)
            191: Keys.SLASH,      # /
            222: Keys.APOSTROPHE, # '
            189: Keys.MINUS,      # - → size decrease
            187: Keys.EQUAL,      # = (also +) → size increase
            188: Keys.COMMA,      # ,
            190: Keys.PERIOD,     # .
            220: Keys.BACKSLASH,  # \
            219: Keys.BRACKETLEFT,  # [
            221: Keys.BRACKETRIGHT, # ]
            # Numpad
            107: Keys.NUM_ADD,    # Numpad +
            109: Keys.NUM_SUBTRACT, # Numpad -
            96: Keys.NUM_0, 97: Keys.NUM_1, 98: Keys.NUM_2,
            99: Keys.NUM_3, 100: Keys.NUM_4, 101: Keys.NUM_5,
            102: Keys.NUM_6, 103: Keys.NUM_7, 104: Keys.NUM_8,
            105: Keys.NUM_9,
        }

        if keycode in JS_TO_KEYS:
            return JS_TO_KEYS[keycode]

        # Letters A-Z (65-90) and numbers 0-9 (48-57) match ASCII
        # which also matches our Keys constants
        if 65 <= keycode <= 90 or 48 <= keycode <= 57:
            return keycode

        # Fallback: return keycode directly (may not match)
        return keycode
