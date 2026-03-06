/**
 * WebGL Cube Client — Entry point.
 *
 * Wires together all modules: scene, model, animation, controls,
 * WebSocket client, and toolbar.
 */

import * as THREE from 'three';
import { BACKGROUND_COLOR } from './constants.js';
import { AppState } from './AppState.js';
import { CubeModel } from './CubeModel.js';
import { AnimationQueue } from './AnimationQueue.js';
import { FaceTurnHandler } from './FaceTurnHandler.js';
import { OrbitControls } from './OrbitControls.js';
import { WsClient } from './WsClient.js';
import { Toolbar } from './Toolbar.js';
import { HistoryPanel } from './HistoryPanel.js';
import { MoveIndicator } from './MoveIndicator.js';
import { SoundManager } from './SoundManager.js';

// ── Application state ──
const state = new AppState();
window.appState = state;  // Expose for E2E test assertions

// ── Three.js setup ──
const canvas = document.getElementById('canvas');

const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true,
    alpha: false,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(BACKGROUND_COLOR);
renderer.outputEncoding = THREE.sRGBEncoding;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);

// Lighting
const ambient = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambient);

const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight.position.set(5, 8, 6);
scene.add(dirLight);

const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
dirLight2.position.set(-3, -2, 4);
scene.add(dirLight2);

// ── Cube model ──
const cubeModel = new CubeModel(scene);

// ── WebSocket client ──
const wsClient = new WsClient(handleMessage);
const send = (msg) => wsClient.send(msg);

// ── Sound manager ──
const soundManager = new SoundManager();

// ── Animation queue ──
const animQueue = new AnimationQueue(cubeModel, send, soundManager);
window._testAnimQueue = animQueue;  // Expose for E2E test assertions

// ── Face turn handler ──
const faceTurnHandler = new FaceTurnHandler(
    cubeModel, camera, canvas, animQueue, send, scene,
);

// ── Orbit controls ──
const controls = new OrbitControls(camera, canvas, faceTurnHandler, send);

// ── Toolbar ──
const toolbar = new Toolbar(state, send, controls, animQueue, soundManager);
toolbar.bind();

// ── History panel ──
const historyPanel = new HistoryPanel(send, animQueue, state);

// ── Move indicator (next-move arrows) ──
const moveIndicator = new MoveIndicator(cubeModel, scene);

/** Check if assist is active (respects local user override). */
function isAssistActive() {
    if (toolbar._assistLocalOverride !== undefined) {
        return toolbar._assistLocalOverride;
    }
    return state.assistEnabled;
}

// Wire debug overlay callback from AnimationQueue → Toolbar
animQueue._onDebugUpdate = (alg, layers, count) => toolbar.updateDebug(alg, layers, count);

// When all animations finish, update stop button and re-show move indicators
animQueue._onAllDone = () => {
    // Update stop button from state machine
    const stopBtn = document.getElementById('btn-stop');
    const a = state.allowedActions || {};
    if (stopBtn) {
        stopBtn.disabled = !a.stop;
    }
    // Re-show move indicators (but not during autoplay, and only if assist is on)
    if (state.isPlaying) return;
    if (isAssistActive() && state.nextMove) {
        moveIndicator.show(state.nextMove);
    }
};

// Wire assist preview callbacks from AnimationQueue → MoveIndicator
animQueue._onAssistShow = (face, layers, direction, isUndo) => {
    if (!isAssistActive()) return;
    moveIndicator.show({ face, layers, direction }, { isUndo });
};
animQueue._onAssistHide = () => {
    moveIndicator.hide();
};

// ── Responsive sizing ──
let _lastAspect = 0;

function resize() {
    const wrapper = canvas.parentElement;
    const isMobile = window.matchMedia('(max-width: 768px)').matches;
    let w, h;

    if (isMobile) {
        w = wrapper.clientWidth;
        h = wrapper.clientHeight;

        // Fallback: on iOS initial load, flex layout may not have settled yet
        // so wrapper dimensions can be 0.  Compute from viewport instead.
        if (h < 50) {
            const toolbarEl = document.getElementById('toolbar');
            const statusEl = document.getElementById('status');
            const vpH = window.visualViewport?.height ?? window.innerHeight;
            h = vpH - (toolbarEl?.offsetHeight || 50) - (statusEl?.offsetHeight || 20) - 10;
        }
        if (w < 50) {
            const histPanel = document.getElementById('history-panel');
            w = window.innerWidth - (histPanel?.offsetWidth || 62) - 8;
        }

        renderer.setSize(w, h);
        camera.aspect = w / h;
    } else {
        const toolbarH = document.getElementById('toolbar')?.offsetHeight || 40;
        const availH = window.innerHeight - toolbarH - 40;
        const size = Math.min(wrapper.clientWidth, availH);
        renderer.setSize(size, size);
        camera.aspect = 1;
    }

    camera.updateProjectionMatrix();

    // Adjust camera distance when aspect ratio changes (orientation change, etc.)
    const aspect = camera.aspect;
    if (Math.abs(aspect - _lastAspect) > 0.01) {
        _lastAspect = aspect;
        controls.fitToView(aspect);
    }
}

// Initial resize
resize();
window.addEventListener('resize', resize);

// iOS: visualViewport fires more reliably on orientation change / keyboard show
if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', resize);
}

// Delayed resize — catches late CSS flex layout on iOS first load
requestAnimationFrame(() => requestAnimationFrame(resize));

// Reset camera and resize on every WebSocket (re)connection
wsClient.onConnected = () => {
    controls.reset();
    _lastAspect = 0;  // force fitToView recalc
    resize();
};

// ── Message handler ──
function handleMessage(msg) {
    switch (msg.type) {
        case 'state': {
            // Unified state snapshot — single source of truth
            document.body.style.cursor = '';

            const wasPlaying = state.isPlaying;

            // Apply snapshot to AppState (updates all fields)
            state.applyServerSnapshot(msg);

            // Update cube model if not animating (including assist preview phase)
            if (state.latestState && !animQueue.isBusy) {
                cubeModel.updateFromState(state.latestState);
            } else if (state.latestState) {
                animQueue.pendingState = state.latestState;
            }

            // Update all UI components from the single state
            toolbar.updateFromState(state);
            historyPanel.updateFromState(state);

            // Update assist delay from state (skip if user locally overrode assist checkbox)
            if (toolbar._assistLocalOverride === undefined) {
                animQueue.assistDelayMs = state.assistEnabled ? state.assistDelayMs : 0;
            }

            // Save session ID
            if (state.sessionId) {
                localStorage.setItem('cube_session_id', state.sessionId);
            }

            // Show next-move indicators if assist is on, not animating, not in autoplay
            if (isAssistActive() && !state.isPlaying && !animQueue.isBusy) {
                moveIndicator.show(state.nextMove);
            }
            if ((state.isPlaying && !wasPlaying) || !isAssistActive()) {
                moveIndicator.hide();
            }

            // Sync client playback mode from server state machine
            const ms = state.machineState;
            if (ms === 'playing' && animQueue.playbackMode !== 'forward') {
                animQueue.startPlayback('forward');
                // If transitioning to PLAYING (e.g., solve_and_play), request first move
                if (!wasPlaying) {
                    send({ type: 'play_next_redo' });
                }
            } else if (ms === 'rewinding' && animQueue.playbackMode !== 'backward') {
                animQueue.startPlayback('backward');
                if (!wasPlaying) {
                    send({ type: 'play_next_undo' });
                }
            } else if (ms !== 'playing' && ms !== 'rewinding' && ms !== 'animating' && ms !== 'stopping') {
                if (animQueue.playbackMode !== null) {
                    animQueue.stopPlayback();
                }
            }
            break;
        }

        case 'animation_start': {
            if (moveIndicator.isVisible) moveIndicator.hide();
            const animState = msg.state || state.latestState;
            if (animState) {
                state.latestState = animState;
                animQueue.enqueue(msg, animState);
            }
            break;
        }

        case 'animation_stop':
            animQueue.stop();
            if (state.latestState) {
                cubeModel.updateFromState(state.latestState);
            }
            break;

        case 'play_empty':
            // No more moves — stop playback
            animQueue.stopPlayback();
            break;

        case 'flush_queue':
            animQueue.flush(state.latestState);
            break;

        case 'color_map':
            cubeModel.buildColorCorrections(msg.colors);
            break;
    }
}

// ── Render loop ──
let lastTime = performance.now();
function animate() {
    requestAnimationFrame(animate);
    const now = performance.now();
    const dt = (now - lastTime) / 1000;
    lastTime = now;

    animQueue.update();
    moveIndicator.updatePulse(dt);
    renderer.render(scene, camera);
}
animate();

// ── Connect ──
wsClient.connect();
