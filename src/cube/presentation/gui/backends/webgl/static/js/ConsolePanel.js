/**
 * ConsolePanel — bottom-docked terminal panel for viewing server debug logs.
 *
 * Opens via toolbar terminal icon. On open, subscribes to server log stream
 * (receives buffered snapshot + live updates). On close, unsubscribes.
 * Auto-scrolls to bottom unless the user has scrolled up.
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
        // Subscribe to live log stream
        this._send({ type: 'console_subscribe' });

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
        // Unsubscribe from live log stream
        this._send({ type: 'console_unsubscribe' });
        if (this._keyHandler) {
            window.removeEventListener('keydown', this._keyHandler, true);
            this._keyHandler = null;
        }
    }

    /** Handle console_snapshot message — replace all lines. */
    onSnapshot(lines) {
        if (!this._content) return;
        this._content.textContent = '';
        for (const line of lines) {
            this._appendLine(line);
        }
        this._scrollToBottom();
    }

    /** Handle console_lines message — append new lines. */
    onLines(lines) {
        if (!this._content) return;
        for (const line of lines) {
            this._appendLine(line);
        }
        if (this._autoScroll) {
            this._scrollToBottom();
        }
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
            // If user scrolled more than 30px from bottom, disable auto-scroll
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
