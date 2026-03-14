/**
 * AlgEditor — algorithm text editor overlay with localStorage persistence.
 *
 * Replaces move buttons when active. User types algorithms (e.g., "R U R' U'"),
 * the server validates on each keystroke, and Play/OK buttons reflect validity.
 *
 * Persistence:
 *   - Latest editor text auto-saved to localStorage (restored on page load)
 *   - Named algorithms: add `%name=myAlg` as first line to save/load by name
 *   - Saved algs stored in localStorage under "cubesolve_saved_algs" key
 *   - A dropdown lets you browse, load, and delete saved algs
 *
 * Buttons:
 *   Play   — preview algorithm from initial state (no animation)
 *   Apply  — make current state the new initial state
 *   Cancel — restore initial state and dismiss
 *   OK     — restore initial state, play algorithm with animation, dismiss
 */

const LS_KEY_TEXT = 'cubesolve_editor_text';
const LS_KEY_ALGS = 'cubesolve_saved_algs';

export class AlgEditor {
    constructor(sendFn) {
        this._send = sendFn;
        this.active = false;
        this._text = '';      // remembered across open/close
        this._valid = false;
        this._debounceTimer = null;

        this._el = document.getElementById('edit-toolbar');
        this._input = document.getElementById('edit-input');
        this._algSelect = document.getElementById('edit-alg-select');
        this._algDeleteBtn = document.getElementById('edit-alg-delete');

        // Restore text from localStorage
        const saved = localStorage.getItem(LS_KEY_TEXT);
        if (saved) this._text = saved;

        this._wireButtons();
        this._wireKeyboard();
        this._wireAlgBrowser();
    }

    /* ── Public API ─────────────────────────────────────── */

    enter() {
        if (this.active) return;
        this.active = true;

        this._send({ type: 'enter_edit_mode' });

        // Show editor, hide move buttons
        this._el.style.display = '';
        document.getElementById('move-buttons').style.display = 'none';
        document.getElementById('history-panel').classList.add('hp-hidden');
        document.body.classList.add('edit-mode');

        // Restore remembered text
        this._input.value = this._text;
        this._updateButtonStates();
        this._refreshAlgList();
        this._input.focus();

        // Validate if there's existing text
        if (this._text.trim()) {
            this._sendParse(this._text);
        }
    }

    exit() {
        if (!this.active) return;
        this.active = false;

        clearTimeout(this._debounceTimer);

        this._el.style.display = 'none';
        document.getElementById('move-buttons').style.display = '';
        document.getElementById('history-panel').classList.remove('hp-hidden');
        document.body.classList.remove('edit-mode');
    }

    /** Handle parse result from server. */
    onParseResult(valid, error) {
        this._valid = valid;
        this._updateButtonStates();
    }

    /** Apply server state — update remembered text and active flag. */
    applyState(editMode, editAlgText) {
        if (editAlgText !== undefined) {
            this._text = editAlgText;
            if (this.active && this._input) {
                this._input.value = this._text;
            }
        }
        // If server says we're not in edit mode but we think we are, exit
        if (!editMode && this.active) {
            this.exit();
        }
    }

    /* ── Internal ───────────────────────────────────────── */

    _sendParse(text) {
        this._send({ type: 'parse_alg', text });
    }

    _onInput(text) {
        this._text = text;
        this._persistText(text);
        clearTimeout(this._debounceTimer);

        // Auto-save named alg
        this._autoSaveNamed(text);

        if (!text.trim()) {
            this._valid = false;
            this._updateButtonStates();
            return;
        }

        this._debounceTimer = setTimeout(() => {
            this._sendParse(text);
        }, 150);
    }

    _updateButtonStates() {
        const playBtn = document.getElementById('edit-play');
        const okBtn = document.getElementById('edit-ok');

        if (playBtn) {
            playBtn.disabled = !this._valid;
            playBtn.classList.toggle('edit-btn-green', this._valid);
            playBtn.classList.toggle('edit-btn-red', !this._valid);
        }
        if (okBtn) {
            okBtn.disabled = !this._valid;
            okBtn.classList.toggle('edit-btn-green', this._valid);
            okBtn.classList.toggle('edit-btn-red', !this._valid);
        }
    }

    _wireButtons() {
        document.getElementById('edit-play')?.addEventListener('click', () => {
            if (!this._valid) return;
            this._send({ type: 'edit_play', text: this._text });
        });

        document.getElementById('edit-apply')?.addEventListener('click', () => {
            this._send({ type: 'edit_apply' });
        });

        document.getElementById('edit-cancel')?.addEventListener('click', () => {
            this._send({ type: 'edit_cancel' });
            this.exit();
        });

        document.getElementById('edit-ok')?.addEventListener('click', () => {
            if (!this._valid) return;
            this._send({ type: 'edit_ok', text: this._text });
            // Don't call exit() here — server will send editMode=false
            // when it exits EDITING state, and applyState() will call exit()
        });
    }

    _wireKeyboard() {
        // Handle input events on the text field
        this._input?.addEventListener('input', (e) => {
            this._onInput(e.target.value);
        });

        // Escape to cancel, Ctrl+Enter to play
        this._input?.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                e.stopImmediatePropagation();
                this._send({ type: 'edit_cancel' });
                this.exit();
            }
            // Ctrl+Enter to play (preview) — plain Enter inserts newline in textarea
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                if (this._valid) {
                    this._send({ type: 'edit_play', text: this._text });
                }
            }
        });
    }

    /* ── localStorage persistence ───────────────────────── */

    _persistText(text) {
        try { localStorage.setItem(LS_KEY_TEXT, text); } catch { /* quota */ }
    }

    /** Extract %name=xxx from first line, if present. */
    _parseName(text) {
        const m = text.match(/^%name\s*=\s*(.+)/m);
        return m ? m[1].trim() : null;
    }

    /** Auto-save named alg to localStorage when %name= header present. */
    _autoSaveNamed(text) {
        const name = this._parseName(text);
        if (!name) return;
        const store = this._loadStore();
        store[name] = text;
        this._saveStore(store);
        this._refreshAlgList();
    }

    _loadStore() {
        try {
            const raw = localStorage.getItem(LS_KEY_ALGS);
            if (raw) return JSON.parse(raw);
        } catch { /* corrupted */ }
        return {};
    }

    _saveStore(store) {
        try { localStorage.setItem(LS_KEY_ALGS, JSON.stringify(store)); } catch { /* quota */ }
    }

    /* ── Saved alg browser ──────────────────────────────── */

    _wireAlgBrowser() {
        // Load selected alg
        this._algSelect?.addEventListener('change', () => {
            const name = this._algSelect.value;
            if (!name) return;
            const store = this._loadStore();
            const text = store[name];
            if (text !== undefined) {
                this._text = text;
                this._input.value = text;
                this._persistText(text);
                this._onInput(text);
            }
            // Reset select to placeholder after loading
            this._algSelect.value = '';
        });

        // Delete selected alg
        this._algDeleteBtn?.addEventListener('click', () => {
            const name = this._parseName(this._text);
            if (!name) return;
            const store = this._loadStore();
            if (!(name in store)) return;
            if (!confirm(`Delete saved alg "${name}"?`)) return;
            delete store[name];
            this._saveStore(store);
            this._refreshAlgList();
        });
    }

    _refreshAlgList() {
        if (!this._algSelect) return;
        const store = this._loadStore();
        const names = Object.keys(store).sort();

        // Clear existing options (keep placeholder)
        while (this._algSelect.options.length > 1) {
            this._algSelect.remove(1);
        }

        for (const name of names) {
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            this._algSelect.appendChild(opt);
        }

        // Show/hide delete button based on whether current text has a name
        if (this._algDeleteBtn) {
            const currentName = this._parseName(this._text);
            this._algDeleteBtn.style.display = currentName ? '' : 'none';
        }
    }
}
