/**
 * ConsolePanel — bottom-docked terminal panel for viewing server debug logs.
 *
 * Uses an index-based pull protocol:
 * - Server assigns a monotonic index to each log line.
 * - When subscribed, server sends periodic `console_head` notifications
 *   with just the current head index (tiny, droppable).
 * - Client tracks its own `_lastIndex` and fetches gaps on demand.
 * - On open/reopen/reconnect, client subscribes with its last known index
 *   so only missing lines are sent.
 *
 * This eliminates the push-flooding bug where individual log messages
 * overwhelmed the WebSocket during solver runs.
 */

export class ConsolePanel {
    /**
     * @param {function} sendFn — send message to server
     */
    constructor(sendFn) {
        this._send = sendFn;
        this._visible = false;
        this._built = false;

        /** @type {HTMLElement|null} */
        this._panel = null;
        /** @type {HTMLElement|null} */
        this._content = null;
        /** @type {boolean} */
        this._autoScroll = true;
        /** @type {((e: KeyboardEvent) => void)|null} */
        this._keyHandler = null;

        /** Index of the last line we have rendered (-1 = none). */
        this._lastIndex = -1;
        /** True while a console_fetch request is in flight. */
        this._fetchPending = false;
        /** If a new head arrives while fetch is pending, stash it here. */
        this._deferredHead = -1;
    }

    get visible() { return this._visible; }

    toggle() {
        if (this._visible) this.hide();
        else this.show();
    }

    show() {
        if (!this._built) this._build();
        this._panel.style.display = '';
        this._visible = true;
        this._autoScroll = true;
        document.body.classList.add('console-open');

        // Subscribe with our last known index — server sends only what we're missing
        this._fetchPending = false;
        this._deferredHead = -1;
        this._send({ type: 'console_subscribe', from: this._lastIndex + 1 });

        // ESC to close
        this._keyHandler = (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                e.stopImmediatePropagation();
                this.hide();
            }
        };
        window.addEventListener('keydown', this._keyHandler, true);
    }

    hide() {
        if (this._panel) this._panel.style.display = 'none';
        this._visible = false;
        document.body.classList.remove('console-open');
        this._send({ type: 'console_unsubscribe' });
        if (this._keyHandler) {
            window.removeEventListener('keydown', this._keyHandler, true);
            this._keyHandler = null;
        }
    }

    /**
     * Called on reconnect — if panel was visible, re-subscribe to
     * resume from where we left off.
     */
    onReconnect() {
        if (this._visible) {
            this._fetchPending = false;
            this._deferredHead = -1;
            this._send({ type: 'console_subscribe', from: this._lastIndex + 1 });
        }
    }

    /**
     * Handle `console_head` — server says "head is now at index N".
     * If we're behind, fetch the gap.
     */
    onHead(index) {
        if (index <= this._lastIndex) return;  // already up to date

        if (this._fetchPending) {
            // A fetch is already in flight — remember this head for later
            this._deferredHead = Math.max(this._deferredHead, index);
            return;
        }

        this._requestFetch();
    }

    /**
     * Handle `console_data` — batch of lines from server (response to
     * subscribe or fetch).
     */
    onData(msg) {
        if (!this._content) return;

        const lines = msg.lines || [];
        if (msg.truncated) {
            this._appendLine('--- earlier lines truncated ---');
        }
        for (const entry of lines) {
            // Only append lines we haven't seen
            if (entry.i > this._lastIndex) {
                this._appendLine(entry.t);
                this._lastIndex = entry.i;
            }
        }
        if (this._autoScroll) {
            this._scrollToBottom();
        }

        // If a head notification arrived while we were fetching, fetch again
        this._fetchPending = false;
        if (this._deferredHead > this._lastIndex) {
            this._deferredHead = -1;
            this._requestFetch();
        }
    }

    /** Send a fetch request for lines after our last known index. */
    _requestFetch() {
        this._fetchPending = true;
        this._send({ type: 'console_fetch', from: this._lastIndex + 1 });
    }

    _appendLine(text) {
        const div = document.createElement('div');
        div.className = 'console-line';
        div.textContent = text;
        this._content.appendChild(div);
    }

    _scrollToBottom() {
        if (this._content) {
            this._content.scrollTop = this._content.scrollHeight;
        }
    }

    _build() {
        this._panel = document.createElement('div');
        this._panel.id = 'console-panel';
        this._panel.style.display = 'none';

        // Header
        const header = document.createElement('div');
        header.className = 'console-header';

        const title = document.createElement('span');
        title.className = 'console-title';
        title.textContent = '>_ Console';

        const controls = document.createElement('div');
        controls.className = 'console-controls';

        const clearBtn = document.createElement('button');
        clearBtn.className = 'console-ctrl-btn';
        clearBtn.textContent = 'Clear';
        clearBtn.addEventListener('click', () => {
            if (this._content) this._content.textContent = '';
        });

        const closeBtn = document.createElement('button');
        closeBtn.className = 'console-ctrl-btn';
        closeBtn.textContent = '\u2715';
        closeBtn.addEventListener('click', () => this.hide());

        controls.appendChild(clearBtn);
        controls.appendChild(closeBtn);
        header.appendChild(title);
        header.appendChild(controls);

        // Content (scrollable)
        this._content = document.createElement('div');
        this._content.className = 'console-content';

        // Track user scroll to disable auto-scroll
        this._content.addEventListener('scroll', () => {
            const el = this._content;
            const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 30;
            this._autoScroll = atBottom;
        });

        this._panel.appendChild(header);
        this._panel.appendChild(this._content);

        // Fixed to bottom of viewport (like browser DevTools)
        document.body.appendChild(this._panel);

        this._built = true;
    }
}
