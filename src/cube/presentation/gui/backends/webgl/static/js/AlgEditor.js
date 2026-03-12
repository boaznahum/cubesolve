/**
 * AlgEditor — algorithm text editor overlay.
 *
 * Replaces move buttons when active. User types algorithms (e.g., "R U R' U'"),
 * the server validates on each keystroke, and Play/OK buttons reflect validity.
 *
 * Buttons:
 *   Play   — preview algorithm from initial state (no animation)
 *   Apply  — make current state the new initial state
 *   Cancel — restore initial state and dismiss
 *   OK     — restore initial state, play algorithm with animation, dismiss
 */

export class AlgEditor {
    constructor(sendFn) {
        this._send = sendFn;
        this.active = false;
        this._text = '';      // remembered across open/close
        this._valid = false;
        this._debounceTimer = null;

        this._el = document.getElementById('edit-toolbar');
        this._input = document.getElementById('edit-input');

        this._wireButtons();
        this._wireKeyboard();
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
        clearTimeout(this._debounceTimer);

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
            this.exit();
        });
    }

    _wireKeyboard() {
        // Handle input events on the text field
        this._input?.addEventListener('input', (e) => {
            this._onInput(e.target.value);
        });

        // Escape to cancel
        this._input?.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                e.stopImmediatePropagation();
                this._send({ type: 'edit_cancel' });
                this.exit();
            }
            // Enter to play (preview)
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (this._valid) {
                    this._send({ type: 'edit_play', text: this._text });
                }
            }
        });
    }
}
