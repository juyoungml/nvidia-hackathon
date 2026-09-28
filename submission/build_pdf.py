"""Render the Korean technical submission from report_content.json.

Usage: uv run --with reportlab python submission/build_pdf.py --content submission/report_content.json \
    --output submission/report.pdf
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = ROOT / "submission/fonts/NanumGothic-Regular.ttf"
W, H = A4
LEFT = 48
RIGHT = W - LEFT
CW = RIGHT - LEFT
BOTTOM = 61
INK = colors.HexColor("#17283A")
NAVY = colors.HexColor("#10263B")
TEAL = colors.HexColor("#087E80")
MID = colors.HexColor("#516273")
PALE = colors.HexColor("#E6EDEF")
LIGHT = colors.HexColor("#F3F7F7")
AMBER = colors.HexColor("#B47829")
FONT = "NanumGothic"


def para(value: Any, size: float, leading: float, color: colors.Color = INK) -> Paragraph:
    markup = html.escape(str(value)).replace("\n", "<br/>")
    return Paragraph(
        markup,
        ParagraphStyle(
            "text",
            fontName=FONT,
            fontSize=size,
            leading=leading,
            textColor=color,
            wordWrap="CJK",
            splitLongWords=True,
        ),
    )


def ph(value: Any, width: float, size: float, leading: float) -> float:
    return para(value, size, leading).wrap(width, H)[1]


def write(
    c: canvas.Canvas,
    value: Any,
    x: float,
    top: float,
    width: float,
    size: float,
    leading: float,
    color: colors.Color = INK,
) -> float:
    p = para(value, size, leading, color)
    _, height = p.wrap(width, H)
    p.drawOn(c, x, top - height)
    return top - height


def line(
    c: canvas.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: colors.Color = PALE,
    width: float = 0.75,
    dash: tuple[int, int] | None = None,
) -> None:
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(width)
    if dash:
        c.setDash(*dash)
    c.line(x1, y1, x2, y2)
    c.restoreState()


def label(
    c: canvas.Canvas, value: str, x: float, y: float, size: float = 7.5, color: colors.Color = MID
) -> None:
    c.setFillColor(color)
    c.setFont(FONT, size)
    c.drawString(x, y, value)


def box(
    c: canvas.Canvas,
    x: float,
    top: float,
    width: float,
    height: float,
    title: str,
    detail: str = "",
    fill: colors.Color = LIGHT,
    stroke: colors.Color = PALE,
    dashed: bool = False,
    title_size: float = 8.3,
) -> None:
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.9)
    if dashed:
        c.setDash(3, 2)
    c.roundRect(x, top - height, width, height, 4, stroke=1, fill=1)
    c.restoreState()
    body_top = write(c, title, x + 7, top - 7, width - 14, title_size, 11, NAVY)
    if detail:
        write(c, detail, x + 7, body_top - 3, width - 14, 7.2, 9.3, MID)


def arrow(
    c: canvas.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    dashed: bool = False,
    color: colors.Color = TEAL,
) -> None:
    line(c, x1, y1, x2, y2, color, 1.2, (3, 2) if dashed else None)
    import math

    theta = math.atan2(y2 - y1, x2 - x1)
    size = 4
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(1.2)
    for delta in (-0.55, 0.55):
        c.line(x2, y2, x2 - size * math.cos(theta + delta), y2 - size * math.sin(theta + delta))
    c.restoreState()


def diagram_system(c: canvas.Canvas, top: float) -> float:
    """Data, edge, cloud, validation, and planned path in one evidence-safe view."""
    h = 260
    x = LEFT
    line(c, x, top, RIGHT, top)
    label(c, "FIGURE 01  /  SYSTEM PATH", x, top - 13, 7.4, TEAL)
    # Background boundaries are deliberately separated; local and hosted are explicit.
    c.setFillColor(colors.HexColor("#F7F9FA"))
    c.roundRect(x, top - 171, 305, 139, 6, fill=1, stroke=0)
    c.roundRect(x + 315, top - 171, 100, 139, 6, fill=1, stroke=0)
    label(c, "LOCAL / NANO S1", x + 9, top - 46, 7.5, TEAL)
    label(c, "HOSTED / ULTRA S2", x + 324, top - 46, 7.5, TEAL)
    y = top - 58
    box(c, x + 9, y, 87, 46, "공개 기록", "오프라인 입력")
    box(c, x + 108, y, 88, 46, "집계", "사건별 정리")
    box(
        c,
        x + 208,
        y,
        88,
        46,
        "Nano S1",
        "로컬 1차 판독",
        colors.HexColor("#E6F3F1"),
        colors.HexColor("#A1CDCA"),
    )
    box(c, x + 9, top - 124, 87, 44, "검증/규칙", "승격→패킷\n그 외→보류")
    box(c, x + 108, top - 124, 88, 44, "이벤트 패킷", "검증된 전달")
    box(c, x + 208, top - 124, 88, 44, "공개 기록 도구", "측정·이전 신고")
    box(
        c,
        x + 325,
        y,
        86,
        46,
        "Ultra S2",
        "심층 조사",
        colors.HexColor("#E6F3F1"),
        colors.HexColor("#A1CDCA"),
    )
    box(c, x + 423, y, 73, 46, "엔지니어", "최종 판단")
    for a, b in ((x + 96, x + 108), (x + 196, x + 208), (x + 411, x + 423)):
        arrow(c, a, y - 23, b, y - 23)
    line(c, x + 251, top - 104, x + 251, top - 111, TEAL, 1.2)
    line(c, x + 251, top - 111, x + 53, top - 111, TEAL, 1.2)
    arrow(c, x + 53, top - 111, x + 53, top - 124)
    arrow(c, x + 96, top - 146, x + 108, top - 146)
    line(c, x + 152, top - 124, x + 152, top - 117, TEAL, 1.2)
    line(c, x + 152, top - 117, x + 310, top - 117, TEAL, 1.2)
    line(c, x + 310, top - 117, x + 310, top - 81, TEAL, 1.2)
    arrow(c, x + 310, top - 81, x + 325, top - 81)
    line(c, x + 325, top - 104, x + 325, top - 157, TEAL, 1.2)
    arrow(c, x + 325, top - 140, x + 296, top - 140)
    arrow(c, x + 296, top - 157, x + 325, top - 157)
    label(c, "공개 데이터", x + 326, top - 152, 6.6, MID)
    # Independent evaluation and planned document index are visually distinct.
    box(c, x + 9, top - 186, 220, 37, "보류 평가 세트", "개발 입력과 분리", colors.white, PALE)
    box(
        c,
        x + 267,
        top - 186,
        229,
        37,
        "문서 인덱스 (계획)",
        "도면 · 매뉴얼 연결 범위",
        colors.white,
        AMBER,
        dashed=True,
    )
    arrow(c, x + 330, top - 186, x + 252, top - 168, dashed=True, color=AMBER)
    label(c, "실선 = 구현된 경로", x + 9, top - 241, 7.2, MID)
    label(c, "점선 = 계획 범위", x + 164, top - 241, 7.2, AMBER)
    line(c, x, top - h, RIGHT, top - h)
    return top - h


def diagram_sequence(c: canvas.Canvas, top: float) -> float:
    h = 158
    line(c, LEFT, top, RIGHT, top)
    label(c, "FIGURE 02  /  INCIDENT RESPONSE", LEFT, top - 13, 7.4, TEAL)
    gap = 7
    bw = (CW - 3 * gap) / 4
    steps = [
        ("01 사건 입력", "증상 · 태그 · 시간"),
        ("02 게이트", "범위 · 근거 검사"),
        ("03 공개 도구", "get_recent_measurements\nget_prior_incidents"),
        ("04 답변", "인용 · 불확실성"),
    ]
    y = top - 38
    for i, (title, detail) in enumerate(steps):
        bx = LEFT + i * (bw + gap)
        box(c, bx, y, bw, 61, title, detail, LIGHT if i != 3 else colors.HexColor("#E6F3F1"))
        if i < 3:
            arrow(c, bx + bw, y - 31, bx + bw + gap, y - 31)
    label(c, "근거가 부족하면 결론을 보류하고 추가 확인을 요청", LEFT + 3, top - 123, 8.2, MID)
    line(c, LEFT, top - h, RIGHT, top - h)
    return top - h


def diagram_security(c: canvas.Canvas, top: float) -> float:
    h = 163
    line(c, LEFT, top, RIGHT, top)
    label(c, "FIGURE 03  /  SECURITY SCOPE", LEFT, top - 13, 7.4, TEAL)
    box(
        c,
        LEFT + 2,
        top - 34,
        239,
        88,
        "격리된 OpenShell 프로브",
        "명령 → 정책 검사\n허용 파일 읽기 → exit 0\n금지 읽기/쓰기/TCP → exit 1",
        LIGHT,
    )
    box(
        c,
        LEFT + 256,
        top - 34,
        239,
        71,
        "운영 경계 (제안)",
        "로컬 S1 · 현장 데이터 배치\n권한 정책 · 운영 통신 경로\n실제 배포 환경에서 재검증 필요",
        colors.white,
        AMBER,
        dashed=True,
    )
    label(c, "프로브에는 호스트 마운트와 모델 엔드포인트가 없음", LEFT + 3, top - 143, 8.1, MID)
    line(c, LEFT, top - h, RIGHT, top - h)
    return top - h


def diagram_economics(c: canvas.Canvas, top: float) -> float:
    h = 175
    line(c, LEFT, top, RIGHT, top)
    label(c, "FIGURE 04  /  ILLUSTRATIVE TIME MODEL", LEFT, top - 13, 7.4, TEAL)
    bar_x = LEFT + 67
    hour = 18.5
    parts = (
        ("식별", TEAL),
        ("준비", colors.HexColor("#80AAA9")),
        ("수리", colors.HexColor("#BCCBD1")),
    )
    for i, (name, color) in enumerate(parts):
        xx = LEFT + i * 92
        c.setFillColor(color)
        c.rect(xx, top - 35, 8, 8, stroke=0, fill=1)
        label(c, name, xx + 12, top - 34, 7.4, MID)
    for name, values, y in (("기준", (8, 4, 8), top - 72), ("대안", (0.5, 4, 8), top - 119)):
        label(c, name, LEFT + 1, y + 8, 8.4, NAVY)
        cursor = bar_x
        for hours, (_, color) in zip(values, parts, strict=True):
            c.setFillColor(color)
            c.rect(cursor, y, hours * hour, 22, stroke=0, fill=1)
            cursor += hours * hour
        label(c, f"{sum(values):g} h", bar_x + 375, y + 7, 8.4, NAVY)
    label(c, "식별 8→0.5 h · 준비 4 h · 수리 8 h", LEFT + 1, top - 145, 8.4, NAVY)
    label(c, "차이 7.5 h는 관측 성과가 아닌 시나리오 계산", LEFT + 1, top - 161, 7.5, MID)
    line(c, LEFT, top - h, RIGHT, top - h)
    return top - h


DIAGRAMS = {
    "system": diagram_system,
    "sequence": diagram_sequence,
    "security": diagram_security,
    "economics": diagram_economics,
}


def image_path(value: str, content_path: Path) -> Path:
    candidate = (ROOT / value).resolve()
    if not candidate.is_file():
        candidate = (content_path.parent / value).resolve()
    if not candidate.is_relative_to(ROOT) or not candidate.is_file():
        raise ValueError(f"Image must be an existing repository file: {value}")
    return candidate


def image_size(path: Path, max_height: float) -> tuple[float, float]:
    source_w, source_h = ImageReader(str(path)).getSize()
    scale = min(CW / source_w, max_height / source_h)
    return source_w * scale, source_h * scale


def table_layout(table: dict, scale: float) -> tuple[list[float], list[float], float]:
    cols = table["columns"]
    widths = [CW / len(cols)] * len(cols)
    # Bias a short identifier column while preserving space for long narrative cells.
    if len(cols) == 2:
        widths = [CW * 0.29, CW * 0.71]
    elif len(cols) == 3:
        widths = [CW * 0.22, CW * 0.39, CW * 0.39]
    elif len(cols) == 6:
        widths = [CW * 0.15, CW * 0.17, CW * 0.17, CW * 0.17, CW * 0.17, CW * 0.17]
    heights = [
        max(ph(v, widths[i] - 14, 8.5 * scale, 11.3 * scale) for i, v in enumerate(cols)) + 13
    ]
    for row in table["rows"]:
        heights.append(
            max(ph(v, widths[i] - 14, 8.25 * scale, 11.25 * scale) for i, v in enumerate(row)) + 13
        )
    return widths, heights, sum(heights)


def draw_table(c: canvas.Canvas, table: dict, top: float, scale: float) -> float:
    widths, heights, _ = table_layout(table, scale)
    for row_i, row in enumerate([table["columns"], *table["rows"]]):
        height = heights[row_i]
        c.setFillColor(NAVY if row_i == 0 else (LIGHT if row_i % 2 == 0 else colors.white))
        c.rect(LEFT, top - height, CW, height, stroke=0, fill=1)
        x = LEFT
        for i, value in enumerate(row):
            write(
                c,
                value,
                x + 7,
                top - 6,
                widths[i] - 14,
                8.5 * scale if row_i == 0 else 8.25 * scale,
                11.3 * scale if row_i == 0 else 11.25 * scale,
                colors.white if row_i == 0 else INK,
            )
            x += widths[i]
        top -= height
        line(c, LEFT, top, RIGHT, top, PALE)
    return top


def validate(data: dict) -> list[dict]:
    if not isinstance(data.get("title"), str) or not data["title"].strip():
        raise ValueError("title must be a nonempty string")
    pages = data.get("pages")
    if not isinstance(pages, list) or not 7 <= len(pages) <= 9:
        raise ValueError("pages must contain seven to nine entries")
    for n, page in enumerate(pages, 1):
        if not isinstance(page, dict) or not all(
            isinstance(page.get(k), str) for k in ("heading", "lead")
        ):
            raise ValueError(f"Page {n} needs heading and lead strings")
        if not isinstance(page.get("sections"), list):
            raise ValueError(f"Page {n} needs a sections list")
        for section in page["sections"]:
            if not isinstance(section, dict) or not all(
                isinstance(section.get(k), str) for k in ("title", "body")
            ):
                raise ValueError(f"Page {n} has an invalid section")
        if page.get("diagram") and page["diagram"] not in DIAGRAMS:
            raise ValueError(f"Page {n} has an unknown diagram")
        if page.get("table"):
            table = page["table"]
            cols = table.get("columns")
            rows = table.get("rows")
            if not isinstance(cols, list) or not 2 <= len(cols) <= 6 or not isinstance(rows, list):
                raise ValueError(f"Page {n} has an invalid table")
            if not all(len(row) == len(cols) for row in rows):
                raise ValueError(f"Page {n} table rows must match columns")
    return pages


def content_height(data: dict, page: dict, first: bool, scale: float, image: Path | None) -> float:
    total = 0.0
    if first:
        total += 19  # Cover eyebrow and its gap above the title.
        total += ph(data["title"], CW, 23, 30) + 4
        if data.get("subtitle"):
            total += ph(data["subtitle"], CW, 9.2, 13) + 14
    else:
        total += 19
    total += ph(page["heading"], CW, 19 * scale, 25 * scale) + 19 * scale
    total += ph(page["lead"], CW, 10.15 * scale, 15.7 * scale) + 18 * scale
    if page.get("diagram"):
        total += {"system": 260, "sequence": 158, "security": 163, "economics": 175}[
            page["diagram"]
        ] + 15 * scale
    if image:
        total += image_size(image, 205)[1] + 15 * scale
    for section in page["sections"]:
        total += ph(section["title"], CW, 10.8 * scale, 14.2 * scale) + 5 * scale
        total += ph(section["body"], CW, 10.2 * scale, 15.25 * scale) + 14 * scale
    if page.get("table"):
        total += table_layout(page["table"], scale)[2] + 15 * scale
    if page.get("footnote"):
        total += ph(page["footnote"], CW, 7.6 * scale, 10.7 * scale) + 8
    return total


def draw_page(
    c: canvas.Canvas, data: dict, page: dict, n: int, total_pages: int, content_path: Path
) -> None:
    first = n == 1
    image = image_path(page["image"], content_path) if page.get("image") else None
    top_start = H - 44
    usable = top_start - BOTTOM
    scales = (1.0, 0.97, 0.94, 0.91)
    scale = next((s for s in scales if content_height(data, page, first, s, image) <= usable), None)
    if scale is None:
        raise ValueError(f"Page {n} overflows at 9.75 pt base body; split or shorten content")
    leftover = usable - content_height(data, page, first, scale, image)
    # Controlled white space brings short pages into balance without huge gaps.
    extra = min(7.5, leftover / max(1, len(page["sections"]) + 2))
    c.setFillColor(NAVY)
    c.rect(0, H - 7, W, 7, fill=1, stroke=0)
    top = top_start
    if first:
        label(c, "PLANT RELIABILITY / TECHNICAL SUBMISSION", LEFT, top + 2, 8, TEAL)
        top -= 19
        top = write(c, data["title"], LEFT, top, CW, 23, 30, NAVY) - 4
        if data.get("subtitle"):
            top = write(c, data["subtitle"], LEFT, top, CW, 9.2, 13, MID) - 14
    else:
        label(c, str(data["title"]), LEFT, top + 1, 7.6, MID)
        top -= 19
    label(c, f"{n:02d}  /  {total_pages:02d}", RIGHT - 48, H - 44, 8, TEAL)
    top = write(c, page["heading"], LEFT, top, CW, 19 * scale, 25 * scale, NAVY) - 7 * scale
    line(c, LEFT, top, LEFT + 42, top, TEAL, 2)
    top -= 12 * scale
    top = (
        write(c, page["lead"], LEFT, top, CW, 10.15 * scale, 15.7 * scale, MID) - 18 * scale - extra
    )
    if page.get("diagram"):
        top = DIAGRAMS[page["diagram"]](c, top) - 15 * scale - extra
    if image:
        iw, ih = image_size(image, 205)
        c.drawImage(
            str(image),
            LEFT + (CW - iw) / 2,
            top - ih,
            width=iw,
            height=ih,
            preserveAspectRatio=True,
            mask="auto",
        )
        top -= ih + 15 * scale + extra
    for i, section in enumerate(page["sections"]):
        if i:
            line(c, LEFT, top + 7 * scale, RIGHT, top + 7 * scale)
        top = (
            write(c, section["title"], LEFT, top, CW, 10.8 * scale, 14.2 * scale, TEAL) - 5 * scale
        )
        top = (
            write(c, section["body"], LEFT, top, CW, 10.2 * scale, 15.25 * scale, INK)
            - 14 * scale
            - extra
        )
    if page.get("table"):
        top = draw_table(c, page["table"], top, scale) - 15 * scale
    if page.get("footnote"):
        line(c, LEFT, top + 3, RIGHT, top + 3)
        top = write(c, page["footnote"], LEFT, top - 5, CW, 7.6 * scale, 10.7 * scale, MID)
    if top < BOTTOM - 1:
        raise ValueError(f"Page {n} crossed the bottom margin: {top:.1f}")
    line(c, LEFT, 46, RIGHT, 46, PALE)
    label(c, "NVIDIA HACKATHON  /  ENGINEERING REVIEW", LEFT, 31, 7.1, MID)
    c.setFillColor(MID)
    c.setFont(FONT, 7.3)
    c.drawRightString(RIGHT, 31, f"{n:02d} / {total_pages:02d}")
    c.showPage()


def build(content_path: Path, output_path: Path, font_path: Path) -> None:
    content_path = content_path.resolve()
    data = json.loads(content_path.read_text(encoding="utf-8"))
    pages = validate(data)
    if not font_path.is_file():
        raise FileNotFoundError(f"Korean font is required: {font_path}")
    pdfmetrics.registerFont(TTFont(FONT, str(font_path)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=1)
    c.setTitle(data["title"])
    c.setAuthor("Plant AI")
    for n, page in enumerate(pages, 1):
        draw_page(c, data, page, n, len(pages), content_path)
    c.save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", type=Path, default=ROOT / "submission/report_content.json")
    parser.add_argument("--output", type=Path, default=ROOT / "submission/report.pdf")
    parser.add_argument("--font", type=Path, default=FONT_PATH)
    args = parser.parse_args()
    build(args.content, args.output, args.font)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
