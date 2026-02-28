/**
 * WebSocket client — connects to server, sends messages, auto-reconnects.
 */

export class WsClient {
    constructor(onMessage) {
        this._onMessage = onMessage;
        this._ws = null;
        this._statusEl = document.getElementById('status');
    }

    connect() {
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${proto}//${location.host}/ws`;

        this._ws = new WebSocket(url);

        this._ws.onopen = () => {
            this._statusEl.textContent = 'Connected';
            this._statusEl.className = 'connected';
            const connectMsg = { type: 'connected' };
            const savedId = localStorage.getItem('cube_session_id');
            if (savedId) connectMsg.session_id = savedId;
            this._ws.send(JSON.stringify(connectMsg));
        };

        this._ws.onclose = () => {
            this._statusEl.textContent = 'Reconnecting...';
            this._statusEl.className = 'error';
            setTimeout(() => this.connect(), 2000);
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
}
