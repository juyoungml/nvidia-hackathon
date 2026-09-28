"""Build the Plant Reliability Agent submission deck.

Run from the repo root:
    uv run --with python-pptx python submission/slides/build_deck.py
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "Plant_Reliability_Agent_submission.pptx"
CHART29 = ROOT / "web/assets/system2-case29-trend.png"

FONT = "Apple SD Gothic Neo"
PAPER = RGBColor(0xFB, 0xF9, 0xF4)
INK = RGBColor(0x17, 0x2B, 0x27)
GREEN = RGBColor(0x24, 0x4E, 0x41)
MUTED = RGBColor(0x62, 0x73, 0x6A)
LINE = RGBColor(0xBF, 0xC8, 0xBF)
ORANGE = RGBColor(0xD0, 0x6B, 0x3D)
NV = RGBColor(0x76, 0xB9, 0x00)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SOFT = RGBColor(0xF1, 0xEE, 0xE6)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def _font(run, size, color, bold):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rpr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rpr.find(qn(tag))
        if el is None:
            el = rpr.makeelement(qn(tag), {})
            rpr.append(el)
        el.set("typeface", FONT)


def text(
    slide,
    x,
    y,
    w,
    h,
    lines,
    size=20,
    color=INK,
    bold=False,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    spacing=1.15,
):
    """lines: str or list of str / list of (str, dict) runs per paragraph."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    _fill(tf, lines, size, color, bold, align, spacing)
    return tb


def _fill(tf, lines, size, color, bold, align, spacing=1.15):
    if isinstance(lines, str):
        lines = [lines]
    for i, para in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        runs = para if isinstance(para, list) else [(para, {})]
        for t, st in runs:
            r = p.add_run()
            r.text = t
            _font(r, st.get("size", size), st.get("color", color), st.get("bold", bold))


def box(
    slide,
    x,
    y,
    w,
    h,
    lines="",
    fill=WHITE,
    line=LINE,
    size=18,
    color=INK,
    bold=False,
    shape=MSO_SHAPE.ROUNDED_RECTANGLE,
    align=PP_ALIGN.CENTER,
    lw=1.25,
):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = 0.12
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    s.shadow.inherit = False
    sp = s._element.spPr
    if sp.find(qn("a:effectLst")) is None:
        sp.append(sp.makeelement(qn("a:effectLst"), {}))
    tf = s.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.1)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    if lines:
        _fill(tf, lines, size, color, bold, align)
    return s


def arrow(slide, x1, y1, x2, y2, color=MUTED, w=2):
    c = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    c.line.color.rgb = color
    c.line.width = Pt(w)
    ln = c.line._get_or_add_ln()
    tail = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"})
    ln.append(tail)
    return c


def new_slide(title=None, kicker=None, notes=""):
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = PAPER
    if kicker:
        text(s, 0.8, 0.5, 11.5, 0.4, kicker, size=16, color=ORANGE, bold=True)
    if title:
        text(s, 0.8, 0.85, 11.8, 0.9, title, size=36, color=INK, bold=True)
    s.notes_slide.notes_text_frame.text = notes
    return s


def page_no(s, n):
    text(s, 12.2, 6.95, 0.8, 0.3, str(n), size=12, color=MUTED, align=PP_ALIGN.RIGHT)


# 1 Cover -------------------------------------------------------------------
s = new_slide(
    notes=(
        "겨울에 한 집에서 '난방이 안 된다'는 신고가 들어왔습니다. 그런데 계측값을 보면 공급온도는 목표와 거의 같습니다. "
        "숫자는 정상인데 방은 추운 상황이죠. 저희 Plant Reliability Agent는 이런 신고가 들어오면, 엔지니어보다 먼저 "
        "AI 에이전트가 첫 조사를 해 두는 도구입니다. 에이전트의 두뇌는 NVIDIA Nemotron 3 Ultra입니다."
    )
)
box(s, 0, 0, 0.35, 7.5, fill=GREEN, line=None, shape=MSO_SHAPE.RECTANGLE)
text(s, 1.0, 1.7, 11, 1.2, "계측은 정상인데, 방은 춥다", size=54, color=INK, bold=True)
text(s, 1.0, 3.0, 11, 0.8, "Plant Reliability Agent", size=32, color=GREEN, bold=True)
box(s, 1.0, 3.95, 1.2, 0.06, fill=ORANGE, line=None, shape=MSO_SHAPE.RECTANGLE)
text(
    s,
    1.0,
    4.3,
    11,
    0.6,
    "설비 이상 신고가 들어오면, 첫 조사는 AI 에이전트가 먼저",
    size=24,
    color=INK,
)
text(
    s,
    1.0,
    5.6,
    11,
    0.5,
    [[("Built with ", {"color": MUTED}), ("NVIDIA Nemotron 3 Ultra", {"color": NV, "bold": True})]],
    size=20,
)
text(s, 1.0, 6.6, 11, 0.4, "NVIDIA Korea Agentic AI Hackathon", size=14, color=MUTED)

# 2 Problem -----------------------------------------------------------------
s = new_slide(
    "신고 한 건에, 자료는 여러 곳",
    "문제",
    notes=(
        "설비 이상 신고가 오면 엔지니어는 계측 데이터, 과거 신고, 정비 기록을 시스템마다 하나씩 열어 봅니다. "
        "더 어려운 건 계측이 정상처럼 보일 때입니다. 숫자만 보면 문제가 없으니, 어디부터 봐야 할지 판단하기가 힘듭니다. "
        "저희는 이 첫 조사 단계를 에이전트에게 맡겨 보기로 했습니다."
    ),
)
box(s, 0.8, 2.3, 2.3, 1.2, "이상 신고", fill=ORANGE, line=None, size=22, color=WHITE, bold=True)
for i, lab in enumerate(["계측 데이터", "과거 신고", "정비 기록"]):
    y = 1.95 + i * 0.75
    box(s, 4.3, y, 2.8, 0.6, lab, fill=WHITE, size=20)
    arrow(s, 3.1, 2.9, 4.3, y + 0.3)
text(
    s,
    7.6,
    2.05,
    5.0,
    1.8,
    ["엔지니어가", "하나씩 열어 보고", "직접 맞춰 본다"],
    size=22,
    color=MUTED,
)
box(s, 0.8, 4.6, 11.7, 1.5, "", fill=SOFT, line=None)
text(
    s,
    1.2,
    4.75,
    11,
    1.2,
    [
        [("계측이 정상처럼 보이면 ", {}), ("더 어렵다", {"color": ORANGE, "bold": True})],
        "숫자에 문제가 없으니, 어디부터 볼지 정하기 힘들다",
    ],
    size=26,
    anchor=MSO_ANCHOR.MIDDLE,
)
page_no(s, 2)

# 3 Background --------------------------------------------------------------
s = new_slide(
    "30초 배경: 지역난방",
    "처음 보시는 분께",
    notes=(
        "지역난방은 한 곳에서 만든 뜨거운 물을 도시 배관으로 보내고, 건물마다 있는 서브스테이션에서 열을 건물 배관으로 옮기는 방식입니다. "
        "이 공개 데이터에는 공급온도 센서 기록은 있지만, 건물 안 배관의 유량이나 실내 온도는 없습니다. "
        "샤워기 물이 뜨거워도 수압이 약하면 씻기 어렵죠. 온도가 정상이어도 방이 추울 수 있는 이유입니다."
    ),
)
labels = [
    "열 생산 시설",
    "도시 배관\n(1차)",
    "서브스테이션\n(열교환)",
    "건물 배관\n(2차)",
    "집 안\n라디에이터",
]
bw, gap, x0, yb = 2.0, 0.42, 0.8, 2.35
for i, lab in enumerate(labels):
    x = x0 + i * (bw + gap)
    hl = i == 2
    box(
        s,
        x,
        yb,
        bw,
        1.25,
        lab.split("\n"),
        fill=GREEN if hl else WHITE,
        line=None if hl else LINE,
        size=19,
        color=WHITE if hl else INK,
        bold=hl,
    )
    if i < 4:
        arrow(s, x + bw + 0.04, yb + 0.62, x + bw + gap - 0.04, yb + 0.62, color=ORANGE, w=2.5)
# sensor tags
tags = [
    (2, "공급온도 센서", "기록 있음", GREEN),
    (3, "건물 배관 유량", "기록 없음", ORANGE),
    (4, "실내 온도", "기록 없음", ORANGE),
]
for i, a, b, col in tags:
    x = x0 + i * (bw + gap)
    arrow(s, x + bw / 2, yb + 1.3, x + bw / 2, yb + 1.75, color=col, w=1.5)
    box(
        s,
        x,
        yb + 1.8,
        bw,
        0.95,
        [[(a, {"size": 17})], [(b, {"size": 18, "bold": True, "color": col})]],
        fill=PAPER,
        line=col,
        lw=1.75,
    )
box(s, 0.8, 5.65, 11.7, 0.95, "", fill=SOFT, line=None)
text(
    s,
    1.2,
    5.65,
    11,
    0.95,
    "샤워기 물이 뜨거워도, 수압이 약하면 씻기 어렵다",
    size=24,
    bold=True,
    color=GREEN,
    anchor=MSO_ANCHOR.MIDDLE,
)
page_no(s, 3)

# 4 Real incident -----------------------------------------------------------
s = new_slide(
    '실제 신고: "난방이 안 된다"',
    "사례 29 · 공개 데이터 PreDist v2",
    notes=(
        "실제 공개 데이터 PreDist v2의 사례입니다. 2019년 1월 9일 오후 2시 18분, 17번 서브스테이션 고객이 난방이 안 된다고 신고했습니다. "
        "신고 직전 마지막 계측은 2시 10분, 공급온도 63.9도, 목표 63.8도로 정상처럼 보입니다. "
        "하지만 24시간, 10분 간격 144개 기록을 보면 그전에 두 선이 여러 번 벌어졌고, 차이가 최대 13.4도까지 났습니다."
    ),
)
text(s, 0.8, 1.95, 4.0, 0.4, "신고 직전 마지막 계측 (14:10)", size=18, color=MUTED)
text(
    s,
    0.8,
    2.4,
    4.2,
    0.9,
    [[("63.9°C", {"color": GREEN, "bold": True}), ("  공급", {"size": 20, "color": MUTED})]],
    size=44,
)
text(
    s,
    0.8,
    3.25,
    4.2,
    0.9,
    [[("63.8°C", {"color": ORANGE, "bold": True}), ("  목표", {"size": 20, "color": MUTED})]],
    size=44,
)
text(s, 0.8, 4.2, 4.2, 0.5, "→ 정상처럼 보인다", size=22, bold=True)
text(
    s,
    0.8,
    5.2,
    4.3,
    1.4,
    [
        "하지만 그전 24시간에는",
        [("최대 13.4°C", {"color": ORANGE, "bold": True}), (" 벌어졌다", {})],
    ],
    size=22,
)
if CHART29.exists():
    pic = s.shapes.add_picture(str(CHART29), Inches(5.3), Inches(2.1), width=Inches(7.4))
text(
    s,
    5.3,
    5.3,
    7.4,
    0.4,
    [
        [
            ("■ ", {"color": GREEN}),
            ("실제 공급온도   ", {}),
            ("■ ", {"color": ORANGE}),
            ("목표 온도", {}),
        ]
    ],
    size=16,
    color=MUTED,
)
text(
    s,
    5.3,
    5.7,
    7.4,
    0.4,
    "17번 서브스테이션 · 2019-01-09 14:18 신고 · 24시간, 10분 간격 144개 기록",
    size=15,
    color=MUTED,
)
page_no(s, 4)

# 5 What the agent did ------------------------------------------------------
s = new_slide(
    "에이전트가 한 일",
    "사례 29",
    notes=(
        "여기서 Nemotron 3 Ultra가 스스로 어떤 자료를 볼지 골랐습니다. 최근 계측, 센서 설명, 과거 신고, 정비 기록, 목표에서 벗어난 시간대, "
        "그리고 1시부터 2시 18분 구간을 다시 조회했습니다. 모델과 도구 실행 시간은 약 20초입니다. "
        "결과는 원본 기록에 연결된 점검 3가지와, 데이터로는 알 수 없는 것의 목록입니다. 최종 판단은 엔지니어가 합니다."
    ),
)
text(
    s,
    0.8,
    1.95,
    5.6,
    0.4,
    [[("Nemotron 3 Ultra", {"color": NV, "bold": True}), ("가 고른 자료 6종", {})]],
    size=20,
)
reads = [
    "최근 계측",
    "센서 설명",
    "과거 신고",
    "정비 기록",
    "목표 이탈 시간대",
    "13:00~14:18 재조회",
]
for i, r in enumerate(reads):
    col, row = i % 2, i // 2
    box(s, 0.8 + col * 2.75, 2.5 + row * 0.8, 2.6, 0.62, r, fill=WHITE, line=NV, size=17, lw=1.5)
text(
    s,
    0.8,
    5.0,
    5.4,
    0.9,
    [
        [("약 20초", {"size": 40, "bold": True, "color": INK})],
        [("모델·도구 실행 시간 (현장 처리 시간 아님)", {"size": 15, "color": MUTED})],
    ],
    size=18,
)
arrow(s, 6.35, 3.6, 6.95, 3.6, color=ORANGE, w=3)
text(s, 7.1, 1.95, 5.6, 0.4, "점검 3가지 · 원본 기록에 연결", size=20)
checks = ["① 실내·라디에이터 온도 확인", "② 건물 배관 유량 측정", "③ 제어기 설정·경보 기록 검토"]
for i, c in enumerate(checks):
    box(
        s,
        7.1,
        2.5 + i * 0.8,
        5.4,
        0.62,
        c,
        fill=GREEN,
        line=None,
        size=19,
        color=WHITE,
        bold=True,
        align=PP_ALIGN.LEFT,
    )
box(
    s,
    7.1,
    4.95,
    5.4,
    0.62,
    "+ 데이터로 알 수 없는 것도 함께 전달",
    fill=PAPER,
    line=ORANGE,
    size=18,
    color=ORANGE,
    align=PP_ALIGN.LEFT,
    lw=1.5,
)
text(s, 7.1, 5.85, 5.4, 0.5, "판단은 엔지니어가 한다", size=22, bold=True)
page_no(s, 5)

# 6 Architecture ------------------------------------------------------------
s = new_slide(
    "구조",
    "어떻게 동작하나",
    notes=(
        "구조는 단순합니다. 신고 내용과 접수 시각이 들어오면, NVIDIA NIM에서 돌아가는 Nemotron 3 Ultra가 읽을 자료를 고릅니다. "
        "읽기 전용 도구 6종은 NeMo Agent Toolkit으로 실행되고, 결과가 다시 모델로 돌아옵니다. "
        "마지막으로 모든 점검 항목이 원본 기록에 연결됐는지 검사한 뒤 엔지니어에게 전달합니다. 초록색이 NVIDIA 기술입니다."
    ),
)
yc = 3.0
box(s, 0.8, yc, 2.0, 1.3, ["신고", "+ 접수 시각"], fill=WHITE, size=19)
box(
    s,
    3.5,
    yc - 0.3,
    2.9,
    1.9,
    [[("Nemotron 3 Ultra", {"bold": True, "size": 21})], [("NVIDIA NIM", {"size": 16})]],
    fill=NV,
    line=None,
    color=WHITE,
)
box(
    s,
    3.5,
    yc + 2.25,
    2.9,
    1.45,
    [
        [("읽기 전용 도구 6종", {"bold": True, "size": 19, "color": INK})],
        [("NeMo Agent Toolkit", {"size": 16, "color": NV, "bold": True})],
    ],
    fill=WHITE,
    line=NV,
    lw=2,
)
box(s, 7.1, yc, 2.4, 1.3, ["근거 연결", "검사"], fill=WHITE, size=19)
box(s, 10.2, yc, 2.3, 1.3, "엔지니어", fill=GREEN, line=None, size=21, color=WHITE, bold=True)
arrow(s, 2.85, yc + 0.65, 3.45, yc + 0.65)
arrow(s, 4.55, yc + 1.65, 4.55, yc + 2.2, color=NV, w=2.5)
arrow(s, 5.35, yc + 2.2, 5.35, yc + 1.65, color=NV, w=2.5)
text(s, 3.5, yc + 1.68, 1.0, 0.5, "요청", size=14, color=MUTED, align=PP_ALIGN.RIGHT)
text(s, 5.45, yc + 1.68, 1.0, 0.5, "결과", size=14, color=MUTED)
arrow(s, 6.45, yc + 0.65, 7.05, yc + 0.65)
arrow(s, 9.55, yc + 0.65, 10.15, yc + 0.65)
text(
    s,
    7.1,
    1.9,
    5.4,
    0.8,
    [[("■ ", {"color": NV}), ("NVIDIA 기술", {})]],
    size=18,
    color=MUTED,
    align=PP_ALIGN.RIGHT,
)
text(
    s,
    7.1,
    5.3,
    5.4,
    1.2,
    ["모든 점검은 원본 기록에 연결돼야 통과", "도구는 읽기만 한다"],
    size=18,
    color=MUTED,
)
page_no(s, 6)

# 7 NVIDIA roles ------------------------------------------------------------
s = new_slide(
    "NVIDIA 기술이 맡은 일",
    "역할과 현재 상태",
    notes=(
        "NVIDIA 기술이 각각 무슨 일을 했는지 정리했습니다. Nemotron 3 Ultra는 두뇌입니다. 어떤 자료를 읽을지 스스로 고르고, 결과를 대조해 정해진 JSON 형식으로 점검안을 만듭니다. 데모 전체의 핵심 경로입니다. "
        "NeMo Agent Toolkit은 읽기 도구 6종을 등록하고 실행합니다. 직접 호출과 결과가 같은지 검사했고, 사례 52에서 모델이 고른 조회 6회를 실행했습니다. 조사 순서 루프 자체는 저희 Python 코드입니다. "
        "OpenShell은 안전장치로, 시험 데이터에서 허용 파일 읽기만 통과하고 나머지는 차단되는 것을 확인했습니다. 전체 경로 적용은 아직입니다."
    ),
)
cols = [
    (
        "Nemotron 3 Ultra",
        "nvidia/nemotron-3-ultra-550b-a55b",
        "두뇌 · NVIDIA NIM",
        ["읽을 자료를 스스로 고름", "결과 대조", "JSON 형식 점검안 생성"],
        "데모 전체의 핵심 경로",
        True,
    ),
    (
        "NeMo Agent Toolkit",
        "버전 1.8.0",
        "도구 실행",
        ["읽기 도구 6종 등록·실행", "직접 호출과 결과 동일", "사례 52: 조회 6회 실행"],
        "일부 적용 · 루프는 자체 코드",
        False,
    ),
    (
        "OpenShell",
        "버전 0.1.2",
        "안전장치",
        ["허용 파일 읽기만 통과", "다른 읽기·쓰기 차단", "외부 통신 차단"],
        "시험 데이터로 확인 · 전체 적용 전",
        False,
    ),
]
cw, cg, cx0, cy = 3.75, 0.23, 0.8, 1.95
for i, (name, sub, role, lines_, status, core) in enumerate(cols):
    x = cx0 + i * (cw + cg)
    box(s, x, cy, cw, 3.85, "", fill=WHITE, line=NV, lw=2.5 if core else 1.5)
    text(s, x + 0.25, cy + 0.3, cw - 0.5, 0.5, role, size=18, color=MUTED, bold=True)
    text(s, x + 0.25, cy + 0.7, cw - 0.5, 0.6, name, size=24, color=NV, bold=True)
    text(s, x + 0.25, cy + 1.25, cw - 0.5, 0.4, sub, size=13, color=MUTED)
    text(s, x + 0.25, cy + 1.8, cw - 0.5, 1.1, lines_, size=18, color=INK)
    box(
        s,
        x + 0.25,
        cy + 3.05,
        cw - 0.5,
        0.55,
        status,
        fill=NV if core else SOFT,
        line=None,
        size=15,
        color=WHITE if core else INK,
        bold=core,
    )
box(s, 0.8, 6.05, 11.7, 0.75, "", fill=SOFT, line=None)
text(
    s,
    1.1,
    6.05,
    11.2,
    0.75,
    [
        [
            ("다음  ", {"bold": True, "color": ORANGE}),
            ("Nemotron Nano", {"bold": True, "color": NV}),
            (" 상시 감시 (수만 개 신호)   ·   ", {}),
            ("NeMo Retriever", {"bold": True, "color": NV}),
            (" 문서·도면 검색", {}),
        ]
    ],
    size=19,
    anchor=MSO_ANCHOR.MIDDLE,
)
page_no(s, 7)

# 8 Honest results ----------------------------------------------------------
s = new_slide(
    "솔직한 결과",
    "같은 자료 · 같은 출력 형식 · 신고 4건",
    notes=(
        "같은 자료와 같은 출력 형식으로 신고 4건을 돌렸고, 참고 기준으로 Anthropic Claude Sonnet 5를 읽기와 검색만 허용해 비교했습니다. "
        "근거 연결 검사 통과는 Ultra 4건 중 2건, Sonnet 4건 모두입니다. Ultra가 놓친 2건은 조회 6회를 다 쓰고 정리하지 못한 경우였습니다. "
        "한도에 닿으면 모은 자료로 정리하도록 고쳤고, 사례 52에서 6회 조회, 27.8초, 점검 3개로 확인했지만 2/4에는 넣지 않았습니다. "
        "둘 다 끝낸 2건의 내용 검토는 48점 만점에 41대 42입니다. 이것은 진단 정확도가 아닙니다."
    ),
)
text(s, 0.8, 1.95, 6, 0.4, "근거 연결 검사 통과", size=20, color=MUTED)
text(s, 0.8, 2.4, 3.0, 1.1, [[("2/4", {"color": NV, "bold": True})]], size=66)
text(s, 0.8, 3.5, 3.0, 0.4, "Nemotron 3 Ultra", size=18, color=NV, bold=True)
text(s, 3.6, 2.4, 3.0, 1.1, [[("4/4", {"color": MUTED, "bold": True})]], size=66)
text(s, 3.6, 3.5, 3.0, 0.4, "Claude Sonnet 5 (참고)", size=18, color=MUTED, bold=True)
text(s, 0.8, 4.4, 6.0, 0.4, "둘 다 끝낸 2건 · 내용 검토", size=20, color=MUTED)
text(
    s,
    0.8,
    4.85,
    6.0,
    0.8,
    [
        [
            ("41", {"color": NV, "bold": True}),
            (" : ", {"color": MUTED}),
            ("42", {"color": MUTED, "bold": True}),
            ("  / 48", {"size": 22, "color": MUTED}),
        ]
    ],
    size=44,
)
box(s, 7.2, 1.95, 5.3, 3.75, "", fill=WHITE, line=LINE)
text(
    s,
    7.5,
    2.15,
    4.8,
    3.4,
    [
        [("놓친 2건의 원인", {"bold": True, "color": ORANGE})],
        "조회 6회를 다 쓰고 정리하지 못함",
        [("고침", {"bold": True, "color": ORANGE})],
        '"한도에 닿으면 모은 자료로 정리"',
        [("사례 52 재확인", {"bold": True, "color": ORANGE})],
        "조회 6회 · 27.8초 · 점검 3개",
        [("(2/4에는 포함하지 않음)", {"size": 15, "color": MUTED})],
    ],
    size=18,
    spacing=1.2,
)
text(
    s,
    0.8,
    6.2,
    11.7,
    0.5,
    "이 검사는 진단 정확도가 아니다 · Sonnet은 Claude Code로 읽기·검색만 허용",
    size=16,
    color=MUTED,
)
page_no(s, 8)

# 9 Next --------------------------------------------------------------------
s = new_slide(
    "다음 단계",
    notes=(
        "다음 단계는 세 가지입니다. 먼저 현장 엔지니어에게 이 점검안이 실제로 쓸모 있는지 평가받고, 새 사건으로 다시 검증합니다. "
        "그 다음 발전소로 넓히고, Nemotron Nano로 수만 개 신호를 상시 감시하는 쪽으로 가려고 합니다. "
        "오늘 데모는 저장된 실제 실행 기록을 재생한 것입니다. 판단은 엔지니어가, 자료 수집은 Plant가 합니다. 감사합니다."
    ),
)
steps = [
    ("1", "현장 엔지니어 평가"),
    ("2", "새 사건으로 재검증"),
    ("3", "발전소 확장\n+ Nano 상시 감시"),
]
for i, (n, lab) in enumerate(steps):
    x = 0.8 + i * 4.05
    box(s, x, 2.3, 3.6, 1.9, "", fill=WHITE, line=LINE)
    text(s, x + 0.3, 2.45, 1, 0.7, n, size=32, color=ORANGE, bold=True)
    parts = lab.split("\n")
    para = [[(parts[0], {})]] + (
        [[("+ ", {}), ("Nano", {"color": NV, "bold": True}), (" 상시 감시", {})]]
        if len(parts) > 1
        else []
    )
    text(s, x + 0.3, 3.15, 3.1, 1.0, para, size=21, bold=False)
    if i < 2:
        arrow(s, x + 3.65, 3.25, x + 4.0, 3.25, color=ORANGE, w=2.5)
text(
    s,
    0.8,
    4.9,
    11.7,
    1.0,
    "판단은 엔지니어가, 자료 수집은 Plant가.",
    size=36,
    color=GREEN,
    bold=True,
    align=PP_ALIGN.CENTER,
)
text(
    s,
    0.8,
    6.2,
    11.7,
    0.4,
    "데모는 저장된 실제 실행 기록을 재생합니다",
    size=16,
    color=MUTED,
    align=PP_ALIGN.CENTER,
)
page_no(s, 9)

prs.save(OUT)
print(f"saved {OUT} ({len(prs.slides)} slides)")
