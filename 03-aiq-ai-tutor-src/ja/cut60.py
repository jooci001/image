"""Cut the 120 s Japanese AiQ+ video to 60 s.
Seven source segments joined with 0.4 s crossfades; narration clips are re-placed at their
source times mapped into the new timeline (only lines fully inside a kept segment are used)."""
import numpy as np, wave, re, subprocess, sys, os
SRC_V, NAR_DIR, NAR_PY, OUT_NAR, OUT_FILTER = sys.argv[1:6]
XF = 0.4
SEG = [  # (src_start, src_end, label)
    (0.0, 8.0,    'title'),
    (14.8, 22.8,  'why: voices -> TO-BE'),
    (23.0, 32.2,  'socratic AI tutor'),
    (33.6, 43.0,  '12 subjects hub'),
    (55.4, 62.4,  'chat demo'),
    (74.2, 87.8,  'use cases'),
    (110.4, 117.6, 'closing'),
]
starts = [float(m) for m in re.findall(r"^\s+\((\d+\.\d+),", open(NAR_PY, encoding='utf-8').read(), re.M)]
def load(f):
    with wave.open(f) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768, w.getframerate()
# output offset of each segment
off = []; acc = 0.0
for i, (a, b, _) in enumerate(SEG):
    off.append(acc); acc += (b - a) - (XF if i < len(SEG) - 1 else 0)
total = acc
sr = load(f'{NAR_DIR}/00.wav')[1]
tr = np.zeros(int(60 * sr) + sr, np.float32); used = []
for i, st in enumerate(starts):
    c, _ = load(f'{NAR_DIR}/{i:02d}.wav'); d = len(c) / sr
    for k, (a, b, lab) in enumerate(SEG):
        # line must sit fully inside the segment, clear of the crossfade zones
        lo = a + (XF if k > 0 else 0); hi = b - (XF if k < len(SEG) - 1 else 0)
        if st >= lo - 0.05 and st + d <= hi + 0.05:
            t = off[k] + (st - a); i0 = int(t * sr); tr[i0:i0 + len(c)] += c[: len(tr) - i0]
            used.append((i, round(t, 2), round(t + d, 2), lab)); break
tr = tr[: int(60 * sr)]
with wave.open(OUT_NAR, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(tr, -1, 1) * 32767).astype(np.int16).tobytes())
# ffmpeg filter: trim each segment, chain xfades
parts = [f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[s{k}]" for k, (a, b, _) in enumerate(SEG)]
prev = 's0'
for k in range(1, len(SEG)):
    o = f'x{k}' if k < len(SEG) - 1 else 'vx'
    parts.append(f"[{prev}][s{k}]xfade=transition=fade:duration={XF}:offset={off[k]:.3f}[{o}]"); prev = o
parts.append(f"[vx]fade=t=out:st={total-1.0:.3f}:d=1.0:color=white,trim=0:60,setpts=PTS-STARTPTS[v]")
open(OUT_FILTER, 'w').write(';\n'.join(parts))
print('video length', round(total, 2))
for u in used: print('line', *u)
