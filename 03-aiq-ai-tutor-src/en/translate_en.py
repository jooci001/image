"""Build scene_en.html from the Korean AiQ+ scene by exact-string replacement.
Fails if any source string is missing or any Hangul remains."""
import re, sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()

R = [
 ('<html lang="ko">', '<html lang="en">'),
 ('font-family:"WenQuanYi Zen Hei","Noto Color Emoji",sans-serif;', 'font-family:"Inter","Noto Color Emoji",sans-serif;letter-spacing:-.01em;'),
 ('<style>', '<style>\n@font-face{font-family:"Inter";src:url(fonts/InterVariable.ttf) format("truetype");font-weight:100 900}'),
 ('.h1,.h2,.voice,.tobe,.band,.way .t,.side .s .t,.pill,.step3 .t,.big,b{-webkit-text-stroke:.03em currentColor}',
  '.h1,.h2,.voice,.tobe,.band,.way .t,.side .s .t,.pill,.step3 .t,.big,b{font-weight:700}.h1{font-weight:800;letter-spacing:-.03em}.h2{letter-spacing:-.02em}'),
 ('font-size:34px;white-space:nowrap;color:var(--navy)}', 'font-size:32px;white-space:nowrap;color:var(--navy)}'),
 ('padding:0 16px;font-size:23px;color:var(--navy)', 'padding:0 16px;font-size:21px;color:var(--navy)'),
 # S1
 ('Mobility &amp; Marketing 본부 · 직무교육 AI Tutor', 'Mobility &amp; Marketing Division · AI Tutor for Job Training'),
 ('언제·어디서나 내 곁에서, <span style="color:var(--navy)">묻고 답하는 AI 튜터</span>',
  'Always by your side — <span style="color:var(--navy)">an AI tutor that asks and answers</span>'),
 # S2
 ('기존 교육은, 아쉬운 점이 있었습니다', 'Traditional training had its limits'),
 ('[ 구성원의 목소리 ]', '[ Voices from employees ]'),
 ('“집체교육, 또 모여야 하나요?”', '“Do we really have to gather again?”'),
 ('“아는 건 또 듣고, 모르는 건 물어볼 데가 없어요.”', '“Same old content, and no one to ask.”'),
 ('“뭘 모르는지도, 누구에게 물어야 할지도…”', '“I don’t even know what I don’t know…”'),
 ('언제든 필요할 때, 바로 학습', 'Learn right when you need it'),
 ('내 수준에 맞춰, 필요한 내용만', 'Just what you need, at your level'),
 ('막막할 땐, 딱 맞춘 과목 설계로', 'Stuck? Get a tailored path'),
 ('필요한 순간, 필요한 지식을 각자의 눈높이에 맞춰', 'The right knowledge, at the right moment, for every learner'),
 # S3
 ('그래서, <span style="color:var(--teal)">AI Tutor</span>를<br>만들었습니다', 'So we built<br>an <span style="color:var(--teal)">AI Tutor</span>'),
 ('>소크라틱 방식<', '>Socratic method<'),
 ('답을 바로 주지 않고, 되물어 스스로 깨닫게', 'Asks back instead of handing out answers'),
 ('>내 수준에 맞춰<', '>Fits your level<'),
 ('내 수준을 진단하고, 딱 맞는 깊이로', 'Diagnoses your level, matches the depth'),
 ('소크라틱 AI 튜터 <b style="color:var(--navy)">‘펭군’</b>', 'Socratic AI tutor <b style="color:var(--navy)">“Peng”</b>'),
 # S4
 ('M&amp;M 공통 <span style="color:var(--teal)">12개 직무 과목</span>을 하나의 AI Tutor로',
  '<span style="color:var(--teal)">12 core job subjects</span>, one AI Tutor'),
 ('지식 12 / 12', 'Knowledge 12 / 12'),
 ('과목의 경계를 넘나들며 (Boundary-Crossing) 질문의 맥락까지 짚어줍니다', 'Crossing subject boundaries to read the context behind every question'),
 ("'M&M 경제성 평가의 이해'", "'M&M Economic Evaluation'"), ("'M&M 본부 손익의 이해'", "'M&M Division P&L'"),
 ("'Pricing 및 가격정책'", "'Pricing & Price Policy'"), ("'여신 및 담보설정'", "'Credit & Collateral'"),
 ("'SAP 활용법_주문/채권'", "'SAP Orders/Receivables'"), ("'사고채권관리 및 법적절차'", "'Bad Debt & Legal Steps'"),
 ("'주유소 영업시설 관리'", "'Station Facility Mgmt'"), ("'회사 마케팅프로그램'", "'Marketing Programs'"),
 ("'Network 개발 프로세스'", "'Network Development'"), ("'CC제도 및 파트너플러스'", "'CC & Partner Plus'"),
 ("'중대재해처벌법과 안전관리'", "'Safety & Accident Law'"), ("'회사 공정 및 제품의 이해'", "'Refining & Products'"),
 # S5
 ('>세 가지 학습 방식<', '>Three ways to learn<'),
 ('배우고, 묻고, 코칭받는 AI 튜터', 'Learn, ask, and get coached'),
 ('“모두가 같은 강의를 들어야 함”', '“Everyone sits through the same lecture”'),
 ('배우기 📖', 'Learn 📖'), ('과목을 골라 수준별로 학습', 'Pick a subject, study at your level'),
 ('“궁금할 땐 물어볼 곳이 없음”', '“No one to ask when questions come up”'),
 ('물어보기 💬', 'Ask 💬'), ('업무 중 궁금한 건 바로 질문', 'Ask anything, mid-task'),
 ('“뭐부터 알아야 할지 막막함”', '“No idea where to start”'),
 ('코칭받기 🧭', 'Coach 🧭'), ('나에게 맞는 커리큘럼 추천', 'Get a curriculum that fits you'),
 # S6
 ('03 · HOW · 배우기', '03 · HOW · Learn'),
 ('>과목 선택<', '>Pick a subject<'), ('12개 직무 과목 중 선택', 'Choose from 12 job subjects'),
 ('>소크라틱 학습<', '>Socratic learning<'), ('수준에 맞춘 문답, 한 단계씩', 'Step-by-step Q&amp;A at your level'),
 ('>학습 정리<', '>Wrap-up<'), ('이해도 평가 리포트 발급', 'Get a comprehension report'),
 ('M&amp;M 소크라틱 AI Tutor', 'M&amp;M Socratic AI Tutor'),
 ('12번 학습할래', 'Let’s study No. 12'),
 ('과목 12. <b>회사 공정 및 제품의 이해</b>를 시작할게요!<br>고객이 <em>“요즘 기름 품질에 문제 있는 거 아닌가요?”</em> 라고 한다면,<br>공정을 아는 영업사원과 모르는 영업사원의 대응은 어떻게 달라질까요?',
  'Let’s begin Subject 12: <b>Refining &amp; Products</b>!<br>A customer asks, <em>“Is something wrong with your fuel lately?”</em><br>How would a rep who knows the process respond differently?'),
 ('정해진 규격으로 생산된다는 걸 강조해서 대응할 수 있어요', 'I’d stress that it’s made to fixed specifications.'),
 ('정확하게 핵심을 짚으셨어요! ✨ 한 걸음 더 들어가 볼까요?<br>그 말을 하려면 <em>최소한 어떤 공정·제품 지식</em>이 필요할까요?',
  'Spot on! ✨ Let’s go one step deeper.<br>To say that with confidence, <em>what process knowledge</em> do you need?'),
 ('<b>최종 이해도 평가 리포트</b><br>정유공정 메커니즘 이해도', '<b>Final Comprehension Report</b><br>Refining mechanisms'),
 ('공정-경제 가치 추론', 'Process-to-value reasoning'),
 ('다음 추천 학습 → <b>블렌딩 공정 심화</b>', 'Recommended next → <b>Advanced Blending</b>'),
 # S7
 ('현업 사례 · 각자의 현장에서', 'Use cases · in every role'),
 ('<span style="color:var(--teal)">바로</span> 꺼내 쓰는 <span style="color:var(--teal)">지식</span>',
  'Knowledge you can use <span style="color:var(--teal)">right on the job</span>'),
 ('<span class="pill">신입사원</span>', '<span class="pill">New hire</span>'),
 ('<span class="pill">팀장 · 지사장</span>', '<span class="pill">Team · Branch lead</span>'),
 ('파트너가 여신 한도 증대를 문의했어', 'A partner asked to raise their credit limit'),
 ('총한도 = 담보한도 + 신용한도<br>현황 확인 → 증액 검토 → <b>개별 품의</b><br>+ 파트너 소통 화법까지 안내',
  'Total = collateral + credit limit<br>Check → review → <b>formal approval</b><br>+ how to explain it to the partner'),
 ('안전점검, 뭐가 바뀌었던 거 같은데..?', 'Safety checks… did something change?'),
 ('종이 → <b>순회점검 App &amp; 대시보드</b><br>위치 기반 점검 · 사진 첨부 · 전자서명<br>바뀐 매뉴얼과 규정을 바로 안내',
  'Paper → <b>inspection app &amp; dashboard</b><br>GPS check-in · photos · e-signature<br>New rules explained right away'),
 ('파트너 만나러 가기 전에 지역 현황 파악해줘', 'Brief me on the local market before my visit'),
 ('인근 평균가 전국 대비 <b>30~44원 ↓</b><br>7일 연속 하락 · 최저가 경쟁 현황<br>미팅 활용 화법까지 정리',
  'Nearby prices <b>₩30–44 below</b> average<br>7-day decline · lowest-price rivals<br>Plus talking points for the visit'),
 # S8
 ('학습자 니즈 중심', 'Learner-centered'),
 ('>개념 학습<', '>Concepts<'), ('단순 지식은<br>업무 속에서 바로', 'Basics, learned<br>in the flow of work'),
 ('>집중 심화<', '>Deep dive<'), ('실전 심화는 대면에서<br>Case · 토론으로', 'Hands-on in class<br>cases &amp; discussion'),
 ('>복습 · 질의<', '>Review &amp; ask<'), ('학습이 끝난 뒤에도<br>언제·어디서든 다시', 'After training,<br>anytime, anywhere'),
 ('미리 배우고 · 깊게 다지고 · 언제든 다시 활용합니다', 'Learn ahead · go deeper · come back anytime'),
 # S9
 ('04 · 확장', '04 · Expansion'),
 ('사내에서 시작한 AI 튜터를, <span style="color:var(--teal)">파트너 교육</span>까지',
  'From in-house tutor to <span style="color:var(--teal)">partner training</span>'),
 ('사내 임직원 직무교육', 'Employee job training'),
 ('M&amp;M 본부 임직원<br><b style="color:var(--navy)">12개 직무 과목</b> · 지속 확장 예정<br>사내 공개 · 활용 중',
  'M&amp;M Division employees<br><b style="color:var(--navy)">12 job subjects</b> · more to come<br>Live in-house'),
 ('주유소 파트너<br><b style="color:var(--teal2)">경영 실무 8개 과목</b> · 시설안전·마케팅·법규·노무<br>외부 노출·운영 준비 중',
  'Gas station partners<br><b style="color:var(--teal2)">8 business subjects</b> · safety, legal, labor<br>Preparing external launch'),
 ('교육 자료 + 기간계 시스템(SAP · ER · FAMS) 연동으로 활용도를 높여갑니다', 'Linking training content with core systems (SAP · ER · FAMS) to drive adoption'),
 # S10
 ('묻고, 배우고, 쌓는다.', 'Ask. Learn. Build.'),
 ('AI Tutor는 시작일 뿐, 진짜 자산은 그 아래 쌓인 <span style="color:var(--teal)">지식</span>입니다',
  'The AI Tutor is just the beginning — the real asset is the <span style="color:var(--teal)">knowledge</span> it builds'),
]
for a, b in R:
    if a not in s: sys.exit(f'MISSING: {a[:70]}')
    s = s.replace(a, b)
left = sorted(set(re.findall(r'[가-힣][가-힣 ·,.!?]*', s)))
if left: sys.exit('HANGUL LEFT: ' + ' | '.join(left))
open(dst, 'w', encoding='utf-8').write(s)
print('ok', len(R), 'replacements')
