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

    def __init__(self):
        self._running = False
        self._has_exit = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._clients: set = set()
        self._scheduled: list[tuple[float, Callable[[float], None], float | None]] = []
        self._start_time = time.monotonic()
        self._port = 8765

        # Callbacks for call_soon
        self._pending_callbacks: list[Callable[[], None]] = []

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
        site = web.TCPSite(runner, 'localhost', self._port)
        await site.start()

        print(f"Web backend running at http://localhost:{self._port}", flush=True)
        print("Press Ctrl+C to stop", flush=True)

        # Open browser
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
            elif msg_type == "key":
                # TODO: Forward to WebWindow
                print(f"Key event: {data}", flush=True)
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
        self._has_exit = True

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
