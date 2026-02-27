"""Session manager for the web backend.

Manages all active client sessions. Handles session lifecycle (create, remove,
lookup) and GeoIP resolution for connected clients.
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

from cube.presentation.gui.backends.web.ClientSession import ClientInfo, ClientSession

if TYPE_CHECKING:
    from aiohttp.web import BaseRequest, WebSocketResponse

    from cube.presentation.gui.backends.web.WebEventLoop import WebEventLoop


class SessionManager:
    """Manages all active client sessions."""

    def __init__(self, event_loop: "WebEventLoop", gui_test_mode: bool = False) -> None:
        self._event_loop = event_loop
        self._gui_test_mode = gui_test_mode
        self._sessions: dict[str, ClientSession] = {}
        self._ws_to_session: dict["WebSocketResponse", ClientSession] = {}
        # GeoIP cache: ip -> (city, country, timestamp)
        self._geo_cache: dict[str, tuple[str, str, float]] = {}
        self._geo_cache_ttl: float = 3600.0  # 1 hour

    async def create_session(
        self, ws: "WebSocketResponse", request: "BaseRequest"
    ) -> ClientSession:
        """Create a new session for a WebSocket connection."""
        session_id = uuid.uuid4().hex[:12]
        ip = self._get_client_ip(request)

        # GeoIP lookup (async, with cache)
        city, country = await self._geoip_lookup(ip)

        client_info = ClientInfo(
            session_id=session_id,
            ip=ip,
            city=city,
            country=country,
        )

        session = ClientSession(
            ws=ws,
            event_loop=self._event_loop,
            client_info=client_info,
            gui_test_mode=self._gui_test_mode,
        )

        self._sessions[session_id] = session
        self._ws_to_session[ws] = session

        print(
            f"Session created: {session_id} from {ip} ({city}, {country}). "
            f"Total: {len(self._sessions)}",
            flush=True,
        )
        self._log_all_clients()
        self._broadcast_client_count()
        return session

    def remove_session(self, ws: "WebSocketResponse") -> None:
        """Remove and clean up a session by its WebSocket."""
        session = self._ws_to_session.pop(ws, None)
        if session is None:
            return

        sid = session.client_info.session_id
        info = session.client_info
        self._sessions.pop(sid, None)
        session.cleanup()

        print(
            f"Session removed: {sid} ({info.ip}, {info.city}, {info.country}). "
            f"Total: {len(self._sessions)}",
            flush=True,
        )
        self._log_all_clients()
        self._broadcast_client_count()

    def get_session(self, ws: "WebSocketResponse") -> ClientSession | None:
        """Look up session by WebSocket."""
        return self._ws_to_session.get(ws)

    @property
    def session_count(self) -> int:
        return len(self._sessions)

    @property
    def all_sessions(self) -> list[ClientSession]:
        return list(self._sessions.values())

    def _broadcast_client_count(self) -> None:
        """Broadcast current client count to all connected sessions."""
        count = self.session_count
        for session in self.all_sessions:
            session.send_client_count(count)

    def _log_all_clients(self) -> None:
        """Log the full client list to console."""
        if not self._sessions:
            print("  No clients connected.", flush=True)
            return
        for s in self.get_session_summary():
            print(
                f"  {s['session_id']} | {s['ip']} | "
                f"{s['city']}, {s['country']} | {s['duration']}",
                flush=True,
            )

    def get_session_summary(self) -> list[dict[str, str]]:
        """Get summary info for all sessions (for logging)."""
        now_ts = time.time()
        result: list[dict[str, str]] = []
        for session in self._sessions.values():
            info = session.client_info
            duration_s = now_ts - info.connected_at.timestamp()
            minutes = int(duration_s // 60)
            seconds = int(duration_s % 60)
            result.append({
                "session_id": info.session_id,
                "ip": info.ip,
                "city": info.city,
                "country": info.country,
                "duration": f"{minutes}m{seconds:02d}s",
            })
        return result

    @staticmethod
    def _get_client_ip(request: "BaseRequest") -> str:
        """Extract client IP from request, checking proxy headers."""
        # Check X-Forwarded-For (common behind reverse proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        # Check X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        # Fall back to direct peer
        peername = request.transport.get_extra_info("peername") if request.transport else None
        if peername:
            return peername[0]
        return "unknown"

    async def _geoip_lookup(self, ip: str) -> tuple[str, str]:
        """Look up city and country for an IP address using ip-api.com.

        Uses a local cache (1hr TTL) to respect the free tier rate limit
        (45 requests/minute). Returns ("Unknown", "Unknown") on failure.
        """
        # Skip for localhost/private IPs
        if ip in ("127.0.0.1", "::1", "localhost", "unknown") or ip.startswith("192.168.") or ip.startswith("10."):
            return ("Local", "Local")

        # Check cache
        now = time.time()
        if ip in self._geo_cache:
            city, country, ts = self._geo_cache[ip]
            if now - ts < self._geo_cache_ttl:
                return (city, country)

        try:
            import aiohttp
            async with aiohttp.ClientSession() as http_session:
                url = f"http://ip-api.com/json/{ip}?fields=city,country,status"
                async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "success":
                            city = data.get("city", "Unknown")
                            country = data.get("country", "Unknown")
                            self._geo_cache[ip] = (city, country, now)
                            return (city, country)
        except Exception:
            pass  # Fail silently — GeoIP is best-effort

        return ("Unknown", "Unknown")
