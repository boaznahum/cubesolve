/**
 * History Panel — shows undo/redo operation queue with elegant UI.
 *
 * Layout:
 *   Header: "History" + clear button
 *   Scrollable list: done items (solid) → NOW marker → redo items (faded)
 *   Footer: undo / redo / fast-play buttons
 */

export class HistoryPanel {
    constructor(sendFn) {
        this._send = sendFn;
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
        this._isPlaying = false;

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
                this._send({ type: 'command', name: 'fast_play' });
            });
        }
        if (this._btnRewind) {
            this._btnRewind.addEventListener('click', () => {
                this._send({ type: 'command', name: 'fast_rewind' });
            });
        }
        if (this._btnClear) {
            this._btnClear.addEventListener('click', () => {
                this._send({ type: 'command', name: 'clear_history' });
            });
        }
    }

    /**
     * Update from server history_state message.
     * msg: { done: [{alg, type}], redo: [{alg, type}], redo_source: "solver"|"undo" }
     */
    updateFromServer(msg) {
        this._doneItems = (msg.done || []).map((item, i) => ({
            alg: item.alg,
            type: item.type || 'move',
            index: i + 1,
        }));
        this._redoItems = (msg.redo || []).map((item, i) => ({
            alg: item.alg,
            type: item.type || 'move',
            index: this._doneItems.length + i + 1,
        }));
        this._redoSource = msg.redo_source || 'undo';
        this._render();
    }

    /** Update playing state (disable/enable buttons). */
    setPlaying(playing) {
        this._isPlaying = playing;
        this._updateButtons();
    }

    _render() {
        if (!this._list) return;
        this._list.innerHTML = '';

        // Done items (executed operations)
        const lastDoneIdx = this._doneItems.length - 1;
        for (let i = 0; i < this._doneItems.length; i++) {
            const el = this._createItem(this._doneItems[i], 'done');
            if (i === lastDoneIdx) el.classList.add('hp-last-done');
            this._list.appendChild(el);
        }

        // NOW marker (only if there are items on either side)
        if (this._doneItems.length > 0 || this._redoItems.length > 0) {
            const doneCount = this._doneItems.length;
            const redoCount = this._redoItems.length;
            const isSolver = this._redoSource === 'solver';

            let label = 'NOW';
            if (redoCount > 0 && isSolver) {
                label += ` (solver ${redoCount})`;
            } else if (redoCount > 0) {
                label += ` (redo ${redoCount})`;
            }

            const marker = document.createElement('div');
            marker.className = 'hp-marker';
            marker.innerHTML =
                '<span class="hp-marker-line"></span>' +
                `<span class="hp-marker-text">${label}</span>` +
                '<span class="hp-marker-line"></span>';
            this._list.appendChild(marker);
        }

        // Redo items (future operations)
        for (let i = 0; i < this._redoItems.length; i++) {
            const el = this._createItem(this._redoItems[i], 'redo');
            if (i === 0) el.classList.add('hp-next-redo');
            this._list.appendChild(el);
        }

        this._updateButtons();

        // Scroll to NOW marker
        requestAnimationFrame(() => {
            const marker = this._list.querySelector('.hp-marker');
            if (marker) {
                marker.scrollIntoView({ behavior: 'smooth', block: 'center' });
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

        const badge = document.createElement('span');
        badge.className = `hp-item-badge hp-badge-${item.type}`;
        badge.textContent = this._badgeLabel(item.type);

        el.appendChild(num);
        el.appendChild(alg);
        el.appendChild(badge);

        return el;
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
        const hasDone = this._doneItems.length > 0;
        const hasRedo = this._redoItems.length > 0;

        if (this._btnUndo) this._btnUndo.disabled = !hasDone || this._isPlaying;
        if (this._btnRedo) this._btnRedo.disabled = !hasRedo || this._isPlaying;
        if (this._btnPlay) this._btnPlay.disabled = !hasRedo || this._isPlaying;
        if (this._btnRewind) this._btnRewind.disabled = !hasDone || this._isPlaying;

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
