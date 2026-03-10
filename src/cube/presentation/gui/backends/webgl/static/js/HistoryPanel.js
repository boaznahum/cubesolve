/**
 * History Panel — shows undo/redo operation queue with elegant UI.
 *
 * Layout:
 *   Header: "History" + clear button
 *   Scrollable list: done items (solid) → NOW marker → redo items (faded)
 *   Footer: undo / redo / fast-play buttons
 */

export class HistoryPanel {
    constructor(sendFn, animQueue, appState) {
        this._send = sendFn;
        this._animQueue = animQueue;
        this._appState = appState;
        this._panel = document.getElementById('history-panel');
        this._list = document.getElementById('history-list');
        this._btnUndo = document.getElementById('btn-undo');
        this._btnRedo = document.getElementById('btn-redo');
        this._btnPlay = document.getElementById('btn-fastplay');
        this._btnRewind = document.getElementById('btn-fastrewind');
        this._btnClear = document.getElementById('btn-history-clear');

        // State
        this._doneItems = [];    // [{alg, type, index}, ...]
        this._redoItems = [];    // [{alg, type, index}, ...]
        this._redoSource = 'undo';  // 'solver' | 'undo'

        this._bind();
    }

    _bind() {
        if (this._btnUndo) {
            this._btnUndo.addEventListener('click', () => {
                this._send({ type: 'command', name: 'undo' });
            });
        }
        if (this._btnRedo) {
            this._btnRedo.addEventListener('click', () => {
                this._send({ type: 'command', name: 'redo' });
            });
        }
        if (this._btnPlay) {
            this._btnPlay.addEventListener('click', () => {
                if (this._animQueue) {
                    this._animQueue.startPlayback('forward');
                }
                this._send({ type: 'play_next_redo' });
            });
        }
        if (this._btnRewind) {
            this._btnRewind.addEventListener('click', () => {
                if (this._animQueue) {
                    this._animQueue.startPlayback('backward');
                }
                this._send({ type: 'play_next_undo' });
            });
        }
        if (this._btnClear) {
            this._btnClear.addEventListener('click', () => {
                this._send({ type: 'command', name: 'clear_history' });
            });
        }
    }

    /** Update from unified AppState snapshot. */
    updateFromState(appState) {
        this._doneItems = (appState.historyDone || []).map((item, i) => ({
            alg: item.alg,
            type: item.type || 'move',
            text: item.text || '',
            index: i + 1,
        }));
        this._redoItems = (appState.historyRedo || []).map((item, i) => ({
            alg: item.alg,
            type: item.type || 'move',
            text: item.text || '',
            index: (appState.historyDone || []).length + i + 1,
        }));
        this._redoSource = appState.redoSource || 'undo';
        this._redoTainted = appState.redoTainted || false;
        this._render();
    }

    _render() {
        if (!this._list) return;
        this._list.innerHTML = '';

        // Done items (executed operations) — skip scramble summaries
        const doneVisible = this._doneItems.filter(item => item.type !== 'scramble');
        const lastVisIdx = doneVisible.length - 1;
        for (let i = 0; i < doneVisible.length; i++) {
            const item = doneVisible[i];
            if (item.type === 'heading') {
                this._list.appendChild(this._createHeading(item, 'done'));
            } else {
                const el = this._createItem(item, 'done');
                if (i === lastVisIdx) el.classList.add('hp-last-done');
                this._list.appendChild(el);
            }
        }

        // NOW marker (only if there are items on either side)
        if (this._doneItems.length > 0 || this._redoItems.length > 0) {
            const redoCount = this._redoItems.length;

            let label = 'NEXT';
            if (redoCount > 0) {
                label += ` ${redoCount}`;
            }

            // Warning icon when solver queue is tainted by manual moves
            let warn = '';
            let tooltip = '';
            if (this._redoTainted) {
                warn = ' <span class="hp-marker-warn" title="Manual moves were made — playing the queue will NOT solve the cube">&#x26A0;</span>';
                tooltip = 'Manual moves were made — playing the queue will NOT solve the cube';
            }

            const marker = document.createElement('div');
            marker.className = 'hp-marker';
            if (tooltip) marker.title = tooltip;
            marker.innerHTML =
                '<span class="hp-marker-line"></span>' +
                `<span class="hp-marker-text">${label}${warn}</span>` +
                '<span class="hp-marker-line"></span>';
            this._list.appendChild(marker);
        }

        // Redo items (future operations)
        for (let i = 0; i < this._redoItems.length; i++) {
            const item = this._redoItems[i];
            if (item.type === 'heading') {
                this._list.appendChild(this._createHeading(item, 'redo'));
            } else {
                const el = this._createItem(item, 'redo');
                if (i === 0) el.classList.add('hp-next-redo');
                this._list.appendChild(el);
            }
        }

        this._updateButtons();

        // Scroll to NOW marker (use scrollTop instead of scrollIntoView
        // to avoid scrolling the entire page on mobile Safari)
        requestAnimationFrame(() => {
            const marker = this._list.querySelector('.hp-marker');
            if (marker) {
                const list = this._list;
                const targetTop = marker.offsetTop - list.offsetTop
                    - list.clientHeight / 2 + marker.offsetHeight / 2;
                list.scrollTo({ top: targetTop, behavior: 'smooth' });
            }
        });
    }

    _createItem(item, state) {
        const el = document.createElement('div');
        el.className = `hp-item hp-${state}`;

        const num = document.createElement('span');
        num.className = 'hp-item-num';
        num.textContent = item.index;

        const alg = document.createElement('span');
        alg.className = 'hp-item-alg';
        alg.textContent = item.alg;

        el.appendChild(num);
        el.appendChild(alg);

        return el;
    }

    _createHeading(item, state) {
        const el = document.createElement('div');
        el.className = `hp-heading hp-${state}`;
        el.innerHTML =
            '<span class="hp-heading-line"></span>' +
            `<span class="hp-heading-text">${this._esc(item.text)}</span>` +
            '<span class="hp-heading-line"></span>';
        return el;
    }

    _esc(text) {
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    _badgeLabel(type) {
        const labels = {
            'move': '',
            'face': '',
            'slice': 'S',
            'rotation': 'R',
            'scramble': 'Scr',
            'solve': 'Sol',
        };
        return labels[type] || '';
    }

    _updateButtons() {
        // Button state comes from the server's state machine — no client-side reasoning
        const a = this._appState?.allowedActions || {};
        const hasRedo = this._redoItems.length > 0;

        if (this._btnUndo) this._btnUndo.disabled = !a.undo;
        if (this._btnRedo) this._btnRedo.disabled = !a.play_next;
        if (this._btnPlay) this._btnPlay.disabled = !a.play_all;
        if (this._btnRewind) this._btnRewind.disabled = !a.rewind_all;

        // Context-aware labels: solver steps → Play/Play All, manual → Redo/Redo All
        const isSolver = this._redoSource === 'solver';

        if (this._btnRedo) {
            this._btnRedo.title = hasRedo
                ? (isSolver ? 'Play next step' : 'Redo')
                : 'Redo';
        }
        if (this._btnPlay) {
            this._btnPlay.title = hasRedo
                ? (isSolver ? 'Play all' : 'Redo all')
                : 'Play all';
        }
    }

}
