/**
 * SettingsPopup — terminal-style settings dialog.
 *
 * Opens on gear button click. Shows toggle switches for per-session
 * configuration. ESC / backdrop click discards changes. OK sends
 * changed settings to the server.
 *
 * Fully data-driven: SETTINGS array defines all settings. Each entry
 * specifies the DOM id, label, description, AppState key, server key,
 * and whether it's client-only. The snapshot, populate, and apply
 * logic all loop over the same array — no per-setting special cases.
 */

/**
 * Setting definition.
 * @typedef {{
 *   id: string,
 *   label: string,
 *   desc: string,
 *   stateKey: string,
 *   serverKey: string | null,
 *   clientOnly?: boolean,
 * }} SettingDef
 */

/** @type {SettingDef[]} */
const SETTINGS = [
    {
        id: 'settings-debug',
        label: 'Solver Debug',
        desc: 'Show solver step-by-step annotations',
        stateKey: 'debug',
        serverKey: 'solver_debug',
    },
    {
        id: 'settings-h1',
        label: 'Queue Headings',
        desc: 'Show solver phase names in queue',
        stateKey: 'queueHeadingH1',
        serverKey: 'queue_heading_h1',
    },
    {
        id: 'settings-h2',
        label: 'Queue Sub-headings',
        desc: 'Show sub-step details in queue',
        stateKey: 'queueHeadingH2',
        serverKey: 'queue_heading_h2',
    },
    {
        id: 'settings-assist',
        label: 'Assist',
        desc: 'Show move indicator before each animation',
        stateKey: 'assistEnabled',
        serverKey: 'assist_enabled',
    },
    {
        id: 'settings-shadows',
        label: 'Show Shadows (LDB)',
        desc: 'Show hidden faces beside the cube',
        stateKey: '_shadows',   // special: computed from cubeModel
        serverKey: null,        // client-only, no server message
        clientOnly: true,
    },
];

export class SettingsPopup {
    /**
     * @param {function} sendFn  — send message to server
     * @param {object}   appState — AppState instance (read current values)
     * @param {object}   cubeModel — CubeModel for shadow toggle (client-only)
     */
    constructor(sendFn, appState, cubeModel) {
        this._send = sendFn;
        this._state = appState;
        this._cubeModel = cubeModel;

        /** @type {function|null} Callback after settings applied (e.g. update shadow buttons). */
        this.onApply = null;

        /** @type {boolean} */
        this._visible = false;
        /** @type {HTMLElement|null} */
        this._backdrop = null;
        /** @type {HTMLElement|null} */
        this._dialog = null;
        /** @type {boolean} */
        this._built = false;
        /** @type {((e: KeyboardEvent) => void)|null} */
        this._keyHandler = null;

        // Snapshot of values when dialog opens (for cancel/discard)
        /** @type {Object<string, boolean>} keyed by setting id */
        this._snapshot = {};
    }

    get visible() { return this._visible; }

    /** Toggle popup visibility. */
    toggle() {
        if (this._visible) this.hide();
        else this.show();
    }

    /** Show the popup — snapshot current values. */
    show() {
        if (!this._built) this._build();

        // Snapshot all settings from current state
        for (const s of SETTINGS) {
            this._snapshot[s.id] = this._readCurrentValue(s);
            this._setToggle(s.id, this._snapshot[s.id]);
        }

        this._backdrop.style.display = '';
        this._visible = true;

        // Focus OK button for Enter dismiss
        const okBtn = this._dialog.querySelector('.info-ok-btn');
        if (okBtn) okBtn.focus();

        // ESC → discard, Enter → OK (with stopImmediatePropagation so cube keys don't fire)
        this._keyHandler = (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                e.stopImmediatePropagation();
                this._discard();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                e.stopImmediatePropagation();
                this._apply();
            }
        };
        window.addEventListener('keydown', this._keyHandler, true);
    }

    /** Hide the popup (no action). */
    hide() {
        if (this._backdrop) this._backdrop.style.display = 'none';
        this._visible = false;
        if (this._keyHandler) {
            window.removeEventListener('keydown', this._keyHandler, true);
            this._keyHandler = null;
        }
    }

    /** Discard changes and close. */
    _discard() {
        this.hide();
    }

    /** Read current value for a setting from appState or cubeModel. */
    _readCurrentValue(s) {
        if (s.stateKey === '_shadows') {
            return this._cubeModel
                ? ['L', 'D', 'B'].some(f => this._cubeModel.shadowVisible[f])
                : false;
        }
        return !!this._state[s.stateKey];
    }

    /** Apply changes and close. */
    _apply() {
        // Collect server-side changes
        const serverSettings = {};
        let hasServerChanges = false;

        for (const s of SETTINGS) {
            const newVal = this._getToggle(s.id);
            const oldVal = this._snapshot[s.id];
            if (newVal === oldVal) continue;

            if (s.serverKey) {
                // Server-side setting
                serverSettings[s.serverKey] = newVal;
                hasServerChanges = true;
            } else if (s.clientOnly) {
                // Client-only: apply directly
                this._applyClientSetting(s, newVal);
            }
        }

        if (hasServerChanges) {
            this._send({ type: 'set_config', settings: serverSettings });
        }

        if (this.onApply) this.onApply();
        this.hide();
    }

    /** Apply a client-only setting change. */
    _applyClientSetting(s, newVal) {
        if (s.stateKey === '_shadows' && this._cubeModel) {
            for (const f of ['L', 'D', 'B']) {
                if (newVal && !this._cubeModel.shadowVisible[f]) {
                    this._cubeModel.toggleShadow(f);
                } else if (!newVal && this._cubeModel.shadowVisible[f]) {
                    this._cubeModel.toggleShadow(f);
                }
            }
        }
    }

    // -- Toggle helpers --

    _setToggle(id, value) {
        const el = document.getElementById(id);
        if (el) el.checked = value;
    }

    _getToggle(id) {
        const el = document.getElementById(id);
        return el ? el.checked : false;
    }

    // -- DOM construction --

    _build() {
        // Backdrop (reuses info-backdrop class)
        this._backdrop = document.createElement('div');
        this._backdrop.className = 'info-backdrop';
        this._backdrop.addEventListener('click', (e) => {
            if (e.target === this._backdrop) this._discard();
        });

        // Dialog (reuses info-dialog class)
        this._dialog = document.createElement('div');
        this._dialog.className = 'info-dialog settings-dialog';

        // Header
        const header = document.createElement('div');
        header.className = 'info-header';

        const title = document.createElement('span');
        title.className = 'info-header-title';
        title.textContent = '$ cubesolve --settings';

        const closeBtn = document.createElement('button');
        closeBtn.className = 'info-header-close';
        closeBtn.textContent = '\u2715';
        closeBtn.addEventListener('click', () => this._discard());

        header.appendChild(title);
        header.appendChild(closeBtn);

        // Content — built from SETTINGS array
        const content = document.createElement('div');
        content.className = 'info-content settings-content';

        for (const setting of SETTINGS) {
            const row = document.createElement('div');
            row.className = 'settings-row';

            const labelWrap = document.createElement('div');
            labelWrap.className = 'settings-label-wrap';

            const label = document.createElement('label');
            label.className = 'settings-label';
            label.htmlFor = setting.id;
            label.textContent = setting.label;

            const desc = document.createElement('div');
            desc.className = 'settings-desc';
            desc.textContent = setting.desc;

            labelWrap.appendChild(label);
            labelWrap.appendChild(desc);

            // Toggle switch
            const toggle = document.createElement('label');
            toggle.className = 'settings-toggle';

            const input = document.createElement('input');
            input.type = 'checkbox';
            input.id = setting.id;

            const slider = document.createElement('span');
            slider.className = 'settings-slider';

            toggle.appendChild(input);
            toggle.appendChild(slider);

            row.appendChild(labelWrap);
            row.appendChild(toggle);
            content.appendChild(row);
        }

        // Footer with Cancel + OK
        const footer = document.createElement('div');
        footer.className = 'info-footer';

        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'settings-cancel-btn';
        cancelBtn.textContent = 'Cancel';
        cancelBtn.addEventListener('click', () => this._discard());

        const okBtn = document.createElement('button');
        okBtn.className = 'info-ok-btn';
        okBtn.textContent = 'OK';
        okBtn.addEventListener('click', () => this._apply());

        footer.appendChild(cancelBtn);
        footer.appendChild(okBtn);

        // Assemble
        this._dialog.appendChild(header);
        this._dialog.appendChild(content);
        this._dialog.appendChild(footer);
        this._backdrop.appendChild(this._dialog);
        document.body.appendChild(this._backdrop);

        this._built = true;
    }
}
