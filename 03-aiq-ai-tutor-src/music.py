"""Calm ambient-tech BGM for the AiQ+ video (120 s, 80 BPM).
Structure: 0-8 pad intro / 8-32 + piano arpeggio / 32-96 + bass & soft pulse /
96-108 pulse drops out / 108-120 pad + bells, fade out."""
import numpy as np, wave, sys

SR = 44100
DUR = 121.0
N = int(SR * DUR)
BPM = 80
BEAT = 60 / BPM          # 0.75 s
BAR = BEAT * 4           # 3 s
rng = np.random.default_rng(7)

def midi(n): return 440.0 * 2 ** ((n - 69) / 12)

# chords (MIDI), 2 bars each -> 6 s, cycle 24 s
CH = [
    ([48, 55, 59, 64, 67], 36),   # Cmaj7(add9-ish voicing)  root C2
    ([45, 52, 55, 60, 64], 33),   # Am7
    ([41, 48, 52, 57, 64], 29),   # Fmaj7
    ([43, 50, 55, 59, 62], 31),   # G6/G
]
CHORD_LEN = 2 * BAR

L = np.zeros(N); R = np.zeros(N)
t_all = np.arange(N) / SR

def env_section(t, pts):
    """piecewise-linear gain over song time"""
    xs, ys = zip(*pts)
    return np.interp(t, xs, ys)

def add(sig, start, pan=0.0, gain=1.0):
    i0 = int(start * SR)
    if i0 >= N: return
    i1 = min(N, i0 + len(sig))
    s = sig[: i1 - i0] * gain
    L[i0:i1] += s * np.sqrt(0.5 * (1 - pan))
    R[i0:i1] += s * np.sqrt(0.5 * (1 + pan))

# ---------- Pad ----------
def pad_note(f, length):
    n = int(length * SR); t = np.arange(n) / SR
    s = np.zeros(n)
    for k, a in [(1, 1.0), (2, 0.35), (3, 0.15), (4, 0.06)]:
        for det in (-0.12, 0.12):
            s += a * np.sin(2 * np.pi * f * k * (1 + det / 100) * t + rng.uniform(0, 6.28))
    att, rel = 1.6, 2.2
    e = np.minimum(1, t / att) * np.minimum(1, np.maximum(0, (length - t) / rel))
    lfo = 1 + 0.08 * np.sin(2 * np.pi * 0.18 * t + rng.uniform(0, 6.28))
    return s * e * lfo

ci = 0; t0 = 0.0
while t0 < DUR:
    notes, root = CH[ci % 4]
    for j, n in enumerate(notes):
        add(pad_note(midi(n), CHORD_LEN + 2.0), t0, pan=(-0.5 + j * 0.25), gain=0.030)
    ci += 1; t0 += CHORD_LEN

# ---------- Soft electric piano arpeggio ----------
def ep_note(f, length=2.2, vel=1.0):
    n = int(length * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3)
         + 0.08 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 6))
    e = np.exp(-t * 2.2) * np.minimum(1, t / 0.006)
    return s * e * vel

ARP = [0, 2, 3, 4, 3, 2, 1, 2]  # indices into chord upper notes
ci = 0; t0 = 0.0
while t0 < DUR:
    notes, root = CH[ci % 4]
    upper = [n + 12 for n in notes[1:]]  # 4 notes
    for b in range(16):  # 8th notes over 2 bars
        tt = t0 + b * BEAT / 2
        if tt < 8 or tt > 117: continue
        idx = ARP[b % 8] % len(upper)
        vel = 0.9 if b % 4 == 0 else 0.6
        if 8 <= tt < 16 and b % 2: continue  # sparser at start
        add(ep_note(midi(upper[idx]), vel=vel), tt, pan=(-0.35 if b % 2 else 0.35), gain=0.055)
    ci += 1; t0 += CHORD_LEN

# ---------- Sub bass ----------
def bass_note(f, length):
    n = int(length * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t)
    e = np.minimum(1, t / 0.02) * np.exp(-t * 0.5) * np.minimum(1, np.maximum(0, (length - t) / 0.3))
    return s * e

ci = 0; t0 = 0.0
while t0 < DUR:
    notes, root = CH[ci % 4]
    for bar in range(2):
        tt = t0 + bar * BAR
        if 32 <= tt < 108:
            add(bass_note(midi(root), BAR), tt, gain=0.10)
            add(bass_note(midi(root), BEAT * 1.5), tt + BEAT * 2.5, gain=0.05)
    ci += 1; t0 += CHORD_LEN

# ---------- Soft pulse (kick + shaker) ----------
def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 55 + 70 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9)

def shaker():
    n = int(0.09 * SR); t = np.arange(n) / SR
    s = rng.standard_normal(n)
    s = np.diff(np.concatenate([[0], s]))  # crude high-pass
    return s * np.exp(-t * 45) * np.minimum(1, t / 0.01)

beat = 0
while beat * BEAT < DUR:
    tt = beat * BEAT
    if 32 <= tt < 96:
        if beat % 2 == 0: add(kick(), tt, gain=0.16)
        add(shaker(), tt + BEAT / 2, pan=0.3, gain=0.005)
    beat += 1

# ---------- Bells (sparkle, pentatonic) ----------
def bell(f):
    n = int(3.5 * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 2)
         + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 4))
    return s * np.exp(-t * 1.2) * np.minimum(1, t / 0.003)

PENTA = [76, 79, 81, 84, 86, 88]
tt = 4.5
while tt < 116:
    add(bell(midi(PENTA[rng.integers(len(PENTA))])), tt, pan=rng.uniform(-0.6, 0.6), gain=0.022)
    tt += BAR * (2 if 32 <= tt < 96 else 1.5)

# ---------- Reverb (FFT convolution with decaying noise IR) ----------
def reverb(x, secs=2.8, mix=0.32, seed=1):
    r = np.random.default_rng(seed)
    n = int(secs * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t * 3.2 / secs * 2)
    ir[: int(0.02 * SR)] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    m = len(x) + n
    nf = 1 << (m - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[: len(x)]
    return x * (1 - mix) + y * mix

L = reverb(L, seed=1); R = reverb(R, seed=2)

# master envelope: fade in 0-4 s, fade out 114-120 s
g = env_section(t_all, [(0, 0), (4, 1), (114, 1), (120, 0), (DUR, 0)])
L *= g; R *= g
peak = max(np.abs(L).max(), np.abs(R).max())
L = L / peak * 0.89; R = R / peak * 0.89
out = (np.stack([L, R], 1)[: int(120 * SR)] * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('ok', out.shape)
