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

// ── Animation queue ──
const animQueue = new AnimationQueue(cubeModel);
window._testAnimQueue = animQueue;  // Expose for E2E test assertions

// ── WebSocket client ──
const wsClient = new WsClient(handleMessage);
const send = (msg) => wsClient.send(msg);

// ── Face turn handler ──
const faceTurnHandler = new FaceTurnHandler(
    cubeModel, camera, canvas, animQueue, send, scene,
);

// ── Orbit controls ──
const controls = new OrbitControls(camera, canvas, faceTurnHandler, send);

// ── Toolbar ──
const toolbar = new Toolbar(state, send, controls, animQueue);
toolbar.bind();

// ── History panel ──
const historyPanel = new HistoryPanel(send);

// ── Move indicator (next-move arrows) ──
const moveIndicator = new MoveIndicator(cubeModel, scene);

// Track latest history_state for re-showing indicators after animation
let _latestHistoryMsg = null;

// Wire debug overlay callback from AnimationQueue → Toolbar
animQueue._onDebugUpdate = (alg, layers, count) => toolbar.updateDebug(alg, layers, count);

// When all animations finish, re-show move indicators from latest history_state
// (but not during autoplay — indicators would just flash between batches)
animQueue._onAllDone = () => {
    if (state.isPlaying) return;
    if (_latestHistoryMsg && _latestHistoryMsg.next_move) {
        moveIndicator.show(_latestHistoryMsg.next_move);
    }
};

// Wire assist preview callbacks from AnimationQueue → MoveIndicator
animQueue._onAssistShow = (face, layers, direction) => {
    moveIndicator.show({ face, layers, direction });
};
animQueue._onAssistHide = () => {
    moveIndicator.hide();
};

// ── Responsive sizing ──
function resize() {
    const wrapper = canvas.parentElement;
    // Canvas is square: fit within available width and viewport height
    const toolbarH = document.getElementById('toolbar')?.offsetHeight || 40;
    const availH = window.innerHeight - toolbarH - 40;  // toolbar + status bar + padding
    const size = Math.min(wrapper.clientWidth, availH);
    renderer.setSize(size, size);
    camera.aspect = 1;
    camera.updateProjectionMatrix();
}
resize();
window.addEventListener('resize', resize);

// ── Message handler ──
function handleMessage(msg) {
    switch (msg.type) {
        case 'cube_state':
            document.body.style.cursor = '';
            state.latestState = msg;
            if (!animQueue.currentAnim && animQueue.queue.length === 0) {
                cubeModel.updateFromState(msg);
            } else {
                animQueue.pendingState = msg;
            }
            break;

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

        case 'flush_queue':
            animQueue.flush(state.latestState);
            break;

        case 'color_map':
            cubeModel.buildColorCorrections(msg.colors);
            break;

        case 'history_state':
            historyPanel.updateFromServer(msg);
            _latestHistoryMsg = msg;
            // Show next-move indicators if not animating and not in autoplay
            if (!state.isPlaying && !animQueue.currentAnim && animQueue.queue.length === 0) {
                moveIndicator.show(msg.next_move || null);
            }
            break;

        default:
            // Toolbar handles: playing, text_update, version, client_count,
            // speed_update, size_update, toolbar_state, session_id
            toolbar.handleMessage(msg);
            // Forward playing state to history panel + app state
            if (msg.type === 'playing') {
                state.isPlaying = msg.value;
                if (msg.value) moveIndicator.hide();
                historyPanel.setPlaying(msg.value);
            }
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
