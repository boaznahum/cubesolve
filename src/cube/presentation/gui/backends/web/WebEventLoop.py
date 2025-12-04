"""
Web event loop implementation.

Runs asyncio event loop with HTTP + WebSocket server for browser communication.
"""

from __future__ import annotations

import asyncio
import json
import time
import webbrowser
from pathlib import Path
from typing import Callable, TYPE_CHECKING

from cube.presentation.gui.protocols import EventLoop

if TYPE_CHECKING:
    pass


class WebEventLoop(EventLoop):
    """Event loop using asyncio with HTTP + WebSocket server.

    Serves static files and maintains WebSocket connections to browsers.
    Uses aiohttp for both HTTP and WebSocket on the same port.
    """

    def __init__(self, port: int | None = None):
        self._running = False
        self._has_exit = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._clients: set = set()
        self._scheduled: list[tuple[float, Callable[[float], None], float | None]] = []
        self._start_time = time.monotonic()
        # In test mode, find a free port; otherwise use provided or default
        from cube.application import config
        if config.GUI_TEST_MODE:
            self._port = self._find_free_port()
        else:
            self._port = port if port is not None else 8765

        # Callbacks for call_soon
        self._pending_callbacks: list[Callable[[], None]] = []

        # Key event handler (set by WebAppWindow)
        self._key_handler: Callable[[int, int], None] | None = None

        # Client connected callback (for initial draw)
        self._on_client_connected: Callable[[], None] | None = None

    @staticmethod
    def _find_free_port() -> int:
        """Find an available port for the server."""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    def set_key_handler(self, handler: Callable[[int, int], None] | None) -> None:
        """Set handler for key events (symbol, modifiers)."""
        self._key_handler = handler

    def set_client_connected_handler(self, handler: Callable[[], None] | None) -> None:
        """Set handler for client connection (for initial draw)."""
        self._on_client_connected = handler

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

        # WebSocket handler
        async def websocket_handler(request):
            ws = web.WebSocketResponse()
            await ws.prepare(request)

            self._clients.add(ws)
            print(f"Client connected. Total clients: {len(self._clients)}", flush=True)

            try:
                async for msg in ws:
                    if msg.type == web.WSMsgType.TEXT:
                        await self._handle_message(ws, msg.data)
                    elif msg.type == web.WSMsgType.ERROR:
                        print(f"WebSocket error: {ws.exception()}", flush=True)
            finally:
                self._clients.discard(ws)
                print(f"Client disconnected. Total clients: {len(self._clients)}", flush=True)

            return ws

        # Static file handlers
        async def index_handler(request):
            return web.FileResponse(static_dir / "index.html")

        async def static_handler(request):
            filename = request.match_info.get('filename', 'index.html')
            filepath = static_dir / filename
            if filepath.exists():
                return web.FileResponse(filepath)
            return web.Response(status=404, text="Not found")

        # Routes
        app.router.add_get('/ws', websocket_handler)
        app.router.add_get('/', index_handler)
        app.router.add_get('/{filename}', static_handler)

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self._port, reuse_address=True)
        await site.start()

        print(f"Web backend running at http://localhost:{self._port}", flush=True)
        print("Press Ctrl+C to stop", flush=True)

        # Open browser (skip in test mode)
        from cube.application import config
        if not config.GUI_TEST_MODE:
            webbrowser.open(f"http://localhost:{self._port}")

        # Main loop
        try:
            while not self._has_exit:
                await self._process_scheduled()
                await self._process_pending()
                await asyncio.sleep(0.016)  # ~60fps
        finally:
            await runner.cleanup()

    async def _handle_message(self, websocket, message: str) -> None:
        """Handle incoming message from browser."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "connected":
                print("Browser connected and ready", flush=True)
                # Trigger initial draw now that browser is connected
                if self._on_client_connected:
                    self._on_client_connected()
            elif msg_type == "key":
                keycode = data.get("code", 0)
                modifiers = data.get("modifiers", 0)
                key_char = data.get("key", "")
                symbol = self._js_keycode_to_symbol(keycode, key_char)
                print(f"Key: '{key_char}' code={keycode} -> symbol={symbol} mod={modifiers}", flush=True)
                if self._key_handler:
                    self._key_handler(symbol, modifiers)
                else:
                    print("  Warning: No key handler set!", flush=True)
            elif msg_type == "mouse_press":
                print(f"Mouse press: {data}", flush=True)
            elif msg_type == "mouse_drag":
                pass  # Don't log drag events (too noisy)
            elif msg_type == "resize":
                print(f"Resize: {data}", flush=True)

        except json.JSONDecodeError:
            print(f"Invalid JSON: {message}", flush=True)

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
        if self._loop and self._clients:
            for client in self._clients.copy():
                asyncio.run_coroutine_threadsafe(client.close(), self._loop)

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

    def broadcast(self, message: str) -> None:
        """Send message to all connected clients."""
        if self._clients and self._loop:
            for client in self._clients.copy():
                try:
                    # Use create_task since we're in the same event loop
                    asyncio.run_coroutine_threadsafe(
                        client.send_str(message),
                        self._loop
                    )
                except Exception as e:
                    print(f"Broadcast error: {e}", flush=True)

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
            # Punctuation
            191: Keys.SLASH,      # /
            222: Keys.APOSTROPHE, # '
            189: Keys.MINUS,      # -
            187: Keys.EQUAL,      # = (also +)
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
