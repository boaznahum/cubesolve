"""
WebGL event loop implementation.

Runs asyncio event loop with HTTP + WebSocket server for browser communication.
Routes each WebSocket connection to its own ClientSession via SessionManager.

Unlike the web backend which sends rendering commands per-frame, this backend
sends cube state updates. The event loop structure is identical.
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

    from cube.presentation.gui.backends.webgl.SessionManager import SessionManager


class WebglEventLoop(EventLoop):
    """Event loop using asyncio with HTTP + WebSocket server.

    Serves static files and maintains WebSocket connections to browsers.
    Uses aiohttp for both HTTP and WebSocket on the same port.

    Each WebSocket connection is routed to its own ClientSession via
    SessionManager.
    """

    _default_open_browser: bool = False  # set by main_webgl before construction

    def __init__(self, port: int | None = None, gui_test_mode: bool = False):
        self._running = False
        self._has_exit = False
        self._gui_test_mode = gui_test_mode
        self._open_browser = self.__class__._default_open_browser
        self._loop: asyncio.AbstractEventLoop | None = None
        self._session_manager: SessionManager | None = None
        self._scheduled: list[tuple[float, Callable[[float], None], float | None]] = []
        self._start_time = time.monotonic()
        self._explicit_port = port
        self._port: int | None = None
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
        return self._gui_test_mode

    @gui_test_mode.setter
    def gui_test_mode(self, value: bool) -> None:
        if self._port_resolved:
            raise RuntimeError("Cannot change gui_test_mode after port has been resolved")
        self._gui_test_mode = value

    def _resolve_port(self) -> int:
        """Resolve the port to use (lazy, called before server starts)."""
        if not self._port_resolved:
            if self._gui_test_mode:
                self._port = self._find_free_port()
            else:
                self._port = self._explicit_port if self._explicit_port is not None else 8766
            self._port_resolved = True
        assert self._port is not None
        return self._port

    @property
    def running(self) -> bool:
        return self._running

    @property
    def has_exit(self) -> bool:
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
                "aiohttp package required for webgl backend. Install with: pip install aiohttp"
            ) from e

        self._loop = asyncio.get_running_loop()

        app = web.Application()
        static_dir = Path(__file__).parent / "static"

        # WebSocket handler
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

        # Static file handlers (no-cache to ensure fresh JS during development)
        no_cache_headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}

        async def index_handler(request: web.Request) -> web.StreamResponse:
            resp = web.FileResponse(static_dir / "index.html")
            resp.headers.update(no_cache_headers)
            return resp

        async def static_handler(request: web.Request) -> web.StreamResponse:
            filename = request.match_info.get('filename', 'index.html')
            filepath = static_dir / filename
            if filepath.exists():
                resp = web.FileResponse(filepath)
                resp.headers.update(no_cache_headers)
                return resp
            return web.Response(status=404, text="Not found")

        # Routes
        app.router.add_get('/ws', websocket_handler)
        app.router.add_get('/', index_handler)
        app.router.add_get('/{filename}', static_handler)

        port = self._resolve_port()

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        host = 'localhost' if self._gui_test_mode else '0.0.0.0'
        site = web.TCPSite(runner, host, port, reuse_address=True)
        await site.start()

        from cube.version import get_version
        print(f"WebGL backend v{get_version()} running at http://localhost:{port}", flush=True)
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

        # Open browser only if explicitly requested
        if self._open_browser and not self._gui_test_mode:
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
        if self._loop and self._session_manager:
            for session in self._session_manager.all_sessions:
                try:
                    asyncio.run_coroutine_threadsafe(session._ws.close(), self._loop)
                except Exception:
                    pass

    def step(self, timeout: float = 0.0) -> bool:
        return False

    def schedule_once(self, callback: Callable[[float], None], delay: float) -> None:
        scheduled_time = time.monotonic() + delay
        self._scheduled.append((scheduled_time, callback, None))

    def schedule_interval(self, callback: Callable[[float], None], interval: float) -> None:
        scheduled_time = time.monotonic() + interval
        self._scheduled.append((scheduled_time, callback, interval))

    def unschedule(self, callback: Callable[[float], None]) -> None:
        self._scheduled = [
            (t, cb, i) for t, cb, i in self._scheduled
            if cb != callback
        ]

    def call_soon(self, callback: Callable[[], None]) -> None:
        self._pending_callbacks.append(callback)

    def get_time(self) -> float:
        return time.monotonic() - self._start_time

    def idle(self) -> float:
        now = time.monotonic()
        if not self._scheduled:
            return 1.0
        next_time = min(t for t, _, _ in self._scheduled)
        return max(0.0, next_time - now)

    def notify(self) -> None:
        pass

    def send_to(self, ws: "WebSocketResponse", message: str) -> None:
        """Send a message to a specific WebSocket client (unicast)."""
        if self._loop and not ws.closed:
            self._loop.create_task(self._safe_send(ws, message))

    def broadcast(self, message: str) -> None:
        """Send message to all connected clients."""
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
            pass

    def _js_keycode_to_symbol(self, keycode: int, key: str) -> int:
        """Convert JavaScript keyCode to our Keys symbol."""
        from cube.presentation.gui.Keys import Keys

        JS_TO_KEYS = {
            27: Keys.ESCAPE, 13: Keys.RETURN, 32: Keys.SPACE,
            9: Keys.TAB, 8: Keys.BACKSPACE, 46: Keys.DELETE,
            45: Keys.INSERT, 37: Keys.LEFT, 39: Keys.RIGHT,
            38: Keys.UP, 40: Keys.DOWN, 36: Keys.HOME, 35: Keys.END,
            33: Keys.PAGE_UP, 34: Keys.PAGE_DOWN,
            112: Keys.F1, 113: Keys.F2, 114: Keys.F3, 115: Keys.F4,
            116: Keys.F5, 117: Keys.F6, 118: Keys.F7, 119: Keys.F8,
            120: Keys.F9, 121: Keys.F10, 122: Keys.F11, 123: Keys.F12,
            191: Keys.SLASH, 222: Keys.APOSTROPHE,
            189: Keys.MINUS, 187: Keys.EQUAL,
            188: Keys.COMMA, 190: Keys.PERIOD,
            220: Keys.BACKSLASH,
            219: Keys.BRACKETLEFT, 221: Keys.BRACKETRIGHT,
            107: Keys.NUM_ADD, 109: Keys.NUM_SUBTRACT,
            96: Keys.NUM_0, 97: Keys.NUM_1, 98: Keys.NUM_2,
            99: Keys.NUM_3, 100: Keys.NUM_4, 101: Keys.NUM_5,
            102: Keys.NUM_6, 103: Keys.NUM_7, 104: Keys.NUM_8,
            105: Keys.NUM_9,
        }

        if keycode in JS_TO_KEYS:
            return JS_TO_KEYS[keycode]

        if 65 <= keycode <= 90 or 48 <= keycode <= 57:
            return keycode

        return keycode
