"""Build an offline, captioned walkthrough from the saved public-data replay."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "poc/trace-52-pipeline.json"
CHART = ROOT / "web/assets/predist-trend.png"
FONT = ROOT / "submission/fonts/NanumGothic-Regular.ttf"
OUTPUT = ROOT / "submission/demo_walkthrough.mp4"
W, H = 1600, 900
NAVY = "#101c2c"
PANEL = "#1b2b3d"
WHITE = "#f5f5ef"
MUTED = "#b9c7ca"
GREEN = "#7ce0aa"
ORANGE = "#ffbb70"
RED = "#ff9292"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size=34, fill=WHITE):
    draw.text(xy, value, font=font(size), fill=fill)


def base(number: int, title: str, kicker: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, W, 12), fill=GREEN)
    text(draw, (80, 48), kicker.upper(), 23, GREEN)
    text(draw, (80, 86), title, 55)
    draw.line((80, 163, 1520, 163), fill="#3b5361", width=2)
    draw.rectangle((0, 815, W, H), fill="#0a1521")
    text(draw, (80, 832), "저장 실행 기록 기반 설명 영상 · 실시간 녹화 아님", 27, ORANGE)
    text(draw, (1390, 833), f"{number:02d} / 06", 25, MUTED)
    return image, draw


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], outline=None):
    draw.rounded_rectangle(box, radius=22, fill=PANEL, outline=outline or "#344b5c", width=2)


def lines(draw: ImageDraw.ImageDraw, x: int, y: int, entries: list[str], size=31, gap=57):
    for index, entry in enumerate(entries):
        text(draw, (x, y + index * gap), entry, size)


def scene_intro(trace: dict) -> Image.Image:
    image, draw = base(
        1, "알람 이후, 무엇을 먼저 확인할까?", "Plant Reliability Agent / 공개 사건 재생"
    )
    card(draw, (80, 210, 1520, 718))
    text(draw, (122, 252), "PreDist v2 · 지역난방 열교환 설비 21", 34, GREEN)
    text(draw, (122, 323), f"신고: “{trace['triage']['input']['customer_report']['problem']}”", 62)
    lines(
        draw,
        122,
        430,
        [
            "사건 시점의 신고·계측·이전 기록을 연결해 다음 점검을 제안합니다.",
            "사후 진단과 조치 결과는 모델 입력에서 제외했습니다.",
        ],
        32,
        61,
    )
    text(
        draw,
        (122, 643),
        f"판단 시각  {trace['decision_time']}  |  사건 {trace['case_id']}",
        27,
        MUTED,
    )
    return image


def scene_source(trace: dict) -> Image.Image:
    image, draw = base(
        2, "공개 계측: 설정값을 따라가는 공급온도", "PreDist v2 / 실제 144개 샘플 재도표"
    )
    card(draw, (80, 194, 1520, 692))
    chart = Image.open(CHART).convert("RGB")
    chart.thumbnail((1360, 440), Image.Resampling.LANCZOS)
    image.paste(chart, (120 + (1360 - chart.width) // 2, 221))
    gap = trace["triage"]["input"]["measurements"]["supply_setpoint_gap"]
    text(
        draw,
        (98, 713),
        f"2차 공급온도–설정값 차이: 평균 {gap['mean']:.2f} °C · 최대 {gap['max']:.1f} °C",
        31,
        WHITE,
    )
    text(draw, (98, 763), "출처 PreDist v2 / CC BY 4.0 · 실내 열 도달을 입증하지는 않음", 25, MUTED)
    return image


def scene_nano(trace: dict) -> Image.Image:
    image, draw = base(3, "System 1 · Nano 선별", "로컬 Ollama / 저장된 실제 결정")
    triage = trace["triage"]
    measured = triage["input"]["measurements"]
    card(draw, (80, 210, 755, 710))
    card(draw, (785, 210, 1520, 710), GREEN)
    text(draw, (120, 253), "입력", 35, GREEN)
    lines(
        draw,
        120,
        330,
        [
            f"고객 신고: {triage['input']['customer_report']['problem']}",
            f"계측 샘플: {measured['samples']}개",
            f"마지막 샘플: {measured['last_sample_time']}",
            "같은 사건의 사후 진단: 미제공",
        ],
        30,
        75,
    )
    decision = triage["effective_decision"]
    text(draw, (825, 253), "검증된 결정", 35, GREEN)
    text(draw, (825, 341), f"Escalate = {str(decision['escalate']).lower()}", 44)
    text(draw, (825, 413), f"Priority = {decision['priority']}", 40)
    text(draw, (825, 504), "Ultra 조사로 전달", 35, ORANGE)
    text(draw, (825, 631), f"Nano 요청 {triage['latency_seconds']:.2f}초", 29, MUTED)
    text(draw, (88, 749), "검증 상태: valid · 이 3건에서는 단순 신고 규칙보다 선별 이점 미확인", 28)
    return image


def scene_ultra(trace: dict) -> Image.Image:
    image, draw = base(4, "System 2 · Ultra가 근거를 읽고 제안", "저장 trace / 두 개의 읽기 도구")
    events = {event["tool"]: event["result"] for event in trace["events"] if "tool" in event}
    measurements = events["get_recent_measurements"]
    prior = events["get_prior_incidents"]["records"][0]
    card(draw, (80, 195, 770, 433))
    card(draw, (800, 195, 1520, 433))
    text(draw, (112, 220), "01  get_recent_measurements", 29, GREEN)
    text(
        draw,
        (112, 280),
        f"{measurements['samples']}개 / 마지막 {measurements['last_sample_time']}",
        28,
    )
    text(draw, (112, 337), "2차 공급온도는 설정값을 대체로 추적", 30)
    text(draw, (832, 220), "02  get_prior_incidents", 29, GREEN)
    text(draw, (832, 280), f"{prior['report_date'][:10]} · {prior['problem']}", 29)
    text(draw, (832, 337), "과거 난방곡선 상향 기록 (현 건과 무관할 수 있음)", 26)
    text(draw, (80, 469), "모델이 제안한 다음 현장 점검", 36, ORANGE)
    card(draw, (80, 532, 1520, 765))
    lines(
        draw,
        120,
        554,
        [
            "1  2차 난방회로 유량·밸브 개도·대표실 실내온도 실측",
            "2  열교환기 1·2차 입출구 온도를 동시에 측정",
            "3  난방곡선·제어 게인·펌프 모드 설정과 변경 이력 확인",
        ],
        29,
        68,
    )
    return image


def scene_limits(trace: dict) -> Image.Image:
    image, draw = base(5, "실패와 해석 한계도 함께 봅니다", "evaluation/results/README.md")
    card(draw, (80, 200, 1520, 741), RED)
    text(
        draw, (115, 232), "사건 52: 계측 수치를 말했지만 계측 source ID는 최종 답변에 빠짐", 31, RED
    )
    lines(
        draw,
        115,
        315,
        [
            "공급온도 추적 ≠ 실내 난방 확인; 2차 유량·실내온도는 미계측",
            "1차 네트워크 유량을 고객측 2차 유량으로 해석할 수 없음",
            "공개 사건 3건 모두 Nano가 상향; 단순 신고 규칙도 3건 모두 상향",
            "모델 요청 시간은 현장 원인 식별 시간이 아님",
        ],
        29,
        74,
    )
    nano = trace["triage"]["latency_seconds"]
    ultra = sum(event["latency_seconds"] for event in trace["events"] if "step" in event)
    text(
        draw, (115, 658), f"이 사건 요청 시간: Nano {nano:.2f}초 · Ultra {ultra:.2f}초", 29, ORANGE
    )
    return image


def scene_reproduce(trace: dict) -> Image.Image:
    image, draw = base(6, "같은 기록을 직접 재생할 수 있습니다", "오프라인 제출물 / 재현 경로")
    card(draw, (80, 195, 1520, 742))
    text(draw, (116, 225), "API 키 없이 정적 재생", 36, GREEN)
    text(draw, (116, 290), "python3 scripts/serve_demo.py --port 8772", 35)
    text(draw, (116, 345), "http://127.0.0.1:8772/web/investigation.html", 32, MUTED)
    draw.line((116, 418, 1484, 418), fill="#446070", width=2)
    text(draw, (116, 454), "검토할 원본", 34, GREEN)
    lines(
        draw,
        116,
        515,
        [
            "poc/trace-52-pipeline.json · evaluation/results/README.md",
            f"PreDist v2 · DOI {trace['source']['doi']} · CC BY 4.0",
            "8시간 → 30분은 경제성 가정과 목표; 달성 결과가 아닙니다.",
        ],
        29,
        62,
    )
    return image


def main() -> None:
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    assert trace["case_id"] == "PreDist-M1-fault-52"
    assert trace["triage"]["validation_status"] == "valid"
    assert [event["tool"] for event in trace["events"] if "tool" in event] == [
        "get_recent_measurements",
        "get_prior_incidents",
    ]
    scenes = [
        scene_intro(trace),
        scene_source(trace),
        scene_nano(trace),
        scene_ultra(trace),
        scene_limits(trace),
        scene_reproduce(trace),
    ]
    durations = [14, 18, 16, 27, 19, 17]
    with tempfile.TemporaryDirectory(prefix="plant-walkthrough-") as directory:
        directory = Path(directory)
        frame_paths = []
        for index, frame in enumerate(scenes, start=1):
            path = directory / f"scene-{index:02d}.png"
            frame.save(path)
            frame_paths.append(path)
        playlist = directory / "playlist.txt"
        playlist.write_text(
            "".join(
                f"file '{path}'\nduration {duration}\n"
                for path, duration in zip(frame_paths, durations, strict=True)
            )
            + f"file '{frame_paths[-1]}'\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(playlist),
                "-vf",
                "fps=24,format=yuv420p",
                "-c:v",
                "libx264",
                "-crf",
                "23",
                "-preset",
                "medium",
                "-movflags",
                "+faststart",
                "-an",
                "-t",
                str(sum(durations)),
                str(OUTPUT),
            ],
            check=True,
        )
    print(f"Created {OUTPUT} ({sum(durations)} seconds)")


if __name__ == "__main__":
    main()
