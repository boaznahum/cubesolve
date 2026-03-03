/**
 * SoundManager — pleasant mechanical cube rotation sounds via Web Audio API.
 *
 * Produces a soft, satisfying "click-clack" that resembles a real Rubik's
 * cube mechanism — warm low-frequency thump with a gentle tonal tail.
 * No external audio files needed — entirely synthesized.
 *
 * Usage:
 *   const sound = new SoundManager();
 *   sound.play();           // play rotation sound
 *   sound.enabled = false;  // mute
 */

export class SoundManager {
    constructor() {
        this._ctx = null;       // AudioContext (lazy init on first user gesture)
        this._enabled = true;
        this._masterGain = null;
        this._initialized = false;
    }

    get enabled() { return this._enabled; }

    set enabled(val) {
        this._enabled = !!val;
        if (this._masterGain) {
            this._masterGain.gain.value = this._enabled ? 1.0 : 0.0;
        }
    }

    /**
     * Initialize AudioContext lazily (must happen after user gesture).
     */
    _init() {
        if (this._initialized) return;
        try {
            this._ctx = new (window.AudioContext || window.webkitAudioContext)();
            this._masterGain = this._ctx.createGain();
            this._masterGain.gain.value = this._enabled ? 1.0 : 0.0;
            this._masterGain.connect(this._ctx.destination);
            this._initialized = true;
        } catch (e) {
            console.warn('SoundManager: Web Audio API not available', e);
        }
    }

    /**
     * Play a cube rotation sound.
     * @param {number} [volume=0.18] - Volume 0..1
     */
    play(volume = 0.18) {
        if (!this._enabled) return;
        this._init();
        if (!this._ctx) return;

        // Resume context if suspended (autoplay policy)
        if (this._ctx.state === 'suspended') {
            this._ctx.resume();
        }

        const now = this._ctx.currentTime;
        const vol = Math.max(0, Math.min(1, volume));

        // ── Layer 1: Warm mechanical thump (low-frequency body) ──
        this._playThump(now, vol);

        // ── Layer 2: Gentle plastic tick (mid-range, very short) ──
        this._playTick(now, vol * 0.3);

        // ── Layer 3: Soft friction whisper (very quiet filtered noise) ──
        this._playFriction(now, vol * 0.15);
    }

    /**
     * Warm low-frequency thump — the "body" of the rotation sound.
     * Uses a triangle wave for a wooden/plastic feel.
     */
    _playThump(time, vol) {
        const ctx = this._ctx;
        const duration = 0.08;

        const osc = ctx.createOscillator();
        osc.type = 'triangle';
        // Start at a warm mid frequency, sweep down for a "thunk"
        osc.frequency.setValueAtTime(280, time);
        osc.frequency.exponentialRampToValueAtTime(80, time + duration);

        const gain = ctx.createGain();
        // Gentle attack, smooth decay
        gain.gain.setValueAtTime(0, time);
        gain.gain.linearRampToValueAtTime(vol * 0.35, time + 0.003);
        gain.gain.exponentialRampToValueAtTime(0.001, time + duration);

        // Slight low-pass to remove any harshness
        const lpf = ctx.createBiquadFilter();
        lpf.type = 'lowpass';
        lpf.frequency.value = 600;
        lpf.Q.value = 0.5;

        osc.connect(lpf);
        lpf.connect(gain);
        gain.connect(this._masterGain);

        osc.start(time);
        osc.stop(time + duration + 0.01);
    }

    /**
     * Gentle plastic tick — a brief sine "pip" that adds definition.
     */
    _playTick(time, vol) {
        const ctx = this._ctx;
        const duration = 0.035;

        const osc = ctx.createOscillator();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(520, time);
        osc.frequency.exponentialRampToValueAtTime(260, time + duration);

        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0, time);
        gain.gain.linearRampToValueAtTime(vol * 0.25, time + 0.002);
        gain.gain.exponentialRampToValueAtTime(0.001, time + duration);

        osc.connect(gain);
        gain.connect(this._masterGain);

        osc.start(time);
        osc.stop(time + duration + 0.01);
    }

    /**
     * Soft friction whisper — very quiet, short noise to add texture.
     * Simulates the subtle scrape of plastic layers sliding.
     */
    _playFriction(time, vol) {
        const ctx = this._ctx;
        const duration = 0.06;

        // Very short noise buffer
        const bufferSize = Math.ceil(ctx.sampleRate * duration);
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = (Math.random() * 2 - 1);
        }

        const source = ctx.createBufferSource();
        source.buffer = buffer;

        // Low-pass filter — no high frequencies, just a soft rustle
        const lpf = ctx.createBiquadFilter();
        lpf.type = 'lowpass';
        lpf.frequency.value = 1200;
        lpf.Q.value = 0.3;

        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0, time);
        gain.gain.linearRampToValueAtTime(vol * 0.2, time + 0.005);
        gain.gain.exponentialRampToValueAtTime(0.001, time + duration);

        source.connect(lpf);
        lpf.connect(gain);
        gain.connect(this._masterGain);

        source.start(time);
        source.stop(time + duration + 0.01);
    }
}
