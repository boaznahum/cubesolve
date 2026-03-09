/**
 * InfoPopup — terminal-style "About" modal with credits and quick-start guide.
 *
 * Displays a retro green-phosphor terminal popup over the canvas.
 * Content is data-driven: sections with items (text + optional URL).
 * Dismiss via OK button, ESC key, or backdrop click.
 */

// ── Content data ──

const HEADER = {
    title: 'CubeSolve',
    author: 'Boaz Nahum',
    email: 'boaznahum2@gmail.com',
    github: 'https://github.com/boaznahum/cubesolve',
};

const SECTIONS = [
    {
        title: 'Credits',
        items: [
            {
                name: 'Herbert Kociemba',
                url: 'http://kociemba.org/cube.htm',
                desc: 'Two-phase algorithm for optimal 3x3 solving',
            },
            {
                name: 'Daniel Walton (dwalton76)',
                url: 'https://github.com/dwalton76/rubiks-cube-NxNxN-solver',
                desc: 'NxNxN solver — IDA* search with lookup tables',
            },
            {
                name: 'Ryan Heise',
                url: 'https://www.ryanheise.com/cube/commutators.html',
                desc: 'Commutator tutorials and 3-cycle techniques',
            },
            {
                name: 'PuzzleMax13',
                url: 'https://www.youtube.com/@puzzlemax13',
                desc: 'Layer-by-layer big cube solving method',
            },
            {
                name: 'Jaap Scherphuis',
                url: 'https://www.jaapsch.net/puzzles/cube2.htm',
                desc: 'Pocket cube theory and analysis',
            },
            {
                name: 'Ruwix',
                url: 'https://ruwix.com/',
                desc: 'Notation, CFOP, commutators, big cube guides',
            },
            {
                name: 'Speedsolving Wiki',
                url: 'https://www.speedsolving.com/wiki/',
                desc: 'Big cube methods, commutators, algorithms',
            },
            {
                name: 'Cubing Cheatsheet',
                url: 'https://cubingcheatsheet.com/',
                desc: 'OLL, PLL, and 6x6 algorithm reference sheets',
            },
            {
                name: 'SpeedcubeDB',
                url: 'https://speedcubedb.com/',
                desc: 'Edge pairing algorithms (L2E)',
            },
            {
                name: 'alg.cubing.net',
                url: 'https://alg.cubing.net/',
                desc: 'Interactive algorithm database and visualizer',
            },
            {
                name: 'NxN Tutorial',
                url: 'https://sites.google.com/view/nxn-tutorial/home',
                desc: 'Comprehensive NxN solving guide',
            },
        ],
    },
    {
        title: 'Academic',
        items: [
            {
                name: 'MIT — Mathematics of Rubik\'s Cube',
                url: 'https://web.mit.edu/sp.268/www/rubik.pdf',
                desc: 'Group theory applied to cube solving',
            },
            {
                name: 'UC Berkeley — Rubik\'s Cube Theory',
                url: 'https://math.berkeley.edu/~hutching/rubik.pdf',
                desc: 'Mathematical framework and analysis',
            },
        ],
    },
    {
        title: 'Technology',
        items: [
            {
                name: 'Three.js',
                url: 'https://threejs.org/',
                desc: '3D WebGL rendering engine',
            },
            {
                name: 'Python',
                url: 'https://python.org/',
                desc: 'Backend solver and server runtime',
            },
            {
                name: 'Pyglet',
                url: 'https://pyglet.readthedocs.io/',
                desc: 'Desktop OpenGL GUI framework',
            },
            {
                name: 'Inter',
                url: 'https://rsms.me/inter/',
                desc: 'UI typeface by Rasmus Andersson',
            },
        ],
    },
    {
        title: 'Quick Start — Both Platforms',
        text: true,
        items: [
            { name: 'Scramble', desc: 'Tap to scramble — uses the seed shown on the button (0-9 for reproducible, * for random)' },
            { name: 'Seed selector', desc: 'Dropdown next to Scramble — pick seed 0-9 (same seed = same scramble) or * for a different scramble each time' },
            { name: 'Solve', desc: 'Tap to compute and auto-play the solution' },
            { name: 'Solution', desc: 'Compute solution without auto-play — step through manually' },
            { name: 'Drag sticker', desc: 'Turn a face by dragging in the desired direction' },
            { name: 'LDB', desc: 'Show hidden faces (Left, Down, Back) beside the cube' },
            { name: 'Assist', desc: 'Shows arrow preview 400ms before each solver move' },
            { name: 'Paint (🎨)', desc: 'Set sticker colors to match your physical cube' },
            { name: '🔊 Sound', desc: 'Toggle mechanical cube-turning sound effects' },
            { name: 'Spd dropdown', desc: 'Control animation speed (0=slow, 7=fast)' },
        ],
    },
    {
        title: 'Desktop — Keyboard & Mouse',
        text: true,
        items: [
            { name: 'U D F B R L', desc: 'Face turns (hold Shift for prime/reverse)' },
            { name: 'M E S', desc: 'Slice moves (middle, equatorial, standing)' },
            { name: 'X Y Z', desc: 'Whole-cube rotations' },
            { name: 'Space', desc: 'Play next queued move' },
            { name: 'Backspace', desc: 'Undo last move' },
            { name: 'F10', desc: 'Toggle shadow faces (L/D/B)' },
            { name: 'Scroll wheel', desc: 'Zoom in/out' },
            { name: 'Alt + drag', desc: 'Pan camera' },
            { name: 'Alt+C / Ctrl+C', desc: 'Reset camera to default view' },
        ],
    },
    {
        title: 'Mobile — Touch & Buttons',
        text: true,
        items: [
            { name: 'Move buttons', desc: 'Tap F, U, R, L, D, B at bottom of screen' },
            { name: 'Shift (⇧) tap', desc: 'Next move reversed (prime), then auto-resets' },
            { name: 'Shift (⇧) hold', desc: 'Lock reversed — all moves prime until tapped again' },
            { name: 'Pinch', desc: 'Zoom in/out with two fingers' },
            { name: 'Single-finger drag', desc: 'Orbit camera around cube' },
            { name: 'Two-finger drag', desc: 'Pan camera' },
            { name: '▶ / ◀ buttons', desc: 'Step forward/backward in history panel' },
        ],
    },
];


export class InfoPopup {
    constructor() {
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
    }

    /** Toggle popup visibility. */
    toggle() {
        if (this._visible) this.hide();
        else this.show();
    }

    /** Show the popup. */
    show() {
        if (!this._built) this._build();
        this._backdrop.style.display = '';
        this._visible = true;

        // Focus OK button for Enter dismiss
        const okBtn = this._dialog.querySelector('.info-ok-btn');
        if (okBtn) okBtn.focus();

        // ESC handler (with stopImmediatePropagation so cube keys don't fire)
        this._keyHandler = (e) => {
            if (e.key === 'Escape' || e.key === 'Enter') {
                e.preventDefault();
                e.stopImmediatePropagation();
                this.hide();
            }
        };
        window.addEventListener('keydown', this._keyHandler, true);
    }

    /** Hide the popup. */
    hide() {
        if (this._backdrop) this._backdrop.style.display = 'none';
        this._visible = false;
        if (this._keyHandler) {
            window.removeEventListener('keydown', this._keyHandler, true);
            this._keyHandler = null;
        }
    }

    /** Build DOM elements (lazy, first call only). */
    _build() {
        // Backdrop
        this._backdrop = document.createElement('div');
        this._backdrop.className = 'info-backdrop';
        this._backdrop.addEventListener('click', (e) => {
            if (e.target === this._backdrop) this.hide();
        });

        // Dialog
        this._dialog = document.createElement('div');
        this._dialog.className = 'info-dialog';

        // Header
        const header = document.createElement('div');
        header.className = 'info-header';

        const title = document.createElement('span');
        title.className = 'info-header-title';
        title.textContent = '$ cubesolve --info';

        const closeBtn = document.createElement('button');
        closeBtn.className = 'info-header-close';
        closeBtn.textContent = '✕';
        closeBtn.addEventListener('click', () => this.hide());

        header.appendChild(title);
        header.appendChild(closeBtn);

        // Content
        const content = document.createElement('div');
        content.className = 'info-content';
        this._renderContent(content);

        // Footer
        const footer = document.createElement('div');
        footer.className = 'info-footer';

        const okBtn = document.createElement('button');
        okBtn.className = 'info-ok-btn';
        okBtn.textContent = 'OK';
        okBtn.addEventListener('click', () => this.hide());

        footer.appendChild(okBtn);

        // Assemble
        this._dialog.appendChild(header);
        this._dialog.appendChild(content);
        this._dialog.appendChild(footer);
        this._backdrop.appendChild(this._dialog);
        document.body.appendChild(this._backdrop);

        this._built = true;
    }

    /** Render content sections from SECTIONS data. */
    _renderContent(container) {
        // Project header block
        const hdr = document.createElement('div');
        hdr.className = 'info-project-header';

        const projName = document.createElement('div');
        projName.className = 'info-project-name';
        projName.textContent = HEADER.title;
        hdr.appendChild(projName);

        const authorLine = document.createElement('div');
        authorLine.className = 'info-project-meta';
        authorLine.textContent = `by ${HEADER.author}`;
        hdr.appendChild(authorLine);

        const linksLine = document.createElement('div');
        linksLine.className = 'info-project-meta';

        const ghLink = document.createElement('a');
        ghLink.className = 'info-item-name';
        ghLink.href = HEADER.github;
        ghLink.target = '_blank';
        ghLink.rel = 'noopener noreferrer';
        ghLink.textContent = 'GitHub';
        linksLine.appendChild(ghLink);

        linksLine.appendChild(document.createTextNode('  ·  '));

        const emailLink = document.createElement('a');
        emailLink.className = 'info-item-name';
        emailLink.href = `mailto:${HEADER.email}`;
        emailLink.textContent = HEADER.email;
        linksLine.appendChild(emailLink);

        hdr.appendChild(linksLine);
        container.appendChild(hdr);

        for (const section of SECTIONS) {
            const sectionEl = document.createElement('div');
            sectionEl.className = 'info-section';

            const titleEl = document.createElement('div');
            titleEl.className = 'info-section-title';
            titleEl.textContent = `>> ${section.title}`;
            sectionEl.appendChild(titleEl);

            for (const item of section.items) {
                const itemEl = document.createElement('div');
                itemEl.className = 'info-item';

                // Name (linked if URL provided)
                if (item.url) {
                    const link = document.createElement('a');
                    link.className = 'info-item-name';
                    link.href = item.url;
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                    link.textContent = item.name;
                    itemEl.appendChild(link);
                } else {
                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'info-item-name';
                    nameSpan.textContent = item.name;
                    itemEl.appendChild(nameSpan);
                }

                // Description
                if (item.desc) {
                    const descSpan = document.createElement('span');
                    descSpan.className = 'info-item-desc';
                    descSpan.textContent = ` — ${item.desc}`;
                    itemEl.appendChild(descSpan);
                }

                sectionEl.appendChild(itemEl);
            }

            container.appendChild(sectionEl);
        }
    }
}
