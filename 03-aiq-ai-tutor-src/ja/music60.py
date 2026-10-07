"""Bright, upbeat corporate BGM for the AiQ+ video (60 s cut, 112 BPM, D major, I-V-vi-IV).
Layers: marimba-like pluck arps, bright pad, bouncy bass, claps on 2&4, soft hats, sparkle bells.
Sections: 0-4.3 intro (pad+pluck) / 4.3-~107 full / ~107-120 outro (pad+pluck+bells), fade out."""
import numpy as np, wave, sys

SR = 44100
DUR = 61.0
N = int(SR * DUR)
BPM = 112
BEAT = 60 / BPM
BAR = BEAT * 4
rng = np.random.default_rng(11)
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)

# D  A  Bm  G   (one bar each)
CH = [([50, 57, 62, 66, 69], 38), ([45, 52, 57, 61, 64], 33), ([47, 54, 59, 62, 66], 35), ([43, 50, 55, 59, 62], 31)]
L = np.zeros(N); R = np.zeros(N)

def add(sig, start, pan=0.0, gain=1.0):
    i0 = int(start * SR)
    if i0 >= N or i0 < 0: return
    i1 = min(N, i0 + len(sig)); s = sig[: i1 - i0] * gain
    L[i0:i1] += s * np.sqrt(0.5 * (1 - pan)); R[i0:i1] += s * np.sqrt(0.5 * (1 + pan))

def pad(f, length):
    n = int(length * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for k, a in [(1, 1), (2, .5), (3, .25), (4, .12), (5, .06)]:
        for det in (-0.15, 0.15):
            s += a * np.sin(2 * np.pi * f * k * (1 + det / 100) * t + rng.uniform(0, 6.28))
    e = np.minimum(1, t / 0.25) * np.minimum(1, np.maximum(0, (length - t) / 0.6))
    return s * e

def pluck(f, vel=1.0):  # marimba-ish
    n = int(0.9 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 25) + 0.15 * np.sin(2 * np.pi * 10 * f * t) * np.exp(-t * 60)
    return s * np.exp(-t * 6.5) * np.minimum(1, t / 0.002) * vel

def bass(f, length):
    n = int(length * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t)
    return s * np.minimum(1, t / 0.008) * np.exp(-t * 3) * np.minimum(1, np.maximum(0, (length - t) / 0.03))

def kick():
    n = int(0.3 * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(50 + 90 * np.exp(-t * 35)) / SR
    return np.sin(ph) * np.exp(-t * 10)

def noise_hit(length, decay, hp=True):
    n = int(length * SR); t = np.arange(n) / SR; s = rng.standard_normal(n)
    if hp: s = np.diff(np.concatenate([[0], s]))
    return s * np.exp(-t * decay)

def clap():
    s = np.zeros(int(0.25 * SR))
    for off in (0, 0.011, 0.022):
        h = noise_hit(0.2, 22 if off == 0.022 else 70); i = int(off * SR); s[i:i + len(h)] += h[: len(s) - i]
    # band-limit roughly by smoothing
    k = np.ones(6) / 6; return np.convolve(s, k, 'same')

def bell(f):
    n = int(2.5 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3)
    return s * np.exp(-t * 1.8) * np.minimum(1, t / 0.002)

FULL_A, FULL_B = 4 * BAR * 0 + BAR * 2, None
bars = int(DUR / BAR) + 1
outro_bar = int(53 / BAR)
ARP = [0, 2, 1, 3, 2, 4, 3, 2]
for b in range(bars):
    t0 = b * BAR
    notes, root = CH[b % 4]
    full = 2 <= b < outro_bar
    # pad
    for j, n in enumerate(notes[1:]):
        add(pad(midi(n), BAR + 0.5), t0, pan=-0.4 + j * 0.27, gain=0.018)
    # pluck arps (8ths), up an octave
    up = [n + 12 for n in notes]
    for k in range(8):
        tt = t0 + k * BEAT / 2
        if tt > 57.5: continue
        n = up[ARP[k] % len(up)]
        add(pluck(midi(n), 1.0 if k % 2 == 0 else 0.7), tt, pan=(-0.3 if k % 2 else 0.3), gain=0.07)
    if full:
        # bouncy bass: root on 1, octave on & of 2, root on 3, fifth on & of 4
        pat = [(0, root, .9), (1.5, root + 12, .6), (2, root, .8), (3.5, root + 7, .6)]
        for bt, n, v in pat:
            add(bass(midi(n), BEAT * 0.9), t0 + bt * BEAT, gain=0.12 * v)
        # drums
        for bt in (0, 2):
            add(kick(), t0 + bt * BEAT, gain=0.20)
        for bt in (1, 3):
            add(clap(), t0 + bt * BEAT, pan=0.05, gain=0.026)
        for k in range(8):
            add(noise_hit(0.05, 90), t0 + k * BEAT / 2 + (0.012 if k % 2 else 0), pan=0.35, gain=0.007 if k % 2 else 0.004)
    # sparkle bells every 2 bars
    if b % 2 == 0 and t0 < 56:
        PENT = [74, 76, 78, 81, 83, 86]
        add(bell(midi(PENT[rng.integers(len(PENT))])), t0 + BEAT * 3.5, pan=rng.uniform(-.6, .6), gain=0.02)

# light reverb
def reverb(x, secs=1.6, mix=0.18, seed=1):
    r = np.random.default_rng(seed); n = int(secs * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t * 5 / secs); ir[: int(.015 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum())
    nf = 1 << (len(x) + n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[: len(x)]
    return x * (1 - mix) + y * mix
L = reverb(L, seed=1); R = reverb(R, seed=2)
t = np.arange(N) / SR
g = np.interp(t, [0, 1.5, 55, 60, DUR], [0, 1, 1, 0, 0])
L *= g; R *= g
pk = max(np.abs(L).max(), np.abs(R).max()); L = L / pk * .89; R = R / pk * .89
out = (np.stack([L, R], 1)[: int(60 * SR)] * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('ok')
