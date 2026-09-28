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
# Evaluation figure: if present, the results slide shows it instead of the 4-case numbers.
EVAL_FIG = ROOT / "figures/eval-cycle5.png"

# Facts for slides 2 and 4. Fill ONLY from sourced research notes; empty -> neutral wording.
# DOWNTIME: list of (big number, label); DOWNTIME_SOURCE: tiny source line.
DOWNTIME = [
    ("연 1.4조 달러", "포춘 글로벌 500 기업이 비계획 정지로 잃는 비용"),
    ("매출의 약 11%", "2019–2020년 약 8%에서 증가"),
]
DOWNTIME_SOURCE = "Siemens, The True Cost of Downtime 2024 · 대형 산업 전반 수치(발전소 한정 아님)"
# SPARK: list of (model label, DGX Spark count text, basis line). Empty -> "소수의 DGX Spark".
SPARK = [
    (
        "Nemotron 3 Ultra 550B · 평가 모델",
        "DGX Spark 약 4대",
        "약 330–358GB(NVFP4 + 여유) · 최소 3대, 권장 4대 · 추정",
    ),
    (
        "Nemotron 3 Super 120B · 가벼운 대안(미평가)",
        "DGX Spark 1대",
        "약 72–78GB · Spark 1대 메모리 128GB",
    ),
]
SPARK_SOURCE = "DGX Spark 128GB 통합 메모리(NVIDIA 공식) · 대수는 저희 계산"
SECURITY_SOURCE = "예: 북미 NERC CIP-005 전자 보안 경계 · 국내 국가 망 보안체계(N2SF)"

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


def page_no(s, n=None):
    n = len(prs.slides._sldIdLst)
    text(s, 12.2, 6.95, 0.8, 0.3, str(n), size=12, color=MUTED, align=PP_ALIGN.RIGHT)


# 1 Cover -------------------------------------------------------------------
s = new_slide(
    notes=(
        "발전소 설비 이상, 첫 조사를 AI 에이전트가 먼저 하는 이야기입니다. 예를 하나 들겠습니다. 겨울에 한 집에서 '난방이 안 된다'는 신고가 들어왔습니다. 그런데 계측값을 보면 공급온도는 목표와 거의 같습니다. "
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
    5.0,
    11,
    0.5,
    [[("Built with ", {"color": MUTED}), ("NVIDIA Nemotron 3 Ultra", {"color": NV, "bold": True})]],
    size=20,
)
text(s, 1.0, 6.75, 11, 0.4, "Team Sona · NVIDIA Korea Agentic AI Hackathon", size=14, color=MUTED)
text(
    s,
    1.0,
    5.7,
    11.5,
    0.8,
    [
        [
            ("GitHub  ", {"bold": True, "color": GREEN}),
            ("github.com/juyoungml/nvidia-hackathon", {}),
        ],
        [("Live demo  ", {"bold": True, "color": GREEN}), ("juyoung.site/nvidia-hackathon", {})],
    ],
    size=15,
)

# 2 Problem: downtime cost --------------------------------------------------
s = new_slide(
    "발전소가 멈추면, 비용이 크다",
    "문제",
    notes=(
        "발전소 설비가 예정에 없이 멈추는 것을 비계획 정지, 다운타임이라고 부릅니다. "
        + (
            "숫자로 보면 이렇습니다. "
            + "Siemens의 2024년 보고서에 따르면 포춘 글로벌 500 기업이 비계획 정지로 1년에 약 1.4조 달러, 매출의 약 11%를 잃습니다. 발전소만의 수치는 아니고 대형 산업 전반의 수치입니다."
            + " "
            if DOWNTIME
            else "비계획 정지는 큰 손실로 이어집니다. "
        )
        + "그래서 이상 징후를 빨리 알아채고, 원인을 빨리 찾는 것이 중요합니다."
    ),
)
if DOWNTIME:
    n = len(DOWNTIME)
    cw = (11.7 - 0.3 * (n - 1)) / n
    for i, (num, lab) in enumerate(DOWNTIME):
        x = 0.8 + i * (cw + 0.3)
        box(s, x, 2.1, cw, 2.9, "", fill=WHITE, line=LINE)
        text(s, x + 0.3, 2.4, cw - 0.6, 1.2, num, size=40, color=ORANGE, bold=True)
        text(s, x + 0.3, 3.6, cw - 0.6, 1.3, lab, size=19, color=INK)
else:
    box(s, 0.8, 2.1, 11.7, 2.9, "", fill=WHITE, line=LINE)
    text(
        s,
        1.2,
        2.1,
        11,
        2.9,
        [
            [("비계획 정지(다운타임)", {"color": ORANGE, "bold": True})],
            "는 큰 손실로 이어진다",
        ],
        size=36,
        anchor=MSO_ANCHOR.MIDDLE,
    )
box(s, 0.8, 5.3, 11.7, 0.9, "", fill=SOFT, line=None)
text(
    s,
    1.2,
    5.3,
    11,
    0.9,
    "이상을 빨리 알아채고, 원인을 빨리 찾아야 한다",
    size=24,
    bold=True,
    color=GREEN,
    anchor=MSO_ANCHOR.MIDDLE,
)
if DOWNTIME_SOURCE:
    text(s, 0.8, 6.45, 11.3, 0.4, "출처: " + DOWNTIME_SOURCE, size=11, color=MUTED)
page_no(s)

# 3 Why hard ----------------------------------------------------------------
s = new_slide(
    "왜 어려운가: 자료가 흩어져 있다",
    "판단이 어려운 이유",
    notes=(
        "이슈가 생겼을 때 원인을 판단하기 어려운 이유는 자료가 여러 곳에 흩어져 있기 때문입니다. "
        "배관과 계기 연결을 보여 주는 도면인 P&ID와 로직 다이어그램, 과거 이상 신고인 TM, 정비 작업 지시인 WO, "
        "그리고 센서 트렌드 데이터가 모두 다른 시스템에 있습니다. 엔지니어는 이것을 하나씩 열어 머릿속에서 연결해야 합니다."
    ),
)
srcs = [
    ("도면", "P&ID · 로직 다이어그램"),
    ("TM", "과거 이상 신고"),
    ("WO", "작업 지시 · 정비 기록"),
    ("트렌드", "센서 시계열 데이터"),
]
for i, (a, b) in enumerate(srcs):
    y = 1.95 + i * 1.05
    box(
        s,
        0.8,
        y,
        4.6,
        0.85,
        [[(a + "  ", {"bold": True, "size": 22}), (b, {"size": 17, "color": MUTED})]],
        fill=WHITE,
        align=PP_ALIGN.LEFT,
    )
    arrow(s, 5.45, y + 0.42, 7.0, 3.9)
box(s, 7.05, 3.2, 2.4, 1.4, "엔지니어", fill=ORANGE, line=None, size=24, color=WHITE, bold=True)
text(
    s,
    9.8,
    3.0,
    3.0,
    1.8,
    ["하나씩 열어", "머릿속에서", "연결한다"],
    size=22,
    color=MUTED,
    anchor=MSO_ANCHOR.MIDDLE,
)
box(s, 0.8, 6.2, 11.7, 0.65, "", fill=SOFT, line=None)
text(
    s,
    1.2,
    6.2,
    11,
    0.65,
    [[("계측이 정상처럼 보이면 ", {}), ("더 어렵다", {"color": ORANGE, "bold": True})]],
    size=21,
    anchor=MSO_ANCHOR.MIDDLE,
)
page_no(s)

# 4 Constraint: security ------------------------------------------------------
s = new_slide(
    "보안 때문에 클라우드 AI는 어렵다",
    "제약",
    notes=(
        "발전소 제어·운영망은 외부망과 분리하고 통제하는 것이 원칙입니다. 북미의 NERC CIP 표준이나 국내 국가 망 보안체계가 그 예입니다. 그래서 외부 클라우드 AI에 현장 자료를 그대로 보내기 어렵습니다. "
        "그래서 모델을 현장 내부에 설치해야 합니다. 저희는 공개 가중치 모델인 NVIDIA Nemotron과, 책상 위에 올릴 수 있는 NVIDIA DGX Spark를 조합했습니다. "
        "평가에 쓴 모델은 Nemotron 3 Ultra로, 전체 5,500억 파라미터 중 한 번에 550억만 쓰는 구조입니다. "
        + (
            "DGX Spark 한 대의 메모리는 128기가바이트입니다. 저희 계산으로 Ultra는 가중치 약 275기가바이트에 여유를 더해 최소 3대, 권장 DGX Spark 약 4대, 가벼운 대안인 Nemotron 3 Super 120B는 1대면 됩니다. Super는 아직 평가하지 않았고, 대수는 측정이 아닌 추정입니다."
            if SPARK
            else "필요한 장비는 소수의 DGX Spark 수준으로 보고 있습니다."
        )
    ),
)
box(
    s,
    0.8,
    2.1,
    3.3,
    1.5,
    ["제어·운영망은", "외부망과 분리·통제"],
    fill=WHITE,
    line=ORANGE,
    lw=2,
    size=20,
)
arrow(s, 4.15, 2.85, 5.0, 2.85, color=ORANGE, w=3)
box(
    s,
    5.05,
    2.1,
    3.3,
    1.5,
    ["현장 내부 설치", "모델 필요"],
    fill=GREEN,
    line=None,
    size=21,
    color=WHITE,
    bold=True,
)
arrow(s, 8.4, 2.85, 9.25, 2.85, color=NV, w=3)
box(
    s,
    9.3,
    2.1,
    3.2,
    1.5,
    [[("NVIDIA Nemotron", {"bold": True})], [("+ DGX Spark", {"bold": True})]],
    fill=NV,
    line=None,
    size=21,
    color=WHITE,
)
box(s, 0.8, 4.0, 11.7, 2.55, "", fill=WHITE, line=NV, lw=1.5)
text(
    s,
    1.1,
    4.15,
    11.1,
    0.5,
    [
        [
            ("평가 모델  ", {"color": MUTED}),
            ("Nemotron 3 Ultra", {"color": NV, "bold": True}),
            ("  · 전체 550B / 동작 55B (MoE)", {}),
        ]
    ],
    size=20,
)
if SPARK:
    for i, (m, c, basis) in enumerate(SPARK[:2]):
        x = 1.1 + i * 5.7
        text(s, x, 4.8, 5.4, 0.45, m, size=18, color=MUTED, bold=True)
        text(s, x, 5.2, 5.4, 0.7, c, size=30, color=NV, bold=True)
        text(s, x, 5.9, 5.4, 0.5, basis, size=13, color=MUTED)
    text(s, 0.8, 6.65, 11.7, 0.3, SPARK_SOURCE + " · " + SECURITY_SOURCE, size=11, color=MUTED)
else:
    text(
        s,
        1.1,
        4.9,
        11.1,
        1.4,
        [
            [("필요 장비  ", {"color": MUTED}), ("소수의 DGX Spark", {"color": NV, "bold": True})],
            [("현장 서버실에 둘 수 있는 규모", {"size": 17, "color": MUTED})],
        ],
        size=26,
    )
page_no(s)

# 5 Solution: System 1 + System 2 ---------------------------------------------
s = new_slide(
    "해법: 빠른 감시 + 깊은 조사",
    "System 1 · System 2",
    notes=(
        "해법은 두 단계로 나눴습니다. System 1은 항상 켜져 있으면서 트렌드를 감시하고 알람을 냅니다. 가볍고 빨라야 하고, Nemotron Nano를 후보로 보고 있습니다. 이 부분은 아직 설계와 이전 실험 단계입니다. "
        "System 2는 문제가 생겼을 때 도면, TM, WO, 트렌드를 연결해 원인을 찾고 다음 점검을 제안합니다. 오늘 데모는 이 System 2입니다. "
        "나눈 이유는 간단합니다. 상시 감시는 빨라야 하고, 원인 조사는 깊어야 하기 때문입니다."
    ),
)
cards = [
    (
        "System 1 · 상시 감시",
        ["항상 켜짐", "트렌드 감시 · 알람", "가볍고 빠르게"],
        "Nemotron Nano (후보)",
        "설계 · 이전 실험",
        False,
    ),
    (
        "System 2 · 원인 조사",
        ["문제 발생 시 실행", "도면·TM·WO·트렌드 연결", "원인 · 다음 점검 제안"],
        "Nemotron 3 Ultra",
        "구현 · 오늘 데모",
        True,
    ),
]
for i, (name, lines_, model, status, live) in enumerate(cards):
    x = 0.8 + i * 6.05
    box(s, x, 1.95, 5.65, 3.85, "", fill=WHITE, line=NV if live else LINE, lw=2.5 if live else 1.5)
    text(s, x + 0.3, 2.15, 5.1, 0.55, name, size=24, bold=True, color=GREEN)
    text(s, x + 0.3, 2.85, 5.1, 1.5, lines_, size=20)
    text(s, x + 0.3, 4.4, 5.1, 0.45, model, size=19, color=NV, bold=True)
    box(
        s,
        x + 0.3,
        5.0,
        5.05,
        0.55,
        status,
        fill=GREEN if live else SOFT,
        line=None,
        size=16,
        color=WHITE if live else INK,
        bold=live,
    )
arrow(s, 6.47, 3.4, 6.83, 3.4, color=ORANGE, w=3)
box(s, 0.8, 6.05, 11.7, 0.75, "", fill=SOFT, line=None)
text(
    s,
    1.1,
    6.05,
    11.2,
    0.75,
    [
        [
            ("왜 나누나  ", {"bold": True, "color": ORANGE}),
            ("상시 감시는 빠르게, 원인 조사는 깊게", {}),
        ]
    ],
    size=21,
    anchor=MSO_ANCHOR.MIDDLE,
)
page_no(s)

# 5b Architecture -------------------------------------------------------------
s = new_slide(
    "전체 구조",
    notes=(
        "전체 구조를 한 장으로 보겠습니다. 왼쪽은 발전소 안의 자료, 도면, TM, WO, 트렌드입니다. "
        "위쪽 System 1은 트렌드를 상시 감시하는 부분으로, Nemotron Nano를 쓰는 설계 단계라 점선으로 표시했습니다. "
        "아래쪽 System 2가 오늘 데모입니다. 신고나 알람이 들어오면 Nemotron 3 Ultra가 NeMo Agent Toolkit의 읽기 전용 도구 6종으로 자료를 조회하고 대조해 점검안을 씁니다. "
        "모든 인용은 실제 조회 기록과 연결되는지 검사한 뒤 엔지니어에게 전달되고, 결정은 엔지니어가 합니다. "
        "모델과 도구는 OpenShell 격리 환경에서 시험했고, 전체는 현장 내부 DGX Spark에 배포하는 것을 전제로 합니다. 도면 검색용 NeMo Retriever도 계획 단계입니다."
    ),
)
ARCH = ROOT / "docs/assets/architecture.png"
if ARCH.exists():
    s.shapes.add_picture(str(ARCH), Inches(1.9), Inches(1.7), height=Inches(5.35))
page_no(s)

# 6 System 1 requirements -----------------------------------------------------
s = new_slide(
    "System 1이 감당할 양",
    "설계 부하 · 계산값",
    notes=(
        "System 1의 설계 부하를 계산해 봤습니다. 신호 5만 개가 0.1초마다 갱신된다고 가정하면 초당 50만 개 관측값입니다. "
        "값과 시각을 16바이트로 저장하면 초당 8메가바이트, 하루 691기가바이트입니다. 이건 측정값이 아니라 설계 계산입니다. "
        "이 양을 전부 큰 모델에 보낼 수는 없습니다. 그래서 먼저 시계열 코드로 변화율이나 기준선 이탈을 요약하고, Nano가 사건을 묶어 우선순위를 정하고, 선별된 사건만 Ultra가 조사합니다. "
        "지금 로컬 Nano는 요청 한 건에 6에서 11초가 걸려서, 이 부분도 병목이 될 수 있습니다. 부하 시험이 다음 과제입니다."
    ),
)
kpis = [
    ("50,000", "신호"),
    ("100 ms", "갱신 주기"),
    ("50만/초", "관측값"),
    ("691 GB/일", "값+시각 16바이트 기준"),
]
for i, (a, b) in enumerate(kpis):
    x = 0.8 + i * 2.97
    box(s, x, 1.95, 2.75, 1.6, "", fill=WHITE, line=LINE)
    text(s, x + 0.2, 2.1, 2.35, 0.75, a, size=30, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
    text(s, x + 0.2, 2.9, 2.35, 0.5, b, size=15, color=MUTED, align=PP_ALIGN.CENTER)
flow = [
    ("시계열 코드", "요약 · 후보 추출", WHITE, INK),
    ("Nano", "사건 묶기 · 우선순위", WHITE, INK),
    ("Ultra", "선별된 사건만 조사", NV, WHITE),
]
for i, (a, b, f, c) in enumerate(flow):
    x = 0.8 + i * 4.05
    box(
        s,
        x,
        4.0,
        3.5,
        1.25,
        [[(a, {"bold": True, "size": 21})], [(b, {"size": 16})]],
        fill=f,
        line=NV if i else LINE,
        color=c,
        lw=1.75,
    )
    if i < 2:
        arrow(s, x + 3.55, 4.62, x + 4.0, 4.62, color=ORANGE, w=2.5)
text(
    s,
    0.8,
    5.55,
    11.7,
    1.2,
    [
        [("원시 데이터를 전부 큰 모델에 보내지 않는다", {"bold": True})],
        [
            (
                "현재 로컬 Nano 요청 6.3~11.5초 → 병목 가능, 부하 시험이 다음 과제",
                {"size": 16, "color": MUTED},
            )
        ],
    ],
    size=21,
)
page_no(s)

# 3 Background --------------------------------------------------------------
s = new_slide(
    "데이터: 공개 PreDist v2 (지역난방)",
    "고객 데이터는 비공개 → 공개 데이터로 벤치마크 구성",
    notes=(
        "실제 고객 발전소 데이터는 공개할 수 없어서, 공개 데이터인 PreDist v2로 벤치마크를 만들었습니다. PreDist는 지역난방 데이터입니다. 30초만 배경을 설명드리겠습니다. "
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

# 9 Architecture + NVIDIA ------------------------------------------------------
s = new_slide(
    "구조와 NVIDIA 기술",
    "로컬·보안 환경용 에이전트를 빠르게",
    notes=(
        "System 2의 구조입니다. 신고와 접수 시각이 들어오면 NVIDIA NIM으로 제공되는 Nemotron 3 Ultra가 읽을 자료를 고릅니다. "
        "읽기 전용 도구는 NeMo Agent Toolkit으로 등록했고, 사례 52 개발 실행에서 모델이 고른 조회 6회를 NeMo Agent Toolkit이 실행했습니다. 조사 순서 루프 자체는 저희 Python 코드입니다. "
        "OpenShell은 안전장치로, 공개 시험 데이터에서 허용 파일 읽기만 통과하고 나머지는 차단되는 것을 확인했습니다. 전체 경로 적용은 아직입니다. "
        "강조하고 싶은 점은 NIM, NeMo Agent Toolkit, OpenShell처럼 에이전트 실행 환경 생태계가 잘 갖춰져 있어서, 로컬 보안 환경용 에이전트를 빠르게 구성할 수 있었다는 것입니다. 초록색이 NVIDIA 기술입니다."
    ),
)
yc = 2.05
box(s, 0.8, yc, 2.0, 1.2, ["신고", "+ 접수 시각"], fill=WHITE, size=18)
box(
    s,
    3.4,
    yc - 0.1,
    3.0,
    1.4,
    [[("Nemotron 3 Ultra", {"bold": True, "size": 20})], [("NVIDIA NIM", {"size": 15})]],
    fill=NV,
    line=None,
    color=WHITE,
)
box(s, 7.0, yc, 2.4, 1.2, ["근거 연결", "검사"], fill=WHITE, size=18)
box(s, 10.0, yc, 2.5, 1.2, "엔지니어", fill=GREEN, line=None, size=20, color=WHITE, bold=True)
arrow(s, 2.85, yc + 0.6, 3.35, yc + 0.6)
arrow(s, 6.45, yc + 0.6, 6.95, yc + 0.6)
arrow(s, 9.45, yc + 0.6, 9.95, yc + 0.6)
cols = [
    ("NIM", "모델 제공", "Ultra를 표준 API로 호출", "데모 핵심 경로", True),
    (
        "NeMo Agent Toolkit",
        "도구 실행",
        "읽기 도구 등록 · 사례 52 조회 6회",
        "일부 적용 · 루프는 자체 코드",
        False,
    ),
    (
        "OpenShell",
        "안전장치",
        "허용 파일 읽기만 통과 · 나머지 차단",
        "공개 시험 데이터로만 확인",
        False,
    ),
]
cw, cg, cy = 3.75, 0.23, 3.75
for i, (name, role, what, status, core) in enumerate(cols):
    x = 0.8 + i * (cw + cg)
    box(s, x, cy, cw, 2.2, "", fill=WHITE, line=NV, lw=2.5 if core else 1.5)
    text(s, x + 0.25, cy + 0.15, cw - 0.5, 0.4, role, size=15, color=MUTED, bold=True)
    text(s, x + 0.25, cy + 0.5, cw - 0.5, 0.5, name, size=21, color=NV, bold=True)
    text(s, x + 0.25, cy + 1.0, cw - 0.5, 0.6, what, size=15, color=INK)
    box(
        s,
        x + 0.25,
        cy + 1.62,
        cw - 0.5,
        0.42,
        status,
        fill=NV if core else SOFT,
        line=None,
        size=13,
        color=WHITE if core else INK,
        bold=core,
    )
text(
    s,
    0.8,
    6.2,
    11.7,
    0.6,
    [
        [
            ("실행 환경 생태계가 갖춰져 있어 ", {}),
            ("로컬·보안 환경용 에이전트를 빠르게 구성", {"bold": True, "color": GREEN}),
        ]
    ],
    size=19,
)
page_no(s)

# 10 Results --------------------------------------------------------------------
s = new_slide(
    "평가 결과: 판단의 질은 상한선에 가깝다",
    "PreDist 사건 32건 · 같은 자료 · 같은 출력 형식 · 사건당 1회",
    notes=(
        "공개 PreDist 사건 32건을 같은 자료와 같은 출력 형식으로 돌렸습니다. Claude Sonnet 5는 클라우드 최고 수준의 기준점이지만, 보안 때문에 발전소 안에서는 쓸 수 없습니다. "
        "질문은 누가 이기느냐가 아니라, 현장에 설치할 수 있는 모델이 이 상한선에 얼마나 가까운가입니다. "
        "1차 실행에서는 NVIDIA API 오류 13건 때문에 15건만 결과가 나왔지만, 속도를 낮춰 같은 요청을 다시 보내자 모두 결과가 나왔고 Ultra는 32건 중 26건을 통과했습니다. 끝까지 작성한 점검안 26개는 모두 근거 검사를 통과했고, 조회하지 않은 기록을 지어낸 경우는 한 번도 없었습니다. "
        "남은 실패 6건은 모두 시간 구간을 한도보다 길게 요청한 한 가지 도구 실수였습니다. "
        "도구 쪽에서 요청 범위를 자동으로 맞춰 주는 것이 오프라인 보완 계획입니다. 이 검사는 진단 정확도 평가는 아닙니다."
    ),
)
if EVAL_FIG.exists():
    from PIL import Image

    iw, ih = Image.open(EVAL_FIG).size
    maxw, maxh = 7.3, 3.9
    w = min(maxw, maxh * iw / ih)
    s.shapes.add_picture(str(EVAL_FIG), Inches(0.6), Inches(1.95), width=Inches(w))
text(
    s,
    8.2,
    1.95,
    4.6,
    3.9,
    [
        [("Sonnet 5 = 클라우드 상한선", {"bold": True, "color": MUTED})],
        [("보안상 현장 사용 불가 · 32/32", {"size": 15, "color": MUTED})],
        [("", {"size": 8})],
        [("API 오류 재실행 후 Ultra 26/32", {"bold": True, "color": NV})],
        [("작성한 점검안 26개 모두 통과 · 근거 조작 0건", {"size": 15})],
        [("", {"size": 8})],
        [("남은 실패 6건", {"bold": True, "color": ORANGE})],
        [("모두 같은 도구 실수 (24행 초과 요청)", {"size": 15})],
        [("", {"size": 8})],
        [("내용 점수 41 : 42 / 48 (2건)", {"bold": True})],
    ],
    size=19,
    spacing=1.15,
)
box(s, 0.8, 6.0, 11.7, 0.7, "", fill=SOFT, line=None)
text(
    s,
    1.1,
    6.0,
    11.2,
    0.7,
    [
        [
            ("남은 격차는 ", {}),
            ("한 가지 도구 실수", {"bold": True, "color": GREEN}),
            (
                "  →  도구가 요청 범위를 맞추도록 오프라인에서 보완 예정",
                {"size": 16, "color": MUTED},
            ),
        ]
    ],
    size=20,
    anchor=MSO_ANCHOR.MIDDLE,
)
page_no(s)

# 11 Next -----------------------------------------------------------------------
s = new_slide(
    "다음 단계",
    notes=(
        "다음 단계는 세 가지입니다. 먼저 오프라인 현장 환경에서 Ultra의 부족한 부분을 보완하고 현장 엔지니어에게 평가받습니다. "
        "다음으로 System 1을 Nemotron Nano로 구현하고 5만 개 신호 부하 시험을 합니다. "
        "마지막으로 System 1과 System 2를 연결해 DGX Spark 위에서 현장 내부에서 돌리는 것이 목표입니다. "
        "오늘 데모는 저장된 실제 실행 기록을 재생한 것입니다. 판단은 엔지니어가, 자료 수집은 Plant가 합니다. 감사합니다."
    ),
)
steps = [
    ("1", [[("오프라인 보완", {})], [("+ 현장 엔지니어 평가", {"size": 18, "color": MUTED})]]),
    (
        "2",
        [
            [("System 1 구현", {})],
            [("Nano", {"color": NV, "bold": True}), (" · 5만 신호 부하 시험", {"size": 18})],
        ],
    ),
    (
        "3",
        [
            [("현장 내부 통합", {})],
            [("DGX Spark", {"color": NV, "bold": True}), (" 위 System 1+2", {"size": 18})],
        ],
    ),
]
for i, (n, para) in enumerate(steps):
    x = 0.8 + i * 4.05
    box(s, x, 2.3, 3.6, 1.9, "", fill=WHITE, line=LINE)
    text(s, x + 0.3, 2.45, 1, 0.7, n, size=32, color=ORANGE, bold=True)
    text(s, x + 0.3, 3.15, 3.1, 1.0, para, size=21)
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
    "GitHub github.com/juyoungml/nvidia-hackathon  ·  Live demo juyoung.site/nvidia-hackathon  ·  데모는 저장된 실제 실행 기록을 재생합니다",
    size=14,
    color=MUTED,
    align=PP_ALIGN.CENTER,
)
page_no(s)

prs.save(OUT)
print(f"saved {OUT} ({len(prs.slides)} slides)")
