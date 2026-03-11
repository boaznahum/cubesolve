/**
 * WebSocket client — connects to server, sends messages, auto-reconnects.
 *
 * Includes Wake Lock API and Page Visibility handling to prevent
 * solver interruption when iPhone/mobile screen goes idle.
 */

export class WsClient {
    constructor(onMessage) {
        this._onMessage = onMessage;
        this._ws = null;
        this._statusEl = document.getElementById('status');
        this._reconnectTimer = null;
        this._wakeLock = null;
        this.onConnected = null;  // callback: reset view on (re)connect

        this._setupVisibilityHandler();
    }

    connect() {
        // Cancel any pending reconnect timer
        if (this._reconnectTimer) {
            clearTimeout(this._reconnectTimer);
            this._reconnectTimer = null;
        }

        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${proto}//${location.host}/ws`;

        this._ws = new WebSocket(url);

        this._ws.onopen = () => {
            this._statusEl.textContent = 'Connected';
            this._statusEl.className = 'connected';
            const connectMsg = { type: 'connected' };
            const params = new URLSearchParams(window.location.search);
            if (params.has('new')) {
                localStorage.removeItem('cube_session_id');
                // Clean URL without reload
                history.replaceState(null, '', window.location.pathname);
            }
            const savedId = localStorage.getItem('cube_session_id');
            if (savedId) connectMsg.session_id = savedId;
            this._ws.send(JSON.stringify(connectMsg));
            this._acquireWakeLock();
            if (this.onConnected) this.onConnected();
        };

        this._ws.onclose = () => {
            this._statusEl.textContent = 'Reconnecting...';
            this._statusEl.className = 'error';
            this._releaseWakeLock();
            this._reconnectTimer = setTimeout(() => this.connect(), 2000);
        };

        this._ws.onerror = () => {
            this._statusEl.textContent = 'Connection error';
            this._statusEl.className = 'error';
        };

        this._ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                this._onMessage(msg);
            } catch (e) {
                console.error('Parse error:', e);
            }
        };
    }

    send(msg) {
        if (this._ws && this._ws.readyState === WebSocket.OPEN) {
            this._ws.send(JSON.stringify(msg));
        }
    }

    get connected() {
        return this._ws && this._ws.readyState === WebSocket.OPEN;
    }

    _setupVisibilityHandler() {
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                if (!this.connected) {
                    // Page became visible again (iPhone woke up / tab foregrounded)
                    // Reconnect immediately instead of waiting for the timer
                    this.connect();
                } else {
                    // Still connected — re-acquire wake lock
                    // (Safari releases it on visibility change)
                    this._acquireWakeLock();
                }
            }
        });
    }

    async _acquireWakeLock() {
        if (!('wakeLock' in navigator)) return;
        try {
            this._wakeLock = await navigator.wakeLock.request('screen');
            this._wakeLock.addEventListener('release', () => {
                this._wakeLock = null;
            });
        } catch (e) {
            // Can fail on low battery or background tab
            console.log('Wake lock not acquired:', e.message);
        }
    }

    _releaseWakeLock() {
        if (this._wakeLock) {
            this._wakeLock.release();
            this._wakeLock = null;
        }
    }
}
