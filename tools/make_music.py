"""Synthesize an original, royalty-free techy background track for Reels.

Usage: python3 tools/make_music.py <out.wav> <seconds> [seed]
120 BPM electronic loop: sidechained pad chords, plucky arpeggio, sub bass, kick, hats and claps.
The seed varies the chord progression and arpeggio pattern so each Reel can sound a bit different.
"""
import sys
import wave

import numpy as np

out_path, SECONDS = sys.argv[1], float(sys.argv[2])
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 0
rng = np.random.default_rng(SEED)
SR, BPM = 44100, 120
BEAT = 60 / BPM
BAR = 4 * BEAT
n = int(SR * SECONDS)
t_all = np.arange(n) / SR


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(length, attack, release):
    e = np.ones(length)
    a, r = int(attack * SR), int(release * SR)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def saw(f, t):
    return 2 * (t * f % 1) - 1


def lowpass(x, cutoff):
    # one-pole low-pass, vectorized via cumulative filtering in blocks
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(0, len(x), 4096):
        blk = x[i:i + 4096]
        out = np.empty_like(blk)
        for j, v in enumerate(blk):
            acc = (1 - a) * v + a * acc
            out[j] = acc
        y[i:i + 4096] = out
    return y


def add(buf, sig, start):
    s = int(start * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(sig))
    buf[s:e] += sig[: e - s]


# Chord progressions (root midi notes, minor/major triads) in A minor
PROGS = [
    [(57, "m"), (53, "M"), (48, "M"), (55, "M")],  # Am F C G
    [(57, "m"), (55, "M"), (53, "M"), (55, "M")],  # Am G F G
    [(50, "m"), (53, "M"), (57, "m"), (55, "M")],  # Dm F Am G
]
prog = PROGS[SEED % len(PROGS)]
TRIAD = {"m": [0, 3, 7], "M": [0, 4, 7]}
arp_shape = rng.permutation([0, 1, 2, 3])  # order of chord tones in the arpeggio

pad = np.zeros(n)
arp = np.zeros(n)
bass = np.zeros(n)
drums = np.zeros(n)

bars = int(np.ceil(SECONDS / BAR))
for b in range(bars):
    root, q = prog[b % 4]
    notes = [root + i for i in TRIAD[q]]
    t0 = b * BAR
    # Pad: detuned saws, one bar long
    L = int(BAR * SR)
    tt = np.arange(L) / SR
    p = sum(saw(midi(m + 12) * d, tt) for m in notes for d in (0.997, 1.003)) / 6
    add(pad, p * env(L, 0.08, 0.15) * 0.22, t0)
    # Bass: root on every beat, eighth-note pulse
    for k in range(8):
        Lb = int(BEAT / 2 * SR)
        tb = np.arange(Lb) / SR
        bsig = np.sin(2 * np.pi * midi(root - 12) * tb) + 0.3 * np.sin(4 * np.pi * midi(root - 12) * tb)
        add(bass, bsig * env(Lb, 0.005, 0.08) * 0.32, t0 + k * BEAT / 2)
    # Arp: sixteenth notes over the chord tones + octave (starts after the first 2 bars)
    if b >= 2:
        tones = notes + [notes[0] + 12]
        for k in range(16):
            m = tones[arp_shape[k % 4]] + 12 * (1 + (k // 8) % 2)
            La = int(BEAT / 4 * SR)
            ta = np.arange(La) / SR
            asig = (np.sign(np.sin(2 * np.pi * midi(m) * ta)) * 0.5 + np.sin(2 * np.pi * midi(m) * ta) * 0.5)
            add(arp, asig * np.exp(-ta * 18) * 0.10, t0 + k * BEAT / 4)
    # Drums
    for k in range(4):
        tk = t0 + k * BEAT
        Lk = int(0.35 * SR)
        tkk = np.arange(Lk) / SR
        kick = np.sin(2 * np.pi * (45 + 110 * np.exp(-tkk * 30)) * tkk) * np.exp(-tkk * 9)
        add(drums, kick * 0.9, tk)
        if k in (1, 3) and b >= 1:  # clap on 2 and 4
            Lc = int(0.18 * SR)
            clap = rng.standard_normal(Lc) * np.exp(-np.arange(Lc) / SR * 25)
            add(drums, clap * 0.18, tk)
        for h in (0.5,):  # offbeat hat
            Lh = int(0.05 * SR)
            hat = rng.standard_normal(Lh) * np.exp(-np.arange(Lh) / SR * 80)
            add(drums, np.diff(hat, prepend=0) * 0.12, tk + h * BEAT)

# Sidechain pump on pad and arp, keyed to the kick
phase = (t_all % BEAT) / BEAT
pump = 0.35 + 0.65 * np.clip(phase * 3.5, 0, 1)
pad = lowpass(pad, 2200) * pump
arp = arp * (0.6 + 0.4 * pump)

mix = pad + arp + lowpass(bass, 400) + drums
# Gentle intro/outro fades, then normalize with headroom for the platform
mix *= env(n, 0.3, 1.5)
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix /= np.max(np.abs(mix)) / 0.85
# Slight stereo width: arp panned, everything else centered
left = mix + 0.15 * arp
right = mix - 0.15 * arp
stereo = np.stack([left, right], axis=1)
stereo /= np.max(np.abs(stereo)) / 0.89
pcm = (stereo * 32767).astype(np.int16)
with wave.open(out_path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(out_path, f"{SECONDS:.1f}s", "seed", SEED)
