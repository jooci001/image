"""English narration (Supertonic 3, female sid 0) on the 120 s timeline.
Takes are scored against the script with Whisper base.en (on halves split at a pause for long lines)."""
import numpy as np, wave, sys, os, difflib, re
from etools import make_tts, gen, make_asr, asr

LINES = [
    (1.6, 8.6,    "Em and Em, A I Q plus. Introducing our AI tutor for job training."),
    (10.0, 17.8,  "Traditional training meant everyone sat through the same content, on a fixed schedule."),
    (18.4, 22.8,  "What if you could learn when you need it, at your own level?"),
    (24.0, 32.6,  "So we built an AI tutor. Instead of handing out answers, it asks questions back, so you discover them yourself."),
    (34.0, 44.6,  "It brings twelve core job subjects into one tutor, crossing subject boundaries to understand the context behind every question."),
    (46.2, 54.6,  "Learn, ask, and get coached. Three ways to learn, anytime, anywhere."),
    (56.2, 64.0,  "Pick a subject, and Peng, your tutor, guides your thinking one question at a time."),
    (66.6, 72.8,  "When you finish, you get a comprehension report, and a recommendation for what to learn next."),
    (74.6, 78.2,  "For new hires, credit limit questions."),
    (78.3, 81.8,  "For sales managers, new safety procedures."),
    (81.9, 85.4,  "For team leads, local market briefings."),
    (85.6, 88.9,  "Knowledge you can use, right on the job."),
    (90.2, 98.6,  "Not one curriculum for everyone, but one for every individual. Learn ahead, go deeper, and come back anytime."),
    (100.2, 109.6, "Starting in-house, the AI tutor is now expanding to partner training. The more it's used, the more knowledge it builds."),
    (111.2, 113.9, "Ask. Learn. Build."),
    (114.3, 118.4, "Em and Em, A I Q plus."),
]

def norm(x):
    x = x.lower().replace('&', ' and ')
    x = re.sub(r"[^a-z0-9 ]", " ", x)
    x = re.sub(r"\s+", " ", x).strip()
    for a, b in [('em and em', 'mm'), ('m and m', 'mm'), ('m and n', 'mm'), ('a i q plus', 'aiq'), ('aiq plus', 'aiq'), ('a i q', 'aiq'),
                 ('a i ', 'ai '), ('12', 'twelve'), ('3 ', 'three ')]:
        x = x.replace(a, b)
    return x.replace(' ', '')

tts = make_tts(); rec = make_asr()
SR = tts.sample_rate
track = np.zeros(int(120 * SR), np.float32)
os.makedirs('nar_en', exist_ok=True)
pad = np.zeros(int(1.0 * SR), np.float32)
for i, (st, end, text) in enumerate(LINES):
    room = end - st; best = None
    for speed in [1.0, 1.0, 1.0, 1.05, 1.05, 1.05, 1.1, 1.1, 1.15, 1.2]:
        s, _ = gen(tts, text, 0, speed=speed, steps=12)
        nz = np.where(np.abs(s) > 0.01)[0]
        s = s[max(0, nz[0] - int(.03 * SR)): nz[-1] + int(.12 * SR)]
        d = len(s) / SR
        if d > room: continue
        if len(text) > 45:
            e = np.convolve(np.abs(s), np.ones(2000) / 2000, 'same'); n = len(s); k = int(n * .3) + int(np.argmin(e[int(n * .3):int(n * .7)]))
            t = asr(rec, np.concatenate([pad, s[:k], pad]), SR) + ' ' + asr(rec, np.concatenate([pad, s[k:], pad]), SR)
        else:
            t = asr(rec, np.concatenate([pad, s, pad]), SR)
        sc = difflib.SequenceMatcher(None, norm(text), norm(t)).ratio()
        if best is None or sc > best[0]: best = (sc, s, d, speed, t)
        if sc >= 0.97: break
    if best is None:
        print(i, 'DOES NOT FIT', room); sys.exit(1)
    sc, s, d, speed, t = best
    with wave.open(f'nar_en/{i:02d}.wav', 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(s, -1, 1) * 32767).astype(np.int16).tobytes())
    i0 = int(st * SR); track[i0:i0 + len(s)] += s[: len(track) - i0]
    print(i, st, round(d, 2), round(room, 1), speed, round(sc, 3), t.strip(), flush=True)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())
