/**
 * NotationGuide — compact notation reference modal.
 *
 * Displays a short cheat-sheet of algorithm notation in the terminal theme.
 * Opened from the "?" button inside the algorithm editor toolbar.
 * Dismiss via OK button, ESC key, or backdrop click.
 */

const NOTATION_REF = 'https://www.worldcubeassociation.org/regulations/#article-12-notation';

export class NotationGuide {
    constructor() {
        /** @type {boolean} */
        this._visible = false;
        /** @type {HTMLElement|null} */
        this._backdrop = null;
        /** @type {boolean} */
        this._built = false;
        /** @type {((e: KeyboardEvent) => void)|null} */
        this._keyHandler = null;
    }

    toggle() {
        if (this._visible) this.hide();
        else this.show();
    }

    show() {
        if (!this._built) this._build();
        this._backdrop.style.display = '';
        this._visible = true;

        const okBtn = this._backdrop.querySelector('.info-ok-btn');
        if (okBtn) okBtn.focus();

        this._keyHandler = (e) => {
            if (e.key === 'Escape' || e.key === 'Enter') {
                e.preventDefault();
                e.stopImmediatePropagation();
                this.hide();
            }
        };
        window.addEventListener('keydown', this._keyHandler, true);
    }

    hide() {
        if (this._backdrop) this._backdrop.style.display = 'none';
        this._visible = false;
        if (this._keyHandler) {
            window.removeEventListener('keydown', this._keyHandler, true);
            this._keyHandler = null;
        }
    }

    _build() {
        // Backdrop (reuse info-backdrop class)
        this._backdrop = document.createElement('div');
        this._backdrop.className = 'info-backdrop';
        this._backdrop.addEventListener('click', (e) => {
            if (e.target === this._backdrop) this.hide();
        });

        // Dialog
        const dialog = document.createElement('div');
        dialog.className = 'info-dialog notation-guide-dialog';

        // Header
        const header = document.createElement('div');
        header.className = 'info-header';

        const title = document.createElement('span');
        title.className = 'info-header-title';
        title.textContent = '$ notation --help';

        const closeBtn = document.createElement('button');
        closeBtn.className = 'info-header-close';
        closeBtn.textContent = '\u2715';
        closeBtn.addEventListener('click', () => this.hide());

        header.appendChild(title);
        header.appendChild(closeBtn);

        // Content
        const content = document.createElement('div');
        content.className = 'info-content notation-guide-content';
        this._renderContent(content);

        // Footer
        const footer = document.createElement('div');
        footer.className = 'info-footer';

        const link = document.createElement('a');
        link.className = 'notation-guide-link';
        link.href = NOTATION_REF;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = 'WCA Standard';

        const okBtn = document.createElement('button');
        okBtn.className = 'info-ok-btn';
        okBtn.textContent = 'OK';
        okBtn.addEventListener('click', () => this.hide());

        footer.appendChild(link);
        footer.appendChild(okBtn);

        // Assemble
        dialog.appendChild(header);
        dialog.appendChild(content);
        dialog.appendChild(footer);
        this._backdrop.appendChild(dialog);
        document.body.appendChild(this._backdrop);

        this._built = true;
    }

    _renderContent(container) {
        const lines = [
            ['Faces', "R  L  U  D  F  B", 'clockwise 90\u00B0'],
            ['Prime', "R' L' U' D' F' B'", 'counter-clockwise'],
            ['Double', "R2 L2 U2 D2 F2 B2", '180\u00B0 turn'],
            ['Slice', 'M  E  S', 'middle layer'],
            ['Wide', 'Rw  Lw  r  l ...', '2 layers together'],
            ['Cube', 'X  Y  Z', 'rotate whole cube'],
        ];

        const table = document.createElement('div');
        table.className = 'notation-guide-table';

        for (const [label, moves, desc] of lines) {
            const row = document.createElement('div');
            row.className = 'notation-guide-row';

            const labelEl = document.createElement('span');
            labelEl.className = 'notation-guide-label';
            labelEl.textContent = label;

            const movesEl = document.createElement('span');
            movesEl.className = 'notation-guide-moves';
            movesEl.textContent = moves;

            const descEl = document.createElement('span');
            descEl.className = 'notation-guide-desc';
            descEl.textContent = desc;

            row.appendChild(labelEl);
            row.appendChild(movesEl);
            row.appendChild(descEl);
            table.appendChild(row);
        }

        container.appendChild(table);

        // Tip line
        const tip = document.createElement('div');
        tip.className = 'notation-guide-tip';
        tip.textContent = "Combine moves into algorithms: R U R' U'";
        container.appendChild(tip);
    }
}
