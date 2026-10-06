"""Japanese narration (Supertonic 3, female sid 0) placed on the 120 s timeline.
Each line is generated several times; the take whose Japanese ASR transcript best matches
the script (and fits its scene window) is kept."""
import numpy as np, wave, sys, os, difflib, re, unicodedata
from jtools import make_tts, gen, make_asr, asr

LINES = [
    (1.6, 8.6,    "エムアンドエム・エーアイキュープラス。職務教育エーアイチューターをご紹介します。"),
    (10.0, 17.8,  "これまでの教育では、全員が同じ内容を、決められた日程で受ける必要がありました。"),
    (18.4, 22.8,  "必要な時に、自分の目線で学べないでしょうか。"),
    (24.0, 32.6,  "そこで生まれたのが、エーアイチューターです。すぐに答えを与えず、問い返しながら、自ら気づくよう導きます。"),
    (34.0, 44.6,  "エムアンドエム共通の十二の職務科目をひとつに統合し、科目の境界を越えて、質問の文脈まで読み解きます。"),
    (46.2, 54.6,  "学ぶ、聞く、コーチングを受ける。三つのスタイルで、いつでもどこでも学習できます。"),
    (56.2, 64.0,  "科目を選ぶと、チューターのペンくんが問いかけながら、一歩ずつ考えを導きます。"),
    (66.6, 72.8,  "学習が終わると、理解度レポートとともに、次の学習までおすすめします。"),
    (74.6, 78.2,  "新入社員は、与信枠の相談に。"),
    (78.3, 81.8,  "エスエムは、変わった安全点検の手順に。"),
    (81.9, 85.4,  "チーム長は、商談前の地域状況に。"),
    (85.6, 88.9,  "現場ですぐに使える知識です。"),
    (90.2, 98.6,  "全員に同じカリキュラムではなく、一人ひとりのためのカリキュラムへ。事前に学び、深く固め、いつでも再活用。"),
    (100.2, 109.6, "社内で始まったエーアイチューターは、パートナー教育へと広がっています。使うほど知識が蓄積され、新たな学びへとつながります。"),
    (111.2, 113.9, "問いかけ、学び、積み重ねる。"),
    (114.3, 118.4, "エムアンドエム・エーアイキュープラス。"),
]

def norm(x):
    x = unicodedata.normalize('NFKC', x).upper()
    for a, b in [('エムアンドエム', 'MM'), ('M&M', 'MM'), ('エーアイキュープラス', 'AIQ'), ('AIQ+', 'AIQ'),
                 ('エーアイ', 'AI'), ('エスエム', 'SM'), ('ひとり', '一人'), ('十二', '12'), ('三つ', '3つ'), ('一つ', '1つ'), ('ひとつ', '1つ')]:
        x = x.replace(a, b)
    return re.sub(r'[\s、。，．・,.!?！？「」+&]', '', x)

tts = make_tts(); rec = make_asr()
SR = tts.sample_rate
track = np.zeros(int(120 * SR), np.float32)
os.makedirs('nar_ja', exist_ok=True)
for i, (st, end, text) in enumerate(LINES):
    room = end - st; best = None
    for speed in [1.0, 1.0, 1.0, 1.05, 1.05, 1.05, 1.1, 1.1, 1.15, 1.2]:
        s, _ = gen(tts, text, 0, speed=speed, steps=12)
        nz = np.where(np.abs(s) > 0.01)[0]
        s = s[max(0, nz[0] - int(.03 * SR)): nz[-1] + int(.12 * SR)]
        d = len(s) / SR
        if d > room: continue
        pad = np.zeros(int(1.0 * SR), np.float32)
        t = asr(rec, np.concatenate([pad, s, pad]), SR)
        if len(text) > 24:  # long lines: also score halves split at a pause (ASR drops leading phrases)
            e = np.convolve(np.abs(s), np.ones(2000) / 2000, 'same'); n = len(s); k = int(n * .3) + int(np.argmin(e[int(n * .3):int(n * .7)]))
            t = asr(rec, np.concatenate([pad, s[:k], pad]), SR) + asr(rec, np.concatenate([pad, s[k:], pad]), SR)
        sc = difflib.SequenceMatcher(None, norm(text), norm(t)).ratio()
        if best is None or sc > best[0]: best = (sc, s, d, speed, t)
        if sc >= 0.97: break
    if best is None:
        print(i, 'DOES NOT FIT', room); sys.exit(1)
    sc, s, d, speed, t = best
    with wave.open(f'nar_ja/{i:02d}.wav', 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(s, -1, 1) * 32767).astype(np.int16).tobytes())
    i0 = int(st * SR); track[i0:i0 + len(s)] += s[: len(track) - i0]
    print(i, st, round(d, 2), round(room, 1), speed, round(sc, 3), t, flush=True)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())
