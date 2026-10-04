"""Generate narration clips (female KSS voice) and place them on the 120 s timeline.
Each line: (start_sec, latest_end_sec, text). Text is written phonetically where needed."""
import sherpa_onnx, wave, numpy as np, json, sys, os

M = os.path.join(os.path.dirname(__file__), '..', 'vits-mimic3-ko_KO-kss_low')
LINES = [
    (1.6, 8.6,   "엠앤엠, 에이아이큐 플러스. 직무교육 에이아이 튜터를 소개합니다."),
    (10.0, 17.8, "기존 교육은, 모두가 같은 내용을 정해진 일정에 들어야 했습니다."),
    (18.4, 22.8, "필요한 순간에, 내 눈높이에 맞춰 배울 수는 없을까요?"),
    (24.0, 32.6, "그래서 에이아이 튜터를 만들었습니다. 답을 바로 주는 대신, 되물으며 스스로 깨닫게 돕습니다."),
    (34.0, 44.6, "엠앤엠 공통 열두 개 직무 과목을 하나로 통합해, 과목의 경계를 넘나들며 질문의 맥락까지 짚어줍니다."),
    (46.2, 54.6, "배우기, 물어보기, 코칭받기. 세 가지 방식으로 언제 어디서나 학습합니다."),
    (56.2, 64.0, "과목을 고르면, 튜터 펭군이 질문을 던지며 한 단계씩 생각을 이끌어 냅니다."),
    (66.6, 72.8, "학습이 끝나면 이해도 리포트와 함께, 다음 학습까지 추천해 줍니다."),
    (74.6, 78.2, "신입사원은 여신 한도 문의에,"),
    (78.3, 81.8, "에스엠은 바뀐 안전점검 절차에,"),
    (81.9, 85.4, "팀장은 미팅 전 지역 현황에."),
    (85.6, 88.9, "현장에서 바로 꺼내 쓰는 지식입니다."),
    (90.2, 98.6, "모두를 위한 하나의 과정이 아니라, 한 사람 한 사람을 위한 과정. 미리 배우고, 깊게 다지고, 언제든 다시 활용합니다."),
    (100.2, 109.6, "사내에서 시작한 에이아이 튜터는 이제 파트너 교육까지 넓혀갑니다. 쓸수록 지식이 쌓이고, 다시 배움으로 이어집니다."),
    (111.2, 113.9, "묻고, 배우고, 쌓는다."),
    (114.3, 118.4, "엠앤엠, 에이아이큐 플러스."),
]

import sys as _s; _s.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from st import make, gen
tts = make()
import difflib, re
D='sherpa-onnx-zipformer-korean-2024-06-24'
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{D}/encoder-epoch-99-avg-1.int8.onnx', decoder=f'{D}/decoder-epoch-99-avg-1.onnx', joiner=f'{D}/joiner-epoch-99-avg-1.int8.onnx', tokens=f'{D}/tokens.txt', num_threads=4)
TXT = ['']
def norm(x):
    x = x.upper().replace('AIQ', '에이아이큐').replace('AI', '에이아이').replace('SM', '에스엠').replace('3', '세')
    return re.sub(r'[^가-힣]', '', x)
def score(s, sr, text):
    st_ = rec.create_stream(); st_.accept_waveform(sr, s); rec.decode_stream(st_)
    TXT[0] = st_.result.text
    return difflib.SequenceMatcher(None, norm(text), norm(st_.result.text)).ratio()
SR = tts.sample_rate
DUR = 120.0
track = np.zeros(int(DUR * SR), np.float32)
report = []
os.makedirs('aiq/nar', exist_ok=True)
for i, (st, end, text) in enumerate(LINES):
    room = end - st
    best = None
    for trial in range(8):
        speed = [0.97, 1.0, 1.0, 1.04, 0.97, 1.0, 1.04, 1.08][trial]
        s, _sr = gen(tts, text, 0, speed=speed, steps=12)
        nz = np.where(np.abs(s) > 0.01)[0]
        s = s[max(0, nz[0] - int(.03 * SR)): nz[-1] + int(.12 * SR)]
        d = len(s) / SR
        if d > room: continue
        sc = score(s, SR, text)
        if best is None or sc > best[0]: best = (sc, s, d, speed)
        if sc >= 0.97: break
    if best is None:
        speed = 1.15; s, _sr = gen(tts, text, 0, speed=speed, steps=12); d = len(s)/SR; best = (score(s, SR, text), s, d, speed)
    sc, s, d, speed = best
    with wave.open(f'aiq/nar/{i:02d}.wav', 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(s, -1, 1) * 32767).astype(np.int16).tobytes())
    i0 = int(st * SR); track[i0:i0 + len(s)] += s[: len(track) - i0]
    report.append((i, st, round(d, 2), round(room,1), speed, round(sc,3), 'OK' if d <= room else 'OVER', TXT[0]))
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())
for r in report: print(*r)
